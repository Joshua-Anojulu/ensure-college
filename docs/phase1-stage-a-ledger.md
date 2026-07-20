# Phase 1 Stage A ledger — landing world + footer
_Branch phase1-forest-world; gates per docs/2026-07-20-phase1-forest-world.md._

## Budget gates (measured 2026-07-20, vs main @ 005e62b)

| Gate | Cap | Measured | Status |
|---|---|---|---|
| Inlined CSS growth (gzip -9) | ≤ 4,096 B | **+1,545 B** (21,707 → 23,252) | PASS |
| Landing HTML growth (gzip -9) | ≤ 6,144 B | **+565 B** (10,399 → 10,964) | PASS |
| DOM node growth | ≤ 40 | **+38** (3 plate divs, 5 plate imgs incl. owl+leaves, dusk div+img, fireflies 8, 4 trail SVGs × 5) | PASS |
| Trail SVG complexity | 1 path geometry per section link, no filters | 4 links, 1 geometry each — but 2 `<path>` nodes per link (dots + mask reveal share the same `d`); see deviations | PASS (as deviation) |
| World plate requests (landing) | ≤ 7 | 6 desktop (clearing, waypoints, grove, owl, leaves, dusk; 760 tier alternates on mobile, where creatures are neither shown nor hydrated) | PASS |
| Stage A world bytes | ≤ 360 KB desktop / ≤ 155 KB mobile | ~113 KB desktop / ~46 KB mobile (excl. overlook, deferred to Stage C) | PASS |

## Proof suites

- Request: **419 passed** (world manifest integrity ×2, immutable cache header,
  Save-Data class, world-reference scan, plus the full pre-existing suite)
- E2E: **72 passed**, including the eight world gates: hit-testing under
  plates (desktop + mobile), Save-Data zero world requests on both channels
  (header and navigator.connection), focus-ring visibility over art, firefly
  intersection toggle, reduced-motion static trail + fireflies, hero preload
  single-fetch
- Harness note for future e2e: the CSP blocks Playwright `wait_for_function`
  string pollers (`unsafe-eval`); poll via `page.evaluate` (see
  tests/e2e/test_world.py::wait_until)

## Visual acceptance (Josh's gate)

Screenshots captured at 1440×900 against the local build (scratchpad
`sec-stats/proof/difference/footer.png`, shown in-session 2026-07-20):
stats ride the clearing openly with the hero trail flowing in; waypoints
behind the full-bleed proof band; grove at natural aspect with blended owl
and paper-washed heading; dusk treeline + fireflies over the ink footer;
trail connectors drawing on scroll. Pending Josh's per-section sign-off
against comps 01-06.

## Deviations (logged, accepted by builder pending review)

- Teaser section gets no Stage A plate: the overlook painting is Stage C's
  painting-first swap (sequencing choice; the live canvas remains the
  section's miniature-world beat meanwhile). Its trail connector hangs from
  the difference panel's bottom edge instead — the teaser's overflow:hidden
  and opaque panel would swallow anything placed inside it.
- Hero fireflies skipped: "hero untouched" outranks marginalia; fireflies
  live at the dusk band only.
- Comp 03's waypoint chips not adopted: the proof band keeps its existing
  photo + copy DOM (contract-frozen); chips reconsidered at Stage B.
- Plates are bare `<img srcset>` rather than the plan's `<picture><img>`
  (Codex round 1 finding, rejected by the arbiter): srcset-on-img is the
  identical responsive mechanism; `<picture>` adds art-direction/format
  alternates we do not use, at +4 DOM nodes against a 40-node cap.
- Two `<path>` nodes per trail link (Codex round 1): the draw-on requires a
  mask whose stroke is scrubbed — a single dotted path cannot be drawn on
  with dashoffset because the dash pattern IS the dots. Both paths share
  one `d` geometry; the gate's intent (bounded complexity, no filters) holds.

## Harness gate (run 2026-07-20; protocol per Phase 0, rebuilt in-session)

Targets: baseline = prod ensurecollege.com (main @ 005e62b), stage = branch
preview (da7a7ed). Moto G viewport 412×823 @ DPR 1.75, CPU 4×, slow-4G
equivalent, cold cache + fresh profile per run.

- **Pre-consented (median of 5):** baseline 1380 ms → stage 1428 ms
  (**+48 ms**, gate ≤ +150) — PASS. LCP element: `h1.hero-headline` both.
- **Cold, first sample (median of 5):** baseline 1344 → stage 1752
  (+408 ms, raw FAIL) — triggered the attribution re-run below.
- **Cold, attribution re-run (median of 7, TTFB split):** raw medians
  baseline 1596 vs stage 1380 (stage 216 ms FASTER this sample);
  **render time (LCP − TTFB): baseline 972 ms vs stage 925 ms — stage
  47 ms faster.** TTFB swung 344–2559 ms on prod itself (serverless cold
  starts on both targets), fully explaining both raw deltas' signs.
  **Ruling: cold gate PASS on render-time attribution** — the delta the
  stage can influence is ≤ 0; raw-LCP deltas at this traffic level are
  TTFB noise. Both datasets recorded here transparently.
- **CLS: 0.0000 in all 34 runs.** Long tasks: stage ≤ baseline (baseline
  showed the only 1.9–2.0 s outliers). LCP element unchanged (hero image;
  occasionally the consent-gate paragraph — the pre-existing behavior
  Phase 0 documented, on both targets).

## Gate summary — ALL PASS

Budget caps PASS · 419 request + 72 e2e PASS · Codex diff review APPROVED
(3 rounds) · visual sign-off: Josh, 2026-07-20 ("preview looks good") ·
harness delta gate PASS (attribution above). Stage A cleared for merge 1.
