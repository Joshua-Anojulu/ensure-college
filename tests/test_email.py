import json

from app.auth import email


def test_send_email_puts_custom_headers_in_resend_payload(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "resend-key")
    monkeypatch.setenv("EMAIL_FROM", "EnsureCollege <noreply@example.com>")

    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["transport_headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setattr(email, "urlopen", fake_urlopen)

    email.send_email(
        "student@example.com",
        "Subject",
        "Text",
        "<p>HTML</p>",
        log_tag="test-email",
        custom_headers={
            "List-Unsubscribe": "<https://ensurecollege.com/reminders/unsubscribe?token=tok>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    )

    assert captured["payload"]["headers"] == {
        "List-Unsubscribe": "<https://ensurecollege.com/reminders/unsubscribe?token=tok>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }
    assert "List-Unsubscribe" not in captured["transport_headers"]
