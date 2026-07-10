"""Transparent matching for elite summer programs.

Mirrors the scholarship matcher's additive, explainable approach and shares its
field, demographic, citizenship, grade, and deadline helpers (app.matching.common)
so the two stay consistent. Programs are scored on subject overlap, demographic fit, and a
financial-accessibility signal (a free or stipend program is a strong fit for a
student who indicated financial need). Grade level, GPA, citizenship, and a
passed deadline act as gates only when a real (non-VERIFY) value is present.
"""

from __future__ import annotations

from datetime import date

from app.matching.common import (
    FIELD_ADJACENCY,
    GRADE_LABELS,
    citizenship_satisfies,
    earliest_future_qualifying_grade,
    grade_level_matches,
    matching_demographics,
    matching_fields,
    normalize_tag,
    parse_iso_deadline,
    related_fields,
)
from app.models.program import (
    ProgramMatchResponse,
    ProgramMatchResult,
    ProgramNearMiss,
    ProgramScoreBreakdown,
    SummerProgram,
)
from app.models.student import StudentProfile

WEIGHT_SUBJECT = 40.0
WEIGHT_SUBJECT_OPEN = 10.0
WEIGHT_SUBJECT_RELATED = 20.0
WEIGHT_DEMOGRAPHICS = 25.0
WEIGHT_FINANCIAL_ACCESS = 10.0
STRONG_MATCH_THRESHOLD = 35.0


def _match_tier(score: float) -> str:
    return "strong" if score >= STRONG_MATCH_THRESHOLD else "possible"


def _explanation_lines(
    breakdown: ProgramScoreBreakdown, *, weighted_zero: list[tuple[str, float]]
) -> list[str]:
    """Mirrors matcher._explanation_lines for the program breakdown shape."""
    lines: list[str] = []
    components = [
        ("subject", breakdown.subject),
        ("demographics", breakdown.demographics),
        ("financial access", breakdown.financial_access),
    ]
    nonzero = [(name, pts) for name, pts in components if pts]
    if breakdown.total:
        joined = ", ".join(f"{name} {pts:g}" for name, pts in nonzero)
        lines.append(f"Fit score {breakdown.total:g}: {joined}")
    hints = sorted(weighted_zero, key=lambda pair: -pair[1])[:2]
    lines.extend(line for line, _pts in hints)
    return lines


def _evaluate_program(
    student: StudentProfile,
    program: SummerProgram,
    today: date,
) -> ProgramMatchResult | None:
    reasons: list[str] = []
    breakdown = ProgramScoreBreakdown()
    elig = program.eligibility

    # Grade level is a gate when the program states which grades it accepts.
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
    parsed_deadline = parse_iso_deadline(program.deadline)
    if parsed_deadline is not None and parsed_deadline < today:
        return None

    # Subject overlap is the primary fit signal.
    required_fields = elig.fields_of_study
    matched_fields = matching_fields(student.intended_majors, required_fields)
    related = related_fields(student.intended_majors, required_fields)
    field_mismatch = bool(required_fields) and not matched_fields and not related
    if not required_fields:
        breakdown.subject = WEIGHT_SUBJECT_OPEN
        reasons.append("Open to all subject areas")
    elif matched_fields:
        breakdown.subject = WEIGHT_SUBJECT
        reasons.append("Subject overlap: " + ", ".join(matched_fields))
    elif related:
        breakdown.subject = WEIGHT_SUBJECT_RELATED
        for field in related:
            student_field = next(
                major
                for major in student.intended_majors
                if normalize_tag(major) in FIELD_ADJACENCY.get(normalize_tag(field), set())
            )
            reasons.append(f"Related field: {field} (your {student_field} is adjacent)")
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

    # A free or stipend program is a strong practical fit for a student who
    # indicated financial need.
    if program.cost_category in {"free", "stipend"} and student.financial_need_level in {
        "medium",
        "high",
    }:
        breakdown.financial_access = WEIGHT_FINANCIAL_ACCESS
        reasons.append("Low-cost program fits your indicated financial need")

    breakdown.total = round(
        breakdown.subject + breakdown.demographics + breakdown.financial_access, 2
    )
    match_tier = _match_tier(breakdown.total)
    special_requirements = elig.special_requirements
    # A subject-mismatched program stays visible but never as a strong match.
    if field_mismatch and match_tier == "strong":
        match_tier = "possible"
    if special_requirements:
        reasons.append(
            "Special eligibility to check: "
            + "; ".join(requirement.label for requirement in special_requirements)
        )
        if match_tier == "strong":
            match_tier = "possible"

    weighted_zero: list[tuple[str, float]] = []
    if required_fields and breakdown.subject == 0:
        weighted_zero.append(
            (f"No subject overlap; subject fit adds up to {int(WEIGHT_SUBJECT)} points", WEIGHT_SUBJECT)
        )
    if elig.demographics and breakdown.demographics == 0:
        weighted_zero.append(
            (
                f"No demographic overlap; this program adds up to {int(WEIGHT_DEMOGRAPHICS)} points for it",
                WEIGHT_DEMOGRAPHICS,
            )
        )
    reasons.extend(_explanation_lines(breakdown, weighted_zero=weighted_zero))

    return ProgramMatchResult(
        program_id=program.id,
        name=program.name,
        host=program.host,
        subject=program.subject,
        cost=program.cost,
        cost_category=program.cost_category,
        selectivity=program.selectivity,
        program_format=program.program_format,
        location=program.location,
        program_dates=program.program_dates,
        deadline=program.deadline,
        estimated_deadline=program.estimated_deadline,
        url=str(program.url),
        verified=program.verified,
        verification_source_url=(
            str(program.verification.source_url)
            if program.verification is not None
            else None
        ),
        last_verified_at=(
            program.verification.last_verified_at
            if program.verification is not None
            else None
        ),
        essay_required=program.eligibility.essay_required,
        score=breakdown.total,
        match_tier=match_tier,
        match_reasons=reasons,
        score_breakdown=breakdown,
        application_requirements=program.application_requirements,
        requires_special_check=bool(special_requirements),
        special_requirements=special_requirements,
    )


def match_programs(
    student: StudentProfile,
    programs: list[SummerProgram],
    *,
    today: date | None = None,
) -> list[ProgramMatchResult]:
    """Return summer programs ranked by transparent additive score (highest first)."""
    reference_date = today or date.today()
    results: list[ProgramMatchResult] = []
    for program in programs:
        match = _evaluate_program(student, program, reference_date)
        if match is not None:
            results.append(match)
    results.sort(key=lambda result: (-result.score, result.name.lower()))
    return results


def _near_miss_reason_for(
    student: StudentProfile, program: SummerProgram, today: date
) -> str | None:
    """Reason string when the program fails EXACTLY one gate and that gate is a
    qualifying near-miss type; otherwise None. Gates checked: GPA, grade level,
    deadline, citizenship (the same gates _evaluate_program applies; programs
    have no state gate)."""
    failures: list[str] = []
    qualifying_reason: str | None = None
    elig = program.eligibility

    min_gpa = elig.min_gpa
    if isinstance(min_gpa, (int, float)) and student.gpa < float(min_gpa):
        gap = float(min_gpa) - student.gpa
        failures.append("gpa")
        if 0 < gap <= 0.3:
            qualifying_reason = f"Needs GPA {min_gpa:g}; your profile says {student.gpa:g}"

    grade_levels = elig.grade_levels
    if grade_levels and not grade_level_matches(student.grade_level, grade_levels):
        failures.append("grade")
        future = earliest_future_qualifying_grade(student.grade_level, grade_levels)
        if future is not None:
            qualifying_reason = f"Eligible when you are {GRADE_LABELS[future]}"

    parsed_deadline = parse_iso_deadline(program.deadline)
    if parsed_deadline is not None and parsed_deadline < today:
        failures.append("deadline")

    if citizenship_satisfies(student.citizenship, elig.citizenship_requirement) is False:
        failures.append("citizenship")

    if len(failures) != 1 or qualifying_reason is None:
        return None
    return qualifying_reason


def near_miss_programs(
    student: StudentProfile, programs: list[SummerProgram], today: date
) -> list[ProgramNearMiss]:
    entries: list[ProgramNearMiss] = []
    for program in programs:
        reason = _near_miss_reason_for(student, program, today)
        if reason is None:
            continue
        entries.append(
            ProgramNearMiss(
                program_id=program.id,
                name=program.name,
                host=program.host,
                cost=program.cost,
                deadline=program.deadline,
                estimated_deadline=program.estimated_deadline,
                url=str(program.url),
                verified=program.verified,
                near_miss_reason=reason,
            )
        )
    entries.sort(key=_near_miss_sort_key)
    return entries[:15]


def _near_miss_sort_key(entry: ProgramNearMiss) -> tuple:
    real = parse_iso_deadline(entry.deadline)
    if real is not None:
        return (0, real.toordinal(), entry.name.lower())
    est = parse_iso_deadline(entry.estimated_deadline or "")
    if est is not None:
        return (1, est.toordinal(), entry.name.lower())
    return (2, 0, entry.name.lower())


def match_programs_response(
    student: StudentProfile,
    programs: list[SummerProgram],
    *,
    today: date | None = None,
) -> ProgramMatchResponse:
    reference_date = today or date.today()
    return ProgramMatchResponse(
        matches=match_programs(student, programs, today=reference_date),
        near_misses=near_miss_programs(student, programs, reference_date),
    )
