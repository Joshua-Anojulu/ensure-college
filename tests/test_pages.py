import base64
import hashlib
from html.parser import HTMLParser
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import _SECURITY_HEADERS, app


ASSET_VERSION = "20260721-2"
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
VERSIONED_ASSET_PATHS = {
    "/static/css/style.css",
    "/static/css/world.css",
    "/static/js/app.js",
    "/static/js/gsap.min.js",
    "/static/js/landing-motion.js",
    "/static/js/journey-teaser.js",
    "/static/js/journey.js",
    "/static/js/vendor/gsap.min.js",
    "/static/js/vendor/ScrollTrigger.min.js",
    "/static/img/campus-quad.jpg",
    "/static/img/campus-quad-380.webp",
    "/static/img/campus-quad-760.webp",
}
VERSION_EXEMPT_PATHS = {
    "/static/favicon.svg",
    "/static/js/vendor/three.min.js",
}


class AssetUrlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.inline_scripts = []
        self._script_attrs = None
        self._script_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ("href", "src"):
            value = attrs.get(name)
            if value:
                self.urls.append(value)
        srcset = attrs.get("srcset")
        if srcset:
            for candidate in srcset.split(","):
                url = candidate.strip().split(" ", 1)[0]
                if url:
                    self.urls.append(url)
        if tag == "script" and "src" not in attrs:
            self._script_attrs = attrs
            self._script_parts = []

    def handle_data(self, data):
        if self._script_attrs is not None:
            self._script_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._script_attrs is not None:
            self.inline_scripts.append((self._script_attrs, "".join(self._script_parts)))
            self._script_attrs = None
            self._script_parts = []


def parse_html(text):
    parser = AssetUrlParser()
    parser.feed(text)
    return parser


def path_and_query(url):
    path, _, query = url.partition("?")
    return path, query


def csp_directives(csp):
    directives = {}
    for directive in csp.split(";"):
        parts = directive.strip().split()
        if parts:
            directives[parts[0]] = parts[1:]
    return directives


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


class TestVercelAnalytics:
    """The Web Analytics tag is injected only on Vercel deployments: the
    /_vercel/insights/ path does not exist locally and would 404 in every
    dev console."""

    ANALYTICS_SRC = "/_vercel/insights/script.js"
    PAGES = ["/", "/journey", "/privacy", "/terms", "/browse", "/guides/essays", "/scholarships/coca-cola-scholars"]

    @pytest.mark.parametrize("page", PAGES)
    def test_tag_absent_locally(self, client, page, monkeypatch):
        monkeypatch.delenv("VERCEL", raising=False)
        response = client.get(page)
        assert response.status_code == 200
        assert self.ANALYTICS_SRC not in response.text
        # The placeholder comment is swapped out (for the tag or for nothing),
        # never served raw.
        assert "__ANALYTICS__" not in response.text

    @pytest.mark.parametrize("page", PAGES)
    def test_tag_present_on_vercel(self, client, page, monkeypatch):
        monkeypatch.setenv("VERCEL", "1")
        response = client.get(page)
        assert response.status_code == 200
        assert f'<script defer src="{self.ANALYTICS_SRC}"></script>' in response.text


class TestProductionHygiene:
    def test_security_headers_on_index(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in response.headers

    def test_landing_csp_admits_served_consent_boot_hash(self, client):
        response = client.get("/")
        parser = parse_html(response.text)
        scripts = [
            script
            for attrs, script in parser.inline_scripts
            if attrs.get("id") == "site-consent-boot"
        ]
        assert len(scripts) == 1
        digest = base64.b64encode(hashlib.sha256(scripts[0].encode("utf-8")).digest()).decode("ascii")
        script_src = csp_directives(response.headers["Content-Security-Policy"])["script-src"]
        assert f"'sha256-{digest}'" in script_src

    def test_landing_script_csp_has_no_unsafe_inline(self, client):
        response = client.get("/")
        script_src = csp_directives(response.headers["Content-Security-Policy"])["script-src"]
        assert "'unsafe-inline'" not in script_src

    def test_non_landing_route_keeps_global_csp(self, client):
        response = client.get("/privacy")
        assert response.headers["Content-Security-Policy"] == _SECURITY_HEADERS["Content-Security-Policy"]

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

    def test_landing_keeps_inline_css_and_only_prefetches_external_stylesheet(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "<style>" in response.text
        assert "/*__INLINE_CSS__*/" not in response.text
        assert 'rel="stylesheet" href="/static/css/style.css' not in response.text
        assert f'rel="prefetch" href="/static/css/style.css?v={ASSET_VERSION}" as="style"' in response.text

    def test_landing_preloads_mobile_hero_art_byte_identical_to_css_url(self, client):
        """The mobile hero art is the LCP element; the preload href must match
        the style.css url() byte-for-byte (unversioned) or it double-fetches."""
        response = client.get("/")
        assert (
            '<link rel="preload" href="/static/img/hero-forest-mobile.webp" '
            'as="image" media="(max-width: 768px)" fetchpriority="high">'
        ) in response.text
        # No desktop hero preload: the gate is the mobile gate.
        assert 'preload" href="/static/img/hero-forest.webp"' not in response.text

    def test_landing_hero_art_is_a_real_attributable_image(self, client):
        """The forest stage must be a DOM <img>, not a ::before background:
        Lighthouse cannot attribute pseudo-element LCP. URLs stay unversioned,
        byte-identical to the mobile preload href."""
        response = client.get("/")
        assert '<div class="hero-stage">' in response.text
        assert (
            '<source media="(max-width: 768px)" '
            'srcset="/static/img/hero-forest-mobile.webp">'
        ) in response.text
        assert (
            '<img src="/static/img/hero-forest.webp" alt="" '
            'fetchpriority="high">'
        ) in response.text
        css = Path("app/static/css/style.css").read_text(encoding="utf-8")
        assert ".hero-stage" in css
        assert 'url("/static/img/hero-forest' not in css

    def test_landing_consent_gate_initial_markup_is_paintable(self, client):
        response = client.get("/")
        assert 'id="site-consent-boot"' in response.text
        assert '<div id="age-gate" class="age-gate">' in response.text
        assert 'id="age-gate-continue" disabled' in response.text
        assert "html.has-site-consent .age-gate" in response.text

    def test_landing_campus_quad_uses_responsive_webp_picture(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert '<picture>' in response.text
        assert (
            f'<source type="image/webp" srcset="/static/img/campus-quad-380.webp?v={ASSET_VERSION} 380w, '
            f'/static/img/campus-quad-760.webp?v={ASSET_VERSION} 760w" '
            'sizes="(max-width: 760px) calc(100vw - 2rem), 48vw">'
        ) in response.text
        assert f'<img src="/static/img/campus-quad.jpg?v={ASSET_VERSION}"' in response.text
        assert 'alt="Students walking across a college campus between classes"' in response.text
        assert 'loading="lazy"' in response.text
        assert 'decoding="async"' in response.text

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

    @pytest.mark.parametrize(
        "asset",
        [
            "/static/img/campus-quad-380.webp",
            "/static/img/campus-quad-760.webp",
            "/static/img/campus-quad.jpg",
        ],
    )
    def test_campus_quad_assets_return_200(self, client, asset):
        response = client.get(asset)
        assert response.status_code == 200, asset

    @pytest.mark.parametrize(
        "page",
        [
            "app/static/index.html",
            "app/static/journey.html",
            "app/static/privacy.html",
            "app/static/terms.html",
            "app/templates/base.html",
        ],
    )
    def test_versioned_asset_urls_are_cache_busted_in_lockstep(self, page):
        parser = parse_html(Path(page).read_text(encoding="utf-8"))
        seen = set()
        for url in parser.urls:
            path, query = path_and_query(url)
            if path in VERSION_EXEMPT_PATHS:
                continue
            if path not in VERSIONED_ASSET_PATHS:
                continue
            seen.add(path)
            assert query == f"v={ASSET_VERSION}", url
        assert seen, page

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
