# UI cohesion pass (2026-10-17)

Branch `ui/cohesion-pass`, stacked on `fix/ec01-landing-load` (EC-01). An audit of every served surface for visual cohesion, accessibility and honest labeling, with fixes for everything that could be fixed without touching the catalog data, auth, the matcher or the Digest.

**Process note.** The plan-hardening chain (grill, then Codex review) was not run for this pass, because Codex was not available where the work was done. Nothing here is on the never-skip list. The changes closest to it are listed under "Review these directly" so a reviewer can check them first.

## Method

- One audit harness, run before (EC-01 head, b483b71) and after (branch head): 68 captures at 1440x900 and 390x844 covering the landing page, Preview, profile form, results, plan, Journey, opportunity pages, Browse, guides, 404, privacy, terms, the Digest unsubscribe pages and the login dialog.
- Width sweep: 13 pages at 13 widths from 320 to 1440px, checking for sideways overflow.
- Contrast: text over the World art was pixel-sampled at four widths, because computed colors cannot see the painting behind the text.
- Structure: exactly one h1 per page, a main landmark, a skip link, and an accessible name on every control.

## Results

| Check | Before | After |
|---|---|---|
| Sideways overflow, summed over all captures | 1,358px | 0 |
| Captures without exactly one h1 | 12 | 0 |
| Controls with no accessible name | 16 | 0 |
| Captures missing a main landmark | 2 | 0 |
| Captures missing a skip link | 6 | 2 (the unsubscribe pages, which have one header link before main) |
| Text over World art below WCAG AA | 22 of 75 samples | 0 of 104 |
| Pages that overflow at some width from 320 to 1440px | 9 | 0 |

Findings: 54 (5 High, 24 Medium, 25 Low). 36 fixed, 18 left, each with a reason.

| Severity | Total | Fixed | Left |
|---|---|---|---|
| High | 5 | 5 | 0 |
| Medium | 24 | 18 | 6 |
| Low | 25 | 13 | 12 |

## Findings

| ID | Sev | Surface | Evidence | Status |
|---|---|---|---|---|
| H1 | High | Opportunity pages, Browse, guides, 404 and Journey on phones | Scrolled 10 to 80px sideways at 320 to 414px; header links wrapped into fragments | Fixed 7813eb0 |
| H2 | High | Browse lane pages, all widths | Rows up to about 3,000px wide: the meta line could not wrap and can hold a whole recognition paragraph | Fixed 7813eb0 |
| H3 | High | Landing Teaser | White copy over the pale painting: 1.1:1 on phones, 2.8:1 on tablets, 4.0:1 at line ends on desktop | Fixed eec110e |
| H4 | High | Footer on every page; Teaser button | Keyboard focus ring 1.0:1 on the footer, 1.3:1 on the Teaser | Fixed 3394a81 |
| H5 | High | Opportunity pages and match cards | Raw VERIFY placeholders shown to students: page title "Golden Door Scholars: VERIFY scholarship", award "VERIFY", recognition "VERIFY", and a curator research note shown as recognition | Fixed 156d97f |
| M1 | Med | Signed-in header on phones | Saved, Settings and Log out did not fit at 320 to 390px | Fixed 7813eb0 |
| M2 | Med | Server-rendered pages over the World art | Breadcrumbs, eyebrows and summaries at 1.4 to 3.9:1 | Fixed eec110e |
| M3 | Med | Lanes with few results | Lane summary at 2.4:1 over the art | Fixed eec110e |
| M4 | Med | Small text colors | `--muted-2` used for text at 3.7:1; `--accent-deep` on the amber tint at 4.49:1 | Fixed eec110e |
| M5 | Med | Journey map stops; Journey rail | Stops ahead faded to 0.55 opacity: 2.1 to 3.7:1 | Fixed eec110e |
| M6 | Med | Landing stats; grove intro | Labels over ferns; intro at 4.0 to 4.4:1 | Fixed eec110e |
| M7 | Med | Profile form | Backing sheet painted over the form, tinting the whole panel green | Fixed af2dabe |
| M8 | Med | Program and competition cards | Unstarted Checklist steps wore the success check | Fixed af2dabe |
| M9 | Med | Browse, guides and 404 | No h1; guide pages skipped heading levels | Fixed af2dabe |
| M10 | Med | Guide pages | No inner padding; doubled list indents | Fixed af2dabe |
| M11 | Med | Privacy and Terms | No skip link or main landmark; favicon 404; stray middots; eyebrow style overridden | Fixed af2dabe (legal copy untouched) |
| M12 | Med | Match cards, Quick apply, near-miss and recommendation-letter rows | Estimated deadlines lost their "~"; the deadline-sort e2e test passed without checking anything | Fixed 156d97f |
| M13 | Med | Opportunity pages | An unknown deadline read "Not yet published" (we do not know that); stale estimates posed as upcoming deadlines | Fixed 156d97f |
| M14 | Med | Saved opportunity controls | Status and Notes had no accessible name | Fixed 156d97f |
| M15 | Med | Digest unsubscribe pages | Retired Highlighter palette | Fixed bab49c6 |
| M16 | Med | Plan, signed out | Two contradictory messages and no way to act | Fixed a8064f7 |
| M17 | Med | Journey intro | 2.4 to 4.0:1 over the sky | Fixed a8064f7 |
| M18 | Med | Social card (og-image.png) | Broken logo mark; printed the internal name FOREST LIGHT; its source file was still Highlighter | Fixed ea689bf |
| M19 | Med | Catalog text | 11 free-text values in 7 entries still carry curator notes that mention VERIFY (science-olympiad-national-tournament, junior-science-and-humanities-symposium, zero-robotics, physicsbowl, usa-biology-olympiad, us-national-chemistry-olympiad, golden-door-scholars) | Left: data |
| M20 | Med | Catalog text | 40 em dashes and 111 en dashes in the four data files | Left: phase2 commit 21a09ae normalizes them |
| M21 | Med | Password reset, Digest and new-match emails | Old palette | Left: auth and Digest code |
| M22 | Med | "Why this matched" on match cards | Caveats show under the same green check as met criteria | Left: matcher |
| M23 | Med | Tool surfaces | In-world chrome (ADR 0002) not built | Left: Phase 2 |
| M24 | Med | Journey map, signed out | No sample path, although CONTEXT.md says it shows one | Left: Phase 2 |
| L1 | Low | Quick apply and near-miss rows on phones | Centered rows with staggered left edges | Fixed 7813eb0 |
| L2 | Low | Landing photo band | Photo stopped short of its frame (37px at 1440, 81px at 1024) | Fixed af2dabe |
| L3 | Low | Out-of-date verification strip | A tint but no box | Fixed af2dabe |
| L4 | Low | Buttons with a trailing arrow | Arrow touched the label | Fixed af2dabe |
| L5 | Low | Footer links | Centered under left-aligned text | Fixed af2dabe |
| L6 | Low | Journey favicon | Mismatched version pin | Fixed af2dabe |
| L7 | Low | Copy | Browse list labels; an em dash in the fit-ring label; plan-card separators | Fixed 156d97f |
| L8 | Low | Dialog backdrops, pressed buttons, footer rule, photo wash | Old-palette color values | Fixed bab49c6 |
| L9 | Low | style.css | About 2 KB of dead rules; comment bytes on the critical path | Fixed bab49c6, af6f3fd |
| L10 | Low | Headings | Inherited the body's 1.6 line-height | Fixed a8064f7 |
| L11 | Low | Preview error; filters on phones | Spacing; filter widths | Fixed a8064f7 |
| L12 | Low | Landing stats; account pitch | Hover lift on plain text; off-system eyebrow | Fixed fccb959 |
| L13 | Low | Teaser landmark labels | "Profile" chip at 3.1:1 under the scrim, made worse by this branch's wider scrim | Fixed 942cfbd |
| L14 | Low | Opportunity pages | Paragraph-length award text in the stat slot | Left: data or design call; phase2 locks one such value |
| L15 | Low | Award amounts | Unformatted numbers ("20000") | Left: data; phase2 locks the string |
| L16 | Low | Plan delete | The browser's built-in confirm box; its copy leaves out competitions | Left: the delete flow changes student data |
| L17 | Low | docs/brand; og-image.svg | Still the Highlighter brand | Left: Josh's call; phase2 edits the SVG |
| L18 | Low | Search inputs | Browser-default blue clear button | Left: Phase 2 filter chrome |
| L19 | Low | Filters | "Clear filters" sits on its own row | Left: Phase 2 filter chrome |
| L20 | Low | Buttons and links | Unicode arrows and checks instead of World glyphs | Left: Phase 2 Stage 1 |
| L21 | Low | Journey map | 9.6px labels | Left: Phase 2 Stage 2 (its new labels are 9 to 10px too) |
| L22 | Low | Landing Preview | Empty forest beside it | Left: deferred Phase 1 nit |
| L23 | Low | Teaser and Journey console | three.js deprecation warning | Left: needs a vendor upgrade |
| L24 | Low | Match cards | Hidden `.path-bar` still emitted | Left: a DOM-contract change, best done with Phase 2 |
| L25 | Low | Short lanes and the empty plan | An 18px strip of art cut off under the panel | Left: Phase 2 Stage 3 |

## Review these directly

- **Digest unsubscribe pages, `app/main.py` (bab49c6).** Only the HTML wrapper changed: both pages now share `_reminder_page()` with the site header and stylesheet. The token is still escaped with `html.escape(..., quote=True)`; the form, the POST handler and the Digest cron are unchanged. The stylesheet link has no `?v=` on purpose (see the docstring), so it adds no lockstep location.
- **Plan, signed out (a8064f7).** Rendering only. Adds `saved-signed-out`, `saved-signup-btn` and `saved-login-btn` to `tests/dom_contract.json`, deliberately.
- **Placeholder labeling, `app/seo_pages.py` and `app.js` (156d97f).** No catalog value changed. A VERIFY placeholder is never shown raw, including values that carry a curator note after the token. Opportunity pages now label deadlines exactly as the match cards already did:

  | Data | Value | Note |
  |---|---|---|
  | Real date | the date | none |
  | `rolling` | Rolling | Applications accepted anytime |
  | Estimated deadline, upcoming | ~date | Estimated; confirm on sponsor site |
  | Estimated deadline, already past | Not yet announced | Last cycle closed Month Year; check sponsor site |
  | VERIFY, no estimate | Not listed | Confirm on sponsor site |

  An unknown award reads "Not listed / Confirm on sponsor site" in the facts panel, and the page title and meta never carry one.
- **Landing CSS.** The stylesheet inlined into `/` grows by 648 B gzip across the branch (24,303 to 24,951) after about 2 KB of dead rules were removed. LCP was not re-measured. At Lighthouse's throttled 1.6 Mbps, 648 B is about 3 ms against the 40 ms margin to the 2.5 s gate.
- **Social card (ea689bf).** `og-image.png` is redrawn. Platforms cache the card, so links shared before the deploy can show the old one until they are re-scraped.
- **Existing test changed.** `test_e2e.py`'s deadline-sort test now checks the order within each match-quality group and fails if no estimated deadline carries its "~". The old version had been passing without checking anything.

## Left, and why

- **Catalog text** (M19, M20, L14, L15). Fixing these means editing catalog values, which needs its own pass against the sponsors' official pages. M19 is the most visible: Golden Door Scholars' special-check text tells students that a field "is set to VERIFY" and that the wording "should be confirmed by a reviewer". Phase 2 already handles the dashes.
- **Off limits for a UI pass** (M21 auth and Digest emails, M22 the matcher's reason types, L16 the delete flow for saved student data).
- **Belongs to Phase 2** (M23, M24, L18 to L21, L24, L25).
- **L17.** Rewriting the brand doc is Josh's call, and phase2 edits og-image.svg.
- **L22** is a deferred Phase 1 nit. **L23** needs a three.js upgrade.

## phase2-integration: status and merge notes

**Status.** Three commits from 2026-07-23 on main c41e720: 21a09ae (Stage 1, component chrome and glyph language), c25b1ed (Stage 2, contract table) and 035b83d (Stage 2, Journey map rebuilt on four landmarks). Stages 1 and 2 are built and pass on their own (445 request; 96 e2e passed and 1 skipped, plus the 2 sandbox-only teaser failures noted under Verification). Stage 3 (marginalia, the landing hero frame, landing glyph swaps, the whole-site walkthrough and the single merge) has not started. The Stage 1 and 2 Codex reviews, Josh's preview-versus-comp verdicts and stage ledgers were never recorded. The signed comps lived in the gitignored `.handoff/`; the old checkout was under OneDrive (Documents/ScholarMatch), which may still have them.

**Do not merge it yet.** PLAN.md decision 8: "single merge after the Stage 3 whole-site walkthrough; prod never shows a half-integrated state." Merging now would put tool surfaces in wood-and-paper chrome while the landing page stays Phase 1. Its new Journey map also has 9 to 10px labels and tombstones at 0.6 opacity, the fade-to-recede pattern this pass removed elsewhere.

**When it merges onto this branch** (trial merge: 476 request passed; 145 e2e passed and 1 skipped; of 4 e2e failures, 2 were the sandbox-only teaser tests, 1 is the test to retire below, and 1 was fixed on this branch in 65ce5a9):
- 10 conflicts. 8 are `?v=` pins: take a fresh lockstep bump. In privacy.html and terms.html keep both this branch's skip link and phase2's chrome defs, defs first, as base.html does. In style.css take phase2's deletion of the old six-stop map rules.
- Retire or retarget `test_journey_map_stops_ahead_stay_legible`: it targets the map phase2 removes.
- The stylesheet lands at 26,785 B gzip against phase2's 27,648 cap, leaving about 860 B for Stage 3. world.css is 1,954 against 14,336.
- Recheck the new map's label sizes and tombstone opacity against M5 and L21.

**To ship Phase 2:** recover the comps or re-sign them; run the skipped Stage 1 and 2 gates (Codex review, verdicts, ledgers, `STAGE1_VISUAL_QA=1`); build Stage 3 inside the remaining bytes; merge once with a fresh lockstep bump and the resolutions above.

## Verification

At the branch head:
- Request suite: 462 passed (EC-01 baseline 457; +5 placeholder-labeling tests).
- E2E suite: 132 passed, 0 failed, with pages told they have 8 cores (see the last point). The fixes are covered by 47 new test cases (27 tests, some run per page or width) in `tests/e2e/test_cohesion.py`.
- `scripts/validate_dataset.py`: exit 0, no structural errors. No catalog file changed.
- GitHub CI caught one case the sandbox runs missed. "load" can fire before Satoshi swaps in, and on the fallback font the privacy and terms headers ran 2 to 4px past a 320px screen. The headers now have room on either font at 320px, and the overflow test checks both states: once after the web fonts load, once with them blocked.
- In a 2-CPU sandbox, `test_landing_teaser_paints` and `test_teaser_painting_first_and_same_box_swap` fail at the EC-01 baseline too: journey-teaser.js treats the machine as low-end and keeps the static painting. Both pass when the page reports 8 cores.
