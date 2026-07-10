# Matcher Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Field-proximity partial credit, an honest "Not yet eligible" near-miss group per lane, richer per-card explanations, and cleaner activity matching.

**Architecture:** All eligibility/scoring changes live in `app/matching/` (shared helpers in `common.py`, per-kind matchers). Matcher cores keep returning lists (internal callers: `app/alerts.py`, `/match/preview`); new `*_response` wrappers add `near_misses` and the three match endpoints return `{matches, near_misses}` objects. The client stores near misses per lane and renders a collapsed `<details>` group after the tier sections, untouched by filters/batching.

**Tech Stack:** Python/FastAPI/Pydantic, pytest, vanilla JS.

**Spec:** `docs/superpowers/specs/2026-07-10-matcher-improvements-design.md` (the adjacency table, weights, and rules there are normative).

## Global Constraints

- Venv python: `.venv/Scripts/python.exe` (Git Bash on Windows). Full suite must stay green at every commit (259 tests before this plan; counts grow as tasks add tests).
- Weights (exact values): `WEIGHT_FIELD_OF_STUDY = 40.0` (unchanged), new `WEIGHT_FIELD_OF_STUDY_RELATED = 20.0`, `WEIGHT_FIELD_OF_STUDY_OPEN = 10.0` (unchanged). Program/competition equivalents: `WEIGHT_SUBJECT_RELATED = 20.0` alongside their existing 40/10.
- Near-miss rule (exact): passed every gate except exactly one; that gate is GPA with `0 < min_gpa - student.gpa <= 0.3`, OR grade level where a strictly later grade in the student's progression qualifies. Past deadlines always exclude. Preview (`skip_residency_gates=True`) returns no near misses. Cap 15 per lane, ordered real deadlines first chronologically, then estimated, then none.
- Copy voice: sentence case, no em dashes (use `;` or `·`), no hype verbs. Reason strings in this plan are exact.
- Gates never earn points; nothing in this plan may turn a failed gate into a ranked match.
- Do not touch: Quick applies, rec rollup, batching internals, catalog, SEO pages, `activateOpportunityView`.
- No `?v=` bumps inside tasks (controller bumps once at the end).
- Commits may end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: Shared helpers — adjacency map, future-grade logic, grade labels

**Files:**
- Modify: `app/matching/common.py`
- Test: `tests/test_matching_common.py` (create; if a test file for common helpers already exists, extend it instead)

**Interfaces:**
- Produces (later tasks import these from `app.matching.common`):
  - `FIELD_ADJACENCY: dict[str, set[str]]` (symmetric, spec table)
  - `related_fields(student_majors: list[str], required_fields: list[str]) -> list[str]` — required fields with no exact/child match but at least one student major adjacent; returns the required-field names
  - `GRADE_PROGRESSION: list[str]` — `["middle_school", "high_school_freshman", "high_school_sophomore", "high_school_junior", "high_school_senior", "college_freshman", "college_sophomore", "college_junior", "college_senior"]`
  - `GRADE_LABELS: dict[str, str]` — value → human label ("high_school_senior" → "a high school senior"; college grades "a college freshman" etc.; "middle_school" → "in middle school")
  - `earliest_future_qualifying_grade(student_grade: str, required_grades: list[str]) -> str | None` — earliest grade strictly after the student's current position in `GRADE_PROGRESSION` that satisfies `grade_level_matches` for the requirement; None if none or if the student grade is unknown

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for shared matching helpers (adjacency, future grades)."""

from app.matching.common import (
    FIELD_ADJACENCY,
    GRADE_PROGRESSION,
    earliest_future_qualifying_grade,
    related_fields,
)
from app.vocabulary import get_vocabulary


class TestFieldAdjacency:
    def test_map_is_symmetric(self):
        for field, neighbors in FIELD_ADJACENCY.items():
            for neighbor in neighbors:
                assert field in FIELD_ADJACENCY.get(neighbor, set()), (
                    f"{field} -> {neighbor} is not symmetric"
                )

    def test_map_uses_only_vocabulary_fields(self):
        vocab = {o["value"] for o in get_vocabulary()["fields_of_study"]}
        for field, neighbors in FIELD_ADJACENCY.items():
            assert field in vocab, field
            for neighbor in neighbors:
                assert neighbor in vocab, neighbor

    def test_related_fields_finds_adjacent(self):
        assert related_fields(["computer_science"], ["engineering"]) == ["engineering"]

    def test_related_fields_skips_exact_matches(self):
        # engineering is exact via the requirement itself, so it is not "related"
        assert related_fields(["engineering"], ["engineering"]) == []

    def test_related_fields_skips_child_matches(self):
        # computer_science satisfies "science" via FIELD_REQUIREMENT_CHILDREN;
        # that is an exact-tier match, not a related one
        assert related_fields(["computer_science"], ["science"]) == []

    def test_related_fields_empty_when_no_adjacency(self):
        assert related_fields(["music"], ["law"]) == []


class TestFutureGrade:
    def test_junior_qualifies_next_year_for_senior_award(self):
        assert (
            earliest_future_qualifying_grade("high_school_junior", ["high_school_senior"])
            == "high_school_senior"
        )

    def test_senior_has_no_future_high_school_grade(self):
        assert (
            earliest_future_qualifying_grade("high_school_senior", ["high_school_junior"])
            is None
        )

    def test_broad_requirement_uses_child_expansion(self):
        # middle schooler will qualify for a "high_school" requirement as a freshman
        assert (
            earliest_future_qualifying_grade("middle_school", ["high_school"])
            == "high_school_freshman"
        )

    def test_unknown_student_grade_returns_none(self):
        assert earliest_future_qualifying_grade("graduate", ["high_school"]) is None
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/Scripts/python.exe -m pytest tests/test_matching_common.py -q`
Expected: FAIL with ImportError (`FIELD_ADJACENCY` not defined).

- [ ] **Step 3: Implement in `app/matching/common.py`**

Append (after `GRADE_REQUIREMENT_CHILDREN`):

```python
# Related-field adjacency: partial fit credit only, never eligibility.
# Symmetric by construction; a test enforces it. Values are fields_of_study
# vocabulary entries.
FIELD_ADJACENCY: dict[str, set[str]] = {
    "computer_science": {"technology", "engineering", "mathematics", "science"},
    "technology": {"computer_science", "engineering"},
    "engineering": {"computer_science", "technology", "mathematics", "science", "architecture"},
    "mathematics": {"computer_science", "engineering", "science", "research", "business"},
    "science": {
        "natural_sciences",
        "environmental_science",
        "health_medicine",
        "research",
        "mathematics",
        "engineering",
        "computer_science",
    },
    "natural_sciences": {"science", "environmental_science", "agriculture", "research"},
    "environmental_science": {"science", "natural_sciences", "agriculture"},
    "agriculture": {"environmental_science", "natural_sciences"},
    "health_medicine": {"nursing", "science"},
    "nursing": {"health_medicine"},
    "arts": {"music", "literature", "architecture", "communications"},
    "music": {"arts"},
    "literature": {"humanities", "arts", "communications"},
    "humanities": {"literature", "philosophy", "social_sciences", "law"},
    "philosophy": {"humanities"},
    "social_sciences": {"humanities", "law", "education", "communications"},
    "law": {"social_sciences", "humanities", "business"},
    "business": {"communications", "law", "mathematics"},
    "communications": {"arts", "literature", "social_sciences", "business"},
    "education": {"social_sciences"},
    "research": {"science", "mathematics", "natural_sciences"},
    "architecture": {"engineering", "arts"},
}

GRADE_PROGRESSION: list[str] = [
    "middle_school",
    "high_school_freshman",
    "high_school_sophomore",
    "high_school_junior",
    "high_school_senior",
    "college_freshman",
    "college_sophomore",
    "college_junior",
    "college_senior",
]

GRADE_LABELS: dict[str, str] = {
    "middle_school": "in middle school",
    "high_school_freshman": "a high school freshman",
    "high_school_sophomore": "a high school sophomore",
    "high_school_junior": "a high school junior",
    "high_school_senior": "a high school senior",
    "college_freshman": "a college freshman",
    "college_sophomore": "a college sophomore",
    "college_junior": "a college junior",
    "college_senior": "a college senior",
}


def related_fields(student_majors: list[str], required_fields: list[str]) -> list[str]:
    """Required fields with no exact/child overlap but an adjacent student major.

    Exact and child matches are handled by matching_fields; this only reports
    requirements that would otherwise score zero.
    """
    if not required_fields:
        return []
    exact = set(matching_fields(student_majors, required_fields))
    norm_majors = {normalize_tag(major) for major in student_majors}
    related: list[str] = []
    for field in required_fields:
        if field in exact:
            continue
        adjacent = FIELD_ADJACENCY.get(normalize_tag(field), set())
        if norm_majors.intersection(adjacent):
            related.append(field)
    return related


def earliest_future_qualifying_grade(
    student_grade: str, required_grades: list[str]
) -> str | None:
    """Earliest grade strictly after the student's current one that qualifies."""
    norm = normalize_tag(student_grade)
    if norm not in GRADE_PROGRESSION:
        return None
    start = GRADE_PROGRESSION.index(norm) + 1
    for grade in GRADE_PROGRESSION[start:]:
        if grade_level_matches(grade, required_grades):
            return grade
    return None
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_matching_common.py -q` — PASS.
Full suite: `.venv/Scripts/python.exe -m pytest tests/ -q` — all pass.

- [ ] **Step 5: Commit**

```bash
git add app/matching/common.py tests/test_matching_common.py
git commit -m "Add field adjacency and future-grade helpers"
```

---

### Task 2: Field proximity scoring in all three matchers

**Files:**
- Modify: `app/matching/matcher.py` (field block ~lines 204-216 and weights ~line 18), `app/matching/program_matcher.py`, `app/matching/competition_matcher.py`
- Test: `tests/test_matcher.py` (or the existing matcher test files — find them with `grep -rl "match_scholarships" tests/`), plus the program/competition matcher test files

**Interfaces:**
- Consumes: `related_fields` from Task 1.
- Produces: constant names `WEIGHT_FIELD_OF_STUDY_RELATED = 20.0` (matcher.py) and `WEIGHT_SUBJECT_RELATED = 20.0` (program & competition matchers). Reason string (exact): `Related field: {required} (your {student_field} is adjacent)` where `{student_field}` is the first student major adjacent to that requirement.

- [ ] **Step 1: Failing tests** (adapt fixture style to the existing matcher tests — they build `StudentProfile` and `Scholarship` objects; copy an existing test's fixture pattern)

```python
def test_related_field_scores_partial_credit(...):
    # student: intended_majors=["computer_science"]; scholarship requires ["engineering"],
    # everything else permissive
    result = <evaluate via match_scholarships>
    assert result.score_breakdown.field_of_study == 20.0
    assert any(r.startswith("Related field: engineering") for r in result.match_reasons)

def test_related_field_does_not_set_field_mismatch_caveat(...):
    # same setup; a related match must not add the "May not match this
    # scholarship's field of study" caveat and must be allowed to be strong
    # if its total crosses the threshold

def test_exact_match_still_beats_related(...):
    # majors ["engineering"] vs required ["engineering"] -> 40.0

def test_no_overlap_still_zero(...):
    # majors ["music"] vs required ["law"] -> 0.0 field component, caveat present
```

Mirror one related-field test each for the program matcher (subject list) and competition matcher (its fields list).

- [ ] **Step 2: Verify failure** — run the touched test files; the related tests fail (component is 0).

- [ ] **Step 3: Implement.** In `matcher.py`, replace the field block's else-branch logic:

```python
    required_fields = scholarship.eligibility.fields_of_study
    matched_fields = _matching_fields(student.intended_majors, required_fields)
    related = related_fields(student.intended_majors, required_fields)
    field_mismatch = bool(required_fields) and not matched_fields and not related
    if not required_fields:
        breakdown.field_of_study = WEIGHT_FIELD_OF_STUDY_OPEN
        reasons.append("Open to all fields of study (weaker fit signal, partial score)")
    elif matched_fields:
        breakdown.field_of_study = WEIGHT_FIELD_OF_STUDY
        for field in matched_fields:
            reasons.append(f"Field of study overlap: {field}")
    elif related:
        breakdown.field_of_study = WEIGHT_FIELD_OF_STUDY_RELATED
        for field in related:
            student_field = next(
                major
                for major in student.intended_majors
                if normalize_tag(major) in FIELD_ADJACENCY.get(normalize_tag(field), set())
            )
            reasons.append(f"Related field: {field} (your {student_field} is adjacent)")
    else:
        reasons.append("No field of study overlap")
        reasons.append("May not match this scholarship's field of study, check eligibility")
```

Add the constant next to the others and import `related_fields`, `FIELD_ADJACENCY`, `normalize_tag` from common (matcher.py may already alias some — follow its import style). Apply the same three-level structure to the program matcher's subject block and the competition matcher's field block with `WEIGHT_SUBJECT_RELATED` (their "related" reason uses the same exact string with their field/subject value).

- [ ] **Step 4: Run** the three matcher test files, then full suite — all pass.

- [ ] **Step 5: Commit** — `git commit -m "Score related fields with partial credit"`

---

### Task 3: Richer explanations (fit-context + missing-component hints)

**Files:**
- Modify: `app/matching/matcher.py`, `app/matching/program_matcher.py`, `app/matching/competition_matcher.py`
- Test: same matcher test files as Task 2

**Interfaces:**
- Reason strings (exact formats):
  - Fit context (appended last to reasons): `Fit score {total:g}: ` + comma-joined nonzero components using these names — scholarships: `field of study`, `demographics`, `target school`, `activities`, `financial need`; programs/competitions: their breakdown component names in the same human style. Example: `Fit score 45: field of study 40, financial need 5`. Omit the line when the total is 0.
  - Missing hints (at most 2, ordered by descending potential points, only for components the item actually weights AND that scored exactly 0):
    - demographics (required_demographics non-empty, component 0): `No demographic overlap; this award adds up to {int(WEIGHT_DEMOGRAPHICS)} points for it`
    - field (required fields non-empty, component 0): `No field overlap; field fit adds up to {int(WEIGHT_FIELD_OF_STUDY)} points`
    - target school (eligible_schools non-empty, student listed target_schools, component 0): `No target school match; a school match adds {int(WEIGHT_TARGET_SCHOOL)} points`
    For programs/competitions apply the analogous hints for the components their breakdowns actually have (inspect their breakdown models; skip hints for components a kind does not score). Partial scores (e.g. related-field 20) generate no hint.

- [ ] **Step 1: Failing tests**

```python
def test_fit_context_line_lists_nonzero_components(...):
    # field 40 + need 5 profile/scholarship pair
    assert "Fit score 45: field of study 40, financial need 5" in result.match_reasons

def test_missing_hints_capped_at_two_and_ordered(...):
    # scholarship weighting demographics (25), field (40), school (15); student
    # matches none -> expect the field hint (40) and demographics hint (25), no school hint
    reasons = result.match_reasons
    assert "No field overlap; field fit adds up to 40 points" in reasons
    assert "No demographic overlap; this award adds up to 25 points for it" in reasons
    assert not any(r.startswith("No target school match") for r in reasons)

def test_partial_component_generates_no_hint(...):
    # related-field 20 -> no field hint

def test_zero_total_omits_fit_context(...):
```

- [ ] **Step 2: Verify failure.**

- [ ] **Step 3: Implement** a small private helper in each matcher (they have different breakdown shapes; keep it local, ~15 lines) called right before the result object is built:

```python
def _explanation_lines(breakdown, *, weighted_zero: list[tuple[str, float]]) -> list[str]:
    """weighted_zero: (hint_line, potential_points) for components the item
    weights that scored 0, any order; returns fit-context + top-2 hints."""
    lines: list[str] = []
    components = [
        ("field of study", breakdown.field_of_study),
        ("demographics", breakdown.demographics),
        ("target school", breakdown.target_school),
        ("activities", breakdown.activities),
        ("financial need", breakdown.financial_need),
    ]
    nonzero = [(name, pts) for name, pts in components if pts]
    if breakdown.total:
        joined = ", ".join(f"{name} {pts:g}" for name, pts in nonzero)
        lines.append(f"Fit score {breakdown.total:g}: {joined}")
    hints = sorted(weighted_zero, key=lambda pair: -pair[1])[:2]
    lines.extend(line for line, _pts in hints)
    return lines
```

In `_evaluate_scholarship`, before constructing `MatchResult`, build `weighted_zero`:

```python
    weighted_zero: list[tuple[str, float]] = []
    if required_fields and breakdown.field_of_study == 0:
        weighted_zero.append(
            (f"No field overlap; field fit adds up to {int(WEIGHT_FIELD_OF_STUDY)} points", WEIGHT_FIELD_OF_STUDY)
        )
    if required_demographics and breakdown.demographics == 0:
        weighted_zero.append(
            (f"No demographic overlap; this award adds up to {int(WEIGHT_DEMOGRAPHICS)} points for it", WEIGHT_DEMOGRAPHICS)
        )
    if eligible_schools and student.target_schools and breakdown.target_school == 0:
        weighted_zero.append(
            (f"No target school match; a school match adds {int(WEIGHT_TARGET_SCHOOL)} points", WEIGHT_TARGET_SCHOOL)
        )
    reasons.extend(_explanation_lines(breakdown, weighted_zero=weighted_zero))
```

Programs/competitions: same pattern with their component lists (adapt names to their breakdown fields; e.g. programs have subject/demographics/financial_access).

- [ ] **Step 4: Run + full suite** — pass. (Existing tests that assert exact reason lists may need the new trailing lines accounted for; prefer asserting membership over full-list equality when updating.)

- [ ] **Step 5: Commit** — `git commit -m "Add fit-context and missing-component explanation lines"`

---

### Task 4: Activity matching cleanup

**Files:**
- Modify: `app/matching/matcher.py` (`_activity_keywords` ~line 76, `_matching_activities` ~line 86)
- Test: the matcher test file

**Interfaces:** behavior only; signatures unchanged.

- [ ] **Step 1: Failing tests**

```python
def test_short_tokens_do_not_match_substrings(...):
    # activities ["art"] with description containing "participants" -> no activity score

def test_word_boundary_matching(...):
    # activities ["debate team"] with description "national debate championship" -> matches

def test_synonym_fold(...):
    # activities ["robotics club"] with description "build a robot" -> matches

def test_cap_still_enforced(...):
    # 5 matching activities -> breakdown.activities == 10.0
```

- [ ] **Step 2: Verify failure** (the substring test fails against current behavior).

- [ ] **Step 3: Implement:**

```python
_ACTIVITY_SYNONYMS: dict[str, set[str]] = {
    "robotics": {"robot", "robots"},
    "volunteering": {"volunteer", "volunteers"},
    "debating": {"debate", "debates"},
    "athletics": {"athletic", "athlete", "athletes"},
    "music": {"musician", "musicians"},
    "writing": {"writer", "writers"},
}


def _activity_keywords(activities: list[str]) -> set[str]:
    keywords: set[str] = set()
    for activity in activities:
        for token in re.split(r"[^a-z0-9]+", activity.lower()):
            if len(token) < 4:
                continue
            keywords.add(token)
            for canonical, variants in _ACTIVITY_SYNONYMS.items():
                if token == canonical or token in variants:
                    keywords.add(canonical)
                    keywords.update(variants)
    return keywords


def _matching_activities(activities: list[str], description: str) -> list[str]:
    keywords = _activity_keywords(activities)
    if not keywords:
        return []
    text = description.lower()
    matched = [
        keyword
        for keyword in sorted(keywords)
        if re.search(rf"\b{re.escape(keyword)}\b", text)
    ]
    return matched
```

(`import re` if not present. Check the current `_matching_activities` return semantics — if callers expect original activity phrases rather than tokens, keep returning the tokens; the reason line joins them and tokens read fine.)

- [ ] **Step 4: Run + full suite** — pass (existing activity tests may need updating if they relied on substring behavior; judge each on the spec's intent).

- [ ] **Step 5: Commit** — `git commit -m "Match activities on word boundaries with synonym folding"`

---

### Task 5: Near-miss backend (models, matcher passes, endpoints, internal callers)

**Files:**
- Modify: `app/models/match.py`, `app/models/program.py`, `app/models/competition.py`, `app/matching/matcher.py`, `app/matching/program_matcher.py`, `app/matching/competition_matcher.py`, `app/main.py` (the three match endpoints)
- Test: matcher test files + the API tests that call `/match`, `/programs/match`, `/competitions/match` (grep `client.post("/match"` etc. — MANY existing tests parse a list response; they change to `payload["matches"]`)

**Interfaces:**
- Produces, in `app/models/match.py`:

```python
class ScholarshipNearMiss(BaseModel):
    scholarship_id: str
    scholarship_name: str
    sponsor: str
    award_amount: Union[float, str]
    deadline: str
    estimated_deadline: str | None = None
    url: str
    verified: bool
    near_miss_reason: str


class MatchResponse(BaseModel):
    matches: list[MatchResult]
    near_misses: list[ScholarshipNearMiss]
```

  Analogous `ProgramNearMiss`/`ProgramMatchResponse` (host + cost instead of sponsor + award_amount) and `CompetitionNearMiss`/`CompetitionMatchResponse` (host + recognition), each mirroring the field names their MatchResult uses.
- Produces, per matcher (exact names; cores stay list-returning for `app/alerts.py` and preview):
  - `match_scholarships(...) -> list[MatchResult]` (unchanged signature/behavior)
  - `match_scholarships_response(student, scholarships, *, today=None) -> MatchResponse` — matches from the core plus near misses; never called with skip_residency_gates
  - `near_miss_scholarships(student, scholarships, today) -> list[ScholarshipNearMiss]`
  - Same trio pattern for programs and competitions.
- Endpoints: `POST /match` returns `MatchResponse` (`match_scholarships_response(...)`); preview endpoint UNCHANGED (still calls the list core with skip_residency_gates=True); `/programs/match`, `/competitions/match` return their response models. `app/alerts.py` untouched (it imports the list cores — verify with grep and state the result in the report).

- [ ] **Step 1: Failing tests** (matcher-level first)

```python
def test_gpa_near_miss_within_window(...):
    # min_gpa 3.8, student 3.6, everything else passing ->
    nm = near_miss_scholarships(student, [scholarship], today)
    assert len(nm) == 1
    assert nm[0].near_miss_reason == "Needs GPA 3.8; your profile says 3.6"

def test_gpa_gap_above_window_excluded(...):
    # min_gpa 3.8, student 3.49 -> []

def test_future_grade_near_miss(...):
    # requires high_school_senior, student high_school_junior ->
    assert nm[0].near_miss_reason == "Eligible when you are a high school senior"

def test_two_failed_gates_excluded(...):
    # GPA gap 0.2 AND wrong-state -> []

def test_past_deadline_excluded_even_with_gap(...):

def test_near_miss_absent_from_matches(...):
    # the same scholarship must not appear in match_scholarships output

def test_response_wrapper_shape(...):
    resp = match_scholarships_response(student, scholarships)
    assert resp.matches and isinstance(resp.near_misses, list)

def test_cap_and_ordering(...):
    # 17 GPA-gap items with mixed deadlines -> 15 returned, real deadlines
    # chronological first, then estimated, then none
```

API-level: update every existing test that reads the match response as a list to `response.json()["matches"]`, and add one asserting `near_misses` is present (list) on all three endpoints, plus one asserting `/match/preview`'s shape is unchanged.

- [ ] **Step 2: Verify failure.**

- [ ] **Step 3: Implement.** Near-miss evaluation must NOT duplicate gate semantics: restructure each matcher's gate section into a small internal pass that records failures instead of returning early. Concretely for `matcher.py`, add:

```python
def _near_miss_reason_for(
    student: StudentProfile, scholarship: Scholarship, today: date
) -> str | None:
    """Reason string when the item fails EXACTLY one gate and that gate is a
    qualifying near-miss type; otherwise None."""
    failures: list[str] = []
    qualifying_reason: str | None = None

    min_gpa = scholarship.eligibility.min_gpa
    if isinstance(min_gpa, (int, float)) and student.gpa < float(min_gpa):
        gap = float(min_gpa) - student.gpa
        failures.append("gpa")
        if 0 < gap <= 0.3:
            qualifying_reason = f"Needs GPA {min_gpa:g}; your profile says {student.gpa:g}"

    grade_levels = scholarship.eligibility.grade_levels
    if grade_levels and not _grade_level_matches(student.grade_level, grade_levels):
        failures.append("grade")
        future = earliest_future_qualifying_grade(student.grade_level, grade_levels)
        if future is not None:
            qualifying_reason = f"Eligible when you are {GRADE_LABELS[future]}"

    parsed_deadline = _parse_iso_deadline(scholarship.deadline)
    if parsed_deadline is not None and parsed_deadline < today:
        failures.append("deadline")

    if _citizenship_satisfies(
        student.citizenship, scholarship.eligibility.citizenship_requirement
    ) is False:
        failures.append("citizenship")

    if not _state_matches(student.state, scholarship.eligibility.states):
        failures.append("state")

    if len(failures) != 1 or qualifying_reason is None:
        return None
    return qualifying_reason
```

Note the subtlety the tests pin: `qualifying_reason` is only meaningful when the single failure IS the qualifying gate — with exactly one failure recorded, a non-None `qualifying_reason` implies that. Grade label sentence uses `GRADE_LABELS` ("Eligible when you are a high school senior").

Then:

```python
def near_miss_scholarships(
    student: StudentProfile, scholarships: list[Scholarship], today: date
) -> list[ScholarshipNearMiss]:
    entries: list[ScholarshipNearMiss] = []
    for scholarship in scholarships:
        reason = _near_miss_reason_for(student, scholarship, today)
        if reason is None:
            continue
        entries.append(
            ScholarshipNearMiss(
                scholarship_id=scholarship.id,
                scholarship_name=scholarship.name,
                sponsor=scholarship.sponsor,
                award_amount=scholarship.award_amount,
                deadline=scholarship.deadline,
                estimated_deadline=scholarship.estimated_deadline,
                url=str(scholarship.url),
                verified=scholarship.verified,
                near_miss_reason=reason,
            )
        )
    entries.sort(key=_near_miss_sort_key)
    return entries[:15]


def _near_miss_sort_key(entry) -> tuple:
    real = _parse_iso_deadline(entry.deadline)
    if real is not None:
        return (0, real.toordinal(), entry.scholarship_name.lower())
    est = _parse_iso_deadline(entry.estimated_deadline or "")
    if est is not None:
        return (1, est.toordinal(), entry.scholarship_name.lower())
    return (2, 0, entry.scholarship_name.lower())


def match_scholarships_response(
    student: StudentProfile,
    scholarships: list[Scholarship],
    *,
    today: date | None = None,
) -> MatchResponse:
    reference_date = today or date.today()
    return MatchResponse(
        matches=match_scholarships(student, scholarships, today=reference_date),
        near_misses=near_miss_scholarships(student, scholarships, reference_date),
    )
```

Program/competition matchers get the same trio (their gates: grade, GPA, deadline, citizenship where present — check each matcher's actual gate list and record EVERY gate it applies in its `_near_miss_reason_for`; sort key fields adapt to their name field). Endpoints in `app/main.py` switch to the `*_response` functions with `response_model` updated; preview endpoint untouched. Grep `alerts.py` for the core function names to confirm untouched behavior.

- [ ] **Step 4: Run matcher + API tests, then full suite** — all pass.

- [ ] **Step 5: Commit** — `git commit -m "Return near misses alongside matches"`

---

### Task 6: Frontend — new response shape + "Not yet eligible" groups

**Files:**
- Modify: `app/static/js/app.js` (match submit handlers reading the three endpoints; the three lane render functions), `app/static/css/style.css`, `tests/test_pages.py` (markup assertion if the group is static; it is JS-rendered, so instead assert nothing server-side — SKIP page test and note it), `app/static/index.html` only if a static container is needed (it is not; render into the existing lane containers)
- Test: `node --check` + browser verification (no JS test framework)

**Interfaces:**
- Consumes: `{matches, near_misses}` JSON from the three endpoints; near-miss fields per kind as defined in Task 5.
- Produces: `lastNearMisses = { scholarships: [], programs: [], competitions: [] }` module state; `buildNearMissGroup(kind, entries)` returning a `<details class="near-miss-group">` element.

- [ ] **Step 1: Update the fetch handlers.** Find where the three match responses are consumed (grep `fetch("/match"`, `"/programs/match"`, `"/competitions/match"`). Each currently does `lastResults = await response.json()`-style assignment (possibly via helper). Change to:

```javascript
const payload = await response.json();
lastResults = payload.matches;          // and lastPrograms / lastCompetitions
lastNearMisses.scholarships = payload.near_misses || [];   // per kind
```

Declare `const lastNearMisses = { scholarships: [], programs: [], competitions: [] };` near the other match state. Reset all three to `[]` in the same `setLoading(true)` block that resets lane windows.

- [ ] **Step 2: Build and render the group.** Add:

```javascript
const NEAR_MISS_KIND_META = {
  scholarships: { path: "scholarships", idField: "scholarship_id", nameField: "scholarship_name" },
  programs: { path: "programs", idField: "program_id", nameField: "program_name" },
  competitions: { path: "competitions", idField: "competition_id", nameField: "competition_name" },
};
// Verify the program/competition near-miss field names against the Task 5
// models and correct this map to match them exactly.

function buildNearMissGroup(kind, entries) {
  const meta = NEAR_MISS_KIND_META[kind];
  const details = document.createElement("details");
  details.className = "near-miss-group";
  const summary = document.createElement("summary");
  summary.textContent = `Not yet eligible (${entries.length})`;
  details.appendChild(summary);
  const list = document.createElement("div");
  list.className = "near-miss-list";
  for (const entry of entries) {
    const row = document.createElement("div");
    row.className = "browse-row near-miss-row";
    const left = document.createElement("div");
    left.className = "quick-apply-left";
    const nameLine = document.createElement("p");
    nameLine.className = "quick-apply-name";
    const link = document.createElement("a");
    link.className = "card-title-link";
    link.href = `/${meta.path}/${encodeURIComponent(entry[meta.idField])}`;
    link.textContent = entry[meta.nameField];
    nameLine.appendChild(link);
    left.appendChild(nameLine);
    const dl = deadlineParts(entry.deadline, entry.estimated_deadline);
    const metaLine = document.createElement("p");
    metaLine.className = "browse-row-meta";
    metaLine.textContent = `${entry.near_miss_reason} · ${dl.value}${dl.note ? ` (${dl.note})` : ""}`;
    left.appendChild(metaLine);
    row.appendChild(left);
    list.appendChild(row);
  }
  details.appendChild(list);
  return details;
}
```

In each lane render function (`renderResults`, `renderPrograms`, `renderCompetitions`), AFTER the tier sections and the lane Show-more button, append `buildNearMissGroup(kind, lastNearMisses[kind])` when that array is non-empty. The group is outside the filter/batching logic by construction (it renders from `lastNearMisses`, not the filtered list) — every re-render includes it unchanged.

- [ ] **Step 3: CSS** (append to end of style.css):

```css
/* "Not yet eligible" near-miss group: informational, never a ranked match. */
.near-miss-group { margin-top: 1rem; padding: 0.9rem 1.1rem; border: 1px dashed var(--line-strong); border-radius: var(--radius); background: var(--surface-inset); }
.near-miss-group summary { cursor: pointer; color: var(--ink-soft); font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; }
.near-miss-group summary:hover { color: var(--ink); }
.near-miss-list { display: flex; flex-direction: column; gap: 0.1rem; margin-top: 0.55rem; }
```

- [ ] **Step 4: Verify.** `node --check app/static/js/app.js`; full pytest suite; browser check (fresh server on port 8499, kill after): run a match with a profile engineered for near misses (e.g. GPA 3.5 with fields selected — several 3.7/3.75-minimum awards exist), confirm the collapsed group renders after tier sections in the scholarships lane, expands with reason lines, survives filter changes and Show more untouched, and appears in programs/competitions lanes when applicable (a middle-school or freshman grade profile produces future-grade near misses).

- [ ] **Step 5: Commit** — `git commit -m "Render Not yet eligible near-miss groups in match lanes"`

---

### Task 7 (controller): bump `?v=`, full E2E verification, final whole-branch review, deploy on user confirmation.
