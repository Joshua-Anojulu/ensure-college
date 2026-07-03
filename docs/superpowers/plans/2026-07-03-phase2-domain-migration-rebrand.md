# Phase 2: Domain Migration + Full Visual Rebrand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. NOTE: Group A (brand assets) is design work run via the `design` skill by the controller, not a code subagent.

**Goal:** Rebrand Scholarships4U → EnsureCollege (name + full visual identity) and migrate the live site to ensurecollege.com, with a permanent 301 redirect from scholarships4u.dev.

**Architecture:** New brand assets (logo, favicon, OG images) are generated to a brand spec, then swapped in. User-facing brand strings and domain URLs are updated across the app (backend + static), while internal identifiers are deliberately left unchanged. A Host-based redirect middleware sends old-domain traffic to the new domain. Infra steps (DNS, host domain, Resend, OAuth, env vars) are a user dashboard checklist, since they can't be done from code.

**Tech Stack:** FastAPI, Starlette middleware, vanilla-JS frontend, Resend email, Render hosting. Run Python via `.venv\Scripts\python.exe`.

## Global Constraints

- New brand name string is exactly **EnsureCollege** (one word, camelCase). New domain is **ensurecollege.com** (apex, https).
- **Do NOT rename these internal identifiers** (not user-facing; renaming risks breakage or churn): the local SQLite filename `scholarships4u.db` (`app/db/database.py`, `alembic.ini`), the Render blueprint resource names in `render.yaml`, and the `SCHOLARSHIPS4U_URL` env var name in `scripts/`. Leave them; add a one-line comment only where it aids a future reader.
- Keep scholarships4u.dev registered; it 301-redirects to ensurecollege.com (permanent).
- Preserve the existing visual system's bones unless the brand spec (Task A1) says otherwise: primary indigo `#4f46e5`, light canvas `#f5f7fb`, dark canvas `#0b0e16`, fonts Plus Jakarta Sans (display) + Inter (body).
- Keep the full test suite green (currently 203). Update tests whose assertions encode the old brand/domain; do not delete coverage.
- Commit as the repo owner (Claude co-author trailer is acceptable on this repo).
- No AI features are re-enabled in this phase (`AI_FEATURES_ENABLED` stays off).

---

## Group A — Brand Identity + Assets (run via the `design` skill)

### Task A1: Define the EnsureCollege brand identity spec

**Files:**
- Create: `docs/brand/ensurecollege-brand.md`

**Interfaces:**
- Produces: the brand spec (name, tagline, palette, fonts, logo/mark concept, asset sizes) that Tasks A2, A3, and Group B consume.

- [ ] **Step 1: Write the brand spec** capturing (proposed, adjust with user):
  - Name: **EnsureCollege**. Tagline: **"Your whole college plan, in one place."**
  - Palette: keep primary indigo `#4f46e5`, light canvas `#f5f7fb`, dark canvas `#0b0e16`; add a supporting accent only if needed.
  - Fonts: Plus Jakarta Sans (display) + Inter (body) — unchanged.
  - Mark concept: replace the single-letter "S" tile with an **"ensure" motif — a rounded shield containing a checkmark**, in the indigo tile style already used in the header/email.
  - Assets required (produced in A2/A3): `favicon.svg`; `og-image.png` (1200×630 light) + `og-image.svg`; `og-image-dark.png` (1200×630) + `og-image-dark.svg`.
- [ ] **Step 2: Commit** `git add docs/brand/ensurecollege-brand.md && git commit -m "Add EnsureCollege brand identity spec"`

### Task A2: Generate the logo/mark + favicon

**Files:**
- Replace: `app/static/favicon.svg`
- Create (working): brand mark SVG used by A3 and the in-app header

**Interfaces:**
- Consumes: `docs/brand/ensurecollege-brand.md`.
- Produces: `favicon.svg` (shield+check mark, indigo), and a header mark usable inline in `index.html`/email.

- [ ] **Step 1:** Using the `design` skill (icon/logo generation), produce the shield+check mark per A1 as clean SVG at favicon dimensions; save to `app/static/favicon.svg`.
- [ ] **Step 2:** Visually verify the SVG renders at 16/32/180px (open in browser); confirm it reads at small sizes.
- [ ] **Step 3: Commit** `git add app/static/favicon.svg && git commit -m "Add EnsureCollege favicon/mark"`

### Task A3: Generate OG/social images (light + dark)

**Files:**
- Replace: `app/static/og-image.png`, `app/static/og-image.svg`, `app/static/og-image-dark.png`, `app/static/og-image-dark.svg`

**Interfaces:**
- Consumes: A1 spec + A2 mark.
- Produces: 1200×630 OG images (light + dark) branded EnsureCollege.

- [ ] **Step 1:** Using the `design` skill (social image via HTML→screenshot), build a 1200×630 layout: EnsureCollege wordmark + mark, tagline, trust-SaaS style matching the site. Render light and dark variants to PNG; keep the SVG sources.
- [ ] **Step 2:** Verify each PNG is exactly 1200×630 and visually correct.
- [ ] **Step 3: Commit** `git add app/static/og-image*.png app/static/og-image*.svg && git commit -m "Add EnsureCollege OG/social images"`

---

## Group B — Rebrand strings + swap assets in the app (code)

### Task B1: Rebrand the static frontend (HTML/CSS/JS)

**Files:**
- Modify: `app/static/index.html`, `app/static/privacy.html`, `app/static/terms.html`, `app/static/js/app.js`, `app/static/css/style.css`
- Test: `tests/test_pages.py`, `tests/test_api.py`

**Interfaces:**
- Consumes: new assets (A2/A3).
- Produces: served pages branded EnsureCollege.

- [ ] **Step 1: Update the failing brand assertions first (TDD).** In `tests/test_api.py:62` change `assert "Scholarships4U" in response.text` → `assert "EnsureCollege" in response.text`. In `tests/test_pages.py:62-65` change the four `scholarships4u.dev` URLs to `ensurecollege.com` (og:url + three canonicals).
- [ ] **Step 2: Run those tests to verify they fail**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_api.py tests/test_pages.py -q`
  Expected: FAIL (pages still say Scholarships4U / old domain).
- [ ] **Step 3: Replace brand + domain in the static files.** In `index.html`, `privacy.html`, `terms.html`: replace every visible "Scholarships4U" → "EnsureCollege"; replace `https://scholarships4u.dev` → `https://ensurecollege.com` in `og:url` and `rel="canonical"`; update `<title>` and meta/OG text. In `app.js` and `style.css`: replace "Scholarships4U" in comments/UI strings. Keep the same markup structure.
- [ ] **Step 4: Run the tests to verify they pass**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_api.py tests/test_pages.py -q`
  Expected: PASS.
- [ ] **Step 5: Verify no residual old brand in served static pages**
  Run: `grep -rniI "scholarships4u" app/static/*.html app/static/js app/static/css`
  Expected: no user-facing matches remain (asset filenames `og-image*` are unchanged by design).
- [ ] **Step 6: Commit** `git add app/static tests/test_api.py tests/test_pages.py && git commit -m "Rebrand static frontend to EnsureCollege"`

### Task B2: Rebrand backend user-facing strings (email, ICS, app title, download name)

**Files:**
- Modify: `app/auth/email.py`, `app/ics.py`, `app/api/account_routes.py:151`, `app/main.py:157`
- Test: `tests/test_ics.py`

**Interfaces:**
- Produces: EnsureCollege-branded reset email, ICS calendar, and download filename.

- [ ] **Step 1: Update ICS test assertions first (TDD).** In `tests/test_ics.py`: change `X-WR-CALNAME:Scholarships4U verified deadlines` → `X-WR-CALNAME:EnsureCollege verified deadlines`, and the `@scholarships4u` UID suffix assertions (lines 16-17, 27) → `@ensurecollege`.
- [ ] **Step 2: Run to verify they fail**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_ics.py -q`  → FAIL.
- [ ] **Step 3: Update the backend strings:**
  - `app/ics.py`: `_PRODID` "Scholarships4U" → "EnsureCollege"; `X-WR-CALNAME` → "EnsureCollege verified deadlines"; UID suffix `@scholarships4u` → `@ensurecollege`.
  - `app/auth/email.py`: all visible "Scholarships4U" → "EnsureCollege"; footer `scholarships4u.dev` → `ensurecollege.com`; subject/body strings; and the `User-Agent` header (line 129) → `"EnsureCollege/1.0 (+https://ensurecollege.com)"` (keep it a valid non-default UA — the Cloudflare fix from Phase-1 relies on a non-`urllib` UA).
  - `app/api/account_routes.py:151`: filename `scholarships4u-deadlines.ics` → `ensurecollege-deadlines.ics`.
  - `app/main.py:157`: FastAPI `title="Scholarships4U"` → `title="EnsureCollege"`.
- [ ] **Step 4: Run tests to verify they pass**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_ics.py -q`  → PASS.
- [ ] **Step 5: Full suite**
  Run: `.venv\Scripts\python.exe -m pytest tests/ -q`  → all pass.
- [ ] **Step 6: Commit** `git add app/auth/email.py app/ics.py app/api/account_routes.py app/main.py tests/test_ics.py && git commit -m "Rebrand backend user-facing strings to EnsureCollege"`

---

## Group C — Domain config + redirect (code)

### Task C1: Update config/docs and scripts to the new domain/brand

**Files:**
- Modify: `.env.example`, `render.yaml` (comment/text only — NOT the resource names), `scripts/smoke_test_live.py`, `scripts/capture_readme_screenshots.py`, `README.md`

**Interfaces:**
- Produces: docs/scripts that reference ensurecollege.com.

- [ ] **Step 1:** In `.env.example`: `EMAIL_FROM` example → `"EnsureCollege <no-reply@mail.ensurecollege.com>"`; `PUBLIC_APP_URL` example → `https://ensurecollege.com`; OAuth redirect comment → `https://ensurecollege.com/auth/google/callback`.
- [ ] **Step 2:** In `scripts/smoke_test_live.py` and `scripts/capture_readme_screenshots.py`: change the DEFAULT URL value `https://scholarships4u.dev` → `https://ensurecollege.com`. Leave the `SCHOLARSHIPS4U_URL` env var NAME unchanged (internal; per Global Constraints).
- [ ] **Step 3:** In `render.yaml`: update only the human-readable comment (line 3) and any brand text; leave `name:` resource identifiers unchanged. In `README.md`: replace visible "Scholarships4U" → "EnsureCollege" and old domain → new domain.
- [ ] **Step 4:** No test asserts these; verify by `grep -rniI "scholarships4u.dev" .env.example scripts README.md render.yaml` shows only intended remnants (none).
- [ ] **Step 5: Commit** `git add .env.example render.yaml scripts README.md && git commit -m "Point docs and scripts at ensurecollege.com"`

### Task C2: Add a 301 redirect from the old domain to the new one

**Files:**
- Modify: `app/main.py` (add a Host-based redirect middleware)
- Test: `tests/test_pages.py` (or a new `tests/test_redirect.py`)

**Interfaces:**
- Consumes: nothing.
- Produces: any request with `Host` of `scholarships4u.dev`/`www.scholarships4u.dev` gets a 301 to `https://ensurecollege.com<path>`.

- [ ] **Step 1: Write the failing test.** In a new `tests/test_redirect.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_old_domain_redirects_permanently():
    r = client.get("/terms", headers={"host": "scholarships4u.dev"}, follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"] == "https://ensurecollege.com/terms"


def test_new_domain_not_redirected():
    r = client.get("/health", headers={"host": "ensurecollege.com"}, follow_redirects=False)
    assert r.status_code == 200
```

- [ ] **Step 2: Run to verify it fails**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_redirect.py -q`  → FAIL (no redirect yet).
- [ ] **Step 3: Implement the middleware** in `app/main.py`, registered alongside the other `app.add_middleware(...)` / `@app.middleware` code (place BEFORE `SecurityHeadersMiddleware` so redirects are cheap):

```python
_OLD_HOSTS = {"scholarships4u.dev", "www.scholarships4u.dev"}


@app.middleware("http")
async def _redirect_old_domain(request: StarletteRequest, call_next):
    host = request.headers.get("host", "").split(":")[0].lower()
    if host in _OLD_HOSTS:
        target = f"https://ensurecollege.com{request.url.path}"
        if request.url.query:
            target += f"?{request.url.query}"
        return Response(status_code=301, headers={"Location": target})
    return await call_next(request)
```

(`Response` and `StarletteRequest` are already imported in `app/main.py`.)

- [ ] **Step 4: Run the test to verify it passes**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_redirect.py -q`  → PASS.
- [ ] **Step 5: Full suite**
  Run: `.venv\Scripts\python.exe -m pytest tests/ -q`  → all pass.
- [ ] **Step 6: Commit** `git add app/main.py tests/test_redirect.py && git commit -m "301-redirect scholarships4u.dev to ensurecollege.com"`

---

## Group D — User dashboard checklist (NOT agent tasks — you do these)

These cannot be done from code. Do them around the code deploy:

- [ ] **Render → Settings → Custom Domains:** add `ensurecollege.com` and `www.ensurecollege.com`; create the DNS records Render shows at your registrar (apex A record to Render's IP; `www` CNAME to the `*.onrender.com` host). Wait for TLS to issue.
- [ ] **Also add `scholarships4u.dev` + `www` as custom domains on the same Render service** so the redirect middleware (C2) receives old-domain traffic. Keep the domain registered.
- [ ] **Set env var** `PUBLIC_APP_URL=https://ensurecollege.com` in Render → redeploy. (Drives sitemap, robots, and password-reset links.)
- [ ] **Resend → Domains:** add and verify `mail.ensurecollege.com` (SPF, DKIM, DMARC). Set env `EMAIL_FROM="EnsureCollege <no-reply@mail.ensurecollege.com>"`.
- [ ] **Google Cloud → OAuth client:** add `https://ensurecollege.com/auth/google/callback` (and `https://www.ensurecollege.com/auth/google/callback`) to Authorized redirect URIs. Remove the old ones after cutover.
- [ ] **Google Search Console:** add ensurecollege.com as a property; submit `https://ensurecollege.com/sitemap.xml`.
- [ ] **After cutover verify:** load https://ensurecollege.com (loads, TLS valid, EnsureCollege branding, new OG image via a link-preview debugger); hit https://scholarships4u.dev/terms and confirm a 301 to the new domain; run a password reset and confirm the email is EnsureCollege-branded from the new domain.

---

## Self-review notes
- Spec §4 coverage: DNS/domain (Group D) ✓, PUBLIC_APP_URL (D) ✓, Resend domain (D) ✓, OAuth (D) ✓, 301 redirect (C2) ✓, rebrand sweep (A + B + C1) ✓, OG/favicon regen (A2/A3) ✓, Search Console (D) ✓.
- Internal identifiers intentionally excluded from the rename per Global Constraints (documented, not an oversight).
- Canonical/OG URLs are currently hardcoded in the static HTML (not templated), so B1 updates them directly and the tests lock the new values.
