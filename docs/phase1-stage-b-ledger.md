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

## Preview gates (run 2026-07-20, preview @ 18e88bc)

Representative pages (throttled mobile, median of 3, LCP attribution):

| Page | Median LCP | LCP element | World requests / bytes |
|---|---|---|---|
| /scholarships/coca-cola-scholars | 1600 ms (one TTFB-3602 cold-start outlier) | P.detail-description | 5 / 96 KB |
| /browse | 1144 ms | SPAN.footer-mark | 4 / 58 KB |
| /guides/essays | 1380 ms | P (guide copy) | 4 / 58 KB |
| 404 (unknown slug) | 1132 ms | SPAN.footer-mark | 4 / 58 KB |

World art never takes LCP on any template page. All under the 2500 ms
ceiling with full margin.

Landing delta re-check (median of 5 per scenario): cold 1380 ms
(render median ~958 ms), pre-consented 1304 ms - within +30 ms of the
Stage A prod measurements, render equal-or-better. CLS 0.0000 in all 10
runs; long tasks unchanged.

## Gate summary - ALL PASS

CSS-only reskin, suites 422 request + 75 e2e, Codex APPROVED (3 rounds:
6 findings round 1 - 5 accepted, 1 rejected with reasoning; 2 accepted
round 2), preview gates above. Awaiting Josh's sign-off for merge 2.

## Post-merge prod snapshot (2026-07-21, merge e482a9e)

Verified on ensurecollege.com after deploy (v=20260721-2):

- Template frame live on detail pages (body::before canopy from world.css);
  6 world requests on /scholarships/coca-cola-scholars.
- Landing fixes that rode the merge, all holding in prod:
  scroll-down-and-back blanking fix (elementsFromPoint hero guard passes),
  first catalog stat inked like its siblings, match-preview cards capped
  with internal scroller.
- Josh signed off in-session after verifying the preview; the blanking bug
  he reported (previously live in prod) is fixed by the merge.

Stage B complete. Next: Stage C (Journey + Teaser, merge 3).
