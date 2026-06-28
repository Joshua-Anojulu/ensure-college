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

# Branded HTML for the reset email. Email clients ignore <style>/<link> and
# external fonts, so everything is table-based with inline styles and a system
# font stack; color-scheme is pinned to light to avoid forced-dark inversion.
_RESET_EMAIL_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>Reset your Scholarships4U password</title>
</head>
<body style="margin:0; padding:0; background-color:#f5f7fb;">
<div style="display:none; max-height:0; overflow:hidden; opacity:0;">Reset your Scholarships4U password. This link expires in one hour.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f5f7fb;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0" border="0" style="width:480px; max-width:480px; background-color:#ffffff; border:1px solid #e4e8f0; border-radius:14px;">
        <tr>
          <td style="padding:32px; font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td width="36" height="36" align="center" valign="middle" bgcolor="#4f46e5" style="width:36px; height:36px; border-radius:9px; color:#ffffff; font-family:'Segoe UI',Arial,sans-serif; font-size:20px; font-weight:bold; text-align:center; line-height:36px;">S</td>
                <td style="padding-left:10px; font-size:17px; font-weight:bold; color:#0f172a;">Scholarships4U</td>
              </tr>
            </table>
            <h1 style="margin:26px 0 12px 0; font-size:22px; line-height:1.3; color:#0f172a;">Reset your password</h1>
            <p style="margin:0 0 22px 0; font-size:15px; line-height:1.6; color:#364152;">We received a request to reset the password for your Scholarships4U account. Choose a new one with the button below.</p>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px 0;">
              <tr>
                <td align="center" bgcolor="#4f46e5" style="border-radius:10px;">
                  <a href="{RESET_URL}" style="display:inline-block; padding:13px 30px; font-family:'Segoe UI',Arial,sans-serif; font-size:15px; font-weight:bold; color:#ffffff; text-decoration:none; border-radius:10px;">Reset your password</a>
                </td>
              </tr>
            </table>
            <p style="margin:0 0 6px 0; font-size:13px; line-height:1.5; color:#5a6b85;">Or paste this link into your browser:</p>
            <p style="margin:0 0 24px 0; font-size:13px; line-height:1.5; word-break:break-all;"><a href="{RESET_URL}" style="color:#4f46e5; text-decoration:underline;">{RESET_URL}</a></p>
            <p style="margin:0 0 4px 0; font-size:13px; line-height:1.6; color:#5a6b85;">This link expires in one hour.</p>
            <p style="margin:0; font-size:13px; line-height:1.6; color:#5a6b85;">If you didn't request this, you can safely ignore this email and your password will stay the same.</p>
          </td>
        </tr>
      </table>
      <p style="margin:18px 0 0 0; font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; font-size:12px; color:#7a8499;">Scholarships4U &middot; scholarships4u.dev</p>
    </td>
  </tr>
</table>
</body>
</html>"""


def _reset_email_html(escaped_url: str) -> str:
    """Render the branded reset email with the already HTML-escaped link."""
    return _RESET_EMAIL_HTML.replace("{RESET_URL}", escaped_url)


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
        "html": _reset_email_html(escaped_url),
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
