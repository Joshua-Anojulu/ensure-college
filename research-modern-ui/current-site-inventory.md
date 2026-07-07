# Current-site UI inventory (baseline for comparison)

Branch `phase3-competitions-vertical` @ fa9d7a2, 2026-07-06.
Frontend: single-page `app/static/index.html` (29KB) + `css/style.css` (66KB, hand-rolled) + `js/app.js` (133KB vanilla JS). No build step. Brand: "The Highlighter" editorial identity, indigo #4f46e5 + marigold highlighter accent, Plus Jakarta Sans display + Hanken Grotesk body.

## Page structure (index.html)
- `site-header` with `account-nav` (ARIA-labelled)
- Hero (`intro hero`) with reveal-on-scroll
- `proof-band` (campus photo band), `trust-strip`, `difference-panel`
- `resume-import` panel (hidden, gated)
- `opportunity-tabs`: tabpanels for scholarships / programs / catalog / saved (`role="tabpanel"`, aria-labelledby)
- Modals: `role="dialog"` custom overlays (NOT native `<dialog>`)
- `site-footer`

## What already exists (don't re-recommend)
- Token-based theming: theme-independent tokens + light theme + `:root[data-theme="dark"]` overrides; manual theme toggle button (sun/moon)
- ARIA-labelled tabs, dialogs, sections; ~38 aria- attributes in index.html
- Scroll-reveal micro-interactions (JS, `data-reveal-delay`), respects `prefers-reduced-motion` (app.js:220, 3356)
- Chips + badges, fit gauge, stat rows for results
- Curated photography with grain/wash overlays; dark-theme photo filter
- Editorial visual identity (recent restyle, commits 3657608 + 6e0106a)

## Known gaps (verified by grep — zero occurrences in style.css)
- No `prefers-color-scheme` anywhere: dark mode does not follow OS preference, JS toggle only; no `light-dark()`
- No native `<dialog>` or Popover API: modals are hand-rolled div overlays
- No skeleton screens / loading placeholders
- No View Transitions API, no scroll-driven animations (reveals are JS IntersectionObserver-style), no `@starting-style`
- No `content-visibility`, no Speculation Rules
- No container queries / `:has()` / nesting / cascade layers in style.css
- 133KB hand-rolled app.js doing fetch + DOM templating (candidate for HTMX-style comparison)
- Results rendering: card lists; no client-side fuzzy search, no sortable tables, no date-picker components

## Constraints for recommendations
- Must work no-build (script tag / pure CSS only), degrade gracefully (school Chromebooks), keep existing brand tokens, mobile-heavy student audience, Vercel serverless FastAPI backend (static assets currently served through the Python function — payload size matters).
