# EnsureCollege — working agreement

College-planning web app for U.S. high-school students (FastAPI + vanilla JS, Vercel + Neon).
Read [CONTEXT.md](CONTEXT.md) for the domain vocabulary — use those terms exactly; they are not interchangeable with synonyms.

## How feature work happens here

**Any non-trivial feature or change starts with a plan, and the plan gets hardened before code is written.**

1. **Plan** — invoke `/grill-with-docs-codex`. Act 1 interviews the user and challenges the idea against CONTEXT.md; Act 2 hands the plan to OpenAI Codex, which adversarially reviews it read-only until it returns `VERDICT: APPROVED` or rounds run out. The user signs off before any code.
   - Already have a plan and only want the cross-model review? `/codex-review`.
   - Want the second model to *write* the code from the frozen plan? `/codex-build` (needs a clean git tree; Claude reviews the diff and runs the proof test).
2. **Build** — Claude implements, or Codex does via `/codex-build`. Either way the plan is the contract.
3. **Verify** — run the proof command below. Evidence before claims.

**Skip the grill for:** typo fixes, copy tweaks, dataset entry edits, dependency bumps, anything obviously cheap to revert.
**Never skip it for:** auth, session/cookie handling, the matcher's gates or scoring, database schema/migrations, the digest cron, or anything touching student data.

### Plan artifacts

This repo already keeps plans in `docs/`, dated and paired:
- `docs/YYYY-MM-DD-<feature>-design.md` — the design/exploration
- `docs/YYYY-MM-DD-<feature>.md` — the implementation plan

Point the skills at those paths rather than a root `PLAN.md`:
`/grill-with-docs-codex plan=docs/2026-07-12-<feature>.md` (the round-by-round Codex argument lands in `PLAN-REVIEW-LOG.md`).

## Installed tooling (OMC, Neon MCP, context7)

Newer tooling exists in this environment; here is how it interacts with the rules above.

1. **The plan-hardening chain overrides OMC routing.** oh-my-claudecode's autopilot/ralph/executor
   orchestration does not replace the grill → codex-review → codex-build chain described above.
   For anything the chain covers, OMC agents may *implement* only after the human has signed off
   on an approved plan — never plan-and-build autonomously.
2. **Neon MCP is read-only against prod** (`.mcp.json` → `https://mcp.neon.tech/mcp`). Before any
   deploy, compare prod's `alembic_version` against the repo's migration head and report drift.
   Schema changes must be rehearsed on a Neon branch before touching `main` — the 0006–0008
   migration history (see Non-negotiables) is why this rule exists.
3. **Consult context7 first for framework API questions.** For FastAPI/SQLAlchemy/Alembic API
   usage, query the context7 MCP docs before implementing rather than relying on trained knowledge.

## Non-negotiables

These are the ways this project has actually been broken before. A plan that violates one of them should be rejected in review.

- **Data honesty over completeness.** A `VERIFY` placeholder means "we don't know," never "no requirement." The matcher must never gate on it. A wrong deadline in a student-facing tool is worse than an honest blank. Never invent, infer, or backfill a sponsor fact that isn't on the sponsor's official page.
- **Migrations do not auto-apply in production.** Vercel runs Alembic at *build* time (`RUN_MIGRATIONS_ON_STARTUP=false`). A schema change is not live until it is applied against Neon. Migrations 0006/0007/0008 were never applied, and 0008 took auth down on 2026-07-08. Any plan touching `app/db/` must state explicitly how and when the migration reaches Neon.
- **AI features stay dormant.** `AI_FEATURES_ENABLED` defaults to `false`. Do not re-enable, and do not route student data to any AI provider, unless a plan says so and the user signs off.
- **Never commit secrets.** `.env` is gitignored; `.env.example` documents names only. Do not put real values in committed docs (including handoff files).
- **Special checks are not Strong matches.** Niche gates the profile can't verify (nomination, membership, finalist, first-gen-only) surface in the special-check lane. Don't quietly promote them.
- **The DOM contract is frozen.** `app.js` depends on ~184 selectors, their `data-*` values, element types, form field names, and the class names it emits. `tests/dom_contract.json` is the manifest and `tests/test_dom_contract.py` enforces it. Restructuring markup means updating the manifest deliberately, never silently.
- **Cache-bust in lockstep.** The asset `?v=` string appears in `app/static/index.html`, `journey.html`, `privacy.html`, `terms.html`, `app/templates/base.html`, and `tests/test_pages.py`. Bump them together, or returning visitors get a stale mix.
- **The landing page inlines its CSS.** `main.py::_inline_css` injects the stylesheet into `/` to keep the render-blocking request off the mobile critical path (LCP 2.46s, gate is 2.5s). Other pages use the cached external file. Don't "tidy" this back into a `<link>` without re-measuring.

## Commands

```bash
# dev server — 8099 is canonical; local Google OAuth expects it
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8099

# proof: BOTH suites. This is what counts as verification.
python -m pytest tests/ --ignore=tests/e2e -v   # 369 request tests, externals mocked
python -m pytest tests/e2e                      # 39 browser tests (Playwright, ~2 min)

# dataset integrity — exits non-zero on structural errors
python scripts/validate_dataset.py
```

**Any change to the frontend must be proven in the browser suite, not just the
request suite.** The request tests cannot see a dead event listener, a stranded
scroll, a hidden-but-laid-out tooltip, or a WebGL page that never paints; the
E2E suite has already caught all of those. Add a test to `tests/e2e/` for every
UI bug you fix.

## Git

Commit and push as the user only. **Do not add a `Co-Authored-By: Claude` trailer** to commits in this repo.
