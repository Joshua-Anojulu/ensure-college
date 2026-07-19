# Plan: Phase 0 LCP tuning — pass the mobile gate while keeping the immersive hero
_Locked via grill-with-docs — by Claude + Josh, 2026-07-19. Terms per CONTEXT.md. Rev 3 after Codex rounds 1–2 (REVISE)._

## Goal

The Phase 0 Forest-Journey landing **fails the mobile LCP gate as-built**: on the
Vercel preview, pinned Lighthouse mobile gave median LCP **3548 ms** (runs
2939 / 3548 / 3591) against a gate of **<2500 ms median and no single run
>2700 ms**. The likely lever is **pre-existing image debt, not the immersive
hero**: `campus-quad.jpg` is a 285 KB raw JPG on the landing and the top
Lighthouse byte-cleanup opportunity (`uses-responsive-images` 1050 ms +
`modern-image-formats` 450 ms), present on `main` too. **Those savings estimate
bytes, not LCP causality** — the image is below-fold/lazy, so step 1's trace
waterfall must confirm whether it actually delays the measured LCP candidate (as
a bandwidth competitor) before we bank the win on it. There is also a
pre-existing, timing-variable
mobile **CLS ~0.9** (0.949 / 0.906 / 0 across runs). Josh chose to **tune and
re-measure** rather than take the [ADR 0001](adr/0001-immersive-illustration-on-a-utility.md)
fallback, because the gate miss looks fixable without abandoning the immersive
direction. This plan brings LCP under the gate and materially reduces CLS, all
on the `redesign/forest-journey` branch, then re-runs the pinned protocol as the
go/no-go for the Phase 1 fan-out.

## Approach

Steps are **measurement-gated**: we confirm what the LCP element and the CLS
culprit actually are before applying the fixes that depend on them. No blind
preloads, no blind app.js changes.

### 1. Diagnose on the mobile preview (before any fix)
A small `puppeteer-core` script driving the installed Chrome is used **for
element attribution only — never as a timing/pass-fail source** (see step 7 for
the one authoritative timing protocol). Run it under the **same conditions as the
gate** — mobile viewport + DPR, cold cache, and CPU/network throttling matching
Lighthouse mobile — so the LCP element, lazy-load behavior, and CLS race it
observes are the ones that occur under the gate, not an unthrottled artifact.
From the trace, capture and record in the review log:
- the **actual LCP element** (hero headline text? hero `::before` background?
  the `hero-demo` panel? `campus-quad`?), with its load/render phase breakdown,
  and specifically **whether `campus-quad`'s download delays the LCP candidate**;
- **every `layout-shift` entry** with its source node(s) and timestamp — do NOT
  pre-assume the culprit. Score each candidate *category*: font swap, the
  auth/header reveal, deferred motion (GSAP/ScrollTrigger) setup, hero/`hero-demo`
  layout, and post-FCP `app.js` population. The trace, not a hypothesis, decides
  which category the fix targets.

These facts gate steps 2 (is it byte-cleanup or an LCP lever?), 3 (preload?), and
5 (what to reserve?). If the tooling still cannot attribute the nodes, fall back
to manual bisection (toggle candidates, re-measure) rather than guessing.

### 2. Optimise `campus-quad.jpg` — the top byte-cleanup opportunity
`campus-quad.jpg` (285 KB, 1200×800 raw JPG) lives in the `.proof-band` section
(below the hero, below the mobile fold) and is Lighthouse's #1 opportunity
(~1.5 s combined). Treat it as **byte cleanup first**; it becomes an **LCP lever
only if step 1's trace waterfall shows its download competes with the measured
LCP candidate**. Either way the optimisation is worth doing.
- Generate properly-sized **WebP** variants offline and commit them; **document
  the exact generation command** in the plan/log for reproducibility (there is no
  repo image pipeline — the existing `hero-forest.webp` assets were made offline
  the same way).
- Convert the single `<img>` to a **responsive `srcset` + correct `sizes`** (or
  `<picture>` with a WebP source and the JPG as fallback). The **sole source of
  truth** for `sizes` and the `srcset` width descriptors is the **measured
  rendered CSS width** of `.proof-photo` at the target breakpoints, combined with
  DPR (emit 1× and 2× width candidates for each). Do not size from an estimated
  `vw`; measure `.proof-photo`'s box (it sits inside `.main`'s side padding) and
  derive the `sizes` expression from that. Keep `width`/`height`,
  `loading="lazy"`, `decoding="async"`.
- **WebP only, not AVIF** — a 285 KB JPG → ~30–45 KB WebP is already an ~8×
  win and needs no extra tooling. Revisit AVIF only if WebP misses the gate.
- **The DOM contract does not currently track this proof image**, so an absent
  contract failure does NOT prove safety. Add **explicit** assertions (request +
  browser) for the new markup: `picture`/`source`/`img` presence, the resolved
  `currentSrc` (correct variant per viewport), rendered dimensions, `alt`,
  `loading`, `decoding`. Update `tests/dom_contract.json` deliberately only if the
  markup changes something it does track.
- While here, check **why a lazy below-fold image loads in the critical window**
  (Chrome's lazy-load look-ahead margin on slow links); the optimised bytes help
  regardless, but avoid any JS/motion hook that eagerly triggers its load.

### 3. Conditional hero preload (only if it IS the LCP element)
If step 1 confirms the **mobile hero image (`hero-forest-mobile.webp`, 29 KB)**
is the measured LCP element, add **one mobile-only** media-scoped
`<link rel="preload" as="image" media="(max-width: 768px)">` for it — the gate is
the mobile gate, so we do **not** add a desktop preload (that only risks a second,
breakpoint-mismatched tag). The `media` must match the CSS `::before` breakpoint
exactly. Because the hero art is a CSS `::before` **background**, the preload
`href` and the CSS `url()` must be **byte-identical, including any `?v=`** — a
versioned preload will NOT dedupe against an unversioned background URL and would
double-fetch; version both together in step 6.
**If LCP is text (the headline), do NOT preload an image** — instead ensure
nothing render-blocking delays the headline, and rely on steps 2 and 4 to free
the critical path.

### 4. Reclaim the `style.css` preload bandwidth (landing only)
`index.html` inlines the full stylesheet via `main.py::_inline_css` **and**
separately `<link rel="preload" as="style" href="style.css">` (line 27) purely
to warm the cache for later navigation to secondary pages. On a ~40 ms-margin
budget that preload competes for the landing's critical bandwidth. Change it to
**`rel="prefetch"`** (correct semantics for a *future* navigation: low priority,
non-competing). Secondary pages still fetch/cache `style.css` via their own
links. This is a landing-only head change. **`prefetch` is not guaranteed
non-competing** — after the change, verify in the trace waterfall that it lands at
Lowest priority and does not sit on the LCP path; **if it still competes, remove
the landing stylesheet hint entirely** (secondary pages fetch their own CSS
regardless).

### 5. Fix the pre-existing CLS ~0.9 — branch on step 1's actual culprit
The fix is chosen by the layout-shift **category** step 1 identifies, not assumed:
- **DOM/layout culprit** (a container `app.js` populates/reveals post-FCP, or the
  hero/`hero-demo` box resizing): **reserve space** (explicit `min-height` /
  `aspect-ratio`) so the late content does not shift visible content. CSS-only.
- **Auth/header reveal** (a logged-in/out header swap changing height on hydration):
  reserve the header's height / render a stable placeholder so the reveal is
  in-place. CSS-only.
- **Font swap** (unexpected, since faces are metric-matched with `size-adjust` +
  overrides — but if the trace shows it): re-check `font-display` and that the
  hero face is preloaded, tighten the fallback metrics. CSS/head-only.
- **Deferred motion** (GSAP/ScrollTrigger setup mutating layout on init): ensure
  motion transforms don't reflow (composite-only transforms; set initial state
  before paint). May touch the motion init, not `app.js`'s DOM.

Across all branches, prefer the fix that leaves **`app.js` and the DOM contract
untouched**. Only if the correct-category fix still cannot get CLS under 0.1 do we
restructure `app.js` render timing — and if so, update `app.js` +
`tests/dom_contract.json` deliberately. CLS is **best-effort <0.1**, not a hard
gate (see acceptance).

### 6. Cache-bust in lockstep
Bump the asset `?v=` string together across `app/static/index.html`,
`journey.html`, `privacy.html`, `terms.html`, `app/templates/base.html`, and
`tests/test_pages.py` — plus any **new `campus-quad` variant URLs**, the hero
preload `href` (byte-identical to the CSS `url()`, per step 3), and the
prefetch URL — per the non-negotiable. **`tests/test_pages.py` currently only
checks app CSS/JS version strings**; extend it to parse `src`, `srcset`, and
`href` (preload/prefetch/image) so newly-versioned image/preload URLs are covered
by the lockstep, not silently un-versioned. Vendored `three.min.js` / favicon stay
on their slower cadence (exempt).

### 7. Prove, then re-measure (the gate)
- **Proof suite green:** request suite (`tests/ --ignore=tests/e2e`) + e2e
  (incl. the Journey-map tests) + DOM contract + `validate_dataset.py`. Add/adjust
  e2e for the responsive image (step 2 assertions) and any reserved-space markup;
  a frontend change is proven in the **browser** suite, not just requests.
- **Guard the inlined-CSS non-negotiable:** add/keep a request-level test that `/`
  contains the inline `<style>` critical CSS, uses **no `rel="stylesheet"`** for
  the landing CSS, and carries **only** the intended `prefetch`/`preload` hints —
  so this head surgery can't silently regress `_inline_css`.
- **Re-measure the gate on the preview — one authoritative protocol.** All
  pass/fail timings come from **pinned Lighthouse mobile** (NOT the step-1
  attribution script). Pin and record every variable: Lighthouse `@11` (**the
  same version the failing 3548 ms baseline was measured with**, so the
  before/after comparison is valid), `--form-factor=mobile` with its default
  Moto-G-class DPR/viewport, default simulated throttling, headless Chrome (fixed
  binary), **cold cache per run**, the exact preview URL, and **the deployed
  commit SHA** the preview built from.
  **Median of 5** (up from 3 — the observed LCP noise of 2939–3591 and CLS
  0.9/0.9/0 warrants more samples). **GO** iff median LCP <2500 ms **and** no
  single run >2700 ms. Record CLS alongside (target <0.1, best-effort).
- On **GO** → Phase 1 fan-out is unblocked. On a marginal or failing median →
  either a second tuning lever (the inlined-CSS trim noted in Risks) or the
  ADR 0001 fallback, Josh's call.

## Key decisions & tradeoffs

- **Fixes land on the branch** (not main-first): the gate is measured on the
  branch preview, so the fixes must be there to move it; prod benefits on merge
  (or a cherry-pick if urgent).
- **CLS: fix by the trace-confirmed culprit category (step 5), preferring the
  contract-safe fix per branch; app.js only if forced** — protects the frozen
  `app.js`/DOM-contract; accepts a possible escalation if the correct-category
  fix can't get CLS under 0.1 alone.
- **LCP is the gate; CLS is best-effort <0.1** — keeps the go/no-go decisive on
  the original bet and avoids coupling it to a potentially deeper app.js fix.
- **`prefetch` over `preload`** for `style.css` on the landing — trades a tiny
  bit of secondary-nav cache warmth for landing LCP headroom.
- **WebP, not AVIF** — sufficient win, no new tooling; AVIF held in reserve.
- **Measurement-gated preload/CLS** — we confirm the LCP element and the shift
  culprit before acting, rather than preloading or reserving blind.

## Risks / open questions

- **The gate is near-flaky.** LCP varied 2939–3591 and CLS 0.9/0.9/0 across three
  runs — the shift appears race-driven. Mitigation: median-of-5 + the "no run
  >2700" guard. If the post-fix median lands ~2.4–2.6 s we are inside the noise
  band and may need a further lever or a marginal-accept decision.
- **campus-quad may not be the LCP element.** If step 1 shows LCP is the headline
  **text** gated by the 367 KB inlined-CSS parse, image fixes help less directly
  (via bandwidth only). Contingency lever: trim unused inlined CSS — but that
  touches `_inline_css` and is **out of scope** unless step 1 forces it.
- **CSS reservation may not fully tame a JS-timing shift** → may force the app.js
  escalation, with its contract-update cost.
- **No repo image pipeline** — variants are generated offline; reproducibility
  depends on documenting the exact command.

## Out of scope

- The other heavy JPGs (`students-walking.jpg`, `campus-hall.jpg`) — **not on the
  landing**; they belong to other surfaces.
- The **Phase 1 fan-out** — gated on this passing.
- Matcher gates/scoring, auth, digest cron, dataset, dormant AI — untouched.
- Reducing the inlined-CSS payload / changing `_inline_css` — only if step 1
  proves a text-LCP path forces it.
