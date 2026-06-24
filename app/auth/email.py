"""Transactional email helpers for account recovery.

Resend is called over its HTTPS API rather than through a provider SDK, keeping
the deployment dependency surface small. The provider key and sender address
stay in environment variables and are never exposed to the browser.
"""

from __future__ import annotations

import html
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

RESEND_EMAILS_URL = "https://api.resend.com/emails"


class EmailDeliveryError(RuntimeError):
    """Raised when a transactional email cannot be safely delivered."""


def password_reset_email_is_configured() -> bool:
    """Return whether every setting needed to deliver reset links is present."""
    return bool(
        os.getenv("RESEND_API_KEY", "").strip()
        and os.getenv("EMAIL_FROM", "").strip()
        and os.getenv("PUBLIC_APP_URL", "").strip()
    )


def password_reset_url(token: str) -> str:
    """Build the public reset-link URL from an opaque, one-time token."""
    app_url = os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/")
    if not app_url:
        raise EmailDeliveryError("Password-reset email is not configured")
    return f"{app_url}/?reset_token={quote(token, safe='')}"


def send_password_reset_email(recipient: str, token: str) -> None:
    """Ask Resend to send a password-reset link to ``recipient``.

    The API response is intentionally not surfaced to callers: account-recovery
    endpoints must not reveal provider internals or whether an address exists.
    """
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("EMAIL_FROM", "").strip()
    if not api_key or not sender or not password_reset_email_is_configured():
        raise EmailDeliveryError("Password-reset email is not configured")

    reset_url = password_reset_url(token)
    escaped_url = html.escape(reset_url, quote=True)
    payload = {
        "from": sender,
        "to": [recipient],
        "subject": "Reset your Scholarships4U password",
        "text": (
            "We received a request to reset your Scholarships4U password. "
            f"Use this link within one hour: {reset_url}\n\n"
            "If you did not request this, you can safely ignore this email."
        ),
        "html": (
            "<p>We received a request to reset your Scholarships4U password.</p>"
            f'<p><a href="{escaped_url}">Reset your password</a></p>'
            "<p>This link expires in one hour. If you did not request this, "
            "you can safely ignore this email.</p>"
        ),
    }
    request = Request(
        RESEND_EMAILS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise EmailDeliveryError("Password-reset email could not be delivered")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise EmailDeliveryError("Password-reset email could not be delivered") from exc
