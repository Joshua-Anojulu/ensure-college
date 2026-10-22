"""The 3D island, repainted into the World (2026-10-22 plan, scope D).

The Journey flight and the Teaser's live island must read as the same
painted world as the watercolor plates. These gates measure rendered pixels
against a palette sampled from the plates themselves (never from the scene
code): almost every pixel must sit near a plate colour, saturated orange
(the old roofs, desk and autumn trees) and vivid green (the old grass) must
be gone, the shipped grain tile must lie over the canvas as multiplied
paper, and the fog must be the mist token the CSS sky is painted with. The
Teaser's live island must sit close to its own painting in colour, so the
painting-to-live swap is not jarring, and its copy must stay legible over
the live picture. The safety paths still never fetch the dusk plate.

Pixel analysis reuses the cohesion suite's PNG decoder, so the test deps
stay image-library free.
"""
import math

import pytest

from tests.e2e.test_cohesion import CONSENT, _assert_legible, _decode_png, text_over_art
from tests.e2e.test_world import wait_until

# The Teaser keeps its painting on low-end devices (2 cores or 2 GB); these
# gates are about the live island, so they run as a capable device would.
CAPABLE = (
    "Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});"
    "Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});"
)

# Dominant tones of the shipped plates (k-means clusters per plate), plus the
# overlook's landmark accents: trail gold, cabin and desk wood, tower stone.
PLATE_PALETTE = """
f8f9f3 f8f4e5 eaece3 d8dfd0 c1ccb8 a6b49e 859780 5a725f 2e4b3b f8e8c5
e9e9d9 7f8d75 d4d8c6 a0a991 bcc4ae 5b6e59 304939 ede2c0 d6c38f
eaecdf c5d0bf 98aa98 b0bfae 7f9381 365040 5c7462
f5ecdb f6e7cf 21372a f5e0be f4d3a4 394d3d e7bd8b 6b725c a49472
a0ac85 708768 bec9ab d8dfca 395640
e6e8e2 b5c0b0 d2d9ce 364e3e 6b7e6c 98a592
c4a24f d7af5c af923f 827557 8e886d 53482f a7a68e 76735d
""".split()

HIDE_CHROME = (
    ".site-header, .journey-head, .journey-copy-layer, .journey-rail"
    " { visibility: hidden !important; }"
)

WAIT_FRAMES = """(n) => new Promise((resolve) => {
  let k = 0;
  const step = () => { k += 1; if (k >= n) resolve(); else requestAnimationFrame(step); };
  requestAnimationFrame(step);
})"""


def _lab(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(float(v)) for v in rgb)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


PALETTE_LAB = [_lab((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))) for h in PLATE_PALETTE]


def _pixels(png, x_from=0.0, step=3):
    """Every step-th pixel of a screenshot, optionally right of x_from."""
    width, height, bpp, rows = _decode_png(png)
    x0 = int(width * x_from)
    out = []
    for y in range(0, height, step):
        row = rows[y]
        for x in range(x0, width, step):
            k = x * bpp
            out.append((row[k], row[k + 1], row[k + 2]))
    return out


def _paint_report(pixels):
    """How far a frame sits from the plates: share of pixels near a plate
    tone, share of saturated orange, share of vivid green, and mean Lab."""
    near = orange = vivid = 0
    total = [0.0, 0.0, 0.0]
    cache = {}
    for px in pixels:
        lab = cache.get(px)
        if lab is None:
            lab = cache[px] = _lab(px)
        L, a, b = lab
        total[0] += L
        total[1] += a
        total[2] += b
        chroma = math.hypot(a, b)
        hue = math.degrees(math.atan2(b, a)) % 360
        if chroma > 32 and 40 <= hue <= 78 and L > 35:
            orange += 1
        if chroma > 22 and 100 < hue < 170:
            vivid += 1
        if min((L - p[0]) ** 2 + (a - p[1]) ** 2 + (b - p[2]) ** 2 for p in PALETTE_LAB) <= 100:
            near += 1
    n = len(pixels)
    return {
        "near_palette": near / n,
        "orange": orange / n,
        "vivid_green": vivid / n,
        "mean_lab": tuple(v / n for v in total),
    }


def _assert_painted(report, where):
    assert report["near_palette"] >= 0.95, f"{where}: only {report['near_palette']:.1%} of pixels near a plate tone"
    assert report["orange"] < 0.005, f"{where}: saturated orange covers {report['orange']:.2%}"
    assert report["vivid_green"] < 0.02, f"{where}: vivid green covers {report['vivid_green']:.2%}"


def _token(page, name):
    return page.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('{name}').trim()").lower()


def _fly_to(page, stop, frames=80):
    page.evaluate(
        """(stop) => {
          const track = document.getElementById('journey-track');
          const max = track.offsetHeight - window.innerHeight;
          window.scrollTo({ top: stop ? track.offsetTop + max * stop : 0, behavior: 'instant' });
        }""",
        stop,
    )
    page.evaluate(WAIT_FRAMES, frames)


def test_journey_flight_is_painted_from_the_plates(browser, live_server):
    """Start, lanes and gate: every stop is made of plate tones, with no
    saturated orange or vivid green; the grain tile lies over the canvas;
    the fog is the mist token by day and the dawn mist past the gate, where
    the painted sky has crossfaded to the dusk-treeline plate."""
    context = browser.new_context(viewport={"width": 720, "height": 450})
    context.add_init_script(CONSENT)
    page = context.new_page()
    plates = []
    page.on("request", lambda r: plates.append(r.url) if "/static/img/world/" in r.url else None)
    page.goto(f"{live_server}/journey", wait_until="load")
    page.wait_for_selector("html.journey-live", state="attached", timeout=30000)

    paper = page.evaluate(
        """(() => { const s = getComputedStyle(document.querySelector('.journey-paper'));
          return { image: s.backgroundImage, blend: s.mixBlendMode, opacity: parseFloat(s.opacity) }; })()"""
    )
    assert "/static/img/grain.png" in paper["image"], paper
    assert paper["blend"] == "multiply", paper
    assert 0 < paper["opacity"] <= 0.2, paper

    page.add_style_tag(content=HIDE_CHROME)
    _fly_to(page, 0, frames=12)
    assert page.evaluate("document.getElementById('journey-canvas').dataset.fog") == _token(page, "--paint-mist")
    _assert_painted(_paint_report(_pixels(page.screenshot())), "journey start")

    _fly_to(page, 0.36)
    _assert_painted(_paint_report(_pixels(page.screenshot())), "three lanes")

    _fly_to(page, 0.93, frames=110)
    _assert_painted(_paint_report(_pixels(page.screenshot())), "the gate")

    # Past the gate the dawn is complete: the fog is the dawn mist and the
    # sky is the dusk-treeline plate, fetched only now that the flight runs.
    _fly_to(page, 1.0, frames=90)
    assert page.evaluate("document.getElementById('journey-canvas').dataset.fog") == _token(page, "--paint-dawn-mist")
    dawn = page.evaluate(
        """(() => { const s = getComputedStyle(document.querySelector('.journey-sky'), '::after');
          return { opacity: parseFloat(s.opacity), image: s.backgroundImage }; })()"""
    )
    assert dawn["opacity"] == 1, dawn
    assert "dusk-treeline" in dawn["image"], dawn
    assert any("dusk-treeline" in url for url in plates), plates
    context.close()


def test_journey_static_fallback_paints_no_sky(browser, live_server):
    """Reduced motion keeps the static page: no sky layer and no three.js.

    The static page still wears the shared chrome: the forest stage behind
    it and the footer's dusk band (the same dusk-treeline file the sky would
    crossfade to). Those are the only World images it may fetch."""
    context = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    context.add_init_script(CONSENT)
    page = context.new_page()
    fetched = []
    page.on(
        "request",
        lambda r: fetched.append(r.url) if ("/static/img/world/" in r.url or "three.min.js" in r.url) else None,
    )
    page.goto(f"{live_server}/journey", wait_until="networkidle")
    page.wait_for_timeout(600)
    assert page.evaluate("document.documentElement.classList.contains('journey-static')")
    assert page.evaluate("getComputedStyle(document.querySelector('.journey-sky')).display") == "none"
    assert not any("three.min.js" in url for url in fetched), fetched
    chrome = page.evaluate(
        """(() => {
          const urls = [];
          const stage = document.querySelector('.journey-page > .world-stage');
          for (const pseudo of [null, '::before', '::after']) {
            const bg = stage ? getComputedStyle(stage, pseudo).backgroundImage : 'none';
            for (const m of bg.matchAll(/url\\("?([^")]+)"?\\)/g)) urls.push(new URL(m[1], location.href).href);
          }
          const dusk = document.querySelector('.world-dusk img');
          if (dusk && dusk.currentSrc) urls.push(dusk.currentSrc);
          return urls;
        })()"""
    )
    plates = [url for url in fetched if "/static/img/world/" in url]
    assert all(url in chrome for url in plates), (plates, chrome)
    context.close()


def _teaser_page(browser, live_server, width, height, held=None):
    """A capable device on the landing with the Teaser in view. With held
    (a dict), three.js is held back until the test releases held['route']."""
    context = browser.new_context(viewport={"width": width, "height": height})
    context.add_init_script(CONSENT)
    context.add_init_script(CAPABLE)
    page = context.new_page()
    if held is not None:
        page.route("**/three.min.js*", lambda route: held.setdefault("route", route))
    page.goto(live_server, wait_until="load")
    page.evaluate("document.querySelector('.journey-teaser').scrollIntoView({block: 'center', behavior: 'instant'})")
    return context, page


LIVE_SETTLED = """(() => {
  const s = document.querySelector('.journey-teaser');
  if (!s.classList.contains('teaser-live')) return false;
  const veil = getComputedStyle(document.querySelector('.teaser-painting'), '::before').opacity;
  const canvas = getComputedStyle(document.getElementById('journey-teaser-canvas')).opacity;
  const labels = getComputedStyle(document.querySelector('.teaser-landmarks')).opacity;
  return veil === '1' && canvas === '1' && labels === '0';
})()"""

KEEP_IN_VIEW = """(() => {
  const s = document.querySelector('.journey-teaser');
  const r = s.getBoundingClientRect();
  if (r.top < 0 || r.bottom > innerHeight) s.scrollIntoView({block: 'center', behavior: 'instant'});
})()"""


def _wait_live(page, timeout_ms=40000):
    """The swap needs the section in view for a 4s dwell after three.js
    loads; hold it there (the landing can nudge scroll while it boots)."""
    elapsed = 0
    while elapsed <= timeout_ms:
        if page.evaluate(LIVE_SETTLED):
            return
        page.evaluate(KEEP_IN_VIEW)
        page.wait_for_timeout(250)
        elapsed += 250
    raise AssertionError(f"teaser never settled live within {timeout_ms}ms")


def test_teaser_live_island_reads_as_its_painting(browser, live_server):
    """The swap keeps the picture: the live island sits within a small Lab
    distance of the overlook painting it replaces (the old live island on
    the dark wash measured 41.6), is made of plate tones, wears the grain
    as multiplied paper, fogs to the mist token, and the copy stays legible
    over the live picture."""
    held = {}
    context, page = _teaser_page(browser, live_server, 1440, 900, held)
    page.wait_for_selector(".teaser-painting img.world-loaded", state="attached", timeout=20000)
    wait_until(page, "getComputedStyle(document.querySelector('.teaser-landmarks')).opacity === '1'")
    painting = _paint_report(_pixels(page.locator(".journey-teaser").screenshot(), x_from=0.52))

    elapsed = 0
    while "route" not in held and elapsed < 10000:
        page.wait_for_timeout(250)
        elapsed += 250
    assert "route" in held, "three.min.js was never requested on the live path"
    held["route"].continue_()
    _wait_live(page)
    page.wait_for_timeout(300)
    live = _paint_report(_pixels(page.locator(".journey-teaser").screenshot(), x_from=0.52))
    _assert_painted(live, "teaser live island")
    gap = math.dist(painting["mean_lab"], live["mean_lab"])
    assert gap <= 8, f"live island drifts from its painting by dE {gap:.1f}: {painting['mean_lab']} vs {live['mean_lab']}"

    grain = page.evaluate(
        """(() => { const s = getComputedStyle(document.querySelector('.journey-teaser'), '::after');
          return { image: s.backgroundImage, blend: s.mixBlendMode, opacity: parseFloat(s.opacity) }; })()"""
    )
    assert "/static/img/grain.png" in grain["image"], grain
    assert grain["blend"] == "multiply", grain
    assert 0 < grain["opacity"] <= 0.2, grain
    assert page.evaluate("document.getElementById('journey-teaser-canvas').dataset.fog") == _token(page, "--paint-mist")

    _assert_legible(
        text_over_art(page, ["#journey-teaser-title", ".journey-teaser-copy p"]), "teaser copy over the live island"
    )
    context.close()


def test_teaser_canvas_waits_for_the_swap_on_phones(browser, live_server):
    """Phones used to show the canvas at 0.45 opacity before the swap (a
    leftover from the pre-painting teaser), so the island ghosted over the
    painting the moment it initialized. The canvas now stays hidden until
    the swap, then takes exactly the painting's band."""
    context, page = _teaser_page(browser, live_server, 390, 844)
    assert not page.evaluate("document.querySelector('.journey-teaser').classList.contains('teaser-live')")
    assert page.evaluate("getComputedStyle(document.getElementById('journey-teaser-canvas')).opacity") == "0"
    _wait_live(page)
    band = page.evaluate(
        """(() => {
          const c = document.getElementById('journey-teaser-canvas').getBoundingClientRect();
          const p = document.querySelector('.teaser-painting').getBoundingClientRect();
          return [Math.round(c.top), Math.round(c.height), Math.round(p.top), Math.round(p.height)];
        })()"""
    )
    assert band[0] == band[2] and band[1] == band[3], f"canvas band {band[:2]} vs painting band {band[2:]}"
    context.close()
