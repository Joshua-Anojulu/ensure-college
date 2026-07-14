from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.scholarship import (
    ApplicationRequirement,
    SpecialRequirement,
    validate_http_url_string,
)


class ScoreBreakdown(BaseModel):
    """Points contributed by each scored factor (gates are not included)."""

    field_of_study: float = 0.0
    demographics: float = 0.0
    target_school: float = 0.0
    activities: float = 0.0
    financial_need: float = 0.0
    total: float = 0.0


class MatchResult(BaseModel):
    """A ranked scholarship match with transparent scoring."""

    scholarship_id: str
    scholarship_name: str
    sponsor: str
    award_amount: str | float
    deadline: str
    estimated_deadline: str | None = None
    url: str
    verified: bool
    verification_source_url: str | None = None
    last_verified_at: date | None = None
    essay_required: bool = Field(
        default=False,
        description="Whether the scholarship requires an essay (used by the no-essay filter).",
    )
    closing_soon: bool = Field(
        default=False,
        description="True when a real parsed deadline falls within 30 days (badge only, not scored).",
    )
    score: float = Field(description="Sum of fit-related score_breakdown components.")
    match_tier: Literal["strong", "possible"] = Field(
        description=(
            "Frontend grouping band: strong for high-confidence fits, possible for "
            "weaker fits or opportunities with extra eligibility checks."
        ),
    )
    match_reasons: list[str]
    score_breakdown: ScoreBreakdown
    eligible_schools: list[str] = Field(
        default_factory=list,
        description="Institution names this award is restricted to; empty if not school-specific.",
    )
    requires_special_check: bool = Field(
        default=False,
        description="True when niche eligibility requirements need manual confirmation.",
    )
    special_requirements: list[SpecialRequirement] = Field(default_factory=list)
    application_requirements: list[ApplicationRequirement] = Field(default_factory=list)

    @field_validator("verification_source_url")
    @classmethod
    def _verification_source_url_is_http(cls, value: str | None) -> str | None:
        return validate_http_url_string(value)


class ScholarshipNearMiss(BaseModel):
    """A scholarship excluded by exactly one qualifying-type gate (GPA gap
    within 0.3, or a future grade level); informational, never a ranked match."""

    scholarship_id: str
    scholarship_name: str
    sponsor: str
    award_amount: str | float
    deadline: str
    estimated_deadline: str | None = None
    url: str
    verified: bool
    near_miss_reason: str


class MatchResponse(BaseModel):
    """Ranked matches plus near-miss scholarships worth flagging to the student."""

    matches: list[MatchResult]
    near_misses: list[ScholarshipNearMiss]


class PreviewMatchResponse(BaseModel):
    """Teaser for the three-question preview: top matches plus the full count."""

    total_matches: int
    results: list[MatchResult] = Field(
        description="Top-scored matches (at most 3), with residency gates flagged, not applied.",
    )
