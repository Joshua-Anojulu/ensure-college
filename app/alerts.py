"""New-match alerts.

When opportunities are added to the catalog, email each opted-in user with a
saved profile the *new* ones that are a strong match for them. The first run
per user records their current strong matches as a baseline (no email), so
users are only alerted about opportunities added after that point.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.auth.email import EmailDeliveryError, send_email
from app.db.models import User, UserProfile
from app.matching.competition_matcher import match_competitions
from app.matching.matcher import match_scholarships
from app.matching.program_matcher import match_programs
from app.models.student import StudentProfile

# Cap the number of new matches surfaced in one email so a big catalog jump
# does not produce an overwhelming message; the rest surface on the next run.
MAX_ALERTS_PER_EMAIL = 8


@dataclass(frozen=True)
class MatchRef:
    key: str  # "scholarship:<id>" etc. — stable identity for the alerted set
    name: str
    kind: str
    url: str | None


def _public_base_url() -> str:
    return os.getenv("PUBLIC_APP_URL", "https://ensurecollege.com").strip().rstrip("/")


def strong_matches(
    profile: StudentProfile,
    scholarships: list,
    programs: list,
    competitions: list,
    *,
    today: date,
) -> list[MatchRef]:
    """All current strong-tier, non-special matches for a profile (high signal)."""
    refs: list[MatchRef] = []
    for r in match_scholarships(profile, scholarships, today=today):
        if r.match_tier == "strong" and not r.requires_special_check:
            refs.append(MatchRef(f"scholarship:{r.scholarship_id}", r.scholarship_name, "Scholarship", str(r.url)))
    for r in match_programs(profile, programs, today=today):
        if r.match_tier == "strong" and not r.requires_special_check:
            refs.append(MatchRef(f"program:{r.program_id}", r.name, "Summer program", str(r.url)))
    for r in match_competitions(profile, competitions, today=today):
        if r.match_tier == "strong" and not r.requires_special_check:
            refs.append(MatchRef(f"competition:{r.competition_id}", r.name, "Competition", str(r.url)))
    return refs


def build_alert_email(new_refs: list[MatchRef], unsubscribe_token: str) -> tuple[str, str, str]:
    base = _public_base_url()
    unsubscribe = f"{base}/reminders/unsubscribe?token={unsubscribe_token}"
    n = len(new_refs)
    subject = f"{n} new {'match' if n == 1 else 'matches'} for your profile"

    text_lines = ["New opportunities that match your EnsureCollege profile:", ""]
    for r in new_refs:
        text_lines.append(f"- {r.name} ({r.kind})")
        if r.url:
            text_lines.append(f"  {r.url}")
    text_lines += [
        "",
        f"See them on your matches: {base}/",
        "Always confirm eligibility and deadlines on the official page.",
        f"Turn off these emails: {unsubscribe}",
    ]
    text_body = "\n".join(text_lines)

    rows = ""
    for r in new_refs:
        name = html.escape(r.name)
        name_cell = (
            f'<a href="{html.escape(r.url)}" style="color:#1b2430; font-weight:700; text-decoration:none;">{name}</a>'
            if r.url else f'<span style="color:#1b2430; font-weight:700;">{name}</span>'
        )
        rows += (
            '<tr><td style="padding:10px 0; border-bottom:1px solid #ece9df;">'
            f'{name_cell}<div style="font-size:13px; color:#5c6069;">{html.escape(r.kind)}</div>'
            '</td></tr>'
        )

    html_body = f"""\
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="color-scheme" content="light">
<meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0; background:#eae8e1;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eae8e1;"><tr>
<td align="center" style="padding:32px 16px;">
<table role="presentation" width="520" cellpadding="0" cellspacing="0" style="width:520px; max-width:520px; background:#fbfaf7; border:1px solid #ddd9cd; border-radius:14px;">
<tr><td style="padding:30px 32px; font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td width="34" height="34" align="center" valign="middle" bgcolor="#1b2430" style="width:34px; height:34px; border-radius:9px; color:#fbfaf7; font-family:Georgia,serif; font-size:19px; font-weight:bold; line-height:34px;">E</td>
<td style="padding-left:10px; font-size:17px; font-weight:bold; color:#17181c;">EnsureCollege</td>
</tr></table>
<h1 style="margin:22px 0 6px; font-size:21px; color:#17181c;">New matches for you</h1>
<p style="margin:0 0 16px; font-size:15px; line-height:1.55; color:#33373f;">We just added these, and they're a strong fit for your profile:</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-family:'Segoe UI',Arial,sans-serif; font-size:15px;">{rows}</table>
<div style="margin:22px 0 0;"><a href="{html.escape(base)}/" style="display:inline-block; padding:12px 26px; background:#1b2430; color:#fbfaf7; font-size:15px; font-weight:bold; text-decoration:none; border-radius:10px;">See my matches</a></div>
<p style="margin:20px 0 0; font-size:13px; line-height:1.6; color:#5c6069;">Always confirm eligibility and the deadline on the official page.</p>
</td></tr></table>
<p style="margin:16px 0 0; font-family:'Segoe UI',Arial,sans-serif; font-size:12px; color:#83858c;">
You saved a profile on EnsureCollege &middot; <a href="{html.escape(unsubscribe)}" style="color:#83858c;">turn off emails</a>
</p>
</td></tr></table></body></html>"""
    return subject, text_body, html_body


def send_new_match_alerts(
    db: Session,
    scholarships: list,
    programs: list,
    competitions: list,
    *,
    today: date | None = None,
) -> dict[str, int]:
    """Alert opted-in users about newly-matching opportunities. Returns counts."""
    today = today or date.today()
    considered = baselined = sent = skipped_empty = skipped_no_profile = failed = 0

    users = (
        db.query(User)
        .filter(User.reminders_enabled.is_(True))
        .filter(User.reminder_unsubscribe_token.isnot(None))
        .all()
    )
    for user in users:
        considered += 1
        record = db.get(UserProfile, user.id)
        if record is None:
            skipped_no_profile += 1
            continue
        try:
            profile = StudentProfile.model_validate(record.data)
        except Exception:
            skipped_no_profile += 1
            continue

        current = strong_matches(profile, scholarships, programs, competitions, today=today)
        current_keys = [r.key for r in current]

        if user.alerted_opportunity_ids is None:
            # First exposure: baseline silently so only later additions alert.
            user.alerted_opportunity_ids = current_keys
            db.commit()
            baselined += 1
            continue

        seen = set(user.alerted_opportunity_ids)
        new_refs = [r for r in current if r.key not in seen]
        if not new_refs:
            skipped_empty += 1
            continue

        to_send = new_refs[:MAX_ALERTS_PER_EMAIL]
        subject, text_body, html_body = build_alert_email(to_send, user.reminder_unsubscribe_token)
        try:
            send_email(user.email, subject, text_body, html_body, log_tag="match-alert-email")
        except EmailDeliveryError:
            failed += 1
            continue
        # Only mark the ones we actually surfaced; the rest alert next run.
        user.alerted_opportunity_ids = sorted(seen | {r.key for r in to_send})
        db.commit()
        sent += 1

    return {
        "considered": considered,
        "baselined": baselined,
        "sent": sent,
        "skipped_empty": skipped_empty,
        "skipped_no_profile": skipped_no_profile,
        "failed": failed,
    }
