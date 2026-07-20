import pytest
from playwright.sync_api import expect


CLS_OBSERVER = """
window.__cls = 0;
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) window.__cls += entry.value;
  }
}).observe({ type: "layout-shift", buffered: true });
"""


def assert_no_visible_reveal_is_hidden(page):
    hidden = page.evaluate(
        """() => Array.from(document.querySelectorAll('.reveal-on-scroll'))
          .filter((el) => {
            const rect = el.getBoundingClientRect();
            const visible = rect.bottom > 0 && rect.top < window.innerHeight;
            return visible && getComputedStyle(el).opacity === '0';
          })
          .map((el) => el.className)"""
    )
    assert hidden == []


def cls_value(page):
    return page.evaluate("() => window.__cls || 0")


class TestLandingConsentBoot:
    def test_gate_is_visible_and_dismissible_when_app_js_is_blocked(self, browser, live_server):
        context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
        page = context.new_page()
        page.route("**/static/js/app.js*", lambda route: route.abort())
        page.goto(live_server, wait_until="domcontentloaded")

        gate = page.locator("#age-gate")
        expect(gate).to_be_visible()
        expect(page.locator("#age-gate-continue")).to_be_disabled()

        page.check("#age-gate-agree")
        expect(page.locator("#age-gate-continue")).to_be_enabled()
        page.click("#age-gate-continue")
        expect(gate).to_be_hidden()
        assert page.evaluate("() => localStorage.getItem('site_consent_v1')") == "yes"
        context.close()

    def test_storage_blocked_accept_hides_only_current_document(self, browser, live_server):
        context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
        context.add_init_script(
            """
            Object.defineProperty(window, 'localStorage', {
              value: {
                getItem: () => null,
                setItem: () => { throw new DOMException('blocked', 'SecurityError'); },
              },
            });
            """
        )
        page = context.new_page()
        page.goto(live_server, wait_until="domcontentloaded")

        expect(page.locator("#age-gate")).to_be_visible()
        page.check("#age-gate-agree")
        page.click("#age-gate-continue")
        expect(page.locator("#age-gate")).to_be_hidden()

        page.goto(live_server, wait_until="domcontentloaded")
        expect(page.locator("#age-gate")).to_be_visible()
        context.close()

    def test_fully_storage_blocked_visitor_still_sees_the_gate(self, browser, live_server):
        """getItem throwing must mean NOT consented — never silently consented.

        This is the signed-off consent semantics: a visitor whose storage cannot
        even be read sees the gate, and accepting hides it for the current
        document only, so the next navigation re-prompts.
        """
        context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
        context.add_init_script(
            """
            Object.defineProperty(window, 'localStorage', {
              value: {
                getItem: () => { throw new DOMException('blocked', 'SecurityError'); },
                setItem: () => { throw new DOMException('blocked', 'SecurityError'); },
              },
            });
            """
        )
        page = context.new_page()
        page.goto(live_server, wait_until="domcontentloaded")

        expect(page.locator("#age-gate")).to_be_visible()
        page.check("#age-gate-agree")
        page.click("#age-gate-continue")
        expect(page.locator("#age-gate")).to_be_hidden()

        page.goto(live_server, wait_until="domcontentloaded")
        expect(page.locator("#age-gate")).to_be_visible()
        context.close()

    def test_cold_gate_focus_inertness_and_keyboard_trap(self, cold_page):
        gate = cold_page.locator("#age-gate")
        expect(gate).to_be_visible()
        expect(cold_page.locator("#age-gate-continue")).to_be_disabled()
        cold_page.wait_for_function("() => document.activeElement?.id === 'age-gate-agree'")

        assert cold_page.evaluate(
            """() => Array.from(document.body.children)
              .filter((child) => child.id !== 'age-gate' && child.tagName !== 'SCRIPT')
              .every((child) => child.hasAttribute('inert'))"""
        )

        cold_page.keyboard.press("Escape")
        expect(gate).to_be_visible()

        for _ in range(4):
            cold_page.keyboard.press("Tab")
            assert cold_page.evaluate(
                "() => document.getElementById('age-gate').contains(document.activeElement)"
            )

        cold_page.check("#age-gate-agree")
        cold_page.click("#age-gate-continue")
        expect(gate).to_be_hidden()
        assert cold_page.evaluate(
            """() => Array.from(document.body.children)
              .filter((child) => child.id !== 'age-gate' && child.tagName !== 'SCRIPT')
              .every((child) => !child.hasAttribute('inert'))"""
        )

    def test_consented_state_hides_gate_and_keeps_background_available(self, accepted_page):
        expect(accepted_page.locator("#age-gate")).to_be_hidden()
        assert accepted_page.locator("html.has-site-consent").count() == 1
        assert accepted_page.evaluate(
            """() => Array.from(document.body.children)
              .filter((child) => child.id !== 'age-gate' && child.tagName !== 'SCRIPT')
              .every((child) => !child.hasAttribute('inert'))"""
        )


class TestLandingClsAndResponsiveImage:
    def test_cold_top_load_has_no_reveal_cls(self, browser, live_server):
        context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
        context.add_init_script(CLS_OBSERVER)
        page = context.new_page()
        page.goto(live_server, wait_until="load")
        page.wait_for_timeout(1800)

        assert cls_value(page) < 0.1
        assert_no_visible_reveal_is_hidden(page)
        context.close()

    def test_hash_scroll_load_has_no_reveal_cls(self, browser, live_server):
        context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
        context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
        context.add_init_script(CLS_OBSERVER)
        page = context.new_page()
        page.goto(f"{live_server}/#browse", wait_until="load")
        page.wait_for_timeout(1800)

        assert page.evaluate("() => window.scrollY") > 200
        assert cls_value(page) < 0.1
        assert_no_visible_reveal_is_hidden(page)
        context.close()

    def test_mobile_resize_has_no_reveal_cls(self, browser, live_server):
        context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
        context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
        context.add_init_script(CLS_OBSERVER)
        page = context.new_page()
        page.goto(live_server, wait_until="load")
        page.wait_for_timeout(800)
        page.set_viewport_size({"width": 823, "height": 412})
        page.wait_for_timeout(800)

        assert cls_value(page) < 0.1
        assert_no_visible_reveal_is_hidden(page)
        context.close()

    def test_hero_stage_image_paints_the_mobile_art(self, accepted_page):
        """The hero art is a real, eagerly-fetched <img> that resolves the
        mobile source at a mobile viewport and fills the stage box."""
        img = accepted_page.locator(".hero-stage img")
        accepted_page.wait_for_function(
            "() => document.querySelector('.hero-stage img')?.complete"
        )
        assert "hero-forest-mobile.webp" in img.evaluate("img => img.currentSrc")
        assert img.get_attribute("fetchpriority") == "high"
        assert img.get_attribute("loading") is None  # eager: it is the LCP
        box = img.bounding_box()
        assert box is not None and box["width"] >= 412

    @pytest.mark.parametrize(
        "device_scale_factor,expected_candidate",
        [
            (1, "campus-quad-380.webp"),
            (1.75, "campus-quad-760.webp"),
        ],
    )
    def test_campus_quad_responsive_image_contract(
        self, browser, live_server, device_scale_factor, expected_candidate
    ):
        context = browser.new_context(
            viewport={"width": 412, "height": 823},
            device_scale_factor=device_scale_factor,
        )
        context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
        page = context.new_page()
        page.goto(live_server, wait_until="load")
        image = page.locator(".proof-photo img")
        image.scroll_into_view_if_needed()
        page.wait_for_function(
            "() => document.querySelector('.proof-photo img')?.complete"
        )

        assert page.locator(".proof-photo picture").count() == 1
        assert page.locator('.proof-photo source[type="image/webp"]').count() == 1
        assert expected_candidate in image.evaluate("img => img.currentSrc")
        assert image.get_attribute("alt") == "Students walking across a college campus between classes"
        assert image.get_attribute("loading") == "lazy"
        assert image.get_attribute("decoding") == "async"
        box = image.bounding_box()
        assert box is not None
        assert 360 <= box["width"] <= 390
        assert 235 <= box["height"] <= 270
        context.close()
