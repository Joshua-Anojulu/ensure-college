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
