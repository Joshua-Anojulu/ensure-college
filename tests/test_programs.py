"""Tests for the elite summer-programs feature: dataset, matcher gates/scoring, API."""

from datetime import date

from fastapi.testclient import TestClient

from app.data.loader import load_summer_programs
from app.main import app
from app.matching.program_matcher import (
    match_programs,
    match_programs_response,
    near_miss_programs,
)
from app.models.program import SummerProgram
from app.models.scholarship import Eligibility
from app.models.student import StudentProfile

REF_DATE = date(2026, 6, 26)


def _profile(**overrides) -> StudentProfile:
    base = {
        "gpa": 3.9,
        "grade_level": "high_school_junior",
        "citizenship": "us_citizen",
        "state": "TX",
        "intended_majors": ["engineering"],
        "demographic_tags": [],
        "financial_need_level": "high",
        "activities": [],
        "target_schools": [],
    }
    base.update(overrides)
    return StudentProfile(**base)


def _program(**overrides) -> SummerProgram:
    base = dict(
        id="p1",
        name="Test Program",
        host="Test Host",
        subject="STEM research",
        url="https://example.org/",
        eligibility=Eligibility(fields_of_study=["engineering"]),
        description="A test program.",
    )
    base.update(overrides)
    return SummerProgram(**base)


def test_programs_dataset_loads_and_is_verified():
    programs = load_summer_programs()
    assert len(programs) >= 3
    for program in programs:
        assert program.verified is True
        assert program.verification is not None
        assert program.verification.last_verified_at is not None
        requirement_ids = [requirement.id for requirement in program.application_requirements]
        assert len(requirement_ids) == len(set(requirement_ids))


def test_stem_junior_matches_free_program_with_financial_bonus():
    programs = load_summer_programs()
    results = match_programs(_profile(), programs, today=REF_DATE)
    by_id = {r.program_id: r for r in results}
    assert "mites-summer" in by_id
    mites = by_id["mites-summer"]
    assert mites.score_breakdown.subject > 0  # engineering overlaps MITES STEM
    assert mites.score_breakdown.financial_access > 0  # free + high need
    assert mites.match_tier == "strong"


def test_grade_level_gates_out_a_non_junior():
    programs = load_summer_programs()
    senior = _profile(grade_level="high_school_senior", intended_majors=["science"])
    ids = {r.program_id for r in match_programs(senior, programs, today=REF_DATE)}
    assert "mites-summer" not in ids  # MITES is juniors only
    assert "summer-science-program" not in ids  # SSP is current juniors / rising seniors


def test_junior_matches_ssp_and_programs_include_checklists():
    programs = load_summer_programs()
    junior = _profile(grade_level="high_school_junior", intended_majors=["science"])
    by_id = {r.program_id: r for r in match_programs(junior, programs, today=REF_DATE)}

    assert "summer-science-program" in by_id
    assert by_id["summer-science-program"].application_requirements
    assert by_id["mites-summer"].essay_required is True
    assert by_id["promys"].essay_required is True


def test_special_program_requirement_caps_strong_match_and_flags_manual_check():
    programs = load_summer_programs()
    junior = _profile(
        grade_level="high_school_junior",
        intended_majors=["science"],
        citizenship="us_citizen",
    )
    by_id = {r.program_id: r for r in match_programs(junior, programs, today=REF_DATE)}

    simons = by_id["simons-summer-research"]
    assert simons.match_tier == "possible"
    assert simons.requires_special_check is True
    assert simons.special_requirements[0].label == "High school nomination required"
    assert any("Special eligibility to check" in reason for reason in simons.match_reasons)


def test_broad_legacy_high_school_profile_does_not_match_junior_only_program():
    programs = load_summer_programs()
    broad = _profile(grade_level="high_school")
    ids = {r.program_id for r in match_programs(broad, programs, today=REF_DATE)}
    assert "mites-summer" not in ids


def test_citizenship_gates_out_international_for_us_only_program():
    programs = load_summer_programs()
    intl = _profile(
        grade_level="high_school",
        citizenship="international",
        intended_majors=["mathematics"],
    )
    ids = {r.program_id for r in match_programs(intl, programs, today=REF_DATE)}
    assert "mites-summer" not in ids  # requires US citizen / permanent resident
    assert "promys" in ids  # PROMYS is open regardless of citizenship


def test_related_subject_scores_partial_credit():
    program = _program(eligibility=Eligibility(fields_of_study=["engineering"]))
    student = _profile(intended_majors=["computer_science"])
    results = match_programs(student, [program], today=REF_DATE)

    assert len(results) == 1
    result = results[0]
    assert result.score_breakdown.subject == 20.0
    assert any(
        reason.startswith("Related field: engineering") for reason in result.match_reasons
    )


def test_fit_context_line_lists_nonzero_components():
    program = _program(
        eligibility=Eligibility(fields_of_study=["engineering"]),
        cost_category="free",
    )
    student = _profile(intended_majors=["engineering"], financial_need_level="high")
    result = match_programs(student, [program], today=REF_DATE)[0]

    assert "Fit score 50: subject 40, financial access 10" in result.match_reasons


def test_missing_subject_hint_when_field_mismatch():
    program = _program(eligibility=Eligibility(fields_of_study=["engineering"]))
    student = _profile(intended_majors=["literature"], financial_need_level="low")
    result = match_programs(student, [program], today=REF_DATE)[0]

    assert result.score_breakdown.subject == 0.0
    assert "No subject overlap; subject fit adds up to 40 points" in result.match_reasons


def test_api_programs_endpoints():
    # Context manager triggers the lifespan so app.state.programs is loaded.
    with TestClient(app) as client:
        listing = client.get("/programs")
        assert listing.status_code == 200
        assert len(listing.json()) >= 3

        matched = client.post(
            "/programs/match",
            json={
                "gpa": 3.8,
                "grade_level": "high_school_junior",
                "citizenship": "us_citizen",
                "state": "CA",
                "intended_majors": ["engineering"],
                "financial_need_level": "medium",
            },
        )
        assert matched.status_code == 200
        payload = matched.json()
        assert isinstance(payload["near_misses"], list)
        body = payload["matches"]
        assert isinstance(body, list) and len(body) >= 1
        first = body[0]
        assert {"program_id", "score", "match_tier", "match_reasons"} <= first.keys()


class TestProgramNearMiss:
    def test_gpa_near_miss_within_window(self):
        student = _profile(gpa=3.6)
        program = _program(eligibility=Eligibility(min_gpa=3.8))

        nm = near_miss_programs(student, [program], REF_DATE)

        assert len(nm) == 1
        assert nm[0].near_miss_reason == "Needs GPA 3.8; your profile says 3.6"
        assert nm[0].program_id == "p1"

    def test_gpa_gap_above_window_excluded(self):
        student = _profile(gpa=3.49)
        program = _program(eligibility=Eligibility(min_gpa=3.8))

        assert near_miss_programs(student, [program], REF_DATE) == []

    def test_future_grade_near_miss(self):
        student = _profile(grade_level="high_school_junior")
        program = _program(
            eligibility=Eligibility(
                fields_of_study=["engineering"], grade_levels=["high_school_senior"]
            )
        )

        nm = near_miss_programs(student, [program], REF_DATE)

        assert len(nm) == 1
        assert nm[0].near_miss_reason == "Eligible when you are a high school senior"

    def test_two_failed_gates_excluded(self):
        # GPA gap 0.2 (qualifying alone) AND unmet citizenship -> not a near miss.
        student = _profile(gpa=3.8, citizenship="international")
        program = _program(
            eligibility=Eligibility(
                fields_of_study=["engineering"],
                min_gpa=4.0,
                citizenship_requirement="us_citizen",
            )
        )

        assert near_miss_programs(student, [program], REF_DATE) == []

    def test_past_deadline_excluded_even_with_gap(self):
        student = _profile(gpa=3.8)
        program = _program(
            eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
            deadline="2020-01-01",
        )

        assert near_miss_programs(student, [program], REF_DATE) == []

    def test_near_miss_absent_from_matches(self):
        student = _profile(gpa=3.8)
        program = _program(eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0))

        nm = near_miss_programs(student, [program], REF_DATE)
        matches = match_programs(student, [program], today=REF_DATE)

        assert len(nm) == 1
        assert matches == []

    def test_response_wrapper_shape(self):
        student = _profile(gpa=3.8)
        passing = _program(id="passing-program")
        gap = _program(
            id="near-miss-program",
            eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
        )

        resp = match_programs_response(student, [passing, gap], today=REF_DATE)

        assert resp.matches
        assert isinstance(resp.near_misses, list)
        assert len(resp.near_misses) == 1
        assert resp.near_misses[0].program_id == "near-miss-program"

    def test_cap_and_ordering(self):
        student = _profile(gpa=3.8)
        programs: list[SummerProgram] = []

        real_dates = [
            "2026-08-01",
            "2026-07-01",
            "2026-09-01",
            "2026-06-30",
            "2026-10-01",
            "2026-06-27",
        ]
        for i, deadline in enumerate(real_dates):
            programs.append(
                _program(
                    id=f"real-{i}",
                    name=f"Real {i}",
                    deadline=deadline,
                    eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
                )
            )

        estimated_dates = [
            "2026-05-01",
            "2026-04-01",
            "2026-06-01",
            "2026-03-01",
            "2026-02-01",
        ]
        for i, estimate in enumerate(estimated_dates):
            programs.append(
                _program(
                    id=f"estimated-{i}",
                    name=f"Estimated {i}",
                    deadline="VERIFY",
                    estimated_deadline=estimate,
                    eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
                )
            )

        for name in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF"):
            programs.append(
                _program(
                    id=f"none-{name}",
                    name=name,
                    deadline="VERIFY",
                    eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
                )
            )

        assert len(programs) == 17

        nm = near_miss_programs(student, programs, REF_DATE)

        assert len(nm) == 15
        expected_order = [
            "real-5",  # 2026-06-27
            "real-3",  # 2026-06-30
            "real-1",  # 2026-07-01
            "real-0",  # 2026-08-01
            "real-2",  # 2026-09-01
            "real-4",  # 2026-10-01
            "estimated-4",  # 2026-02-01
            "estimated-3",  # 2026-03-01
            "estimated-1",  # 2026-04-01
            "estimated-0",  # 2026-05-01
            "estimated-2",  # 2026-06-01
            "none-AAA",
            "none-BBB",
            "none-CCC",
            "none-DDD",
        ]
        assert [entry.program_id for entry in nm] == expected_order
