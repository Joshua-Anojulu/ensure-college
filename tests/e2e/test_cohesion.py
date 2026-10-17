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


def _rgb(css):
    """'rgb(1, 2, 3)' / 'rgba(1, 2, 3, 0.5)' / 'color(srgb r g b / a)' -> (r, g, b, a)."""
    css = css.strip()
    if css.startswith("color(srgb"):
        parts = css[len("color(srgb") : -1].replace("/", " ").split()
        vals = [float(v) for v in parts]
        return (vals[0] * 255, vals[1] * 255, vals[2] * 255, vals[3] if len(vals) > 3 else 1.0)
    parts = css[css.index("(") + 1 : -1].replace("/", " ").replace(",", " ").split()
    vals = [float(v) for v in parts]
    return (vals[0], vals[1], vals[2], vals[3] if len(vals) > 3 else 1.0)


def _luminance(rgb):
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2])


def contrast(a, b):
    """WCAG contrast ratio of two opaque colors (alpha composited onto b first)."""
    a, b = _rgb(a) if isinstance(a, str) else a, _rgb(b) if isinstance(b, str) else b
    alpha = a[3]
    a = tuple(a[i] * alpha + b[i] * (1 - alpha) for i in range(3))
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


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


# ------------------------------------------------- focus on dark bands


def _keyboard_focus(page, selector):
    """Focus via the keyboard so :focus-visible applies (a programmatic
    focus() after the consent click does not match it in Chromium)."""
    page.evaluate(
        "(s) => { const el = document.querySelector(s); el.scrollIntoView({block: 'center'}); el.focus(); }",
        selector,
    )
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    return page.evaluate(
        """(s) => {
          const el = document.querySelector(s);
          const st = getComputedStyle(el);
          return {visible: el === document.activeElement && el.matches(':focus-visible'),
                  style: st.outlineStyle, color: st.outlineColor};
        }""",
        selector,
    )


@pytest.mark.parametrize(
    "selector,band",
    [
        (".site-footer .footer-links a", ".site-footer"),
        (".journey-teaser-cta", ".teaser-painting::after"),
    ],
)
def test_focus_ring_reads_on_dark_bands(page, selector, band):
    """The brand-colored ring sat on the brand footer and the dusk teaser:
    keyboard focus there was invisible (1.0:1 against the footer)."""
    ring = _keyboard_focus(page, selector)
    assert ring["visible"] and ring["style"] != "none", ring
    if band.endswith("::after"):
        # The teaser CTA rides the dusk scrim, whose darkest stop is brand-strong.
        backdrop = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--brand-strong')")
        backdrop = page.evaluate(
            "(hex) => { const d = document.createElement('div'); d.style.color = hex;"
            " document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; }",
            backdrop.strip(),
        )
    else:
        backdrop = page.evaluate(f"getComputedStyle(document.querySelector('{band}')).backgroundColor")
    ratio = contrast(ring["color"], backdrop)
    assert ratio >= 3, f"{selector} focus ring {ring['color']} on {backdrop}: {ratio:.2f}:1"
