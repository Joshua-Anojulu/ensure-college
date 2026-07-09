"""Request and response schemas for accounts and saved data."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.competition import Competition
from app.models.program import SummerProgram
from app.models.scholarship import Scholarship
from app.models.student import StudentProfile

# bcrypt only uses the first 72 bytes, so there is no value in allowing more.
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 72


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class DeleteAccountRequest(BaseModel):
    """Password confirms deletion for password accounts; Google-only accounts
    have no password, so it is optional and their session alone authorizes."""

    password: Optional[str] = Field(default=None, min_length=1, max_length=PASSWORD_MAX_LENGTH)


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    has_password: bool = True
    google_connected: bool = False
    reminders_enabled: bool = True


class ReminderPrefUpdate(BaseModel):
    enabled: bool


class ProfileResponse(BaseModel):
    """A saved profile, or null when the user has not saved one yet."""

    profile: StudentProfile | None = None
    updated_at: datetime | None = None


SavedStatus = Literal["interested", "drafting", "submitted", "awarded", "rejected"]


class SavedScholarshipItem(BaseModel):
    scholarship_id: str
    saved_at: datetime
    status: SavedStatus = "interested"
    notes: str = ""
    completed_requirement_ids: list[str] = Field(default_factory=list)
    scholarship: Scholarship | None = Field(
        default=None,
        description="Full scholarship record, or null if it left the dataset.",
    )


class SavedProgramItem(BaseModel):
    program_id: str
    saved_at: datetime
    status: SavedStatus = "interested"
    notes: str = ""
    completed_requirement_ids: list[str] = Field(default_factory=list)
    program: SummerProgram | None = Field(
        default=None,
        description="Full summer-program record, or null if it left the dataset.",
    )


class SavedCompetitionItem(BaseModel):
    competition_id: str
    saved_at: datetime
    status: SavedStatus = "interested"
    notes: str = ""
    completed_requirement_ids: list[str] = Field(default_factory=list)
    competition: Competition | None = Field(
        default=None,
        description="Full competition record, or null if it left the dataset.",
    )


class SavedUpdateRequest(BaseModel):
    """Patch the tracker fields on a saved scholarship. Omitted fields are unchanged."""

    status: Optional[SavedStatus] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    completed_requirement_ids: list[str] | None = Field(default=None, max_length=50)

    @field_validator("completed_requirement_ids")
    @classmethod
    def validate_requirement_ids(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        normalized: list[str] = []
        for value in values:
            requirement_id = value.strip()
            if (
                not requirement_id
                or len(requirement_id) > 80
                or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for char in requirement_id)
            ):
                raise ValueError("completed_requirement_ids must contain stable requirement ids")
            if requirement_id not in normalized:
                normalized.append(requirement_id)
        return normalized


class SavedListResponse(BaseModel):
    saved: list[SavedScholarshipItem]
    programs: list[SavedProgramItem] = Field(default_factory=list)
    competitions: list[SavedCompetitionItem] = Field(default_factory=list)
