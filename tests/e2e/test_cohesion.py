"""UI cohesion pass (2026-10-17): regressions the request suite cannot see.

Each group pins one visible defect found in the audit: layouts that scrolled
sideways on phones, focus rings that vanished on dark surfaces, text that
rode illustrated art below WCAG contrast, and components that drifted from
the Forest Light system.
"""
import time

import pytest

from tests.e2e.test_e2e import fill_profile_and_submit

CONSENT = "window.localStorage.setItem('site_consent_v1', 'yes');"
SIDEWAYS = "() => document.documentElement.scrollWidth - window.innerWidth"


def _context(browser, width, height=844, **kwargs):
    ctx = browser.new_context(viewport={"width": width, "height": height}, **kwargs)
    ctx.add_init_script(CONSENT)
    return ctx


def _sign_up(page):
    page.wait_for_selector("#auth-logged-out:not([hidden])")
    page.click("#open-signup")
    page.wait_for_selector("#auth-modal[open]")
    page.fill("#auth-email", f"cohesion-{int(time.time() * 1000)}@example.com")
    page.fill("#auth-password", "cohesion-password-123")
    page.click("#auth-submit")
    page.wait_for_selector("#auth-logged-in:not([hidden])", timeout=15000)


# ------------------------------------------------- no sideways scroll


TEMPLATE_PAGES = [
    "/browse/competitions",
    "/browse/programs",
    "/scholarships/coca-cola-scholars",
    "/guides/essays",
    "/journey",
    "/privacy",
    "/scholarships/does-not-exist",
]


@pytest.mark.parametrize("width", [320, 390, 1440])
def test_template_family_never_scrolls_sideways(browser, live_server, width):
    """The template header's three links wrapped into stacked fragments and
    pushed every Opportunity page 10-80px wide on phones, and directory meta
    (a competition's whole recognition paragraph, nowrap) ran 3000px wide."""
    ctx = _context(browser, width, reduced_motion="reduce")
    page = ctx.new_page()
    for path in TEMPLATE_PAGES:
        page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
        assert page.evaluate(SIDEWAYS) <= 0, f"{path} scrolls sideways at {width}px"
    ctx.close()


@pytest.mark.parametrize("width", [390, 1440])
def test_directory_meta_wraps_inside_the_list(browser, live_server, width):
    ctx = _context(browser, width)
    page = ctx.new_page()
    for kind in ("competitions", "programs"):
        page.goto(f"{live_server}/browse/{kind}", wait_until="domcontentloaded")
        escaped = page.evaluate(
            """() => {
              const list = document.querySelector('.browse-list').getBoundingClientRect();
              return Array.from(document.querySelectorAll('.browse-row-meta'))
                .filter((m) => m.getBoundingClientRect().right > list.right + 1).length;
            }"""
        )
        assert escaped == 0, f"{escaped} {kind} rows push their meta outside the list"
    ctx.close()


def test_signed_in_header_fits_a_phone(browser, live_server):
    ctx = _context(browser, 390)
    page = ctx.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    _sign_up(page)
    # Widest case: a saved-count bubble beside Saved.
    page.evaluate(
        "() => { const c = document.getElementById('saved-count'); c.hidden = false; c.textContent = '12'; }"
    )
    assert page.evaluate(SIDEWAYS) <= 0
    heights = page.eval_on_selector_all(
        "#auth-logged-in button", "els => els.map((b) => b.getBoundingClientRect().height)"
    )
    assert heights and max(heights) < 48, f"an account button wrapped to two lines: {heights}"
    # The brand link keeps its accessible name while the wordmark yields.
    assert page.get_attribute(".site-header .brand-link", "aria-label") == "EnsureCollege home"
    ctx.close()


def test_stacked_quick_apply_rows_share_one_left_edge(browser, live_server):
    """Below 760px rows stack; centering them staggered every row's edge."""
    ctx = _context(browser, 390)
    page = ctx.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    fill_profile_and_submit(page)
    page.click("#tab-saved")
    page.wait_for_selector("#quick-applies-list .quick-apply-row", timeout=15000)
    offsets = page.eval_on_selector_all(
        "#quick-applies-list .quick-apply-row",
        """rows => rows.map((row) => {
          const left = row.querySelector('.quick-apply-left').getBoundingClientRect().left;
          const link = row.querySelector('.quick-apply-link').getBoundingClientRect().left;
          return Math.round(Math.abs(left - link));
        })""",
    )
    assert offsets and max(offsets) <= 1, f"row parts start at different edges: {offsets}"
    ctx.close()
