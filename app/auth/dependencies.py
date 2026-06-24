"""Authentication dependencies that read the signed session cookie."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User

SESSION_USER_KEY = "user_id"
SESSION_AUTH_VERSION_KEY = "auth_version"


def set_authenticated_session(request: Request, user: User) -> None:
    """Start a session tied to the user's current credential version."""
    request.session.clear()
    request.session[SESSION_USER_KEY] = user.id
    request.session[SESSION_AUTH_VERSION_KEY] = user.auth_version


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Return the logged-in user if a valid session exists, else None."""

    user_id = request.session.get(SESSION_USER_KEY)
    if user_id is None:
        return None

    user = db.get(User, user_id)
    session_version = request.session.get(SESSION_AUTH_VERSION_KEY)
    if user is None or session_version != user.auth_version:
        # Password changes invalidate other signed cookies immediately.
        request.session.clear()
        return None
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    """Require an authenticated user or raise 401."""

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "You need to be logged in to do that."},
        )
    return user
