"""Tests for the competitions feature: model, matcher gates/scoring, dataset, API."""

from datetime import date

from app.matching.competition_matcher import match_competitions
from app.models.competition import Competition
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


def _competition(**overrides) -> Competition:
    base = dict(
        id="c1",
        name="Test Competition",
        host="Test Host",
        category="STEM research",
        url="https://example.org/",
        eligibility=Eligibility(fields_of_study=["engineering"]),
        description="A test competition.",
        deadline="VERIFY",
    )
    base.update(overrides)
    return Competition(**base)


def test_competition_defaults_unconfirmed_fields_to_verify():
    c = Competition(
        id="isef",
        name="Regeneron ISEF",
        host="Society for Science",
        category="STEM research",
        url="https://www.societyforscience.org/isef/",
        eligibility=Eligibility(),
        description="International science and engineering fair.",
    )
    assert c.cost_category == "VERIFY"
    assert c.participation_format == "VERIFY"
    assert c.deadline == "VERIFY"
    assert c.verified is False


def test_strong_category_match_scores_high():
    comp = _competition(
        eligibility=Eligibility(fields_of_study=["engineering"]),
        cost_category="free",
    )
    results = match_competitions(_profile(), [comp], today=REF_DATE)
    assert len(results) == 1
    result = results[0]
    assert result.score_breakdown.category > 0
    assert result.match_tier == "strong"


def test_passed_real_deadline_excludes():
    comp = _competition(deadline="2026-01-01")
    results = match_competitions(_profile(), [comp], today=REF_DATE)
    assert results == []


def test_grade_gate_excludes_when_not_met():
    comp = _competition(
        eligibility=Eligibility(
            fields_of_study=["engineering"],
            grade_levels=["high_school_senior"],
        )
    )
    junior = _profile(grade_level="high_school_junior")
    assert match_competitions(junior, [comp], today=REF_DATE) == []


def test_open_category_competition_appears_as_possible():
    comp = _competition(eligibility=Eligibility(fields_of_study=[]))
    student = _profile(intended_majors=["philosophy"])
    results = match_competitions(student, [comp], today=REF_DATE)
    assert len(results) == 1
    result = results[0]
    assert result.score_breakdown.category > 0  # open-to-all credit
    assert result.match_tier == "possible"
    assert any("Open to all" in reason for reason in result.match_reasons)
