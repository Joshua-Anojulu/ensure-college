"""Account endpoints for signup, sessions, and password recovery."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse, RedirectResponse
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

try:
    from authlib.integrations.starlette_client import OAuth, OAuthError
except ImportError:  # pragma: no cover - dependency is installed from requirements.
    OAuth = None

    class OAuthError(Exception):
        """Fallback so missing Authlib fails cleanly instead of at import time."""

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
PASSWORD_RESET_RESPONSE_FLOOR_SECONDS = 0.25
_LOGIN_DUMMY_PASSWORD_HASH = "$2b$12$rS1X/8jxGpazrNp2VkR8neAjUAfC8uORcKJGYK4FgbHjzaaZWblJe"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_SCOPE = "openid email profile"
GOOGLE_NOT_CONFIGURED = "Google sign-in is not configured yet."


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _pad_password_reset_response(start: float) -> None:
    remaining = PASSWORD_RESET_RESPONSE_FLOOR_SECONDS - (time.perf_counter() - start)
    if remaining > 0:
        time.sleep(remaining)


def google_oauth_is_configured() -> bool:
    return bool(
        os.getenv("GOOGLE_CLIENT_ID", "").strip()
        and os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        and OAuth is not None
    )


def _public_base_url(request: Request) -> str:
    configured = os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/")
    return configured or str(request.base_url).rstrip("/")


def _google_callback_url(request: Request) -> str:
    return f"{_public_base_url(request)}/auth/google/callback"


def _google_client():
    if not google_oauth_is_configured():
        return None

    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID", "").strip(),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
        server_metadata_url=GOOGLE_DISCOVERY_URL,
        client_kwargs={"scope": GOOGLE_SCOPE},
    )
    return oauth.google


async def _fetch_google_userinfo(request: Request) -> Mapping[str, object]:
    client = _google_client()
    if client is None:
        raise RuntimeError(GOOGLE_NOT_CONFIGURED)

    token = await client.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if userinfo is None:
        response = await client.get("https://openidconnect.googleapis.com/v1/userinfo", token=token)
        userinfo = response.json()
    return userinfo


def _require_verified_google_identity(userinfo: Mapping[str, object]) -> tuple[str, str]:
    email = _normalize_email(str(userinfo.get("email") or ""))
    google_sub = str(userinfo.get("sub") or "").strip()
    email_verified = userinfo.get("email_verified")
    if isinstance(email_verified, str):
        email_verified = email_verified.lower() == "true"

    if not email or not google_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Google did not return the account details needed to sign in."},
        )
    if email_verified is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Google has not verified that email address."},
        )
    return email, google_sub


def _find_or_create_google_user(db: Session, email: str, google_sub: str) -> User:
    # The Google `sub` is the stable identifier; the email on a Google account
    # can change. An already-linked user signs in by sub regardless, and we
    # adopt their new address when no other account holds it (never lock them
    # out over an email change on Google's side).
    user_with_sub = db.query(User).filter(User.google_sub == google_sub).first()
    if user_with_sub is not None:
        if user_with_sub.email != email:
            email_taken = db.query(User).filter(User.email == email).first() is not None
            if not email_taken:
                user_with_sub.email = email
                db.commit()
                db.refresh(user_with_sub)
        return user_with_sub

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email, google_sub=google_sub, password_hash=None)
        db.add(user)
    elif user.google_sub and user.google_sub != google_sub:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "That email is already linked to another Google account."},
        )
    else:
        user.google_sub = google_sub

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "That Google account could not be linked. Try logging in again."},
        ) from None
    db.refresh(user)
    return user


@router.get("/google/login")
async def google_login(request: Request):
    client = _google_client()
    if client is None:
        return PlainTextResponse(GOOGLE_NOT_CONFIGURED, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return await client.authorize_redirect(request, _google_callback_url(request))


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    if not google_oauth_is_configured():
        return PlainTextResponse(GOOGLE_NOT_CONFIGURED, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        userinfo = await _fetch_google_userinfo(request)
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Google sign-in could not be completed. Try again."},
        ) from exc
    except RuntimeError:
        return PlainTextResponse(GOOGLE_NOT_CONFIGURED, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    email, google_sub = _require_verified_google_identity(userinfo)
    user = _find_or_create_google_user(db, email, google_sub)
    set_authenticated_session(request, user)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


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
    password_hash = user.password_hash if user is not None and user.password_hash else _LOGIN_DUMMY_PASSWORD_HASH
    password_ok = verify_password(body.password, password_hash)

    if user is None or not user.password_hash or not password_ok:
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
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "This account uses Google sign-in and does not have a password."},
        )
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
    start = time.perf_counter()
    try:
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
        db.add(reset_token)
        db.commit()

        try:
            send_password_reset_email(user.email, raw_token)
        except EmailDeliveryError:
            # Do not leave a usable token behind when we know the mail handoff
            # failed. Older links are still intact at this point, so a transient
            # mail outage never strands the user with zero working links.
            db.delete(reset_token)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "Password reset is temporarily unavailable. Please try again later."},
            ) from None

        # The delivered link supersedes all older, unused links for this user.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.id != reset_token.id,
        ).delete(synchronize_session=False)
        db.commit()

        return PASSWORD_RESET_ACCEPTED
    finally:
        _pad_password_reset_response(start)


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
    if user.password_hash:
        if not body.password or not verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Password is incorrect."},
            )
    # Google-only accounts have no password to confirm with; the authenticated
    # session is the authorization. Without this branch they could never delete
    # their account or its data.
    db.delete(user)
    db.commit()
    request.session.clear()
    return {"ok": True}
