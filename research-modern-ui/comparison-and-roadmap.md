# Modern-UI research → EnsureCollege: comparison & roadmap

Date: 2026-07-06. Baseline: `phase3-competitions-vertical` ("Highlighter" restyle).
Full findings: `report.md` (16 items, all fields). Site inventory: `current-site-inventory.md`.

## Already modern (research confirmed, nothing to do)
- Editorial identity, fluid type via `clamp()`, curated photography — matches the 2025-26 editorial trend direction
- Token-based two-theme CSS with `color-scheme` on both themes
- `:has(input:checked)` filter chips, `accent-color` on checks/range
- ARIA tabs/dialogs/labelled sections; global `prefers-reduced-motion` kill switch
- Faceted filtering UI (search, quality/sort selects, chip toggles, min-score range)

## Incorporated now (commit 48879eb)
| Change | Research item | Notes |
|---|---|---|
| ~~Dark mode wired up~~ **REMOVED** (commit ba0de23) | Dark mode & theming | Built and verified, then removed: owner decided the site is light-only. Do not reintroduce. Lesson kept: CSP `script-src 'self'` blocks inline scripts, so any pre-paint bootstrap must be an external file |
| `scroll-padding-top` on html | Navigation | WCAG 2.4.11 fix for the sticky header |
| Skeleton loading cards in #loading | Loading & perceived performance | Shimmer killed automatically by the global reduced-motion rule |
| Modal entry fade+rise via `@starting-style` + `allow-discrete` | Micro-interactions | Entry-only; exit stays instant because `[hidden]` is `display:none !important` |
| `content-visibility: auto` on `.match-card` | Loading & perceived performance | Skips offscreen card rendering in long match lists |
| `field-sizing: content` on resume textarea | Native primitives / Form UX | Progressive; auto-grows where supported |
| `:user-invalid` border styling | Form UX | Complements existing JS validation |

## Deferred follow-ups (bigger jobs, in recommended order)
1. **Native `<dialog>` migration** (native primitives, adopt): replace the hand-rolled `.modal-overlay` divs with `<dialog>` + `showModal()` — free focus trapping, Escape handling, top layer. Touches modal open/close code in app.js.
2. **HTMX pilot** (adopt, incremental): pilot on the matcher search flow with `HX-Request` branching in FastAPI routes; long-term path to shrinking the 133KB app.js. Decide vs. Datastar 1.0.
3. **Multi-step "one thing per page" profile form** (Form UX + GOV.UK patterns, adapt): step indicator, validation summary, `autocomplete` tokens; biggest conversion lever for the matcher intake. Mind WCAG 3.3.7 (no re-asking data).
4. **Preview-first funnel** (conversion, adapt): 3 questions → 3 real matches before the auth wall; server-computed stat band; explicit free/privacy microcopy for a scam-wary audience.
5. **Fuzzy search + date picker** (utility libraries): Fuse.js (or 2KB microfuzz) for typeahead over scholarship names; Cally for deadline pickers. Skip Tabulator/List.js.
6. **Cascade-layer reorganization** of the 66KB stylesheet (@layer reset/tokens/components/utilities) + container-query result cards — do when CSS churn next spikes.
7. **Speculation Rules / cross-document view transitions**: only relevant if the site goes multi-page (it's a single page today).

## Rejected
- Full CSS framework swap (Pico etc.) — the hand-rolled system is coherent and on-brand; use Open Props only as a token reference
- Web Awesome wholesale — selective components only (toast/drawer) if ever needed
- Brutalist/raw-HTML trend, fake-urgency conversion patterns — off-brand and off-mission
