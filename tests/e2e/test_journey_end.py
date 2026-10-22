"""The end of the flight: the stage leaves with the section.

On the old /journey page the sky, canvas, paper and cards were fixed to the
viewport, and past the track the page slid in underneath them. On the home
page the stage is sticky inside its section, so at the end of the runway it
scrolls away with the page: the profile form below is never covered, and the
last stop (with its "Build my profile" button) is still on screen as the
form arrives. Off screen the flight stops drawing entirely, so the form and
results below it never pay for a WebGL loop.
"""
import pytest

from tests.e2e.flight import CAPABLE, CONSENT, FLY_TO, WAIT_FRAMES, fly_live

LAYOUT = """(() => {
  const stage = document.querySelector('.journey-stage').getBoundingClientRect();
  const form = document.getElementById('profile-form').getBoundingClientRect();
  const cards = [...document.querySelectorAll('.journey-card')]
    .filter((c) => parseFloat(getComputedStyle(c).opacity) > 0.05)
    .map((c) => { const r = c.getBoundingClientRect(); return [Math.round(r.top), Math.round(r.bottom)]; });
  return { stageBottom: stage.bottom, formTop: form.top, cards };
})()"""

# Counts every WebGL draw call, so a test can tell whether the loop is idle.
COUNT_DRAWS = """
(() => {
  window.__draws = 0;
  for (const proto of [window.WebGLRenderingContext, window.WebGL2RenderingContext]) {
    if (!proto) continue;
    for (const name of ['drawElements', 'drawArrays']) {
      const original = proto.prototype[name];
      proto.prototype[name] = function (...args) { window.__draws += 1; return original.apply(this, args); };
    }
  }
})();
"""


@pytest.mark.parametrize("width,height", [(390, 844), (1440, 900)])
def test_stage_scrolls_away_with_the_section(browser, live_server, width, height):
    context = browser.new_context(viewport={"width": width, "height": height})
    context.add_init_script(CONSENT)
    context.add_init_script(CAPABLE)
    page = context.new_page()
    page.goto(live_server, wait_until="load")
    fly_live(page)

    page.evaluate(FLY_TO, 1.0)
    page.evaluate(WAIT_FRAMES, 120)
    end = page.evaluate(LAYOUT)
    # The last stop holds at the end of the runway: its button is the exit.
    last = page.evaluate("getComputedStyle(document.querySelectorAll('.journey-card')[3]).opacity")
    assert float(last) > 0.95, f"the last stop faded before the runway ended: {last}"
    assert end["stageBottom"] <= end["formTop"] + 1, end

    # Half a screen past the runway the form is arriving and nothing covers it.
    page.evaluate(f"window.scrollBy({{top: {height // 2}, behavior: 'instant'}})")
    page.evaluate(WAIT_FRAMES, 20)
    past = page.evaluate(LAYOUT)
    assert past["formTop"] < height, f"the form is not arriving: {past}"
    assert past["stageBottom"] <= past["formTop"] + 1, past
    for top, bottom in past["cards"]:
        assert bottom <= past["formTop"] + 1, f"a stop card covers the profile form: {past}"
    context.close()


def test_flight_stops_drawing_off_screen(browser, live_server):
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.add_init_script(CONSENT)
    context.add_init_script(CAPABLE)
    context.add_init_script(COUNT_DRAWS)
    page = context.new_page()
    page.goto(live_server, wait_until="load")
    fly_live(page)
    page.evaluate(WAIT_FRAMES, 10)
    start = page.evaluate("window.__draws")
    page.evaluate(WAIT_FRAMES, 10)
    assert page.evaluate("window.__draws") > start, "the flight is not drawing while on screen"

    page.evaluate(
        "window.scrollTo({top: document.getElementById('profile-form').getBoundingClientRect().top"
        " + scrollY + 400, behavior: 'instant'})"
    )
    page.wait_for_timeout(800)
    idle = page.evaluate("window.__draws")
    page.wait_for_timeout(1500)
    assert page.evaluate("window.__draws") == idle, "the flight kept drawing while off screen"

    # And it wakes again when the visitor comes back.
    page.evaluate(FLY_TO, 0.5)
    page.wait_for_timeout(1200)
    assert page.evaluate("window.__draws") > idle, "the flight never woke up"
    context.close()
