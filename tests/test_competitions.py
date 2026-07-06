"""Tests for the competitions feature: model, matcher gates/scoring, dataset, API."""

from app.models.competition import Competition
from app.models.scholarship import Eligibility


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
