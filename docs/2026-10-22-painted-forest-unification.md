# Painted forest everywhere (2026-10-22)

## Problem

The 2026-10-17 cohesion pass fixed defects (contrast, phone overflow, labels, raw VERIFY). It did not fix the larger problem Josh describes: the site does not look like one thing. A side-by-side of every surface shows four visual languages:

1. **Painted watercolor forest:** the landing page, the form's sunset band and the plan's trail map.
2. **A 3D low-poly island:** the Journey page, and the landing Teaser once it goes live. It has saturated greens and orange roofs, and nothing in it is painted.
3. **Plain gray app panels:** results, profile form and plan. The `stage-tools` scene shows only behind the results section.
4. **Botanical sprigs:** the `canopy-edge` strip and fern corners framing the template family (opportunity pages, Browse, guides, 404) and the legal pages.

The chrome changes from page to page as well:

| Pages | Header nav |
|---|---|
| App pages | Matches, Plan, Browse, How it works, Log in, Sign up |
| Template family and Journey | How it works, Browse all, Find my matches |
| Legal pages | Back to homepage |
| Unsubscribe pages | Brand only |

The landing has a painted dusk footer, and every other page has a plain one.

## Decision (Josh, 2026-10-22, by question card)

- **Look:** painted forest everywhere. The watercolor landscape language of the Phase 1 plates is the site's one look; everything else is brought into it.
- **3D island:** repaint it to match (palette, soft shading, painted sky, paper grain), keeping the 3D flight. Closer, not true watercolor.
- **No mockups exist.** The reference is the shipped Phase 1 plates (`app/static/img/world/`), the Forest Light tokens in `style.css`, and ADR 0001. Phase 2's wood-and-paper chrome (`phase2-integration`) is not part of this direction.
- **Delivery:** commits go straight to `main`; there are no PRs. CI runs on every push.

## Scope

### A. One chrome on every page
- **Header:** the same brand block and the same nav items, in the same order and style, everywhere: Matches, Plan, Browse, How it works. The right side stays page-appropriate: the SPA keeps its auth controls, and server-rendered pages keep one solid "Find my matches". The two must be styled identically.
- **Footer:** the same footer everywhere, links and painted dusk band included. The dusk band is the landing's `dusk-treeline`, lazy and decorative.

### B. One frame
- Every non-landing surface sits on the same misty forest stage (`stage-tools`): the template family, the legal pages, unsubscribe, 404 and the SPA tool views (form, results, plan).
- Working content rides in legible panels over the stage (ADR 0001).
- The botanical frame (`canopy-edge` strip and fern corners) is retired.
- The landing keeps its own scroll world.

### C. One panel system
- SPA panels (results lane chooser, filters, plan, form) and template cards share one paper surface, border, radius, shadow and eyebrow treatment.
- The gray-on-gray app panels go.

### D. The 3D island, repainted
- `journey.js` and `journey-teaser.js`:
  - materials and lighting move to the plates' palette (sage and deep forest greens, warm paper, muted gold);
  - soft banded shading;
  - fog in the paper colour;
  - a painted sky;
  - `grain.png` paper overlay.
- The Teaser's live island should read as the same picture as its `overlook` painting.

## Constraints (non-negotiable)

- **DOM contract.** Any markup change that `app.js` depends on updates `tests/dom_contract.json` deliberately.
- **Cache-bust in lockstep.** One `?v=` bump across every location.
- **Landing LCP.** The landing inlines `style.css`, so its gzip budget test and the LCP gate stand. World art stays lazy and off the landing's critical path.
- **Fallbacks stay intact:** Save-Data, `prefers-reduced-data`, `prefers-reduced-motion`, forced colors, and the Journey's low-end and reduced-motion paths.
- **Proof.** Every visual change is proven in `tests/e2e/`, and the legibility checks from the cohesion pass (`tests/e2e/test_cohesion.py`) must still pass.
- No em dashes in user-facing copy.

## Not in scope

- Data.
- Matcher behaviour.
- Auth and Digest logic.
- Email templates.
- Phase 2's in-world chrome.

## Process note

Codex review is unavailable in this environment. Josh signed off on the direction through question cards on 2026-10-22 and asked for commits straight to `main`.
