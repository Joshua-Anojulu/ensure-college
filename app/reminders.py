"""Deadline reminder digests.

Finds a user's saved opportunities whose real (non-VERIFY, non-rolling)
deadline falls within a short window and emails a plain, branded digest with an
unsubscribe link. Run on a schedule via the cron-secured endpoint in main.py.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from datetime import date
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.auth.email import (
    EMAIL_ACCENT_DEEP,
    EMAIL_BRAND,
    EMAIL_FONT,
    EMAIL_INK,
    EMAIL_INK_SOFT,
    EMAIL_LINE,
    EMAIL_MARK_HTML,
    EMAIL_MIST,
    EMAIL_MUTED,
    EMAIL_PAPER,
    EmailDeliveryError,
    email_button_html,
    list_unsubscribe_headers,
    send_email,
)
from app.db.models import (
    SavedCompetition,
    SavedProgram,
    SavedScholarship,
    User,
)
from app.matching.common import parse_iso_deadline

REMINDER_WINDOW_DAYS = 14
# Do not re-send within this many days even if the endpoint is hit repeatedly.
MIN_DAYS_BETWEEN_SENDS = 5


@dataclass(frozen=True)
class DueItem:
    name: str
    kind: str  # "Scholarship" | "Summer program" | "Competition"
    deadline: date
    days_left: int
    url: str | None


def _public_base_url() -> str:
    return (os.getenv("PUBLIC_APP_URL", "").strip() or "https://ensurecollege.com").rstrip("/")


def reminder_unsubscribe_url(unsubscribe_token: str) -> str:
    return f"{_public_base_url()}/reminders/unsubscribe?token={quote(unsubscribe_token, safe='')}"


def _within_window(deadline: str, today: date, window_days: int) -> tuple[date, int] | None:
    parsed = parse_iso_deadline(deadline)
    if parsed is None:
        return None
    days_left = (parsed - today).days
    if 0 <= days_left <= window_days:
        return parsed, days_left
    return None


def due_items_for_user(
    user: User,
    db: Session,
    scholarship_index: dict,
    program_index: dict,
    competition_index: dict,
    *,
    today: date,
    window_days: int = REMINDER_WINDOW_DAYS,
) -> list[DueItem]:
    """Return the user's saved opportunities closing soon."""
    items: list[DueItem] = []

    for row in db.query(SavedScholarship).filter(SavedScholarship.user_id == user.id):
        s = scholarship_index.get(row.scholarship_id)
        if s is None:
            continue
        hit = _within_window(s.deadline, today, window_days)
        if hit:
            items.append(DueItem(s.name, "Scholarship", hit[0], hit[1], str(s.url)))

    for row in db.query(SavedProgram).filter(SavedProgram.user_id == user.id):
        p = program_index.get(row.program_id)
        if p is None:
            continue
        hit = _within_window(p.deadline, today, window_days)
        if hit:
            items.append(DueItem(p.name, "Summer program", hit[0], hit[1], str(p.url)))

    for row in db.query(SavedCompetition).filter(SavedCompetition.user_id == user.id):
        c = competition_index.get(row.competition_id)
        if c is None:
            continue
        hit = _within_window(c.deadline, today, window_days)
        if hit:
            items.append(DueItem(c.name, "Competition", hit[0], hit[1], str(c.url)))

    items.sort(key=lambda i: (i.deadline, i.name.lower()))
    return items


def _fmt(d: date) -> str:
    return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")


def build_reminder_email(items: list[DueItem], unsubscribe_token: str) -> tuple[str, str, str]:
    """Return (subject, text_body, html_body) for a digest of due items."""
    base = _public_base_url()
    unsubscribe = reminder_unsubscribe_url(unsubscribe_token)
    n = len(items)
    subject = f"{n} saved {'opportunity' if n == 1 else 'opportunities'} closing soon"

    text_lines = ["Deadlines coming up on your EnsureCollege plan:", ""]
    for i in items:
        when = "today" if i.days_left == 0 else f"in {i.days_left} day{'s' if i.days_left != 1 else ''}"
        text_lines.append(f"- {i.name} ({i.kind}): {_fmt(i.deadline)} ({when})")
        if i.url:
            text_lines.append(f"  {i.url}")
    text_lines += [
        "",
        f"Open your plan: {base}/",
        "Always confirm the deadline on the official page before you apply.",
        f"Turn off these reminders: {unsubscribe}",
    ]
    text_body = "\n".join(text_lines)

    rows = ""
    for i in items:
        when = "today" if i.days_left == 0 else f"in {i.days_left} day{'s' if i.days_left != 1 else ''}"
        name = html.escape(i.name)
        name_cell = (
            f'<a href="{html.escape(i.url)}" style="color:{EMAIL_BRAND}; font-weight:700; text-decoration:none;">{name}</a>'
            if i.url else f'<span style="color:{EMAIL_INK}; font-weight:700;">{name}</span>'
        )
        rows += (
            '<tr>'
            f'<td style="padding:10px 0; border-bottom:1px solid {EMAIL_LINE};">{name_cell}'
            f'<div style="font-size:13px; color:{EMAIL_MUTED};">{html.escape(i.kind)}</div></td>'
            f'<td style="padding:10px 0 10px 14px; border-bottom:1px solid {EMAIL_LINE}; text-align:right; white-space:nowrap;">'
            f'<div style="font-weight:700; color:{EMAIL_INK};">{_fmt(i.deadline)}</div>'
            f'<div style="font-size:13px; color:{EMAIL_ACCENT_DEEP};">{when}</div></td>'
            '</tr>'
        )

    button = email_button_html(f"{html.escape(base)}/", "Open my plan")
    html_body = f"""\
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="color-scheme" content="light">
<meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0; background:{EMAIL_MIST};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{EMAIL_MIST}" style="background:{EMAIL_MIST};"><tr>
<td align="center" style="padding:32px 16px;">
<table role="presentation" width="520" cellpadding="0" cellspacing="0" bgcolor="{EMAIL_PAPER}" style="width:100%; max-width:520px; background:{EMAIL_PAPER}; border:1px solid {EMAIL_LINE}; border-radius:16px;">
<tr><td style="padding:30px 32px; font-family:{EMAIL_FONT};">
{EMAIL_MARK_HTML}
<h1 style="margin:22px 0 6px; font-size:21px; color:{EMAIL_INK};">Deadlines coming up</h1>
<p style="margin:0 0 16px; font-size:15px; line-height:1.55; color:{EMAIL_INK_SOFT};">These saved items on your plan close within the next two weeks:</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-family:{EMAIL_FONT}; font-size:15px;">{rows}</table>
<div style="margin:22px 0 0;">{button}</div>
<p style="margin:20px 0 0; font-size:13px; line-height:1.6; color:{EMAIL_MUTED};">Always confirm the deadline on the official page before you apply.</p>
</td></tr></table>
<p style="margin:16px 0 0; font-family:{EMAIL_FONT}; font-size:12px; color:{EMAIL_MUTED};">
You get these because you saved opportunities on EnsureCollege &middot; <a href="{html.escape(unsubscribe)}" style="color:{EMAIL_MUTED};">turn off reminders</a>
</p>
</td></tr></table></body></html>"""
    return subject, text_body, html_body


def send_reminder_digests(
    db: Session,
    scholarship_index: dict,
    program_index: dict,
    competition_index: dict,
    *,
    today: date | None = None,
) -> dict[str, int]:
    """Send a digest to every opted-in user with a due item. Returns counts."""
    today = today or date.today()
    considered = sent = skipped_recent = skipped_empty = failed = 0

    users = (
        db.query(User)
        .filter(User.reminders_enabled.is_(True))
        .filter(User.reminder_unsubscribe_token.isnot(None))
        .all()
    )
    for user in users:
        considered += 1
        if user.reminder_last_sent_on and (today - user.reminder_last_sent_on).days < MIN_DAYS_BETWEEN_SENDS:
            skipped_recent += 1
            continue
        items = due_items_for_user(
            user, db, scholarship_index, program_index, competition_index, today=today
        )
        if not items:
            skipped_empty += 1
            continue
        subject, text_body, html_body = build_reminder_email(items, user.reminder_unsubscribe_token)
        try:
            send_email(
                user.email,
                subject,
                text_body,
                html_body,
                log_tag="reminder-email",
                custom_headers=list_unsubscribe_headers(
                    reminder_unsubscribe_url(user.reminder_unsubscribe_token)
                ),
            )
        except EmailDeliveryError:
            failed += 1
            continue
        user.reminder_last_sent_on = today
        db.commit()
        sent += 1

    return {
        "considered": considered,
        "sent": sent,
        "skipped_recent": skipped_recent,
        "skipped_empty": skipped_empty,
        "failed": failed,
    }
