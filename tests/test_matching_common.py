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
