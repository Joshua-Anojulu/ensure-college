"""Tests for the competitions feature: model, matcher gates/scoring, dataset, API."""

from datetime import date

from app.matching.competition_matcher import (
    match_competitions,
    match_competitions_response,
    near_miss_competitions,
)
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


def test_related_category_scores_partial_credit():
    comp = _competition(eligibility=Eligibility(fields_of_study=["engineering"]))
    student = _profile(intended_majors=["computer_science"])
    results = match_competitions(student, [comp], today=REF_DATE)

    assert len(results) == 1
    result = results[0]
    assert result.score_breakdown.category == 20.0
    assert any(
        reason.startswith("Related field: engineering") for reason in result.match_reasons
    )


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


def test_fit_context_line_lists_nonzero_components():
    comp = _competition(
        eligibility=Eligibility(fields_of_study=["engineering"]),
        cost_category="free",
    )
    student = _profile(intended_majors=["engineering"], financial_need_level="high")
    result = match_competitions(student, [comp], today=REF_DATE)[0]

    assert "Fit score 50: category 40, financial access 10" in result.match_reasons


def test_missing_category_hint_when_field_mismatch():
    comp = _competition(eligibility=Eligibility(fields_of_study=["engineering"]))
    student = _profile(intended_majors=["literature"], financial_need_level="low")
    result = match_competitions(student, [comp], today=REF_DATE)[0]

    assert result.score_breakdown.category == 0.0
    assert "No category overlap; category fit adds up to 40 points" in result.match_reasons


def test_competitions_dataset_loads_and_has_provenance():
    from app.data.loader import load_competitions

    competitions = load_competitions()
    assert len(competitions) >= 10
    for competition in competitions:
        assert competition.verification is not None
        assert str(competition.verification.source_url).startswith("http")
        requirement_ids = [r.id for r in competition.application_requirements]
        assert len(requirement_ids) == len(set(requirement_ids))


def test_competitions_dataset_has_no_structural_errors():
    from app.data.loader import load_competitions
    from scripts.validate_dataset import audit_competitions

    report = audit_competitions(load_competitions())
    assert report["errors"] == []


def test_competitions_dataset_has_no_vocabulary_warnings():
    from app.data.loader import load_competitions
    from scripts.validate_dataset import audit_competitions

    report = audit_competitions(load_competitions())
    vocab_warnings = [w for w in report["warnings"] if "not in vocabulary" in w]
    assert vocab_warnings == []


def test_api_competitions_endpoints():
    from fastapi.testclient import TestClient

    from app.main import app

    # Context manager triggers the lifespan so app.state.competitions is loaded.
    with TestClient(app) as client:
        listing = client.get("/competitions")
        assert listing.status_code == 200
        assert len(listing.json()) >= 10

        matched = client.post(
            "/competitions/match",
            json={
                "gpa": 3.8,
                "grade_level": "high_school_junior",
                "citizenship": "us_citizen",
                "state": "CA",
                "intended_majors": ["science", "mathematics"],
                "financial_need_level": "medium",
            },
        )
        assert matched.status_code == 200
        payload = matched.json()
        assert isinstance(payload["near_misses"], list)
        body = payload["matches"]
        assert isinstance(body, list) and len(body) >= 1
        first = body[0]
        assert {"competition_id", "score", "match_tier", "match_reasons"} <= first.keys()
        scores = [r["score"] for r in body]
        assert scores == sorted(scores, reverse=True)


class TestCompetitionNearMiss:
    def test_gpa_near_miss_within_window(self):
        student = _profile(gpa=3.6)
        comp = _competition(eligibility=Eligibility(min_gpa=3.8))

        nm = near_miss_competitions(student, [comp], REF_DATE)

        assert len(nm) == 1
        assert nm[0].near_miss_reason == "Needs GPA 3.8; your profile says 3.6"
        assert nm[0].competition_id == "c1"

    def test_gpa_gap_above_window_excluded(self):
        student = _profile(gpa=3.49)
        comp = _competition(eligibility=Eligibility(min_gpa=3.8))

        assert near_miss_competitions(student, [comp], REF_DATE) == []

    def test_future_grade_near_miss(self):
        student = _profile(grade_level="high_school_junior")
        comp = _competition(
            eligibility=Eligibility(
                fields_of_study=["engineering"], grade_levels=["high_school_senior"]
            )
        )

        nm = near_miss_competitions(student, [comp], REF_DATE)

        assert len(nm) == 1
        assert nm[0].near_miss_reason == "Eligible when you are a high school senior"

    def test_two_failed_gates_excluded(self):
        # GPA gap 0.2 (qualifying alone) AND unmet citizenship -> not a near miss.
        student = _profile(gpa=3.8, citizenship="international")
        comp = _competition(
            eligibility=Eligibility(
                fields_of_study=["engineering"],
                min_gpa=4.0,
                citizenship_requirement="us_citizen",
            )
        )

        assert near_miss_competitions(student, [comp], REF_DATE) == []

    def test_past_deadline_excluded_even_with_gap(self):
        student = _profile(gpa=3.8)
        comp = _competition(
            eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
            deadline="2020-01-01",
        )

        assert near_miss_competitions(student, [comp], REF_DATE) == []

    def test_near_miss_absent_from_matches(self):
        student = _profile(gpa=3.8)
        comp = _competition(eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0))

        nm = near_miss_competitions(student, [comp], REF_DATE)
        matches = match_competitions(student, [comp], today=REF_DATE)

        assert len(nm) == 1
        assert matches == []

    def test_response_wrapper_shape(self):
        student = _profile(gpa=3.8)
        passing = _competition(id="passing-competition")
        gap = _competition(
            id="near-miss-competition",
            eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
        )

        resp = match_competitions_response(student, [passing, gap], today=REF_DATE)

        assert resp.matches
        assert isinstance(resp.near_misses, list)
        assert len(resp.near_misses) == 1
        assert resp.near_misses[0].competition_id == "near-miss-competition"

    def test_cap_and_ordering(self):
        student = _profile(gpa=3.8)
        comps: list[Competition] = []

        real_dates = [
            "2026-08-01",
            "2026-07-01",
            "2026-09-01",
            "2026-06-30",
            "2026-10-01",
            "2026-06-27",
        ]
        for i, deadline in enumerate(real_dates):
            comps.append(
                _competition(
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
            comps.append(
                _competition(
                    id=f"estimated-{i}",
                    name=f"Estimated {i}",
                    deadline="VERIFY",
                    estimated_deadline=estimate,
                    eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
                )
            )

        for name in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF"):
            comps.append(
                _competition(
                    id=f"none-{name}",
                    name=name,
                    deadline="VERIFY",
                    eligibility=Eligibility(fields_of_study=["engineering"], min_gpa=4.0),
                )
            )

        assert len(comps) == 17

        nm = near_miss_competitions(student, comps, REF_DATE)

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
        assert [entry.competition_id for entry in nm] == expected_order


def test_save_list_update_and_remove_competition():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        signup = client.post(
            "/auth/signup",
            json={"email": "comp-saver@example.com", "password": "password123"},
        )
        assert signup.status_code == 201

        competition_id = client.get("/competitions").json()[0]["id"]

        saved = client.post(f"/account/saved/competitions/{competition_id}")
        assert saved.status_code == 201
        assert saved.json()["competition_id"] == competition_id
        assert saved.json()["competition"]["id"] == competition_id

        # Idempotent double-save.
        again = client.post(f"/account/saved/competitions/{competition_id}")
        assert again.status_code == 201

        listing = client.get("/account/saved").json()
        assert [c["competition_id"] for c in listing["competitions"]] == [competition_id]

        updated = client.patch(
            f"/account/saved/competitions/{competition_id}",
            json={"status": "drafting", "notes": "register early"},
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == "drafting"
        assert updated.json()["notes"] == "register early"

        unknown = client.post("/account/saved/competitions/not-a-real-competition")
        assert unknown.status_code == 404

        removed = client.delete(f"/account/saved/competitions/{competition_id}")
        assert removed.status_code == 200
        assert client.get("/account/saved").json()["competitions"] == []
