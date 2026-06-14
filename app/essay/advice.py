"""Server-side Anthropic integration for scholarship essay guidance."""

from __future__ import annotations

import os
from typing import Any

from anthropic import (
    Anthropic,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from app.models.scholarship import Scholarship
from app.models.student import StudentProfile

ESSAY_MODEL = "claude-sonnet-4-6"
ESSAY_FALLBACK_MODELS = (
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
)
ESSAY_MAX_TOKENS = 1024


class EssayAdviceError(Exception):
    """Raised when essay advice cannot be produced; carries a safe user message."""

    def __init__(self, user_message: str, status_code: int = 503) -> None:
        self.user_message = user_message
        self.status_code = status_code
        super().__init__(user_message)


SYSTEM_PROMPT = """You are a practical scholarship essay coach for U.S. students.
You write concise, specific guidance tied to the student's real profile and one scholarship.
Be honest and direct. Do not flatter or pad.
Do NOT use em dashes anywhere in your output. Use commas, periods, or parentheses instead.
If the student provided very little information, say what additional detail would help rather than inventing facts about them."""


def _format_student_context(student: StudentProfile) -> str:
    activities = ", ".join(student.activities) if student.activities else "(none provided)"
    majors = ", ".join(student.intended_majors) if student.intended_majors else "(none provided)"
    demographics = (
        ", ".join(student.demographic_tags) if student.demographic_tags else "(none provided)"
    )
    schools = (
        ", ".join(student.target_schools)
        if student.target_schools
        else "(none provided)"
    )
    return f"""Student profile:
- GPA: {student.gpa}
- Grade level: {student.grade_level}
- Citizenship: {student.citizenship}
- State: {student.state}
- Financial need level: {student.financial_need_level}
- Intended fields of study: {majors}
- Demographic tags: {demographics}
- Activities: {activities}
- Target schools: {schools}"""


def _format_scholarship_context(scholarship: Scholarship) -> str:
    eligibility = scholarship.eligibility
    fields = (
        ", ".join(eligibility.fields_of_study)
        if eligibility.fields_of_study
        else "open to all fields"
    )
    demographics = (
        ", ".join(eligibility.demographics)
        if eligibility.demographics
        else "no specific demographic requirements"
    )
    return f"""Scholarship:
- Name: {scholarship.name}
- Sponsor: {scholarship.sponsor}
- Description: {scholarship.description}
- Fields of study: {fields}
- Demographics emphasized: {demographics}
- Essay required: {eligibility.essay_required}"""


def build_essay_prompt(student: StudentProfile, scholarship: Scholarship) -> str:
    return f"""{_format_student_context(student)}

{_format_scholarship_context(scholarship)}

Using ONLY the student's real inputs above, write tailored essay guidance with these sections:

1. Essay angle suggestions: Provide two or three specific angles that draw on the student's actual activities, fields of study, grade level, and demographic context. Reference their real inputs. Do not use hypotheticals like "if you volunteered" when they already listed activities.

2. What this sponsor likely values: A short note on what the sponsor appears to value based on its description and eligibility, and how this student can speak to that with their real background.

3. Common mistake to avoid: One mistake applicants often make for this type of scholarship essay.

Keep the total response concise and practical. Use plain section headings."""


def _get_api_key() -> str | None:
    raw = os.environ.get("ANTHROPIC_API_KEY")
    if not raw:
        return None
    cleaned = raw.strip().strip('"').strip("'")
    return cleaned or None


def _map_api_error(exc: Exception) -> EssayAdviceError:
    if isinstance(exc, AuthenticationError):
        return EssayAdviceError(
            "Essay advice could not connect to the AI service. "
            "Check that ANTHROPIC_API_KEY in .env is valid and active.",
            status_code=503,
        )
    if isinstance(exc, PermissionDeniedError):
        return EssayAdviceError(
            "Essay advice is not available for this API key. "
            "Confirm your Anthropic account has API access enabled.",
            status_code=503,
        )
    if isinstance(exc, NotFoundError):
        return EssayAdviceError(
            "Essay advice could not reach the configured AI model. "
            "The server may need a model update. Try again later.",
            status_code=503,
        )
    if isinstance(exc, RateLimitError):
        return EssayAdviceError(
            "Too many essay advice requests. Wait a minute and try again.",
            status_code=429,
        )
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return EssayAdviceError(
            "Could not reach the AI service. Check your network and try again.",
            status_code=503,
        )
    return EssayAdviceError(
        "Essay advice could not be generated right now. Try again in a few minutes.",
        status_code=503,
    )


def _call_model(client: Anthropic, user_prompt: str, model: str) -> Any:
    return client.messages.create(
        model=model,
        max_tokens=ESSAY_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )


def generate_essay_advice(
    student: StudentProfile,
    scholarship: Scholarship,
    *,
    client: Anthropic | None = None,
) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise EssayAdviceError(
            "Essay advice is not available right now. The server needs an API key configured.",
            status_code=503,
        )

    anthropic_client = client or Anthropic(api_key=api_key)
    user_prompt = build_essay_prompt(student, scholarship)
    models_to_try = (ESSAY_MODEL, *ESSAY_FALLBACK_MODELS)

    response: Any | None = None
    last_error: Exception | None = None
    for model in models_to_try:
        try:
            response = _call_model(anthropic_client, user_prompt, model)
            break
        except NotFoundError as exc:
            last_error = exc
            continue
        except Exception as exc:
            raise _map_api_error(exc) from None

    if response is None:
        raise _map_api_error(last_error or Exception("No model available"))

    text_blocks = [
        block.text
        for block in response.content
        if hasattr(block, "text") and block.text
    ]
    if not text_blocks:
        raise EssayAdviceError(
            "Essay advice came back empty. Try again in a few minutes.",
            status_code=502,
        )

    return "\n".join(text_blocks).strip()
