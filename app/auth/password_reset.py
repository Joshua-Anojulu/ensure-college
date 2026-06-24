"""One-time, hashed password-reset token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

RESET_TOKEN_TTL = timedelta(hours=1)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_reset_token() -> str:
    """Generate an opaque token safe for use in a URL query parameter."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Hash a reset token before it is persisted to the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def reset_token_expires_at(now: datetime | None = None) -> datetime:
    return (now or utcnow()) + RESET_TOKEN_TTL


def is_expired(expires_at: datetime, now: datetime | None = None) -> bool:
    """Compare a token expiry in UTC, including SQLite's naive round-trip."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= (now or utcnow())
