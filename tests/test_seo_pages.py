"""Tests for server-rendered SEO pages (detail, browse, sitemap)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestSlugIndexes:
    def test_state_has_slug_lookup_dicts(self, client):
        state = client.app.state
        assert state.scholarships_by_id["coca-cola-scholars"].name == "Coca-Cola Scholars Program"
        assert len(state.scholarships_by_id) == len(state.scholarships)
        assert len(state.programs_by_id) == len(state.programs)
        assert len(state.competitions_by_id) == len(state.competitions)


class TestScholarshipDetailPage:
    def test_known_slug_renders_page(self, client):
        response = client.get("/scholarships/coca-cola-scholars")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Coca-Cola Scholars Program" in response.text
        assert 'rel="canonical"' in response.text
        assert "/scholarships/coca-cola-scholars" in response.text
        assert "View and apply" in response.text
        assert "application/ld+json" in response.text
        assert "MonetaryGrant" in response.text

    def test_unknown_slug_renders_styled_404(self, client):
        response = client.get("/scholarships/not-a-real-scholarship")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "EnsureCollege" in response.text

    def test_detail_page_sends_edge_cache_header(self, client):
        response = client.get("/scholarships/coca-cola-scholars")
        assert response.headers["cache-control"] == "public, s-maxage=86400, stale-while-revalidate=604800"

    def test_entry_fields_are_html_escaped(self, client):
        import copy
        state = client.app.state
        fake = copy.deepcopy(state.scholarships_by_id["coca-cola-scholars"])
        fake.id = "xss-test-entry"
        fake.name = '<script>alert("x")</script> Award'
        state.scholarships_by_id[fake.id] = fake
        try:
            response = client.get("/scholarships/xss-test-entry")
            assert response.status_code == 200
            assert '<script>alert("x")</script>' not in response.text
            assert "&lt;script&gt;" in response.text
        finally:
            del state.scholarships_by_id[fake.id]

    def test_jsonld_cannot_break_out_of_script_tag(self, client):
        """entry.name/description reach the JSON-LD block via json.dumps, which does
        not escape "</script>". Rendered raw with `| safe`, a name containing
        "</script><script>alert(1)</script>" would close the JSON-LD script tag
        early and let the attacker's script tag execute for real."""
        import copy
        state = client.app.state
        fake = copy.deepcopy(state.scholarships_by_id["coca-cola-scholars"])
        fake.id = "jsonld-xss-test-entry"
        fake.name = "</script><script>alert(1)</script>"
        state.scholarships_by_id[fake.id] = fake
        try:
            response = client.get("/scholarships/jsonld-xss-test-entry")
            assert response.status_code == 200
            assert "</script><script>alert(1)</script>" not in response.text
        finally:
            del state.scholarships_by_id[fake.id]

    def test_unverified_or_estimated_entries_carry_labels(self, client):
        import copy
        state = client.app.state
        fake = copy.deepcopy(state.scholarships_by_id["coca-cola-scholars"])
        fake.id = "unverified-test-entry"
        fake.verified = False
        fake.estimated_deadline = "2027-03-15"
        fake.deadline = "VERIFY"
        state.scholarships_by_id[fake.id] = fake
        try:
            response = client.get("/scholarships/unverified-test-entry")
            assert "Not yet verified" in response.text
            assert "confirm on sponsor site" in response.text
        finally:
            del state.scholarships_by_id[fake.id]
