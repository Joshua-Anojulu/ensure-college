# Phase 1 Stage B ledger — tool views + template family
_Branch phase1-forest-world; gates per docs/2026-07-20-phase1-forest-world.md._

## What shipped

`world.css` carries the whole stage: the quiet-center scene + canopy/fern
frame + world glyphs for the template family and legal pages (CSS-only —
verification labels and JSON-LD byte-identical, enforced by host-normalized
goldens in tests/goldens/), and the SPA quiet-center stage behind the
results-section family, activated by the first `activateOpportunityView`
call (Save-Data gated) with `.world-ready` set only in the stylesheet load
callback. Landing critical path untouched (world.css never linked there —
tested).

## Deviations (logged, arbiter-accepted)

- **`#profile-form` is not staged** (plan listed the profile form among SPA
  views): the form is itself an opaque `panel` — staging behind it renders
  zero pixels. The world surrounds it via the landing canvas.
- **Template-family Save-Data is media-query-only** (`prefers-reduced-data`):
  those responses are edge-cached (`s-maxage=86400`), so a per-header HTML
  variant would poison the shared cache. Legal pages (no-cache) and the
  landing reflect the header server-side; decorative art is ~113 KB,
  immutable and shared, accepted residual for cached pages on browsers
  without the media query.
- **SPA stage is a CSS background pseudo, not `<picture><img>`**: fetch
  timing is governed by world.css activation (post-LCP by construction),
  backgrounds reserve no layout (CLS-free), and the DOM contract is
  untouched entirely.
- **Representative-page gate runs pre-merge** on the Vercel preview (like
  Stage A's harness): one Opportunity page, /browse, one guide, and 404 —
  request budget + LCP attribution. Results recorded below when run.

## Proof suites

422 request + 75 e2e green, including: template family + legal + 404 carry
the frame while the landing never links world.css; JSON-LD byte-goldens for
verified (coca-cola-scholars) / unverified (conrad-challenge) / estimated
(dell-scholars); Save-Data reflection on legal pages; e2e waterfall gate
(no world.css before #nav-browse-btn, exactly one request after, stage
visible); template frame + glyphs + request budget; forced-colors smoke
(decoration suppressed, primary action clickable).

## Outstanding before merge

1. Preview gates: representative pages (opportunity/browse/guide/404)
   request budget + LCP attribution; landing harness delta re-check.
2. Codex approval.
3. Josh's visual sign-off (detail page + catalog stage screenshots shown
   in-session; final call on the preview).
