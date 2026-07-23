import os
from pathlib import Path

import pytest

from tests.e2e.test_e2e import fill_profile_and_submit, signup


pytestmark = pytest.mark.skipif(
    os.environ.get("STAGE1_VISUAL_QA") != "1",
    reason="Set STAGE1_VISUAL_QA=1 to capture Stage 1 visual QA.",
)

OUTPUT_DIR = Path(".handoff/phase2-qa/stage1")
VIEWPORTS = (375, 768, 1280)
STATIC_ROUTES = (
    ("browse-hub", "/browse"),
    ("browse-scholarships", "/browse/scholarships"),
    ("scholarship-detail", "/scholarships/dell-scholars"),
    ("program-detail", "/programs/promys"),
    ("competition-detail", "/competitions/profile-in-courage-essay-contest"),
    ("guides", "/guides/essays"),
    ("guide-detail", "/guides/essays/community-impact"),
    ("privacy", "/privacy"),
    ("terms", "/terms"),
    ("not-found", "/missing-stage1-route"),
)


def capture(page, name):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=OUTPUT_DIR / f"{name}.png", full_page=True)


def capture_control_states(page, width, scope):
    targets = (
        ("filters", ".results-filters"),
        ("save", ".btn-save"),
        ("status", ".tracker-status"),
        ("checklist", ".tracker-task"),
        ("card-link", ".card-link"),
        ("filter-clear", ".filter-clear"),
    )
    for label, selector in targets:
        locator = page.locator(selector).first
        if locator.count() == 0 or not locator.is_visible():
            continue
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(80)
        locator.hover()
        capture(page, f"{width}-{scope}-{label}-hover")
        locator.focus()
        capture(page, f"{width}-{scope}-{label}-focus")
        box = locator.bounding_box()
        if box is not None:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down()
            capture(page, f"{width}-{scope}-{label}-active")
            page.mouse.up()
        if selector in (".btn-save", ".filter-clear"):
            locator.evaluate("(el) => { el.disabled = true; }")
            capture(page, f"{width}-{scope}-{label}-disabled")
            locator.evaluate("(el) => { el.disabled = false; }")


def open_tab(page, selector):
    tab = page.locator(selector).first
    if tab.count() == 0 or not tab.is_visible():
        return
    tab.click()
    page.wait_for_timeout(250)


def test_stage1_visual_qa_matrix(browser, live_server):
    for width in VIEWPORTS:
        height = 820 if width == 375 else 900
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        capture(page, f"{width}-landing")
        signup(page)
        fill_profile_and_submit(page)
        page.wait_for_selector("#results-container .match-card")
        capture(page, f"{width}-scholarship-lane")
        capture_control_states(page, width, "scholarship-lane")
        open_tab(page, "#tab-programs")
        capture(page, f"{width}-program-lane")
        open_tab(page, "#tab-competitions")
        capture(page, f"{width}-competition-lane")
        open_tab(page, "#tab-catalog")
        capture(page, f"{width}-catalog")
        open_tab(page, "#tab-saved")
        capture(page, f"{width}-saved-plan")
        capture_control_states(page, width, "saved-plan")
        for slug, route in STATIC_ROUTES:
            page.goto(live_server + route, wait_until="networkidle")
            capture(page, f"{width}-{slug}")
            capture_control_states(page, width, slug)
        context.close()
