"""Transparent matching for competitions.

Mirrors the summer-program matcher's additive, explainable approach and shares its
field, demographic, citizenship, grade, and deadline helpers (app.matching.common)
so the verticals stay consistent. Competitions are scored on category overlap,
demographic fit, and a financial-accessibility signal (a free or stipend
competition is a strong fit for a student who indicated financial need). Grade
level, GPA, citizenship, and a passed deadline act as gates only when a real
(non-VERIFY) value is present.
"""

from __future__ import annotations

from datetime import date

from app.matching.common import (
    citizenship_satisfies,
    grade_level_matches,
    matching_demographics,
    matching_fields,
    parse_iso_deadline,
)
from app.models.competition import (
    Competition,
    CompetitionMatchResult,
    CompetitionScoreBreakdown,
)
from app.models.student import StudentProfile

WEIGHT_CATEGORY = 40.0
WEIGHT_CATEGORY_OPEN = 10.0
WEIGHT_DEMOGRAPHICS = 25.0
WEIGHT_FINANCIAL_ACCESS = 10.0
STRONG_MATCH_THRESHOLD = 35.0


def _match_tier(score: float) -> str:
    return "strong" if score >= STRONG_MATCH_THRESHOLD else "possible"


def _evaluate_competition(
    student: StudentProfile,
    competition: Competition,
    today: date,
) -> CompetitionMatchResult | None:
    reasons: list[str] = []
    breakdown = CompetitionScoreBreakdown()
    elig = competition.eligibility

    # Grade level is a gate when the competition states which grades it accepts.
    if elig.grade_levels:
        if not grade_level_matches(student.grade_level, elig.grade_levels):
            return None
        reasons.append(f"Open to your grade level ({student.grade_level})")
    else:
        reasons.append("No specific grade level requirement")

    # GPA gates only on a real numeric floor.
    if isinstance(elig.min_gpa, (int, float)):
        if student.gpa < float(elig.min_gpa):
            return None
        reasons.append(f"Meets GPA requirement (minimum {elig.min_gpa})")

    # Citizenship gates only when known and not satisfied.
    citizenship_result = citizenship_satisfies(
        student.citizenship, elig.citizenship_requirement
    )
    if citizenship_result is False:
        return None
    if citizenship_result is True:
        if elig.citizenship_requirement == "any":
            reasons.append("Open regardless of citizenship")
        else:
            reasons.append("Meets citizenship requirement")
    else:
        reasons.append("Citizenship requirement not yet verified")

    # A passed deadline excludes only when a real date is published.
    parsed_deadline = parse_iso_deadline(competition.deadline)
    if parsed_deadline is not None and parsed_deadline < today:
        return None

    # Category overlap is the primary fit signal.
    required_fields = elig.fields_of_study
    matched_fields = matching_fields(student.intended_majors, required_fields)
    field_mismatch = bool(required_fields) and not matched_fields
    if not required_fields:
        breakdown.category = WEIGHT_CATEGORY_OPEN
        reasons.append("Open to all subject areas")
    elif matched_fields:
        breakdown.category = WEIGHT_CATEGORY
        reasons.append("Category overlap: " + ", ".join(matched_fields))
    else:
        reasons.append("May focus on a different subject area, check eligibility")

    matched_demographics = matching_demographics(
        student.demographic_tags, elig.demographics
    )
    if elig.demographics and matched_demographics:
        fraction = len(matched_demographics) / len(elig.demographics)
        breakdown.demographics = round(WEIGHT_DEMOGRAPHICS * fraction, 2)
        for tag in matched_demographics:
            reasons.append(f"Demographic match: {tag}")

    # A free or stipend competition is a strong practical fit for a student who
    # indicated financial need.
    if competition.cost_category in {"free", "stipend"} and student.financial_need_level in {
        "medium",
        "high",
    }:
        breakdown.financial_access = WEIGHT_FINANCIAL_ACCESS
        reasons.append("Low-cost competition fits your indicated financial need")

    breakdown.total = round(
        breakdown.category + breakdown.demographics + breakdown.financial_access, 2
    )
    match_tier = _match_tier(breakdown.total)
    special_requirements = elig.special_requirements
    # A category-mismatched competition stays visible but never as a strong match.
    if field_mismatch and match_tier == "strong":
        match_tier = "possible"
    if special_requirements:
        reasons.append(
            "Special eligibility to check: "
            + "; ".join(requirement.label for requirement in special_requirements)
        )
        if match_tier == "strong":
            match_tier = "possible"

    return CompetitionMatchResult(
        competition_id=competition.id,
        name=competition.name,
        host=competition.host,
        category=competition.category,
        cost=competition.cost,
        cost_category=competition.cost_category,
        recognition=competition.recognition,
        participation_format=competition.participation_format,
        location=competition.location,
        competition_dates=competition.competition_dates,
        deadline=competition.deadline,
        estimated_deadline=competition.estimated_deadline,
        url=str(competition.url),
        verified=competition.verified,
        verification_source_url=(
            str(competition.verification.source_url)
            if competition.verification is not None
            else None
        ),
        last_verified_at=(
            competition.verification.last_verified_at
            if competition.verification is not None
            else None
        ),
        essay_required=competition.eligibility.essay_required,
        score=breakdown.total,
        match_tier=match_tier,
        match_reasons=reasons,
        score_breakdown=breakdown,
        application_requirements=competition.application_requirements,
        requires_special_check=bool(special_requirements),
        special_requirements=special_requirements,
    )


def match_competitions(
    student: StudentProfile,
    competitions: list[Competition],
    *,
    today: date | None = None,
) -> list[CompetitionMatchResult]:
    """Return competitions ranked by transparent additive score (highest first)."""
    reference_date = today or date.today()
    results: list[CompetitionMatchResult] = []
    for competition in competitions:
        match = _evaluate_competition(student, competition, reference_date)
        if match is not None:
            results.append(match)
    results.sort(key=lambda result: (-result.score, result.name.lower()))
    return results
