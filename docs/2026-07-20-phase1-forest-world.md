# Plan: Phase 1 — the World carried across every surface (rev 5)
_Locked via grill-with-docs — by Claude + Josh, 2026-07-20. Terms per CONTEXT.md. Dials 9/8/4 (house-style). Input: docs/2026-07-20-phase1-forest-world-design.md + the ten approved comps in `.handoff/phase1-comps/` (visual contract). Rev 5 after Codex rounds 1–4 (REVISE)._

## Goal

Carry the [[World]] — the Forest Light illustrated environment — across every
surface, per ADR 0001's accepted immersive-everywhere decision: full scene per
surface, with a quiet paper-mist center behind working areas so panels stay
legible. The landing becomes one continuous hike (morning trailhead → sunlit
clearing → trail waypoints → deep grove → valley overlook → dusk treeline
footer), the [[Trail]] is the persistent element connecting it, the [[Teaser]]
becomes painting-first with the live island swapping in after load, and the
[[Journey]] is reskinned to a clay-miniature register under a paper overlay.
Working content always rides in legible panels; the world decorates, never
gates.

## What the comps bind — and what they do not

The ten comps bind **art direction only**: palette, scene composition, the
Trail, panel treatment, world-glyph style, section mood. They are explicitly
**non-binding** for: form fields (the [[Preview]] stays GPA / grade / interest
— comp 10's "State" dropdown is wrong), nav and footer IA (real routes and
labels only), copy, and any DOM semantics. The hero's DOM, form names, and its
measured LCP element are untouched; comp 01's carved-sign treatment is
decorative art/CSS *around* the existing preview panel, never a restructure of
it.

## Release gates (all stages)

- **The Phase 0 attribution harness (real-throttle, gate-matched) is the
  release gate.** The pinned Lighthouse protocol is recorded per stage as
  **advisory only** — Phase 0 proved LH11 cannot attribute this page's LCP
  element (docs/2026-07-19-phase0-lcp-tuning.md, Outcome) and its pessimistic
  fallback responds to nothing real. Do not chase it.
- **Delta budget, precisely:** at stage start, re-measure the baseline on a
  no-change preview (same harness, median of 5). The stage gate is **stage
  median ≤ baseline + 150 ms**. Separately, if the stage median exceeds
  2500 ms, stop and investigate before merging — even if the delta passes —
  and if the *baseline itself* exceeds 2500 ms, a pre-existing regression is
  investigated before the stage proceeds. **CLS < 0.1** (Phase 0 achieved 0 —
  new plates must keep it there).
- **Two harness scenarios, both gated with LCP-element attribution:** a cold
  first visit (consent gate present) AND a pre-consented returning visit —
  so world regressions cannot hide behind the gate's paint.
- **Main-thread budget:** the harness records TBT/long tasks per the Phase 0
  precedent; a stage may not add > 50 ms of new long-task time at the
  gate-matched throttle. Stage C additionally checks frame budget during the
  Teaser live swap and Journey scroll.
- Both proof suites green; DOM contract untouched unless a stage deliberately
  updates the manifest; validator warnings unchanged.
- **Post-merge check per stage:** the same median-of-5 protocol against prod,
  recorded in the stage's ledger entry: the LCP element as a selector/node
  summary (plus its resource URL only when the LCP entry is resource-backed),
  loaded world-asset URLs and total bytes, and any CLS contributors. No new
  RUM infra.
- **Visual acceptance:** per stage, Playwright screenshots of the mapped comp
  sections are captured into the ledger and Josh signs them off against the
  comps manually — art direction is a human gate, not a pixel-diff.

## Approach

### Stage 0 — asset inventory (before any markup; inside the Higgsfield trial window)
1. Write the plate inventory to `docs/phase1-asset-inventory.md`: every plate
   named, with **cost class** (CSS-only / one image / script-driven), byte
   target, format, preload-vs-lazy, reduced-motion behavior, **and per-stage
   aggregates: total bytes, first-viewport bytes, max parallel image
   requests, and decoded-memory estimate**. No unlisted asset ships.
2. Generate all plates via Higgsfield (~20–30 generations) in one pass with a
   shared style block (trial-window economics, Q8): five landing scene plates,
   the shared frame set (canopy edge, fern corners — reused, cache-shared
   across all 322 template-family pages), SPA stage plates, the world-glyph
   sprite (one sheet), boundary creatures (owl, leaves), and regenerated
   comps 07/08 at full-scene-quiet-center. **Production plates carry no baked
   text or UI.** Redo budget reserved (~15 credits) for drift rejects.
3. Process through the committed Pillow WebP generator (mobile + desktop
   crops, measured `sizes`/`srcset`). **World assets ship content-hashed**
   (hash in filename) under `app/static/img/world/` — exempt from `?v=`
   lockstep by design, and the lockstep test's parser is **extended to scan
   CSS `url()` and JS string asset URLs** so nothing references world art by
   unhashed path. Two supporting mechanisms, both tested: (a) a generated
   **manifest that verifies each `world/` filename digest against the bytes
   on disk** (hash-integrity test); (b) **response-header behavior for
   `/static/img/world/` only** — `Cache-Control: public, max-age=31536000,
   immutable` set explicitly in the app (StaticFiles does not do this today),
   asserted by a request test. The mobile hero preload stays **unversioned
   and byte-identical** per the existing contract (tests/test_pages.py); hero
   art is explicitly exempt from re-processing, with a no-double-fetch test.

### Stage A — landing world + footer (merge 1)
4. Per-section scene plates as **absolutely-positioned `<picture><img>`
   elements** (not CSS backgrounds): `loading="lazy"`, `decoding="async"`,
   `fetchpriority="low"`, explicit width/height or `aspect-ratio` reserving
   the box (CLS rule: never hide or move what has painted). Decorative plates
   carry `aria-hidden="true"` and empty `alt`. The hero and its LCP element
   are untouched.
5. **Landing critical CSS is capped:** `main.py::_inline_css` inlines all of
   `style.css` into `/`, so Stage A sets a hard gzip byte cap for the inlined
   sheet (baseline measured at stage start, growth ≤ 4 KB gzip). World CSS
   that the landing does not need at first paint lives in a separate
   `world.css`: the **template family loads it as a normal `<link>`** (those
   pages are not the landing's critical path), and the **SPA tool views —
   which live inside `/`'s `index.html` — get it appended by `app.js` only
   on first SPA-world activation** (the first time a tool view is shown),
   never at init — so the request is non-critical by construction and can
   never compete in the returning-visitor LCP waterfall (asserted by a
   waterfall check in the harness scenario: no `world.css` request before
   activation). SPA world stages are scoped under a `.world-ready` class set
   **only in the stylesheet's `load` callback**: a view that renders before
   the sheet arrives simply shows plain Forest Light (already the world's
   quiet register) and the stage fades in as a decorative opacity transition
   when ready — never an unstyled pop, never a layout move, instant/off
   under reduced-motion. The landing's own above-fold world rules stay in
   `style.css` under the cap.
   The inline SVG [[Trail]] is bounded too: Stage A gates include **HTML
   byte growth (≤ 6 KB gzip), DOM node count growth (≤ 40 nodes), and SVG
   path complexity (one path per section link, no filters)**.
6. The [[Trail]] as an inline SVG path connecting sections, drawn-on by CSS
   scroll-driven animation inside `@supports (animation-timeline: scroll())`;
   static trail otherwise and under `prefers-reduced-motion`. No scroll
   listeners; the CSP derived-hash inline consent boot is preserved
   untouched, and a test asserts no new inline executable scripts or inline
   event handlers appear.
7. Boundary creatures as small transparent WebPs (owl at the grove, leaves at
   the clearing). Fireflies: static dots by default; their twinkle class is
   toggled by a **dedicated small IntersectionObserver** (the existing reveal
   observer is one-shot and is not reused): observe the firefly containers,
   add the class on intersect, remove it off-viewport, `disconnect()` on
   teardown; never applied under `prefers-reduced-motion`; covered by an e2e
   test. Gutter marginalia only ≥1200px; never overlapping content; focus
   rings must remain visible over art.
8. Dusk-treeline footer replacing the flat ink footer: treeline plate over
   the existing ink band, marigold hairline kept, real link set.
9. Mobile: full world with lighter art-directed crops per comp 10 — headline
   areas stay clean paper. **Save-Data is enforceable by construction:**
   below-fold world plates ship inert (`data-src`/`data-srcset`) and are
   hydrated by `app.js` only when the signal is absent on **both** channels:
   `serve_index()` stamps a `save-data` class on `<html>` when the
   `Save-Data: on` request header is present (browser JS cannot see that
   header), and `app.js` additionally checks
   `navigator.connection.saveData`. No-JS visitors get plain Forest Light
   (decorative art only — nothing functional is lost). Tests cover both
   channels: a request test asserts the class is emitted for the header, and
   a browser test asserts saveData on → zero world-plate requests.
10. Stage gates per **Release gates**, plus: e2e for trail static fallback,
    firefly pause, and `elementFromPoint` hit-testing on every primary
    landing control (CTA, preview form fields, nav links) proving no world
    layer intercepts them.

### Stage B — tool views + template family (merge 2)
11. SPA views (match lanes, catalog, saved, profile form): full-scene
    quiet-center stage plates as positioned `<img>` layers behind existing
    containers — panels and the DOM contract untouched. Legibility is a
    pass/fail check per surface: panel text contrast measured over the
    busiest plate region; failure means more mist, not smaller type; a
    surface that cannot pass falls back to motif-framing per ADR 0001.
12. Template family (`base.html`: Opportunity pages, browse, guides, 404):
    shared canopy-edge + fern-corner frame plates plus a quiet scene,
    cache-shared across all pages; world glyphs in the facts panel per comp
    08. **Legal pages (`privacy.html`, `terms.html`) are static HTML, not
    `base.html`** — they are separate reskin targets receiving the frame via
    shared CSS classes, with their snapshot-hashed legal copy untouched and
    their existing `?v=` lockstep entries bumped. **Gate: one Opportunity
    page, one browse page, one guide page, and 404 each pass a
    request-budget + LCP-attribution check on the preview**, and template
    tests cover a verified entry, an unverified entry, and an
    estimated-deadline entry asserting the verification labels and JSON-LD
    are byte-unchanged by the reskin.
13. Two-tier icon rule enforced: world glyphs from the sprite only inside
    illustrated moments; functional icon family unchanged inside working
    controls. Semantic e2e additions: tab switching, form steps, overlay
    clickability (`elementFromPoint`) on the staged surfaces; forced-colors
    smoke check that panels and controls stay usable.

### Stage C — Journey + Teaser (merge 3)
14. [[Journey]] reskin, skin only: three.js materials to clay-miniature in
    Forest Light tokens (matte, fog, marigold path dots), cold-press paper
    overlay above the canvas; existing perf gate and reduced-motion fallback
    kept. The three.js pin inside `journey-teaser.js`/`journey.js` string
    URLs is covered by the extended lockstep parser.
15. [[Teaser]] painting-first: the overlook plate renders immediately (one
    hero-class WebP; per the Stage 0 no-baked-text rule the landmark labels
    profile → essays → deadlines → award are **DOM/SVG overlays positioned
    over the plate, not baked in**, tested readable and click-safe in the
    reduced-motion static mode); `journey-teaser.js` loads on
    idle/visibility and swaps the live island into the same-size box —
    nothing painted moves. Reduced-motion,
    `Save-Data`, and low-end devices keep the painting. E2e: painting visible
    pre-swap, same-box swap with zero layout shift, reduced-motion stays
    static, CTA clickable before and after swap.
16. Final cohesion pass: eyebrow cap, em-dash sweep of all new copy, token
    audit — **first convert the existing hardcoded-hex exceptions in
    `style.css` to tokens, then enforce a CSS/JS hex scan with an explicit
    allowlist**; asset lockstep test green; full proof suites.

## Key decisions & tradeoffs (the grill's resolutions)

- **Full world on every surface** (Q1), quiet-center execution (Q1b) — ADR
  0001's letter; mist is world, so legibility and immersion stop trading off.
- **The landing scroll arc is binding** (Q2): one hike, morning to dusk,
  including the dusk footer.
- **Teaser = painting-first, live island on idle** (Q3) — comp art is the
  guaranteed visual; liveness is progressive enhancement; CLS-safe swap.
- **Journey = clay miniature + paper overlay** (Q4).
- **The Trail is the scroll companion** (Q5); creatures stay at boundaries.
- **Two-tier icon rule** (Q6): world glyphs (one generated sprite) inside
  illustrated moments; the functional family everywhere controls live.
- **Three staged merges** (Q7): landing, then tool+template, then
  Journey/Teaser — each independently gated and revertable.
- **All production art generated up front** (Q8), inside the trial window.
  Codex round 1 preferred per-stage generation to limit style drift; rejected
  by the arbiter: plates cost ~2 credits each and the trial window is hard —
  drift risk is carried by the shared style block plus a reserved redo
  budget.

## Risks / open questions

- **Style drift across ~25 generated plates**: shared prompt block, one-pass
  generation, reject/redo per plate against the comp set; inventory is the
  checklist.
- **Landing bandwidth contention**: below-fold plates could compete with the
  hero during load; `fetchpriority="low"` + lazy + the harness delta budget
  on the Stage A preview is the arbiter.
- **Legibility over full scenes on tool views**: pass/fail per surface with
  the mist dial as the fix; ADR 0001's motif-framing fallback per surface if
  it cannot pass.
- **`animation-timeline: scroll()` support**: progressive by design; the
  static trail is the baseline experience, not a degraded one.
- **Template-family weight on indexed pages**: gated representatives per
  Stage B rather than spot-checks.
- **Trial window**: Stage 0 must complete before the Higgsfield trial is
  cancelled (~2026-07-23); slippage means paid credits or re-scoping plates.

## Out of scope

- Matcher gates/scoring, auth/session code, database schema (no migrations in
  any stage), digest cron, consent-gate semantics and the CSP hash mechanism
  (signed off in Phase 0 — untouched), copy repositioning, AI features (stay
  dormant), Journey-map personalization logic, RUM/analytics infrastructure.
  The DOM contract changes only if a stage explicitly updates the manifest
  deliberately.
