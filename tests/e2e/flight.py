"""Shared helpers for driving the home page's How it works flight.

Kept out of the test modules so any suite can import them without import
cycles (test_cohesion imports test_e2e, which needs these too).
"""
from tests.e2e.test_world import wait_until

CONSENT = "window.localStorage.setItem('site_consent_v1', 'yes');"

# Two or fewer cores (or 2 GB) keep the static section; tests about the live
# flight run as a capable device would, everywhere.
CAPABLE = (
    "try {"
    " Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8, configurable: true});"
    " Object.defineProperty(navigator, 'deviceMemory', {get: () => 8, configurable: true});"
    " } catch (e) {}"
)

WAIT_FRAMES = """(n) => new Promise((resolve) => {
  let k = 0;
  const step = () => { k += 1; if (k >= n) resolve(); else requestAnimationFrame(step); };
  requestAnimationFrame(step);
})"""

# Scroll so the flight sits at `stop` (0 = the stage has just pinned, 1 = the
# end of the runway). The runway is the track minus the stuck stage.
FLY_TO = """(stop) => {
  const track = document.getElementById('journey-track');
  const stage = track.querySelector('.journey-stage');
  const top = track.getBoundingClientRect().top + window.scrollY;
  const runway = track.offsetHeight - stage.offsetHeight;
  window.scrollTo({ top: top + runway * stop, behavior: 'instant' });
}"""


def capable_home(browser, live_server, width, height, held=None):
    """A capable device on the home page. With held (a dict), three.js is
    held back until the test releases held['route']."""
    context = browser.new_context(viewport={"width": width, "height": height})
    context.add_init_script(CONSENT)
    context.add_init_script(CAPABLE)
    page = context.new_page()
    if held is not None:
        page.route("**/three.min.js*", lambda route: held.setdefault("route", route))
    page.goto(live_server, wait_until="load")
    return context, page


def fly_live(page, timeout_ms=40000):
    """Bring the section into view and wait for the island's first frame."""
    page.evaluate(FLY_TO, 0)
    wait_until(page, "document.documentElement.classList.contains('journey-live')", timeout_ms)
