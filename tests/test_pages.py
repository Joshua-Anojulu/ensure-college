import base64
import hashlib
from html.parser import HTMLParser
import json
import re
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

from app.main import _SECURITY_HEADERS, _edge_cacheable, app


ASSET_VERSION = "20261022-2"
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
]
VERSIONED_ASSET_PATHS = {
    "/static/css/style.css",
    "/static/css/world.css",
    "/static/js/app.js",
    "/static/js/gsap.min.js",
    "/static/js/landing-motion.js",
    "/static/js/journey.js",
    "/static/js/vendor/gsap.min.js",
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
    PAGES = ["/", "/privacy", "/terms", "/browse", "/guides/essays", "/scholarships/coca-cola-scholars"]

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
        "page",
        [
            "app/static/index.html",
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

    @pytest.mark.parametrize("path", ["/privacy", "/terms"])
    def test_legal_pages_have_no_em_dashes(self, client, path):
        """Privacy (two) and Terms (one) still punctuated with em dashes."""
        response = client.get(path)
        assert response.status_code == 200
        assert "\u2014" not in response.text, path
        assert "&mdash;" not in response.text, path

    def test_emails_have_no_em_dashes(self, monkeypatch):
        """The reminder digest's text body joined each item to its date with
        an em dash. Every transactional email is checked, text and HTML."""
        from datetime import date, timedelta

        from app.alerts import MatchRef, build_alert_email
        from app.auth import email as email_module
        from app.reminders import DueItem, build_reminder_email

        today = date(2026, 10, 22)
        items = [
            DueItem("Alpha Scholarship", "Scholarship", today, 0, "https://example.org/a"),
            DueItem("Beta Program", "Summer program", today + timedelta(days=3), 3, None),
        ]
        _subject, reminder_text, reminder_html = build_reminder_email(items, "tok")
        refs = [
            MatchRef("scholarship:a", "Alpha Scholarship", "Scholarship", "https://example.org/a"),
            MatchRef("program:b", "Beta Program", "Summer program", None),
        ]
        _subject, alert_text, alert_html = build_alert_email(refs, "tok")

        sent = {}
        monkeypatch.setenv("RESEND_API_KEY", "key")
        monkeypatch.setenv("EMAIL_FROM", "EnsureCollege <noreply@example.com>")
        monkeypatch.setenv("PUBLIC_APP_URL", "https://ensurecollege.com")
        monkeypatch.setattr(
            email_module,
            "send_email",
            lambda recipient, subject, text_body, html_body, **_kw: sent.update(text=text_body, html=html_body),
        )
        email_module.send_password_reset_email("student@example.com", "tok")

        bodies = {
            "reminder text": reminder_text,
            "reminder html": reminder_html,
            "alert text": alert_text,
            "alert html": alert_html,
            "reset text": sent["text"],
            "reset html": sent["html"],
        }
        for name, body in bodies.items():
            assert "\u2014" not in body, name
            assert "&mdash;" not in body, name


class TestJourneyOnHomePage:
    """The Journey is the home page's How it works section (2026-10-22): the
    separate /journey page and the landing teaser are retired, and every
    old link lands on the section."""

    def test_journey_url_redirects_to_the_home_section(self, client):
        response = client.get("/journey", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/#how-it-works"

    def test_journey_leaves_the_sitemap(self, client):
        response = client.get("/sitemap.xml")
        assert "/journey</loc>" not in response.text

    def test_home_carries_the_four_stops_as_real_markup(self, client):
        text = client.get("/").text
        assert '<section id="how-it-works" class="journey-home" aria-labelledby="how-it-works-title">' in text
        assert '<h2 id="how-it-works-title">' in text
        for heading in (
            "One profile. That's the work.",
            "Three lanes, one search.",
            "A plan, not a pile of tabs.",
            "The gate is closer than it looks.",
        ):
            assert f"<h3>{heading}</h3>" in text, heading
        # The flight's data contract: four banded cards and four rail stops.
        assert len(re.findall(r'class="journey-card" data-band="[\d.]+,[\d.]+"', text)) == 4
        assert len(re.findall(r'<button type="button" data-stop="[\d.]+">', text)) == 4

    def test_home_loads_the_flight_lazily_and_the_teaser_is_gone(self, client):
        text = client.get("/").text
        assert f'<script defer src="/static/js/journey.js?v={ASSET_VERSION}"></script>' in text
        # three.js is fetched by journey.js on approach, never by the page.
        assert "three.min.js" not in text
        for retired in ("journey-teaser", "proof-band", "difference-panel", "stack-card", "ScrollTrigger"):
            assert retired not in text, retired

    def test_every_how_it_works_link_points_at_the_section(self, client):
        assert '<a class="btn-ghost" href="#how-it-works">How it works</a>' in client.get("/").text
        for page in ("/privacy", "/terms", "/browse", "/scholarships/coca-cola-scholars", "/scholarships/no-such-entry"):
            text = client.get(page).text
            assert '<a class="btn-ghost" href="/#how-it-works">How it works</a>' in text, page
            assert 'href="/journey"' not in text, page

    @pytest.mark.parametrize(
        "asset",
        ["/static/js/vendor/three.min.js", "/static/js/journey.js"],
    )
    def test_journey_assets_return_200(self, client, asset):
        response = client.get(asset)
        assert response.status_code == 200, asset


class TestStageCohesion:
    """Stage C cohesion gates: colors flow through tokens, and every
    versioned URL a script constructs stays in cache-bust lockstep."""

    HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    # The one legitimate CSS hex outside token definitions and mask ramps:
    # the trail's SVG mask stroke is literal white by definition of a mask.
    CSS_HEX_ALLOWLIST = {"stroke: #fff;"}

    @pytest.mark.parametrize("name", ["style.css", "world.css"])
    def test_css_hex_literals_are_tokens_or_allowlisted(self, name):
        text = Path(f"app/static/css/{name}").read_text(encoding="utf-8")
        # Custom-property hexes are exempt only inside a bare `:root` token
        # block; a --var defined mid-component or under a scoped selector
        # like `:root .card` is still an offender. Blocks are resolved as
        # character spans by brace matching, so same-line and multi-line
        # `:root` shapes both end exactly where the CSS does.
        root_spans = []
        for m in re.finditer(r"(?m)^[ \t]*:root\b", text):
            brace = text.find("{", m.end())
            if brace == -1 or text[m.end() : brace].strip():
                continue  # `:root .scoped {` is not the token block
            depth = 0
            for i in range(brace, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        root_spans.append((brace, i))
                        break
        offenders = []
        for hm in self.HEX_RE.finditer(text):
            line_start = text.rfind("\n", 0, hm.start()) + 1
            line_end = text.find("\n", hm.start())
            if line_end == -1:
                line_end = len(text)
            stripped = text[line_start:line_end].strip()
            in_root = any(s <= hm.start() < e for s, e in root_spans)
            decl_start = max(text.rfind(c, 0, hm.start()) for c in ";{}\n")
            decl = text[decl_start + 1 : hm.start()].strip()
            if in_root and re.match(r"^--[\w-]+:", decl):
                continue
            if "mask-image" in stripped:
                continue  # alpha ramps: #000 is the only sensible literal
            if stripped in self.CSS_HEX_ALLOWLIST:
                continue
            offenders.append(stripped)
        assert offenders == [], offenders

    @pytest.mark.parametrize(
        "name", ["app.js", "journey.js"]
    )
    def test_js_versioned_urls_match_lockstep(self, name):
        text = Path(f"app/static/js/{name}").read_text(encoding="utf-8")
        pins = re.findall(r"/static/[\w/.-]+\?v=([\w-]+)", text)
        # Each of these files constructs at least one versioned URL today; an
        # empty match means the regex silently stopped seeing it, not that
        # the file went pin-free.
        assert pins, f"{name}: no versioned URLs found; update or drop this file"
        assert all(v == ASSET_VERSION for v in pins), (name, pins)

    @pytest.mark.parametrize(
        "name", ["app.js", "journey.js"]
    )
    def test_js_never_carries_css_hex_strings(self, name):
        text = Path(f"app/static/js/{name}").read_text(encoding="utf-8")
        assert not re.search(r"['\"]#[0-9a-fA-F]{3,8}['\"]", text), name

    def test_three_palette_literals_stay_in_journey_scenes(self):
        text = Path("app/static/js/app.js").read_text(encoding="utf-8")
        assert not re.search(r"0x[0-9a-fA-F]{6}", text)


EDGE_CACHE_CONTROL = "public, max-age=0, s-maxage=86400"
EDGE_CACHED_ASSETS = [
    "/static/css/style.css",
    f"/static/css/world.css?v={ASSET_VERSION}",
    f"/static/js/app.js?v={ASSET_VERSION}",
    "/static/js/vendor/three.min.js",
    "/static/fonts/Satoshi-Regular.woff2",
    "/static/img/hero-forest-mobile.webp",
    "/static/favicon.svg",
]


def _scope_request(path):
    return Request({"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""})


class TestEdgeCacheHeaders:
    """vercel.json sends every path, /static included, to the function, so an
    uncached asset or /vocabulary request can wait on a cold start (EC-01).
    Shared, cookie-free responses carry s-maxage so Vercel's CDN answers them;
    browsers still revalidate (max-age=0) and each deploy starts empty."""

    def test_vocabulary_is_edge_cacheable(self, client):
        response = client.get("/vocabulary")
        assert response.status_code == 200
        assert response.headers["cache-control"] == EDGE_CACHE_CONTROL
        assert "set-cookie" not in response.headers

    @pytest.mark.parametrize("asset", EDGE_CACHED_ASSETS)
    def test_static_assets_are_edge_cacheable(self, client, asset):
        response = client.get(asset)
        assert response.status_code == 200, asset
        assert response.headers["cache-control"] == EDGE_CACHE_CONTROL
        assert "set-cookie" not in response.headers

    def test_revalidation_keeps_the_same_policy(self, client):
        etag = client.get("/static/css/style.css").headers["etag"]
        response = client.get("/static/css/style.css", headers={"If-None-Match": etag})
        assert response.status_code == 304
        assert response.headers["cache-control"] == EDGE_CACHE_CONTROL

    def test_world_art_keeps_its_immutable_policy(self, client):
        manifest = json.loads(Path("app/static/img/world/manifest.json").read_text(encoding="utf-8"))
        for path in (f"/static/img/world/{next(iter(manifest))}", "/static/img/world/manifest.json"):
            response = client.get(path)
            assert response.status_code == 200, path
            assert response.headers["cache-control"] == "public, max-age=31536000, immutable"

    @pytest.mark.parametrize(
        "path",
        ["/", "/privacy", "/terms", "/static/index.html"],
    )
    def test_html_pages_never_gain_s_maxage(self, client, path):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "s-maxage" not in response.headers.get("cache-control", "")

    @pytest.mark.parametrize(
        "path",
        ["/scholarships", "/programs", "/competitions", "/health", "/auth/me", "/static/missing.css"],
    )
    def test_api_auth_and_missing_responses_never_gain_s_maxage(self, client, path):
        response = client.get(path)
        assert "s-maxage" not in response.headers.get("cache-control", ""), path

    def test_preview_match_post_never_gains_s_maxage(self, client):
        response = client.post(
            "/match/preview",
            json={"gpa": 3.7, "grade_level": "high_school_junior", "intended_majors": ["engineering"]},
        )
        assert response.status_code == 200
        assert "s-maxage" not in response.headers.get("cache-control", "")

    def test_signed_in_requests_set_no_cookie_and_account_routes_stay_private(self, client):
        email = f"edge-cache-{uuid.uuid4().hex[:12]}@example.com"
        signup = client.post("/auth/signup", json={"email": email, "password": "password123"})
        assert signup.status_code == 201
        for path in ("/vocabulary", "/static/css/style.css"):
            response = client.get(path)
            assert response.headers["cache-control"] == EDGE_CACHE_CONTROL, path
            assert "set-cookie" not in response.headers, path
        for path in ("/auth/me", "/account/profile", "/account/saved", "/"):
            response = client.get(path)
            assert response.status_code == 200, path
            assert "s-maxage" not in response.headers.get("cache-control", ""), path

    def test_cookie_setting_or_cookie_varying_replies_are_never_marked_shared(self):
        # Older Starlette releases re-sign the session cookie on every response
        # for a signed-in visitor, static files included. Such a reply must not
        # carry the edge header (Vercel would refuse to cache it anyway).
        response = Response(b"body{}", media_type="text/css")
        assert _edge_cacheable(_scope_request("/static/css/style.css"), response)
        response.set_cookie("session", "signed-value")
        assert not _edge_cacheable(_scope_request("/static/css/style.css"), response)
        varying = Response(b"{}", media_type="application/json", headers={"Vary": "Cookie"})
        assert not _edge_cacheable(_scope_request("/vocabulary"), varying)
