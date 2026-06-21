import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestLegalPages:
    def test_privacy_is_served(self, client):
        response = client.get("/privacy")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Key disclosures must be present.
        assert "Anthropic" in response.text
        assert "13" in response.text

    def test_terms_is_served(self, client):
        response = client.get("/terms")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "sponsor" in response.text.lower()
