# Plan: Phase 2 — Forest-world integration (in-world components, Journey map, connective tissue)
_Locked via grill-with-docs — by Claude + Josh, 2026-07-22. Rev 5 after Codex rounds 1-4. Terms per CONTEXT.md. Dials 9/8/4 (house-style)._

## Goal

Close the gap between Phase 1's environment layer and the original Forest-Journey
vision (docs/2026-07-18-forest-journey-redesign.md): the working UI itself becomes
part of the illustrated world. Every treated surface reads as one drawn world in
the Hack the North / Hook'em Hacks sense: containers are drawn objects, icons are
one hand-drawn language, and the saved view carries the personalized Journey map.
Josh's Phase 1 verdict ("trees look pasted on, matched things look the same,
underwhelming") is the failure this plan exists to reverse.

## Key decisions (grill-resolved)

1. **All three pillars ship in this phase:** (a) in-world components, (b) the
   Journey map rebuild, (c) connective tissue (glyph language, marginalia, hero
   moment).
2. **Level 2 diegesis is law on tool surfaces** (ADR 0002): every container is a
   drawn physical object (paper cards with deckled edges, carved wooden tier
   markers, trail-sign profile form, clipboard filters); the CONTENT inside
   stays the current clean type/data system. Level 3 only as single accents in
   the hero and the Journey map, never in match lanes.
3. **Journey map metaphor:** fixed landmark geography (Profile cabin -> Essays
   grove -> Deadlines watchtower -> Award summit) with saved Opportunities as
   markers positioned by Status, frontier flag, marker -> checklist. See "Stage
   2 is a migration" below — a six-stop Journey map already exists in prod.
4. **Art pipeline split by role:** chrome + glyphs are authored SVG in the
   Forest Light token palette; Higgsfield raster only for painterly assets
   (map terrain base, texture kit). **Credit budget: 46 credits, expiring
   2026-07-23, spend-down tonight:** comps (contract) -> map bases -> texture
   kit -> style-reference sheets. **Status: COMPLETE 2026-07-22, credits
   spent to zero** — artifacts catalogued in `.handoff/phase2-art/MANIFEST.md`
   (signed comps x3, chosen desktop terrain map-base-A + mobile portrait
   base, two vector glyph sheets, two paper-card SVG blanks, paper/wood
   textures). Not generated before credits ran out: carved-sign blank and
   fox/owl marginalia — both are hand-authored as SVG in Stages 1/3, with
   the lane comp as the sign reference. No Higgsfield dependency remains.
5. **Privacy rule for external AI tools (binding):** prompts, screenshots, and
   reference material sent to Higgsfield or any external generator contain
   synthetic data only — never a real student profile, saved opportunity,
   note, checklist state, or email. (Catalog facts are public and fine.)
6. **Perf gates HOLD, caps fixed NOW (pre-Stage-1, measured 2026-07-22):**
   - Landing mobile LCP < 2.5s, CLS < 0.1, no new render-blocking requests.
   - `style.css` (inlined on `/`): total gzip <= 27 KB (today 24.7 KB — the
     landing hero moment and landing glyph swaps live inside ~2.3 KB).
   - `world.css` (home of ALL tool-surface chrome): total gzip <= 14 KB
     (today 1.6 KB). Deferral is landing/SPA-path-only: template-family and
     legal pages load world.css render-blocking by design, so every stage's
     harness run also gates LCP for `/browse`, one Opportunity page, and
     `/privacy`: 5-run median <= pre-stage baseline + 100 ms and CLS <= 0.1
     per route.
   - `app.js` growth for map migration + chrome behavior: <= +6 KB gzip
     (today 47.4 KB).
   - Repeated-card DOM: <= 6 added nodes per card; SVG defs emitted once per
     document, namespaced `ec-*` to prevent duplicate-ID collisions.
   - Map rasters: desktop <= 90 KB, mobile <= 35 KB WebP (today 68.7/27.6).
   - Save-Data continues to suppress every world asset including map rasters.
7. **Comps are the visual contract** (signed by Josh before build) AND a
   written one: **DESIGN.md** is created in Stage 1 specifying the chrome
   primitives (paper card, carved marker, trail sign, clipboard), their
   states (hover/focus/active/disabled), token usage, glyph inventory with
   accessible-name rules, and the Level 2/3 boundary — so the system outlives
   the screenshots. Comp-vs-preview mismatch is a blocking gate failure.
8. **Staged on one branch, single merge** after the Stage 3 whole-site
   walkthrough; prod never shows a half-integrated state.

## Stage 2 is a migration, not a greenfield build

The saved view already renders `#journey-map` (app.js:2505 area): six
landmarks (Profile, Matches, Saved, Drafting, Submitted, Awarded) positioned
over `journey-map.webp` via CSS background, present in the DOM contract and
covered by tests. Stage 2 therefore:

- Replaces the six-stop stop-model with the four-landmark fixed geography;
  the five Status values map to **per-item marker positions** along the trail:
  interested/drafting markers sit between their stage landmarks, submitted at
  the watchtower, awarded at the summit, rejected in a quiet side clearing
  (kept honest, not hidden). The old milestone chips retire.
- Ships `computeJourneyMapState(items)` as a pure function with a written
  contract table BEFORE implementation, covering: frontier definition
  (furthest landmark with an item at or past it; profile cabin when nothing
  saved), awarded-only, all-rejected, checklist-complete-but-interested,
  and **tombstones** — saved rows whose catalog record is gone
  (`scholarship/program/competition: null`) render as a faded unnamed marker
  with count, matching renderSaved()'s skip behavior instead of silently
  disagreeing with it. Tombstone markers are **non-interactive**: one
  aggregated faded marker with a count and an accessible label ("N saved
  items whose listings were removed"), aria-disabled, excluded from the
  marker tab sequence — never a checklist button, since renderSaved()
  (app.js ~2605) renders no card for them. Unknown/future Status values:
  API-written rows cannot carry them (SavedStatus validation in
  app/models/auth.py + the account_routes PATCH guard, cited with tests in
  the contract table), but the DB columns are unconstrained strings, so
  computeJourneyMapState still carries a defensive default — any
  unrecognized status renders at the interested position, no crash, covered
  by a unit test with a synthetic bad row.
- Marker -> checklist: saved cards gain stable `data-saved-kind`/`data-saved-id`
  anchors; marker click scrolls to and expands that card's checklist with
  focus moved to it; keyboard: markers are buttons in one tab sequence with
  visible focus rings; e2e covers click, keyboard, and focus behavior.
- app.js, style.css/world.css, `tests/dom_contract.json`, and the existing
  journey-map tests are updated deliberately in one reviewed diff; the old
  map never coexists with the new one on a deployed surface.
- New terrain rasters live under `/static/img/world/` in the hashed world
  manifest (immutable cache + integrity tests apply automatically). The old
  map's raw CSS backgrounds — `url("/static/img/journey-map.webp")` and the
  mobile variant, style.css ~3148/~3213 — are removed and both old asset
  files deleted in the same diff.
- Save-Data / reduced-data: `html.save-data` (and `prefers-reduced-data`
  where supported) gets a vector-only map (no raster base); e2e proves zero
  map raster requests after saved-view activation under both signal channels.
- Status-change race fix ships WITH the map: the status select disables
  while its PATCH is pending (per-row), and the map re-renders only from the
  latest response; e2e covers rapid consecutive status changes.

## Approach

**Stage 0: art batch + contract — DONE 2026-07-22.**
1. Higgsfield spend-down complete (see decision 4); assets in
   .handoff/phase2-art/ + .handoff/phase2-comps/, synthetic data only.
2. Josh signed all three comps 2026-07-22 and chose map-base-A; the comps
   are the per-stage acceptance reference.

**Stage 1: component chrome system + glyph language.**
3. DESIGN.md written first (primitives, states, tokens, glyph inventory,
   accessibility rules). Then the SVG chrome kit + texture fills, authored
   against the caps in decision 6.
4. Glyph sweep with a pre-build inventory: every icon on treated surfaces is
   listed (source, usage, accessible name) before replacement; every control
   keeps a text label or aria-label; decorative glyphs get `aria-hidden`;
   focus states asserted per control. Stage B's three sprite glyphs fold in.
5. Apply chrome to: match Lanes (cards, tier headers, filters, near-miss
   group), Application plan tab, saved/tracker chrome, Browse/catalog,
   profile form, landing swaps (inside the style.css cap). Opportunity
   pages + the Browse hub and its lane listings via their world-frame path.
   Guides/legal/404:
   glyphs + light chrome only. /journey untouched.
6. Protection tests added BEFORE the chrome lands on those surfaces:
   - Opportunity pages: exact-snippet snapshot tests for the visible
     verification/source/estimated-deadline DOM (one scholarship, one
     program, one competition), beyond the existing JSON-LD byte tests.
   - Legal pages: snapshot-hash tests for privacy, terms, footer disclaimer,
     and consent-gate copy.
   - Hit-testing e2e (elementFromPoint) for: filters, save buttons, status
     selects, checklist labels, card links, on desktop + mobile viewports.
   - Visual QA matrix: Playwright screenshots of every treated route at
     375, 768, and 1280 px, including hover/focus/active/disabled states of
     the chromed components, captured per stage and diffed against the
     prior stage's set (and judged against the signed comps).
7. Stage 1 gates: both suites, byte caps measured in CI-style assertions
   (test_pages asserts gzip sizes against decision-6 caps), Codex diff
   review, Josh preview-vs-comp verdict.

**Stage 2: Journey map migration** (see section above).
8. Gates: suites + map e2e (marker positions track Status changes, tombstone
   state, empty/sample state, zero pre-activation fetches, Save-Data zero
   rasters, keyboard) + Codex diff review + Josh preview-vs-comp verdict.

**Stage 3: connective tissue + cohesion walkthrough.**
9. Gutter marginalia (one creature moment max), the landing hero diegetic
   frame, landing glyph swaps — all inside the style.css cap.
10. Whole-site cohesion walkthrough (Josh, against comps + references), then
    single merge, post-merge snapshot + prod harness delta.

## Observability (recorded per stage, in the stage ledger)

- Harness runs (Phase 0 protocol): LCP median + LCP element selector (and
  resource URL only when resource-backed), CLS contributors, long tasks.
- Request inventory: every world/chrome/map resource URL + transfer bytes,
  cold and pre-consented; separate Save-Data inventory proving suppression.
- Console: zero errors/warnings on treated surfaces (asserted in e2e).
- Map: marker count vs saved count reconciliation (tombstones counted),
  logged in the e2e assertions.
- Byte-cap table: measured vs cap for style.css, world.css, app.js delta,
  per-card added nodes, raster sizes.

## Risks / open questions

- The carved-sign blank and fox/owl marginalia were not generated before
  credits ran out and must be hand-authored as SVG matching the signed
  comps' style; if they cannot be made to match, the fallback is omitting
  the marginalia (allowed — it is a finish, not a pillar) and building the
  sign from the wood texture + vector strokes.
- Comp-to-build fidelity is the known failure mode of AI-comp pipelines; the
  per-stage comp-vs-preview gate exists to catch it.
- The six->four stop migration changes a shipped personalized surface;
  the computeJourneyMapState contract table is written and reviewed before
  any rendering code.

## Out of scope

- /journey changes, matcher logic, backend, schema (no migrations).
- The pre-existing duplicate-save race (concurrent saves can raise an
  unhandled IntegrityError in the three save routes, account_routes.py
  ~172/~223/~274) is explicitly accepted as a known issue this phase does
  not touch; queued as its own backend follow-up with rollback+reselect
  handling.
- Dark theme (light-only, standing decision). AI features stay dormant.
- Auto-anything on sponsor sites.
- The deferred Phase 1 nits ride along only if Stage 1 chrome naturally
  resolves them; otherwise unchanged.
