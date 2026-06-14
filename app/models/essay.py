from pydantic import BaseModel, Field

from app.models.student import StudentProfile


class EssayAdviceRequest(BaseModel):
    """Request body for tailored essay guidance."""

    student: StudentProfile
    scholarship_id: str = Field(min_length=1)


class EssayAdviceResponse(BaseModel):
    """Generated essay guidance for one student and scholarship pair."""

    scholarship_id: str
    scholarship_name: str
    advice: str
