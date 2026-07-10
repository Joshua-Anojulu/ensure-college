from datetime import date

import pytest

from app.matching.matcher import (
    match_scholarships,
    match_scholarships_response,
    near_miss_scholarships,
)
from app.models.scholarship import Eligibility, Scholarship
from app.models.student import StudentProfile

TEST_URL = "https://example.org/scholarship"
FIXED_TODAY = date(2026, 6, 13)


def make_student(**overrides) -> StudentProfile:
    defaults = {
        "gpa": 3.8,
        "grade_level": "high_school_senior",
        "intended_majors": ["engineering"],
        "demographic_tags": ["african_american"],
        "state": "CA",
        "citizenship": "us_citizen",
        "financial_need_level": "high",
        "activities": ["robotics club"],
    }
    defaults.update(overrides)
    return StudentProfile(**defaults)


def make_scholarship(**overrides) -> Scholarship:
    eligibility_defaults = {
        "min_gpa": 3.5,
        "fields_of_study": ["engineering"],
        "grade_levels": ["high_school_senior"],
        "demographics": ["african_american"],
        "states": "any",
        "essay_required": True,
        "citizenship_requirement": "us_citizen",
    }
    scholarship_defaults = {
        "id": "test-scholarship",
        "name": "Test Scholarship",
        "sponsor": "Test Foundation",
        "award_amount": 10000,
        "deadline": "2026-09-30",
        "url": TEST_URL,
        "eligibility": eligibility_defaults,
        "description": "A test scholarship for unit tests.",
        "verified": False,
    }
    if "eligibility" in overrides:
        merged = {**eligibility_defaults, **overrides.pop("eligibility")}
        scholarship_defaults["eligibility"] = merged
    scholarship_defaults.update(overrides)
    return Scholarship(**scholarship_defaults)


def match_one(student: StudentProfile, scholarship: Scholarship):
    results = match_scholarships(student, [scholarship], today=FIXED_TODAY)
    return results[0] if results else None


class TestPerfectMatch:
    def test_perfect_match_scores_high_and_lists_reasons(self):
        student = make_student()
        scholarship = make_scholarship(
            eligibility={"fields_of_study": ["engineering"]},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score == pytest.approx(65.0)
        assert result.verified is False
        assert "Meets GPA requirement (minimum 3.5)" in result.match_reasons
        assert "Grade level matches (high_school_senior)" in result.match_reasons
        assert "Meets citizenship requirement" in result.match_reasons
        assert "Field of study overlap: engineering" in result.match_reasons
        assert "Demographic match: african_american" in result.match_reasons
        assert result.score_breakdown.total == result.score
        assert result.closing_soon is False


class TestApplicationRequirements:
    def test_scholarship_with_requirements_passes_them_through(self):
        student = make_student()
        scholarship = make_scholarship(
            eligibility={"fields_of_study": ["engineering"]},
            application_requirements=[
                {
                    "id": "transcript",
                    "label": "Submit an official transcript",
                    "required": True,
                    "source_url": TEST_URL,
                },
                {
                    "id": "essay",
                    "label": "Write a 500-word essay",
                    "required": True,
                    "source_url": TEST_URL,
                },
            ],
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert [req.id for req in result.application_requirements] == ["transcript", "essay"]

    def test_scholarship_without_requirements_returns_empty_list(self):
        student = make_student()
        scholarship = make_scholarship(
            eligibility={"fields_of_study": ["engineering"]},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.application_requirements == []


class TestFieldScoring:
    def test_specific_field_match_scores_above_open_to_all(self):
        student = make_student(intended_majors=["engineering"])
        specific = make_scholarship(
            id="specific-field",
            eligibility={"fields_of_study": ["engineering"], "demographics": []},
        )
        open_field = make_scholarship(
            id="open-field",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        specific_result = match_one(student, specific)
        open_result = match_one(student, open_field)

        assert specific_result is not None
        assert open_result is not None
        assert specific_result.score_breakdown.field_of_study == 40.0
        assert open_result.score_breakdown.field_of_study == 10.0
        assert specific_result.score > open_result.score

    def test_specific_field_ranks_above_open_with_demographic(self):
        student = make_student(
            intended_majors=["science"],
            demographic_tags=["african_american"],
        )
        field_specific = make_scholarship(
            id="science-scholarship",
            name="Science Scholarship",
            eligibility={"fields_of_study": ["science"], "demographics": []},
        )
        open_with_demo = make_scholarship(
            id="open-demo-scholarship",
            name="Open Demo Scholarship",
            eligibility={"fields_of_study": [], "demographics": ["african_american"]},
        )
        results = match_scholarships(
            student,
            [open_with_demo, field_specific],
            today=FIXED_TODAY,
        )

        assert results[0].scholarship_id == "science-scholarship"
        assert results[0].score > results[1].score

    def test_broad_science_does_not_match_specific_computer_science_requirement(self):
        student = make_student(intended_majors=["science"])
        scholarship = make_scholarship(
            id="cs-specific",
            eligibility={"fields_of_study": ["computer_science"], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        # "science" is not a recognized child of the "computer_science" requirement,
        # so it never earns an exact/broad-parent match -- but the two fields are
        # adjacent in FIELD_ADJACENCY, so this now earns related-field partial credit
        # instead of the zero it would score without that adjacency.
        assert result.score_breakdown.field_of_study == pytest.approx(20.0)
        assert "Field of study overlap: computer_science" not in result.match_reasons
        assert "Related field: computer_science (your science is adjacent)" in result.match_reasons

    def test_broad_scholarship_field_can_match_specific_student_field(self):
        student = make_student(intended_majors=["computer_science"])
        scholarship = make_scholarship(
            id="science-broad",
            eligibility={"fields_of_study": ["science"], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.field_of_study == pytest.approx(40.0)
        assert "Field of study overlap: science" in result.match_reasons

    def test_related_field_scores_partial_credit(self):
        student = make_student(intended_majors=["computer_science"])
        scholarship = make_scholarship(
            id="related-field",
            eligibility={"fields_of_study": ["engineering"], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.field_of_study == 20.0
        assert any(
            reason.startswith("Related field: engineering") for reason in result.match_reasons
        )

    def test_related_field_does_not_set_field_mismatch_caveat(self):
        student = make_student(
            intended_majors=["computer_science"],
            demographic_tags=["african_american"],
        )
        scholarship = make_scholarship(
            id="related-field-strong",
            eligibility={
                "fields_of_study": ["engineering"],
                "demographics": ["african_american"],
            },
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert (
            "May not match this scholarship's field of study, check eligibility"
            not in result.match_reasons
        )
        assert result.match_tier == "strong"

    def test_exact_match_still_beats_related(self):
        student = make_student(intended_majors=["engineering"])
        scholarship = make_scholarship(
            id="exact-field",
            eligibility={"fields_of_study": ["engineering"], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.field_of_study == 40.0

    def test_no_overlap_still_zero(self):
        student = make_student(intended_majors=["music"])
        scholarship = make_scholarship(
            id="no-overlap",
            eligibility={"fields_of_study": ["law"], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.field_of_study == 0.0
        assert (
            "May not match this scholarship's field of study, check eligibility"
            in result.match_reasons
        )


class TestGradeLevelMatching:
    def test_specific_high_school_grade_matches_broad_high_school_award(self):
        student = make_student(grade_level="high_school_senior")
        scholarship = make_scholarship(
            id="broad-high-school",
            eligibility={"grade_levels": ["high_school"]},
        )

        result = match_one(student, scholarship)

        assert result is not None
        assert "Grade level matches (high_school_senior)" in result.match_reasons

    def test_specific_college_grade_matches_broad_undergraduate_award(self):
        student = make_student(grade_level="college_junior")
        scholarship = make_scholarship(
            id="broad-undergrad",
            eligibility={"grade_levels": ["college_undergraduate"]},
        )

        result = match_one(student, scholarship)

        assert result is not None
        assert "Grade level matches (college_junior)" in result.match_reasons

    def test_broad_legacy_high_school_student_does_not_match_senior_only_award(self):
        student = make_student(grade_level="high_school")
        scholarship = make_scholarship(
            id="senior-only",
            eligibility={"grade_levels": ["high_school_senior"]},
        )

        assert match_one(student, scholarship) is None

    def test_broad_legacy_undergraduate_student_does_not_match_junior_only_award(self):
        student = make_student(grade_level="college_undergraduate")
        scholarship = make_scholarship(
            id="junior-only",
            eligibility={"grade_levels": ["college_junior"]},
        )

        assert match_one(student, scholarship) is None


class TestTieBreaking:
    def test_equal_scores_prefer_confirmed_deadline(self):
        student = make_student()
        with_deadline = make_scholarship(
            id="with-deadline",
            name="Zulu Scholarship",
            deadline="2026-09-30",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        verify_deadline = make_scholarship(
            id="verify-deadline",
            name="Alpha Scholarship",
            deadline="VERIFY",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        results = match_scholarships(
            student,
            [verify_deadline, with_deadline],
            today=FIXED_TODAY,
        )

        assert results[0].scholarship_id == "with-deadline"

    def test_equal_scores_and_deadlines_sort_alphabetically(self):
        student = make_student()
        scholarship_z = make_scholarship(
            id="z-scholarship",
            name="Zulu Scholarship",
            deadline="VERIFY",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        scholarship_a = make_scholarship(
            id="a-scholarship",
            name="Alpha Scholarship",
            deadline="VERIFY",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        results = match_scholarships(
            student,
            [scholarship_z, scholarship_a],
            today=FIXED_TODAY,
        )

        assert results[0].scholarship_name == "Alpha Scholarship"
        assert results[1].scholarship_name == "Zulu Scholarship"


class TestMatchTier:
    def test_strong_tier_for_high_scores(self):
        student = make_student()
        scholarship = make_scholarship(
            eligibility={"fields_of_study": ["engineering"], "demographics": ["african_american"]},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.match_tier == "strong"

    def test_possible_tier_for_low_scores(self):
        student = make_student()
        scholarship = make_scholarship(
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.match_tier == "possible"

    def test_field_mismatch_caps_an_otherwise_strong_match_at_possible(self):
        student = make_student(
            intended_majors=["literature"],
            activities=["robotics", "debate"],
            financial_need_level="high",
        )
        scholarship = make_scholarship(
            description="A need-based award for financial need, robotics, and debate.",
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score == pytest.approx(45.0)
        assert result.match_tier == "possible"
        assert (
            "May not match this scholarship's field of study, check eligibility"
            in result.match_reasons
        )

    def test_special_requirement_caps_strong_match_and_flags_manual_check(self):
        student = make_student()
        scholarship = make_scholarship(
            eligibility={
                "fields_of_study": ["engineering"],
                "demographics": ["african_american"],
                "special_requirements": [
                    {
                        "kind": "competition_or_finalist",
                        "label": "ISEF finalist only",
                        "details": "Must already be a Regeneron ISEF finalist.",
                    }
                ],
            },
        )

        result = match_one(student, scholarship)

        assert result is not None
        assert result.score == pytest.approx(65.0)
        assert result.match_tier == "possible"
        assert result.requires_special_check is True
        assert result.special_requirements[0].label == "ISEF finalist only"
        assert any("Special eligibility to check" in reason for reason in result.match_reasons)


class TestTargetSchoolMatching:
    def test_target_school_alias_adds_points_and_reason(self):
        student = make_student(target_schools=["UT Austin"])
        scholarship = make_scholarship(
            eligibility={
                "eligible_schools": [
                    {
                        "name": "The University of Texas at Austin",
                        "aliases": ["UT Austin"],
                    }
                ]
            }
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.target_school == pytest.approx(15.0)
        assert "Target school match: The University of Texas at Austin" in result.match_reasons

    def test_school_mismatch_caps_an_otherwise_strong_match_at_possible(self):
        student = make_student(target_schools=["Rice University"])
        scholarship = make_scholarship(
            eligibility={
                "eligible_schools": [
                    {"name": "The University of Texas at Austin", "aliases": ["UT Austin"]}
                ]
            }
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score == pytest.approx(65.0)
        assert result.match_tier == "possible"
        assert "May only be available at another school, check eligibility" in result.match_reasons

    def test_empty_target_schools_do_not_trigger_school_mismatch(self):
        student = make_student()
        scholarship = make_scholarship(
            eligibility={
                "eligible_schools": [
                    {"name": "The University of Texas at Austin", "aliases": ["UT Austin"]}
                ]
            }
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.target_school == pytest.approx(0.0)
        assert result.match_tier == "strong"
        assert not any("another school" in reason for reason in result.match_reasons)

    def test_verification_metadata_flows_to_match_result(self):
        scholarship = make_scholarship(
            verification={
                "source_url": "https://example.org/official-source",
                "last_verified_at": "2026-06-21",
            }
        )
        result = match_one(make_student(), scholarship)

        assert result is not None
        assert result.verification_source_url == "https://example.org/official-source"
        assert result.last_verified_at == date(2026, 6, 21)

    def test_eligible_schools_are_carried_to_result(self):
        scholarship = make_scholarship(
            eligibility={
                "eligible_schools": [
                    {"name": "The University of Texas at Austin", "aliases": ["UT Austin"]}
                ]
            }
        )
        result = match_one(make_student(target_schools=[]), scholarship)

        assert result is not None
        assert result.eligible_schools == ["The University of Texas at Austin"]

    def test_non_school_specific_award_has_empty_eligible_schools(self):
        result = match_one(make_student(), make_scholarship())

        assert result is not None
        assert result.eligible_schools == []


class TestClosingSoon:
    def test_deadline_within_30_days_sets_closing_soon(self):
        student = make_student()
        scholarship = make_scholarship(deadline="2026-07-01")
        result = match_one(student, scholarship)

        assert result is not None
        assert result.closing_soon is True
        assert "Closing soon (within 30 days)" in result.match_reasons

    def test_deadline_beyond_30_days_does_not_set_closing_soon(self):
        student = make_student()
        scholarship = make_scholarship(deadline="2026-09-30")
        result = match_one(student, scholarship)

        assert result is not None
        assert result.closing_soon is False

    def test_deadline_does_not_affect_match_score(self):
        student = make_student()
        near_deadline = make_scholarship(
            id="near-deadline",
            deadline="2026-07-01",
            eligibility={"fields_of_study": ["engineering"]},
        )
        far_deadline = make_scholarship(
            id="far-deadline",
            deadline="2026-12-31",
            eligibility={"fields_of_study": ["engineering"]},
        )
        near_result = match_one(student, near_deadline)
        far_result = match_one(student, far_deadline)

        assert near_result is not None
        assert far_result is not None
        assert near_result.score == far_result.score


class TestGpaExclusion:
    def test_student_below_numeric_min_gpa_is_excluded(self):
        student = make_student(gpa=3.0)
        scholarship = make_scholarship(eligibility={"min_gpa": 3.5})
        results = match_scholarships(student, [scholarship], today=FIXED_TODAY)
        assert results == []


class TestDeadlineExclusion:
    def test_past_iso_deadline_excludes_scholarship(self):
        student = make_student()
        scholarship = make_scholarship(deadline="2020-01-01")
        results = match_scholarships(student, [scholarship], today=FIXED_TODAY)
        assert results == []


class TestPartialMatch:
    def test_partial_overlap_returns_lower_score(self):
        student = make_student(
            intended_majors=["literature"],
            demographic_tags=["african_american"],
        )
        scholarship = make_scholarship()
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.field_of_study == 0.0
        assert result.score_breakdown.demographics == pytest.approx(25.0)
        assert "No field of study overlap" in result.match_reasons
        assert "Demographic match: african_american" in result.match_reasons


class TestActivitiesScoring:
    def test_activity_keyword_in_description_adds_points(self):
        student = make_student(activities=["robotics club"])
        scholarship = make_scholarship(
            description="Award for students passionate about robotics and engineering.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(5.0)
        assert any("robotics" in reason for reason in result.match_reasons)

    def test_activities_bonus_is_capped(self):
        student = make_student(activities=["robotics", "debate", "chess"])
        scholarship = make_scholarship(
            description="We reward excellence in robotics, debate, and chess.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(10.0)

    def test_no_activity_overlap_scores_zero(self):
        student = make_student(activities=["swimming"])
        scholarship = make_scholarship(
            description="A test scholarship for unit tests.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(0.0)

    def test_structural_words_do_not_match(self):
        # "club" and "team" are stopwords and must not score on their own.
        student = make_student(activities=["chess club", "track team"])
        scholarship = make_scholarship(
            description="Our club and team value dedication.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(0.0)

    def test_short_tokens_do_not_match_substrings(self):
        # "art" is only 3 chars, should not match substring in "participants"
        student = make_student(activities=["art"])
        scholarship = make_scholarship(
            description="Participants in this scholarship may create art.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(0.0)

    def test_word_boundary_matching(self):
        # "debate" matches "debate" in "debate championship", not as substring
        student = make_student(activities=["debate team"])
        scholarship = make_scholarship(
            description="Award for winners of the national debate championship.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(5.0)

    def test_digit_tokens_do_not_earn_activity_credit(self):
        # "2026" is a pure-digit token >=4 chars; it must not survive the
        # tokenizer's length filter and score on an incidental year overlap.
        # "treasurer" is alpha and >=4 chars but absent from the description,
        # so it legitimately scores nothing here too.
        student = make_student(activities=["Class of 2026 treasurer"])
        scholarship = make_scholarship(
            description="Open to students entering college in 2026.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(0.0)

    def test_synonym_fold(self):
        # "robot" should match to "robotics" via synonym folding
        student = make_student(activities=["robotics club"])
        scholarship = make_scholarship(
            description="Award for students passionate about building a robot.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(5.0)

    def test_synonym_group_counts_once(self):
        # "robotics" and "robot" in the same description are one conceptual
        # activity: the synonym group must collapse to a single match.
        student = make_student(activities=["robotics"])
        scholarship = make_scholarship(
            description="Our robotics program lets you build a robot.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(5.0)

    def test_cap_still_enforced(self):
        # 5 matching activities should cap at 10.0
        student = make_student(
            activities=["robotics", "debate", "chess", "music", "writing"]
        )
        scholarship = make_scholarship(
            description="Recognize excellence in robotics, debate, chess, musician skills, and writer talents.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.activities == pytest.approx(10.0)


class TestFinancialNeedScoring:
    def test_need_based_description_rewards_high_need(self):
        student = make_student(financial_need_level="high")
        scholarship = make_scholarship(
            description="A need-based scholarship for students with financial need.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.financial_need == pytest.approx(10.0)
        assert "Need-based award matches your high financial need" in result.match_reasons

    def test_need_based_medium_need_gets_partial(self):
        student = make_student(financial_need_level="medium")
        scholarship = make_scholarship(
            description="A need based award for low-income students.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.financial_need == pytest.approx(5.0)

    def test_low_need_student_gets_no_need_points(self):
        student = make_student(financial_need_level="low")
        scholarship = make_scholarship(
            description="A need-based scholarship for students with financial need.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.financial_need == pytest.approx(0.0)

    def test_non_need_based_scholarship_scores_zero(self):
        student = make_student(financial_need_level="high")
        scholarship = make_scholarship(
            description="A merit scholarship recognizing academic achievement.",
            eligibility={"fields_of_study": [], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.financial_need == pytest.approx(0.0)


class TestVerifyPlaceholders:
    def test_verify_min_gpa_does_not_exclude(self):
        student = make_student(gpa=2.0)
        scholarship = make_scholarship(eligibility={"min_gpa": "VERIFY"})
        result = match_one(student, scholarship)

        assert result is not None
        assert "GPA requirement not yet verified" in result.match_reasons

    def test_null_min_gpa_does_not_exclude(self):
        student = make_student(gpa=2.0)
        scholarship = make_scholarship(eligibility={"min_gpa": None})
        result = match_one(student, scholarship)

        assert result is not None
        assert "GPA requirement not yet verified" in result.match_reasons

    def test_any_citizenship_requirement_does_not_exclude(self):
        student = make_student(citizenship="international")
        scholarship = make_scholarship(eligibility={"citizenship_requirement": "any"})
        result = match_one(student, scholarship)

        assert result is not None
        assert "No citizenship restriction verified" in result.match_reasons

    def test_verify_deadline_does_not_exclude(self):
        student = make_student()
        scholarship = make_scholarship(deadline="VERIFY")
        result = match_one(student, scholarship)

        assert result is not None
        assert result.closing_soon is False
        assert "Deadline not yet verified" in result.match_reasons

    def test_verify_deadline_with_extra_text_does_not_exclude(self):
        student = make_student()
        scholarship = make_scholarship(deadline="VERIFY (PSAT/NMSQT qualifying year)")
        result = match_one(student, scholarship)

        assert result is not None
        assert "Deadline not yet verified" in result.match_reasons

    def test_rolling_deadline_does_not_exclude(self):
        student = make_student()
        scholarship = make_scholarship(deadline="rolling")
        result = match_one(student, scholarship)

        assert result is not None
        assert result.closing_soon is False
        assert "Rolling deadline (no fixed cutoff)" in result.match_reasons


class TestUnverifiedScholarshipsStillMatch:
    def test_unverified_scholarship_is_included_in_results(self):
        student = make_student()
        scholarship = make_scholarship(verified=False)
        result = match_one(student, scholarship)

        assert result is not None
        assert result.verified is False

    def test_verified_flag_is_carried_in_result(self):
        student = make_student()
        scholarship = make_scholarship(verified=True)
        result = match_one(student, scholarship)

        assert result is not None
        assert result.verified is True


class TestEstimatedDeadline:
    def test_estimate_flows_through_and_never_excludes(self):
        student = make_student()
        # Deadline unknown, but an estimate that is already in the past: the
        # scholarship must NOT be excluded, and the estimate is carried through.
        scholarship = make_scholarship(deadline="VERIFY", estimated_deadline="2000-01-01")
        result = match_one(student, scholarship)

        assert result is not None
        assert result.estimated_deadline == "2000-01-01"

    def test_confirmed_past_deadline_still_excludes_despite_estimate(self):
        student = make_student()
        scholarship = make_scholarship(deadline="2020-01-01", estimated_deadline="2027-01-01")
        results = match_scholarships(student, [scholarship], today=FIXED_TODAY)

        assert results == []

    def test_estimate_does_not_set_closing_soon(self):
        student = make_student()
        # An estimate within 30 days must not raise a closing-soon badge.
        soon = (FIXED_TODAY).isoformat()
        scholarship = make_scholarship(deadline="VERIFY", estimated_deadline=soon)
        result = match_one(student, scholarship)

        assert result is not None
        assert result.closing_soon is False


class TestExplanationLines:
    def test_fit_context_line_lists_nonzero_components(self):
        student = make_student(
            intended_majors=["engineering"],
            demographic_tags=[],
            financial_need_level="medium",
            target_schools=[],
        )
        scholarship = make_scholarship(
            eligibility={"fields_of_study": ["engineering"], "demographics": []},
            description="A need based award for low-income students.",
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert "Fit score 45: field of study 40, financial need 5" in result.match_reasons

    def test_missing_hints_capped_at_two_and_ordered(self):
        student = make_student(
            intended_majors=["literature"],
            demographic_tags=[],
            target_schools=[],
        )
        scholarship = make_scholarship(
            eligibility={
                "fields_of_study": ["engineering"],
                "demographics": ["african_american"],
                "eligible_schools": [
                    {
                        "name": "The University of Texas at Austin",
                        "aliases": ["UT Austin"],
                    }
                ],
            },
        )
        result = match_one(student, scholarship)

        assert result is not None
        reasons = result.match_reasons
        assert "No field overlap; field fit adds up to 40 points" in reasons
        assert "No demographic overlap; this award adds up to 25 points for it" in reasons
        assert not any(reason.startswith("No target school match") for reason in reasons)

    def test_partial_component_generates_no_hint(self):
        student = make_student(intended_majors=["computer_science"])
        scholarship = make_scholarship(
            eligibility={"fields_of_study": ["engineering"], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.field_of_study == 20.0
        assert not any(
            reason.startswith("No field overlap") for reason in result.match_reasons
        )

    def test_zero_total_omits_fit_context(self):
        student = make_student(
            intended_majors=["music"],
            demographic_tags=[],
            financial_need_level="low",
            activities=[],
            target_schools=[],
        )
        scholarship = make_scholarship(
            eligibility={"fields_of_study": ["law"], "demographics": []},
        )
        result = match_one(student, scholarship)

        assert result is not None
        assert result.score_breakdown.total == 0.0
        assert not any(reason.startswith("Fit score") for reason in result.match_reasons)


class TestDataLoader:
    def test_loader_parses_scholarships_array(self):
        from app.data.loader import load_scholarships

        scholarships = load_scholarships()
        assert len(scholarships) >= 15
        assert all(scholarship.id for scholarship in scholarships)


class TestPreviewMatching:
    """The three-question preview: residency gates flagged, never applied."""

    def _preview_payload(self, **overrides):
        payload = {
            "gpa": 3.7,
            "grade_level": "high_school_junior",
            "intended_majors": ["science"],
        }
        payload.update(overrides)
        return payload

    def test_preview_endpoint_returns_top_three_and_total(self):
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            response = client.post("/match/preview", json=self._preview_payload())
            assert response.status_code == 200
            body = response.json()
            assert body["total_matches"] >= len(body["results"])
            assert 1 <= len(body["results"]) <= 3
            scores = [r["score"] for r in body["results"]]
            assert scores == sorted(scores, reverse=True)

    def test_preview_does_not_gate_on_citizenship_or_state(self):
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            preview = client.post("/match/preview", json=self._preview_payload()).json()
            # An international student in a random state sees fewer or equal
            # full matches; preview must be the superset (no residency gates).
            full = client.post(
                "/match",
                json={
                    **self._preview_payload(),
                    "citizenship": "international",
                    "state": "WY",
                },
            ).json()
            assert preview["total_matches"] >= len(full["matches"])

    def test_preview_flags_residency_requirements_in_reasons(self):
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            body = client.post("/match/preview", json=self._preview_payload()).json()
            all_reasons = [r for item in body["results"] for r in item["match_reasons"]]
            # No preview result may claim a met citizenship/state requirement.
            assert not any(reason.startswith("Meets citizenship") for reason in all_reasons)
            assert not any(reason.startswith("State matches") for reason in all_reasons)

    def test_preview_validates_vocabulary(self):
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            bad = client.post(
                "/match/preview",
                json=self._preview_payload(grade_level="third_grade"),
            )
            assert bad.status_code == 422

    def test_preview_shape_is_unchanged(self):
        """Preview keeps its {total_matches, results} shape; no near_misses,
        no {matches, near_misses} wrapper -- the near-miss feature is /match only."""
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            body = client.post("/match/preview", json=self._preview_payload()).json()
            assert set(body.keys()) == {"total_matches", "results"}
            assert "near_misses" not in body
            assert "matches" not in body


class TestNearMiss:
    def test_gpa_near_miss_within_window(self):
        student = make_student(gpa=3.6)
        scholarship = make_scholarship(eligibility={"min_gpa": 3.8})

        nm = near_miss_scholarships(student, [scholarship], FIXED_TODAY)

        assert len(nm) == 1
        assert nm[0].near_miss_reason == "Needs GPA 3.8; your profile says 3.6"
        assert nm[0].scholarship_id == "test-scholarship"

    def test_gpa_near_miss_at_float_imprecise_boundary(self):
        # 3.7 - 3.4 == 0.30000000000000027 in binary float arithmetic; the
        # spec says a gap of exactly 0.3 qualifies, so this must round-trip.
        student = make_student(gpa=3.4)
        scholarship = make_scholarship(eligibility={"min_gpa": 3.7})

        nm = near_miss_scholarships(student, [scholarship], FIXED_TODAY)

        assert len(nm) == 1
        assert nm[0].near_miss_reason == "Needs GPA 3.7; your profile says 3.4"

    def test_gpa_gap_above_window_excluded(self):
        student = make_student(gpa=3.49)
        scholarship = make_scholarship(eligibility={"min_gpa": 3.8})

        nm = near_miss_scholarships(student, [scholarship], FIXED_TODAY)

        assert nm == []

    def test_future_grade_near_miss(self):
        student = make_student(grade_level="high_school_junior")
        scholarship = make_scholarship(eligibility={"grade_levels": ["high_school_senior"]})

        nm = near_miss_scholarships(student, [scholarship], FIXED_TODAY)

        assert len(nm) == 1
        assert nm[0].near_miss_reason == "Eligible when you are a high school senior"

    def test_two_failed_gates_excluded(self):
        # GPA gap 0.2 (qualifying on its own) AND wrong state -> not a near miss.
        student = make_student(gpa=3.8, state="CA")
        scholarship = make_scholarship(eligibility={"min_gpa": 4.0, "states": ["NY"]})

        nm = near_miss_scholarships(student, [scholarship], FIXED_TODAY)

        assert nm == []

    def test_past_deadline_excluded_even_with_gap(self):
        student = make_student(gpa=3.8)
        scholarship = make_scholarship(eligibility={"min_gpa": 4.0}, deadline="2020-01-01")

        nm = near_miss_scholarships(student, [scholarship], FIXED_TODAY)

        assert nm == []

    def test_near_miss_absent_from_matches(self):
        student = make_student(gpa=3.8)
        scholarship = make_scholarship(eligibility={"min_gpa": 4.0})

        nm = near_miss_scholarships(student, [scholarship], FIXED_TODAY)
        matches = match_scholarships(student, [scholarship], today=FIXED_TODAY)

        assert len(nm) == 1
        assert matches == []

    def test_response_wrapper_shape(self):
        student = make_student(gpa=3.8)
        passing = make_scholarship(id="passing-scholarship")
        near_miss = make_scholarship(id="near-miss-scholarship", eligibility={"min_gpa": 4.0})

        resp = match_scholarships_response(student, [passing, near_miss], today=FIXED_TODAY)

        assert resp.matches
        assert isinstance(resp.near_misses, list)
        assert len(resp.near_misses) == 1
        assert resp.near_misses[0].scholarship_id == "near-miss-scholarship"
        assert all(match.scholarship_id != "near-miss-scholarship" for match in resp.matches)

    def test_cap_and_ordering(self):
        student = make_student(gpa=3.8)
        scholarships: list[Scholarship] = []

        real_dates = [
            "2026-08-01",
            "2026-07-01",
            "2026-09-01",
            "2026-06-20",
            "2026-10-01",
            "2026-06-15",
        ]
        for i, deadline in enumerate(real_dates):
            scholarships.append(
                make_scholarship(
                    id=f"real-{i}",
                    name=f"Real {i}",
                    deadline=deadline,
                    eligibility={"min_gpa": 4.0},
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
            scholarships.append(
                make_scholarship(
                    id=f"estimated-{i}",
                    name=f"Estimated {i}",
                    deadline="VERIFY",
                    estimated_deadline=estimate,
                    eligibility={"min_gpa": 4.0},
                )
            )

        for name in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF"):
            scholarships.append(
                make_scholarship(
                    id=f"none-{name}",
                    name=name,
                    deadline="VERIFY",
                    eligibility={"min_gpa": 4.0},
                )
            )

        assert len(scholarships) == 17

        nm = near_miss_scholarships(student, scholarships, FIXED_TODAY)

        assert len(nm) == 15
        expected_order = [
            "real-5",  # 2026-06-15
            "real-3",  # 2026-06-20
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
        assert [entry.scholarship_id for entry in nm] == expected_order
