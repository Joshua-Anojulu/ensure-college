"""Account endpoints for signup, sessions, and password recovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, set_authenticated_session
from app.auth.email import (
    EmailDeliveryError,
    password_reset_email_is_configured,
    send_password_reset_email,
)
from app.auth.password_reset import (
    generate_reset_token,
    hash_reset_token,
    is_expired,
    reset_token_expires_at,
    utcnow,
)
from app.auth.security import hash_password, verify_password
from app.db.database import get_db
from app.db.models import PasswordResetToken, User
from app.models.auth import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    SignupRequest,
    UserResponse,
)
from app.rate_limit import rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])

_signup_limit = rate_limiter(10, 60, "signup")
_login_limit = rate_limiter(20, 60, "login")
_password_limit = rate_limiter(10, 60, "password")
_delete_limit = rate_limiter(5, 60, "delete_account")
_password_reset_request_limit = rate_limiter(5, 15 * 60, "password_reset_request")
_password_reset_confirm_limit = rate_limiter(10, 15 * 60, "password_reset_confirm")

PASSWORD_RESET_ACCEPTED = {
    "ok": True,
    "message": "If an account exists for that email, a reset link will arrive shortly.",
}


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_signup_limit)],
)
def signup(request: Request, body: SignupRequest, db: Session = Depends(get_db)) -> User:
    email = _normalize_email(body.email)

    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "An account with that email already exists. Try logging in."},
        )

    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "An account with that email already exists. Try logging in."},
        ) from None
    db.refresh(user)

    set_authenticated_session(request, user)
    return user


@router.post("/login", response_model=UserResponse, dependencies=[Depends(_login_limit)])
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> User:
    email = _normalize_email(body.email)
    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Email or password is incorrect."},
        )

    set_authenticated_session(request, user)
    return user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/change-password", dependencies=[Depends(_password_limit)])
def change_password(
    request: Request,
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Your current password is incorrect."},
        )
    user.password_hash = hash_password(body.new_password)
    user.auth_version += 1
    db.commit()
    set_authenticated_session(request, user)
    return {"ok": True}


@router.post(
    "/password-reset/request",
    dependencies=[Depends(_password_reset_request_limit)],
)
def request_password_reset(
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict[str, bool | str]:
    """Send a one-time reset link without revealing whether an email is registered."""
    if not password_reset_email_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Password reset is temporarily unavailable. Please try again later."},
        )

    user = db.query(User).filter(User.email == _normalize_email(body.email)).first()
    if user is None:
        return PASSWORD_RESET_ACCEPTED

    raw_token = generate_reset_token()
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=reset_token_expires_at(),
    )
    # A newly requested link invalidates all older, unused links for this user.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).delete(synchronize_session=False)
    db.add(reset_token)
    db.commit()

    try:
        send_password_reset_email(user.email, raw_token)
    except EmailDeliveryError:
        # Do not leave a usable token behind when we know the mail handoff failed.
        db.delete(reset_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Password reset is temporarily unavailable. Please try again later."},
        ) from None

    return PASSWORD_RESET_ACCEPTED


@router.post(
    "/password-reset/confirm",
    dependencies=[Depends(_password_reset_confirm_limit)],
)
def confirm_password_reset(
    request: Request,
    body: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """Consume a valid one-time token, set a new password, and start a session."""
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == hash_reset_token(body.token))
        .first()
    )
    if (
        reset_token is None
        or reset_token.used_at is not None
        or is_expired(reset_token.expires_at)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "This password-reset link is invalid or expired. Request a new one."},
        )

    user = reset_token.user
    user.password_hash = hash_password(body.new_password)
    user.auth_version += 1
    reset_token.used_at = utcnow()
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != reset_token.id,
        PasswordResetToken.used_at.is_(None),
    ).delete(synchronize_session=False)
    db.commit()
    set_authenticated_session(request, user)
    return {"ok": True}


@router.post("/delete-account", dependencies=[Depends(_delete_limit)])
def delete_account(
    request: Request,
    body: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Password is incorrect."},
        )
    db.delete(user)
    db.commit()
    request.session.clear()
    return {"ok": True}
