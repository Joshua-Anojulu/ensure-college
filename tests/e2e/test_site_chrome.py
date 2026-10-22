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


# ------------------------------------------------------------- one footer

FOOTER_LINKS = [
    ["Browse all opportunities", "/#browse"],
    ["Essay guides", "/guides/essays"],
    ["Privacy", "/privacy"],
    ["Terms", "/terms"],
    ["Report an issue", "https://github.com/Joshua-Anojulu/scholarship-matcher/issues/new"],
    ["Contact", "https://github.com/Joshua-Anojulu"],
]

FOOTER_PROBE = """() => {
  const footer = document.querySelector('.site-footer');
  const dusk = document.querySelector('.world-dusk');
  const img = dusk.querySelector('img');
  const size = (el) => { const b = el.getBoundingClientRect(); return [Math.round(b.width), Math.round(b.height)]; };
  const pick = (el, props) => { const c = getComputedStyle(el); return props.map((p) => c.getPropertyValue(p)); };
  return {
    links: Array.from(footer.querySelectorAll('.footer-links a')).map((a) => [a.textContent.trim(), a.getAttribute('href')]),
    copy: footer.querySelector(':scope > p:not(.footer-links)').innerText.trim(),
    footer: pick(footer, ['background-color', 'color', 'padding-top', 'padding-left', 'font-size', 'text-align']),
    link: pick(footer.querySelector('.footer-links a'), ['font-family', 'font-size', 'letter-spacing', 'text-transform', 'color']),
    mark: pick(footer.querySelector('.footer-mark'), ['font-size', 'color', 'font-weight']),
    footerWidth: size(footer)[0],
    dusk: size(dusk),
    duskShown: getComputedStyle(dusk).display !== 'none' && getComputedStyle(img).opacity === '1',
    duskLoaded: img.complete && img.naturalWidth > 0 && img.currentSrc.includes('dusk-treeline'),
    fireflies: dusk.querySelectorAll('.firefly').length,
    duskBeforeFooter: dusk.nextElementSibling === footer,
  };
}"""


def _wait_until(page, expression, timeout_ms=10000):
    """Poll from Python: the CSP blocks the poller wait_for_function injects."""
    elapsed = 0
    while elapsed <= timeout_ms:
        if page.evaluate(expression):
            return
        page.wait_for_timeout(200)
        elapsed += 200
    raise AssertionError(f"never became true within {timeout_ms}ms: {expression}")


def _bottom_probe(page):
    page.evaluate("window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})")
    _wait_until(
        page,
        "(() => { const i = document.querySelector('.world-dusk img');"
        " return i.complete && i.naturalWidth > 0 && getComputedStyle(i).opacity === '1'; })()",
    )
    return page.evaluate(FOOTER_PROBE)


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_one_footer_with_the_dusk_band_on_every_surface(browser, live_server, width, height):
    ctx = browser.new_context(viewport={"width": width, "height": height})
    ctx.add_init_script(CONSENT)
    page = ctx.new_page()
    found = {}
    page.goto(live_server, wait_until="load")
    found["landing"] = _bottom_probe(page)
    page.click("#nav-plan-btn")
    page.wait_for_selector("#saved-section:not([hidden])")
    found["plan"] = _bottom_probe(page)
    for name, path in SERVER_SURFACES:
        page.goto(f"{live_server}{path}", wait_until="load")
        found[name] = _bottom_probe(page)
    ctx.close()

    reference = found["landing"]
    assert reference["links"] == FOOTER_LINKS, reference["links"]
    assert reference["duskShown"] and reference["duskLoaded"], reference
    for name, probe in found.items():
        for key in ("links", "copy", "footer", "link", "mark", "footerWidth", "dusk", "fireflies"):
            assert probe[key] == reference[key], f"{width}px {name} footer {key}: {probe[key]} != {reference[key]}"
        assert probe["duskShown"] and probe["duskLoaded"], f"{width}px {name}: dusk band not painted"
        assert probe["duskBeforeFooter"], name


def test_server_dusk_band_is_lazy(browser, live_server):
    """The band is below the fold on a long page and waits for the scroll."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    dusk = []
    page.on("request", lambda r: dusk.append(r.url) if "dusk-treeline" in r.url else None)
    page.goto(f"{live_server}/browse/scholarships", wait_until="networkidle")
    assert dusk == [], dusk
    page.evaluate("window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})")
    _wait_until(page, "document.querySelector('.world-dusk img').complete")
    assert len(dusk) == 1, dusk
    ctx.close()


@pytest.mark.parametrize(
    "kwargs,paths",
    [
        # Per-request pages reflect the Save-Data header as html.save-data.
        ({"extra_http_headers": {"Save-Data": "on"}}, ["/", "/privacy", "/journey", "/reminders/unsubscribe?token=x"]),
        ({"forced_colors": "active"}, ["/", "/scholarships/coca-cola-scholars", "/terms"]),
    ],
    ids=["save-data", "forced-colors"],
)
def test_dusk_band_yields_to_save_data_and_forced_colors(browser, live_server, kwargs, paths):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, **kwargs)
    ctx.add_init_script(CONSENT)
    page = ctx.new_page()
    dusk = []
    page.on("request", lambda r: dusk.append(r.url) if "dusk-treeline" in r.url else None)
    for path in paths:
        page.goto(f"{live_server}{path}", wait_until="load")
        page.evaluate("window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})")
        page.wait_for_timeout(600)
        assert page.evaluate("getComputedStyle(document.querySelector('.world-dusk')).display") == "none", path
        assert page.locator(".site-footer .footer-links a").count() == len(FOOTER_LINKS), path
    assert dusk == [], dusk
    ctx.close()
