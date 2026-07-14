"""Guards on the curated scholarship dataset. These keep structural quality green
as entries are edited or verified over time."""

import json
from datetime import timedelta
from pathlib import Path

from app.data.loader import DEFAULT_SPECIAL_REQUIREMENTS_PATH, load_scholarships
from app.models.competition import Competition
from app.models.program import SummerProgram
from app.models.scholarship import Eligibility, Scholarship, SpecialRequirement
from scripts.validate_dataset import (
    audit_competitions,
    audit_dataset,
    audit_programs,
    cross_lane_duplicate_errors,
)


def test_dataset_loads_and_has_entries():
    scholarships = load_scholarships()
    assert len(scholarships) >= 100


def test_no_opportunity_lives_in_two_lanes():
    """An opportunity belongs to exactly one lane.

    Each lane only ever checked its own ids, so a contest could sit in
    scholarships AND competitions: the student saw it twice, and the two copies'
    facts drifted apart.
    """
    from app.data.loader import load_competitions, load_summer_programs

    errors = cross_lane_duplicate_errors(
        load_scholarships(), load_summer_programs(), load_competitions()
    )
    assert errors == []


def _scholarship(**overrides):
    base = {
        "id": "synthetic-scholarship",
        "name": "Synthetic Scholarship",
        "sponsor": "Synthetic Sponsor",
        "award_amount": 1000,
        "deadline": "VERIFY",
        "url": "https://example.org/scholarship",
        "eligibility": Eligibility(),
        "description": "Synthetic scholarship for dataset validator tests.",
        "verified": True,
    }
    base.update(overrides)
    return Scholarship(**base)


def _program(**overrides):
    base = {
        "id": "synthetic-program",
        "name": "Synthetic Program",
        "host": "Synthetic Host",
        "subject": "Synthetic subject",
        "url": "https://example.org/program",
        "eligibility": Eligibility(),
        "description": "Synthetic program for dataset validator tests.",
        "verified": True,
    }
    base.update(overrides)
    return SummerProgram(**base)


def _competition(**overrides):
    base = {
        "id": "synthetic-competition",
        "name": "Synthetic Competition",
        "host": "Synthetic Host",
        "category": "Synthetic category",
        "url": "https://example.org/competition",
        "eligibility": Eligibility(),
        "description": "Synthetic competition for dataset validator tests.",
        "verified": True,
    }
    base.update(overrides)
    return Competition(**base)


def test_special_requirement_model_accepts_new_niche_kinds():
    for kind in ("identity_or_status", "program_content", "activity_or_lifestyle"):
        req = SpecialRequirement(
            kind=kind,
            label="Synthetic special check",
            details="Synthetic details for the special-check lane.",
        )
        assert req.kind == kind


def test_dataset_has_no_structural_errors():
    report = audit_dataset(load_scholarships())
    assert report["errors"] == [], report["errors"]


def test_no_vocabulary_warnings():
    # The seed set should only use canonical field/grade/demographic/state tags.
    #
    # Staleness warnings ("...has passed") are excluded on purpose: they depend
    # on today's date, so asserting on them here would turn CI red on an
    # arbitrary future morning when a deadline rolls by. They are advisory, and
    # `scripts/validate_dataset.py` still reports them to whoever runs the audit.
    report = audit_dataset(load_scholarships())
    warnings = [w for w in report["warnings"] if "has passed" not in w]
    assert warnings == [], warnings


def test_audit_warns_when_hard_identity_requirement_is_not_special_checked():
    scholarship = _scholarship(
        id="women-only",
        description="Open only to women pursuing engineering degrees.",
    )

    report = audit_dataset([scholarship])

    assert any(
        "women-only" in warning and "identity/status" in warning
        for warning in report["warnings"]
    )


def test_audit_accepts_encoded_hard_identity_requirement():
    scholarship = _scholarship(
        id="women-only-encoded",
        description="Open only to women pursuing engineering degrees.",
        eligibility=Eligibility(
            special_requirements=[
                SpecialRequirement(
                    kind="identity_or_status",
                    label="Women applicants only",
                    details="Open only to women pursuing engineering degrees.",
                )
            ]
        ),
    )

    report = audit_dataset([scholarship])

    assert report["warnings"] == []


def test_audit_warns_for_niche_requirements_across_all_lanes():
    scholarship = _scholarship(
        id="first-gen-only",
        description="Applicants must be first-generation college students.",
    )
    program = _program(
        id="disability-program",
        description="Restricted to students with a documented disability.",
    )
    competition = _competition(
        id="member-competition",
        description="Students must be active members of a local coding league to enter.",
    )

    scholarship_report = audit_dataset([scholarship])
    program_report = audit_programs([program])
    competition_report = audit_competitions([competition])

    assert any("first-gen-only" in warning for warning in scholarship_report["warnings"])
    assert any("disability-program" in warning for warning in program_report["warnings"])
    assert any("member-competition" in warning for warning in competition_report["warnings"])


def test_audit_ignores_known_niche_requirement_trap_phrasings():
    scholarships = [
        _scholarship(
            id="regardless-immigration",
            description="Open regardless of immigration status, including DACA recipients.",
        ),
        _scholarship(
            id="lgbtq-allies",
            description="Scholarship supporting LGBTQ+ statisticians and allies pursuing data science.",
        ),
        _scholarship(
            id="daca-alone",
            description="Requires demonstrated financial need; DACA status alone does not qualify.",
        ),
        _scholarship(
            id="women-and-or",
            description="Targets women and/or members of racial or ethnic groups underrepresented in computing.",
        ),
    ]

    report = audit_dataset(scholarships)

    assert report["warnings"] == []


def test_audit_flags_duplicate_special_requirements_after_merge():
    scholarship = _scholarship(
        id="duplicate-special",
        eligibility=Eligibility(
            special_requirements=[
                SpecialRequirement(
                    kind="membership",
                    label="Local chapter membership required",
                    details="Applicants must be members of the local chapter.",
                ),
                SpecialRequirement(
                    kind="membership",
                    label=" local   chapter membership required ",
                    details="Applicants must be members of the local chapter.",
                ),
            ]
        ),
    )

    report = audit_dataset([scholarship])

    assert any("duplicate special requirement" in error for error in report["errors"])


def test_school_pilot_entries_have_provenance():
    by_id = {s.id: s for s in load_scholarships()}
    pilot_ids = (
        "forty-acres-scholars-program",
        "tamu-opportunity-award",
        "georgia-tech-gold-scholars",
        "ut-dallas-aes",
        "cmu-pathway-program",
    )
    for scholarship_id in pilot_ids:
        entry = by_id[scholarship_id]
        assert entry.verified is True
        assert entry.verification is not None
        assert entry.verification.last_verified_at is not None
        assert entry.eligibility.eligible_schools
        assert entry.application_requirements


def test_checklist_programs_meet_expansion_goal():
    with_checklists = [
        scholarship
        for scholarship in load_scholarships()
        if scholarship.application_requirements
    ]
    assert len(with_checklists) >= 20
    assert all(req.source_url for scholarship in with_checklists for req in scholarship.application_requirements)


def test_ids_are_unique():
    ids = [s.id for s in load_scholarships()]
    assert len(ids) == len(set(ids))


def test_special_requirements_sidecar_targets_existing_scholarships():
    scholarships = load_scholarships()
    ids = {s.id for s in scholarships}
    raw = json.loads(Path(DEFAULT_SPECIAL_REQUIREMENTS_PATH).read_text(encoding="utf-8"))
    sidecar_ids = set(raw["requirements"])

    assert sidecar_ids
    assert sidecar_ids.issubset(ids)


def test_ieee_presidents_is_marked_as_special_check():
    by_id = {s.id: s for s in load_scholarships()}
    ieee = by_id["ieee-presidents-scholarship"]

    assert ieee.eligibility.special_requirements
    assert any(
        requirement.kind == "competition_or_finalist"
        for requirement in ieee.eligibility.special_requirements
    )
    assert any(
        requirement.kind == "no_direct_application"
        for requirement in ieee.eligibility.special_requirements
    )


def test_audit_reports_reverification_queue():
    scholarships = load_scholarships()
    report = audit_dataset(scholarships)
    assert "needs_reverification_ids" in report
    assert "stale_audit_ids" in report
    assert "needs_reverification" in report["stats"]
    assert "stale_audit" in report["stats"]
    source_only_ids = {
        scholarship.id
        for scholarship in scholarships
        if scholarship.verified
        and scholarship.verification is not None
        and scholarship.verification.last_verified_at is None
    }
    assert source_only_ids
    assert source_only_ids.issubset(set(report["needs_reverification_ids"]))


def _pilot_audit_dates(scholarships):
    pilot_ids = {
        "forty-acres-scholars-program",
        "tamu-opportunity-award",
        "georgia-tech-gold-scholars",
        "ut-dallas-aes",
        "cmu-pathway-program",
    }
    return [
        s.verification.last_verified_at
        for s in scholarships
        if s.id in pilot_ids and s.verification and s.verification.last_verified_at
    ]


def test_audits_are_not_stale_at_the_90_day_boundary():
    scholarships = load_scholarships()
    audit_dates = _pilot_audit_dates(scholarships)
    assert len(audit_dates) == 5
    # The policy is strictly older than 90 days, not 90 days or older.
    at_boundary = max(audit_dates) + timedelta(days=90)
    report = audit_dataset(scholarships, today=at_boundary)
    assert report["stats"]["stale_audit"] == 0


def test_audits_go_stale_after_window():
    scholarships = load_scholarships()
    audit_dates = _pilot_audit_dates(scholarships)
    # The next day, every audited pilot crosses the staleness threshold.
    just_after_window = max(audit_dates) + timedelta(days=91)
    report = audit_dataset(scholarships, today=just_after_window)
    assert report["stats"]["stale_audit"] >= 5
    # Stale entries are a subset of the actionable re-verification queue.
    assert set(report["stale_audit_ids"]).issubset(set(report["needs_reverification_ids"]))
