import base64
import gzip
import hashlib
from html.parser import HTMLParser
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import _SECURITY_HEADERS, app


ASSET_VERSION = "20260723-2"
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
LEGAL_COPY_HASHES = {
    "privacy": "03b95fc7a18366ce4c50ef8abe86d45373c3cb243de4825c4263b82d61cdc9d7",
    "terms": "15b5bff595fd5c7c3aebb0516cc04f3e46281c02d18c26d4519b513a09e4905a",
    "footer": "9d64f181ef717be4badf0cfdc4e78f974cfdeb88c4f770387e449b549bc66fb0",
    "age_gate": "b6cfc444c8039586f4c50ada4581ab5b7d38ad5df3b9eb7764948fb54fe96c38",
}
CSS_GZIP_CAPS = {
    "style.css": 27 * 1024,
    "world.css": 14 * 1024,
}
CARD_NODE_BUILDERS = ("buildCard", "buildProgramCard", "buildCompetitionCard")
CARD_NODE_COUNT_METHOD = (
    "Treats pre-Stage 1 card markup as the same repeated-card builder with the "
    "chrome-only ec-paper-card class removed. CSS pseudo-elements add zero DOM "
    "nodes, so the test counts only Stage 1 createElementNS/buildChromeUse calls "
    "inside repeated-card builders."
)


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


class TextSnapshotParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data)


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


def normalized_snippet(text):
    return re.sub(r"[ \t]+$", "", text.replace("\r\n", "\n"), flags=re.MULTILINE).strip()


def js_function_body(text, function_name):
    start = text.index(f"function {function_name}")
    # The body brace is the first `{` AFTER the parameter list closes; a
    # default parameter like `options = {}` puts braces inside the parens
    # and must not terminate the scan at the signature.
    paren = text.index("(", start)
    depth = 0
    paren_end = None
    for index in range(paren, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                paren_end = index
                break
    if paren_end is None:
        raise AssertionError(function_name)
    brace = text.index("{", paren_end)
    depth = 0
    for index in range(brace, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError(function_name)


def snippet_lines(lines):
    return normalized_snippet("\n".join(lines))


def first_match(text, pattern):
    match = re.search(pattern, text, re.DOTALL)
    assert match is not None, pattern
    return match.group(0)


def visible_copy_hash(html):
    parser = TextSnapshotParser()
    parser.feed(html)
    normalized = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


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

    def test_privacy_copy_hash_stays_locked(self, client):
        response = client.get("/privacy")
        article = first_match(
            response.text, r'<article class="panel legal-content">.*?</article>'
        )
        assert visible_copy_hash(article) == LEGAL_COPY_HASHES["privacy"]

    def test_terms_copy_hash_stays_locked(self, client):
        response = client.get("/terms")
        article = first_match(
            response.text, r'<article class="panel legal-content">.*?</article>'
        )
        assert visible_copy_hash(article) == LEGAL_COPY_HASHES["terms"]

    def test_footer_disclaimer_copy_hash_stays_locked(self, client):
        response = client.get("/")
        footer = first_match(response.text, r'<footer class="site-footer">.*?</footer>')
        assert visible_copy_hash(footer) == LEGAL_COPY_HASHES["footer"]

    def test_consent_gate_copy_hash_stays_locked(self, client):
        response = client.get("/")
        gate = first_match(
            response.text,
            r'<div id="age-gate" class="age-gate">.*?</div>\s*</div>',
        )
        assert visible_copy_hash(gate) == LEGAL_COPY_HASHES["age_gate"]


class TestOpportunityPageSnippets:
    CARD_STATS_RE = r'<div class="card-stats">.*?</div>\s*</div>'
    VERIFICATION_RE = r'<p class="verification-source detail-verification">.*?</p>'

    @pytest.mark.parametrize(
        "path,expected_stats,expected_verification",
        [
            (
                "/scholarships/dell-scholars",
                snippet_lines(
                    [
                        '<div class="card-stats">',
                        "",
                        '      <div class="stat stat-award">',
                        '        <span class="stat-label">Award</span>',
                        '        <span class="stat-value">20000 plus laptop and textbook credits</span>',
                        "      </div>",
                        "",
                        '      <div class="stat">',
                        '        <span class="stat-label">Deadline</span>',
                        '        <span class="stat-value">~Feb 15, 2027</span>',
                        '        <span class="stat-note">Estimated; confirm on sponsor site</span>',
                        "      </div>",
                        "    </div>",
                    ]
                ),
                snippet_lines(
                    [
                        '<p class="verification-source detail-verification">',
                        "",
                        '        Verified Jul 2, 2026 \u00b7 <a href="https://www.dellscholars.org/students/" rel="noopener noreferrer">View official source</a>',
                        "",
                        "    </p>",
                    ]
                ),
            ),
            (
                "/programs/promys",
                snippet_lines(
                    [
                        '<div class="card-stats">',
                        "",
                        '      <div class="stat stat-award">',
                        '        <span class="stat-label">Cost</span>',
                        '        <span class="stat-value">Tuition-based; need-based aid available up to full cost</span>',
                        "      </div>",
                        "",
                        '      <div class="stat">',
                        '        <span class="stat-label">Deadline</span>',
                        '        <span class="stat-value">~Feb 27, 2027</span>',
                        '        <span class="stat-note">Estimated; confirm on sponsor site</span>',
                        "      </div>",
                        "    </div>",
                    ]
                ),
                snippet_lines(
                    [
                        '<p class="verification-source detail-verification">',
                        "",
                        '        Verified Jun 26, 2026 \u00b7 <a href="https://promys.org/programs/promys/for-students/" rel="noopener noreferrer">View official source</a>',
                        "",
                        "    </p>",
                    ]
                ),
            ),
            (
                "/competitions/profile-in-courage-essay-contest",
                snippet_lines(
                    [
                        '<div class="card-stats">',
                        "",
                        '      <div class="stat stat-award">',
                        '        <span class="stat-label">Recognition</span>',
                        '        <span class="stat-value">First place: $10,000 cash award plus an invitation (with paid travel) to the Profile in Courage Award ceremony in Boston; second place: $3,000; three finalists: $1,000 each; fifteen honorable mentions; all participants receive a Certificate of Participation.</span>',
                        "      </div>",
                        "",
                        '      <div class="stat">',
                        '        <span class="stat-label">Deadline</span>',
                        '        <span class="stat-value">~Jan 12, 2027</span>',
                        '        <span class="stat-note">Estimated; confirm on sponsor site</span>',
                        "      </div>",
                        "    </div>",
                    ]
                ),
                snippet_lines(
                    [
                        '<p class="verification-source detail-verification">',
                        "",
                        '        Verified Jul 6, 2026 \u00b7 <a href="https://www.jfklibrary.org/learn/education/profile-in-courage-essay-contest/recognition-and-awards" rel="noopener noreferrer">View official source</a>',
                        "",
                        "    </p>",
                    ]
                ),
            ),
        ],
    )
    def test_visible_fact_dom_stays_byte_locked(
        self, client, path, expected_stats, expected_verification
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert normalized_snippet(first_match(response.text, self.CARD_STATS_RE)) == expected_stats
        assert normalized_snippet(first_match(response.text, self.VERIFICATION_RE)) == expected_verification


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
            Path("app/static/privacy.html"),
            Path("app/static/terms.html"),
            Path("app/static/css/style.css"),
            Path("app/static/css/world.css"),
            Path("app/static/js/app.js"),
            *Path("app/data").glob("*.json"),
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


class TestStageCohesion:
    """Stage C cohesion gates: colors flow through tokens, and every
    versioned URL a script constructs stays in cache-bust lockstep."""

    HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    # The one legitimate CSS hex outside token definitions and mask ramps:
    # the trail's SVG mask stroke is literal white by definition of a mask.
    CSS_HEX_ALLOWLIST = {"stroke: #fff;"}

    @pytest.mark.parametrize("name", ["style.css", "world.css"])
    def test_stage1_css_gzip_caps_hold(self, name):
        path = Path(f"app/static/css/{name}")
        size = len(gzip.compress(path.read_bytes()))
        assert size <= CSS_GZIP_CAPS[name], (name, size, CSS_GZIP_CAPS[name])

    def test_stage1_repeated_card_added_nodes_stay_capped(self):
        text = Path("app/static/js/app.js").read_text(encoding="utf-8")
        deltas = {}
        for function_name in CARD_NODE_BUILDERS:
            body = js_function_body(text, function_name)
            assert "ec-paper-card" in body
            deltas[function_name] = len(
                re.findall(r"document\.createElementNS\(|buildChromeUse\(", body)
            )
        assert all(delta <= 6 for delta in deltas.values()), (
            CARD_NODE_COUNT_METHOD,
            deltas,
        )

    @pytest.mark.parametrize(
        "route",
        ["/", "/browse", "/scholarships/dell-scholars", "/privacy", "/terms"],
    )
    def test_stage1_svg_defs_emit_once_and_are_namespaced(self, client, route):
        response = client.get(route)
        assert response.status_code == 200
        assert response.text.count('id="ec-chrome-defs"') == 1
        symbol_ids = re.findall(r'<symbol id="([^"]+)"', response.text)
        assert symbol_ids
        assert len(symbol_ids) == len(set(symbol_ids))
        assert all(symbol_id.startswith("ec-") for symbol_id in symbol_ids)

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
        "name", ["app.js", "journey.js", "journey-teaser.js"]
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
        "name", ["app.js", "journey.js", "journey-teaser.js"]
    )
    def test_js_never_carries_css_hex_strings(self, name):
        text = Path(f"app/static/js/{name}").read_text(encoding="utf-8")
        assert not re.search(r"['\"]#[0-9a-fA-F]{3,8}['\"]", text), name

    def test_three_palette_literals_stay_in_journey_scenes(self):
        text = Path("app/static/js/app.js").read_text(encoding="utf-8")
        assert not re.search(r"0x[0-9a-fA-F]{6}", text)
