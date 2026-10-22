"""Visual polish pass (2026-10-22, plan section P): pages look put together.

Josh asked for every page to "look put together": no random blank space and
nothing that looks unfinished. Each test here pins one defect measured on
main before the pass and fails on that code.
"""
import pytest

CONSENT = "window.localStorage.setItem('site_consent_v1', 'yes');"


def _context(browser, width, height, **kwargs):
    ctx = browser.new_context(viewport={"width": width, "height": height}, **kwargs)
    ctx.add_init_script(CONSENT)
    return ctx


def _wait_until(page, expression, timeout_ms=10000):
    """Poll from Python: the CSP blocks the poller wait_for_function injects."""
    elapsed = 0
    while elapsed <= timeout_ms:
        if page.evaluate(expression):
            return
        page.wait_for_timeout(200)
        elapsed += 200
    raise AssertionError(f"never became true within {timeout_ms}ms: {expression}")


# ------------------------------------------------------- 1. page endings
#
# Every page ended with the dusk band (300px desktop / 160px phone) and the
# footer (372px / 269px, its ghost wordmark set at 112px / 45px): 672px, 75%
# of a laptop screen, was decoration. On short pages (404, unsubscribe, the
# Browse index) the real content was a sliver at the top of the page.

# Where the flag stands in dusk-treeline-*.webp, as fractions of the
# painting's height: the pennant spans 0.551 to 0.590 and the pole's foot
# meets the hill near 0.69.
PENNANT_TOP = 0.551
POLE_FOOT = 0.69

ENDING = """() => {
  const band = document.querySelector('.world-dusk');
  const img = band.querySelector('img');
  const footer = document.querySelector('footer.site-footer');
  const header = document.querySelector('.site-header');
  const main = document.querySelector('main');
  const lone = main.querySelector(':scope > .panel:only-child');
  const box = img.getBoundingClientRect();
  // object-fit: cover, so the painting scales to cover the band and the
  // band shows a horizontal slice of it set by object-position.
  const scale = Math.max(box.width / img.naturalWidth, box.height / img.naturalHeight);
  const drawn = img.naturalHeight * scale;
  const [, y] = getComputedStyle(img).objectPosition.split(' ');
  const offset = y.endsWith('%') ? (drawn - box.height) * parseFloat(y) / 100 : -parseFloat(y);
  const r = (el) => el.getBoundingClientRect();
  return {
    band: Math.round(r(band).height),
    footer: Math.round(r(footer).height),
    mark: parseFloat(getComputedStyle(footer.querySelector('.footer-mark')).fontSize),
    fullWidth: Math.abs(scale - box.width / img.naturalWidth) < 1e-6,
    drawn, offset, bandH: box.height,
    doc: document.documentElement.scrollHeight,
    footerBottom: r(footer).bottom + scrollY,
    headerBottom: r(header).bottom + scrollY,
    bandTop: r(band).top + scrollY,
    lone: lone ? [r(lone).top + scrollY, r(lone).bottom + scrollY] : null,
  };
}"""


def _ending(page):
    page.evaluate("window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})")
    _wait_until(
        page,
        "(() => { const i = document.querySelector('.world-dusk img');"
        " return i.complete && i.naturalWidth > 0; })()",
    )
    return page.evaluate(ENDING)


SHORT_PAGES = [
    ("404", "/scholarships/no-such-entry"),
    ("unsubscribe", "/reminders/unsubscribe?token=e2e-polish"),
    ("browse", "/browse"),
]


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_page_ending_is_compact_and_keeps_the_flag(browser, live_server, width, height):
    ctx = _context(browser, width, height)
    page = ctx.new_page()
    desktop = width >= 1024
    for name, path in SHORT_PAGES + [("privacy", "/privacy"), ("landing", "/")]:
        page.goto(f"{live_server}{path}", wait_until="load")
        state = _ending(page)
        where = f"{width}px {name}"
        if desktop:
            assert 150 <= state["band"] <= 200, f"{where}: dusk band {state['band']}px"
            assert state["footer"] <= 200, f"{where}: footer {state['footer']}px"
            assert state["mark"] <= 28, f"{where}: footer wordmark {state['mark']}px"
        else:
            assert 96 <= state["band"] <= 120, f"{where}: dusk band {state['band']}px"
            assert state["footer"] <= 240, f"{where}: footer {state['footer']}px"
            assert state["mark"] <= 24, f"{where}: footer wordmark {state['mark']}px"
        # The ending stays well under half a screen.
        assert state["band"] + state["footer"] <= 0.45 * height, f"{where}: ending {state}"
        # The painting still reads: the flag's pennant clears the band's top
        # fade and the pole's foot on the hill stays inside the band.
        assert state["fullWidth"], f"{where}: the painting no longer spans the band"
        pennant = PENNANT_TOP * state["drawn"] - state["offset"]
        foot = POLE_FOOT * state["drawn"] - state["offset"]
        assert pennant >= 0.2 * state["bandH"], f"{where}: the flag sits in the top fade ({pennant:.0f}px)"
        assert foot <= state["bandH"], f"{where}: the flag's foot is cut off ({foot:.0f}px of {state['bandH']})"
    ctx.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_short_pages_fill_the_screen_and_center_a_lone_panel(browser, live_server, width, height):
    ctx = _context(browser, width, height)
    page = ctx.new_page()
    fits = [("404", "/scholarships/no-such-entry"), ("unsubscribe", "/reminders/unsubscribe?token=e2e-polish")]
    if width >= 1024:
        fits.append(("browse", "/browse"))
    for name, path in fits:
        page.goto(f"{live_server}{path}", wait_until="load")
        state = _ending(page)
        where = f"{width}px {name}"
        # The page is one screen and the footer closes it at the bottom edge.
        assert state["doc"] <= height, f"{where}: {state['doc']}px tall in a {height}px window"
        assert abs(state["footerBottom"] - height) <= 1, f"{where}: footer ends at {state['footerBottom']}"
        if name != "browse":
            # A lone panel sits in the middle of the space it has, not at the
            # top of an empty stretch of page.
            top, bottom = state["lone"]
            above, below = top - state["headerBottom"], state["bandTop"] - bottom
            assert min(above, below) >= 16, f"{where}: panel {above:.0f}px below the header, {below:.0f}px above the band"
            assert abs(above - below) <= 24, f"{where}: panel off center ({above:.0f} above, {below:.0f} below)"
    ctx.close()

