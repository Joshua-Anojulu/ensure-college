# Phase 1 Stage C ledger: Journey + Teaser (merge 3)

Plan: `docs/2026-07-20-phase1-forest-world.md` items 14-16. Branch
`phase1-forest-world`, commits `9284ef1` (implementation) + `547e959`
(polish round). Preview verified at v=20260721-4.

## What shipped

**Item 15 - Teaser, painting-first.** The overlook plate is the guaranteed
visual: it hydrates through the same app.js data-src path as every other
world plate (hydrator selector extended in app.js and tests/dom_contract.json
together), so Save-Data suppresses it with the rest of the world. The four
landmark labels (Profile at the cabin, Essays at the desk, Deadlines at the
tower, Award at the flag) are SVG chip overlays positioned over the plate,
never baked into the art. The live three.js island loads only on idle
(requestIdleCallback, 4s bound) AND proximity (250ms bounded poll), renders
one frame, then `.teaser-live` fades the canvas in over the painting; both
layers fill the same absolute box so the swap cannot shift layout. Static
painting mode (`.teaser-static`) for reduced-motion, Save-Data, low-end
(<=2 cores or <=2GB), and no-WebGL. A dusk scrim inside the painting layer
keeps the copy legible over the pale plate and fades out with the swap.

**Item 14 - Journey clay polish.** The scene was already matte-Lambert
Forest Light with horizon-tracking fog from the 2026-07-18 redesign; Stage C
added the two missing pieces: the three converging plaza paths are now
marigold trail dots (the world's wayfinding motif) instead of solid paving,
and a cold-press paper overlay (inline turbulence SVG data URI, multiply,
opacity 0.2, z-1 between canvas and copy) gives the miniature painted tooth.
Hidden in `.journey-static` mode. Perf gate and reduced-motion fallback
untouched.

**Item 16 - Cohesion.** All style.css hexes now live in :root token
definitions or mask alpha ramps, except one documented allowlist entry
(`stroke: #fff;` - the trail's SVG mask stroke, literal white by definition
of a mask). Conversions: checkbox tick -> var(--brand-ink), teaser gradient
stop -> new --brand-lift token, CTA hover -> color-mix(accent/accent-deep).
New `TestStageCohesion` enforces: CSS hex scan with the allowlist, JS files
never carry CSS-style hex strings, three.js 0x palettes stay in the journey
scenes, and cache-bust lockstep extends to JS-pinned URLs - which
immediately caught app.js still pinning world.css?v=20260720-4. Em-dash
sweep clean (no new eyebrows added).

## Gates

- Suites: 431 request + 80 e2e green at both commits
  (`.venv/Scripts/python.exe -m pytest`).
- New e2e gates (tests/e2e/test_world.py): painting visible pre-swap with
  three.min.js held + CTA clickable + zero-layout-shift same-box swap
  (section rect byte-identical before/after `.teaser-live`); reduced-motion
  never requests three.js and keeps painting + labels; Save-Data JS-channel
  test additionally asserts `.teaser-static` and no three.js.
- Asset budget: overlook-1376 49.1 KB (budget <=90), overlook-760 20.7 KB
  (budget <=40). Lazy, fetchpriority=low, hydration-gated.
- Visual verification on preview (2026-07-21): painting mode legible under
  the dusk scrim with all four landmark chips readable; live island swaps in
  the same box; journey warm (paper veil at 0.2 after the 0.38 polish),
  marigold dots at the plaza stop.
- Landing harness delta (Phase 0 protocol, throttled mobile, same-day
  side-by-side prod control): PASS, table below.

## Landing harness (preview v=20260721-4 vs same-day prod, 9 runs/scenario)

A first 5-run pass showed cold +156 ms; at 9 runs the distributions fully
overlap and the sign flips - the 5-run delta was noise, which is why this
table records the 9-run medians. Each target had one cold-start TTFB
outlier (2740 / 8452 ms) retained in its median.

| Scenario | Preview median LCP | Prod control | Delta | CLS |
|---|---|---|---|---|
| cold | 1368 ms | 1408 ms | -40 ms | 0.0000 |
| pre-consented | 1284 ms | 1328 ms | -44 ms | 0.0000 |

LCP element is the hero art or hero text in every run - world art never
takes LCP. All medians far under the 2500 ms ceiling.

## Codex build review

**Round 1 (.handoff/phase1-stageC-codex.txt): VERDICT REVISE, 9 findings.**
Fixed 7: (P1) teaser Save-Data check was JS-channel only, header-only
Save-Data could fetch three.js - now dual-channel (navigator.connection OR
the server-stamped class) with the header e2e test asserting teaser-static
and zero three.js requests; (P2) the JS-channel test's three.js assertion
was vacuous (scanned the world-request list) - both tests now track
three_requests separately; (P2) /journey loaded the 670 KB vendor script
unconditionally before its fallback gates could run - the static script tag
is gone, journey.js gates first (now including Save-Data, previously never
checked there) and injects three.js only when the flight runs, degrading to
journey-static on load failure, with a new reduced-motion /journey e2e gate;
(P2) mobile landmark chips fell under readable size and the slice crop cut
the right-side stations - hidden below 768px, the painting carries the
mobile teaser; (P2) landmark reveal depended on :has() - replaced with an
adjacent-sibling selector, no support cliff; (P2) no forced-colors handling
for the teaser layers in the inlined stylesheet - added, decorative layers
hidden and the section forced to system colors; (P2) chip fill used a raw
rgba() - now color-mix over var(--surface). The P3 split three.js pin
resolved itself: both pins are JS-side now and the cohesion test asserts
them. Suites after the round: 431 request + 81 e2e.

Deferred with rationale: extending the color scan to rgb()/hsl() means
adjudicating dozens of pre-existing legitimate shadow-alpha rgba() values -
queued as its own audit, out of stage scope; the inline-CSS byte note is
recorded as observed-not-a-regression (the 9-run harness delta is negative).

## Outstanding before merge 3

1. Codex round 2 verdict.
2. Josh's visual sign-off on the preview.
