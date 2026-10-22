"""Transactional emails wear the site's Forest Light palette (2026-10-22).

The password-reset, deadline-reminder and new-match emails still used the
retired navy brand (#1b2430 mark, buttons and links on a warm #eae8e1
backdrop), and they disagreed about the "E" mark: a sans E on the reset
email, a Georgia serif E on the other two. All three now share one mark (the
site's forest tile, a light E and the gold dot of the header mark) and the
style.css palette, and every line of text reads at 4.5:1 or better.
"""
import re
from datetime import date, timedelta
from html.parser import HTMLParser

import pytest

from app.alerts import MatchRef, build_alert_email
from app.auth.email import EMAIL_MARK_HTML, _reset_email_html
from app.reminders import DueItem, build_reminder_email

# Forest Light tokens (app/static/css/style.css).
BRAND, BRAND_INK, ACCENT = "#1e4034", "#fbfcfa", "#c98d2c"
RETIRED = [
    "#1b2430",  # navy mark, buttons and links
    "#eae8e1",  # warm backdrop
    "#fbfaf7",
    "#ddd9cd",
    "#17181c",
    "#33373f",
    "#5c6069",
    "#83858c",
    "#b87c00",
    "#ece9df",
    "georgia",  # the serif E
]


def _emails():
    today = date(2026, 10, 22)
    items = [
        DueItem("Alpha Scholarship", "Scholarship", today, 0, "https://example.org/a"),
        DueItem("Beta Program", "Summer program", today + timedelta(days=3), 3, None),
    ]
    refs = [
        MatchRef("scholarship:a", "Alpha Scholarship", "Scholarship", "https://example.org/a"),
        MatchRef("program:b", "Beta Program", "Summer program", None),
    ]
    return {
        "reset": _reset_email_html("https://ensurecollege.com/?reset_token=abc"),
        "reminder": build_reminder_email(items, "tok")[2],
        "alert": build_alert_email(refs, "tok")[2],
    }


EMAILS = ["reset", "reminder", "alert"]


@pytest.mark.parametrize("name", EMAILS)
def test_email_drops_the_retired_navy_brand(name):
    html = _emails()[name].lower()
    for old in RETIRED:
        assert old not in html, f"{name} email still uses {old}"


def test_all_three_emails_wear_one_mark():
    mark = EMAIL_MARK_HTML.lower()
    # Forest tile, light E, gold dot.
    assert f'bgcolor="{BRAND}"' in mark
    assert f"color:{BRAND_INK}" in mark.replace(" ", "")
    assert f"color:{ACCENT}" in mark.replace(" ", "")
    for name, html in _emails().items():
        assert html.count(EMAIL_MARK_HTML) == 1, f"{name} email does not wear the shared mark"


@pytest.mark.parametrize("name", EMAILS)
def test_email_action_is_the_forest_button(name):
    html = _emails()[name].replace(" ", "").lower()
    assert f'bgcolor="{BRAND}"' in html or f"background:{BRAND}" in html or f"background-color:{BRAND}" in html
    # The call to action is light text on the forest fill.
    assert re.search(rf"<a[^>]*background(-color)?:{BRAND}[^>]*color:{BRAND_INK}", html) or re.search(
        rf'bgcolor="{BRAND}"[^>]*>\s*<a[^>]*color:{BRAND_INK}', html
    ), f"{name}: no forest button"


def _rgb(hex_color):
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _luminance(hex_color):
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = _rgb(hex_color)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(fg, bg):
    a, b = _luminance(fg), _luminance(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


_HEX = r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b"


class _TextRuns(HTMLParser):
    """Every visible text run with its inherited color and backdrop."""

    VOID = {"meta", "br", "img", "hr", "link", "input"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = [{"tag": "root", "color": "#000000", "bg": "#ffffff", "hidden": False}]
        self.runs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        style = (attrs.get("style") or "").lower()
        parent = self.stack[-1]
        node = dict(parent, tag=tag)
        color = re.search(rf"(?:^|;)\s*color\s*:\s*({_HEX})", style)
        if color:
            node["color"] = color.group(1)
        bg = re.search(rf"background(?:-color)?\s*:\s*({_HEX})", style)
        if attrs.get("bgcolor"):
            node["bg"] = attrs["bgcolor"]
        elif bg:
            node["bg"] = bg.group(1)
        if re.search(r"display\s*:\s*none", style) or tag in ("head", "title"):
            node["hidden"] = True
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        node = self.stack[-1]
        text = data.strip()
        # Punctuation-only runs (the mark's gold dot, middots) are decoration.
        if node["hidden"] or not re.search(r"[A-Za-z0-9]", text):
            return
        self.runs.append((text, node["color"], node["bg"]))


@pytest.mark.parametrize("name", EMAILS)
def test_every_line_of_email_text_reads_at_4_5_to_1(name):
    parser = _TextRuns()
    parser.feed(_emails()[name])
    assert parser.runs, name
    low = [
        (text, fg, bg, round(contrast(fg, bg), 2))
        for text, fg, bg in parser.runs
        if contrast(fg, bg) < 4.5
    ]
    assert not low, f"{name} email text below 4.5:1: {low}"
