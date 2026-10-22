# The Journey on the home page, and the visual polish pass (2026-10-22)

## Problem

The painted-forest pass (`2026-10-22-painted-forest-unification.md`) unified the chrome, the frame and the panels. Josh still finds the site awkward to look at, and he named the worst offenders himself:

1. **The home page's middle sections are leftovers from the old design.** They are:
   - a campus photograph in a painted world (`.proof-band`);
   - the "Every match explains itself" band (`.difference-panel`);
   - three sticky stacking cards (`.difference-stack`). They are mostly empty, have no art, and clip each other's titles as they slide over one another.
   - the "Fly through the whole plan" teaser (`.journey-teaser`), which sends visitors to a separate page.
2. **The Journey lives on its own page.** Josh wants it to be part of the site, not a detour.
3. **Empty space and unfinished edges show up sitewide.**

## Decision (Josh, 2026-10-22, by question card)

**The 3D flight moves onto the home page.** It becomes the home page's "How it works" section and replaces the four middle sections above. It keeps the 3D. Josh chose this over a painted 2D version, knowing that:
- the 3D model look will sit next to the watercolor paintings;
- capable laptops will download three.js (670 KB raw) on the home page.

The polish items 1 to 7 below were reported to Josh the same day; he asked for everything to "look put together".

## Scope

### J. The Journey on the home page

**Home page order:**
1. hero with the three-match preview;
2. catalog numbers;
3. **How it works** (`#how-it-works`), the flight;
4. the profile form and the tool views;
5. the dusk band;
6. the footer.

**Removed:**
- `.proof-band`, which includes the campus photo;
- `.difference-panel`, which includes the stacking cards;
- `.journey-teaser`, along with `journey-teaser.js`.

**The flight:**
- It is a tall section with a **sticky** stage: sky, canvas, paper, the four stop cards and the rail.
- Progress is the scroll position within the section.
- The stage leaves with the section, so the `--journey-lift` workaround is no longer needed.
- Its top and bottom edges fade into the paper, so the 3D sits in the page like a plate rather than as a hard-edged box.
- The home flight stays in daylight; the dusk belongs to the end of the page.

**Loading:**
- On capable devices, three.js and the scene load lazily as the section approaches. Rendering pauses while the section is off screen.
- The gates are the same as the teaser's: reduced motion, Save-Data, two or fewer cores or 2 GB or less of memory, and no WebGL.
- A device that fails any gate gets a designed static section: the overlook painting and the four stop cards. It never gets an empty tall track.
- The live or static decision is made before the section is laid out, so the page below it never jumps.

**Copy:** the four stops keep the Journey's copy. The removed sections' trust lines (official sources, transparent fit, source-linked steps) already live in stops 2 and 3. Cards use `h3` under a section `h2`; the page `h1` stays the hero's.

**Links and pages:**
- "How it works" in every header, and the hero's secondary button, point to `/#how-it-works`.
- `/journey` answers 301 to `/#how-it-works` and leaves the sitemap. `journey.html` is deleted.
- CONTEXT.md's **Journey** and **Teaser** entries are updated: the Journey is the home page section, and the Teaser is retired.

**Catalog numbers (polish item 2):** the band and its art get soft edges and the full content width. The trail stub that dangles into the gap goes.

### P. Visual polish

1. **Page endings.** Every page currently ends with about 672px of decoration at 1440x900: the dusk band is 300px, and the footer is 372px with a 112px wordmark. On phones it is 429px (160px plus 269px). Shrink the band and the footer so the content dominates. Short pages (404, unsubscribe, the Browse index, the empty plan) should look intentional, not stranded.
2. *(Covered under J.)*
3. **Highlight boxes with long text.** These are the award, cost, dates and deadline boxes on opportunity pages and cards. Long values render as tall columns of large bold text, and short neighbours stretch to match and sit mostly empty. Long values get a calmer text size, and boxes stop stretching to the tallest neighbour.
4. **Plan panels that only say "none".** Hide the "Recommendation letters needed" panel and the "Special eligibility checks" section when they are empty, because the command center already reports both counts. The requirement matrix stops printing the word "None" in every empty cell.
5. **Signed-in header.**
   - On phones it drops the EnsureCollege wordmark. Keep it.
   - "Saved" and "Plan" both open the plan. Show the saved count on Plan and stop showing a second button for the same place.
6. **Emails.** Password reset, deadline reminders and new-match alerts still use the old navy brand (#1b2430). Move them to the site's forest palette, and use one "E" mark style across all three.
7. **Em dashes** in user-facing copy: Privacy (two), Terms (one), and the reminder email's text body (one).

## Constraints (non-negotiable)

- **DOM contract.** `tests/dom_contract.json` is updated deliberately for any selector, emitted class or element change.
- **Cache-bust in lockstep.** One `?v=` bump across every location, done once at integration.
- **Landing LCP.** The hero stays the LCP element. Everything about the flight is below the fold and lazy: no three.js, no plate and no journey CSS on the critical path. The inlined `style.css` must not grow materially.
- **Fallbacks stay intact:** Save-Data, `prefers-reduced-data`, `prefers-reduced-motion`, forced colors, no WebGL, and low-end devices.
- **Proof.** Both suites pass, and every UI fix has an e2e test. The cohesion legibility checks (`tests/e2e/test_cohesion.py`) still pass.
- No em dashes in user-facing copy.
- **Data honesty.** Hiding an empty panel removes no information that is not already shown elsewhere.

## Not in scope

- Matcher behaviour.
- Data.
- Auth and digest logic. The email change is presentation only: colours, the mark and copy punctuation.
- A watercolor shader for the 3D.

## Process note

Codex review is unavailable in this environment. Josh signed off on the direction through a question card on 2026-10-22, and asked for commits straight to `main`.
