from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_old_domain_redirects_permanently():
    r = client.get("/terms", headers={"host": "scholarships4u.dev"}, follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"] == "https://ensurecollege.com/terms"


def test_new_domain_not_redirected():
    r = client.get("/health", headers={"host": "ensurecollege.com"}, follow_redirects=False)
    assert r.status_code == 200
