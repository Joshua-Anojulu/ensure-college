"""One chrome, one frame, one panel system (2026-10-22 painted-forest pass).

The owner's complaint was that the site did not feel like one thing: the app,
the template family, the Journey, the legal pages and the unsubscribe pages
each wore their own header. These gates drive every surface in a real browser
and require the header to be the same thing everywhere: same labels in the
same order, same computed style, same position, at desktop and phone widths.
"""
import pytest

from tests.e2e.test_e2e import fill_profile_and_submit

CONSENT = "window.localStorage.setItem('site_consent_v1', 'yes');"
NAV = ["Matches", "Plan", "Browse", "How it works"]

SERVER_SURFACES = [
    ("opportunity", "/scholarships/coca-cola-scholars"),
    ("browse", "/browse/scholarships"),
    ("guide", "/guides/essays/identity"),
    ("privacy", "/privacy"),
    ("terms", "/terms"),
    ("journey", "/journey"),
    ("404", "/scholarships/does-not-exist"),
    ("unsubscribe", "/reminders/unsubscribe?token=e2e-chrome"),
]

HEADER_PROBE = """() => {
  const pick = (el, props) => {
    const s = getComputedStyle(el);
    return Object.fromEntries(props.map((p) => [p, s.getPropertyValue(p)]));
  };
  const box = (el) => {
    const r = el.getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
  };
  const header = document.querySelector('.site-header');
  const brand = header.querySelector('.brand');
  const items = Array.from(header.querySelectorAll('.site-nav > *'));
  const solid = Array.from(header.querySelectorAll('.btn-ghost-solid'))
    .find((el) => el.getClientRects().length);
  const itemStyle = ['font-family', 'font-size', 'font-weight', 'color', 'padding-top',
    'padding-right', 'padding-bottom', 'padding-left', 'border-top-left-radius',
    'background-color', 'height', 'letter-spacing'];
  return {
    brand: brand.innerText.replace(/\\s+/g, ' ').trim(),
    brandBox: box(brand),
    headerHeight: Math.round(header.getBoundingClientRect().height),
    headerBg: getComputedStyle(header).backgroundColor,
    labels: items.map((el) => el.innerText.trim()),
    current: items.map((el) => el.hasAttribute('aria-current')),
    clientWidth: document.documentElement.clientWidth,
    visible: items.every((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.left >= 0 && r.right <= innerWidth + 0.5;
    }),
    navBox: box(header.querySelector('.site-nav')),
    itemBoxes: items.map(box),
    itemStyles: items.map((el) => pick(el, itemStyle)),
    solid: solid ? pick(solid, itemStyle.concat(['border-top-width'])) : null,
    sideways: document.documentElement.scrollWidth - innerWidth,
  };
}"""


def _settle(page):
    # Park the pointer off the header: a click leaves its button hovered.
    size = page.viewport_size
    page.mouse.move(size["width"] - 2, size["height"] - 2)
    # fonts.ready can resolve before a face nobody has asked for yet; load
    # the header's faces explicitly so every page is measured on web fonts.
    page.evaluate(
        """() => Promise.all([
          document.fonts.load('800 20px "Cabinet Grotesk"'),
          document.fonts.load('700 14px Satoshi'),
          document.fonts.load('500 12px Satoshi'),
          document.fonts.load('400 14px Satoshi'),
        ]).catch(() => null).then(() => document.fonts.ready).then(() => true)"""
    )
    page.wait_for_timeout(250)


def _probe_everywhere(browser, live_server, width, height):
    ctx = browser.new_context(viewport={"width": width, "height": height})
    ctx.add_init_script(CONSENT)
    page = ctx.new_page()
    found = {}

    page.goto(live_server, wait_until="load")
    page.wait_for_selector("#auth-logged-out:not([hidden])")
    _settle(page)
    found["landing"] = page.evaluate(HEADER_PROBE)

    page.click("#nav-plan-btn")
    page.wait_for_selector("#saved-section:not([hidden])")
    _settle(page)
    found["plan"] = page.evaluate(HEADER_PROBE)

    page.goto(live_server, wait_until="load")
    page.wait_for_selector("#auth-logged-out:not([hidden])")
    fill_profile_and_submit(page)
    _settle(page)
    found["results"] = page.evaluate(HEADER_PROBE)

    for name, path in SERVER_SURFACES:
        page.goto(f"{live_server}{path}", wait_until="load")
        _settle(page)
        found[name] = page.evaluate(HEADER_PROBE)
    ctx.close()
    return found


def _assert_one_header(found, where):
    reference = found["landing"]
    assert reference["labels"] == NAV, (where, reference["labels"])
    for name, probe in found.items():
        assert probe["labels"] == NAV, (where, name, probe["labels"])
        assert probe["visible"], f"{where}: a nav item on {name} is cut off: {probe['itemBoxes']}"
        assert probe["sideways"] <= 0, f"{where}: {name} scrolls sideways by {probe['sideways']}px"
        for key in ("brand", "brandBox", "headerHeight", "headerBg", "navBox", "itemBoxes"):
            assert probe[key] == reference[key], f"{where}: {name} {key} {probe[key]} != landing {reference[key]}"
        for index, (style, current) in enumerate(zip(probe["itemStyles"], probe["current"])):
            style, expected = dict(style), dict(reference["itemStyles"][index])
            if current:  # the Journey marks its own item in brand color
                style.pop("color")
                expected.pop("color")
            assert style == expected, f"{where}: {name} nav item {index} {style} != {expected}"
        # The right side differs by page (account controls or one CTA), but
        # the solid action is the same button either way.
        assert probe["solid"] == reference["solid"], f"{where}: {name} solid action {probe['solid']}"


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844), (320, 640)])
def test_one_header_on_every_surface(browser, live_server, width, height):
    """Same brand, same nav labels in the same order, same computed style
    and position, and the same solid action on the app (landing, results,
    plan) and on every server-rendered page."""
    found = _probe_everywhere(browser, live_server, width, height)
    _assert_one_header(found, f"{width}px")
    landing = found["landing"]
    nav_top, brand_bottom = landing["navBox"][1], landing["brandBox"][1] + landing["brandBox"][3]
    if width < 1024:
        # One phone behavior everywhere: the nav is the header's second row.
        assert nav_top >= brand_bottom - 1, (nav_top, brand_bottom)
    else:
        assert nav_top < brand_bottom, (nav_top, brand_bottom)
        # Centered in the header whatever sits on its right.
        left, _top, w, _h = landing["navBox"]
        assert abs((left + w / 2) - landing["clientWidth"] / 2) <= 2, landing["navBox"]


def test_header_fits_320_on_the_fallback_font(browser, live_server):
    """Web fonts can arrive late or never; the shared header must fit a
    320px phone on the fallback font too."""
    ctx = browser.new_context(viewport={"width": 320, "height": 640})
    ctx.add_init_script(CONSENT)
    ctx.route("**/*.woff2", lambda route: route.abort())
    page = ctx.new_page()
    for path in ["/", "/privacy", "/scholarships/coca-cola-scholars", "/journey"]:
        page.goto(f"{live_server}{path}", wait_until="load")
        probe = page.evaluate(HEADER_PROBE)
        assert probe["labels"] == NAV, path
        assert probe["visible"] and probe["sideways"] <= 0, (path, probe["itemBoxes"], probe["sideways"])
    ctx.close()


def test_server_nav_deep_links_open_the_app_views(page, live_server):
    """Plan, Matches and Browse on a server page open those views in the
    app, and the hash is consumed so a refresh returns to the landing."""
    page.goto(f"{live_server}/privacy", wait_until="load")
    page.click('.site-nav a[href="/#plan"]')
    page.wait_for_selector("#saved-section:not([hidden])", timeout=15000)
    page.wait_for_selector("#saved-signed-out:not([hidden])")
    assert page.evaluate("location.hash") == ""

    page.goto(f"{live_server}/guides/essays", wait_until="load")
    page.click('.site-nav a[href="/#matches"]')
    page.wait_for_url(f"{live_server}/")
    page.wait_for_function(
        "() => { const t = document.getElementById('profile-form').getBoundingClientRect().top;"
        " return t > 0 && t < 260; }",
        timeout=15000,
    )
    assert page.evaluate("location.hash") == ""

    page.goto(f"{live_server}/scholarships/coca-cola-scholars", wait_until="load")
    page.click('.site-nav a[href="/#browse"]')
    page.wait_for_selector("#catalog-section:not([hidden])", timeout=15000)
    assert page.evaluate("location.hash") == ""
    assert not page.console_errors, page.console_errors


def test_in_page_deep_links_switch_views_without_a_reload(page):
    """The footer's /#browse link on the app itself used to change only the
    URL; hash changes now open the view too."""
    page.evaluate("window.__sameDocument = true")
    page.locator('.site-footer a[href="/#browse"]').click()
    page.wait_for_selector("#catalog-section:not([hidden])", timeout=15000)
    assert page.evaluate("window.__sameDocument === true"), "the link reloaded the page"
    assert page.evaluate("location.hash") == ""
