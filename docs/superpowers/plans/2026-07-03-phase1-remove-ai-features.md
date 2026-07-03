# Phase 1: Remove AI Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate all Anthropic-backed features (essay advice/review, program advice, resume auto-fill) behind an off-by-default flag so the site carries zero AI API cost, while keeping the code dormant and re-enableable.

**Architecture:** A single env flag `AI_FEATURES_ENABLED` (read at request time) drives a FastAPI dependency that returns 404 for the four AI routes when off, and is echoed into the page via a `<meta>` tag so the frontend hides the AI UI. No AI code is deleted; flipping the flag restores everything.

**Tech Stack:** FastAPI, Starlette, pytest, vanilla JS frontend. Run Python via `.venv\Scripts\python.exe`.

## Global Constraints

- Flag truthiness set is `{"1", "true", "yes"}` (case-insensitive), matching the existing `SESSION_COOKIE_SECURE` pattern in `app/main.py`.
- `AI_FEATURES_ENABLED` defaults to **false** (AI off).
- `ANTHROPIC_API_KEY` must be **optional** — the app boots and serves fully without it.
- Do **not** delete AI code (`app/essay/`, `app/resume/`, `app/llm.py`, AI models). Keep dormant.
- Do **not** rebrand in this phase — keep the "Scholarships4U" name (rename is Phase 2).
- Keep the full test suite green (currently 195 passing).
- Commit as the repo owner; do NOT add a Claude co-author trailer.

---

### Task 1: Backend AI flag + 404 gate on the four AI routes

**Files:**
- Modify: `app/main.py` (add flag helpers after line ~104; add gate dependency to routes at lines 269, 298, 327, 375)
- Create: `tests/test_ai_gating.py`
- Modify: `tests/test_essay_advice.py`, `tests/test_program_advice.py`, `tests/test_resume.py` (autouse fixture to enable AI)

**Interfaces:**
- Consumes: `os`, `HTTPException`, `Depends` (already imported in `app/main.py`); `_essay_limit`, `_resume_limit` (existing rate-limit deps).
- Produces:
  - `_ai_features_enabled() -> bool`
  - `require_ai_features() -> None` (FastAPI dependency; raises `HTTPException(404)` when disabled)

- [ ] **Step 1: Write the failing test**

Create `tests/test_ai_gating.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_routes_return_404_when_disabled(monkeypatch):
    monkeypatch.delenv("AI_FEATURES_ENABLED", raising=False)
    for path in ("/essay-advice", "/essay-review", "/program-advice"):
        r = client.post(path, json={})
        assert r.status_code == 404, f"{path} -> {r.status_code}"
    r = client.post("/resume/extract", data={"text": "hi"})
    assert r.status_code == 404


def test_homepage_ok_when_ai_disabled(monkeypatch):
    monkeypatch.delenv("AI_FEATURES_ENABLED", raising=False)
    assert client.get("/").status_code == 200


def test_app_serves_without_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert client.get("/health").status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -v`
Expected: FAIL — the AI routes currently return 422 (missing body) / other, not 404.

- [ ] **Step 3: Add the flag helpers**

In `app/main.py`, immediately after the `SESSION_COOKIE_SECURE = ...` line (~line 104), add:

```python
def _ai_features_enabled() -> bool:
    """AI-backed endpoints (essay/program advice, resume parsing) are gated off
    by default; set AI_FEATURES_ENABLED=true to serve them."""
    return os.getenv("AI_FEATURES_ENABLED", "").lower() in {"1", "true", "yes"}


def require_ai_features() -> None:
    """FastAPI dependency: hide AI routes (404) unless the feature flag is on."""
    if not _ai_features_enabled():
        raise HTTPException(
            status_code=404,
            detail={"error": "This feature is not available."},
        )
```

- [ ] **Step 4: Add the gate to each AI route**

In `app/main.py`, prepend `Depends(require_ai_features)` to the `dependencies` list of all four AI routes:

- `/essay-advice` (line 269): `dependencies=[Depends(require_ai_features), Depends(_essay_limit)]`
- `/essay-review` (line 298): `dependencies=[Depends(require_ai_features), Depends(_essay_limit)]`
- `/program-advice` (line 327): `dependencies=[Depends(require_ai_features), Depends(_essay_limit)]`
- `/resume/extract` (line 375): `dependencies=[Depends(require_ai_features), Depends(_resume_limit)]`

- [ ] **Step 5: Run the gating test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Keep the existing AI tests green by enabling the flag for them**

Add this autouse fixture to the top of EACH of `tests/test_essay_advice.py`, `tests/test_program_advice.py`, and `tests/test_resume.py` (after existing imports; add `import pytest` if not present):

```python
import pytest


@pytest.fixture(autouse=True)
def _enable_ai_features(monkeypatch):
    monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
```

- [ ] **Step 7: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: PASS (all tests; was 195, now +3 from `test_ai_gating.py`).

- [ ] **Step 8: Commit**

```bash
git add app/main.py tests/test_ai_gating.py tests/test_essay_advice.py tests/test_program_advice.py tests/test_resume.py
git commit -m "Gate AI features behind AI_FEATURES_ENABLED flag (default off)"
```

---

### Task 2: Expose the flag to the browser via serve_index

**Files:**
- Modify: `app/static/index.html` (add a meta tag with a placeholder in `<head>`)
- Modify: `app/main.py` (`serve_index`, ~line 178, replace the placeholder)
- Modify: `tests/test_ai_gating.py` (add two tests)

**Interfaces:**
- Consumes: `_ai_features_enabled()` from Task 1.
- Produces: a `<meta name="ai-features-enabled" content="true|false">` tag in the served homepage.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ai_gating.py`:

```python
def test_index_exposes_ai_flag_false_by_default(monkeypatch):
    monkeypatch.delenv("AI_FEATURES_ENABLED", raising=False)
    assert '<meta name="ai-features-enabled" content="false">' in client.get("/").text


def test_index_exposes_ai_flag_true_when_enabled(monkeypatch):
    monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
    assert '<meta name="ai-features-enabled" content="true">' in client.get("/").text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -k ai_flag -v`
Expected: FAIL — the meta tag does not exist yet.

- [ ] **Step 3: Add the meta placeholder to index.html**

In `app/static/index.html`, in `<head>` right after the `theme-color` meta (~line 23), add:

```html
  <meta name="ai-features-enabled" content="__AI_FEATURES_ENABLED__">
```

- [ ] **Step 4: Replace the placeholder in serve_index**

In `app/main.py`, in `serve_index` (~line 178), after the existing
`html = _absolute_og_image_urls(html, _public_base_url(request))` line, add:

```python
    html = html.replace(
        "__AI_FEATURES_ENABLED__", "true" if _ai_features_enabled() else "false"
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -k ai_flag -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add app/static/index.html app/main.py tests/test_ai_gating.py
git commit -m "Expose AI_FEATURES_ENABLED to the frontend via meta tag"
```

---

### Task 3: Hide the frontend AI UI when the flag is off

**Files:**
- Modify: `app/static/index.html` (resume-import section: add `id` + `hidden`, ~line 249)
- Modify: `app/static/js/app.js` (add `AI_ENABLED`; guard `wireResumeImport` and the three advice-button sites)
- Modify: `tests/test_ai_gating.py` (assert the resume section ships hidden)

**Interfaces:**
- Consumes: the `ai-features-enabled` meta tag from Task 2.
- Produces: `AI_ENABLED` (module-level boolean in `app.js`).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ai_gating.py` (add `import re` at the top of the file):

```python
def test_resume_import_section_ships_hidden():
    body = client.get("/").text
    assert re.search(
        r'<section[^>]*id="resume-import-section"[^>]*\bhidden\b', body
    ), "resume-import section must ship hidden; JS reveals it only when AI is on"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -k resume_import -v`
Expected: FAIL — the section has neither the id nor `hidden`.

- [ ] **Step 3: Mark the resume-import section hidden with an id**

In `app/static/index.html` (~line 249), change:

```html
    <section class="resume-import panel reveal-on-scroll" data-reveal-delay="135ms">
```
to:
```html
    <section class="resume-import panel reveal-on-scroll" id="resume-import-section" data-reveal-delay="135ms" hidden>
```

- [ ] **Step 4: Add the AI_ENABLED flag near the top of app.js**

In `app/static/js/app.js`, near the other top-level `const` declarations, add:

```javascript
const AI_ENABLED =
  document.querySelector('meta[name="ai-features-enabled"]')?.content === "true";
```

- [ ] **Step 5: Guard the resume import wiring**

In `app/static/js/app.js`, at the start of `wireResumeImport()` (~line 616), before it reads the file input / wires the button:

```javascript
function wireResumeImport() {
  if (!AI_ENABLED) return; // leave the resume-import section hidden and unwired
  const section = document.getElementById("resume-import-section");
  if (section) section.removeAttribute("hidden");
  // ...existing wiring below stays unchanged...
```

- [ ] **Step 6: Guard the three advice-button injection sites**

In `app/static/js/app.js`, wrap the creation-and-append of each advice/review control in `if (AI_ENABLED) { ... }` so no AI button renders when off:

- Program advice — around line 3228, the block that creates the advice button and calls `handleProgramAdvice(...)`.
- Essay advice — around line 3581, the block that creates the advice button and calls `handleEssayAdvice(...)`.
- Essay review — around line 3631, the block that builds the review form and calls `handleEssayReview(...)`.

For each, wrap from where the button/form element is created through its `appendChild`/insertion in:

```javascript
if (AI_ENABLED) {
  // ...existing button/form creation + append...
}
```

Leave the `handle*` function definitions (lines 3807, 3868, 3938) in place — they simply become unreachable when the flag is off.

- [ ] **Step 7: Run the section test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -k resume_import -v`
Expected: PASS.

- [ ] **Step 8: Manual browser verification**

Run: `.venv\Scripts\python.exe -m uvicorn app.main:app --port 8099`
- With AI off (default): load http://localhost:8099 — the resume-import section is absent, and no essay/program advice or review buttons appear on saved/tracked cards. No console errors.
- Then stop, set `AI_FEATURES_ENABLED=true` in `.env`, restart: the resume section and advice/review buttons appear.
Stop the server when done.

- [ ] **Step 9: Commit**

```bash
git add app/static/index.html app/static/js/app.js tests/test_ai_gating.py
git commit -m "Hide resume auto-fill and advice/review UI when AI features are off"
```

---

### Task 4: Remove AI claims from user-facing copy

**Files:**
- Modify: `app/static/index.html` (age-gate disclosure, ~lines 573-576)
- Modify: `tests/test_ai_gating.py` (assert no "Anthropic" in homepage)

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ai_gating.py`:

```python
def test_homepage_has_no_ai_provider_claims():
    body = client.get("/").text
    assert "Anthropic" not in body
    assert "AI features" not in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -k provider_claims -v`
Expected: FAIL — the age-gate paragraph mentions "AI features" and "Anthropic".

- [ ] **Step 3: Update the age-gate paragraph**

In `app/static/index.html` (~lines 573-576), replace:

```html
        Scholarships4U is a personal, educational project. The matcher uses the profile details you enter
        (including optional demographic and financial-need information), and the optional AI features send
        your inputs to Anthropic's API. Please review our
```
with:
```html
        Scholarships4U is a personal, educational project. The matcher uses the profile details you enter
        (including optional demographic and financial-need information). Please review our
```

- [ ] **Step 4: Verify no other visible AI-provider claims remain**

Run: `grep -niE "anthropic|AI feature|AI-powered|essay advice|essay review" app/static/index.html`
Expected: no matches referring to an active AI feature. (References inside the now-hidden resume section are acceptable; if any visible hero/CTA text advertises AI writing help, remove it in this step.)

- [ ] **Step 5: Run the claim test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_gating.py -k provider_claims -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/static/index.html tests/test_ai_gating.py
git commit -m "Remove AI-provider disclosure from homepage copy"
```

---

### Task 5: Document the flag and make the Anthropic key optional in config

**Files:**
- Modify: `.env.example`
- Modify: `render.yaml`

**Interfaces:**
- Consumes: nothing.
- Produces: documented config only.

- [ ] **Step 1: Document the flag in .env.example**

In `.env.example`, add (near the Anthropic key section):

```
# AI-backed help (essay/program advice, resume auto-fill) is OFF by default.
# Leave unset/false to run with zero AI API cost. Set true only when
# ANTHROPIC_API_KEY is configured. ANTHROPIC_API_KEY is optional while off.
# AI_FEATURES_ENABLED=false
```

- [ ] **Step 2: Add the flag to render.yaml**

In `render.yaml`, under the web service `envVars`, add:

```yaml
      - key: AI_FEATURES_ENABLED
        value: "false"
```

- [ ] **Step 3: Verify the suite is still green**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .env.example render.yaml
git commit -m "Document AI_FEATURES_ENABLED and make Anthropic key optional"
```

- [ ] **Step 5: Production follow-up (manual, outside the repo)**

In the Render dashboard (or the eventual host), set `AI_FEATURES_ENABLED=false`. The Anthropic key can be left unset. Redeploy.

---

## Notes for the executor
- Hosting-agnostic: nothing here depends on Render vs. any other host (Task 5's `render.yaml` edit is just documentation of the same flag).
- If the concurrent dataset agent is running, coordinate/pause it to avoid `main` collisions during commits.
