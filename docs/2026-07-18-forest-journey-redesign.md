# Plan: the Forest-Journey site-wide redesign (rev 3)
_Locked via grill-with-docs — by Claude + Josh, 2026-07-18. Terms per CONTEXT.md. Design dials 9/8/4 (house-style). Rev 3 after Codex rounds 1-2 (REVISE)._

## Goal

Turn EnsureCollege into one cohesive, immersive illustrated "forest-journey"
world across **every** surface — the Hack-the-North kind of cohesion — building
on the existing **Forest Light** system rather than replacing it. Every surface
becomes a full illustrated scene with working content riding in legible,
high-contrast panels over it (the "stage + panel" pattern; see
[ADR 0001](adr/0001-immersive-illustration-on-a-utility.md)). The centerpiece is
a new **Journey map**: a 2D illustrated dotted-path progress map personalized
from the student's real [[Status]] data on the saved-applications view, with a
labeled generic sample on marketing surfaces. The 3D [[Journey]] is reskinned,
not replaced. Released **big-bang** off a branch — but proven on a **Phase 0
spike** first, because the two riskiest unknowns (LCP and the DOM/behavior
contract) must be validated on two surfaces before all eleven are touched.

## Approach

### Phase 0 — spike (prove the thesis, or fall back before we're all-in)
Build ONLY the landing hero + the saved-applications **Journey map** on the
branch. Prove, on real hardware/preview:
- mobile **LCP < 2.5s on the landing** against the budget below;
- the **DOM/behavior** contract holds (semantic tests, not just selector
  existence);
- e2e green.
If the immersive-everywhere landing cannot hit the LCP gate here, we fall back
per ADR 0001 (immersive narrative surfaces, motif-framed tool surfaces) **before**
touching the remaining surfaces. Phase 0 is the go/no-go on the core bet.

### LCP budget (hard, not "optimized")
- **No new render-blocking request on the landing.** Critical CSS stays inlined
  via `main.py::_inline_css`; no new blocking `<link>`/`<script>` in the head.
- **CSS growth cap:** the inlined stylesheet may grow by at most a fixed budget
  (set the exact KB in Phase 0 from the measured baseline); **no scene art as
  data-URIs inside `style.css`** (that inflates the render-blocking payload).
- **At most one** small, `preload`ed mobile hero asset, and only if it is the
  measured LCP element. Every other illustration is lazy (`loading="lazy"`,
  `decoding="async"`) with explicit width/height to hold CLS < 0.1.
- Modern formats (AVIF/WebP) with responsive `srcset`; the mobile hero byte
  target is fixed in Phase 0.
- **JS / main-thread budget** (CSS + image budgets alone do not protect LCP/TBT).
  `app.js` is a synchronous body-end script with eager init, so: the Journey-map
  code has a byte cap set in Phase 0; **no eager SVG/DOM construction of the map
  before first paint** — it lazy-inits when the saved view is shown or via
  `requestIdleCallback`; Phase 0 records TBT alongside LCP as evidence.
- **Deterministic measurement protocol** (40ms of headroom means a loose "run
  Lighthouse" is not a gate): run Lighthouse mobile (pinned tool version, its
  default mobile throttling profile) against the **Vercel preview URL**, **median
  of 3 runs must be < 2.5s AND no single run over 2.7s**. This exact protocol is
  the Phase 0 go/no-go and the pre-merge release gate.

### The mockup gate proves shippability, not just aesthetics
Each per-surface mockup is signed off only when it carries: a mobile comp, an
asset inventory, the intended LCP element, a byte target + format, the
preload-vs-lazy decision per asset, and the reduced-motion/static fallback. A
pretty image that cannot meet the budget is not an approved mockup.

### Phase 1 — fan out (only after Phase 0 passes)
Re-skin the remaining surfaces, **skin only**: `index.html` (landing + the
matcher/saved SPA tab states), `journey.html`, `browse.html`, `browse_index.html`,
`detail.html`, `guide.html`, `guides_index.html`, `privacy.html`, `terms.html`,
`404.html`, `base.html`. Content rides in legible panels over illustrated stages.
Re-skin `journey.js`'s 3D scenes to the new palette/motifs (keep its perf-gate
and reduced-motion fallback). Dials 9/8/4; density stays low.

### Preserve exactly (skin only) — enforced by tests, not intent
- **Frozen unless `app.js` changes intentionally:** every existing element id,
  `data-view`/`data-step`/`data-*` value, form field `name`, and emitted class
  the contract tracks. The DOM contract checks *existence*; behavior does not
  come free — so add semantic Playwright tests for tab switching, the 3-step
  profile form, `.card-body` containment, overlay/tooltip clickability, and
  saved-**Status** updates re-rendering the Journey map.
- **SEO golden tests (request-level):** assert head tags (canonical, OG, meta
  description, title) AND the visible verification / estimated-deadline / source
  blocks on one scholarship, one program, one competition Opportunity page, plus
  JSON-LD presence and escaping. `seo_pages.py` output must not silently drift.
- **Legal/age-gate copy:** snapshot-hash privacy, terms, the footer disclaimer,
  and any age-gate string; a changed hash forces an intentional, reviewed diff
  (replaces the current weak "13"/"sponsor" substring checks).

### The Journey map — one state function, all lanes, explicit edge cases
- **`computeJourneyMapState(profile, lastResults, saved, programs, competitions)`**
  is the single source of the map's state, aggregating **all three lanes**
  (`/account/saved` returns scholarships + programs + competitions; `renderSaved`
  already merges them). Call it from the match flow, `renderSaved`, the tracker
  summary refresh, and every status-change handler so the map stays live.
- **Milestones:** profile (profile-progress complete) → matches (matcher run) →
  saved (count of **active** saved, i.e. excluding `rejected`) → drafting
  (`status=drafting`) → submitted (`status=submitted`) → awarded (the flag,
  `status=awarded`). `interested` is the default active-saved state.
- **Milestone independence / inconsistent session state:** each milestone reads
  its own source, so a stale or unrun session never lies. `profile` reflects
  profile-progress; `saved`/`drafting`/`submitted`/`awarded` read the persisted
  saved data and light **independently of `lastResults`** (a returning student
  with saved items but no match run this session still sees their real plan
  progress). The `matches` stop specifically reflects *this session*: if there
  are no current `lastResults` (match not run, or profile incomplete/legacy), it
  reads **"not run this session"** — never implying failure or zero matches.
- **Edge cases (explicit):** zero saved → an inviting empty/start state, not a
  dead path; **all-rejected** → path resets to "saved: 0 active" with rejected
  shown as a muted side count, never as progress; awarded-only / skipped stages
  → light the reached stages honestly; **unknown/legacy DB status** → ignored
  with a `console.warn`, never crashes the viz; **logged-out** → a sample map
  labeled "Sample" and shown only on marketing surfaces, never adjacent to a
  personal plan.
- `prefers-reduced-motion` → fully-drawn static map; asymmetric layout collapses
  cleanly below 768px.

### Cache-bust — one source, includes dynamic loaders
- Bump `?v=` together across `index/journey/privacy/terms.html`, `base.html`,
  `tests/test_pages.py`, **and the dynamically-injected loader URLs**
  (`journey-teaser.js` → `three.min.js?v=…`, `journey.js` vendor loads). A test
  asserts every `?v=` **on a browser-request-issuing URL** resolves to the one
  current version — scoped to served HTML/templates and static JS loader strings
  only, **excluding `docs/`, `PLAN-REVIEW-LOG.md`, logs, and vendor file
  contents** (historical version strings there are not served assets).

### Proof before the single merge
Request suite + e2e + the new semantic/SEO/legal tests + DOM contract +
validator all green; mobile LCP < 2.5s re-measured on the landing; reduced-motion
and <768px collapse verified per surface. Then **one merge to `main`** → deploy.

## Key decisions & tradeoffs

- **Phase 0 spike de-risks the whole bet** (Codex R1). We learn the LCP/DOM
  verdict on 2 surfaces, not after touching 11. Big-bang *release* is unchanged
  (still one merge); only the *build* is sequenced to fail early if it will.
- **Immersive everywhere, panel-over-stage** — the bet and its risks are in
  [ADR 0001](adr/0001-immersive-illustration-on-a-utility.md). Legibility and
  LCP are measured pass/fail, and Phase 0 is the explicit off-ramp to the
  lighter fallback.
- **3D Journey reskinned, not replaced;** Journey map is dynamic + illustrated on
  real aggregated data; extends Forest Light (no palette/type overhaul).

## Risks / open questions

- **LCP is the make-or-break** and now has a real budget + a Phase 0 gate rather
  than a hope. The immersive-everywhere landing may still fail it; the fallback
  is pre-agreed.
- **Branch discipline under active churn:** `main` is taking rapid data/
  special-check commits (this very session). Mitigation: **rebase the branch on
  `main` daily**, stand up a Vercel **preview env** for pre-merge parity (the
  2026-07-13 redesign had none), a short **`main`-freeze** window before the
  final merge, and re-run full proof **after** the final rebase.
- **DOM behavior, not just selectors,** is where a reskin silently breaks — the
  semantic tests above are the guard.
- **SEO/legal silent drift** — golden + snapshot tests are the guard.

## Out of scope

- **No functional, route, data-model, or copy changes** — reskin plus the one
  new Journey-map surface. Matcher gates/scoring, auth, digest cron, dataset
  untouched.
- **"Students like you won this"** — separate, blocked on a data-honesty problem.
- **Dormant AI** stays off. **No new runtime dependencies** without justification
  (prefer CSS/SVG over JS libraries).
- The **72 zero-requirement checklist** pass and the **APS** special-check
  re-verification remain queued separately (and are the churn the branch must
  rebase against).
