"""Tests for server-rendered SEO pages (detail, browse, sitemap)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo_pages import _humanize


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

    def test_detail_page_renders_special_requirements(self, client):
        response = client.get("/scholarships/ieee-presidents-scholarship")
        assert response.status_code == 200
        assert "Special eligibility to verify" in response.text
        assert "ISEF finalist only" in response.text
        assert "No separate application" in response.text


class TestProgramAndCompetitionDetailPages:
    def test_program_detail_renders(self, client):
        program = client.app.state.programs[0]
        response = client.get(f"/programs/{program.id}")
        assert response.status_code == 200
        assert program.name in response.text
        assert "EducationalOccupationalProgram" in response.text

    def test_competition_detail_renders(self, client):
        competition = client.app.state.competitions[0]
        response = client.get(f"/competitions/{competition.id}")
        assert response.status_code == 200
        assert competition.name in response.text

    def test_unknown_program_and_competition_404(self, client):
        assert client.get("/programs/nope").status_code == 404
        assert client.get("/competitions/nope").status_code == 404

    def test_every_catalog_entry_has_a_working_page(self, client):
        state = client.app.state
        for kind, entries in (
            ("scholarships", state.scholarships),
            ("programs", state.programs),
            ("competitions", state.competitions),
        ):
            for entry in entries:
                response = client.get(f"/{kind}/{entry.id}")
                assert response.status_code == 200, f"/{kind}/{entry.id} -> {response.status_code}"


class TestBrowsePages:
    def test_browse_hub_links_all_three_directories(self, client):
        response = client.get("/browse")
        assert response.status_code == 200
        for kind in ("scholarships", "programs", "competitions"):
            assert f'href="/browse/{kind}"' in response.text

    def test_directories_list_every_entry(self, client):
        state = client.app.state
        for kind, entries in (
            ("scholarships", state.scholarships),
            ("programs", state.programs),
            ("competitions", state.competitions),
        ):
            response = client.get(f"/browse/{kind}")
            assert response.status_code == 200
            for entry in entries:
                assert f'href="/{kind}/{entry.id}"' in response.text, f"{kind} directory missing {entry.id}"

    def test_unknown_directory_404s(self, client):
        assert client.get("/browse/nonsense").status_code == 404

    def test_homepage_footer_links_browse(self, client):
        response = client.get("/")
        assert 'href="/browse"' in response.text


class TestSitemap:
    def test_sitemap_lists_every_page(self, client):
        state = client.app.state
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        body = response.text
        expected_urls = (
            3  # /, /privacy, /terms
            + 1  # /browse
            + 3  # directories
            + 1  # /guides/essays
            + 5  # /guides/essays/{theme}
            + len(state.scholarships) + len(state.programs) + len(state.competitions)
        )
        assert body.count("<loc>") == expected_urls
        assert f"/scholarships/{state.scholarships[0].id}</loc>" in body
        assert "/browse/competitions</loc>" in body

    def test_robots_txt_points_to_sitemap(self, client):
        response = client.get("/robots.txt")
        assert "Sitemap:" in response.text and "/sitemap.xml" in response.text


class TestHumanize:
    def test_us_citizen(self):
        assert _humanize("us_citizen") == "U.S. citizen"

    def test_us_citizen_permanent_resident_or_daca(self):
        assert (
            _humanize("us_citizen_permanent_resident_or_daca")
            == "U.S. citizen permanent resident or DACA"
        )

    def test_us_or_esa_member_state_mixed_case(self):
        assert _humanize("US_or_ESA_member_state") == "U.S. or ESA member state"

    def test_freeform_sentence_with_period_returned_unchanged(self):
        text = (
            "U.S. citizen or legal permanent resident (green card) required "
            "to take the National Exam..."
        )
        assert _humanize(text) == text

    def test_high_school_senior(self):
        assert _humanize("high_school_senior") == "High school senior"
