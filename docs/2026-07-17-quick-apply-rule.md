# Plan: settle the Quick apply rule (rev 3)
_Locked via grill-with-docs — by Claude + Josh, 2026-07-17. Terms per CONTEXT.md. Rev 3 after Codex rounds 1-2 (REVISE)._

## Goal

**Quick apply** now has a definition in CONTEXT.md: a match nothing stands
between the student and applying to — no essay, few requirement steps, and no
**special check** — drawn from the current match set. The code does not honour
the last clause: `quickApplyCandidate` never consults `requires_special_check`,
so opportunities that already carry a special-check row leak into the panel —
POSSE (nomination), SHPE and NSBE (membership), IEEE (finalist), and many more
across all three lanes (a catalog-level scan finds on the order of 20
panel-eligible-and-special items — scholarships via the sidecar, programs and
competitions via inline `eligibility.special_requirements`; the exact figure is
profile-dependent, so the test below, not a number here, is the source of
truth). This plan makes the panel obey the definition with a single guard. No
dataset change is required: the leaks already have their rows.

## Approach

1. **Guard the panel.** In `app/static/js/app.js`, `quickApplyCandidate`
   returns `null` when `item.requires_special_check` is truthy — the first
   check in the function, before essay/step logic. This mirrors the three lane
   filters (`app.js:953`, `1031`, `1084`), which already honour the flag. All
   three match kinds carry it: scholarships at `matcher.py:402`, programs at
   `program_matcher.py:211`, competitions at `competition_matcher.py:212`, and
   it is already serialized into every match payload. No model or API change.

2. **Fix the count copy so it stops over-claiming.** `app.js:2178` reads
   "N matches need no essay and 3 or fewer requirements." Items with empty
   `application_requirements` still qualify — they carry `candidate.unverified`
   (set at `app.js:2119`) and render the per-row label "requirements not yet
   verified" — so that blanket count is false for them. Split the count by that
   exact flag, not by the word "verified" (which in this codebase means the
   separate source-audited `verified` field):
   `knownRequirementCount = candidates.filter(c => !c.unverified).length` and
   `unknownRequirementCount = candidates.filter(c => c.unverified).length`.
   Copy: "K need no essay and 3 or fewer requirements" when K>0, plus
   "U more have requirements we haven't verified yet" when U>0 — including the
   K==0/U>0 case, where the first clause is omitted rather than showing "0".
   The unverified fallback in `quickApplyCandidate` itself STAYS — gating on
   empty requirements would contradict CLAUDE.md's "never gate on a VERIFY
   placeholder." (Live-moot today: the 2026-07-17 data pass drove the
   unverified-and-essay-free set to 0, but the copy must not lie if it returns.)

3. **Bump the asset cache-bust in lockstep.** Per CLAUDE.md's non-negotiable,
   an `app.js` change requires the `?v=` string bumped together in
   `app/static/index.html`, `journey.html`, `privacy.html`, `terms.html`,
   `app/templates/base.html`, and `tests/test_pages.py`.

4. **Update the glossary.** Done inline during the grill: the CONTEXT.md
   **Quick apply** entry now says "a match … drawn from the current match set,
   not the saved set," correcting an earlier draft that called it a saved
   opportunity — the code walks `lastResults`/`lastPrograms`/`lastCompetitions`,
   not the saved sets.

5. **Prove it.** Add e2e coverage that a special-check opportunity never
   renders in the Quick applies panel, for ALL THREE kinds (scholarship,
   program, competition) — special-check programs and competitions exist in
   live data (e.g. American Legion Boys State and ALA Girls State in
   `summer_programs.json`; JSHS and Zero Robotics in `competitions.json`, which
   carry inline `eligibility.special_requirements`), and only a per-kind test
   catches a guard that misreads a payload shape. The e2e will drive the guard
   through a **constructed fixture** per kind rather than depending on live
   catalog data, so the test stays stable as the dataset changes. Add a case
   asserting the count copy shows the "requirements we haven't verified yet"
   clause (not "3 or fewer requirements") for an unverified row. Run both suites
   and the validator; confirm the DOM contract test still passes (this change
   adds/renames no elements, so `tests/dom_contract.json` should not move —
   confirmed by the run, not assumed).

## Key decisions & tradeoffs

- **Actionability, not ease** (CONTEXT.md). Rejected an effort/stakes field
  marking fees/portfolios/auditions: it would encode *our* judgment as data,
  against CLAUDE.md's sourced-fact rule, and touch the model, validator, and
  40+ checklists. BMI Composer Awards stays a quick apply — composing a work is
  effort, but nothing blocks you.
- **The guard needs no new dataset rows.** Rev 1 bundled four special-check
  rows (Nurse Corps, NHSC, SMART, TBP). Codex round 1 correctly flagged that
  (a) only Nurse Corps even reaches the panel — NHSC/SMART are essay-required,
  TBP has 4 steps — and (b) forcing federal-service / clearance / debt gates
  under `activity_or_lifestyle` is a questionable use of the **Special check**
  taxonomy. Since the guard already fixes the existing real leaks without them,
  all four rows are removed from this plan and deferred to the audit (Out of scope),
  where the taxonomy question can be settled honestly. This defers — does not
  reverse — Josh's earlier choice to add them.
- **Step count stays at 3.** The panel copy stays literal ("No essay, few
  steps"); only the count line's over-claim is fixed.

## Risks / open questions

- The count-copy split (step 2) is the only change touching visible text besides
  the guard. Keep it minimal so `tests/dom_contract.json` (which pins the
  panel's element ids, not their text) does not move; verify in the run.
- Programs and competitions reach `requires_special_check` through inline
  `eligibility.special_requirements`, scholarships through the merged sidecar —
  two code paths, one flag. The per-kind fixtures in step 5 exercise the guard
  against both so a payload-shape mismatch cannot pass silently.

## Out of scope (follow-up)

- **Special-check rows for the federal-service awards** (Nurse Corps, NHSC,
  SMART) and Tau Beta Pi. Their pre-application eligibility gates (no existing
  service obligation, clearance-eligible, no federal judgment liens/overdue
  federal debt; TBP: initiated-member-or-candidate-by-June-1) are genuine
  special checks, but the `SpecialRequirement.kind` enum (11 closed values in
  `app/models/scholarship.py`) has no honest fit for "federal-service /
  security-clearance / financial-standing" gates. Deciding whether to reuse
  `identity_or_status`, reuse `activity_or_lifestyle` (Hagan precedent), or add
  a new `kind` (a model change needing its own review) belongs to the audit,
  not this panel fix. The sidecar `special_requirements.json` is merged **only**
  by `load_scholarships()` (`loader.py:29`); a program/competition special row
  would need its own path.
- The 12 membership-shaped candidates with no special row (`nabj`, `ans`,
  `chick-fil-a`, `afcea`, `national-beta-club`, `nshss`, `naba`,
  `sons-of-norway`, `women-in-aviation`, `american-physical-society`,
  `courageous-persuaders`); "member" is ambiguous (Chick-fil-A's is likely
  *Team Member* employment). Each needs sponsor verification.
- **Two SMART data bugs found while verifying, to fix separately:** `sponsor`
  says "U.S. Department of Defense" / description "with the DoD", but the
  sponsor's page and our own `verification.notes` say **Department of War
  (DoW)**; and `citizenship_requirement` is `us_citizen` while SMART's page
  says "a citizen of the United States, Australia, Canada, New Zealand, or
  United Kingdom" — too narrow, and gates apply on real values.
- A systematic gate audit of all 223 scholarships.
