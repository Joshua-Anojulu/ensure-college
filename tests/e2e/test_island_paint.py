"""The 3D island, painted into the World, flying on the home page.

The Journey is the home page's How it works section (2026-10-22). Its flight
must read as the same painted world as the watercolor plates. These gates
measure rendered pixels against a palette sampled from the plates themselves
(never from the scene code): almost every pixel must sit near a plate colour,
saturated orange (the old roofs, desk and autumn trees) and vivid green (the
old grass) must be gone, the shipped grain tile must lie over the canvas as
multiplied paper, and the fog must be the mist token the CSS sky is painted
with. The home flight keeps its dusk for the band at the page's end, so its
golden hour is capped and it never fetches the dusk plate for its sky.

The section is painting-first: the overlook painting holds the stage until
the island has rendered a frame, then hands over in the same box. Devices
that should not fly keep the static layout and never download three.js.

Pixel analysis reuses the cohesion suite's PNG decoder, so the test deps
stay image-library free.
"""
import math

from tests.e2e.flight import CAPABLE, CONSENT, FLY_TO, WAIT_FRAMES, capable_home, fly_live
from tests.e2e.test_cohesion import _assert_legible, _decode_png, text_over_art
from tests.e2e.test_world import wait_until

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
    ".site-header, .journey-home-head, .journey-stops, .journey-rail"
    " { visibility: hidden !important; }"
)

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
    page.evaluate(FLY_TO, stop)
    page.evaluate(WAIT_FRAMES, frames)


def test_home_flight_is_painted_from_the_plates(browser, live_server):
    """Start, lanes and gate: every stop is made of plate tones, with no
    saturated orange or vivid green; the grain tile lies over the canvas; the
    fog is the mist token by day. Past the gate the golden hour is capped by
    the section (data-dawn-max), and the home sky never uses the dusk plate."""
    context, page = capable_home(browser, live_server, 720, 450)
    assert page.evaluate("document.documentElement.classList.contains('journey-will-fly')")
    fly_live(page)

    paper = page.evaluate(
        """(() => { const s = getComputedStyle(document.querySelector('.journey-paper'));
          return { image: s.backgroundImage, blend: s.mixBlendMode, opacity: parseFloat(s.opacity) }; })()"""
    )
    assert "/static/img/grain.png" in paper["image"], paper
    assert paper["blend"] == "multiply", paper
    assert 0 < paper["opacity"] <= 0.2, paper

    page.add_style_tag(content=HIDE_CHROME)
    _fly_to(page, 0, frames=20)
    assert page.evaluate("document.getElementById('journey-canvas').dataset.fog") == _token(page, "--paint-mist")
    _assert_painted(_paint_report(_pixels(page.screenshot())), "journey start")

    _fly_to(page, 0.36)
    _assert_painted(_paint_report(_pixels(page.screenshot())), "three lanes")

    _fly_to(page, 0.93, frames=110)
    _assert_painted(_paint_report(_pixels(page.screenshot())), "the gate")

    _fly_to(page, 1.0, frames=120)
    cap = float(page.evaluate("document.getElementById('journey-track').dataset.dawnMax"))
    assert 0 < cap < 1, cap
    sky = page.evaluate(
        """(() => { const sky = document.querySelector('.journey-sky');
          const s = getComputedStyle(sky, '::after');
          return { dawn: parseFloat(sky.style.getPropertyValue('--dawn')), opacity: parseFloat(s.opacity), image: s.backgroundImage }; })()"""
    )
    assert abs(sky["dawn"] - cap) <= 0.02, sky
    assert abs(sky["opacity"] - cap) <= 0.02, sky
    assert "url(" not in sky["image"], sky
    fog = page.evaluate("document.getElementById('journey-canvas').dataset.fog")
    assert fog not in (_token(page, "--paint-mist"), _token(page, "--paint-dawn-mist")), fog
    context.close()


def test_home_static_section_paints_no_sky_and_skips_three(browser, live_server):
    """Reduced motion keeps the static layout: the four stops over the
    overlook painting, no sky layer, no canvas, no runway, and no three.js."""
    context = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    context.add_init_script(CONSENT)
    context.add_init_script(CAPABLE)
    page = context.new_page()
    three = []
    page.on("request", lambda r: three.append(r.url) if "three.min.js" in r.url else None)
    page.goto(live_server, wait_until="networkidle")
    page.evaluate("document.getElementById('how-it-works').scrollIntoView({block: 'start', behavior: 'instant'})")
    wait_until(page, "document.querySelector('.journey-painting img.world-loaded') !== null", 15000)
    page.wait_for_timeout(600)
    state = page.evaluate(
        """(() => {
          const track = document.getElementById('journey-track');
          const stage = track.querySelector('.journey-stage');
          return {
            cls: document.documentElement.className,
            sky: getComputedStyle(document.querySelector('.journey-sky')).display,
            canvas: getComputedStyle(document.getElementById('journey-canvas')).display,
            rail: getComputedStyle(document.querySelector('.journey-rail')).display,
            runway: track.offsetHeight - stage.offsetHeight,
            painting: getComputedStyle(document.querySelector('.journey-painting img')).opacity,
            cards: [...document.querySelectorAll('.journey-card')].map((c) => getComputedStyle(c).opacity),
          };
        })()"""
    )
    assert "journey-static" in state["cls"] and "journey-will-fly" not in state["cls"], state
    assert state["sky"] == state["canvas"] == state["rail"] == "none", state
    assert state["runway"] == 0, state
    assert state["painting"] == "1", state
    assert state["cards"] == ["1", "1", "1", "1"], state
    assert three == [], three
    context.close()


def test_painting_holds_the_stage_until_the_island_renders(browser, live_server):
    """Painting-first, in the same box: while three.js is in flight the
    stage shows the overlook painting and the stops already work; once the
    island has rendered a frame the canvas takes over the stage without
    moving it, the live frame is made of plate tones, and the stop copy
    stays legible over the island."""
    held = {}
    context, page = capable_home(browser, live_server, 1440, 900, held)
    page.evaluate(FLY_TO, 0.05)
    wait_until(page, "document.querySelector('.journey-painting img.world-loaded') !== null", 20000)
    elapsed = 0
    while "route" not in held and elapsed < 10000:
        page.wait_for_timeout(250)
        elapsed += 250
    assert "route" in held, "three.min.js was never requested on the live path"
    # The stops run on scroll alone, before three.js arrives.
    wait_until(page, "parseFloat(getComputedStyle(document.querySelector('.journey-card')).opacity) > 0.9", 10000)
    before = page.evaluate(
        """(() => ({
          live: document.documentElement.classList.contains('journey-live'),
          canvas: getComputedStyle(document.getElementById('journey-canvas')).opacity,
          painting: getComputedStyle(document.querySelector('.journey-painting')).opacity,
          card: getComputedStyle(document.querySelector('.journey-card')).opacity,
          stage: JSON.stringify(document.querySelector('.journey-stage').getBoundingClientRect()),
        }))()"""
    )
    assert before["live"] is False, before
    assert before["canvas"] == "0" and before["painting"] == "1", before
    assert float(before["card"]) > 0.9, f"the first stop must work before three.js arrives: {before}"

    held["route"].continue_()
    wait_until(page, "document.documentElement.classList.contains('journey-live')", 40000)
    wait_until(
        page,
        "getComputedStyle(document.getElementById('journey-canvas')).opacity === '1'"
        " && getComputedStyle(document.querySelector('.journey-painting')).opacity === '0'",
        10000,
    )
    after = page.evaluate("JSON.stringify(document.querySelector('.journey-stage').getBoundingClientRect())")
    assert after == before["stage"], (before["stage"], after)
    page.evaluate(WAIT_FRAMES, 30)
    _assert_legible(
        text_over_art(page, [".journey-card.is-active h3", ".journey-card.is-active p"]),
        "the first stop over the live island",
    )
    page.add_style_tag(content=HIDE_CHROME)
    page.evaluate(WAIT_FRAMES, 5)
    _assert_painted(_paint_report(_pixels(page.screenshot())), "live island under the first stop")
    context.close()


def test_phone_canvas_waits_for_the_swap_and_fills_the_stage(browser, live_server):
    """The canvas stays hidden until the island has a frame, then covers
    exactly the stage the painting held."""
    context, page = capable_home(browser, live_server, 390, 844)
    assert page.evaluate("getComputedStyle(document.getElementById('journey-canvas')).opacity") == "0"
    fly_live(page)
    rects = page.evaluate(
        """(() => {
          const r = (el) => { const b = el.getBoundingClientRect(); return [Math.round(b.top), Math.round(b.left), Math.round(b.width), Math.round(b.height)]; };
          return [r(document.getElementById('journey-canvas')), r(document.querySelector('.journey-stage')), r(document.querySelector('.journey-painting'))];
        })()"""
    )
    assert rects[0] == rects[1] == rects[2], rects
    assert rects[1][2] == 390 and rects[1][3] == 844, rects
    context.close()
