"""Tests for new-match alerts: baseline-then-notify, email build, run endpoint."""

from datetime import date

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.models import User
from app.main import app
from app.models.scholarship import Eligibility, Scholarship

REF = date(2026, 6, 26)

PROFILE = {
    "gpa": 3.9,
    "grade_level": "high_school_senior",
    "citizenship": "us_citizen",
    "state": "TX",
    "intended_majors": ["engineering"],
    "financial_need_level": "medium",
}


def _sch(sid: str) -> Scholarship:
    return Scholarship(
        id=sid,
        name=f"{sid.title()} Engineering Award",
        sponsor="Test Sponsor",
        award_amount=5000,
        deadline="rolling",
        url="https://example.org/",
        eligibility=Eligibility(fields_of_study=["engineering"], citizenship_requirement="any"),
        description="A strong engineering match.",
    )


def test_alert_email_build():
    from app.alerts import MatchRef, build_alert_email

    refs = [MatchRef("scholarship:a", "Alpha Award", "Scholarship", "https://a.org")]
    subject, text, html = build_alert_email(refs, "tok9")
    assert subject == "1 new match for your profile"
    assert "Alpha Award" in text and "Alpha Award" in html
    assert "/reminders/unsubscribe?token=tok9" in text
    assert "/reminders/unsubscribe?token=tok9" in html


def test_baseline_then_alert(monkeypatch):
    import app.alerts as alerts

    with TestClient(app) as client:
        client.post("/auth/signup", json={"email": "alertme@example.com", "password": "password123"})
        client.put("/account/profile", json=PROFILE)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == "alertme@example.com").first()

            sent = {}
            monkeypatch.setattr(
                alerts, "send_email",
                lambda to, subject, text, html, log_tag: sent.update({"to": to, "subject": subject, "text": text}),
            )

            # First run baselines the existing match silently.
            counts1 = alerts.send_new_match_alerts(db, [_sch("gamma")], [], [], today=REF)
            assert counts1["baselined"] == 1 and counts1["sent"] == 0
            assert not sent
            db.refresh(user)
            assert "scholarship:gamma" in (user.alerted_opportunity_ids or [])

            # A newly added matching scholarship triggers an alert.
            counts2 = alerts.send_new_match_alerts(db, [_sch("gamma"), _sch("delta")], [], [], today=REF)
            assert counts2["sent"] == 1
            assert sent["to"] == "alertme@example.com"
            assert "Delta" in sent["text"]

            # No further alert when nothing is new.
            sent.clear()
            counts3 = alerts.send_new_match_alerts(db, [_sch("gamma"), _sch("delta")], [], [], today=REF)
            assert counts3["sent"] == 0 and counts3["skipped_empty"] == 1
            assert not sent
        finally:
            db.close()


def test_no_profile_is_skipped(monkeypatch):
    import app.alerts as alerts

    with TestClient(app) as client:
        client.post("/auth/signup", json={"email": "noprofile@example.com", "password": "password123"})
        db = SessionLocal()
        try:
            monkeypatch.setattr(alerts, "send_email", lambda *a, **k: None)
            counts = alerts.send_new_match_alerts(db, [_sch("x")], [], [], today=REF)
            assert counts["skipped_no_profile"] >= 1
        finally:
            db.close()


def test_run_endpoint_returns_both_sections(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "s3cr3t")
    with TestClient(app) as client:
        resp = client.get("/reminders/run", headers={"Authorization": "Bearer s3cr3t"})
        assert resp.status_code == 200
        body = resp.json()
        assert "deadline_reminders" in body and "new_match_alerts" in body
