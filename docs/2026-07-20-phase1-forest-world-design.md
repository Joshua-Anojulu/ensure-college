# Phase 1 design note: the Forest as a persistent world
_Drafted 2026-07-20, from the Hook'em Hacks reference review.
**Gated on Phase 0 passing the mobile LCP gate.** Design exploration and the
grill happen when Phase 1 opens; this note is the input, not the plan._

## Where this came from

Josh liked https://www.hookemhacks.com/2025.html (and its black "ENTER" teaser
at the root URL) and asked what's worth taking for Phase 1. The site was
reviewed in-browser, not from a text scrape. Reference dials per house-style:
ours stay **variance 9 / motion 8 / density 4**.

## The core idea worth adopting

**The illustrated world persists past the hero.** On the reference, the
underwater environment (water gradient, caustic light, bubbles) runs the full
page height; content sections float *inside* the world rather than below a hero
image. Forest-Journey today is an illustrated hero stage followed by
conventional sections — the biggest available upgrade is carrying the forest
down the page.

### Adopt (in priority order)

1. **Persistent environment.** The forest continues behind every landing
   section: canopy light from above, undergrowth/ferns bleeding into section
   edges, depth fading with scroll. Sections keep their `panel` legibility
   treatment (the paper wash already exists for exactly this).
2. **Diegetic UI.** The reference sets its hero copy inside an in-world ornate
   frame lashed to an anchor. Forest equivalents: a carved trail-marker or
   wooden sign for the hero panel, rope-and-plank edges for section frames.
   One or two moments, not every container — the craft move, not a skin.
3. **Gutter marginalia.** Scuba-mascots swim in the side gutters at wide
   viewports; a submarine persists as a scroll companion. Our gutters at
   >1200px are dead space. Forest equivalents: fireflies, a fox/owl that
   appears at section boundaries, drifting leaves. Subtle, paused by
   `prefers-reduced-motion`, never overlapping content.
4. **Total icon consistency.** Every reference track icon is a drawn sea
   creature — no stock set anywhere. We already have the icon-lock rule; Phase 1
   should draw its section/feature glyphs in the Forest style rather than mix
   Phosphor into the illustrated surfaces.

### Reject (and why)

- **The entry curtain** (black ENTER/SOUND-ON interstitial). This is precisely
  the blocking-overlay-before-content pattern Phase 0 just removed — the age
  gate was the LCP element at 3540 ms. Recreating it deliberately is a
  regression, and ambient sound on a tool students revisit weekly is friction
  by the third visit.
- **Symmetric card rows and the 6-tile stat grid.** Banned pattern (three equal
  cards), variance ~2 against our 9.
- **Text wordmark trust walls** ("Apple Google Meta" as styled text). House
  rule: real SVG logos or nothing.
- **Event scaffolding** (countdown, sponsor carousels, MLH badge equivalents) —
  no meaning for a planning tool.

## The genre boundary (binding for every Phase 1 decision)

A hackathon site is visited **once**, to hype a registration. EnsureCollege is
visited **repeatedly**, by stressed students managing deadlines.
[ADR 0001](../docs/adr/0001-immersive-illustration-on-a-utility.md) already
names this tension. Rule of thumb: the world may **decorate** the journey; it
must never **gate** an action. Anything a returning user must click through,
wait for, or scroll past to reach their matches is out.

## Perf budget (the Phase 0 lesson, made structural)

Phase 0 proved a single modal cost 2144 ms of LCP and one deferred script cost
0.906 CLS — and that we can attribute both precisely. So Phase 1 features get
**priced at design time**:

- Every proposed world element states its cost class up front:
  CSS-only / one image / script-driven.
- The Phase 0 attribution harness (puppeteer, gate-matched throttling) runs on
  a preview per feature branch; the pinned Lighthouse protocol stays the
  authoritative gate. Budget: **median LCP < 2500 ms with the Phase 0 headroom
  preserved (target ≤ 1800 ms), CLS < 0.1**.
- Motion follows the Phase 0 CLS rule: **never hide or move what has already
  painted**; reveal-on-scroll applies only to below-fold targets, world
  elements animate transform/opacity only, off the layout path.
- Assets follow the Phase 0 image discipline: WebP via the committed Pillow
  generator, measured `sizes`/`srcset`, no raw JPGs on the landing.

## Open questions for the grill (when Phase 1 starts)

- Which sections leave the utility register and join the world (landing-only,
  or Journey page too)?
- Fixed scroll companion vs. section-boundary appearances for the marginalia?
- Does the forest environment extend to authenticated/dashboard views at all,
  or is the world strictly the marketing surface? (ADR 0001 leans marketing.)
- Budget arithmetic: the persistent environment likely costs one more
  hero-class WebP layer — what does the harness say it does to LCP?
