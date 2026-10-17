"""EC-01: the landing page stays usable while GET /vocabulary is slow.

app.js used to await /vocabulary before wiring anything. On a cold server the
page looked loaded while every scripted control was dead: no Log in or Sign up,
inert nav buttons, and both forms falling through to a native GET that reloaded
the page. These tests hold that one request with page.route and drive the page
meanwhile, then let it through, fail it, or leave it hanging.
"""
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect

from tests.e2e.test_e2e import fill_profile_and_submit, signup

VOCABULARY = "**/vocabulary"
LOADING_LABEL = "Loading options..."
READY_LABEL = "Show my 3 matches"
LOADING_STATUS = "Loading form options..."
OPTIONS_ERROR = "The form options did not load."


def hold_vocabulary(page):
    """Hold every /vocabulary request until released; returns the held routes."""
    held = []
    page.route(VOCABULARY, lambda route: held.append(route))
    return held


def release(held):
    for route in held:
        try:
            route.continue_()
        except PlaywrightError:
            pass  # an attempt the page already abandoned at its timeout


def test_landing_controls_work_while_options_load(page, live_server):
    held = hold_vocabulary(page)
    page.reload(wait_until="domcontentloaded")

    # Only the submit that needs the options waits, and it says why.
    preview_submit = page.locator("#preview-submit")
    expect(preview_submit).to_be_disabled()
    expect(preview_submit).to_have_text(LOADING_LABEL)
    expect(page.locator("#profile-progress-status")).to_have_text(LOADING_STATUS)

    # Account controls render and open.
    page.click("#open-login")
    page.wait_for_selector("#auth-modal[open]")
    page.click("#auth-modal-close")

    # Site nav answers.
    page.click("#nav-plan-btn")
    expect(page.locator("#saved-section")).to_be_visible()
    expect(page.locator("#saved-summary")).to_contain_text("Log in to save")
    page.click("#nav-browse-btn")
    expect(page.locator("#catalog-section")).to_be_visible()
    page.click("#nav-matches-btn")
    page.wait_for_function(
        "() => Math.abs(document.getElementById('profile-form').getBoundingClientRect().top) < 200"
    )

    # The profile form reacts: progress counts the GPA, steps validate, and
    # Enter no longer falls through to a native GET that reloads the page.
    page.fill("#gpa", "3.8")
    expect(page.locator("#profile-progress-label")).to_have_text("1 of 6 essentials")
    page.click("#step-next-btn")
    expect(page.locator("#form-step-error")).to_contain_text("Select your grade level.")
    page.press("#gpa", "Enter")
    page.wait_for_timeout(300)
    assert page.url == f"{live_server}/"

    # All of the above happened with the options request still pending.
    assert page.locator("#preview-grade option").count() == 1

    release(held)
    expect(preview_submit).to_be_enabled()
    expect(preview_submit).to_have_text(READY_LABEL)
    expect(page.locator("#profile-progress-status")).not_to_have_text(LOADING_STATUS)
    assert page.locator("#fields-of-study input[type=checkbox]").count() > 0

    # The late options work end to end.
    page.fill("#preview-gpa", "3.7")
    page.select_option("#preview-grade", "high_school_junior")
    page.select_option("#preview-field", index=1)
    page.click("#preview-submit")
    page.wait_for_selector("#preview-results:not([hidden])", timeout=15000)
    assert page.locator("#preview-cards > *").count() == 3
    assert not page.console_errors, page.console_errors


def test_failed_options_show_an_error_with_an_in_place_retry(page, live_server):
    attempts = []

    def fail(route):
        attempts.append(route.request.url)
        route.fulfill(status=503, content_type="text/plain", body="cold start")

    page.route(VOCABULARY, fail)
    page.reload(wait_until="domcontentloaded")

    preview_error = page.locator("#preview-error")
    expect(preview_error).to_contain_text(OPTIONS_ERROR)
    expect(page.locator("#form-error")).to_contain_text(OPTIONS_ERROR)
    page.wait_for_timeout(1500)
    assert len(attempts) == 2  # the first request plus exactly one automatic retry
    preview_submit = page.locator("#preview-submit")
    expect(preview_submit).to_have_text(READY_LABEL)
    expect(preview_submit).to_be_disabled()
    expect(page.locator("#profile-progress-status")).not_to_have_text(LOADING_STATUS)
    expect(page.locator("#open-login")).to_be_visible()

    # Once the server answers, Try again recovers in place: no reload.
    page.unroute(VOCABULARY)
    preview_error.get_by_role("button", name="Try again").click()
    expect(preview_submit).to_be_enabled()
    expect(preview_error).to_be_hidden()
    expect(page.locator("#form-error")).to_be_hidden()
    assert page.locator("#preview-grade option").count() > 1
    assert page.evaluate("() => document.activeElement.id") == "preview-gpa"
    assert page.url == f"{live_server}/"


def test_hanging_options_request_ends_in_the_error_not_an_endless_wait(page):
    held = hold_vocabulary(page)
    start = time.monotonic()
    page.reload(wait_until="domcontentloaded")

    expect(page.locator("#preview-error")).to_contain_text(OPTIONS_ERROR, timeout=30000)
    waited = time.monotonic() - start
    # Two attempts, each cut off by the client timeout, then the error.
    assert waited >= 16, waited
    assert len(held) == 2
    expect(page.locator("#preview-submit")).to_have_text(READY_LABEL)
    expect(page.locator("#profile-progress-status")).not_to_have_text(LOADING_STATUS)
    expect(page.locator("#form-error").get_by_role("button", name="Try again")).to_be_visible()


def test_saved_profile_prefills_once_late_options_arrive(page):
    signup(page)
    with page.expect_response(
        lambda r: r.url.endswith("/account/profile") and r.request.method == "PUT"
    ):
        fill_profile_and_submit(page)

    held = hold_vocabulary(page)
    page.reload(wait_until="domcontentloaded")

    # The session renders without the options; the prefill waits for them.
    expect(page.locator("#auth-logged-in")).to_be_visible()
    expect(page.locator("#grade-level option")).to_have_count(1)

    release(held)
    expect(page.locator("#grade-level")).to_have_value("high_school_junior")
    expect(page.locator("#fields-of-study input:checked")).to_have_count(1)
    page.wait_for_selector("#results-container .match-card", timeout=25000)
