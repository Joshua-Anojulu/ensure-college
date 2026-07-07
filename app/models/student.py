from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.vocabulary import (
    CITIZENSHIP_VALUES,
    DEMOGRAPHIC_TAG_VALUES,
    FIELD_OF_STUDY_VALUES,
    GRADE_LEVEL_VALUES,
    STATE_CODE_VALUES,
)


def _check_grade_level(value: str) -> str:
    if value not in GRADE_LEVEL_VALUES:
        raise ValueError(
            f"Unknown grade_level '{value}'. Allowed values: {sorted(GRADE_LEVEL_VALUES)}"
        )
    return value


def _check_intended_majors(values: list[str]) -> list[str]:
    unknown = [field for field in values if field not in FIELD_OF_STUDY_VALUES]
    if unknown:
        raise ValueError(
            f"Unknown intended_majors: {unknown}. "
            f"Allowed values: {sorted(FIELD_OF_STUDY_VALUES)}"
        )
    return values


class StudentProfile(BaseModel):
    """Student input collected from the profile form."""

    gpa: float = Field(ge=0.0, le=4.0)
    grade_level: str = Field(
        description="Student class-year tag from GET /vocabulary, or a legacy broad grade tag.",
    )
    intended_majors: list[str] = Field(
        default_factory=list,
        description="Broad field-of-study tags from GET /vocabulary fields_of_study.",
    )
    target_schools: Optional[list[str]] = Field(
        default=None,
        max_length=30,
        description="Optional list of colleges the student is considering.",
    )
    demographic_tags: list[str] = Field(default_factory=list)
    state: str = Field(description="Two-letter US state code from GET /vocabulary.")
    citizenship: str = Field(description="Canonical citizenship tag from GET /vocabulary.")
    financial_need_level: Literal["low", "medium", "high", "unspecified"] = "unspecified"
    activities: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Extracurriculars, leadership roles, athletics, etc.",
    )

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, value: str) -> str:
        return _check_grade_level(value)

    @field_validator("citizenship")
    @classmethod
    def validate_citizenship(cls, value: str) -> str:
        if value not in CITIZENSHIP_VALUES:
            raise ValueError(
                f"Unknown citizenship '{value}'. Allowed values: {sorted(CITIZENSHIP_VALUES)}"
            )
        return value

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in STATE_CODE_VALUES:
            raise ValueError(
                f"Unknown state '{value}'. Allowed values: {sorted(STATE_CODE_VALUES)}"
            )
        return normalized

    @field_validator("demographic_tags")
    @classmethod
    def validate_demographic_tags(cls, values: list[str]) -> list[str]:
        unknown = [tag for tag in values if tag not in DEMOGRAPHIC_TAG_VALUES]
        if unknown:
            raise ValueError(
                f"Unknown demographic_tags: {unknown}. "
                f"Allowed values: {sorted(DEMOGRAPHIC_TAG_VALUES)}"
            )
        return values

    @field_validator("intended_majors")
    @classmethod
    def validate_intended_majors(cls, values: list[str]) -> list[str]:
        return _check_intended_majors(values)

    @field_validator("target_schools", "activities")
    @classmethod
    def cap_free_text_items(cls, values: list[str] | None) -> list[str] | None:
        """Free-text entries are stored per account and scanned by the matcher,
        so each one is trimmed to a sane length instead of rejecting the form."""
        if values is None:
            return None
        return [value.strip()[:200] for value in values if value.strip()]


class PreviewMatchRequest(BaseModel):
    """The three-question quick preview: enough for an honest teaser match.

    Citizenship and state are deliberately absent — the preview matcher skips
    those gates and flags them as to-confirm instead of assuming values.
    """

    gpa: float = Field(ge=0.0, le=4.0)
    grade_level: str
    intended_majors: list[str] = Field(min_length=1, max_length=5)

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, value: str) -> str:
        return _check_grade_level(value)

    @field_validator("intended_majors")
    @classmethod
    def validate_intended_majors(cls, values: list[str]) -> list[str]:
        return _check_intended_majors(values)
