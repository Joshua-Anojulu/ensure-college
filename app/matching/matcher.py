"""Transparent scholarship matching with explicit handling of VERIFY placeholders."""

from __future__ import annotations

import re
from datetime import date

from app.matching.common import FIELD_ADJACENCY, GRADE_LABELS
from app.matching.common import citizenship_satisfies as _citizenship_satisfies
from app.matching.common import earliest_future_qualifying_grade as _earliest_future_qualifying_grade
from app.matching.common import grade_level_matches as _grade_level_matches
from app.matching.common import matching_demographics as _matching_demographics
from app.matching.common import matching_fields as _matching_fields
from app.matching.common import normalize_tag as _normalize_tag
from app.matching.common import parse_iso_deadline as _parse_iso_deadline
from app.matching.common import related_fields as _related_fields
from app.models.match import MatchResponse, MatchResult, ScholarshipNearMiss, ScoreBreakdown
from app.models.scholarship import EligibleSchool, Scholarship
from app.models.student import StudentProfile

WEIGHT_FIELD_OF_STUDY = 40.0
WEIGHT_FIELD_OF_STUDY_OPEN = 10.0
WEIGHT_FIELD_OF_STUDY_RELATED = 20.0
WEIGHT_DEMOGRAPHICS = 25.0
WEIGHT_TARGET_SCHOOL = 15.0
WEIGHT_ACTIVITY_MATCH = 5.0
WEIGHT_ACTIVITIES_CAP = 10.0
WEIGHT_FINANCIAL_NEED_HIGH = 10.0
WEIGHT_FINANCIAL_NEED_MEDIUM = 5.0
STRONG_MATCH_THRESHOLD = 35.0
CLOSING_SOON_DAYS = 30

# Activity keywords are matched against the scholarship description as a small,
# capped bonus. Structural words carry no signal, so we drop them before matching.
_ACTIVITY_STOPWORDS = frozenset(
    {
        "the", "and", "for", "with", "club", "team", "society", "group", "member",
        "captain", "president", "vice", "varsity", "school", "high", "college",
        "university", "junior", "senior", "national", "honor", "student", "students",
    }
)

# Substrings that mark a scholarship as need-based in its description. Matched on
# the raw lowercased text so multi-word phrases like "financial need" are caught.
_NEED_KEYWORDS = (
    "financial need",
    "need-based",
    "need based",
    "low-income",
    "low income",
    "underserved",
    "economically disadvantaged",
    "economic hardship",
    "demonstrated need",
    "pell",
)

def _normalize_school(value: str) -> str:
    """Normalize a school name or declared alias for exact comparison."""
    return "".join(char for char in value.lower() if char.isalnum())


def _matching_schools(
    target_schools: list[str] | None,
    eligible_schools: list[EligibleSchool],
) -> list[str]:
    """Return canonical school names that match a student's declared targets."""
    if not target_schools or not eligible_schools:
        return []
    targets = {_normalize_school(school) for school in target_schools if school.strip()}
    matches: list[str] = []
    for school in eligible_schools:
        names = (school.name, *school.aliases)
        if any(_normalize_school(name) in targets for name in names):
            matches.append(school.name)
    return matches


_ACTIVITY_SYNONYMS: dict[str, set[str]] = {
    "robotics": {"robot", "robots"},
    "volunteering": {"volunteer", "volunteers"},
    "debating": {"debate", "debates"},
    "athletics": {"athletic", "athlete", "athletes"},
    "music": {"musician", "musicians"},
    "writing": {"writer", "writers"},
}


def _activity_keywords(activities: list[str]) -> set[str]:
    """Pull meaningful, deduplicated keywords out of free-text activity strings.

    Tokens must be at least 4 characters long and not in the stopwords list.
    Synonym folding expands keywords to include canonical forms and their variants.
    """
    keywords: set[str] = set()
    for activity in activities:
        for token in re.split(r"[^a-z0-9]+", activity.lower()):
            if len(token) < 4 or not token.isalpha() or token in _ACTIVITY_STOPWORDS:
                continue
            keywords.add(token)
            # Synonym folding: if token matches a variant, add canonical + all variants
            for canonical, variants in _ACTIVITY_SYNONYMS.items():
                if token == canonical or token in variants:
                    keywords.add(canonical)
                    keywords.update(variants)
    return keywords


def _canonical_activity(token: str) -> str:
    """Map a token to its synonym-group canonical form (or itself if ungrouped)."""
    for canonical, variants in _ACTIVITY_SYNONYMS.items():
        if token == canonical or token in variants:
            return canonical
    return token


def _matching_activities(activities: list[str], description: str) -> list[str]:
    """Return activity keywords that also appear as whole words in the description.

    Matches are deduplicated per synonym group so a description mentioning both
    "robotics" and "robot" counts as one conceptual activity, not two.
    """
    if not activities:
        return []
    keywords = _activity_keywords(activities)
    if not keywords:
        return []
    text = description.lower()
    matched_canonicals: set[str] = {
        _canonical_activity(keyword)
        for keyword in keywords
        if re.search(rf"\b{re.escape(keyword)}\b", text)
    }
    return sorted(matched_canonicals)


def _is_need_based(description: str) -> bool:
    text = description.lower()
    return any(keyword in text for keyword in _NEED_KEYWORDS)


def _state_matches(student_state: str, states: list[str] | str) -> bool:
    if states == "any" or states == "VERIFY":
        return True
    norm_state = _normalize_tag(student_state)
    return norm_state in {_normalize_tag(state) for state in states}


def _closing_soon(deadline_date: date, today: date) -> bool:
    days_until = (deadline_date - today).days
    return 0 <= days_until <= CLOSING_SOON_DAYS


def _has_upcoming_deadline(deadline: str, today: date) -> bool:
    parsed = _parse_iso_deadline(deadline)
    return parsed is not None and parsed >= today


def _match_tier(score: float) -> str:
    if score >= STRONG_MATCH_THRESHOLD:
        return "strong"
    return "possible"


def _sort_key(result: MatchResult, today: date) -> tuple:
    deadline_priority = 0 if _has_upcoming_deadline(result.deadline, today) else 1
    return (-result.score, deadline_priority, result.scholarship_name.lower())


def _explanation_lines(breakdown: ScoreBreakdown, *, weighted_zero: list[tuple[str, float]]) -> list[str]:
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


def _evaluate_scholarship(
    student: StudentProfile,
    scholarship: Scholarship,
    today: date,
    *,
    skip_residency_gates: bool = False,
) -> MatchResult | None:
    reasons: list[str] = []
    breakdown = ScoreBreakdown()
    closing_soon = False

    # GPA, grade level, and state are gate-only criteria: they can exclude a
    # scholarship but never add ranking points. Fit scoring uses field overlap,
    # demographic overlap, activity keyword overlap, and a need-based signal.
    min_gpa = scholarship.eligibility.min_gpa
    if isinstance(min_gpa, (int, float)):
        if student.gpa < float(min_gpa):
            return None
        reasons.append(f"Meets GPA requirement (minimum {min_gpa})")
    else:
        reasons.append("GPA requirement not yet verified")

    grade_levels = scholarship.eligibility.grade_levels
    if grade_levels:
        if not _grade_level_matches(student.grade_level, grade_levels):
            return None
        reasons.append(f"Grade level matches ({student.grade_level})")
    else:
        reasons.append("No specific grade level requirement")

    parsed_deadline = _parse_iso_deadline(scholarship.deadline)
    if parsed_deadline is not None:
        if parsed_deadline < today:
            return None
        closing_soon = _closing_soon(parsed_deadline, today)
        reasons.append(f"Deadline is upcoming ({scholarship.deadline})")
        if closing_soon:
            reasons.append("Closing soon (within 30 days)")
    elif scholarship.deadline == "rolling":
        reasons.append("Rolling deadline (no fixed cutoff)")
    else:
        reasons.append("Deadline not yet verified")

    if skip_residency_gates:
        # Preview mode: the student hasn't been asked citizenship or state yet,
        # so those gates cannot be applied honestly. Flag them instead.
        if scholarship.eligibility.citizenship_requirement not in ("any", "VERIFY"):
            reasons.append("Citizenship requirement to confirm with your full profile")
        if isinstance(scholarship.eligibility.states, list):
            reasons.append("State eligibility to confirm with your full profile")
    else:
        citizenship_result = _citizenship_satisfies(
            student.citizenship,
            scholarship.eligibility.citizenship_requirement,
        )
        if citizenship_result is False:
            return None
        if citizenship_result is True:
            if scholarship.eligibility.citizenship_requirement == "any":
                reasons.append("No citizenship restriction verified")
            else:
                reasons.append("Meets citizenship requirement")
        else:
            reasons.append("Citizenship requirement not yet verified")

        states = scholarship.eligibility.states
        if not _state_matches(student.state, states):
            return None
        if states == "any":
            reasons.append("Eligible in all states")
        elif states == "VERIFY":
            reasons.append("State eligibility not yet verified (treated as all states)")
        else:
            reasons.append(f"State matches ({student.state})")

    required_fields = scholarship.eligibility.fields_of_study
    matched_fields = _matching_fields(student.intended_majors, required_fields)
    related = _related_fields(student.intended_majors, required_fields)
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
                if _normalize_tag(major) in FIELD_ADJACENCY.get(_normalize_tag(field), set())
            )
            reasons.append(f"Related field: {field} (your {student_field} is adjacent)")
    else:
        reasons.append("No field of study overlap")
        reasons.append("May not match this scholarship's field of study, check eligibility")

    eligible_schools = scholarship.eligibility.eligible_schools
    matched_schools = _matching_schools(student.target_schools, eligible_schools)
    school_mismatch = (
        bool(student.target_schools) and bool(eligible_schools) and not matched_schools
    )
    if matched_schools:
        breakdown.target_school = WEIGHT_TARGET_SCHOOL
        reasons.append("Target school match: " + ", ".join(matched_schools))
    elif school_mismatch:
        reasons.append("May only be available at another school, check eligibility")

    required_demographics = scholarship.eligibility.demographics
    matched_demographics = _matching_demographics(
        student.demographic_tags,
        required_demographics,
    )
    if not required_demographics:
        reasons.append("No specific demographic requirements")
    elif matched_demographics:
        fraction = len(matched_demographics) / len(required_demographics)
        breakdown.demographics = round(WEIGHT_DEMOGRAPHICS * fraction, 2)
        for tag in matched_demographics:
            reasons.append(f"Demographic match: {tag}")
    else:
        reasons.append("No demographic tag overlap")

    matched_activities = _matching_activities(student.activities, scholarship.description)
    if matched_activities:
        breakdown.activities = min(
            WEIGHT_ACTIVITY_MATCH * len(matched_activities),
            WEIGHT_ACTIVITIES_CAP,
        )
        reasons.append(
            "Activities align with this scholarship: " + ", ".join(matched_activities)
        )

    if _is_need_based(scholarship.description):
        if student.financial_need_level == "high":
            breakdown.financial_need = WEIGHT_FINANCIAL_NEED_HIGH
            reasons.append("Need-based award matches your high financial need")
        elif student.financial_need_level == "medium":
            breakdown.financial_need = WEIGHT_FINANCIAL_NEED_MEDIUM
            reasons.append("Need-based award matches your medium financial need")

    breakdown.total = round(
        breakdown.field_of_study
        + breakdown.demographics
        + breakdown.target_school
        + breakdown.activities
        + breakdown.financial_need,
        2,
    )
    match_tier = _match_tier(breakdown.total)
    special_requirements = scholarship.eligibility.special_requirements
    # Fields listed in the dataset can be either firm eligibility rules or a
    # sponsor preference. Keep those opportunities visible, but never present
    # a field-mismatched result as a strong match.
    if field_mismatch and match_tier == "strong":
        match_tier = "possible"
    if school_mismatch and match_tier == "strong":
        match_tier = "possible"
    if special_requirements:
        reasons.append(
            "Special eligibility to check: "
            + "; ".join(requirement.label for requirement in special_requirements)
        )
        if match_tier == "strong":
            match_tier = "possible"

    weighted_zero: list[tuple[str, float]] = []
    if required_fields and breakdown.field_of_study == 0:
        weighted_zero.append(
            (f"No field overlap; field fit adds up to {int(WEIGHT_FIELD_OF_STUDY)} points", WEIGHT_FIELD_OF_STUDY)
        )
    if required_demographics and breakdown.demographics == 0:
        weighted_zero.append(
            (
                f"No demographic overlap; this award adds up to {int(WEIGHT_DEMOGRAPHICS)} points for it",
                WEIGHT_DEMOGRAPHICS,
            )
        )
    if eligible_schools and student.target_schools and breakdown.target_school == 0:
        weighted_zero.append(
            (f"No target school match; a school match adds {int(WEIGHT_TARGET_SCHOOL)} points", WEIGHT_TARGET_SCHOOL)
        )
    reasons.extend(_explanation_lines(breakdown, weighted_zero=weighted_zero))

    return MatchResult(
        scholarship_id=scholarship.id,
        scholarship_name=scholarship.name,
        sponsor=scholarship.sponsor,
        award_amount=scholarship.award_amount,
        deadline=scholarship.deadline,
        estimated_deadline=scholarship.estimated_deadline,
        url=str(scholarship.url),
        verified=scholarship.verified,
        verification_source_url=(
            str(scholarship.verification.source_url)
            if scholarship.verification is not None
            else None
        ),
        last_verified_at=(
            scholarship.verification.last_verified_at
            if scholarship.verification is not None
            else None
        ),
        essay_required=scholarship.eligibility.essay_required,
        closing_soon=closing_soon,
        score=breakdown.total,
        match_tier=match_tier,
        match_reasons=reasons,
        score_breakdown=breakdown,
        eligible_schools=[school.name for school in scholarship.eligibility.eligible_schools],
        requires_special_check=bool(special_requirements),
        special_requirements=special_requirements,
        application_requirements=scholarship.application_requirements,
    )


def match_scholarships(
    student: StudentProfile,
    scholarships: list[Scholarship],
    *,
    today: date | None = None,
    skip_residency_gates: bool = False,
) -> list[MatchResult]:
    """Return scholarships ranked by transparent additive score (highest first)."""
    reference_date = today or date.today()
    results: list[MatchResult] = []
    for scholarship in scholarships:
        match = _evaluate_scholarship(
            student, scholarship, reference_date, skip_residency_gates=skip_residency_gates
        )
        if match is not None:
            results.append(match)
    results.sort(key=lambda result: _sort_key(result, reference_date))
    return results


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
        if 0 < round(gap, 2) <= 0.3:
            qualifying_reason = f"Needs GPA {min_gpa:g}; your profile says {student.gpa:g}"

    grade_levels = scholarship.eligibility.grade_levels
    if grade_levels and not _grade_level_matches(student.grade_level, grade_levels):
        failures.append("grade")
        future = _earliest_future_qualifying_grade(student.grade_level, grade_levels)
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


def _near_miss_sort_key(entry: ScholarshipNearMiss) -> tuple:
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
