# EnsureCollege — All-in-One College Helper (Design Spec)

Date: 2026-07-03
Status: Approved for planning
Repo: scholarship-matcher (served today at scholarships4u.dev)

## 1. Vision & Positioning

Evolve the current Scholarships4U app into **EnsureCollege**, an all-in-one
college-preparation helper. The product keeps its proven core — transparent,
explainable matching plus a planning layer (deadline/calendar tracking, the
requirement matrix, application guidance) — and broadens from scholarships and
summer programs to also cover **competitions**.

Positioning: trustworthy, deterministic, zero-fluff college guidance. The site
is marketed on its non-AI "moats" (transparent matching, requirement matrix,
deadline tracking, application guidance), which have **zero marginal cost per
user**. AI-assisted writing help is deferred (see Phase 1).

Non-goals (YAGNI for now): monetization/billing, a college-search or
application-tracker vertical, and a unified "opportunity" engine refactor. These
are backlog items, revisited after the three phases below land.

## 2. Sequenced Roadmap

1. **Phase 1 — Remove AI features + reposition.** Fast; eliminates the API scale
   cost immediately and de-risks the launch.
2. **Phase 2 — Migrate to ensurecollege.com + rebrand.** Fast; establishes a
   broad, trustworthy brand before wider marketing.
3. **Phase 3 — Competitions vertical.** The major feature; mirrors the existing
   programs architecture. Gets its own detailed implementation plan.

The first implementation plan produced after this spec covers **Phase 1**.
Phases 2 and 3 are specified here at enough depth to sequence and estimate, and
each will get its own implementation plan when reached.

## 3. Phase 1 — Remove AI Features

### 3.1 Scope
The only Anthropic-backed surfaces in the app are four endpoints and their UI:

| Route | Handler | AI helper |
|-------|---------|-----------|
| `POST /essay-advice`  | `essay_advice`  | `generate_essay_advice` |
| `POST /essay-review`  | `essay_review`  | `generate_essay_review` |
| `POST /program-advice`| `program_advice`| `generate_program_advice` |
| `POST /resume/extract`| resume extract  | `extract_profile_from_resume` |

Decision (approved): **resume auto-fill is removed along with the essay/program
AI features.** Users enter their profile manually. This keeps the "no AI" story
consistent and removes the last Anthropic dependency from the request path.

### 3.2 Behaviour
- Introduce a single feature flag `AI_FEATURES_ENABLED` (env var, default
  **false**). Read it once at startup, like the other env-driven config in
  `app/main.py`.
- When the flag is false:
  - The four AI routes are **not registered** (a request returns 404). Not
    registering is preferred over in-handler guards so the disabled surface is
    invisible and carries no code path at runtime.
  - The AI UI entry points are removed from `app/static/index.html` and
    `app/static/js/app.js` (essay advice, essay review, program advice, resume
    upload/auto-fill). Manual profile entry remains the path.
  - `ANTHROPIC_API_KEY` is **optional** — the app boots and runs fully without it.
- When the flag is true, behaviour is exactly as today (for future re-enablement).
- The AI code (`app/essay/`, `app/resume/`, `app/llm.py`, related models) stays
  in the tree but dormant. Nothing is deleted; re-enablement is flipping the flag.

### 3.3 Repositioning
- Update homepage copy to lead with transparent matching, the requirement
  matrix, deadline tracking, and application guidance. Remove AI/essay-writing
  claims from `index.html`, meta description, and OG text.
- Ensure no dead UI (buttons/links) points at the disabled routes.

### 3.4 Testing
- AI-specific tests (`test_essay_advice`, `test_program_advice`, `test_resume`)
  run only when `AI_FEATURES_ENABLED` is true (skip/guard otherwise), so the
  default suite is green with AI off.
- Add tests asserting the four routes return 404 when the flag is off, and that
  the app starts with no `ANTHROPIC_API_KEY` set.
- Full suite stays green in both flag states.

### 3.5 Config / docs
- Document `AI_FEATURES_ENABLED` in `.env.example` and `render.yaml`.
- In production (Render), set `AI_FEATURES_ENABLED=false` and remove/ignore the
  Anthropic key from the request path.

## 4. Phase 2 — Domain Migration + Rebrand

Because public URLs already derive from `PUBLIC_APP_URL`
(`_public_base_url` in `app/main.py`), canonical tags, OG URLs, `sitemap.xml`,
`robots.txt`, and password-reset links update automatically when the env var
changes. Steps:

1. Purchase `ensurecollege.com`. Add it and `www.ensurecollege.com` as custom
   domains in Render; configure the DNS records Render provides; wait for the
   managed TLS certificate to issue.
2. Set `PUBLIC_APP_URL=https://ensurecollege.com` in Render and redeploy.
3. Add and verify a Resend sending domain (e.g. `mail.ensurecollege.com`) with
   SPF, DKIM, and DMARC records; update `EMAIL_FROM` to an address on it.
4. Add `https://ensurecollege.com/auth/google/callback` to the Google OAuth
   client's authorized redirect URIs (keep the old one until cutover is done).
5. Add a **301 redirect** from `scholarships4u.dev` to `ensurecollege.com` to
   preserve SEO and existing links.
6. **Rebrand pass** — replace "Scholarships4U" with "EnsureCollege" across
   `index.html`, `privacy.html`, `terms.html`, the reset-email template
   (`app/auth/email.py`), OG images, favicon, `<title>`/meta, and `README.md`.
   This copy/asset work is the bulk of Phase 2's effort.
7. Regenerate OG/social images and favicon for the new brand.
8. Update `.env.example` and `render.yaml` references.
9. Re-submit the new domain to Google Search Console and update the sitemap
   submission.

Caution on brand copy: avoid language that implies a *guaranteed* admission
outcome (legal/trust risk given the "ensure" name).

## 5. Phase 3 — Competitions Vertical

### 5.1 Approach (approved: Option A)
Mirror the existing **programs** pattern with a parallel competitions module.
This is consistent with the current codebase and lowest-risk. A unified
"opportunity" engine (Option B) is explicitly deferred to backlog; revisit once
three verticals exist to generalize from.

### 5.2 Components (parallel to summer programs)
- `app/models/competition.py` — a `Competition` model: `id`, `name`, `sponsor`,
  `category` (e.g. science, math, writing, business, debate, hackathon, arts),
  `eligibility` (grade level, age, citizenship), `deadline`, `url`, `recognition`
  /award, `format` (individual/team), `cost`, `description`, `verified`,
  `verification`, `application_requirements`. Field shapes follow the existing
  program/scholarship models, including the `VERIFY` placeholder convention.
- `app/data/competitions.json` — curated dataset with a `_dataset_notice` and
  the same VERIFY discipline (never fabricate; cite official sources in
  `verification`).
- `app/data/loader.py` — add `load_competitions()`.
- Competitions matcher — adapt the existing program matcher's scoring; keep the
  transparent, explainable scoring and eligibility-caveat behaviour.
- Routes `GET /competitions` and `POST /competitions/match`, registered like the
  programs routes; load into `app.state` on startup.
- UI — a new vertical tab in the nav and a results lane, reusing the requirement
  matrix, calendar/ICS deadline export, and saved-items features.
- `scripts/validate_dataset.py` and `tests/test_dataset.py` — extend to validate
  the competitions dataset and count its placeholders.

### 5.3 Seed dataset (examples)
ISEF / Regeneron STS, AMC/AIME/USAMO, Congressional App Challenge, DECA, FBLA,
NSDA debate, Scholastic Art & Writing Awards, national hackathons, and national
essay contests. Every record sourced from an official page.

## 6. Risks & Notes
- **Concurrent dataset agent:** a separate agent has been committing dataset
  verification to `main` as the repo owner. Coordinate/pause it during phases
  that touch data files or git history to avoid collisions.
- **Brand rename surface area:** "Scholarships4U" appears across many files;
  treat the rebrand as a deliberate sweep, not a one-line change.
- **Re-enabling AI later:** the flag + dormant code make this a config flip, but
  any future paid/BYO-key model is out of scope here and will need its own spec.
```
