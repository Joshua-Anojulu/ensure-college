import pytest

from tests.e2e.test_e2e import fill_profile_and_submit, save_first_result, signup


HIT_TARGET_SCRIPT = (
    '(selector) => {'
    ' const el = document.querySelector(selector);'
    ' if (!el) return "missing:" + selector;'
    ' el.scrollIntoView({ block: "center", inline: "center", behavior: "instant" });'
    " const r = el.getBoundingClientRect();"
    ' if (r.width <= 0 || r.height <= 0) return "empty:" + selector;'
    " const x = Math.min(Math.max(r.left + r.width / 2, 1), window.innerWidth - 1);"
    " const y = Math.min(Math.max(r.top + r.height / 2, 1), window.innerHeight - 1);"
    " const labels = el.labels ? Array.from(el.labels) : [];"
    " const ownsHit = (hit) => hit && (el === hit || el.contains(hit) || hit.contains(el) ||"
    " labels.some((label) => label.contains(hit) || hit.contains(label)));"
    " const points = [[0.5, 0.5], [0.18, 0.25], [0.82, 0.25], [0.18, 0.75], [0.82, 0.75]];"
    " for (const point of points) {"
    " const px = Math.min(Math.max(r.left + r.width * point[0], 1), window.innerWidth - 1);"
    " const py = Math.min(Math.max(r.top + r.height * point[1], 1), window.innerHeight - 1);"
    " if (ownsHit(document.elementFromPoint(px, py))) return true;"
    " }"
    " const hit = document.elementFromPoint(x, y);"
    ' return hit ? hit.outerHTML.slice(0, 120) : "null";'
    "}"
)


def assert_hit_target(page, selector):
    locator = page.locator(selector).first
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    result = page.evaluate(HIT_TARGET_SCRIPT, selector)
    assert result is True, f"{selector} intercepted by: {result}"


@pytest.mark.parametrize("width", [1280, 375])
def test_stage1_chrome_keeps_repeated_controls_hit_testable(browser, live_server, width):
    context = browser.new_context(
        viewport={"width": width, "height": 900},
        device_scale_factor=2 if width == 375 else 1,
    )
    context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
    page = context.new_page()
    try:
        page.goto(live_server, wait_until="domcontentloaded")

        signup(page)
        fill_profile_and_submit(page)
        page.wait_for_selector("#results-filters:not([hidden])", timeout=15000)

        for selector in (
            "#scholarship-search",
            "#filter-sort",
            "#filter-verified-only",
            "#filter-clear",
            "#results-container .btn-save",
            "#results-container .card-link",
        ):
            assert_hit_target(page, selector)

        save_first_result(page)
        page.evaluate("document.querySelector('#nav-plan-btn').click()")
        page.wait_for_selector("#saved-section:not([hidden])", timeout=15000)
        page.wait_for_selector("#saved-container .match-card", timeout=15000)

        for selector in (
            "#saved-container .tracker-status",
            "#saved-container .tracker-task",
            "#saved-container .card-link",
        ):
            assert_hit_target(page, selector)

    finally:
        context.close()
