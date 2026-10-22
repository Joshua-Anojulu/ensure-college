"""The end of the Journey: the flight lands on the dusk band, not over the footer.

The Journey's sky, canvas, paper and cards are fixed to the viewport. Once the
page scrolled past the track, the dusk band and footer slid in underneath
them, and on phones the gate card sat on top of the footer's text and links.
journey.js now lifts those fixed layers by exactly the distance scrolled past
the track, so they leave with the page.
"""
import pytest

from tests.e2e.test_cohesion import CONSENT

END_STATE = """(() => {
  const band = document.querySelector('.world-dusk');
  const footer = document.querySelector('footer.site-footer');
  const canvas = document.getElementById('journey-canvas');
  const cards = [...document.querySelectorAll('.journey-card')]
    .filter((c) => parseFloat(getComputedStyle(c).opacity) > 0.05)
    .map((c) => c.getBoundingClientRect().bottom);
  return {
    bandTop: band.getBoundingClientRect().top,
    footerTop: footer.getBoundingClientRect().top,
    canvasBottom: canvas.getBoundingClientRect().bottom,
    cardBottoms: cards,
  };
})()"""


@pytest.mark.parametrize("width,height", [(390, 844), (1440, 900)])
def test_journey_end_lands_on_the_dusk_band(browser, live_server, width, height):
    context = browser.new_context(viewport={"width": width, "height": height})
    context.add_init_script(CONSENT)
    page = context.new_page()
    page.goto(f"{live_server}/journey", wait_until="load")
    page.wait_for_selector("html.journey-live", state="attached", timeout=30000)

    for fraction in (0.9, 1.0):
        page.evaluate(f"window.scrollTo(0, document.documentElement.scrollHeight * {fraction})")
        page.wait_for_timeout(1200)
        state = page.evaluate(END_STATE)
        assert state["bandTop"] < height, f"the dusk band is not in view at {fraction:.0%}: {state}"
        # The canvas ends at or above the band, and no visible card reaches it.
        assert state["canvasBottom"] <= state["bandTop"] + 1, state
        for bottom in state["cardBottoms"]:
            assert bottom <= state["bandTop"] + 1, f"a Journey card covers the dusk band or footer: {state}"
    context.close()
