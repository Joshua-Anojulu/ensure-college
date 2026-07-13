# Plan: UI redesign — retire "The Highlighter," ship "Forest Light"
_Locked via grill-with-docs — by Claude + Josh, 2026-07-13. Terms per CONTEXT.md._
_Rev 3. Codex-approved (VERDICT: APPROVED, round 3 of 5, 2026-07-13)._

## Goal

Replace the site's visual identity, which is built on now-banned AI-default patterns
(Fraunces display serif, warm cream/paper palette, marigold marker, three equal
feature cards, overloaded hero stack), with a distinctive light-only "Forest Light"
identity: deep forest green carries the brand, cool paper canvas, amber as a small
controlled accent, Cabinet Grotesk display + Satoshi body + JetBrains Mono data
voice, and a real motion layer (GSAP on the landing, IntersectionObserver
everywhere else). The landing sections are recomposed; the app surfaces
(matches, filters, plan, saved, modals) and server-rendered opportunity/guide
pages are deeply reskinned through tokens without structural change.

## Frozen DOM contract (do-not-change map)

The SPA lives at `app/static/index.html`; server templates live at
`app/templates/` (`base.html`, `detail.html`, `browse.html`, `browse_index.html`,
`guide.html`, `guides_index.html`, `404.html`).

Frozen, verbatim:
- All 181 selectors `app.js` queries (IDs, classes), plus their required
  `data-*` values (e.g. `.opportunity-tab[data-view]`, `.catalog-kind-tab`) and
  element types (`#profile-form` stays a `<form>`; `#browse-catalog-btn` stays
  `<button type="button">`; all profile inputs stay native `<input>/<select>`
  with current IDs, names, labels, and checkbox values).
- All CSS class names `app.js` EMITS when rendering (match cards, badges,
  fit rings, save buttons, show-more, verification-source labels, plan rows,
  etc.). These are enumerated from `app.js` template literals at build start
  and every one keeps a styled rule in the new CSS. The JS-emitted markup is a
  CSS contract, not just the queried selectors.
- Nav labels, form field names/order, legal copy (`privacy.html`, `terms.html`
  visual tokens inherit; text untouched), URL structure, wordmark text.

A new `tests/test_dom_contract.py` asserts the FULL frozen contract against
`index.html`: a committed manifest file (`tests/dom_contract.json`) listing all
181 queried selectors, required attribute values (tab `data-view`, catalog kind
tabs), profile form field names, and element-type constraints (`#profile-form`
is a `<form>`, `#browse-catalog-btn` is a `<button>`). The emitted-class side
of the contract is a second, explicitly maintained manifest section, built by
hand-auditing ALL class assignment patterns in `app.js` (template literals,
string assignments, `classList.add`, helper-composed names), not just template
literals; every listed class must have a matching rule in the new CSS
(asserted by a test that greps the stylesheet).

## Approach

### 1. Typography foundation
1. Self-host Cabinet Grotesk (700/800), Satoshi (400/500/700), JetBrains Mono
   (400) as woff2 under `app/static/fonts/` (6 files, budget ~280KB total;
   Fontshare / JetBrains free licenses). `@font-face` with `font-display: swap`
   plus `size-adjust`/`ascent-override` fallback metrics to hold CLS.
2. Preload display 800 + body 400 in `app/static/index.html` only; server-
   rendered pages (`app/templates/base.html`) preload body 400 only, so SEO
   pages do not pay for display weight above the fold they may not use.
   Remove all Google Fonts links/preconnects from both. Fallback metrics are
   tuned against Arial/system-ui (sans metrics for a sans identity; no serif
   fallback remains).
3. Tighten CSP in `app/main.py`: `style-src 'self' 'unsafe-inline'`,
   `font-src 'self'`. New tests assert googleapis/gstatic are ABSENT from the
   CSP header and every new font/vendor asset URL returns 200.

### 2. Token overhaul (`app/static/css/style.css` `:root`)
4. New palette tokens (light-only, cool-based; deliberately NOT the banned warm
   cream family):
   - `--canvas #f1f2ee`, `--surface #fbfcfa`, surface tint steps cooled
   - `--ink #16211b`, muted steps recomputed for WCAG AA
   - `--brand #1e4034` (deep forest; primary actions, links, active states)
   - Amber accent split by use: `--accent-deep #8a5e14` for any text or
     meaningful indicator on light surfaces (AA-checked), `--accent #c98d2c`
     only for large decorative fills/highlights where contrast rules do not
     apply. Focus ring uses forest at 3:1+ against canvas, not amber.
     The `--marker` highlighter effect is retired.
   - Semantic colors (success/amber/danger) recalibrated cool; match-quality
     badge colors stay semantically distinct and AA-legible.
   - Shadows re-tinted green-black; hairlines cooled.
5. Type tokens swap to the new families; display headings drop serif optical
   settings, gain tighter tracking and larger scale contrast.
6. Shape lock: existing radius scale unchanged. Existing easing/duration tokens
   kept, including `--ease-spring`.

### 3. Landing recomposition (`app/static/index.html`, respecting the frozen map)
7. **Hero**: asymmetric split at variance 9. Max 4 text elements: H1 (2 lines
   max), subtext 20 words or fewer, primary CTA as `<a href="#profile-form">`
   (the `<form id="profile-form">` itself is untouched), secondary
   `#browse-catalog-btn` kept as a button. The live 3-question Preview panel
   remains the hero's interactive asset with every `preview-*` ID untouched
   and the form interactive immediately (entrance animates opacity/transform
   only, never gates input). Removed from the hero: eyebrow, "Free to use"
   tagline note, stats strip. Craft: double-bezel on the preview panel,
   overlap composition collapsing to single column below 768px.
8. **Catalog numbers band** (new, below hero): hosts the real
   `__COUNT_SCHOLARSHIPS__` / `__COUNT_PROGRAMS__` / `__COUNT_COMPETITIONS__`
   server-injected counts in mono display scale. Placeholder names unchanged.
9. **Proof band**: recomposed full-bleed editorial composition reusing
   `campus-quad.jpg` with its meaningful `alt` text kept; the decorative
   visible caption is removed (alt semantics preserved). Explicit
   `width`/`height` reserved; stays `loading="lazy"` + `decoding="async"`
   (it is below the fold; the hero text/panel is the LCP element, verified in
   the Lighthouse pass) with `sizes`-appropriate responsive treatment.
10. **Difference section**: three equal cards replaced by an asymmetric 1+2
    composition (exact cell count = content count, visual variation across
    cells); the trust strip's three lines fold in; the separate `trust-strip`
    section is removed.
11. Eyebrow cull to the mechanical cap (max 1 per 3 sections). Punctuation
    sweep (em/en dashes to periods/commas/hyphens, no voice change), scoped:
    `index.html` copy, `app/templates/` chrome, and guide body copy, each
    replacement reviewed individually; `app.js` user-facing strings swept only
    where shown in UI chrome and reviewed one by one; legal pages excluded
    (frozen copy). Nav labels and form fields untouched.
12. Restyle `favicon.svg` and the header brand mark to the new identity
    (wordmark text unchanged). **Regenerate `og-image.png` (1200x630) in the
    new identity in the same release** so shared links match the site.
13. Grain texture, if kept after measurement: a tiny tiled static asset on a
    `fixed` `pointer-events-none` layer with no blend modes or filters; dropped
    if DevTools paint profiling shows measurable cost.

### 4. Motion layer
14. Vendor GSAP + ScrollTrigger under `app/static/js/vendor/` (~90KB,
    CSP-clean), loaded `defer`, initialized only when the landing view is
    active. Choreography: hero entrance sequence and ONE scroll-driven
    proof-band reveal. Pinning rules: `start: "top top"`, image
    dimensions reserved, init deferred until image decode, `ScrollTrigger.refresh()`
    after fonts/images settle, pinning disabled below 768px.
15. IntersectionObserver reveal-with-stagger for remaining landing sections.
    Content is visible by default; hidden/transform pre-states apply only
    after JS adds a `.motion-ready` class AND reduced-motion is not requested.
    No-JS and reduced-motion users get a fully visible static page.
16. **Replace `wirePageMotion()`'s `window.addEventListener("scroll")`**
    (app.js:391, header `has-scrolled` toggle) with a 1px top sentinel +
    IntersectionObserver. This is the one sanctioned app.js touch; the
    `has-scrolled` class name and behavior are preserved.
17. App surfaces: micro-interactions only (hover lift, `:active` push, spring
    count bumps via existing tokens).

### 5. App-surface + template reskin (tokens flow through; no structural change)
18. Audit every component family against the new tokens: buttons, inputs,
    selects, modals, tabs, filter panels, result cards, fit rings, badges,
    checklist rows, status pills, and every JS-emitted class from the frozen
    map. WCAG AA re-verified per component.
19. Match-quality buckets keep canonical names (Strong / Possible / Special
    check) with palette-consistent, semantically distinct colors.
20. Server templates inherit via shared CSS; verify opportunity-page hero,
    verification labeling, and JSON-LD-adjacent content render correctly.
    `tests/test_seo_pages.py` is extended (where not already covered) to
    assert one opportunity page's title, meta description, canonical, JSON-LD
    block, and verification labeling survive the reskin.

### 6. Ship + verify
21. Bump asset cache-bust in `app/static/index.html`, `app/templates/base.html`
    (if versioned), AND `tests/test_pages.py` together (repo guardrail). Update
    any test asserting a changed string in the same commit.
22. Branch `ui-redesign-forest`, Vercel preview deploy, Josh eyeballs desktop +
    phone before merge.
23. Proof, in order:
    - `python -m pytest tests/ -v` green (274 + new DOM-contract/CSP/font tests)
    - `python scripts/validate_dataset.py` clean
    - Scripted browser smoke on the FINAL preview URL, merge-blocking, with a
      dated evidence log committed as `docs/2026-07-13-ui-redesign-smoke.md`
      (browser + version, viewport list, console result, pass/fail per item):
      landing loads with zero console errors, preview 3-question flow returns
      matches, profile form submits, all opportunity tabs switch (`data-view`
      intact), catalog search/filter works, auth modal opens, keyboard-only
      pass through pinned/revealed sections, reduced-motion pass, 375px
      collapse check.
    - Lighthouse on preview vs current prod, BOTH mobile (throttled) and
      desktop; mobile is the merge blocker: LCP < 2.5s, CLS < 0.1, and no
      regression beyond 10% on either metric (byte budget: fonts ~280KB,
      GSAP landing-only ~90KB).
    - Full copy re-read: zero em/en dashes in swept scope, no grammar breaks;
      design-taste-frontend pre-flight checklist run against the landing.

## Key decisions & tradeoffs
- **Full identity overhaul, not evolution** (user-decided): the current identity
  IS the AI tell.
- **Light-only, Forest rendered light** (user-decided): classroom/Chromebook
  ergonomics won over the dark preview; green leads so the palette never
  collapses back into beige+brass.
- **Cabinet Grotesk + Satoshi over Clash Display / Geist** (user-decided).
- **GSAP landing-only + IO elsewhere** (user-decided).
- **Recompose landing, reskin app** (user-decided); DOM contract frozen and
  now test-enforced.
- **Stats relocated below hero, not deleted** (real numbers, banned only
  inside the hero stack).
- **CSP tightened** as a side effect of self-hosting, with explicit tests.
- **Playwright CI infra REJECTED for this release** (Codex round 1 asked for
  it): adding a browser-test dependency + CI runner is real scope this repo
  has never carried. Mitigation: the scripted browser smoke above, run by
  Claude against the Vercel preview before merge, covers the same checklist.
  Playwright adoption goes to the Tier 3 backlog.

## Risks / open questions
- Cabinet Grotesk is wider than Fraunces at display sizes; headline line
  counts re-checked at 360/768/1280.
- The em-dash sweep may touch test-asserted strings; each updated in the same
  commit.
- GSAP entrance must never delay preview-form interactivity (transform/opacity
  only; no pointer-events gating).
- Guide body copy swept punctuation-only, reviewed string by string.

## Out of scope
- Dark mode (tokens make it cheap later).
- App-shell/nav recomposition, results-layout restructuring.
- Copy voice rewrite, nav label changes, URL/slug changes, legal copy changes.
- app.js modularization, full WCAG audit, Playwright CI (all Tier 3 backlog).
- Dormant AI features, matcher logic, datasets, backend behavior.
