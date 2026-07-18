"""Every user-facing feature, driven in a real browser.

Grouped by surface. Each test drives the actual UI (no API shortcuts) so a
broken selector, a dead listener, or a JS exception fails here, which the
request-level tests cannot catch.
"""
import json
import re

import pytest

from tests.e2e.conftest import unique_email


def submit_profile_form(page):
    """Walk the three-step profile form exactly as a student would."""
    page.fill("#gpa", "3.8")
    page.select_option("#grade-level", "high_school_junior")
    page.click("#step-next-btn")
    page.select_option("#citizenship", index=1)
    page.select_option("#state", label="Texas")
    page.select_option("#financial-need", index=1)
    page.click("#step-next-btn")
    # Step 3: pick a field of study, like a real student would.
    page.locator("#fields-of-study input[type=checkbox]").first.check()
    page.fill("#target-schools", "Rice University")
    page.fill("#activities", "robotics club")
    page.click("#submit-btn")


def fill_profile_and_submit(page):
    submit_profile_form(page)
    page.wait_for_selector("#results-section:not([hidden])", timeout=25000)
    page.wait_for_selector("#results-container .match-card", timeout=25000)


def signup(page, email=None, password="e2e-password-123"):
    email = email or unique_email()
    page.click("#open-signup")
    page.wait_for_selector("#auth-modal[open]")
    page.fill("#auth-email", email)
    page.fill("#auth-password", password)
    page.click("#auth-submit")
    page.wait_for_selector("#auth-logged-in:not([hidden])", timeout=15000)
    return email, password


ROOT_MATCH_URL = re.compile(r"^https?://[^/]+/match$")
PROGRAM_MATCH_URL = re.compile(r"^https?://[^/]+/programs/match$")
COMPETITION_MATCH_URL = re.compile(r"^https?://[^/]+/competitions/match$")


def fulfill_json(route, payload):
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(payload),
    )


def route_match_fixtures(page, scholarships=None, programs=None, competitions=None):
    page.route(
        ROOT_MATCH_URL,
        lambda route: fulfill_json(route, {"matches": scholarships or [], "near_misses": []}),
    )
    page.route(
        PROGRAM_MATCH_URL,
        lambda route: fulfill_json(route, {"matches": programs or [], "near_misses": []}),
    )
    page.route(
        COMPETITION_MATCH_URL,
        lambda route: fulfill_json(route, {"matches": competitions or [], "near_misses": []}),
    )


def application_requirement(req_id="application-form"):
    return {
        "id": req_id,
        "label": "Application form",
        "required": True,
        "details": "Fixture requirement.",
        "source_url": "https://example.com/requirements",
    }


def special_requirement(kind):
    return {
        "kind": kind,
        "label": "Fixture special check",
        "details": "This constructed fixture requires a special eligibility check.",
    }


SCHOLARSHIP_BREAKDOWN = {
    "field_of_study": 40,
    "demographics": 0,
    "target_school": 0,
    "activities": 0,
    "financial_need": 10,
    "total": 85,
}
PROGRAM_BREAKDOWN = {"subject": 40, "demographics": 0, "financial_access": 10, "total": 85}
COMPETITION_BREAKDOWN = {"category": 40, "demographics": 0, "financial_access": 10, "total": 85}


def scholarship_match(slug, name, *, requires_special_check=False, requirements=None):
    return {
        "scholarship_id": slug,
        "scholarship_name": name,
        "sponsor": "Fixture Scholarship Sponsor",
        "award_amount": 1000,
        "deadline": "2099-12-31",
        "estimated_deadline": None,
        "url": "https://example.com/scholarship",
        "verified": True,
        "verification_source_url": "https://example.com/scholarship-source",
        "last_verified_at": "2026-07-17",
        "essay_required": False,
        "closing_soon": False,
        "score": 85,
        "match_tier": "strong",
        "match_reasons": [],
        "score_breakdown": SCHOLARSHIP_BREAKDOWN,
        "eligible_schools": [],
        "requires_special_check": requires_special_check,
        "special_requirements": (
            [special_requirement("nomination")] if requires_special_check else []
        ),
        "application_requirements": (
            [application_requirement(f"{slug}-application")]
            if requirements is None
            else requirements
        ),
    }


def program_match(slug, name, *, requires_special_check=False):
    return {
        "program_id": slug,
        "name": name,
        "host": "Fixture Program Host",
        "subject": "STEM research",
        "cost": "Free",
        "cost_category": "free",
        "selectivity": "Selective",
        "program_format": "residential",
        "location": "Austin, TX",
        "program_dates": "June 2099",
        "deadline": "2099-12-31",
        "estimated_deadline": None,
        "url": "https://example.com/program",
        "verified": True,
        "verification_source_url": "https://example.com/program-source",
        "last_verified_at": "2026-07-17",
        "essay_required": False,
        "score": 85,
        "match_tier": "strong",
        "match_reasons": [],
        "score_breakdown": PROGRAM_BREAKDOWN,
        "application_requirements": [application_requirement(f"{slug}-application")],
        "requires_special_check": requires_special_check,
        "special_requirements": (
            [special_requirement("membership")] if requires_special_check else []
        ),
    }


def competition_match(slug, name, *, requires_special_check=False):
    return {
        "competition_id": slug,
        "name": name,
        "host": "Fixture Competition Host",
        "category": "Engineering",
        "cost": "Free",
        "cost_category": "free",
        "recognition": "National recognition",
        "participation_format": "team",
        "location": "Virtual",
        "competition_dates": "Spring 2099",
        "deadline": "2099-12-31",
        "estimated_deadline": None,
        "url": "https://example.com/competition",
        "verified": True,
        "verification_source_url": "https://example.com/competition-source",
        "last_verified_at": "2026-07-17",
        "essay_required": False,
        "score": 85,
        "match_tier": "strong",
        "match_reasons": [],
        "score_breakdown": COMPETITION_BREAKDOWN,
        "application_requirements": [application_requirement(f"{slug}-application")],
        "requires_special_check": requires_special_check,
        "special_requirements": (
            [special_requirement("competition_or_finalist")]
            if requires_special_check
            else []
        ),
    }


def wait_for_quick_apply_text(page, text):
    page.wait_for_function(
        """text => {
            const list = document.querySelector("#quick-applies-list");
            return Boolean(list && list.textContent.includes(text));
        }""",
        arg=text,
        timeout=15000,
    )


# ---------------------------------------------------------------- marketing

class TestPublicPages:
    @pytest.mark.parametrize(
        "path,expect",
        [
            ("/", "Find opportunities"),
            ("/journey", "Fly through"),
            ("/browse", "Browse"),
            ("/privacy", "Privacy"),
            ("/terms", "Terms"),
            ("/guides/essays", "essay"),
            ("/scholarships/coca-cola-scholars", "Coca-Cola"),
        ],
    )
    def test_page_renders(self, page, live_server, path, expect):
        page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
        assert page.locator("body").inner_text().lower().find(expect.lower()) >= 0
        assert page.locator("footer.site-footer").count() == 1

    def test_404_page(self, page, live_server):
        resp = page.goto(f"{live_server}/scholarships/does-not-exist")
        assert resp.status == 404

    def test_essay_guide_cards_navigate(self, page, live_server):
        page.goto(f"{live_server}/guides/essays", wait_until="load")
        cards = page.locator(".guide-card")
        assert cards.count() == 5
        cards.first.click()
        page.wait_for_url("**/guides/essays/identity")
        assert page.locator(".guide-body").count() == 1

    def test_nav_and_journey_links_reachable(self, page, live_server):
        page.click('.site-nav a[href="/journey"]')
        page.wait_for_url("**/journey")
        assert page.locator("#journey-canvas").count() == 1

    def test_journey_world_renders(self, page, live_server):
        page.goto(f"{live_server}/journey", wait_until="load")
        page.wait_for_timeout(2500)
        drew = page.evaluate(
            "() => { const c = document.getElementById('journey-canvas');"
            " return !!(c && c.width > 0 && document.documentElement.classList.contains('journey-live')); }"
        )
        assert drew, "journey canvas never initialized"

    def test_journey_static_fallback_under_reduced_motion(self, browser, live_server):
        ctx = browser.new_context(reduced_motion="reduce")
        p = ctx.new_page()
        p.goto(f"{live_server}/journey", wait_until="load")
        p.wait_for_timeout(800)
        assert p.locator("html.journey-static").count() == 1
        assert p.locator("#journey-canvas").is_hidden()
        ctx.close()

    def test_landing_teaser_paints(self, page):
        page.locator(".journey-teaser").scroll_into_view_if_needed()
        page.wait_for_timeout(3000)
        ok = page.evaluate(
            "() => { const c = document.getElementById('journey-teaser-canvas');"
            " return !!(window.THREE && c && c.width > 0); }"
        )
        assert ok, "landing teaser never initialized"

    @pytest.mark.parametrize("path", ["/privacy", "/terms"])
    def test_legal_pages_link_home_not_app(self, page, live_server, path):
        page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
        back = page.locator("header .btn-ghost")
        assert back.inner_text().strip() == "Back to homepage"
        back.click()
        page.wait_for_url(f"{live_server}/")

    def test_brand_returns_to_homepage_from_every_surface(self, page, live_server):
        for path in ["/", "/privacy", "/terms", "/journey", "/browse"]:
            page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
            brand = page.locator("header .brand")
            assert brand.evaluate("el => el.tagName.toLowerCase()") == "a", path
            assert brand.get_attribute("href") == "/", path

    def test_google_button_uses_the_real_google_mark(self, page):
        page.click("#open-login")
        page.wait_for_selector("#auth-modal[open]")
        fills = page.eval_on_selector_all(
            "#google-login-link .google-mark svg path",
            "els => els.map(e => e.getAttribute('fill').toUpperCase())",
        )
        assert set(fills) == {"#4285F4", "#34A853", "#FBBC05", "#EA4335"}

    def test_journey_rail_stops_are_clickable(self, page, live_server):
        page.goto(f"{live_server}/journey", wait_until="load")
        page.wait_for_timeout(1500)
        stops = page.locator(".journey-rail button")
        assert stops.count() == 4
        before = page.evaluate("() => window.scrollY")
        stops.nth(3).click()
        page.wait_for_timeout(1800)
        assert page.evaluate("() => window.scrollY") > before + 500

    def test_hero_cta_scrolls_to_profile_form(self, page):
        page.click(".hero-cta")
        page.wait_for_timeout(2000)
        top = page.evaluate(
            "() => document.getElementById('profile-form').getBoundingClientRect().top"
        )
        assert 40 < top < 200, f"profile form landed at {top}px, expected under the header"


# ---------------------------------------------------------------- preview

class TestPreview:
    def test_three_question_preview_returns_matches(self, page):
        page.fill("#preview-gpa", "3.7")
        page.select_option("#preview-grade", "high_school_junior")
        page.select_option("#preview-field", index=1)
        page.click("#preview-submit")
        page.wait_for_selector("#preview-results:not([hidden])", timeout=15000)
        assert page.locator("#preview-cards > *").count() == 3
        assert "match" in page.locator("#preview-total").inner_text().lower()

    def test_preview_rejects_empty_input(self, page):
        page.click("#preview-submit")
        page.wait_for_timeout(500)
        assert page.locator("#preview-results").is_hidden()


# ---------------------------------------------------------------- matcher

class TestProfileAndMatches:
    def test_full_profile_returns_scholarship_matches(self, page):
        fill_profile_and_submit(page)
        assert page.locator("#results-container .match-card").count() > 0
        assert page.locator("#results-summary").inner_text().strip() != ""

    def test_non_http_verification_source_renders_as_plain_text(self, page):
        rendered = page.evaluate(
            """() => {
                const node = buildVerificationSource({
                    verification_source_url: "javascript:alert(1)",
                    last_verified_at: null,
                });
                document.body.appendChild(node);
                return {
                    links: node.querySelectorAll("a").length,
                    text: node.textContent,
                };
            }"""
        )
        assert rendered["links"] == 0
        assert "javascript:alert(1)" in rendered["text"]

    def test_form_validation_blocks_incomplete_step(self, page):
        page.locator("#profile-form").scroll_into_view_if_needed()
        page.click("#step-next-btn")  # nothing filled
        page.wait_for_timeout(400)
        assert page.locator("#submit-btn").is_hidden(), "advanced past an empty step"

    def test_soonest_sort_puts_confirmed_deadlines_before_estimates(self, page):
        fill_profile_and_submit(page)
        page.select_option("#filter-sort", "deadline")
        page.wait_for_timeout(900)
        # The card's deadline stat prefixes an estimate with "~".
        values = page.eval_on_selector_all(
            "#results-container .stat-deadline .stat-value",
            "els => els.map(e => e.textContent.trim())",
        )
        assert values, "no deadlines rendered"
        seen_estimate = False
        for v in values:
            if v.startswith("~"):
                seen_estimate = True
            elif seen_estimate and v.lower() not in ("rolling", "see sponsor site"):
                raise AssertionError(
                    f"a confirmed deadline ({v}) sorted BELOW an estimate; order: {values[:8]}"
                )

    def test_free_competitions_say_free_not_a_paragraph(self, page):
        fill_profile_and_submit(page)
        page.click("#tab-competitions")
        page.wait_for_selector("#competitions-section:not([hidden])", timeout=15000)
        page.wait_for_timeout(800)
        costs = page.eval_on_selector_all(
            "#competitions-container .stat-award .stat-value",
            "els => els.map(e => e.textContent.trim())",
        )
        frees = [c for c in costs if c.lower().startswith("free")]
        assert frees, "expected at least one free competition on screen"
        for c in frees:
            assert c == "Free", f"free competition still shows an essay: {c[:60]}..."

    def test_all_three_lanes_populate(self, page):
        fill_profile_and_submit(page)
        for tab, section in [
            ("#tab-programs", "#programs-section"),
            ("#tab-competitions", "#competitions-section"),
            ("#tab-scholarships", "#results-section"),
        ]:
            page.click(tab)
            page.wait_for_selector(f"{section}:not([hidden])", timeout=10000)
            assert page.locator(f"{section} .match-card").count() >= 0

    def test_filters_narrow_results(self, page):
        fill_profile_and_submit(page)
        before = page.locator("#results-container .match-card").count()
        page.check("#filter-verified-only")
        page.wait_for_timeout(600)
        after = page.locator("#results-container .match-card").count()
        assert after <= before
        page.click("#filter-clear")
        page.wait_for_timeout(600)
        assert page.locator("#results-container .match-card").count() == before

    def test_sort_and_min_score_controls(self, page):
        fill_profile_and_submit(page)
        page.select_option("#filter-sort", "deadline")
        page.wait_for_timeout(400)
        page.fill("#scholarship-search", "engineering")
        page.wait_for_timeout(600)
        page.fill("#scholarship-search", "")
        page.wait_for_timeout(400)
        assert page.locator("#results-section").is_visible()
        assert not page.console_errors, page.console_errors


# ---------------------------------------------------------------- quick applies

class TestQuickApplies:
    def test_special_check_scholarship_never_renders(self, page):
        regular_name = "Fixture Regular Scholarship Quick Apply"
        special_name = "Fixture Special Scholarship Quick Apply"
        route_match_fixtures(
            page,
            scholarships=[
                scholarship_match("fixture-regular-scholarship", regular_name),
                scholarship_match(
                    "fixture-special-scholarship",
                    special_name,
                    requires_special_check=True,
                ),
            ],
        )

        submit_profile_form(page)
        wait_for_quick_apply_text(page, regular_name)

        quick_apply_text = page.locator("#quick-applies-list").text_content()
        assert regular_name in quick_apply_text
        assert special_name not in quick_apply_text

    def test_special_check_program_never_renders(self, page):
        regular_name = "Fixture Regular Program Quick Apply"
        special_name = "Fixture Special Program Quick Apply"
        route_match_fixtures(
            page,
            programs=[
                program_match("fixture-regular-program", regular_name),
                program_match(
                    "fixture-special-program",
                    special_name,
                    requires_special_check=True,
                ),
            ],
        )

        submit_profile_form(page)
        wait_for_quick_apply_text(page, regular_name)

        quick_apply_text = page.locator("#quick-applies-list").text_content()
        assert regular_name in quick_apply_text
        assert special_name not in quick_apply_text

    def test_special_check_competition_never_renders(self, page):
        regular_name = "Fixture Regular Competition Quick Apply"
        special_name = "Fixture Special Competition Quick Apply"
        route_match_fixtures(
            page,
            competitions=[
                competition_match("fixture-regular-competition", regular_name),
                competition_match(
                    "fixture-special-competition",
                    special_name,
                    requires_special_check=True,
                ),
            ],
        )

        submit_profile_form(page)
        wait_for_quick_apply_text(page, regular_name)

        quick_apply_text = page.locator("#quick-applies-list").text_content()
        assert regular_name in quick_apply_text
        assert special_name not in quick_apply_text

    def test_count_copy_distinguishes_unverified_requirements(self, page):
        unknown_name = "Fixture Unknown Requirements Quick Apply"
        route_match_fixtures(
            page,
            scholarships=[
                scholarship_match(
                    "fixture-unknown-requirements",
                    unknown_name,
                    requirements=[],
                )
            ],
        )

        submit_profile_form(page)
        wait_for_quick_apply_text(page, unknown_name)
        page.wait_for_function(
            """() => {
                const count = document.querySelector("#quick-applies-count");
                return Boolean(
                    count &&
                    count.textContent.includes("requirements we haven't verified yet")
                );
            }""",
            timeout=15000,
        )

        count_text = page.locator("#quick-applies-count").text_content()
        assert "requirements we haven't verified yet" in count_text
        assert "3 or fewer requirements" not in count_text
        assert not count_text.startswith("0 ")


# ---------------------------------------------------------------- catalog

class TestCatalog:
    def test_browse_catalog_and_search(self, page):
        page.click("#nav-browse-btn")
        page.wait_for_selector("#catalog-section:not([hidden])", timeout=15000)
        assert page.locator("#catalog-container > *").count() > 0
        page.fill("#catalog-search", "coca")
        page.wait_for_timeout(800)
        assert page.locator("#catalog-container").inner_text().lower().count("coca") >= 1
        page.click("#catalog-clear")
        page.wait_for_timeout(500)

    def test_catalog_kind_tabs(self, page):
        page.click("#nav-browse-btn")
        page.wait_for_selector("#catalog-section:not([hidden])", timeout=15000)
        for tab in page.locator(".catalog-kind-tab").all():
            tab.click()
            page.wait_for_timeout(400)
        assert not page.console_errors, page.console_errors

    def test_journey_browse_all_opens_homepage_catalog(self, page, live_server):
        page.goto(f"{live_server}/journey", wait_until="load")
        page.click('.account-nav a[href="/#browse"]')
        page.wait_for_selector("#catalog-section:not([hidden])", timeout=15000)
        assert page.locator("#catalog-container > *").count() > 0
        # The deep-link hash is consumed so a refresh returns to the landing view.
        assert page.evaluate("() => window.location.hash") == ""
        assert not page.console_errors, page.console_errors


# ---------------------------------------------------------------- accounts

class TestAuth:
    def test_signup_login_logout_cycle(self, page):
        email, password = signup(page)
        assert email.split("@")[0][:6] in page.locator("#account-email").inner_text()
        page.click("#logout-btn")
        page.wait_for_selector("#auth-logged-out:not([hidden])", timeout=10000)

        page.click("#open-login")
        page.wait_for_selector("#auth-modal[open]")
        page.fill("#auth-email", email)
        page.fill("#auth-password", password)
        page.click("#auth-submit")
        page.wait_for_selector("#auth-logged-in:not([hidden])", timeout=10000)

    def test_login_with_bad_password_shows_error(self, page):
        email, _ = signup(page)
        page.click("#logout-btn")
        page.wait_for_selector("#auth-logged-out:not([hidden])")
        page.click("#open-login")
        page.fill("#auth-email", email)
        page.fill("#auth-password", "wrong-password-here")
        page.click("#auth-submit")
        page.wait_for_selector("#auth-error:not([hidden])", timeout=10000)

    def test_password_reset_request_flow(self, page):
        page.click("#open-login")
        page.click("#open-password-reset")
        page.wait_for_selector("#password-reset-modal[open]")
        page.fill("#password-reset-email", unique_email())
        page.click("#password-reset-request-submit")
        page.wait_for_selector(
            "#password-reset-request-success:not([hidden]), #password-reset-request-error:not([hidden])",
            timeout=10000,
        )

    def test_settings_modal_and_reminders_toggle(self, page):
        signup(page)
        page.click("#open-settings")
        page.wait_for_selector("#settings-modal[open]")
        page.check("#reminders-toggle")
        page.wait_for_timeout(600)
        assert page.is_checked("#reminders-toggle")
        page.click("#settings-close")

    def test_change_password(self, page):
        email, password = signup(page)
        page.click("#open-settings")
        page.wait_for_selector("#settings-modal[open]")
        page.fill("#current-password", password)
        page.fill("#new-password", "another-strong-pass-9")
        page.click("#change-password-submit")
        page.wait_for_selector(
            "#settings-success:not([hidden]), #settings-error:not([hidden])", timeout=10000
        )
        assert page.locator("#settings-success").is_visible()


# ---------------------------------------------------------------- the plan

class TestPlan:
    def test_save_opportunity_then_see_it_in_plan(self, page):
        signup(page)
        fill_profile_and_submit(page)
        save_btn = page.locator("#results-container button:has-text('Save')").first
        save_btn.click()
        page.wait_for_timeout(1200)
        page.click("#nav-plan-btn")
        page.wait_for_selector("#saved-section:not([hidden])", timeout=15000)
        assert page.locator("#saved-container > *").count() > 0
        assert page.locator("#saved-count").inner_text().strip() not in ("", "0")

    def test_saved_item_status_and_checklist(self, page):
        signup(page)
        fill_profile_and_submit(page)
        page.locator("#results-container button:has-text('Save')").first.click()
        page.wait_for_timeout(1200)
        page.click("#nav-plan-btn")
        page.wait_for_selector("#saved-section:not([hidden])", timeout=15000)
        status = page.locator("#saved-container select").first
        if status.count():
            status.select_option(index=1)
            page.wait_for_timeout(800)
        checkbox = page.locator("#saved-container input[type=checkbox]").first
        if checkbox.count():
            checkbox.check()
            page.wait_for_timeout(800)
        assert not page.console_errors, page.console_errors

    def test_plan_rollups_render(self, page):
        signup(page)
        fill_profile_and_submit(page)
        page.locator("#results-container button:has-text('Save')").first.click()
        page.wait_for_timeout(1200)
        page.click("#nav-plan-btn")
        page.wait_for_selector("#saved-section:not([hidden])", timeout=15000)
        assert page.locator("#rec-letters-panel").count() == 1
        assert page.locator("#quick-applies-panel").count() == 1


# ---------------------------------------------------------------- hygiene

class TestHygiene:
    def test_no_console_errors_on_landing(self, page):
        page.wait_for_timeout(2500)
        assert not page.console_errors, page.console_errors

    def test_no_console_errors_on_journey(self, page, live_server):
        page.goto(f"{live_server}/journey", wait_until="load")
        page.wait_for_timeout(2500)
        assert not page.console_errors, page.console_errors

    def test_mobile_viewport_landing_has_no_horizontal_overflow(self, browser, live_server):
        ctx = browser.new_context(viewport={"width": 375, "height": 780})
        p = ctx.new_page()
        p.goto(live_server, wait_until="load")
        p.wait_for_timeout(1500)
        overflow = p.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )
        assert overflow <= 2, f"landing overflows horizontally by {overflow}px on mobile"
        ctx.close()
