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
