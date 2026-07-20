# Phase 1 asset inventory
_Per docs/2026-07-20-phase1-forest-world.md Stage 0. No unlisted asset ships.
All plates: watercolor Forest Light, generated 2026-07-20 (nano_banana_2,
shared style block, NO baked text/UI), processed by the committed Pillow WebP
generator, shipped content-hashed under `app/static/img/world/` with
`Cache-Control: public, max-age=31536000, immutable`._

Cost classes: `css` = CSS-only (no asset) · `img` = one image · `script` =
script-driven behavior on top of an image.

## Stage A — landing world

| Plate | Cost class | Format / crops | Byte target (desktop / mobile) | Load | Reduced-motion |
|---|---|---|---|---|---|
| `clearing` (stats backdrop, ferns + horizontal trail) | img | WebP q32, 1600w + 760w | ≤ 60 KB / ≤ 25 KB | lazy, `fetchpriority=low`, inert `data-src` (Save-Data) | static (it is static art) |
| `waypoints` (proof backdrop, 3 posts on diagonal trail; chips are DOM anchored to tuned % coords) | img | WebP q32, 1600w + 760w | ≤ 65 KB / ≤ 28 KB | lazy, low, inert | static |
| `grove` (difference backdrop, edge pines + canopy shafts, mist center) | img | WebP q32, 1600w + 760w | ≤ 65 KB / ≤ 28 KB | lazy, low, inert | static |
| `overlook` (Teaser painting; landmark labels are DOM/SVG overlays) | img | WebP q40 (hero-class), 1600w + 760w | ≤ 90 KB / ≤ 40 KB | lazy, low, inert | painting is the reduced-motion mode |
| `dusk-treeline` (footer band; fireflies NOT baked — CSS dots) | img | WebP q32, 1600w + 760w | ≤ 55 KB / ≤ 22 KB | lazy, low, inert | static |
| `owl` (grove boundary creature) | img | WebP q40, 320w | ≤ 12 KB | lazy, low, inert, ≥1200px only | static |
| `leaves` (clearing boundary drift) | img | WebP q40, 320w | ≤ 10 KB | lazy, low, inert, ≥1200px only | static |
| Trail SVG (inline, one path per section link, no filters) | css/script | inline SVG | HTML growth ≤ 6 KB gzip, ≤ 40 nodes | inline | static path (no draw-on) |
| Fireflies | css | none | 0 | n/a | none (class never applied) |
| Hero art | — | UNCHANGED, exempt (byte-identical preload contract) | — | — | — |

**Stage A aggregates:** ≤ 7 world-plate requests total, ≤ 360 KB desktop total
(≤ 155 KB mobile), 0 first-viewport bytes (everything below fold, hero exempt
and unchanged), max 3 parallel image requests expected at any scroll depth,
decoded memory ≈ 1600×900×4×5 ≈ 29 MB desktop worst case (plates decode
lazily, not simultaneously in practice).

## Stage B — tool views + template family

| Plate | Cost class | Format / crops | Byte target | Load | Reduced-motion |
|---|---|---|---|---|---|
| `stage-tools` (one quiet-center full scene reused behind all SPA views) | img + script (`world.css` on first activation, `.world-ready` fade) | WebP q32, 1600w + 760w | ≤ 55 KB / ≤ 22 KB | on first SPA-world activation only | fade off; static |
| `canopy-edge` (template top strip, on-canvas bg) | img | WebP q32, 1600w shallow band | ≤ 25 KB | lazy | static |
| `fern-corner-left` / `fern-corner-right` | img | WebP q32, 640w | ≤ 18 KB each | lazy | static |
| `glyph-sheet` (world-glyph sprite, one inked sheet, 12 glyphs on 4×3 grid) | img | WebP lossless-ish q80, 960w | ≤ 40 KB | lazy (facts panels only) | static |

**Stage B aggregates:** template family adds ≤ 4 requests / ≤ 105 KB per page,
identical URLs on all 322 pages (immutable-cached after first page). SPA adds
≤ 2 requests (`world.css` + `stage-tools`) after activation, never pre-LCP.

## Stage C — Journey + Teaser

| Asset | Cost class | Notes |
|---|---|---|
| Journey clay reskin | script | three.js materials/fog/palette only — no new plates; existing perf gate + reduced-motion fallback kept |
| Paper overlay | css | reuses existing `grain.png` (already shipped) |
| Teaser live swap | script | `journey-teaser.js` on idle/visibility, same-size box; painting (`overlook`) is the fallback |

## Visual contract (not shipped)

- Regenerated comps `07-app-lane` and `08-detail-page` at full-scene
  quiet-center → `.handoff/phase1-comps/` (Josh's sign-off reference).

## Generation ledger

14 generations planned (≈ 28 credits) + ~15-credit redo reserve. Raw plates
land in `.handoff/phase1-plates/` for QA before Pillow processing; QA rejects
any plate that drifts from the comp set's palette/register or contains any
text/UI.
