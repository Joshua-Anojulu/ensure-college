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

**Round 2 (.handoff/phase1-stageC-codex-r2.txt): VERDICT REVISE.** Codex's
own file reads failed (sandbox + MCP), so it could not verify the CSS/test
items from code; what it could retrieve (journey-teaser.js dual-channel
Save-Data, journey.js gating, JS pin lockstep) it verified clean. Round 3
re-ran with the file excerpts inlined.

**Round 3 (.handoff/phase1-stageC-codex-r3.txt): VERDICT REVISE, 1 P1 + 2 P3.**
The P1 (empty test_focus_ring body, module import failure) was a false
positive from a truncated excerpt - the intact body is at
tests/e2e/test_world.py:148 and the module collects 17 tests. Both P3s were
real and fixed in 5bd83a5: the hex-scan custom-property exemption applied
anywhere (now token-block only) and the JS pin lockstep passed vacuously on
an empty match list (now asserts pins are found). CSS items verified clean
in the same round: mobile landmarks hidden under 768px, adjacent-sibling
reveal, forced-colors suppression, color-mix chip fill.

**Round 4 (.handoff/phase1-stageC-codex-r4.txt): VERDICT REVISE, 1 P3.**
Accepted the P1-truncation and vacuous-pin dispositions. Remaining: the
hex-scan's :root tracking ignored brace depth (same-line closes and scoped
selectors like `:root .card` mishandled). Fixed in 2d64740 (brace-depth
tracking), proven on synthetic shapes.

**Round 5 (.handoff/phase1-stageC-codex-r5.txt): VERDICT REVISE, 1 P3.**
Same-line bare `:root { --ink: #hex }` token declarations were still
flagged. Fixed in 36a9744 by restructuring per Codex's suggestion: bare
:root blocks resolved as brace-matched character spans, per-hex declaration
check back to the nearest delimiter. Proven on 8 synthetic shapes
(same-line/multi-line/brace-next-line exempt; scoped, post-block,
component, and non-var-in-root hexes flagged). Suites at 36a9744: 431
request + 81 e2e green, 66 test_pages.

**Round 6 (.handoff/phase1-stageC-codex-r6.txt): VERDICT APPROVED.**
No findings; round-5 case confirmed resolved, no new issue.

## Josh preview feedback round (2026-07-22, post-approval, not re-Codexed)

Visual/decorative changes only, requested by Josh off the preview:
- Gate-pillar ivy removed (a953578): the vines read as floating green
  blobs in the flythrough close-up at the gate stop.
- Teaser live swap dwell-gated (d8845f8; dwell JS itself landed in
  a953578): the swap fired about a second after the section approached
  (500px early), replacing the labeled painting with the sparser live
  island - it read as the teaser vanishing. Now the swap waits until the
  section is at least 85 percent visible for 4s continuous (timer resets
  off-screen) and the crossfade is 1200ms. New e2e gate asserts no swap
  1.5s after the three.js release, then the swap.
- Lockstep bump v=20260721-5 to -6. Suites at merge: 431 request + 81 e2e.

## Merge 3 + post-merge prod snapshot (2026-07-22)

Fast-forward 285560c..d8845f8 on main, merge run with Josh's explicit
authorization. Prod (ensurecollege.com) verified after deploy:
- /health: {"status": "ok", "commit": "d8845f8"}
- v=20260721-6 serving on /
- Teaser dwell on prod: teaser-live false at 2.5s, true at 8s
- journey-paper computed opacity 0.2
- Gate arch vine-free (verified on the same-commit preview deploy;
  screenshots in the session scratchpad)

Stage C complete and live. Deferred nits carried (FULL CATALOG eyebrow
over foliage, catalog-list overflow ~1100px, empty forest beside the
account pitch after a match).
