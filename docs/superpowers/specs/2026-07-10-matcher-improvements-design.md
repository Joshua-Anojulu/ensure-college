# Matcher Improvements — Design

Date: 2026-07-10. User-approved design (all four improvements, approach A).

## Goal

Smooth the matcher's all-or-nothing cliffs and make results more explanatory,
without ever blurring eligibility: gates stay gates; everything new is either
partial *fit* credit (never eligibility) or honestly-labeled future eligibility.

## 1. Field proximity scoring

- New curated symmetric adjacency map `FIELD_ADJACENCY: dict[str, set[str]]` in
  `app/matching/common.py`, over the existing 22-value fields_of_study
  vocabulary:

  | field | adjacent to |
  |---|---|
  | computer_science | technology, engineering, mathematics, science |
  | technology | computer_science, engineering |
  | engineering | computer_science, technology, mathematics, science, architecture |
  | mathematics | computer_science, engineering, science, research, business |
  | science | natural_sciences, environmental_science, health_medicine, research, mathematics, engineering, computer_science |
  | natural_sciences | science, environmental_science, agriculture, research |
  | environmental_science | science, natural_sciences, agriculture |
  | agriculture | environmental_science, natural_sciences |
  | health_medicine | nursing, science |
  | nursing | health_medicine |
  | arts | music, literature, architecture, communications |
  | music | arts |
  | literature | humanities, arts, communications |
  | humanities | literature, philosophy, social_sciences, law |
  | philosophy | humanities |
  | social_sciences | humanities, law, education, communications |
  | law | social_sciences, humanities, business |
  | business | communications, law, mathematics |
  | communications | arts, literature, social_sciences, business |
  | education | social_sciences |
  | research | science, mathematics, natural_sciences |
  | architecture | engineering, arts |

  A unit test asserts the map is symmetric and every key/value is in the
  vocabulary.

- Scoring in all three matchers becomes three-level:
  - exact overlap (including the existing FIELD_REQUIREMENT_CHILDREN parent
    logic): `WEIGHT_FIELD_OF_STUDY` (40), unchanged
  - no exact overlap but at least one student field adjacent to a required
    field: new `WEIGHT_FIELD_OF_STUDY_RELATED = 20.0`
  - open to all fields: `WEIGHT_FIELD_OF_STUDY_OPEN` (10), unchanged
  - no overlap at all: 0, unchanged
- Reason line for the related case: `Related field: {required} (your
  {student_field} is adjacent)`. The existing field-mismatch caveat lines stay
  for the zero case. Related matches do NOT set the `field_mismatch` caveat.
- Score-breakdown chip: the existing field_of_study component simply carries
  20; no new chip type.

## 2. Near-miss surface ("Not yet eligible")

- Each matcher's public function returns `MatchResponse`-style object:
  `{"matches": [...], "near_misses": [...]}` (Pydantic models: `MatchResponse`,
  `ProgramMatchResponse`, `CompetitionMatchResponse`). The `/match`,
  `/programs/match`, `/competitions/match` endpoints return these objects.
  Client and all tests update in the same change. `/match/preview` keeps its
  existing shape and never includes near misses.
- Internal callers must keep working: `app/alerts.py` (new-match alerts) and
  the preview endpoint consume match lists — they use the `.matches` part
  only (or the matchers keep a list-returning core function that the new
  response-building wrapper and internal callers share). Near misses never
  trigger alert emails.
- Qualification rule (strict): the item passed EVERY gate except exactly one,
  and that one failed gate is one of:
  - **GPA**: numeric min_gpa, student below it by ≤ 0.3 (i.e.
    `0 < min_gpa - student.gpa <= 0.3`)
  - **Grade level**: student's current grade fails, but some LATER grade level
    in the student's natural progression qualifies (use the existing grade
    ordering; "later" = any grade after the student's current one). Reason
    names the earliest qualifying future grade.
  Items failing two or more gates, failing deadline (passed), or failing any
  other gate type are excluded entirely, as today.
- Near-miss entry shape (per kind): id, name, sponsor/host, award/cost text
  fields as in the kind's match result, deadline + estimated_deadline,
  verified, url, and `near_miss_reason` (one human string, e.g.
  `Needs GPA 3.8; your profile says 3.6` or
  `Eligible when you are a high school senior`). No score, no tier.
- Cap: 15 per lane, ordered by deadline (real first, chronological).
- UI: in each lane, after the tier sections, a `<details class="near-miss-group">`
  with `<summary>Not yet eligible ({N})</summary>`, collapsed by default,
  rendered only when N > 0. Rows: linked name (detail page), reason line,
  deadline with existing labeling. Styled informational (no fit ring, no save
  button, no hover theater). Lane filters do NOT apply to this group; lane
  batching does not either (already capped at 15).

## 3. Richer explanations

On every match card (all three kinds), in the reasons area:
- A fit-context line appended to the reasons list, built from the existing
  score breakdown: `Fit score {total}: {component} {points}` for each nonzero
  component, e.g. `Fit score 45: field of study 40, financial need 5`.
- Up to TWO "what's missing" hint lines for the largest zero components the
  award actually weights, phrased as facts, not advice:
  - demographics weighted but no overlap: `No demographic overlap; this award
    adds up to {WEIGHT_DEMOGRAPHICS} points for it`
  - field weighted but no overlap/adjacency: `No field overlap; field fit adds
    up to {WEIGHT_FIELD_OF_STUDY} points`
  - school weighted but none matched: analogous with 15.
  Components that scored partially (e.g. related-field 20) do not generate a
  hint. Backend computes these lines (they live with the weights); frontend
  renders them as ordinary reasons.

## 4. Activity matching cleanup

In `_activity_keywords` / `_matching_activities` (and program/competition
equivalents if they share it via common.py):
- Tokenize on word boundaries; match tokens against the description with
  `\b`-anchored regex, case-insensitive; minimum token length 4.
- Small synonym fold applied to tokens (both directions):
  robotics/robot, volunteering/volunteer/volunteers, debating/debate,
  athletics/athletic/athlete, music/musician, writing/writer.
- Existing per-match weight (5) and cap (10) unchanged.
- Unit tests: "art" must not match "particular"; "robot" matches a
  "robotics" description; cap still enforced.

## Out of scope

Tier thresholds, demographic/need weights, preview behavior, saved/plan flows,
and any UI beyond the near-miss group and the new reason lines.

## Testing

- Matcher units: three-level field scoring; adjacency-map symmetry/vocabulary
  validity; exactly-one-gate rule (both-failed excluded; GPA gap 0.31 excluded;
  gap 0.3 included; future-grade included; past-deadline excluded even with a
  qualifying gap); near-miss caps and ordering; explanation lines present with
  correct arithmetic; activity tokenization cases.
- API: new response shapes for the three match endpoints; preview shape
  unchanged.
- Frontend: page test asserts the near-miss `<details>` markup exists; browser
  verification of collapsed group, reasons, and no filter/batching interaction.
- Full suite green; version bump at the end as usual.
