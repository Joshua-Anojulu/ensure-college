import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

THEME_KEYS = ["identity", "why-fit", "leadership-service", "academic-research", "general-writing"]


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestGuidePages:
    def test_index_lists_all_themes(self, client):
        response = client.get("/guides/essays")
        assert response.status_code == 200
        for key in THEME_KEYS:
            assert f"/guides/essays/{key}" in response.text

    @pytest.mark.parametrize("key", THEME_KEYS)
    def test_each_theme_page_renders(self, client, key):
        response = client.get(f"/guides/essays/{key}")
        assert response.status_code == 200
        assert "Example essays" in response.text
        assert 'rel="noopener noreferrer"' in response.text
        assert response.headers["Cache-Control"].startswith("public, s-maxage=86400")

    def test_unknown_theme_404s(self, client):
        assert client.get("/guides/essays/nonexistent").status_code == 404

    def test_sitemap_includes_guides(self, client):
        text = client.get("/sitemap.xml").text
        assert "<loc>http://testserver/guides/essays</loc>" in text
        for key in THEME_KEYS:
            assert f"<loc>http://testserver/guides/essays/{key}</loc>" in text

    def test_guide_content_structure(self):
        data = json.loads(
            (Path(__file__).resolve().parent.parent / "app" / "data" / "essay_guides.json").read_text(encoding="utf-8")
        )
        assert [theme["key"] for theme in data["themes"]] == THEME_KEYS
        for theme in data["themes"]:
            assert theme["title"] and theme["intro"]
            assert len(theme["steps"]) >= 3
            assert len(theme["links"]) >= 2
            for link in theme["links"]:
                assert link["url"].startswith("https://")
                assert link["title"] and link["source"]
