"""UI cohesion pass (2026-10-17): regressions the request suite cannot see.

Each group pins one visible defect found in the audit: layouts that scrolled
sideways on phones, focus rings that vanished on dark surfaces, text that
rode illustrated art below WCAG contrast, and components that drifted from
the Forest Light system.
"""
import struct
import time
import zlib

import pytest

from tests.e2e.test_e2e import fill_profile_and_submit

CONSENT = "window.localStorage.setItem('site_consent_v1', 'yes');"
SIDEWAYS = "() => document.documentElement.scrollWidth - window.innerWidth"


def _context(browser, width, height=844, **kwargs):
    ctx = browser.new_context(viewport={"width": width, "height": height}, **kwargs)
    ctx.add_init_script(CONSENT)
    return ctx


def _rgb(css):
    """'rgb(1, 2, 3)' / 'rgba(1, 2, 3, 0.5)' / 'color(srgb r g b / a)' -> (r, g, b, a)."""
    css = css.strip()
    if css.startswith("color(srgb"):
        parts = css[len("color(srgb") : -1].replace("/", " ").split()
        vals = [float(v) for v in parts]
        return (vals[0] * 255, vals[1] * 255, vals[2] * 255, vals[3] if len(vals) > 3 else 1.0)
    parts = css[css.index("(") + 1 : -1].replace("/", " ").replace(",", " ").split()
    vals = [float(v) for v in parts]
    return (vals[0], vals[1], vals[2], vals[3] if len(vals) > 3 else 1.0)


def _luminance(rgb):
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2])


def contrast(a, b):
    """WCAG contrast ratio of two opaque colors (alpha composited onto b first)."""
    a, b = _rgb(a) if isinstance(a, str) else a, _rgb(b) if isinstance(b, str) else b
    alpha = a[3]
    a = tuple(a[i] * alpha + b[i] * (1 - alpha) for i in range(3))
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _sign_up(page):
    page.wait_for_selector("#auth-logged-out:not([hidden])")
    page.click("#open-signup")
    page.wait_for_selector("#auth-modal[open]")
    page.fill("#auth-email", f"cohesion-{int(time.time() * 1000)}@example.com")
    page.fill("#auth-password", "cohesion-password-123")
    page.click("#auth-submit")
    page.wait_for_selector("#auth-logged-in:not([hidden])", timeout=15000)


# ------------------------------------------------- no sideways scroll


TEMPLATE_PAGES = [
    "/browse/competitions",
    "/browse/programs",
    "/scholarships/coca-cola-scholars",
    "/guides/essays",
    "/journey",
    "/privacy",
    "/scholarships/does-not-exist",
]


@pytest.mark.parametrize("width", [320, 390, 1440])
def test_template_family_never_scrolls_sideways(browser, live_server, width):
    """The template header's three links wrapped into stacked fragments and
    pushed every Opportunity page 10-80px wide on phones, and directory meta
    (a competition's whole recognition paragraph, nowrap) ran 3000px wide."""
    ctx = _context(browser, width, reduced_motion="reduce")
    page = ctx.new_page()
    for path in TEMPLATE_PAGES:
        page.goto(f"{live_server}{path}", wait_until="load")
        assert page.evaluate(SIDEWAYS) <= 0, f"{path} scrolls sideways at {width}px"
    ctx.close()


@pytest.mark.parametrize("width", [390, 1440])
def test_directory_meta_wraps_inside_the_list(browser, live_server, width):
    ctx = _context(browser, width)
    page = ctx.new_page()
    for kind in ("competitions", "programs"):
        page.goto(f"{live_server}/browse/{kind}", wait_until="load")
        escaped = page.evaluate(
            """() => {
              const list = document.querySelector('.browse-list').getBoundingClientRect();
              return Array.from(document.querySelectorAll('.browse-row-meta'))
                .filter((m) => m.getBoundingClientRect().right > list.right + 1).length;
            }"""
        )
        assert escaped == 0, f"{escaped} {kind} rows push their meta outside the list"
    ctx.close()


def test_signed_in_header_fits_a_phone(browser, live_server):
    ctx = _context(browser, 390)
    page = ctx.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    _sign_up(page)
    # Widest case: a saved-count bubble beside Saved.
    page.evaluate(
        "() => { const c = document.getElementById('saved-count'); c.hidden = false; c.textContent = '12'; }"
    )
    assert page.evaluate(SIDEWAYS) <= 0
    heights = page.eval_on_selector_all(
        "#auth-logged-in button", "els => els.map((b) => b.getBoundingClientRect().height)"
    )
    assert heights and max(heights) < 48, f"an account button wrapped to two lines: {heights}"
    # The brand link keeps its accessible name while the wordmark yields.
    assert page.get_attribute(".site-header .brand-link", "aria-label") == "EnsureCollege home"
    ctx.close()


def test_stacked_quick_apply_rows_share_one_left_edge(browser, live_server):
    """Below 760px rows stack; centering them staggered every row's edge."""
    ctx = _context(browser, 390)
    page = ctx.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    fill_profile_and_submit(page)
    page.click("#tab-saved")
    page.wait_for_selector("#quick-applies-list .quick-apply-row", timeout=15000)
    offsets = page.eval_on_selector_all(
        "#quick-applies-list .quick-apply-row",
        """rows => rows.map((row) => {
          const left = row.querySelector('.quick-apply-left').getBoundingClientRect().left;
          const link = row.querySelector('.quick-apply-link').getBoundingClientRect().left;
          return Math.round(Math.abs(left - link));
        })""",
    )
    assert offsets and max(offsets) <= 1, f"row parts start at different edges: {offsets}"
    ctx.close()


# ------------------------------------------------- focus on dark bands


def _keyboard_focus(page, selector):
    """Focus via the keyboard so :focus-visible applies (a programmatic
    focus() after the consent click does not match it in Chromium)."""
    page.evaluate(
        "(s) => { const el = document.querySelector(s); el.scrollIntoView({block: 'center'}); el.focus(); }",
        selector,
    )
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    return page.evaluate(
        """(s) => {
          const el = document.querySelector(s);
          const st = getComputedStyle(el);
          return {visible: el === document.activeElement && el.matches(':focus-visible'),
                  style: st.outlineStyle, color: st.outlineColor};
        }""",
        selector,
    )


@pytest.mark.parametrize(
    "selector,band",
    [
        (".site-footer .footer-links a", ".site-footer"),
        (".journey-teaser-cta", ".teaser-painting::after"),
    ],
)
def test_focus_ring_reads_on_dark_bands(page, selector, band):
    """The brand-colored ring sat on the brand footer and the dusk teaser:
    keyboard focus there was invisible (1.0:1 against the footer)."""
    ring = _keyboard_focus(page, selector)
    assert ring["visible"] and ring["style"] != "none", ring
    if band.endswith("::after"):
        # The teaser CTA rides the dusk scrim, whose darkest stop is brand-strong.
        backdrop = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--brand-strong')")
        backdrop = page.evaluate(
            "(hex) => { const d = document.createElement('div'); d.style.color = hex;"
            " document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; }",
            backdrop.strip(),
        )
    else:
        backdrop = page.evaluate(f"getComputedStyle(document.querySelector('{band}')).backgroundColor")
    ratio = contrast(ring["color"], backdrop)
    assert ratio >= 3, f"{selector} focus ring {ring['color']} on {backdrop}: {ratio:.2f}:1"


# ------------------------------------------------- text over world art
#
# Text over illustrated art cannot be checked from computed styles alone,
# so these gates measure pixels: record each text line box and its color,
# hide all text, screenshot the backdrop, and composite the text color over
# every backdrop pixel inside its line boxes. The 10th percentile (where
# glyphs land on the busiest art) must meet WCAG: 4.5:1, or 3:1 for large.


def _decode_png(data):
    """Minimal PNG decoder (8-bit RGB/RGBA, non-interlaced): Playwright's
    screenshots, without adding an image library to the test deps."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat = 8, []
    width = height = bpp = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind, chunk = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type, _c, _f, interlace = struct.unpack(">IIBBBBB", chunk)
            assert depth == 8 and interlace == 0 and color_type in (2, 6), (depth, color_type)
            bpp = 3 if color_type == 2 else 4
        elif kind == b"IDAT":
            idat.append(chunk)
        elif kind == b"IEND":
            break
    raw = zlib.decompress(b"".join(idat))
    stride = width * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(height):
        kind = raw[i]
        line = bytearray(raw[i + 1 : i + 1 + stride])
        i += 1 + stride
        if kind == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif kind == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif kind == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif kind == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b, c = prev[x], (prev[x - bpp] if x >= bpp else 0)
                p_ = a + b - c
                pa, pb, pc = abs(p_ - a), abs(p_ - b), abs(p_ - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return width, height, bpp, rows


TEXT_BOXES = """(selector) => {
  const out = [];
  for (const el of document.querySelectorAll(selector)) {
    const cs = getComputedStyle(el);
    let op = 1;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) op *= Number(getComputedStyle(n).opacity || 1);
    const rects = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim() || getComputedStyle(node.parentElement).color !== cs.color) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      for (const r of range.getClientRects()) {
        if (r.width > 1 && r.height > 1 && r.top >= 0 && r.bottom <= innerHeight) {
          rects.push([r.left, r.top, r.width, r.height]);
        }
      }
    }
    const size = parseFloat(cs.fontSize);
    const large = size >= 24 || (size >= 18.66 && Number(cs.fontWeight) >= 700);
    if (rects.length) out.push({color: cs.color, op, rects, need: large ? 3 : 4.5});
  }
  return out;
}"""

HIDE_TEXT = (
    "*, *::before, *::after { color: transparent !important;"
    " text-shadow: none !important; caret-color: transparent !important; }"
)


def text_over_art(page, selectors):
    """Worst-10% contrast per selector: {selector: (p10, need)}."""
    boxes = {s: page.evaluate(TEXT_BOXES, s) for s in selectors}
    assert all(boxes.values()), f"no visible text for {[s for s, b in boxes.items() if not b]}"
    every = [r for items in boxes.values() for item in items for r in item["rects"]]
    x0 = max(0, int(min(r[0] for r in every)))
    y0 = max(0, int(min(r[1] for r in every)))
    x1 = int(max(r[0] + r[2] for r in every)) + 1
    y1 = int(max(r[1] + r[3] for r in every)) + 1
    page.add_style_tag(content=HIDE_TEXT)
    page.wait_for_timeout(150)
    png = page.screenshot(clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0})
    width, height, bpp, rows = _decode_png(png)
    results = {}
    for selector, items in boxes.items():
        ratios, need = [], 3
        for item in items:
            fg = _rgb(item["color"])
            fg = (fg[0], fg[1], fg[2], fg[3] * item["op"])
            need = max(need, item["need"])
            for rx, ry, rw, rh in item["rects"]:
                for y in range(max(0, int(ry) - y0), min(height, int(ry + rh) - y0), 2):
                    row = rows[y]
                    for x in range(max(0, int(rx) - x0), min(width, int(rx + rw) - x0), 2):
                        k = x * bpp
                        ratios.append(contrast(fg, (row[k], row[k + 1], row[k + 2], 1.0)))
        ratios.sort()
        results[selector] = (round(ratios[len(ratios) // 10], 2), need)
    return results


def _assert_legible(results, where):
    failing = {s: r for s, r in results.items() if r[0] < r[1]}
    assert not failing, f"{where}: worst-10% contrast below WCAG: {failing}"


@pytest.mark.parametrize("width", [390, 820, 1440])
def test_teaser_copy_reads_over_the_painting(browser, live_server, width):
    """Mobile measured 1.1:1 (white copy on the pale overlook), tablet 2.8:1,
    desktop's paragraph 4.0:1. Static painting mode (reduced motion)."""
    ctx = _context(browser, width, height=900, reduced_motion="reduce")
    page = ctx.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    page.evaluate("document.querySelector('.journey-teaser').scrollIntoView({block: 'center'})")
    page.wait_for_selector(".teaser-painting img.world-loaded", state="attached", timeout=15000)
    page.wait_for_timeout(700)
    results = text_over_art(page, ["#journey-teaser-title", ".journey-teaser-copy p"])
    _assert_legible(results, f"teaser at {width}px")
    ctx.close()


@pytest.mark.parametrize("width", [820, 1440])
def test_template_page_text_reads_over_the_frame(browser, live_server, width):
    """Breadcrumbs, eyebrows, and lane summaries start inside the canopy and
    fern band: 1.4-3.9:1 before the frame learned to recede."""
    ctx = _context(browser, width, height=900)
    page = ctx.new_page()
    for path, selectors in (
        ("/browse/competitions", [".detail-breadcrumb", ".results-header .eyebrow", ".results-summary"]),
        ("/guides/essays", [".results-header .eyebrow", ".results-summary"]),
    ):
        page.goto(f"{live_server}{path}", wait_until="load")
        page.wait_for_timeout(300)
        _assert_legible(text_over_art(page, selectors), f"{path} at {width}px")
    ctx.close()


def test_short_lane_header_reads_over_the_stage(page):
    """An empty catalog search left the lane summary on the stage's edge
    trees (2.4:1); the lane mist keeps header copy on paper."""
    page.click("#nav-browse-btn")
    page.wait_for_selector("#catalog-section:not([hidden]) .match-card", timeout=20000)
    page.click(".catalog-kind-tab[data-kind=programs]")
    page.fill("#catalog-search", "zzzzqqqq")
    page.wait_for_selector("#catalog-empty:not([hidden]), #catalog-container .results-empty", timeout=10000)
    page.wait_for_selector("html.world-ready", state="attached", timeout=10000)
    page.evaluate(
        "window.scrollTo({top: document.querySelector('#catalog-section').getBoundingClientRect().top"
        " + scrollY - 76, behavior: 'instant'})"
    )
    page.wait_for_timeout(900)
    results = text_over_art(page, ["#catalog-section .results-header .eyebrow", "#catalog-summary"])
    _assert_legible(results, "empty catalog lane")


def test_journey_rail_stops_read_before_they_are_reached(page, live_server):
    """Unreached rail stops sat at 0.55 opacity over the scene: 2.2:1."""
    page.goto(f"{live_server}/journey", wait_until="load")
    page.wait_for_selector("html.journey-live", state="attached", timeout=15000)
    page.wait_for_timeout(1200)
    results = text_over_art(page, [".journey-rail button:not(.is-active)"])
    _assert_legible(results, "journey rail")


EFFECTIVE_COLORS = """(selector) => Array.from(document.querySelectorAll(selector)).slice(0, 6).map((el) => {
  const parse = (c) => {
    const m = c.match(/[\\d.]+/g).map(Number);
    const k = c.startsWith('color(srgb') ? 255 : 1;
    return [m[0] * k, m[1] * k, m[2] * k, m.length > 3 ? m[3] : 1];
  };
  let op = 1;
  for (let n = el; n && n.nodeType === 1; n = n.parentElement) op *= Number(getComputedStyle(n).opacity || 1);
  const layers = [];
  for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
    const bg = parse(getComputedStyle(n).backgroundColor);
    if (bg[3] > 0) { layers.push(bg); if (bg[3] >= 1) break; }
  }
  let base = parse(getComputedStyle(document.body).backgroundColor);
  for (const l of layers.reverse()) base = base.map((v, i) => i < 3 ? l[i] * l[3] + v * (1 - l[3]) : 1);
  return {color: getComputedStyle(el).color, op, bg: 'rgb(' + base.slice(0, 3).map(Math.round).join(', ') + ')'};
})"""


def _assert_effective_contrast(page, selector, need=4.5):
    found = page.evaluate(EFFECTIVE_COLORS, selector)
    assert found, f"nothing rendered for {selector}"
    for item in found:
        fg = _rgb(item["color"])
        ratio = contrast((fg[0], fg[1], fg[2], fg[3] * item["op"]), item["bg"])
        assert ratio >= need, f"{selector}: {item['color']} at opacity {item['op']} on {item['bg']} = {ratio:.2f}:1"


def test_small_labels_on_cards_and_tints_pass_contrast(page):
    """--muted-2 text measured 3.4-3.7:1 and --accent-deep on the amber tints
    4.49:1; small labels now use --muted and --amber-strong."""
    fill_profile_and_submit(page)
    page.wait_for_timeout(1500)  # let the cards' arrival animation settle
    for selector in (".fit-ring-num span", ".verification-stale-flag", ".badge-closing, .badge-special, .badge-school"):
        _assert_effective_contrast(page, f"#results-container {selector}")
    page.click("#tab-programs")
    page.wait_for_selector("#programs-container .match-card", timeout=20000)
    page.wait_for_timeout(1500)
    _assert_effective_contrast(page, "#programs-container .card-program-meta")


def test_journey_map_stops_ahead_stay_legible(page):
    """A new plan's stops ahead were dimmed to 0.55 opacity: labels 3.65:1,
    badges 2.13:1. They now recede by color."""
    _sign_up(page)
    page.click("#nav-plan-btn")
    page.wait_for_selector("#journey-map:not([hidden]) .journey-stop.is-ahead", timeout=15000)
    _assert_effective_contrast(page, ".journey-stop.is-ahead .journey-stop-label")
    _assert_effective_contrast(page, ".journey-stop.is-ahead .journey-stop-badge")


# ------------------------------------------------- components back on system


@pytest.mark.parametrize(
    "path",
    [
        "/browse",
        "/browse/scholarships",
        "/guides/essays",
        "/guides/essays/identity",
        "/scholarships/coca-cola-scholars",
        "/scholarships/does-not-exist",
        "/privacy",
        "/terms",
    ],
)
def test_server_pages_have_one_h1_and_no_skipped_levels(page, live_server, path):
    """Browse, guide, and 404 pages had no h1 (their titles were h2/h3) and
    the guide jumped from its title to h3/h4."""
    page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
    levels = page.eval_on_selector_all(
        "main h1, main h2, main h3, main h4, main h5, main h6",
        "els => els.filter((h) => h.getClientRects().length).map((h) => Number(h.tagName[1]))",
    )
    assert levels.count(1) == 1, f"{path}: h1 count {levels.count(1)} in {levels}"
    assert levels[0] == 1, f"{path}: first heading is h{levels[0]}"
    skips = [(a, b) for a, b in zip(levels, levels[1:]) if b > a + 1]
    assert not skips, f"{path}: heading levels skip {skips} in {levels}"


@pytest.mark.parametrize("path", ["/privacy", "/terms"])
def test_legal_pages_carry_the_site_chrome(page, live_server, path):
    """Legal pages had no skip link, no favicon, and a footer without the
    wordmark that strung its links on stray middots."""
    page.goto(f"{live_server}{path}", wait_until="load")
    assert page.locator('link[rel="icon"][href^="/static/favicon.svg"]').count() == 1
    assert page.locator(".site-footer .footer-mark").count() == 1
    assert page.locator(".footer-links span").count() == 0
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.className") == "skip-link"
    page.keyboard.press("Enter")
    assert page.evaluate("location.hash") == "#main"
    assert page.locator("main#main").count() == 1
    eyebrow = page.evaluate(
        "(() => { const s = getComputedStyle(document.querySelector('.legal-content .eyebrow'));"
        " return [s.color, s.fontSize]; })()"
    )
    accent = page.evaluate(
        "(() => { const d = document.createElement('div'); d.style.color = 'var(--accent-deep)';"
        " document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })()"
    )
    assert eyebrow == [accent, "11.2px"], f"legal eyebrow renders as body text: {eyebrow}"


@pytest.mark.parametrize("width", [390, 1440])
def test_footer_links_start_on_the_footer_text_edge(browser, live_server, width):
    """Footer links were centered inside a 52ch box beneath left-aligned
    footer text, so every row started at a different edge."""
    ctx = _context(browser, width)
    page = ctx.new_page()
    for path in ("/", "/browse", "/privacy"):
        page.goto(f"{live_server}{path}", wait_until="load")
        edges = page.evaluate(
            """() => {
              const text = document.querySelector('.site-footer > p:not(.footer-links)');
              const links = Array.from(document.querySelectorAll('.footer-links a'));
              const rows = new Map();
              for (const a of links) {
                const r = a.getBoundingClientRect();
                const key = Math.round(r.top);
                rows.set(key, Math.min(rows.get(key) ?? Infinity, r.left));
              }
              return {text: text.getBoundingClientRect().left, rows: Array.from(rows.values())};
            }"""
        )
        off = [round(left - edges["text"]) for left in edges["rows"]]
        assert all(abs(o) <= 1 for o in off), f"{path} at {width}px: link rows start {off}px off the text edge"
    ctx.close()


def _png_mean(page, clip):
    width, height, bpp, rows = _decode_png(page.screenshot(clip=clip))
    total = [0, 0, 0]
    count = 0
    for row in rows:
        for x in range(0, width * bpp, bpp * 3):
            total[0] += row[x]
            total[1] += row[x + 1]
            total[2] += row[x + 2]
            count += 1
    return tuple(v / count for v in total)


def test_profile_form_face_is_plain_paper(page):
    """The stacked sheet behind the form painted over the form's own face
    (the form is its own stacking context), tinting it green with tilted
    seams. The face reads as --surface now."""
    page.evaluate(
        "window.scrollTo({top: document.querySelector('#profile-form').getBoundingClientRect().top"
        " + scrollY - 80, behavior: 'instant'})"
    )
    page.wait_for_timeout(500)
    box = page.evaluate(
        """() => {
          const actions = document.querySelector('#profile-form .form-actions').getBoundingClientRect();
          const form = document.querySelector('#profile-form').getBoundingClientRect();
          // Empty face: right of the action row's note, inside the bezel.
          return {x: actions.right - 220, y: actions.top + 4, width: 180, height: actions.height - 8,
                  formRight: form.right};
        }"""
    )
    mean = _png_mean(page, {k: box[k] for k in ("x", "y", "width", "height")})
    surface = page.evaluate(
        "(() => { const d = document.createElement('div'); d.style.color = 'var(--surface)';"
        " document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })()"
    )
    target = _rgb(surface)
    distance = max(abs(mean[i] - target[i]) for i in range(3))
    # The film grain overlay keeps pixels within a few levels of the token.
    assert distance < 8, f"form face {tuple(round(v) for v in mean)} vs --surface {target[:3]}"


@pytest.mark.parametrize("width", [390, 1440])
def test_proof_photo_fills_its_paper_frame(browser, live_server, width):
    ctx = _context(browser, width, reduced_motion="reduce")
    page = ctx.new_page()
    page.goto(live_server, wait_until="domcontentloaded")
    page.evaluate("document.querySelector('.proof-band').scrollIntoView({block: 'center'})")
    page.wait_for_function("document.querySelector('.proof-photo img').complete")
    gap = page.evaluate(
        """() => {
          const frame = document.querySelector('.proof-photo');
          // Layout sizes, not bounding boxes: the frame rests rotated.
          const img = frame.querySelector('img');
          const pad = parseFloat(getComputedStyle(frame).paddingTop);
          return Math.round((frame.clientHeight - 2 * pad) - img.offsetHeight);
        }"""
    )
    assert abs(gap) <= 2, f"photo stops {gap}px short of its frame at {width}px"
    ctx.close()


def test_card_details_follow_the_system(page):
    """Application steps wore the success check (an unstarted step read as
    done); the stale-verification strip had color but no box; buttons with
    a trailing arrow glyph ran it into the label ("Next→")."""
    gap = page.evaluate(
        """() => {
          const btn = document.querySelector('#step-next-btn');
          const arrow = btn.querySelector('span[aria-hidden="true"]').getBoundingClientRect();
          const range = document.createRange();
          range.selectNodeContents(btn.firstChild);
          return arrow.left - range.getBoundingClientRect().right;
        }"""
    )
    assert gap >= 4, f"arrow glyph sits {gap:.1f}px from the label"
    fill_profile_and_submit(page)
    page.click("#tab-programs")
    page.wait_for_selector("#programs-container .program-steps li", timeout=20000)
    marks = page.evaluate(
        """() => {
          const step = getComputedStyle(document.querySelector('.program-steps .reason-list li'), '::after');
          const reason = document.querySelector('#programs-container .reasons:not(.program-steps) .reason-list li');
          return {step: step.maskImage || step.webkitMaskImage,
                  reason: reason ? (getComputedStyle(reason, '::after').maskImage || getComputedStyle(reason, '::after').webkitMaskImage) : null};
        }"""
    )
    assert marks["step"] == "none", f"application step still wears the check mark: {marks['step'][:60]}"
    if marks["reason"] is not None:
        assert marks["reason"] != "none", "match reasons lost their check mark"
    stale = page.evaluate(
        """() => {
          const el = document.querySelector('.verification-source.verification-stale');
          if (!el) return null;
          const s = getComputedStyle(el);
          return [parseFloat(s.paddingLeft), parseFloat(s.borderTopWidth), parseFloat(s.borderTopLeftRadius)];
        }"""
    )
    if stale is not None:
        assert all(v > 0 for v in stale), f"stale strip has no box: padding/border/radius {stale}"


def test_guide_body_panel_has_inner_padding(page, live_server):
    # "load", not DOMContentLoaded: template pages carry no script, so DCL can
    # fire before their stylesheet applies.
    page.goto(f"{live_server}/guides/essays/identity", wait_until="load")
    inset = page.evaluate(
        """() => {
          const panel = document.querySelector('.guide-body').getBoundingClientRect();
          const first = document.querySelector('.guide-body > h2').getBoundingClientRect();
          return [first.left - panel.left, first.top - panel.top];
        }"""
    )
    assert min(inset) >= 16, f"guide content sits on the panel border: {inset}"


# ------------------------------------------------- copy and terminology


def test_unknown_award_is_labeled_never_shown_raw(page):
    """Two scholarships carry a VERIFY award; the card showed the raw token
    in display type where the other unknown stats read "Not listed"."""
    page.click("#nav-browse-btn")
    page.wait_for_selector("#catalog-section:not([hidden]) .match-card", timeout=20000)
    page.click(".catalog-kind-tab[data-kind=scholarships]")
    page.fill("#catalog-search", "Golden Door Scholars")
    page.wait_for_timeout(900)
    card = page.locator("#catalog-container .match-card", has_text="Golden Door")
    card.first.scroll_into_view_if_needed()
    award = card.first.locator(".stat-award")
    assert award.locator(".stat-value").inner_text().strip() == "Not listed"
    assert award.locator(".stat-note").inner_text().strip() == "Confirm on sponsor site"
    assert "VERIFY" not in award.inner_text()


def test_tracker_controls_have_accessible_names(page):
    """The plan's Status select and Notes box had no programmatic label
    (their captions are spans), so assistive tech announced bare controls."""
    _sign_up(page)
    fill_profile_and_submit(page)
    page.locator("#results-container .btn-save").first.click()
    page.wait_for_selector("#results-container button:text-is('Saved')", timeout=15000)
    page.click("#tab-saved")
    page.wait_for_selector("#saved-container .tracker-status", timeout=15000)
    # textContent: cards are content-visibility: auto, so innerText of an
    # offscreen card can be empty.
    name = page.locator("#saved-container .card-title").first.text_content().strip()
    status = page.locator("#saved-container .tracker-status").first
    notes = page.locator("#saved-container .tracker-notes").first
    assert status.get_attribute("aria-label") == f"Status: {name}"
    assert notes.get_attribute("aria-label") == f"Notes: {name}"
    ring = page.locator("#results-container .fit-ring").first.get_attribute("aria-label") or ""
    assert "\u2014" not in ring


# ------------------------------------------------- old-brand leftovers


def _token(page, name):
    return page.evaluate(
        "(n) => { const d = document.createElement('div'); d.style.color = `var(${n})`;"
        " document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; }",
        name,
    )


@pytest.mark.parametrize("width", [390, 1440])
def test_reminder_pages_wear_forest_light(browser, live_server, width):
    """The unsubscribe pages (linked from every digest email) still wore the
    retired Highlighter palette: cream canvas, slate button, system font."""
    ctx = browser.new_context(viewport={"width": width, "height": 844})
    page = ctx.new_page()
    page.goto(f"{live_server}/reminders/unsubscribe?token=preview", wait_until="load")
    assert page.locator("h1").inner_text() == "Turn off reminders?"
    assert page.locator(".site-header .brand-link").count() == 1
    body = page.evaluate("(() => { const s = getComputedStyle(document.body); return [s.backgroundColor, s.fontFamily]; })()")
    assert body[0] == _token(page, "--canvas"), body
    assert body[1].startswith('"Satoshi"') or body[1].startswith("Satoshi"), body
    button = page.locator("button[type=submit]")
    assert button.evaluate("b => getComputedStyle(b).backgroundColor") == _token(page, "--brand")
    assert page.evaluate(SIDEWAYS) <= 0
    ctx.close()


def test_scrims_and_pressed_buttons_use_forest_tints(page):
    """Dialog and consent scrims were slate (23, 24, 28) and pressed buttons a
    warm brown inset, both from the retired palettes."""
    page.click("#open-login")
    page.wait_for_selector("#auth-modal[open]")
    page.wait_for_timeout(400)
    backdrop = page.evaluate("getComputedStyle(document.querySelector('#auth-modal'), '::backdrop').backgroundColor")
    ink = _rgb(_token(page, "--ink"))
    got = _rgb(backdrop)
    assert max(abs(got[i] - ink[i]) for i in range(3)) <= 1 and abs(got[3] - 0.6) < 0.01, backdrop
