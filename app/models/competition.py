"""Models for the competitions feature.

A Competition reuses the scholarship building blocks (Eligibility,
ApplicationRequirement, VerificationMetadata) and adds the facts that matter for
a competition: category, recognition/prize, participation format, cost, and run
dates. The same VERIFY discipline applies: an unconfirmed field stays "VERIFY".
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, Field, HttpUrl

from app.models.scholarship import (
    ApplicationRequirement,
    Eligibility,
    SpecialRequirement,
    VerificationMetadata,
)

CompetitionCostCategory = Literal["free", "stipend", "paid", "VERIFY"]
ParticipationFormat = Literal["individual", "team", "either", "VERIFY"]


class Competition(BaseModel):
    """A curated, verified competition (a college-application enhancer)."""

    id: str
    name: str
    host: str = Field(description="Sponsoring/organizing body.")
    category: str = Field(description="Short category label, e.g. 'STEM research'.")
    url: HttpUrl
    cost: str = Field(default="VERIFY", description='Human-readable cost, e.g. "Free to enter".')
    cost_category: CompetitionCostCategory = "VERIFY"
    recognition: str = Field(
        default="VERIFY",
        description='Human-readable prize/recognition, e.g. "Cash prizes; national medal".',
    )
    participation_format: ParticipationFormat = "VERIFY"
    location: str = "VERIFY"
    competition_dates: str = Field(
        default="VERIFY",
        description="When the competition runs, distinct from the registration deadline.",
    )
    deadline: Union[str, Literal["rolling"]] = Field(
        default="VERIFY",
        description='Registration deadline: ISO date (YYYY-MM-DD), "rolling", or "VERIFY".',
    )
    estimated_deadline: str | None = Field(
        default=None,
        description="Approximate ISO deadline from a prior cycle; informational only.",
    )
    eligibility: Eligibility
    description: str
    application_requirements: list[ApplicationRequirement] = Field(default_factory=list)
    verified: bool = False
    verification: VerificationMetadata | None = None


class CompetitionScoreBreakdown(BaseModel):
    """Per-component contributions to a competition's fit score (all additive)."""

    category: float = 0.0
    demographics: float = 0.0
    financial_access: float = 0.0
    total: float = 0.0


class CompetitionMatchResult(BaseModel):
    """A competition scored for one student, with transparent reasons."""

    competition_id: str
    name: str
    host: str
    category: str
    cost: str
    cost_category: CompetitionCostCategory
    recognition: str
    participation_format: ParticipationFormat
    location: str
    competition_dates: str
    deadline: str
    estimated_deadline: str | None
    url: str
    verified: bool
    verification_source_url: str | None
    last_verified_at: date | None
    essay_required: bool
    score: float
    match_tier: str
    match_reasons: list[str]
    score_breakdown: CompetitionScoreBreakdown
    application_requirements: list[ApplicationRequirement] = Field(default_factory=list)
    requires_special_check: bool = False
    special_requirements: list[SpecialRequirement] = Field(default_factory=list)


class CompetitionNearMiss(BaseModel):
    """A competition excluded by exactly one qualifying-type gate (GPA gap
    within 0.3, or a future grade level); informational, never a ranked match."""

    competition_id: str
    name: str
    host: str
    recognition: str
    deadline: str
    estimated_deadline: str | None = None
    url: str
    verified: bool
    near_miss_reason: str


class CompetitionMatchResponse(BaseModel):
    """Ranked competition matches plus near-miss competitions worth flagging."""

    matches: list[CompetitionMatchResult]
    near_misses: list[CompetitionNearMiss]
