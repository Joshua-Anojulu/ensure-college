"""Stage A world-layer behavior, driven in a real browser.

Covers the Phase 1 plan's gates: plates hydrate without intercepting input,
Save-Data suppresses every world request, fireflies pause off-viewport and
under reduced motion, the Trail rests fully drawn without scroll-timeline
support or with reduced motion, and the hero preload never double-fetches.
"""
import pytest


def wait_until(page, expression, timeout_ms=10000):
    """Poll an expression via page.evaluate.

    The site's CSP (script-src 'self' + consent-boot hash, no unsafe-eval)
    blocks the poller Playwright injects for wait_for_function, so any
    predicate that is not true on its very first evaluation raises EvalError.
    page.evaluate uses a CSP-exempt protocol path, so we poll from Python.
    """
    elapsed = 0
    while elapsed <= timeout_ms:
        if page.evaluate(expression):
            return
        page.wait_for_timeout(250)
        elapsed += 250
    raise AssertionError(f"never became true within {timeout_ms}ms: {expression}")


def _hit_is_inside(page, selector):
    """elementFromPoint at the control's center resolves inside the control."""
    return page.evaluate(
        """(selector) => {
          const el = document.querySelector(selector);
          if (!el) return 'missing:' + selector;
          const r = el.getBoundingClientRect();
          const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
          return hit && (el === hit || el.contains(hit) || hit.contains(el))
            ? true
            : (hit ? hit.outerHTML.slice(0, 120) : 'null');
        }""",
        selector,
    )


def show_last_stop(page):
    """Bring How it works' last stop (and its Build my profile button) on
    screen: the end of the runway when the device flies, the card itself in
    the static layout."""
    flying = page.evaluate("document.documentElement.classList.contains('journey-will-fly')")
    if flying:
        page.evaluate(
            """() => {
              const track = document.getElementById('journey-track');
              const stage = track.querySelector('.journey-stage');
              const top = track.getBoundingClientRect().top + window.scrollY;
              window.scrollTo({ top: top + track.offsetHeight - stage.offsetHeight, behavior: 'instant' });
            }"""
        )
        wait_until(page, "document.querySelectorAll('.journey-card')[3].classList.contains('is-active')", 15000)
    else:
        page.locator(".journey-card-cta").scroll_into_view_if_needed()
    page.wait_for_timeout(400)


def test_world_plates_hydrate_and_primary_controls_stay_clickable(page):
    # The numbers' clearing and leaves plus How it works' overlook painting.
    wait_until(page, "document.querySelectorAll('.world-plate img[src], .journey-painting img[src]').length >= 3")
    for selector in (
        "#preview-form button",
        "#preview-form input, #preview-form select",
        ".site-header a",
        ".hero-actions a, .hero-actions button",
    ):
        result = _hit_is_inside(page, selector)
        assert result is True, f"{selector} intercepted by: {result}"
    # Scroll the world sections into view and re-test below-fold controls.
    show_last_stop(page)
    result = _hit_is_inside(page, ".journey-card-cta")
    assert result is True, f".journey-card-cta intercepted by: {result}"
    page.locator(".footer-links a").first.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    result = _hit_is_inside(page, ".footer-links a")
    assert result is True, f".footer-links a intercepted by: {result}"


def test_primary_controls_clickable_on_mobile(browser, live_server):
    context = browser.new_context(
        viewport={"width": 412, "height": 823}, device_scale_factor=1.75
    )
    context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
    page = context.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    for selector in ("#preview-form button", ".hero-actions a, .hero-actions button"):
        # Hit-test where the control is on screen: the two-row phone header
        # (2026-10-22) puts the preview's submit just below an 823px fold.
        page.locator(selector).first.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        result = _hit_is_inside(page, selector)
        assert result is True, f"[mobile] {selector} intercepted by: {result}"
    show_last_stop(page)
    result = _hit_is_inside(page, ".journey-card-cta")
    assert result is True, f"[mobile] How it works CTA intercepted by: {result}"
    context.close()


def test_save_data_suppresses_every_world_asset_request(browser, live_server):
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        extra_http_headers={"Save-Data": "on"},
    )
    context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
    page = context.new_page()
    world_requests = []
    three_requests = []
    page.on(
        "request",
        lambda r: (
            world_requests.append(r.url) if "/static/img/world/" in r.url else None,
            three_requests.append(r.url) if "three.min.js" in r.url else None,
        ),
    )
    page.goto(live_server, wait_until="networkidle")
    assert page.evaluate("document.documentElement.classList.contains('save-data')")
    page.mouse.wheel(0, 30000)
    page.wait_for_timeout(1500)
    assert world_requests == [], world_requests
    # Header-only Save-Data (no JS channel) must still keep How it works
    # static: the dual-channel check reads the server-stamped class.
    assert page.evaluate(
        "document.documentElement.classList.contains('journey-static')"
    )
    assert three_requests == [], three_requests
    context.close()


def test_connection_savedata_js_channel_suppresses_world_requests(browser, live_server):
    """The client channel alone (navigator.connection.saveData, no header)."""
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.add_init_script(
        """
        window.localStorage.setItem('site_consent_v1', 'yes');
        const conn = navigator.connection || {};
        try {
          Object.defineProperty(conn, 'saveData', { get: () => true });
          if (!navigator.connection) {
            Object.defineProperty(navigator, 'connection', { get: () => conn });
          }
        } catch (e) {}
        """
    )
    page = context.new_page()
    world_requests = []
    three_requests = []
    page.on(
        "request",
        lambda r: (
            world_requests.append(r.url) if "/static/img/world/" in r.url else None,
            three_requests.append(r.url) if "three.min.js" in r.url else None,
        ),
    )
    page.goto(live_server, wait_until="networkidle")
    page.mouse.wheel(0, 30000)
    page.wait_for_timeout(1500)
    assert world_requests == [], world_requests
    # How it works rests on its static layout: no three.js (tracked in its
    # own list; the world list can never contain it).
    assert page.evaluate(
        "document.documentElement.classList.contains('journey-static')"
    )
    assert three_requests == [], three_requests
    context.close()


def test_focus_ring_stays_visible_over_world_art(page):
    show_last_stop(page)
    page.evaluate("document.querySelector('.journey-card-cta').focus()")
    outline = page.evaluate(
        """(() => {
          const el = document.querySelector('.journey-card-cta');
          const s = getComputedStyle(el);
          return { outline: s.outlineStyle, width: s.outlineWidth, shadow: s.boxShadow };
        })()"""
    )
    has_ring = outline["outline"] != "none" or outline["shadow"] != "none"
    assert has_ring, outline


def test_fireflies_twinkle_only_in_view(page):
    page.evaluate("document.querySelector('.world-dusk').scrollIntoView()")
    wait_until(
        page,
        "(() => { const f = document.querySelector('.fireflies'); return !!f && f.classList.contains('fireflies-live'); })()",
    )
    page.evaluate("window.scrollTo(0, 0)")
    wait_until(
        page,
        "(() => { const f = document.querySelector('.fireflies'); return !!f && !f.classList.contains('fireflies-live'); })()",
    )


def test_reduced_motion_keeps_fireflies_static_and_trail_drawn(browser, live_server):
    context = browser.new_context(
        viewport={"width": 1440, "height": 900}, reduced_motion="reduce"
    )
    context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
    page = context.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    page.locator(".world-dusk").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    assert not page.evaluate(
        "document.querySelector('.fireflies').classList.contains('fireflies-live')"
    )
    # The trail mask rests fully drawn: stroke-dashoffset must be 0.
    offsets = page.evaluate(
        """Array.from(document.querySelectorAll('.trail-reveal')).map(
             (el) => getComputedStyle(el).strokeDashoffset
           )"""
    )
    assert offsets and all(value == "0px" for value in offsets), offsets
    context.close()


def test_world_css_loads_only_on_spa_activation(page):
    """Stage B waterfall gate: world.css must never load at the top of the
    landing; activating a tool view loads it once, sets .world-ready in its
    load callback, and the quiet-center stage appears behind the tool views."""
    loaded_before = page.evaluate(
        "performance.getEntriesByType('resource').filter(e => e.name.includes('world.css')).length"
    )
    assert loaded_before == 0
    page.click("#nav-browse-btn")
    wait_until(page, "document.documentElement.classList.contains('world-ready')")
    loaded_after = page.evaluate(
        "performance.getEntriesByType('resource').filter(e => e.name.includes('world.css')).length"
    )
    assert loaded_after == 1
    wait_until(
        page,
        "parseFloat(getComputedStyle(document.querySelector('.tool-stage > .world-stage')).opacity) > 0",
    )
    scene = page.evaluate(
        "getComputedStyle(document.querySelector('.tool-stage > .world-stage'), '::before').backgroundImage"
    )
    assert "stage-tools" in scene, scene


def test_template_page_stage_glyphs_and_request_budget(browser, live_server):
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.goto(live_server + "/scholarships/coca-cola-scholars", wait_until="networkidle")
    scene = page.evaluate("getComputedStyle(document.querySelector('.world-stage'), '::before').backgroundImage")
    assert "stage-tools" in scene, scene
    glyph = page.evaluate(
        "getComputedStyle(document.querySelector('.detail-page .stat-label'), '::before').backgroundImage"
    )
    assert "glyph-sheet" in glyph, glyph
    world = page.evaluate(
        "performance.getEntriesByType('resource').map(e => e.name).filter(n => n.includes('/static/img/world/'))"
    )
    # The stage, the glyph sheet, and the dusk band once it is near.
    assert len(world) <= 3, world
    assert not [n for n in world if "canopy-edge" in n or "fern-corner" in n], world
    context.close()


def test_forced_colors_suppresses_world_decoration(browser, live_server):
    context = browser.new_context(
        viewport={"width": 1440, "height": 900}, forced_colors="active"
    )
    page = context.new_page()
    page.goto(live_server + "/scholarships/coca-cola-scholars", wait_until="networkidle")
    body_bg = page.evaluate("getComputedStyle(document.body).backgroundImage")
    assert "world" not in body_bg, body_bg
    scene = page.evaluate("getComputedStyle(document.querySelector('.world-stage'), '::before').content")
    assert scene in ("none", "normal"), scene
    world = page.evaluate(
        "performance.getEntriesByType('resource').filter(e => e.name.includes('/static/img/world/')).length"
    )
    assert world == 0, world
    # The primary action stays rendered and clickable under forced colors.
    assert page.locator(".card-link").first.is_visible()
    page.locator(".card-link").first.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    result = _hit_is_inside(page, ".card-link")
    assert result is True, f"[forced-colors] card-link intercepted by: {result}"
    context.close()


def test_hero_preload_never_double_fetches_on_mobile(browser, live_server):
    context = browser.new_context(
        viewport={"width": 412, "height": 823}, device_scale_factor=1.75
    )
    context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
    page = context.new_page()
    hero_requests = []
    page.on(
        "request",
        lambda r: hero_requests.append(r.url) if "hero-forest-mobile" in r.url else None,
    )
    page.goto(live_server, wait_until="networkidle")
    assert len(hero_requests) == 1, hero_requests
    context.close()


def test_first_catalog_stat_shares_the_clearing_ink(page):
    """The world layer made the stat cards transparent; the first stat must not
    keep the cream ink that belonged to its old dark card (it vanished into
    the clearing)."""
    colors = page.evaluate(
        """() => {
          const strongs = document.querySelectorAll('.catalog-number strong');
          const spans = document.querySelectorAll('.catalog-number span');
          return {
            firstStrong: getComputedStyle(strongs[0]).color,
            secondStrong: getComputedStyle(strongs[1]).color,
            firstSpan: getComputedStyle(spans[0]).color,
            secondSpan: getComputedStyle(spans[1]).color,
          };
        }"""
    )
    assert colors["firstStrong"] == colors["secondStrong"], colors
    assert colors["firstSpan"] == colors["secondSpan"], colors


def test_preview_results_cards_scroll_inside_capped_panel(page):
    """On two-column hero widths the match preview's cards scroll inside a
    capped region instead of stretching the hero viewports tall and stranding
    the left column against empty backdrop; the finish-profile CTA stays out
    of the scroller."""
    page.fill("#preview-gpa", "3.8")
    page.select_option("#preview-grade", "high_school_junior")
    page.select_option("#preview-field", "computer_science")
    page.click("#preview-submit")
    page.wait_for_selector("#preview-results:not([hidden])", timeout=15000)
    cards = page.evaluate(
        """() => {
          const el = document.querySelector('#preview-cards');
          const style = getComputedStyle(el);
          return {
            overflowY: style.overflowY,
            maxHeight: style.maxHeight,
            scrolls: el.scrollHeight > el.clientHeight,
          };
        }"""
    )
    assert cards["overflowY"] == "auto", cards
    assert cards["maxHeight"] not in ("none", ""), cards
    assert cards["scrolls"] is True, cards
    # The CTA lives outside the scroller, still reachable without scrolling it.
    assert page.evaluate(
        "!document.querySelector('#preview-cards').contains(document.querySelector('#preview-complete-btn'))"
    )


def test_landing_paints_hero_after_scroll_down_and_back(page):
    """Chromium regression guard: after a fast scroll to the bottom and back
    to the top, the profile form must not paint (or hit-test) at a stale
    viewport offset over the hero. When the layer sticks, elementsFromPoint
    over the hero resolves to #profile-form and the landing looks blank."""
    for _ in range(8):
        page.mouse.wheel(0, 900)
        page.wait_for_timeout(150)
    page.evaluate("window.scrollTo(0, 0)")
    wait_until(page, "window.scrollY === 0")
    page.wait_for_timeout(500)
    hits = page.evaluate(
        """() => {
          const form = document.querySelector('#profile-form');
          const points = [[400, 300], [300, 200], [1000, 400]];
          return points.map(([x, y]) => {
            const top = document.elementsFromPoint(x, y)[0];
            return {
              point: [x, y],
              coveredByForm: top === form || (form && form.contains(top)),
              top: top ? top.tagName + '.' + (top.className || '').toString().slice(0, 40) : null,
            };
          });
        }"""
    )
    for hit in hits:
        assert not hit["coveredByForm"], hits


def test_reduced_motion_keeps_the_static_section_and_never_downloads_three(browser, live_server):
    """Reduced motion keeps How it works static: the overlook painting and
    the four stops are the whole section, three.js is never requested, and
    the last stop's Build my profile button is on the page and clickable."""
    context = browser.new_context(
        viewport={"width": 1440, "height": 900}, reduced_motion="reduce"
    )
    context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
    context.add_init_script(
        "try {"
        " Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8, configurable: true});"
        " Object.defineProperty(navigator, 'deviceMemory', {get: () => 8, configurable: true});"
        " } catch (e) {}"
    )
    page = context.new_page()
    three_requests = []
    page.on(
        "request",
        lambda r: three_requests.append(r.url) if "three.min.js" in r.url else None,
    )
    page.goto(live_server, wait_until="networkidle")
    assert page.evaluate("document.documentElement.classList.contains('journey-static')")
    page.locator(".journey-painting").scroll_into_view_if_needed()
    wait_until(page, "document.querySelector('.journey-painting img.world-loaded') !== null")
    show_last_stop(page)
    page.wait_for_timeout(2200)
    assert three_requests == [], three_requests
    result = _hit_is_inside(page, ".journey-card-cta")
    assert result is True, f"[reduced-motion] How it works CTA intercepted by: {result}"
    context.close()
