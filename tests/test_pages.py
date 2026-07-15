import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


ASSET_VERSION = "20260715-1"
FONT_ASSETS = [
    "/static/fonts/CabinetGrotesk-Bold.woff2",
    "/static/fonts/CabinetGrotesk-Extrabold.woff2",
    "/static/fonts/Satoshi-Regular.woff2",
    "/static/fonts/Satoshi-Medium.woff2",
    "/static/fonts/Satoshi-Bold.woff2",
    "/static/fonts/JetBrainsMono-Regular.woff2",
]
VENDOR_ASSETS = [
    "/static/js/vendor/gsap.min.js",
    "/static/js/vendor/ScrollTrigger.min.js",
]


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestLegalPages:
    def test_privacy_is_served(self, client):
        response = client.get("/privacy")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Age disclosure must be present.
        assert "13" in response.text

    def test_terms_is_served(self, client):
        response = client.get("/terms")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "sponsor" in response.text.lower()


class TestProductionHygiene:
    def test_security_headers_on_index(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in response.headers

    def test_csp_uses_self_hosted_styles_and_fonts(self, client):
        response = client.get("/")
        csp = response.headers["Content-Security-Policy"]
        assert "fonts.googleapis.com" not in csp
        assert "fonts.gstatic.com" not in csp
        assert "style-src 'self' 'unsafe-inline'" in csp
        assert "font-src 'self'" in csp

    def test_robots_txt_lists_sitemap(self, client):
        response = client.get("/robots.txt")
        assert response.status_code == 200
        assert "User-agent: *" in response.text
        assert "Sitemap:" in response.text
        assert response.text.endswith("\n")

    def test_sitemap_xml_includes_public_pages(self, client):
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<loc>http://testserver/</loc>" in response.text
        assert "<loc>http://testserver/privacy</loc>" in response.text
        assert "<loc>http://testserver/terms</loc>" in response.text

    def test_index_uses_absolute_og_image_url(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert 'property="og:image" content="http://testserver/static/og-image.png"' in response.text
        assert 'name="twitter:image" content="http://testserver/static/og-image.png"' in response.text

    def test_public_pages_include_production_canonical_urls(self, client):
        index = client.get("/")
        privacy = client.get("/privacy")
        terms = client.get("/terms")

        assert 'property="og:url" content="https://ensurecollege.com/"' in index.text
        assert 'rel="canonical" href="https://ensurecollege.com/"' in index.text
        assert 'rel="canonical" href="https://ensurecollege.com/privacy"' in privacy.text
        assert 'rel="canonical" href="https://ensurecollege.com/terms"' in terms.text

    def test_openapi_available_in_development(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_index_includes_catalog_browse_and_search_controls(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="tab-catalog"' in response.text
        assert 'id="catalog-section"' in response.text
        assert 'id="scholarship-search"' in response.text
        assert 'id="program-search"' in response.text
        assert 'id="catalog-search"' in response.text

    def test_index_includes_google_login_link_and_updated_assets(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="google-login-link"' in response.text
        assert 'href="/auth/google/login"' in response.text
        assert f"/static/css/style.css?v={ASSET_VERSION}" in response.text
        assert f"/static/js/app.js?v={ASSET_VERSION}" in response.text
        assert f"/static/js/landing-motion.js?v={ASSET_VERSION}" in response.text

    def test_index_uses_self_hosted_fonts(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "fonts.googleapis.com" not in response.text
        assert "fonts.gstatic.com" not in response.text
        assert 'href="/static/fonts/CabinetGrotesk-Extrabold.woff2"' in response.text
        assert 'href="/static/fonts/Satoshi-Regular.woff2"' in response.text

    @pytest.mark.parametrize("asset", FONT_ASSETS + VENDOR_ASSETS)
    def test_self_hosted_font_and_vendor_assets_return_200(self, client, asset):
        response = client.get(asset)
        assert response.status_code == 200, asset

    def test_index_substitutes_live_catalog_counts(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "__COUNT_" not in response.text
        assert re.search(r"<strong>\d+</strong>\s*<span>scholarships</span>", response.text)

    def test_swept_copy_has_no_em_or_en_dashes(self, client):
        response = client.get("/")
        assert response.status_code == 200
        swept_files = [
            Path("app/static/index.html"),
            Path("app/static/journey.html"),
            Path("app/static/js/app.js"),
            *Path("app/templates").glob("*.html"),
        ]
        for path in swept_files:
            text = path.read_text(encoding="utf-8")
            assert "—" not in text, path
            assert "–" not in text, path
            assert "&mdash;" not in text, path
            assert "&ndash;" not in text, path
        assert "—" not in response.text
        assert "–" not in response.text
        assert "&mdash;" not in response.text
        assert "&ndash;" not in response.text


class TestJourneyPage:
    def test_journey_is_served_with_seo_copy(self, client):
        response = client.get("/journey")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert 'rel="canonical" href="https://ensurecollege.com/journey"' in response.text
        assert "One profile." in response.text
        assert 'href="/#profile-form"' in response.text

    def test_journey_in_sitemap(self, client):
        response = client.get("/sitemap.xml")
        assert "<loc>http://testserver/journey</loc>" in response.text

    def test_nav_links_to_journey(self, client):
        response = client.get("/")
        assert 'href="/journey"' in response.text

    @pytest.mark.parametrize(
        "asset",
        ["/static/js/vendor/three.min.js", "/static/js/journey.js"],
    )
    def test_journey_assets_return_200(self, client, asset):
        response = client.get(asset)
        assert response.status_code == 200, asset
