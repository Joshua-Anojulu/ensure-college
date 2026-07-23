# Phase 2 Stage 1 Chrome And Glyph Contract

This file defines the Stage 1 production contract for the Forest Light work surfaces. It implements Level 2 diegesis from `docs/adr/0002-level-2-diegesis-on-tool-surfaces.md`: containers are drawn physical objects, while the information inside them stays clean, honest, and scannable.

## Chrome Primitives

| Primitive | Form | Surfaces | States |
| --- | --- | --- | --- |
| Paper card | Cream paper sheet with uneven ink edge, soft paper grain, and one brass pin. The card content remains a plain layout inside the sheet. | Match cards, catalog cards, saved cards, guide cards, legal/detail content cards where light chrome is allowed. | Hover lifts by one tokenized depth step and darkens the ink edge. Focus-visible on links/buttons uses the site focus ring above the sheet. Active lowers the lift. Disabled lowers opacity only on controls, never on the card copy. |
| Carved tier marker | Wooden plank sign with a hand-cut silhouette, subtle grain strokes, and carved label text. | Strong, Possible, and Special check tier headers across the three Lanes and near-miss groups. | Hover is not applied because headings are static. Focus is not applicable. Tier state is expressed by text and tone, not by animation. |
| Trail-sign form frame | Light wood frame around a paper center, as if a form is clipped to a trail marker. | Profile form, Opportunity tabs, Browse hub panels, application plan guidance, guide/legal/404 light panels. | Hover is neutral unless the component contains a direct link. Focus-visible remains on the inner control. Disabled form fields keep native disabled affordances. |
| Clipboard filter panel | Narrow wooden clipboard body with a brass clip and paper inset. | Scholarship, program, competition, and catalog filter panels. | Hover is neutral. Focus-visible on every contained input, select, checkbox, and button must be visible over the panel. Active only applies to buttons inside the panel. Disabled controls keep a visible label and reduced opacity. |

## Token Rules

Chrome color comes from existing Forest Light tokens in `style.css`. New CSS may reference tokens, gradients of tokens, alpha-adjusted tokens, and SVG masks. New hex literals are forbidden outside the root token block, mask-image data, or the existing test allowlist.

Use only site easing tokens for transitions. Any new transform or opacity motion must be suppressed under `prefers-reduced-motion: reduce`. Save-Data must suppress new raster requests. Stage 1 chrome is SVG and CSS-first, with raster textures optional and skipped unless they stay inside byte caps.

## Glyph Inventory

Every glyph is decorative unless the table names an accessible control. Clickable controls keep visible text or an `aria-label`; glyphs never act as controls by themselves.

| Glyph | Replaces Current Icon | Usage Sites | Accessible Name |
| --- | --- | --- | --- |
| `ec-glyph-scholarship` | Generic lane marker | Scholarship lane headers, catalog scholarship kind | `aria-hidden="true"` |
| `ec-glyph-program` | Generic lane marker | Program lane headers, catalog program kind | `aria-hidden="true"` |
| `ec-glyph-competition` | Generic lane marker | Competition lane headers, catalog competition kind | `aria-hidden="true"` |
| `ec-glyph-match` | Numeric-only fit cue | Match quality headers, fit summary decoration | `aria-hidden="true"` |
| `ec-glyph-award` | Award stat marker | Award, cost, recognition stat labels | `aria-hidden="true"` |
| `ec-glyph-deadline` | Deadline stat marker | Deadline stat labels, deadline sort affordance | `aria-hidden="true"` |
| `ec-glyph-source` | Verification/source marker | Verified source text and source links | `aria-hidden="true"` |
| `ec-glyph-save` | Plain save affordance | Save buttons and saved-plan empty state | Control keeps text: `Save`, `Saved`, or `Remove` |
| `ec-glyph-plan` | Plain plan affordance | Plan tab, saved/tracker panels, application plan guidance | Control keeps text: `Plan` or panel heading text |
| `ec-glyph-filter` | Plain filter affordance | Clipboard filter panels and clear filter controls | Filter controls keep labels |
| `ec-glyph-search` | Browser-default search field only | Search inputs in match and Browse filters | Input keeps associated label |
| `ec-glyph-checklist` | Plain checklist marker | Application checklist and recommendation-letter rollup | `aria-hidden="true"` |
| `ec-glyph-status` | Plain status select marker | Saved opportunity status select row | Select keeps label `Status` |
| `ec-glyph-link` | Text arrow and external-link arrow | Card links, source links, guide links | Link keeps visible text |
| `ec-glyph-profile` | Form-section marker | Profile form and profile completion surfaces | `aria-hidden="true"` |
| `ec-glyph-school` | School badge marker | School and target-school badges | `aria-hidden="true"` |
| `ec-glyph-essay` | Essay/draft marker | Essay advice, essay prompts, guide cards | `aria-hidden="true"` |
| `ec-glyph-special` | Warning-like special check marker | Special check badges and near-miss groups | Text carries the warning meaning |
| `ec-glyph-browse` | Catalog marker | Browse hub and catalog kind tabs | Controls keep text |
| `ec-glyph-legal` | Plain legal page marker | Privacy, terms, guides, and 404 light chrome | `aria-hidden="true"` |
| `ec-glyph-clear` | Plain clear button | Clear filter buttons | Button keeps text `Clear filters` |

## Level Boundary

Level 2 is the maximum for Stage 1 work surfaces. Cards, filters, form frames, tabs, legal panels, and tracker surfaces may look like paper, wood, brass, ink, and trail signs. They may not gain creatures, environmental props that compete with controls, or world geography that implies navigation.

Level 3 remains reserved for immersive surfaces: the existing hero world, the Journey, the Journey map migration in Stage 2, and marginalia creatures in Stage 3. Stage 1 must not change `/journey`, `#journey-map`, or add marginalia.

## Journey Map State Contract (Stage 2)

`computeJourneyMapState(items)` is a pure function. Inputs are pre-derived by
the caller so the function needs no clock, no DOM, and no fetch: each item is
`{ kind, id, title, status, deadlineSortKey, hasCatalog }`, where
`deadlineSortKey` is the existing real -> estimated -> none ordering already
used by the lanes, and `hasCatalog` is false when the saved row's catalog
record is gone (renderSaved() skips these). Output:
`{ sample, frontier, markers, tombstoneCount, rejected }`.

Geography: fixed landmarks along the Trail - Profile cabin, Essays grove,
Deadlines watchtower, Award summit - over the map-base-A painting; a side
clearing off the trail holds rejected items.

| # | Input condition | Output |
|---|---|---|
| 1 | `items` empty (nothing saved / signed out) | `sample: true` - labeled generic sample path, no personal markers |
| 2 | `status: "interested"` | marker on the cabin->grove segment |
| 3 | `status: "drafting"` | marker on the grove->watchtower segment |
| 4 | `status: "submitted"` | marker at the watchtower |
| 5 | `status: "awarded"` | marker at the summit |
| 6 | `status: "rejected"` | marker in the side clearing; excluded from frontier |
| 7 | unrecognized status string (DB columns are unconstrained; API rejects these, belt-and-suspenders) | treated as `interested`, no crash, no console noise |
| 8 | `hasCatalog: false` (tombstone) | not an individual marker; folded into ONE aggregated faded marker near the trailhead with `tombstoneCount`, non-interactive, `aria-disabled`, out of the tab sequence, label "N saved items whose listings were removed" |
| 9 | checklist complete but status still `interested` | Status is authoritative: position does NOT advance; checklist progress never moves markers |
| 10 | frontier | the landmark the most advanced non-rejected, non-tombstone item is walking toward: interested->grove, drafting->watchtower, submitted->summit, awarded->summit with the flag planted at it |
| 11 | only rejected items (plus tombstones) | frontier: cabin; side clearing populated; not sample mode |
| 12 | only tombstones | frontier: cabin; real map (not sample) with only the aggregated tombstone marker |
| 13 | ordering within a segment | by `deadlineSortKey`, then title; positions staggered deterministically by index (no randomness) |
| 14 | marker interaction (non-tombstone) | markers are buttons in one tab sequence with visible focus rings; activation scrolls to and expands that item's checklist via its `data-saved-kind`/`data-saved-id` anchor and moves focus to it |

Unit tests cover every row, including a synthetic bad-status row (7) and a
synthetic tombstone row (8). The function asserts exhaustiveness over the
five known Status values with row 7 as the only fallback path.
