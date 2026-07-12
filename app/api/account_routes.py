"""Endpoints for a logged-in user's saved profile and saved scholarships."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import (
    SavedCompetition,
    SavedProgram,
    SavedScholarship,
    User,
    UserProfile,
)
from app.models.auth import (
    ProfileResponse,
    ReminderPrefUpdate,
    SavedCompetitionItem,
    SavedListResponse,
    SavedProgramItem,
    SavedScholarshipItem,
    SavedUpdateRequest,
)
from app.models.competition import Competition
from app.models.program import SummerProgram
from app.models.scholarship import Scholarship
from app.models.student import StudentProfile

router = APIRouter(prefix="/account", tags=["account"])


def _scholarship_index(request: Request) -> dict[str, Scholarship]:
    scholarships: list[Scholarship] = request.app.state.scholarships
    return {s.id: s for s in scholarships}


def _program_index(request: Request) -> dict[str, SummerProgram]:
    programs: list[SummerProgram] = request.app.state.programs
    return {p.id: p for p in programs}


def _competition_index(request: Request) -> dict[str, Competition]:
    competitions: list[Competition] = request.app.state.competitions
    return {c.id: c for c in competitions}


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    record = db.get(UserProfile, user.id)
    if record is None:
        return ProfileResponse(profile=None, updated_at=None)
    try:
        profile = StudentProfile.model_validate(record.data)
    except Exception:
        # A stored profile can predate vocabulary changes; treat it as absent
        # rather than 500 on every profile load (same stance as alerts.py).
        return ProfileResponse(profile=None, updated_at=None)
    return ProfileResponse(
        profile=profile,
        updated_at=record.updated_at,
    )


@router.put("/profile", response_model=ProfileResponse)
def save_profile(
    profile: StudentProfile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    data = profile.model_dump()
    record = db.get(UserProfile, user.id)
    if record is None:
        record = UserProfile(user_id=user.id, data=data)
        db.add(record)
    else:
        record.data = data
    db.commit()
    db.refresh(record)
    return ProfileResponse(
        profile=StudentProfile.model_validate(record.data),
        updated_at=record.updated_at,
    )


@router.get("/saved", response_model=SavedListResponse)
def list_saved(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedListResponse:
    index = _scholarship_index(request)
    program_index = _program_index(request)
    competition_index = _competition_index(request)
    scholarship_rows = (
        db.query(SavedScholarship)
        .filter(SavedScholarship.user_id == user.id)
        .order_by(SavedScholarship.created_at.desc())
        .all()
    )
    program_rows = (
        db.query(SavedProgram)
        .filter(SavedProgram.user_id == user.id)
        .order_by(SavedProgram.created_at.desc())
        .all()
    )
    competition_rows = (
        db.query(SavedCompetition)
        .filter(SavedCompetition.user_id == user.id)
        .order_by(SavedCompetition.created_at.desc())
        .all()
    )
    items = [
        SavedScholarshipItem(
            scholarship_id=row.scholarship_id,
            saved_at=row.created_at,
            status=row.status,
            notes=row.notes,
            completed_requirement_ids=row.completed_requirement_ids,
            scholarship=index.get(row.scholarship_id),
        )
        for row in scholarship_rows
    ]
    program_items = [
        SavedProgramItem(
            program_id=row.program_id,
            saved_at=row.created_at,
            status=row.status,
            notes=row.notes,
            completed_requirement_ids=row.completed_requirement_ids,
            program=program_index.get(row.program_id),
        )
        for row in program_rows
    ]
    competition_items = [
        SavedCompetitionItem(
            competition_id=row.competition_id,
            saved_at=row.created_at,
            status=row.status,
            notes=row.notes,
            completed_requirement_ids=row.completed_requirement_ids,
            competition=competition_index.get(row.competition_id),
        )
        for row in competition_rows
    ]
    return SavedListResponse(saved=items, programs=program_items, competitions=competition_items)


@router.post(
    "/saved/{scholarship_id}",
    response_model=SavedScholarshipItem,
    status_code=status.HTTP_201_CREATED,
)
def save_scholarship(
    scholarship_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedScholarshipItem:
    index = _scholarship_index(request)
    scholarship = index.get(scholarship_id)
    if scholarship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "That scholarship was not found in the current dataset."},
        )

    existing = (
        db.query(SavedScholarship)
        .filter(
            SavedScholarship.user_id == user.id,
            SavedScholarship.scholarship_id == scholarship_id,
        )
        .first()
    )
    if existing is not None:
        return SavedScholarshipItem(
            scholarship_id=existing.scholarship_id,
            saved_at=existing.created_at,
            status=existing.status,
            notes=existing.notes,
            completed_requirement_ids=existing.completed_requirement_ids,
            scholarship=scholarship,
        )

    row = SavedScholarship(user_id=user.id, scholarship_id=scholarship_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return SavedScholarshipItem(
        scholarship_id=row.scholarship_id,
        saved_at=row.created_at,
        status=row.status,
        notes=row.notes,
        completed_requirement_ids=row.completed_requirement_ids,
        scholarship=scholarship,
    )


@router.post(
    "/saved/programs/{program_id}",
    response_model=SavedProgramItem,
    status_code=status.HTTP_201_CREATED,
)
def save_program(
    program_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedProgramItem:
    index = _program_index(request)
    program = index.get(program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "That summer program was not found in the current dataset."},
        )

    existing = (
        db.query(SavedProgram)
        .filter(
            SavedProgram.user_id == user.id,
            SavedProgram.program_id == program_id,
        )
        .first()
    )
    if existing is not None:
        return SavedProgramItem(
            program_id=existing.program_id,
            saved_at=existing.created_at,
            status=existing.status,
            notes=existing.notes,
            completed_requirement_ids=existing.completed_requirement_ids,
            program=program,
        )

    row = SavedProgram(user_id=user.id, program_id=program_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return SavedProgramItem(
        program_id=row.program_id,
        saved_at=row.created_at,
        status=row.status,
        notes=row.notes,
        completed_requirement_ids=row.completed_requirement_ids,
        program=program,
    )


@router.post(
    "/saved/competitions/{competition_id}",
    response_model=SavedCompetitionItem,
    status_code=status.HTTP_201_CREATED,
)
def save_competition(
    competition_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedCompetitionItem:
    index = _competition_index(request)
    competition = index.get(competition_id)
    if competition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "That competition was not found in the current dataset."},
        )

    existing = (
        db.query(SavedCompetition)
        .filter(
            SavedCompetition.user_id == user.id,
            SavedCompetition.competition_id == competition_id,
        )
        .first()
    )
    if existing is not None:
        return SavedCompetitionItem(
            competition_id=existing.competition_id,
            saved_at=existing.created_at,
            status=existing.status,
            notes=existing.notes,
            completed_requirement_ids=existing.completed_requirement_ids,
            competition=competition,
        )

    row = SavedCompetition(user_id=user.id, competition_id=competition_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return SavedCompetitionItem(
        competition_id=row.competition_id,
        saved_at=row.created_at,
        status=row.status,
        notes=row.notes,
        completed_requirement_ids=row.completed_requirement_ids,
        competition=competition,
    )


@router.patch("/saved/competitions/{competition_id}", response_model=SavedCompetitionItem)
def update_saved_competition(
    competition_id: str,
    body: SavedUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedCompetitionItem:
    row = (
        db.query(SavedCompetition)
        .filter(
            SavedCompetition.user_id == user.id,
            SavedCompetition.competition_id == competition_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "That competition is not in your saved list."},
        )

    if body.status is not None:
        row.status = body.status
    if body.notes is not None:
        row.notes = body.notes

    index = _competition_index(request)
    if body.completed_requirement_ids is not None:
        competition = index.get(row.competition_id)
        requirement_ids = {
            requirement.id
            for requirement in (competition.application_requirements if competition else [])
        }
        invalid_ids = set(body.completed_requirement_ids) - requirement_ids
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Checklist steps must belong to this competition."},
            )
        row.completed_requirement_ids = body.completed_requirement_ids
    db.commit()
    db.refresh(row)

    return SavedCompetitionItem(
        competition_id=row.competition_id,
        saved_at=row.created_at,
        status=row.status,
        notes=row.notes,
        completed_requirement_ids=row.completed_requirement_ids,
        competition=index.get(row.competition_id),
    )


@router.delete("/saved/competitions/{competition_id}", status_code=status.HTTP_200_OK)
def unsave_competition(
    competition_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    row = (
        db.query(SavedCompetition)
        .filter(
            SavedCompetition.user_id == user.id,
            SavedCompetition.competition_id == competition_id,
        )
        .first()
    )
    if row is not None:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.patch("/saved/{scholarship_id}", response_model=SavedScholarshipItem)
def update_saved_scholarship(
    scholarship_id: str,
    body: SavedUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedScholarshipItem:
    row = (
        db.query(SavedScholarship)
        .filter(
            SavedScholarship.user_id == user.id,
            SavedScholarship.scholarship_id == scholarship_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "That scholarship is not in your saved list."},
        )

    if body.status is not None:
        row.status = body.status
    if body.notes is not None:
        row.notes = body.notes

    index = _scholarship_index(request)
    if body.completed_requirement_ids is not None:
        scholarship = index.get(row.scholarship_id)
        requirement_ids = {
            requirement.id for requirement in (scholarship.application_requirements if scholarship else [])
        }
        invalid_ids = set(body.completed_requirement_ids) - requirement_ids
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Checklist steps must belong to this scholarship."},
            )
        row.completed_requirement_ids = body.completed_requirement_ids
    db.commit()
    db.refresh(row)

    return SavedScholarshipItem(
        scholarship_id=row.scholarship_id,
        saved_at=row.created_at,
        status=row.status,
        notes=row.notes,
        completed_requirement_ids=row.completed_requirement_ids,
        scholarship=index.get(row.scholarship_id),
    )


@router.patch("/saved/programs/{program_id}", response_model=SavedProgramItem)
def update_saved_program(
    program_id: str,
    body: SavedUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedProgramItem:
    row = (
        db.query(SavedProgram)
        .filter(
            SavedProgram.user_id == user.id,
            SavedProgram.program_id == program_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "That summer program is not in your saved list."},
        )

    if body.status is not None:
        row.status = body.status
    if body.notes is not None:
        row.notes = body.notes

    index = _program_index(request)
    if body.completed_requirement_ids is not None:
        program = index.get(row.program_id)
        requirement_ids = {
            requirement.id for requirement in (program.application_requirements if program else [])
        }
        invalid_ids = set(body.completed_requirement_ids) - requirement_ids
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Checklist steps must belong to this summer program."},
            )
        row.completed_requirement_ids = body.completed_requirement_ids
    db.commit()
    db.refresh(row)

    return SavedProgramItem(
        program_id=row.program_id,
        saved_at=row.created_at,
        status=row.status,
        notes=row.notes,
        completed_requirement_ids=row.completed_requirement_ids,
        program=index.get(row.program_id),
    )


@router.delete("/saved/{scholarship_id}", status_code=status.HTTP_200_OK)
def unsave_scholarship(
    scholarship_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    row = (
        db.query(SavedScholarship)
        .filter(
            SavedScholarship.user_id == user.id,
            SavedScholarship.scholarship_id == scholarship_id,
        )
        .first()
    )
    if row is not None:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.delete("/saved/programs/{program_id}", status_code=status.HTTP_200_OK)
def unsave_program(
    program_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    row = (
        db.query(SavedProgram)
        .filter(
            SavedProgram.user_id == user.id,
            SavedProgram.program_id == program_id,
        )
        .first()
    )
    if row is not None:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.patch("/reminders")
def set_reminder_pref(
    body: ReminderPrefUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    user.reminders_enabled = body.enabled
    db.commit()
    return {"enabled": user.reminders_enabled}
