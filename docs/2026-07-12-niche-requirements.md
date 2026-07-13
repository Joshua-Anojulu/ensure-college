# Plan: Niche-requirement special checks + honest guidance placeholders

_Locked via grill — by Claude + Joshua_

## Goal

Every hard eligibility requirement in the catalog that the profile cannot verify is encoded as a special check — surfaced in the "Special opportunities to check" group, never as a Strong match — instead of living only in description prose where the matcher ignores it (the Norman Beery failure mode, found ~30 more times in a full-catalog survey). Additionally, the application-guidance layer becomes visibly honest when essay-prompt data is missing, so saved opportunities without verified prompts say so instead of showing nothing.

## Background (survey results, 2026-07-12)

A pattern scan of all 322 opportunities found ~30 entries whose descriptions state hard requirements with no `special_requirements` (or demographics) encoding:

- disability (6): lime-connect-pathways-scholarship, microsoft-disability-scholarship, anne-ford-scholarship, +3
- military/veteran family (5 candidates, some likely incidental mentions): jack-kent-cooke-college, taco-bell-live-mas-scholarship, scholastic-art-writing-awards, +2
- immigrant/undocumented (4): aiga-worldstudio-dxd-scholarships, maldef-law-school-scholarship, paul-daisy-soros-new-americans, rhodes-scholarship
- women-only (3): society-of-women-engineers-scholarship, +2
- athletics (3): foot-locker-scholar-athletes, wharton-moneyball-academy (P), princeton-laboratory-learning-program (P)
- program-content specifics (3): sallie-mae-bridging-the-dream-graduate, ashrae-scholarship-program, asme-mechanical-engineering-scholarships
- LGBTQ+ (2): point-foundation-flagship, american-statistical-association-pride-scholarship
- partner-school (1): questbridge-match
- employer (1): burger-king-scholars
- membership (1): congressional-app-challenge (C)
- singles: hagan-scholarship (service hours), mathematical-association-of-america-scholarships (hardship event), vegetarian-resource-group-college-scholarship

Categories already fully covered by the existing mechanism (no work needed): nomination 18/18, tribal 5/5, scouting 3/3, first-generation 3/3, religion 2/2.

## Approach

1. **Extend `SpecialRequirement.kind`** (`app/models/scholarship.py`, mirrored in program/competition models if they define their own) with three new values, under an explicit **kind-reuse rule**: existing kinds keep their meaning and existing entries are not migrated — `military_affiliation` continues to cover military/veteran-family ties, `family_or_affiliation` continues to cover family/heritage/organization ties (it already holds first-gen and Elks/K-of-C entries). New kinds are used only where no existing kind fits: `identity_or_status` (disability, gender, LGBTQ+, immigration status, foster care), `program_content` ("program that substantially incorporates statistics", ABET-accredited), `activity_or_lifestyle` (varsity athletics, community-service hours, vegetarian/vegan commitment). No database migration — special requirements are dataset-side; profiles and saved data are untouched.
2. **Adjudicate each survey candidate from its already-verified description.** For each of the ~30: if the description states a hard requirement ("must be", "limited to", "open only to", "for X only"), add a sidecar `special_requirements` entry (scholarships: `app/data/special_requirements.json`; programs/competitions: inline `eligibility.special_requirements`) whose label/details restate the verified prose — no new sponsor facts are introduced, satisfying the data-honesty rule without a re-verification pass. **A written skip list with per-entry rationale is produced before encoding**: candidates whose mentions are alternatives, inclusions, or context (likely: burger-king-scholars, jack-kent-cooke-college, scholastic-art-writing-awards, aiga-worldstudio ["and/or"], maldef [inclusive], point-foundation/asa-pride if "and allies", wharton-moneyball [sports as subject matter]) are skipped, following the simon-youth precedent. Expected outcome: roughly 15-20 encoded, 10-15 skipped.
3. **Extend the validator guard** (`scripts/validate_dataset.py`): extract the first-generation check into a shared niche-requirement guard driven by a small table of high-precision category patterns (requirement phrasing + category term), and call it from all three audits (`audit_dataset`, `audit_programs`, `audit_competitions`). Warning-level only — never a structural error. **Hard constraint: `tests/test_dataset.py:25` asserts the real catalog is warning-free**, so after step 2 the guard must fire zero warnings on the live catalog; warning behavior is tested with synthetic fixtures, including negative cases for known trap phrasings ("regardless of immigration status", "LGBTQ+ and allies", "DACA status alone does not qualify").
4. **Add a duplicate guard for the loader's inline+sidecar concatenation** (`app/data/loader.py:31-35` concatenates without dedupe): a validator error (or test) that flags the same special-requirement label appearing twice for one opportunity.
5. **Render special requirements on opportunity pages**: pass `special_requirements` explicitly from the context builder in `app/seo_pages.py` into `app/templates/detail.html` (match cards already render them via `buildSpecialRequirements`); add an opportunity-page rendering test. An opportunity page must never look cleaner than the match card.
6. **Honest guidance placeholder** (`app/static/js/app.js`): in `buildPromptBlock`, when a requirement is a writing requirement (existing `isWritingRequirement`) with no `essay_prompts` data, render "Essay prompts not yet verified — check the sponsor page." styled like the existing gated-prompt note. `buildPromptBlock` feeds both checklist rows and the essay reuse map — browser-verify both surfaces, specifically that the note inside checklist `<label>` rows does not toggle the checkbox (the existing preventDefault handler covers non-`<details>` blocks; confirm it).
7. **Tests + verification**: model tests for the new kinds; validator tests (synthetic fixtures, positive + negative); opportunity-page rendering test; a wiring assertion in `tests/test_essay_prompts.py` that the placeholder text ("Essay prompts not yet verified") appears in `app/static/js/app.js`; existing matcher tests stay green (matcher code is untouched — it already sets `requires_special_check` from `special_requirements`). The loader duplicate guard compares normalized `(kind, label)` after the sidecar merge, not exact strings. Browser-verify the placeholder (both surfaces) and one newly special-checked entry locally, and glance at the grown special-check group's rendering (it is a plain section, not collapsible — if it feels heavy at ~+20 entries, note a follow-up rather than scope-creeping). Run `scripts/validate_dataset.py` + full pytest; bump asset cache-bust version (index.html + tests/test_pages.py; also base.html if CSS changes); deploy and confirm via /health + a prod opportunity page.

## Key decisions & tradeoffs

- **No new profile questions.** The user chose special-check-everything over collecting sensitive identity attributes (disability, LGBTQ+, immigration status). The previously-designed first-generation profile question is dropped; first-gen entries remain special-check permanently. Tradeoff: students who *do* qualify see these as "check eligibility" instead of Strong matches — honesty over precision, consistent with the site's privacy posture.
- **Prose-derived encoding, no re-verification.** Descriptions were verified against sponsor pages when the entries were added; re-encoding verified prose into structured form introduces no new facts. Entries with stale audits are already tracked by the existing re-verification queue.
- **Warning-level validator heuristics.** Regex category guards will have false positives/negatives; making them errors would block dataset work. Warnings keep the honest-encoding pressure without brittleness.
- **Placeholder over backfill.** The essay-prompt coverage gap is fixed honestly (say "not yet verified") rather than with a bundled mega data pass; the verified prompt-expansion pass is queued as separate follow-up work.
- **Matcher untouched.** `special_requirements` already caps match quality below Strong and emits the "Special eligibility to check" reason. Note the API contract precisely: `match_tier` remains `strong|possible` — "Special check" is a frontend grouping driven by the `requires_special_check` flag, not a third API tier value. Tests assert the flag, not a tier string. All change is data + model enum + validator + two rendering surfaces.

## Risks / open questions

- Adjudication judgment calls (requirement vs. preference) are subjective for a handful of entries; the skip list with rationale makes each call reviewable.
- The special-check group grows from ~116 to ~135 entries; it renders as a plain section (not collapsible), so the browser check includes a look at its weight, with a follow-up noted if it reads as heavy.
- Match-quality demotions (Strong → Special check) reduce some users' strong-match counts. Alerts only fire on *new* strong matches, so demotions send no email and no baseline reset is needed.

## Out of scope

- The verified essay-prompt expansion data pass (separate follow-up).
- Any new profile fields or identity questions (user decision, this grill).
- A "Statistics" (or other) field-of-study vocabulary addition.
- Near-miss system changes (special checks are permanent conditions, not fixable gaps).
- Matcher scoring changes.
