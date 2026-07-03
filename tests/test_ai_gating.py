import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_routes_return_404_when_disabled(monkeypatch):
    monkeypatch.delenv("AI_FEATURES_ENABLED", raising=False)
    for path in ("/essay-advice", "/essay-review", "/program-advice"):
        r = client.post(path, json={})
        assert r.status_code == 404, f"{path} -> {r.status_code}"
    r = client.post("/resume/extract", data={"text": "hi"})
    assert r.status_code == 404


def test_homepage_ok_when_ai_disabled(monkeypatch):
    monkeypatch.delenv("AI_FEATURES_ENABLED", raising=False)
    assert client.get("/").status_code == 200


def test_app_serves_without_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert client.get("/health").status_code == 200


def test_index_exposes_ai_flag_false_by_default(monkeypatch):
    monkeypatch.delenv("AI_FEATURES_ENABLED", raising=False)
    assert '<meta name="ai-features-enabled" content="false">' in client.get("/").text


def test_index_exposes_ai_flag_true_when_enabled(monkeypatch):
    monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
    assert '<meta name="ai-features-enabled" content="true">' in client.get("/").text


def test_resume_import_section_ships_hidden():
    body = client.get("/").text
    assert re.search(
        r'<section[^>]*id="resume-import-section"[^>]*\bhidden\b', body
    ), "resume-import section must ship hidden; JS reveals it only when AI is on"
