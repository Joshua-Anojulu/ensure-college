"""Visual polish pass (2026-10-22, plan section P): pages look put together.

Josh asked for every page to "look put together": no random blank space and
nothing that looks unfinished. Each test here pins one defect measured on
main before the pass and fails on that code.
"""
import pytest

CONSENT = "window.localStorage.setItem('site_consent_v1', 'yes');"


def _context(browser, width, height, **kwargs):
    ctx = browser.new_context(viewport={"width": width, "height": height}, **kwargs)
    ctx.add_init_script(CONSENT)
    return ctx


def _wait_until(page, expression, timeout_ms=10000):
    """Poll from Python: the CSP blocks the poller wait_for_function injects."""
    elapsed = 0
    while elapsed <= timeout_ms:
        if page.evaluate(expression):
            return
        page.wait_for_timeout(200)
        elapsed += 200
    raise AssertionError(f"never became true within {timeout_ms}ms: {expression}")


# ------------------------------------------------------- 1. page endings
#
# Every page ended with the dusk band (300px desktop / 160px phone) and the
# footer (372px / 269px, its ghost wordmark set at 112px / 45px): 672px, 75%
# of a laptop screen, was decoration. On short pages (404, unsubscribe, the
# Browse index) the real content was a sliver at the top of the page.

# Where the flag stands in dusk-treeline-*.webp, as fractions of the
# painting's height: the pennant spans 0.551 to 0.590 and the pole's foot
# meets the hill near 0.69.
PENNANT_TOP = 0.551
POLE_FOOT = 0.69

ENDING = """() => {
  const band = document.querySelector('.world-dusk');
  const img = band.querySelector('img');
  const footer = document.querySelector('footer.site-footer');
  const header = document.querySelector('.site-header');
  const main = document.querySelector('main');
  const lone = main.querySelector(':scope > .panel:only-child');
  const box = img.getBoundingClientRect();
  // object-fit: cover, so the painting scales to cover the band and the
  // band shows a horizontal slice of it set by object-position.
  const scale = Math.max(box.width / img.naturalWidth, box.height / img.naturalHeight);
  const drawn = img.naturalHeight * scale;
  const [, y] = getComputedStyle(img).objectPosition.split(' ');
  const offset = y.endsWith('%') ? (drawn - box.height) * parseFloat(y) / 100 : -parseFloat(y);
  const r = (el) => el.getBoundingClientRect();
  return {
    band: Math.round(r(band).height),
    footer: Math.round(r(footer).height),
    mark: parseFloat(getComputedStyle(footer.querySelector('.footer-mark')).fontSize),
    fullWidth: Math.abs(scale - box.width / img.naturalWidth) < 1e-6,
    drawn, offset, bandH: box.height,
    doc: document.documentElement.scrollHeight,
    footerBottom: r(footer).bottom + scrollY,
    headerBottom: r(header).bottom + scrollY,
    bandTop: r(band).top + scrollY,
    lone: lone ? [r(lone).top + scrollY, r(lone).bottom + scrollY] : null,
  };
}"""


def _ending(page):
    page.evaluate("window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})")
    _wait_until(
        page,
        "(() => { const i = document.querySelector('.world-dusk img');"
        " return i.complete && i.naturalWidth > 0; })()",
    )
    return page.evaluate(ENDING)


SHORT_PAGES = [
    ("404", "/scholarships/no-such-entry"),
    ("unsubscribe", "/reminders/unsubscribe?token=e2e-polish"),
    ("browse", "/browse"),
]


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_page_ending_is_compact_and_keeps_the_flag(browser, live_server, width, height):
    ctx = _context(browser, width, height)
    page = ctx.new_page()
    desktop = width >= 1024
    for name, path in SHORT_PAGES + [("privacy", "/privacy"), ("landing", "/")]:
        page.goto(f"{live_server}{path}", wait_until="load")
        state = _ending(page)
        where = f"{width}px {name}"
        if desktop:
            assert 150 <= state["band"] <= 200, f"{where}: dusk band {state['band']}px"
            assert state["footer"] <= 200, f"{where}: footer {state['footer']}px"
            assert state["mark"] <= 28, f"{where}: footer wordmark {state['mark']}px"
        else:
            assert 96 <= state["band"] <= 120, f"{where}: dusk band {state['band']}px"
            assert state["footer"] <= 240, f"{where}: footer {state['footer']}px"
            assert state["mark"] <= 24, f"{where}: footer wordmark {state['mark']}px"
        # The ending stays well under half a screen.
        assert state["band"] + state["footer"] <= 0.45 * height, f"{where}: ending {state}"
        # The painting still reads: the flag's pennant clears the band's top
        # fade and the pole's foot on the hill stays inside the band.
        assert state["fullWidth"], f"{where}: the painting no longer spans the band"
        pennant = PENNANT_TOP * state["drawn"] - state["offset"]
        foot = POLE_FOOT * state["drawn"] - state["offset"]
        assert pennant >= 0.2 * state["bandH"], f"{where}: the flag sits in the top fade ({pennant:.0f}px)"
        assert foot <= state["bandH"], f"{where}: the flag's foot is cut off ({foot:.0f}px of {state['bandH']})"
    ctx.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_short_pages_fill_the_screen_and_center_a_lone_panel(browser, live_server, width, height):
    ctx = _context(browser, width, height)
    page = ctx.new_page()
    fits = [("404", "/scholarships/no-such-entry"), ("unsubscribe", "/reminders/unsubscribe?token=e2e-polish")]
    if width >= 1024:
        fits.append(("browse", "/browse"))
    for name, path in fits:
        page.goto(f"{live_server}{path}", wait_until="load")
        state = _ending(page)
        where = f"{width}px {name}"
        # The page is one screen and the footer closes it at the bottom edge.
        assert state["doc"] <= height, f"{where}: {state['doc']}px tall in a {height}px window"
        assert abs(state["footerBottom"] - height) <= 1, f"{where}: footer ends at {state['footerBottom']}"
        if name != "browse":
            # A lone panel sits in the middle of the space it has, not at the
            # top of an empty stretch of page.
            top, bottom = state["lone"]
            above, below = top - state["headerBottom"], state["bandTop"] - bottom
            assert min(above, below) >= 16, f"{where}: panel {above:.0f}px below the header, {below:.0f}px above the band"
            assert abs(above - below) <= 24, f"{where}: panel off center ({above:.0f} above, {below:.0f} below)"
    ctx.close()


# ------------------------------------------- 3. highlight boxes, long values
#
# The award / cost / recognition / dates / deadline boxes assumed a short
# figure like "$20,000". A long value (Conrad Challenge's prize terms, 319
# characters) rendered as a 151px-wide, 1203px-tall column of 24px bold gold
# text on a phone, overflowing its box, and its short neighbour ("Deadline")
# stretched to the same height and sat empty.

STATS = """(root) => Array.from((root || document).querySelectorAll('.card-stats')).map((row) => ({
  width: row.getBoundingClientRect().width,
  stats: Array.from(row.children).map((s) => {
    const v = s.querySelector('.stat-value');
    const cs = getComputedStyle(v);
    const box = s.getBoundingClientRect();
    const content = Math.max(...Array.from(s.children).map((c) => c.getBoundingClientRect().bottom)) - box.top
      + parseFloat(getComputedStyle(s).paddingBottom);
    return {
      long: s.classList.contains('stat-long'),
      award: s.classList.contains('stat-award'),
      len: v.textContent.trim().length,
      font: parseFloat(cs.fontSize),
      weight: parseInt(cs.fontWeight, 10),
      width: box.width,
      height: box.height,
      slack: box.height - content,
      overflow: v.scrollWidth - v.clientWidth,
    };
  }),
}))"""


def _assert_long_values_read_calmly(rows, where, phone):
    seen_long = False
    for row in rows:
        stats = row["stats"]
        has_long = any(s["len"] > 24 for s in stats)
        for s in stats:
            assert s["overflow"] <= 1, f"{where}: a value spills out of its box: {s}"
            if s["len"] > 24:
                seen_long = True
                assert s["long"], f"{where}: a {s['len']}-character value is not marked long: {s}"
                assert s["font"] <= 15 and s["weight"] < 700, f"{where}: long value still set as a headline: {s}"
                if phone:
                    assert s["width"] >= 0.9 * row["width"], f"{where}: long value squeezed into a narrow column: {s}"
            else:
                assert not s["long"], f"{where}: a short value is marked long: {s}"
                if has_long:
                    # A short neighbour keeps its own height.
                    assert s["slack"] <= 2, f"{where}: short box stretched to a long neighbour: {s}"
    assert seen_long, f"{where}: no long value on the page"


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_opportunity_page_long_values_read_calmly(browser, live_server, width, height):
    ctx = _context(browser, width, height)
    page = ctx.new_page()
    for path in ("/competitions/conrad-challenge", "/programs/ala-girls-state"):
        page.goto(f"{live_server}{path}", wait_until="load")
        _assert_long_values_read_calmly(page.evaluate(STATS), f"{width}px {path}", width < 760)
    # A real figure keeps the headline treatment.
    page.goto(f"{live_server}/scholarships/coca-cola-scholars", wait_until="load")
    award = page.evaluate(STATS)[0]["stats"][0]
    assert award["award"] and not award["long"], award
    assert award["font"] == 24 and award["weight"] == 800, f"the short award lost its headline style: {award}"
    ctx.close()


LONG_AWARD = "Tuition, fees, and books for residents; a non-resident tuition waiver for out-of-state students"
LONG_RECOGNITION = (
    "Winning teams receive academic scholarships, an all-expenses-paid trip, free patent support "
    "from IP lawyers, and honors including scholar titles"
)
LONG_DATES = "Registration opens July 15 and closes December 6; qualification flights run through spring"


def test_match_cards_long_values_read_calmly(browser, live_server):
    from tests.e2e.test_e2e import (
        competition_match,
        program_match,
        route_match_fixtures,
        scholarship_match,
        submit_profile_form,
    )

    for width, height in ((390, 844), (1440, 900)):
        ctx = _context(browser, width, height)
        page = ctx.new_page()
        scholarship = dict(scholarship_match("fixture-long-award", "Fixture Long Award"), award_amount=LONG_AWARD)
        short = scholarship_match("fixture-short-award", "Fixture Short Award")
        program = dict(program_match("fixture-program", "Fixture Program"), cost=LONG_AWARD, program_dates=LONG_DATES)
        competition = dict(
            competition_match("fixture-competition", "Fixture Competition"),
            recognition=LONG_RECOGNITION,
            competition_dates=LONG_DATES,
        )
        route_match_fixtures(page, scholarships=[scholarship, short], programs=[program], competitions=[competition])
        page.goto(live_server, wait_until="domcontentloaded")
        submit_profile_form(page)
        page.wait_for_selector("#results-container .match-card", timeout=25000)
        page.wait_for_timeout(400)
        where = f"{width}px"
        rows = page.evaluate(STATS, None)
        _assert_long_values_read_calmly(rows, f"{where} scholarship cards", width < 760)
        figures = [s for row in rows for s in row["stats"] if s["award"] and not s["long"]]
        assert figures and all(s["font"] == 24 for s in figures), f"{where}: short award lost its headline: {figures}"
        for tab, container in (("#tab-programs", "#programs-container"), ("#tab-competitions", "#competitions-container")):
            page.click(tab)
            page.wait_for_selector(f"{container} .match-card", timeout=15000)
            page.wait_for_timeout(300)
            rows = page.evaluate(STATS.replace("(root || document)", f"document.querySelector('{container}')"), None)
            _assert_long_values_read_calmly(rows, f"{where} {container}", width < 760)
        ctx.close()


# ------------------------------------------ 4. plan panels that say "none"
#
# The signed-in plan showed a "Recommendation letters needed" panel whose
# only content was "None of your saved items require recommendation
# letters", a "Special eligibility checks" section that only said none were
# detected, and the word "None" in every empty cell of the requirement
# matrix (11 of 18 cells for three typical saves). The command center
# ("What needs attention next") already reports both counts.

PLAIN = ["gates-scholarship", "burger-king-scholars"]  # no letters, no special checks
WITH_LETTERS = "dell-scholars"  # asks for a recommendation letter
WITH_SPECIAL = "terry-foundation-scholarship"  # carries a special eligibility check

PLAN = """() => {
  const shown = (el) => Boolean(el) && !el.closest('[hidden]') && el.getClientRects().length > 0;
  const cells = Array.from(document.querySelectorAll('.plan-table tbody td')).map((td) => {
    const sr = td.querySelector('.visually-hidden');
    const srBox = sr && sr.getBoundingClientRect();
    return {
      visible: (sr ? td.textContent.replace(sr.textContent, '') : td.textContent).trim(),
      spoken: td.textContent.trim(),
      srHidden: !sr || (srBox.width <= 1 && srBox.height <= 1),
    };
  });
  const card = (title) => Array.from(document.querySelectorAll('.plan-card'))
    .find((c) => c.querySelector('h4').textContent.trim() === title);
  return {
    recPanel: shown(document.getElementById('rec-letters-panel')),
    recRows: document.querySelectorAll('#rec-letters-list .rec-letter-need').length,
    specialPanel: shown(document.querySelector('.plan-special-panel')),
    specialCards: document.querySelectorAll('.plan-special-panel .special-check-card').length,
    specialStat: card('Special checks') ? card('Special checks').querySelector('p').textContent.trim() : null,
    recommendations: card('Recommendations') ? card('Recommendations').querySelector('p').textContent.trim() : null,
    cells,
  };
}"""


def _save(page, scholarship_id):
    status = page.evaluate(
        "(id) => fetch('/account/saved/' + encodeURIComponent(id), {method: 'POST'}).then((r) => r.status)",
        scholarship_id,
    )
    assert status in (200, 201), (scholarship_id, status)


def _open_plan(page):
    page.click("#nav-plan-btn")
    page.wait_for_selector("#saved-container .plan-guidance", timeout=15000)
    page.wait_for_timeout(300)
    return page.evaluate(PLAN)


def test_plan_hides_panels_that_only_say_none(browser, live_server):
    from tests.e2e.test_e2e import signup

    ctx = _context(browser, 1440, 900)
    page = ctx.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    signup(page)
    for scholarship_id in PLAIN:
        _save(page, scholarship_id)
    plan = _open_plan(page)

    assert not plan["recPanel"], "the letters panel shows with no letters to ask for"
    assert not plan["specialPanel"], "the special-checks section shows with nothing to check"
    # Nothing is lost: the command center still states both.
    assert plan["specialStat"] == "0 to confirm", plan["specialStat"]
    assert plan["recommendations"] == "No unfinished recommendation steps detected.", plan["recommendations"]
    # Empty matrix cells are quiet on screen and still read "None" aloud.
    empty = [c for c in plan["cells"] if not c["visible"]]
    assert empty, plan["cells"]
    assert all(c["visible"] != "None" for c in plan["cells"]), "the matrix still prints None"
    assert all(c["spoken"] == "None" and c["srHidden"] for c in empty), empty
    assert any("/" in c["visible"] for c in plan["cells"]), "the step counts disappeared"

    # Saving items that need a letter and a special check brings both back.
    _save(page, WITH_LETTERS)
    _save(page, WITH_SPECIAL)
    page.click("#nav-matches-btn")
    plan = _open_plan(page)
    assert plan["recPanel"] and plan["recRows"] >= 1, plan
    assert plan["specialPanel"] and plan["specialCards"] >= 1, plan
    assert plan["specialStat"] == "1 to confirm", plan["specialStat"]
    ctx.close()
