# Phase 2b: Deploy on Vercel (serverless) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the FastAPI app run correctly on Vercel's serverless (Python) runtime without losing any functionality, by removing the assumptions that only hold on a single persistent process.

**Architecture:** Three adaptations — (1) replace per-process in-memory rate-limit state with an Upstash Redis REST store (env-selected, in-memory fallback kept for local/tests); (2) stop running DB migrations on every cold start and use a serverless-safe connection pool; (3) add a Vercel ASGI entrypoint + `vercel.json`. External Postgres (Neon, pooled) and Upstash Redis are provisioned by the user. No feature behavior changes; nothing is removed.

**Tech Stack:** FastAPI on `@vercel/python`, Neon Postgres (pooled), Upstash Redis (REST), pytest. Upstash + Neon are reached over HTTPS/psycopg — **no new Python dependency** (Upstash via stdlib `urllib`, matching the existing Resend call). Run Python via `.venv\Scripts\python.exe`.

## Global Constraints

- **No functionality regressions.** Every existing endpoint behaves identically; this is an infra adaptation only.
- **No new runtime dependency** unless unavoidable. Use stdlib `urllib` for the Upstash REST call (same pattern as `app/auth/email.py`).
- The rate-limit **dependency interface is unchanged**: `rate_limiter(max_requests, window_seconds, scope)` still returns a FastAPI dependency; call sites in `app/main.py`/`app/api/*` are NOT modified.
- Env-selected behavior with safe fallback: when `UPSTASH_REDIS_REST_URL`/`_TOKEN` are unset, use the existing in-memory limiter (so local + tests are unchanged). When Upstash is unreachable at request time, **fail open** (allow the request) — never lock users out because Redis blipped.
- Keep the full suite green (currently 205 on the Phase-2 branch; this plan builds on top of it). Do not weaken `RATE_LIMIT_ENABLED=false` behavior (tests rely on it).
- This is an ALTERNATIVE host to Render; it depends on the Phase-2 rebrand branch being merged first (or built on it). Commit as the repo owner (Claude co-author trailer acceptable on this repo).

---

### Task V1: Upstash-backed distributed rate limiter (env-selected, in-memory fallback)

**Files:**
- Modify: `app/rate_limit.py`
- Test: `tests/test_rate_limit.py`

**Interfaces:**
- Consumes: env `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `RATE_LIMIT_ENABLED`.
- Produces: unchanged `rate_limiter(max_requests, window_seconds, scope)` dependency whose enforcement uses Upstash when configured.

- [ ] **Step 1: Write the failing test** in `tests/test_rate_limit.py` (append):

```python
def test_upstash_path_blocks_over_limit(monkeypatch):
    import app.rate_limit as rl
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "tok")
    calls = {"n": 0}

    def fake_incr(key, window_seconds):
        calls["n"] += 1
        return calls["n"]  # 1, 2, 3, ...

    monkeypatch.setattr(rl, "_upstash_incr", fake_incr)
    dep = rl.rate_limiter(2, 60, "test")

    class Req:
        class client:
            host = "1.2.3.4"

    dep(Req())  # 1 -> ok
    dep(Req())  # 2 -> ok
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        dep(Req())  # 3 -> blocked


def test_upstash_fail_open(monkeypatch):
    import app.rate_limit as rl
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "tok")

    def boom(key, window_seconds):
        raise OSError("redis down")

    monkeypatch.setattr(rl, "_upstash_incr", boom)
    dep = rl.rate_limiter(1, 60, "test")

    class Req:
        class client:
            host = "9.9.9.9"

    dep(Req()); dep(Req())  # must NOT raise (fail open)
```

- [ ] **Step 2: Run to verify it fails**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_rate_limit.py -k upstash -v`  → FAIL (`_upstash_incr` doesn't exist).

- [ ] **Step 3: Implement the Upstash path** in `app/rate_limit.py`. Add near the top (after imports):

```python
import json
from urllib.request import Request as _UrlRequest, urlopen


def _upstash_configured() -> bool:
    return bool(
        os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
        and os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    )


def _upstash_incr(key: str, window_seconds: float) -> int:
    """Fixed-window counter in Upstash Redis over its REST API.

    Increments a per-window bucket key and sets its TTL so old windows expire.
    Returns the current count. Raises on transport errors (caller fails open).
    """
    base = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    bucket = int(time.time() // window_seconds)
    rkey = f"rl:{key}:{bucket}"
    body = json.dumps([["INCR", rkey], ["EXPIRE", rkey, int(window_seconds)]]).encode("utf-8")
    req = _UrlRequest(
        f"{base}/pipeline",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=3) as resp:
        results = json.loads(resp.read().decode("utf-8"))
    return int(results[0]["result"])
```

- [ ] **Step 4: Route the dependency through Upstash when configured.** In `rate_limiter(...)`'s inner `dependency`, replace the `if not limiter.allow(...)` block so it uses Upstash when configured, fail-open on error:

```python
    def dependency(request: Request) -> None:
        if not _enabled():
            return
        client = request.client.host if request.client else "unknown"
        key = f"{scope}:{client}"
        if _upstash_configured():
            try:
                allowed = _upstash_incr(key, window_seconds) <= max_requests
            except (OSError, ValueError, KeyError):
                allowed = True  # fail open: never lock users out on a Redis blip
        else:
            allowed = limiter.allow(key)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "Too many requests. Please wait a moment and try again."},
            )
```

- [ ] **Step 5: Run the tests to verify they pass**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_rate_limit.py -v`  → PASS (new + existing).

- [ ] **Step 6: Commit**
  `git add app/rate_limit.py tests/test_rate_limit.py && git commit -m "Add Upstash Redis rate-limit backend for serverless (in-memory fallback)"`

---

### Task V2: Serverless-safe DB pool + migrations out of cold start

**Files:**
- Modify: `app/db/database.py`, `app/main.py` (the `lifespan` function)
- Test: `tests/test_config.py` (or new `tests/test_startup.py`)

**Interfaces:**
- Consumes: env `RUN_MIGRATIONS_ON_STARTUP` (default `true`), `DATABASE_URL`.
- Produces: `init_db()` unchanged; startup only calls it when the flag is true; Postgres engine uses a serverless-safe pool.

- [ ] **Step 1: Write the failing test** in `tests/test_startup.py`:

```python
import importlib


def test_startup_skips_migrations_when_disabled(monkeypatch):
    monkeypatch.setenv("RUN_MIGRATIONS_ON_STARTUP", "false")
    import app.main as main
    called = {"n": 0}
    monkeypatch.setattr(main, "init_db", lambda: called.__setitem__("n", called["n"] + 1))
    # Drive the lifespan startup manually.
    import anyio

    async def run():
        async with main.lifespan(main.app):
            pass

    anyio.run(run)
    assert called["n"] == 0
```

- [ ] **Step 2: Run to verify it fails**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_startup.py -v`  → FAIL (startup always calls `init_db`).

- [ ] **Step 3: Gate migrations in `lifespan`.** In `app/main.py`, change the `lifespan` startup so `init_db()` runs only when enabled:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("RUN_MIGRATIONS_ON_STARTUP", "true").lower() not in {"0", "false", "no"}:
        init_db()
    app.state.scholarships = load_scholarships()
    app.state.programs = load_summer_programs()
    yield
```

- [ ] **Step 4: Serverless-safe Postgres pool.** In `app/db/database.py`, after `_engine_kwargs = {"pool_pre_ping": True}`, add a NullPool for Postgres so each serverless invocation doesn't hold a pool against the Neon pooler:

```python
if DATABASE_URL.startswith("postgresql"):
    from sqlalchemy.pool import NullPool

    _engine_kwargs["poolclass"] = NullPool
```

(Leave the SQLite branch unchanged. NullPool + Neon's pooled endpoint is the recommended serverless combination.)

- [ ] **Step 5: Run the test to verify it passes**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_startup.py -v`  → PASS.

- [ ] **Step 6: Full suite**
  Run: `.venv\Scripts\python.exe -m pytest tests/ -q`  → all pass (local/tests use SQLite + default `RUN_MIGRATIONS_ON_STARTUP=true`, so behavior is unchanged).

- [ ] **Step 7: Commit**
  `git add app/db/database.py app/main.py tests/test_startup.py && git commit -m "Gate startup migrations + serverless-safe Postgres pool"`

---

### Task V3: Vercel entrypoint + config

**Files:**
- Create: `api/index.py`, `vercel.json`, `.vercelignore`

**Interfaces:**
- Produces: a Vercel Python function that serves the whole FastAPI app.

- [ ] **Step 1: Create the ASGI entrypoint** `api/index.py`:

```python
"""Vercel serverless entrypoint. Vercel's @vercel/python runtime serves the
FastAPI ASGI `app` exported here for every route (see vercel.json)."""
from app.main import app  # noqa: F401
```

- [ ] **Step 2: Create `vercel.json`** routing all paths to the function and running migrations at build:

```json
{
  "version": 2,
  "buildCommand": "python -m alembic upgrade head",
  "builds": [{ "src": "api/index.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "api/index.py" }]
}
```

- [ ] **Step 3: Create `.vercelignore`** so the local DB, venv, tests, and scratch aren't uploaded:

```
.venv
.superpowers
tests
docs
*.db
scholarships4u.db
```

- [ ] **Step 4: Sanity-check the entrypoint imports** (no server needed):
  Run: `.venv\Scripts\python.exe -c "import api.index; print('ok', api.index.app.title)"`
  Expected: `ok EnsureCollege`.

- [ ] **Step 5: Commit**
  `git add api/index.py vercel.json .vercelignore && git commit -m "Add Vercel serverless entrypoint and config"`

---

### Task V4: Document the Vercel/Neon/Upstash env

**Files:**
- Modify: `.env.example`, `README.md`

- [ ] **Step 1:** In `.env.example`, add:

```
# --- Serverless (Vercel) hosting only ---
# Postgres: use a Neon POOLED connection string (has -pooler in the host).
# DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.neon.tech/db?sslmode=require
# Distributed rate limiting (required on serverless; in-memory won't work):
# UPSTASH_REDIS_REST_URL=
# UPSTASH_REDIS_REST_TOKEN=
# Run Alembic in the Vercel build step instead of on cold start:
# RUN_MIGRATIONS_ON_STARTUP=false
```

- [ ] **Step 2:** In `README.md`, add a short "Deploying on Vercel" subsection summarizing: import repo, set the env vars above, `alembic upgrade head` runs at build, provision Neon (pooled) + Upstash.
- [ ] **Step 3: Commit**
  `git add .env.example README.md && git commit -m "Document Vercel/Neon/Upstash deployment env"`

---

## Group E — User dashboard checklist (NOT agent tasks — you do these)

- [ ] **Neon:** create a project + database; copy the **pooled** connection string (host contains `-pooler`).
- [ ] **Upstash:** create a Redis database; copy `UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN`.
- [ ] **Vercel:** import the GitHub repo; set env vars: `DATABASE_URL` (Neon pooled), `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `RUN_MIGRATIONS_ON_STARTUP=false`, `PUBLIC_APP_URL=https://ensurecollege.com`, `SESSION_SECRET`, `SESSION_COOKIE_SECURE=true`, `RESEND_API_KEY`, `EMAIL_FROM`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`. Leave `AI_FEATURES_ENABLED` unset/false.
- [ ] **First deploy** runs `alembic upgrade head` (buildCommand) against Neon — verify the tables were created.
- [ ] **Domain:** add `ensurecollege.com` (+ `www` and `scholarships4u.dev` for the 301) to the Vercel project; set the DNS records Vercel shows; wait for TLS.
- [ ] **Google OAuth:** add `https://ensurecollege.com/auth/google/callback` to authorized redirect URIs.
- [ ] **Verify after deploy:** homepage loads (EnsureCollege brand), sign up + log in (Neon persists), password reset email arrives, hit an old-domain URL and confirm the 301, and exceed the password-reset limit quickly to confirm the Upstash limiter returns 429.

---

## Self-review notes
- Covers the three serverless gaps identified: rate limiter (V1), migrations-on-cold-start + pooling (V2), entrypoint/config (V3), plus docs (V4) and the provisioning checklist (E).
- No feature is removed or changed; local/test behavior is preserved by env-gated fallbacks (in-memory limiter, `RUN_MIGRATIONS_ON_STARTUP` default true, SQLite pool unchanged).
- Depends on the Phase-2 rebrand branch (`phase2-rebrand-domain`) being merged first; `api/index.py`'s title check expects "EnsureCollege".
