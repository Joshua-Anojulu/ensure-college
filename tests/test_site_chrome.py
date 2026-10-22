"""One chrome on every page (2026-10-22 painted-forest unification, scope A).

Every surface carries the same header: the same brand block and the same
Sections nav (Matches, Plan, Browse, How it works) in the same order. The
right side stays page-appropriate: the app keeps its account controls, and
every server-rendered page keeps one solid "Find my matches". These checks
read the served HTML, so a page that drifts from the shared markup fails
here before it ever reaches a browser.
"""
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

NAV_LABELS = ["Matches", "Plan", "Browse", "How it works"]
SERVER_NAV = [
    ("Matches", "/#matches"),
    ("Plan", "/#plan"),
    ("Browse", "/#browse"),
    ("How it works", "/journey"),
]
SERVER_PAGES = [
    "/scholarships/coca-cola-scholars",
    "/programs/summer-science-program",
    "/browse",
    "/browse/scholarships",
    "/guides/essays",
    "/guides/essays/identity",
    "/scholarships/does-not-exist",
    "/privacy",
    "/terms",
    "/journey",
    "/reminders/unsubscribe?token=chrome-check",
]


class HeaderParser(HTMLParser):
    """Collects the brand, nav and right-side controls of .site-header."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0  # >0 while inside <header class="site-header">
        self.stack = []
        self.brand = None
        self.brand_text = []
        self.nav = None
        self.nav_items = []
        self.right = []
        self._current = None
        self._region = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        if tag == "header" and "site-header" in classes:
            self.depth = 1
            return
        if not self.depth:
            return
        self.stack.append((tag, self._region))
        if "brand" in classes and tag == "a":
            self._region = "brand"
            self.brand = {"href": attrs.get("href"), "aria-label": attrs.get("aria-label")}
        elif "site-nav" in classes:
            self._region = "nav"
            self.nav = {"tag": tag, "aria-label": attrs.get("aria-label")}
        elif "account-nav" in classes:
            self._region = "right"
        if tag in ("a", "button") and self._region in ("nav", "right"):
            self._current = {
                "tag": tag,
                "href": attrs.get("href"),
                "class": " ".join(sorted(classes)),
                "id": attrs.get("id"),
                "aria-current": attrs.get("aria-current"),
                "text": [],
            }

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == "header" and not self.stack:
            self.depth = 0
            return
        if self._current is not None and tag == self._current["tag"]:
            self._current["text"] = " ".join(" ".join(self._current["text"]).split())
            (self.nav_items if self._region == "nav" else self.right).append(self._current)
            self._current = None
        while self.stack:
            opened, region = self.stack.pop()
            if opened == tag:
                self._region = region
                break

    def handle_data(self, data):
        if not self.depth:
            return
        if self._region == "brand":
            self.brand_text.append(data)
        if self._current is not None:
            self._current["text"].append(data)


def parse_header(html):
    parser = HeaderParser()
    parser.feed(html)
    assert parser.brand is not None, "no .site-header brand link"
    parser.brand["text"] = " ".join(" ".join(parser.brand_text).split())
    return parser


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("path", SERVER_PAGES)
def test_server_pages_share_one_header(client, path):
    response = client.get(path)
    assert response.status_code in (200, 404), path
    header = parse_header(response.text)
    assert header.brand == {
        "href": "/",
        "aria-label": "EnsureCollege home",
        "text": "EnsureCollege Your whole college plan",
    }, path
    assert header.nav == {"tag": "nav", "aria-label": "Sections"}, path
    assert [(item["text"], item["href"]) for item in header.nav_items] == SERVER_NAV, path
    assert all(item["tag"] == "a" and item["class"] == "btn-ghost" for item in header.nav_items), path
    assert [(item["text"], item["href"], item["class"]) for item in header.right] == [
        ("Find my matches", "/#profile-form", "btn-ghost btn-ghost-solid")
    ], path


def test_unsubscribe_completion_page_shares_the_header(client):
    response = client.post("/reminders/unsubscribe", data={"token": "chrome-check"})
    assert response.status_code == 200
    header = parse_header(response.text)
    assert [(item["text"], item["href"]) for item in header.nav_items] == SERVER_NAV
    assert [item["text"] for item in header.right] == ["Find my matches"]


def test_only_the_journey_marks_how_it_works_as_current(client):
    for path in SERVER_PAGES:
        header = parse_header(client.get(path).text)
        current = [item["text"] for item in header.nav_items if item["aria-current"]]
        assert current == (["How it works"] if path == "/journey" else []), path


def test_app_header_carries_the_same_brand_and_nav():
    """The app's nav switches views in place (buttons app.js wires by id),
    so it is compared by label, order and class rather than by href."""
    index = Path(__file__).resolve().parents[1] / "app" / "static" / "index.html"
    header = parse_header(index.read_text(encoding="utf-8"))
    assert header.brand == {
        "href": "/",
        "aria-label": "EnsureCollege home",
        "text": "EnsureCollege Your whole college plan",
    }
    assert header.nav == {"tag": "nav", "aria-label": "Sections"}
    assert [item["text"] for item in header.nav_items] == NAV_LABELS
    assert all(item["class"] == "btn-ghost" for item in header.nav_items)
    assert [item["id"] for item in header.nav_items[:3]] == [
        "nav-matches-btn",
        "nav-plan-btn",
        "nav-browse-btn",
    ]
    assert header.nav_items[3]["href"] == "/journey"
    # Signed out, the solid action sits where the server pages' one does.
    solid = [item for item in header.right if "btn-ghost-solid" in item["class"].split()]
    assert [(item["id"], item["class"]) for item in solid] == [
        ("open-signup", "btn-ghost btn-ghost-solid")
    ]


FOOTER_LINKS = [
    ("Browse all opportunities", "/#browse"),
    ("Essay guides", "/guides/essays"),
    ("Privacy", "/privacy"),
    ("Terms", "/terms"),
    ("Report an issue", "https://github.com/Joshua-Anojulu/scholarship-matcher/issues/new"),
    ("Contact", "https://github.com/Joshua-Anojulu"),
]
FOOTER_COPY = (
    "EnsureCollege helps you plan your path to college. Confirm every deadline "
    "and requirement on the official sponsor page before you apply."
)
DUSK_760 = "/static/img/world/dusk-treeline-760.d1d890d8bc.webp"
DUSK_1376 = "/static/img/world/dusk-treeline-1376.8551cabfa9.webp"


class FooterParser(HTMLParser):
    """The dusk band's image and the site footer's mark, copy and links."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_dusk = 0
        self.dusk_img = None
        self.dusk_then_footer = False
        self.in_footer = False
        self.mark = []
        self.copy = []
        self.links = []
        self._where = None
        self._link = None
        self._last_closed_dusk = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        if "world-dusk" in classes:
            self.in_dusk = 1
            return
        if self.in_dusk:
            if tag == "img":
                self.dusk_img = attrs
            if tag == "div":
                self.in_dusk += 1
            return
        if tag == "footer" and "site-footer" in classes:
            self.in_footer = True
            self.dusk_then_footer = self._last_closed_dusk
            return
        if not self.in_footer:
            if tag not in ("script",):
                self._last_closed_dusk = False
            return
        if "footer-mark" in classes:
            self._where = "mark"
        elif tag == "p" and "footer-links" not in classes:
            self._where = "copy"
        elif tag == "a":
            self._link = {"href": attrs.get("href"), "target": attrs.get("target"), "text": []}

    def handle_endtag(self, tag):
        if self.in_dusk:
            if tag == "div":
                self.in_dusk -= 1
                if not self.in_dusk:
                    self._last_closed_dusk = True
            return
        if not self.in_footer:
            return
        if tag == "footer":
            self.in_footer = False
        elif tag == "a" and self._link is not None:
            self.links.append((" ".join("".join(self._link["text"]).split()), self._link["href"]))
            self._link = None
        elif tag in ("span", "p"):
            self._where = None

    def handle_data(self, data):
        if not self.in_footer:
            return
        if self._link is not None:
            self._link["text"].append(data)
        elif self._where == "mark":
            self.mark.append(data)
        elif self._where == "copy":
            self.copy.append(data)


def parse_footer(html):
    parser = FooterParser()
    parser.feed(html)
    return parser


def _assert_shared_footer(footer, where):
    assert "".join(footer.mark).strip() == "EnsureCollege", where
    assert " ".join(" ".join(footer.copy).split()) == FOOTER_COPY, where
    assert footer.links == FOOTER_LINKS, where
    assert footer.dusk_then_footer, f"{where}: the dusk band must sit right before the footer"


@pytest.mark.parametrize("path", SERVER_PAGES)
def test_server_pages_share_one_footer_with_a_lazy_dusk_band(client, path):
    footer = parse_footer(client.get(path).text)
    _assert_shared_footer(footer, path)
    img = footer.dusk_img
    assert img is not None, path
    # No app.js on these pages: a native lazy image, never on the critical path.
    assert img.get("loading") == "lazy" and img.get("fetchpriority") == "low", (path, img)
    assert img.get("src") == DUSK_760, (path, img)
    assert img.get("srcset") == f"{DUSK_760} 760w, {DUSK_1376} 1376w", (path, img)
    assert img.get("alt") == "", path


def test_app_footer_is_the_same_footer():
    index = Path(__file__).resolve().parents[1] / "app" / "static" / "index.html"
    footer = parse_footer(index.read_text(encoding="utf-8"))
    _assert_shared_footer(footer, "index.html")
    # The app hydrates its plates itself (Save-Data aware): inert data-src.
    assert footer.dusk_img.get("data-src") == DUSK_1376
    assert "src" not in footer.dusk_img


def test_unsubscribe_pages_reflect_save_data(client):
    for response in (
        client.get("/reminders/unsubscribe?token=x", headers={"Save-Data": "on"}),
        client.post("/reminders/unsubscribe", data={"token": "x"}, headers={"Save-Data": "on"}),
    ):
        assert response.text.startswith('<!DOCTYPE html><html lang="en" class="save-data">')
    plain = client.get("/reminders/unsubscribe?token=x")
    assert "save-data" not in plain.text
