"""Transactional email helpers for account recovery.

Resend is called over its HTTPS API rather than through a provider SDK, keeping
the deployment dependency surface small. The provider key and sender address
stay in environment variables and are never exposed to the browser.
"""

from __future__ import annotations

import html
import json
import os
import sys
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
<title>Reset your EnsureCollege password</title>
</head>
<body style="margin:0; padding:0; background-color:#eae8e1;">
<div style="display:none; max-height:0; overflow:hidden; opacity:0;">Reset your EnsureCollege password. This link expires in one hour.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#eae8e1;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0" border="0" style="width:480px; max-width:480px; background-color:#fbfaf7; border:1px solid #ddd9cd; border-radius:14px;">
        <tr>
          <td style="padding:32px; font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td width="36" height="36" align="center" valign="middle" bgcolor="#1b2430" style="width:36px; height:36px; border-radius:9px; color:#ffffff; font-family:'Segoe UI',Arial,sans-serif; font-size:20px; font-weight:bold; text-align:center; line-height:36px;">E</td>
                <td style="padding-left:10px; font-size:17px; font-weight:bold; color:#17181c;">EnsureCollege</td>
              </tr>
            </table>
            <h1 style="margin:26px 0 12px 0; font-size:22px; line-height:1.3; color:#17181c;">Reset your password</h1>
            <p style="margin:0 0 22px 0; font-size:15px; line-height:1.6; color:#33373f;">We received a request to reset the password for your EnsureCollege account. Choose a new one with the button below.</p>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px 0;">
              <tr>
                <td align="center" bgcolor="#1b2430" style="border-radius:10px;">
                  <a href="{RESET_URL}" style="display:inline-block; padding:13px 30px; font-family:'Segoe UI',Arial,sans-serif; font-size:15px; font-weight:bold; color:#ffffff; text-decoration:none; border-radius:10px;">Reset your password</a>
                </td>
              </tr>
            </table>
            <p style="margin:0 0 6px 0; font-size:13px; line-height:1.5; color:#5c6069;">Or paste this link into your browser:</p>
            <p style="margin:0 0 24px 0; font-size:13px; line-height:1.5; word-break:break-all;"><a href="{RESET_URL}" style="color:#1b2430; text-decoration:underline;">{RESET_URL}</a></p>
            <p style="margin:0 0 4px 0; font-size:13px; line-height:1.6; color:#5c6069;">This link expires in one hour.</p>
            <p style="margin:0; font-size:13px; line-height:1.6; color:#5c6069;">If you didn't request this, you can safely ignore this email and your password will stay the same.</p>
          </td>
        </tr>
      </table>
      <p style="margin:18px 0 0 0; font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; font-size:12px; color:#83858c;">EnsureCollege &middot; ensurecollege.com</p>
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
    missing = [
        k for k in ("RESEND_API_KEY", "EMAIL_FROM", "PUBLIC_APP_URL")
        if not os.getenv(k, "").strip()
    ]
    if missing:
        print(f"[reset-email] config check failed; missing env: {missing}", file=sys.stderr, flush=True)
        return False
    return True


def password_reset_url(token: str) -> str:
    """Build the public reset-link URL from an opaque, one-time token."""
    app_url = os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/")
    if not app_url:
        raise EmailDeliveryError("Password-reset email is not configured")
    return f"{app_url}/?reset_token={quote(token, safe='')}"


def send_email(recipient: str, subject: str, text_body: str, html_body: str, *, log_tag: str) -> None:
    """Send one transactional email through Resend. Raises EmailDeliveryError.

    The provider response is intentionally not surfaced to callers; only a
    server-side diagnostic is logged.
    """
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("EMAIL_FROM", "").strip()
    if not api_key or not sender:
        missing = [k for k in ("RESEND_API_KEY", "EMAIL_FROM") if not os.getenv(k, "").strip()]
        print(f"[{log_tag}] not configured; missing env: {missing}", file=sys.stderr, flush=True)
        raise EmailDeliveryError("Email delivery is not configured")

    payload = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }
    request = Request(
        RESEND_EMAILS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Resend's API is fronted by Cloudflare, which blocks the default
            # "Python-urllib" agent with a 403 (error 1010). Send an explicit
            # User-Agent so the request is not rejected before it reaches Resend.
            "User-Agent": "EnsureCollege/1.0 (+https://ensurecollege.com)",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                body = response.read(600).decode("utf-8", "ignore")
                print(
                    f"[{log_tag}] resend non-2xx {response.status} from={sender!r}: {body}",
                    file=sys.stderr, flush=True,
                )
                raise EmailDeliveryError("Email could not be delivered")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:600]
        print(
            f"[{log_tag}] resend HTTPError {exc.code} from={sender!r}: {detail}",
            file=sys.stderr, flush=True,
        )
        raise EmailDeliveryError("Email could not be delivered") from exc
    except (URLError, TimeoutError, OSError) as exc:
        print(
            f"[{log_tag}] resend transport error: {type(exc).__name__}: {exc}",
            file=sys.stderr, flush=True,
        )
        raise EmailDeliveryError("Email could not be delivered") from exc


def send_password_reset_email(recipient: str, token: str) -> None:
    """Ask Resend to send a password-reset link to ``recipient``.

    The API response is intentionally not surfaced to callers: account-recovery
    endpoints must not reveal provider internals or whether an address exists.
    """
    if not password_reset_email_is_configured():
        raise EmailDeliveryError("Password-reset email is not configured")

    reset_url = password_reset_url(token)
    escaped_url = html.escape(reset_url, quote=True)
    send_email(
        recipient,
        subject="Reset your EnsureCollege password",
        text_body=(
            "We received a request to reset your EnsureCollege password. "
            f"Use this link within one hour: {reset_url}\n\n"
            "If you did not request this, you can safely ignore this email."
        ),
        html_body=_reset_email_html(escaped_url),
        log_tag="reset-email",
    )
