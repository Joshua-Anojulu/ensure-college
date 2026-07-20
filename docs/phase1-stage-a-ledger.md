# Phase 1 Stage A ledger — landing world + footer
_Branch phase1-forest-world; gates per docs/2026-07-20-phase1-forest-world.md._

## Budget gates (measured 2026-07-20, vs main @ 005e62b)

| Gate | Cap | Measured | Status |
|---|---|---|---|
| Inlined CSS growth (gzip -9) | ≤ 4,096 B | **+1,545 B** (21,707 → 23,252) | PASS |
| Landing HTML growth (gzip -9) | ≤ 6,144 B | **+565 B** (10,399 → 10,964) | PASS |
| DOM node growth | ≤ 40 | **+38** (3 plate divs, 5 plate imgs incl. owl+leaves, dusk div+img, fireflies 8, 4 trail SVGs × 5) | PASS |
| Trail SVG complexity | 1 path geometry per section link, no filters | 4 links, 1 geometry each — but 2 `<path>` nodes per link (dots + mask reveal share the same `d`); see deviations | PASS (as deviation) |
| World plate requests (landing) | ≤ 7 | 6 (clearing, waypoints, grove, owl, dusk ×1376 tier; 760 tier alternates) | PASS |
| Stage A world bytes | ≤ 360 KB desktop / ≤ 155 KB mobile | ~112 KB / ~47 KB (excl. overlook, deferred to Stage C) | PASS |

## Proof suites

- Request: **419 passed** (world manifest integrity ×2, immutable cache header,
  Save-Data class, world-reference scan, plus the full pre-existing suite)
- E2E: **69 passed**, including the five new world gates: hit-testing under
  plates, Save-Data zero world requests, firefly intersection toggle,
  reduced-motion static trail + fireflies, hero preload single-fetch
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

## Outstanding before merge

1. Vercel preview: dual-scenario attribution harness (cold + pre-consented),
   median of 5, delta ≤ +150 ms vs re-measured baseline, CLS < 0.1, TBT
   long-task delta ≤ 50 ms.
2. Codex diff review.
3. Josh's visual sign-off.
