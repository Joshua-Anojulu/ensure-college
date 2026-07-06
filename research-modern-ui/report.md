# Research Report: Modern website UI patterns and non-AI website components (with concrete code sources) applicable to a FastAPI + vanilla-JS college-helper site (EnsureCollege)

Items: 16  |  Generated from `results/` (uncertain values skipped)

## Table of Contents

1. [2025-2026 web design trends (editorial layouts, bento gri...](#2025-2026-web-design-trends-editorial-layouts-bento-gri) - Verdict: **adopt** | Effort: low
2. [Accessible component patterns (W3C ARIA Authoring Practic...](#accessible-component-patterns-w3c-aria-authoring-practic) - Verdict: **adopt** | Effort: low
3. [Classless and no-build CSS frameworks: Pico CSS, Open Pro...](#classless-and-no-build-css-frameworks-pico-css-open-pro) - Verdict: **adapt** | Effort: modern-normalize: lo...
4. [Dark mode and theming architecture: CSS custom properties...](#dark-mode-and-theming-architecture-css-custom-properties) - Verdict: **adopt** | Effort: medium
5. [Faceted filtering and search-results UI (filter chips, re...](#faceted-filtering-and-search-results-ui-filter-chips-re) - Verdict: **adopt** | Effort: medium
6. [Form UX patterns (multi-step forms, inline validation, sm...](#form-ux-patterns-multi-step-forms-inline-validation-sm) - Verdict: **adopt** | Effort: low
7. [Government design systems as form-pattern code sources (G...](#government-design-systems-as-form-pattern-code-sources-g) - Verdict: **adapt** | Effort: low
8. [HTMX and progressive enhancement for FastAPI](#htmx-and-progressive-enhancement-for-fastapi) - Verdict: **adopt** | Effort: low
9. [Landing and hero conversion patterns](#landing-and-hero-conversion-patterns) - Verdict: **adapt** | Effort: low
10. [Loading and perceived-performance patterns](#loading-and-perceived-performance-patterns) - Verdict: **adopt** | Effort: low
11. [Micro-interactions and modern CSS animation](#micro-interactions-and-modern-css-animation) - Verdict: **adopt** | Effort: low
12. [Modern CSS architecture primitives: container queries, :h...](#modern-css-architecture-primitives-container-queries-h) - Verdict: **adopt** | Effort: low
13. [Native HTML interactive primitives](#native-html-interactive-primitives) - Verdict: **adopt** | Effort: low
14. [Navigation patterns (sticky headers, framework-free mobil...](#navigation-patterns-sticky-headers-framework-free-mobil) - Verdict: **adopt** | Effort: low
15. [Vanilla-JS component libraries (Web Awesome / Shoelace an...](#vanilla-js-component-libraries-web-awesome-shoelace-an) - Verdict: **adapt** | Effort: low
16. [Vanilla utility libraries for data-heavy pages (fuzzy sea...](#vanilla-utility-libraries-for-data-heavy-pages-fuzzy-sea) - Verdict: **adapt** | Effort: low

---

## 2025-2026 web design trends (editorial layouts, bento gri...

### Basic Info

**category**: design-trend

**description**: 

> The dominant visual direction of 2025-2026 web design: (1) Editorial layouts — magazine-style asymmetric grids, generous whitespace, strong typographic hierarchy that treats the page like a publication rather than an app shell. (2) Bento grids — modular card mosaics popularized by Apple keynote pages; in 2026 evolving into 'active grids' where tiles expand, play media, or reveal secondary data on hover/tap. (3) Fluid typography — clamp()-based type scales (the Utopia methodology) that interpolate smoothly between viewport sizes instead of jumping at breakpoints. (4) Oversized/kinetic type and type-as-interface — headlines become the primary interface architecture, partly an aesthetic choice and partly an engineering mandate to reduce page weight (text instead of hero images/video). (5) Scrollytelling — scroll position advances a narrative or animates content; matured from data journalism into product/marketing sites, now implementable with native CSS scroll-driven animations. (6) The brutalist/raw-HTML counter-trend — deliberately raw layouts, visible grid structure, system/monospace fonts, harsh color clashes as a reaction to the ubiquity of polished bento/glass aesthetics; signals authenticity. The problem these solve: differentiating a site from templated SaaS sameness while keeping payloads light.

**adoption_maturity**: 

> Mainstream and stable as a visual language. Bento grids are used by Apple, Vercel, Linear, and countless SaaS marketing pages since 2023 and are now considered a mid-2020s default. Editorial layouts and oversized type dominate Awwwards/site-of-the-day winners across 2024-2026. Fluid typography via clamp() is standard professional practice (Utopia by Trys Mudford and James Gilyead is the canonical methodology). Scrollytelling is established in journalism (NYT, The Pudding) and has moved downstream to product sites. Brutalism remains a deliberate niche/counter-trend rather than a mainstream default. All are techniques, not libraries, so there is no community-health risk.

### Code

**code_sources**: 

> Fluid type: https://utopia.fyi (free calculators emitting copy-paste clamp() CSS custom properties: /type/calculator and /space/calculator); clamp generator https://clampgen.com and https://moderncsstools.com/clamp-calculator/. Bento grid: pure CSS Grid — core pattern is `display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); grid-auto-flow:dense;` with featured tiles spanning via `grid-column:span 2; grid-row:span 2;` — many CodePen examples (search 'bento grid css'); CSS-Tricks grid guide https://css-tricks.com/snippets/css/complete-guide-grid/. Scrollytelling: native CSS scroll-driven animations (`animation-timeline: view()`/`scroll()`) documented with copy-paste demos at https://scroll-driven-animations.style (Bramus, Chrome team) and MDN https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_scroll-driven_animations; JS fallback/general solution: IntersectionObserver (vanilla, no library) or Scrollama https://github.com/russellsamora/scrollama (MIT). Kinetic type: CSS-only examples on CodePen; Splitting.js https://github.com/shshaw/Splitting (MIT) for per-character effects. Brutalist starting points: https://brutalistwebsites.com (gallery), plain semantic HTML plus system font stack.

**license**: 

> n/a for the techniques themselves (pure CSS/HTML). Optional helpers: Scrollama (MIT), Splitting.js (MIT), Utopia calculator output is free to use.

**dependency_footprint**: 

> None for the core trends — bento grids, editorial layout, fluid type, oversized type, and brutalism are pure CSS/HTML. Scrollytelling: pure CSS with scroll-driven animations in supporting browsers, or a few lines of vanilla IntersectionObserver; Scrollama is an optional single script tag. Fully compatible with a no-build vanilla-JS site.

**bundle_size_kb**: 

> 0 for pure CSS techniques; Scrollama ~5 KB gzipped and Splitting.js ~2 KB gzipped if used; IntersectionObserver approach is ~0.5 KB of hand-written JS. Main-thread cost of scroll-driven CSS animations is near zero (compositor-driven).

**ssr_htmx_compat**: 

> Excellent. All techniques are declarative CSS applied to server-rendered HTML, so they survive full server rendering and HTMX/fetch partial swaps with no re-hydration. Only caveat: IntersectionObserver-based scrollytelling must re-observe elements after a partial swap (re-run the observer setup in the swap callback, e.g. htmx:afterSwap); CSS scroll-driven animations need no re-binding at all.

**maintenance_health**: 

> n/a for pure techniques. Scrollama: maintained, stable, last release within recent years; Utopia calculators actively maintained by Clearleft folks (OddBird published follow-on fluid-type work in 2025).

**integration_effort**: 

> low to medium. Fluid type and bento grid: low — drop Utopia-generated custom properties into the existing 66KB stylesheet and refactor headings/cards incrementally. Scrollytelling: medium — needs content design, not just code. Full editorial redesign: medium.

### Design

**key_techniques**: 

> Fluid type scale: `:root { --step-0: clamp(1rem, 0.91rem + 0.43vw, 1.25rem); --step-3: clamp(1.73rem, 1.4rem + 1.62vw, 2.67rem); } h1 { font-size: var(--step-3); }` — always use rem (never px) inside clamp so user font-size preferences and zoom keep working, and keep max <= 2.5x min to pass WCAG 1.4.4. Bento grid: `.bento { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:1rem; grid-auto-flow:dense; } .bento .featured { grid-column:span 2; grid-row:span 2; }`. Scrollytelling (native): `@keyframes reveal { from { opacity:0; translate:0 2rem; } } .card { animation: reveal linear both; animation-timeline: view(); animation-range: entry 0% entry 60%; }` wrapped in `@supports (animation-timeline: view())`. Scrollytelling (fallback JS): `new IntersectionObserver(es => es.forEach(e => e.target.classList.toggle('in-view', e.isIntersecting)), {threshold:.25})`. Oversized type: viewport-relative sizes with safety clamp, e.g. `font-size: clamp(2.5rem, 8vw, 7rem); line-height:.95; letter-spacing:-0.02em; text-wrap: balance;`. Editorial layout: named-line CSS Grid with a wide content column plus breakout columns; `text-wrap: pretty` for body copy. Brutalist accents: system-ui/monospace stacks, visible 1px borders, unpolished hover states.

**visual_examples**: 

> Bento: apple.com product pages (e.g. iPhone/Mac spec sections), vercel.com, linear.app, https://bentogrids.com gallery. Editorial/oversized type: awwwards.com winners, https://www.figma.com/resource-library/web-design-trends/, stripe.com/sessions pages. Scrollytelling: The Pudding (pudding.cool), NYT interactive features, https://scroll-driven-animations.style demo gallery. Brutalism: https://brutalistwebsites.com, craigslist/Berkshire Hathaway as the ur-examples, many personal dev portfolios 2024-2026.

**accessibility_notes**: 

> Fluid type: use rem-based clamp so browser zoom and user font-size settings still scale text; test at 200% zoom. Oversized type must maintain contrast and not truncate at 320px width (WCAG 1.4.10 Reflow). Scrollytelling: gate all motion behind `@media (prefers-reduced-motion: no-preference)` — vestibular-disorder users must get static content; ensure the narrative is readable with animations disabled and content is in DOM order for screen readers. Bento grids: keep DOM order matching visual reading order (grid-auto-flow:dense can visually reorder — verify tab order still makes sense). Brutalism risks poor contrast and unclear affordances if taken literally; keep focus indicators visible.

**wcag_mapping**: 

> Satisfies when done right / risks when not: 1.4.4 Resize Text (rem-based clamp with max<=2.5x min passes; px-based clamp fails), 1.4.10 Reflow (fluid layouts pass at 320px; oversized type can overflow), 1.4.12 Text Spacing (editorial type must tolerate user spacing overrides), 2.3.3 Animation from Interactions (scrollytelling must honor prefers-reduced-motion), 1.3.2 Meaningful Sequence (bento dense packing can break reading order), 2.4.7/2.4.11 Focus Visible / Focus Not Obscured (brutalist minimal styling must keep focus rings; sticky editorial headers must not obscure focused elements).

**progressive_enhancement_fallback**: 

> All trends degrade gracefully: fluid type falls back to the clamp minimum (or a static rem size if clamp unsupported — effectively no real-world browsers anymore); bento grid tiles stack into a single column on narrow screens or without grid support; scroll-driven animations wrapped in @supports simply render content statically (fully readable, plain scroll); IntersectionObserver absence (or JS off) leaves content visible if you author 'visible by default, animate in when JS adds a class' rather than hiding content by default. Brutalism IS the fallback aesthetic.

**mobile_touch_behavior**: 

> Fluid type is specifically designed for the mobile-first continuum — no breakpoint jumps between phone sizes. Bento tiles must collapse to 1-2 columns on phones with touch targets >=44px; hover-reveal 'active grid' interactions need a tap equivalent (or show the content by default on touch — use @media (hover:none)). Oversized headlines: test 320px width for overflow and iOS Safari text-size-adjust. Scrollytelling on mobile: keep sticky graphics from consuming the whole viewport, avoid scroll-jacking (breaks momentum scrolling and frustrates thumb navigation), and account for the dynamic URL-bar viewport (use svh/dvh units, not vh). Student audience is mobile-heavy, so these details are load-bearing.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege already has an editorial 'Highlighter' brand identity with an indigo palette — the 2025-2026 editorial/type-forward direction is exactly aligned with it, meaning the site can look current without a rebrand. Concretely: (1) scholarship/program/competition matcher results are card lists today — a bento treatment with one 'featured match' tile spanning 2x2 gives visual hierarchy to the best matches and makes result pages feel curated rather than database-dumped; (2) a Utopia fluid type scale replaces ad-hoc font sizes in the 66KB hand-rolled CSS with ~10 custom properties, improving consistency and mobile rendering for a student audience browsing on phones; (3) oversized type-as-interface suits the landing/marketing pages (big highlighter-underlined headlines are on-brand and cost 0 KB versus hero imagery); (4) light scrollytelling (staggered card reveal on the results feed) adds perceived polish for near-zero JS. The brutalist counter-trend is a useful discipline check — the site's hand-rolled, no-framework approach is already 'honest HTML'; keep that virtue while adding editorial polish.

**current_gap**: 

> The site has a solid brand but no fluid type scale (font sizes are static and likely breakpoint-jumped within 66KB hand-rolled CSS), no bento/featured-tile hierarchy on matcher results, no scroll-linked reveal or view transitions, and no motion system at all (also no prefers-reduced-motion handling to audit yet). The editorial brand exists in palette/logo but is under-expressed in layout and typography.

**recommended_action**: 

> adopt (fluid type, editorial type hierarchy, bento result cards) / adapt (scrollytelling as light reveal-on-scroll only) / skip (full brutalism, scroll-jacking narratives). Concrete plan: generate a Utopia type + space scale (min 320px/16px, max 1240px/18px, ~1.2-1.25 ratio), paste the custom properties into the root of the existing stylesheet, and migrate headings/body/card text to var(--step-N) incrementally — an afternoon of work, zero bytes of JS. Then restyle matcher result grids as a bento: auto-fill minmax(240px,1fr) with the top-scoring match spanning 2 columns, indigo highlighter accent on the featured tile. Finally add a 10-line IntersectionObserver (or @supports-gated scroll-driven animation) that fades result cards up on entry, wrapped in prefers-reduced-motion: no-preference, with cards visible by default so JS-off and HTMX swaps stay safe.

### Uncertain Fields (skipped)

- baseline_status


---

## Accessible component patterns (W3C ARIA Authoring Practic...

### Basic Info

**category**: a11y-pattern

**description**: 

> The W3C ARIA Authoring Practices Guide (APG) is the canonical catalog of how to build custom interactive widgets accessibly: it specifies the roles, states, properties, and exact keyboard interaction for ~30 patterns including Tabs (role=tablist/tab/tabpanel, arrow-key navigation), Dialog-Modal (focus trap, aria-modal, Escape), Combobox (aria-expanded/aria-activedescendant listbox popups for autocomplete), Disclosure (aria-expanded show/hide, the basis of accordions and menus), plus Accordion, Listbox, Menu, Switch, Alert, and more. It solves the problem that div/span-based custom widgets are invisible or broken for screen-reader and keyboard users, and it is the reference that WCAG audits and ADA lawsuits measure custom widgets against. Critically, as of 2025-2026 several APG patterns now have native zero-JS HTML equivalents that should be preferred: the APG's own 'First Rule of ARIA' - use a native element instead of ARIA when one exists.

**adoption_maturity**: 

> The de facto industry standard since the early 2010s, actively maintained by the W3C ARIA Working Group (task force includes browser and AT vendors); redesigned site launched 2022 at w3.org/WAI/ARIA/apg with ongoing pattern updates through 2024-2026. Every major design system (GitHub Primer, Adobe Spectrum/React Aria, Radix, Shoelace/Web Awesome, GOV.UK) implements or cites APG patterns. Legal anchor: WCAG 2.2 AA (Oct 2023) is the current audit target, and the DOJ's ADA Title II rule (Apr 2024) makes WCAG 2.1 AA legally mandatory for US state/local government web content - deadlines extended in April 2026 to Apr 26, 2027 (entities >=50k population) and Apr 26, 2028 (<50k). Private-sector Title III suits routinely cite WCAG conformance, so APG-correct widgets are the practical liability shield.

### Code

**code_sources**: 

> APG patterns index with full HTML/JS reference implementations: https://www.w3.org/WAI/ARIA/apg/patterns/ ; Tabs (automatic activation example): https://www.w3.org/WAI/ARIA/apg/patterns/tabs/examples/tabs-automatic/ ; Modal dialog example: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/examples/dialog/ ; Combobox with listbox popup: https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-list/ ; Disclosure: https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/ ; Accordion: https://www.w3.org/WAI/ARIA/apg/patterns/accordion/ ; source repo: https://github.com/w3c/aria-practices . All examples are copy-paste-able vanilla JS/HTML/CSS with no dependencies.

**license**: 

> W3C Software and Document License (permissive, allows reuse of example code); the guidance itself is a freely available W3C resource

**dependency_footprint**: 

> None - pure vanilla HTML + ARIA attributes + small hand-written JS (each APG example is typically 1-5 KB of JS). No npm, no build step, no framework. Perfectly compatible with a no-build vanilla-JS site; the cost is authoring and maintaining the JS yourself, which is exactly why native equivalents are now preferred where they exist.

**bundle_size_kb**: 0-5 per pattern (hand-written vanilla JS; tabs ~2KB, modal ~3KB, combobox ~4-5KB unminified)

**ssr_htmx_compat**: 

> The HTML/ARIA markup is fully server-renderable. The weakness is the JS layer: APG-style widgets bind event listeners imperatively on load, so HTMX/fetch partial swaps require re-initializing widgets after every swap (e.g. htmx:afterSwap hook or event delegation on document). This re-binding burden is a standing source of bugs in hand-rolled implementations - another argument for native elements (<details>, <dialog>, popover) which need no binding, or web components which auto-upgrade.

**maintenance_health**: 

> n/a for the technique itself; the APG is actively maintained by the W3C ARIA Working Group (regular updates through 2026). Your own implementation code is self-maintained - that maintenance cost is the pattern's main liability.

**integration_effort**: 

> low-medium - the site already has ARIA-labelled modals/tabs; auditing them against APG keyboard specs is low effort, replacing them with native equivalents is medium

### Design

**key_techniques**: 

> Tabs: role=tablist/tab/tabpanel, aria-selected, roving tabindex (only active tab in tab order), Left/Right arrow keys move focus, Home/End, aria-controls linking tab to panel. Dialog: role=dialog aria-modal=true, focus moved in on open and restored on close, Tab cycles inside (focus trap), Escape closes - all now free via native <dialog>.showModal(). Combobox: input[role=combobox] with aria-expanded, aria-autocomplete=list, aria-controls pointing to role=listbox, aria-activedescendant tracking the highlighted option, Down Arrow opens, Enter selects, Escape closes. Disclosure: <button aria-expanded=false aria-controls=panel> toggling hidden - or natively <details>/<summary>. Accordion: series of disclosures with heading-wrapped buttons - natively <details name="group">. Also: aria-live regions for async result updates (polite announcements when matcher results change), and the First Rule of ARIA: prefer native HTML semantics over ARIA retrofits.

**visual_examples**: 

> The APG example pages themselves (w3.org/WAI/ARIA/apg/patterns/ - every pattern has a live demo); GOV.UK Design System components (design-system.service.gov.uk) as production-grade APG-aligned implementations; Sara Soueidan's and Adrian Roselli's pattern write-ups; Deque's ARIA examples at dequeuniversity.com/library

**accessibility_notes**: 

> APG is the a11y spec itself, but key pitfalls: (1) ARIA is a promise - adding role=tab without implementing arrow-key behavior makes things worse than plain links ('no ARIA is better than bad ARIA'); (2) aria-activedescendant vs roving tabindex tradeoffs in comboboxes (VoiceOver quirks); (3) focus trap implementations commonly break with dynamically added content; (4) screen-reader testing (NVDA + VoiceOver minimum) is still required because ARIA support varies by AT/browser pairing. Native-equivalents note (2025-2026): Dialog pattern -> native <dialog> (full equivalence, browser-managed); Disclosure/Accordion -> <details>/<summary> and <details name> exclusive accordions (zero JS); non-modal popup patterns (menus, tooltips-ish, pickers) -> Popover API + invoker commands; Combobox/Select-only -> customizable <select> covers the select-only combobox case in Chromium (full styled combobox with filtering still needs APG JS everywhere); Tabs -> still NO native equivalent (CSS Carousel/::tab-marker experiments in Chrome are not standard) - tabs remain the pattern where APG JS is genuinely required.

**wcag_mapping**: 

> APG patterns exist to satisfy: 4.1.2 Name Role Value (roles/states on custom widgets), 2.1.1 Keyboard and 2.1.2 No Keyboard Trap (specified keyboard models), 2.4.3 Focus Order (dialog focus management), 1.3.1 Info and Relationships (tab/panel, button/panel associations), 3.2.1 On Focus / 3.2.2 On Input (predictable widget behavior), 4.1.3 Status Messages (aria-live for async updates). New in WCAG 2.2 AA and relevant to these widgets: 2.4.11 Focus Not Obscured Minimum (dialogs/sticky headers must not hide focused elements), 2.5.7 Dragging Movements, 2.5.8 Target Size Minimum (24px minimum for tab/accordion hit areas), 3.2.6 Consistent Help, 3.3.7 Redundant Entry (relevant to multi-step scholarship forms - do not make students re-enter profile data), 3.3.8 Accessible Authentication (no cognitive-test CAPTCHAs on login).

**baseline_status**: 

> ARIA 1.2 attributes used by APG are Baseline Widely available across all browsers (the guidance is not itself a Baseline feature). The native replacements' Baseline: <dialog> Widely available; <details>/<summary> Widely available; details name= Newly available Sept 2024; Popover API Newly available Jan 2025; invoker commands Newly available Dec 2025; customizable <select> Limited (Chromium only, mid-2026).

**progressive_enhancement_fallback**: 

> Hand-rolled APG widgets typically fail hard without JS (tabs that show nothing, dialogs that never open) unless deliberately built as enhancement over working HTML (e.g. tabs enhancing an in-page-anchor list, disclosure enhancing visible content). Native equivalents invert this: <details> works with JS off, <dialog> content can fall back to a page, forms fall back to full-page POST to FastAPI. Recommended architecture: server-rendered content first, APG JS only as a layer, native elements wherever they exist.

**mobile_touch_behavior**: 

> APG keyboard specs do not cover touch well - that is on the implementer. Mobile specifics for a student audience: ensure 24px+ (ideally 44px) touch targets on tabs and accordion headers (WCAG 2.5.8); modal dialogs need dvh-based max heights and internal scrolling so the iOS keyboard does not hide inputs; combobox listboxes must reposition above the input when the virtual keyboard opens; horizontal tab lists need overflow-x scrolling with visible affordance on narrow screens; screen-reader touch exploration (VoiceOver/TalkBack swipe navigation) depends on correct roles, which APG markup provides.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege already ships ARIA-labelled modals and tabs in hand-rolled JS - APG is the yardstick to verify they actually implement the keyboard contracts (arrow keys on tabs, focus trap + restore on modals, Escape everywhere), which is where hand-rolled widgets usually fail audits. The matcher pages need APG-correct patterns most: filter comboboxes/autocompletes (school name, major), aria-live announcements when scholarship results update after filtering, and disclosure-based FAQ/eligibility sections. As a college-focused product, many users are students with disabilities and partner institutions (schools, districts) are public entities subject to the DOJ Title II rule (WCAG 2.1 AA by Apr 2027/2028) - procurement will increasingly demand a VPAT/WCAG conformance, so APG-correct components are a sales asset, not just ethics. Native equivalents let the site delete rather than fix much of this JS.

**current_gap**: 

> The site has ARIA labels on modals/tabs but (per description) no verified APG keyboard behavior audit, no aria-live status announcements for async matcher-result updates, hand-rolled focus management of unknown correctness inside 133KB of JS, and none of the native replacements adopted. There is no documented WCAG 2.2 AA conformance check against the new criteria (2.4.11, 2.5.8, 3.3.7, 3.3.8) that matter for its multi-step forms and auth.

**recommended_action**: 

> adopt (as audit standard) + adapt (replace with native where possible) - Step 1: audit existing tabs and modals against the APG keyboard tables (30 minutes per widget: arrow keys, Home/End, focus trap, Escape, focus restore) and fix gaps. Step 2: replace the modal JS with native <dialog> and the accordion-like sections with <details name>, deleting APG JS rather than maintaining it; keep APG JS only for tabs (no native equivalent) and any filtering combobox. Step 3: add role=status aria-live=polite region to matcher results ('42 scholarships match') and check the WCAG 2.2-specific criteria: 24px targets on tab/accordion controls, focus not obscured under the sticky header, no redundant entry across the multi-step scholarship profile, email-link or password-manager-friendly auth. Document results as a lightweight conformance note for school-district procurement.


---

## Classless and no-build CSS frameworks: Pico CSS, Open Pro...

### Basic Info

**category**: css-framework

**description**: 

> Drop-in CSS foundations that require no build step, no utility classes, and no framework — the natural complements to a hand-rolled stylesheet. (1) Pico CSS: a minimal (~80KB raw, single-digit-KB gzipped) framework that styles semantic HTML directly — headings, forms, tables, buttons, dialogs, accordions (details/summary) look polished with zero or near-zero classes; described as 'a reset CSS on steroids'. Ships a fully classless variant (pico.classless.css) and a conditional version scoped to a .pico container for retrofitting into existing sites. Includes built-in light/dark mode and 20 color themes, all driven by CSS custom properties. (2) Open Props: not a framework but a design-token layer — hundreds of ready-made CSS custom properties (color scales, fluid type sizes, shadows, easings, animations, gradients) that you reference from your own CSS; 'sub-atomic styles'. Normalize file (props + optional normalize) is a few KB over the wire. (3) modern-normalize: sindresorhus's ~1KB successor to normalize.css targeting only modern evergreen browsers (Chrome/Edge/Firefox/Safari); the standard tiny baseline reset (it is what Tailwind's preflight builds on). The problem they solve: consistent, attractive defaults and a token vocabulary without adopting Tailwind/Bootstrap-scale machinery or a build pipeline.

### Code

**code_sources**: 

> Pico CSS: https://github.com/picocss/pico, docs https://picocss.com/docs, classless docs https://picocss.com/docs/classless; CDN: https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css (also pico.classless.min.css and pico.conditional.min.css, plus per-color builds like pico.indigo.min.css). Open Props: https://github.com/argyleink/open-props, site with copy-paste snippets https://open-props.style; CDN: https://unpkg.com/open-props (or import individual files like open-props/postcss/... for build users; CDN users take the whole bundle); Open Props UI: https://open-props-ui.netlify.app. modern-normalize: https://github.com/sindresorhus/modern-normalize (modern-normalize.css is a single short file — copy it into the repo); CDN: https://cdn.jsdelivr.net/npm/modern-normalize/modern-normalize.min.css. All three are pure .css files usable via one link tag or vendored directly.

**license**: Pico CSS: MIT. Open Props: MIT. modern-normalize: MIT.

**dependency_footprint**: 

> One link tag each (or vendor the file into static assets — preferable for privacy/reliability). No JS, no npm requirement, no build step, no framework. All three are fully compatible with a no-build FastAPI + vanilla-JS site. Open Props optionally offers per-file/PostCSS subsetting for build users, but the CDN bundle works standalone.

**ssr_htmx_compat**: 

> Perfect for all three — pure stylesheets that style whatever HTML the server or an HTMX swap delivers. No re-upgrade, no event re-binding, no hydration concerns. Pico's styled details/summary accordions and dialog elements are native HTML, so they keep working after partial swaps (dialog still needs your own small JS to call showModal, which must be event-delegated to survive swaps).

**integration_effort**: 

> modern-normalize: low (one file, before your CSS; diff against your existing reset first). Open Props: low (add link tag, start referencing var(--size-3), var(--indigo-6), var(--shadow-2) etc. from existing CSS; adopt incrementally). Pico full/classless: medium-to-high on an existing 66KB-CSS site — it styles bare elements aggressively and will fight existing rules; Pico conditional (.pico class scoping) or cherry-picking its form/table styles is the low-effort path. On a greenfield internal page (admin, docs), Pico classless is trivially low.

### Design

**key_techniques**: 

> Layered import so brand CSS always wins: `@layer vendor, tokens, base, components; @import url('modern-normalize.min.css') layer(vendor); @import url('open-props.min.css') layer(tokens);`. Open Props usage: `.card { padding: var(--size-4); border-radius: var(--radius-3); box-shadow: var(--shadow-2); transition: box-shadow .2s var(--ease-out-3); } h1 { font-size: var(--font-size-fluid-2); }` — the fluid type props (--font-size-fluid-0..3) are prebuilt clamp() scales. Pico theming via custom properties: `:root { --pico-primary: #4f46e5; --pico-border-radius: .5rem; --pico-font-family: 'YourBrandFont', system-ui; }` and dark mode via `<html data-theme="dark">` or its automatic prefers-color-scheme handling; conditional build: wrap a page region in `<div class="pico">` so only that region is styled. Pico classless gives styled forms free: `<form><label>Email <input type=email required></label><button>Submit</button></form>` renders polished with validation styling. modern-normalize: just include first; notable rules include box-sizing:border-box everywhere and system-ui font default.

**visual_examples**: 

> Pico: https://picocss.com (the site is built with it) and docs examples page https://picocss.com/examples; the HTMX community commonly pairs HTMX + Pico for demos. Open Props: https://open-props.style homepage showcases every token interactively; Open Props UI gallery https://open-props-ui.netlify.app shows full components; LogRocket 'Designing a modern UI theme with Open Props' tutorial. modern-normalize has no visual identity by design.

**accessibility_notes**: 

> Pico: built on semantic HTML so baseline a11y is strong (real buttons, labels, fieldsets); its color themes generally meet contrast but verify your chosen primary against WCAG 1.4.3 (indigo on white is fine at 600+ weight/size, check small text); its focus styles are visible by default — do not remove. Its styled details/summary accordions are keyboard-accessible natively. Open Props: token values are a11y-neutral, but its color scales make it easy to pick contrast-safe pairs (e.g. --indigo-7 text on --indigo-0 background — still verify each pair); --animation props should be gated behind prefers-reduced-motion. modern-normalize: preserves accessible browser defaults; no risks. General pitfall: classless frameworks style what you write — sloppy markup (divs as buttons) stays inaccessible; the framework rewards, not replaces, semantic HTML.

**wcag_mapping**: 

> Directly relevant: 1.4.3 Contrast Minimum (Pico themes and Open Props color scales must be pair-checked), 2.4.7 Focus Visible (Pico ships compliant focus rings; keep them), 1.4.4 Resize Text (all three use rem-based sizing; Open Props fluid font tokens are rem-based clamp — compliant), 1.4.10 Reflow (Pico's fluid containers reflow at 320px), 3.2.4 Consistent Identification (a token system like Open Props enforces visual consistency across components). No criteria are violated by the frameworks themselves.

**progressive_enhancement_fallback**: 

> Pure CSS: with styles unloaded or unsupported, users get the browser-default rendering of semantic HTML — fully functional forms, links, and content (this is the classless philosophy's core virtue). Open Props custom properties: an unsupporting browser (none in practice) would fall back to your `var(--x, fallback)` defaults or inherited values. No JS involved anywhere, so 'JS off' changes nothing.

**mobile_touch_behavior**: 

> Pico is mobile-first: fluid typography scale, responsive spacing, full-width touch-friendly form controls (inputs/buttons render at comfortable tap sizes >44px by default), and a responsive container system; its dropdowns/accordions are native elements with correct touch behavior and virtual-keyboard interplay (native inputs scroll into view above the keyboard). Open Props includes fluid type/space tokens designed for small screens. modern-normalize sets text-size-adjust so iOS Safari doesn't inflate text unpredictably. None introduce sticky-header or scroll-hijack behaviors.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege's constraint set — FastAPI, vanilla JS, no build step, hand-rolled 66KB CSS, indigo 'Highlighter' brand — is exactly the target user of this category. The pragmatic play is not adopting Pico wholesale (it would fight 66KB of existing brand CSS) but stealing the architecture: (1) Open Props as the token layer gives an instant professional design vocabulary — its --indigo-0..12 scale matches the brand palette family directly, and its fluid font-size tokens, shadow scale, and easing curves would replace ad-hoc magic numbers throughout the existing CSS, which is also the prerequisite for a clean dark mode; (2) modern-normalize replaces whatever hand-rolled reset the site carries, guaranteeing consistent form rendering across the mobile browsers students actually use; (3) Pico is most valuable as (a) a reference implementation to crib form/table/validation styling from (MIT, copy freely), and (b) a drop-in for secondary surfaces (admin pages, email-preview pages, docs) where zero styling effort is wanted — via its conditional .pico-scoped build so it can't leak into the main app.

**current_gap**: 

> The site has no design-token layer — 66KB of hand-rolled CSS implies repeated literal values (colors, shadows, spacing) rather than a custom-property system; no formal reset/normalize baseline is confirmed; no dark mode exists, and without tokens dark mode requires touching every rule instead of redefining ~20 variables. Form and table styling quality vs. Pico's defaults is unverified but hand-rolled forms usually lag on validation-state and focus styling.

**recommended_action**: 

> adapt (Open Props + modern-normalize), skip-for-main-app but reuse (Pico). Concrete plan: (1) vendor modern-normalize.css into static assets and load it first in a `vendor` cascade layer; delete redundant hand-rolled reset rules. (2) Vendor open-props.min.css (or just its colors, sizes, fonts, shadows, easings files) into a `tokens` layer; map brand aliases once — `:root { --brand: var(--indigo-9); --brand-highlight: var(--indigo-3); --surface: var(--gray-0); }` — then migrate hard-coded hex values in the 66KB stylesheet to tokens opportunistically whenever a file is touched. (3) Do not load full Pico in the main app; instead copy its form-validation and table styles as a starting point for the matcher forms, and use pico.conditional.min.css on low-effort internal pages. This yields a token foundation (which the dark-mode work item depends on) for ~5-6 KB gzipped total and zero build tooling.

### Uncertain Fields (skipped)

- adoption_maturity
- maintenance_health
- baseline_status
- bundle_size_kb


---

## Dark mode and theming architecture: CSS custom properties...

### Basic Info

**category**: theming

**description**: 

> The modern, no-build architecture for theming a site: (1) CSS custom properties as semantic tokens (--surface, --text, --brand) so components never reference raw colors; (2) the color-scheme property (`:root { color-scheme: light dark; }`) which opts native UI — form controls, scrollbars, canvas background — into the active scheme automatically; (3) the light-dark() function, which returns one of two colors depending on the active color scheme (`--surface: light-dark(#fff, #111827);`), eliminating the duplicated media-query blocks older dark-mode implementations required; (4) prefers-color-scheme media query as the OS-preference signal, and a small localStorage-backed toggle that overrides it by setting `data-theme="light|dark"` (which flips color-scheme, which light-dark() then follows). Together these solve the classic retrofit problem: adding dark mode to an existing site with a brand palette without duplicating the stylesheet, and offering user override with system-preference default (the UX-correct three-state pattern: system/light/dark).

**adoption_maturity**: 

> prefers-color-scheme: universal since 2020, used by virtually every major site (GitHub, MDN, Tailwind sites). CSS-custom-property token theming: the industry-standard approach in every design system (Material, Primer, shadcn themes). color-scheme: widely adopted, low-risk. light-dark(): shipped in all engines by May 2024, heavily promoted (12daysofweb, MDN, WordPress core block themes adopted the pattern in 2024-2025); rapidly becoming the default teaching pattern for new dark-mode implementations. The overall architecture is mature and stable; only light-dark() itself is young.

### Code

**code_sources**: 

> MDN light-dark(): https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/light-dark (copy-paste examples). web.dev color-scheme guide: https://web.dev/articles/color-scheme. 12 Days of Web light-dark() walkthrough: https://12daysofweb.dev/2024/css-light-dark/. Vadim Makeev 'Native light and dark color scheme switching': https://pepelsbey.dev/articles/native-light-dark/ — includes the complete three-state toggle (system/light/dark) with the small vanilla JS snippet and FOUC-free inline-script pattern. WordPress dev blog block-theme guide: https://developer.wordpress.org/news/2024/12/mastering-light-and-dark-mode-styling-in-block-themes/. Theming-in-2025 overview: https://mamutlove.com/en/blog/theming-with-css-in-2025/. Toggle skeleton (vanilla): inline `<script>document.documentElement.dataset.theme = localStorage.theme ?? 'system'</script>` in head plus a 15-line handler — pepelsbey article has the canonical version.

**license**: n/a — native CSS features plus ~15 lines of hand-written vanilla JS.

**dependency_footprint**: 

> None. Pure CSS plus a tiny inline script for the user toggle (needed to avoid flash-of-wrong-theme and persist choice). No library, no build step. Fully compatible with a no-build FastAPI + vanilla-JS site.

**bundle_size_kb**: 

> ~0. Token redefinitions add well under 1 KB of CSS; the toggle script is ~0.3 KB. Retrofitting usually shrinks CSS if it replaces duplicated per-theme blocks. No main-thread cost; theme switch is a single style recalc.

**ssr_htmx_compat**: 

> Excellent. Theme state lives on <html data-theme> plus localStorage, both outside any swapped region, so HTMX/fetch partial swaps inherit the theme automatically — swapped-in HTML is styled by the same custom properties with zero re-binding. The only care point: the theme-init script must be inline in <head> of every server-rendered page (FastAPI base template) so first paint is correct; server can also read a theme cookie to set data-theme in the HTML response itself, which is the flash-proof gold standard for SSR.

**maintenance_health**: n/a — browser-native features maintained by engine vendors.

**integration_effort**: 

> medium for the retrofit described: the hard part is not the mechanism but auditing 66KB of existing CSS to replace hard-coded colors with semantic tokens. Mechanism itself (color-scheme, tokens, toggle) is low — an afternoon. A pragmatic partial retrofit (tokenize the ~20 most-used colors covering 90% of surface area) keeps it closer to low-medium.

### Design

**key_techniques**: 

> Foundation: `:root { color-scheme: light dark; }` — this alone makes form controls, scrollbars, and default canvas dark-aware. Tokens with light-dark(): `:root { --surface: light-dark(#ffffff, #0f1220); --surface-raised: light-dark(#f8f8fb, #1a1f33); --text: light-dark(#1a1a2e, #e7e7f0); --brand: light-dark(#4f46e5, #818cf8); --highlight: light-dark(#eef2ff, #312e81); } body { background: var(--surface); color: var(--text); }`. User override that light-dark() respects: `:root[data-theme="light"] { color-scheme: light; } :root[data-theme="dark"] { color-scheme: dark; }` — no token duplication needed; flipping color-scheme flips every light-dark() at once. FOUC-free init (inline in head): `const t = localStorage.theme; if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;`. Toggle handler: cycle system->light->dark, write localStorage, set/remove data-theme. Fallback-compatible variant if supporting pre-2024 browsers: define light tokens on :root, dark overrides inside both `@media (prefers-color-scheme: dark) { :root:not([data-theme=light]) {...} }` and `:root[data-theme=dark] {...}` — more verbose but Baseline-Widely-available. Extras: `<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0f1220">` for mobile browser chrome; swap images per scheme with `<picture><source srcset="logo-dark.svg" media="(prefers-color-scheme: dark)">`; desaturate/dim brand colors in dark mode rather than inverting (indigo-600 on dark fails contrast — lighten to indigo-400 range).

**visual_examples**: 

> pepelsbey.dev (article and site implement the exact three-state pattern), MDN and web.dev sites (system-following with toggle), GitHub.com (canonical token-based multi-theme architecture), WordPress Twenty Twenty-Five block theme. The 12daysofweb.dev article includes live demos of light-dark() driven pages.

**accessibility_notes**: 

> Dark mode is itself an accessibility/comfort feature (light sensitivity, low-vision users, astigmatism halation). Requirements: re-verify every text/background pair in dark theme against WCAG 1.4.3 — dark themes commonly fail with saturated brand colors (indigo #4f46e5 on near-black is ~4:1 or worse for small text; use a lightened variant); avoid pure black #000 backgrounds with pure white text (halation — prefer #0f-#1a range surfaces and slightly dimmed text); keep focus indicators visible in both themes (2.4.7, 1.4.11 Non-text Contrast for the ring itself); respect the user's choice — a toggle must never trap users in a theme (persist and offer 'system'); form controls must not become unstyled ghosts (color-scheme handles this natively). Never implement dark mode with CSS filter: invert() — it breaks images and contrast unpredictably.

**wcag_mapping**: 

> 1.4.3 Contrast (Minimum) — every token pair must pass in both themes; 1.4.11 Non-text Contrast — borders, icons, focus rings, and chart elements need >=3:1 in dark theme too; 1.4.6 Contrast (Enhanced) — easier to hit in dark mode with dimmed-white text if targeted; 2.4.7 Focus Visible — theme-aware focus ring token required; 1.4.8 Visual Presentation (AAA) — user-selectable color schemes directly support it. Risk: 1.4.1 Use of Color unchanged but re-verify status colors (success/warning/error) in dark palette.

**progressive_enhancement_fallback**: 

> If light-dark() is unsupported (pre-mid-2024 browsers), those declarations are dropped — so provide base declarations first (`--surface:#fff; --surface: light-dark(#fff,#111);` — old browsers keep the first value) and users simply get the light theme: fully functional, brand-correct. With JS off, the OS preference still works via prefers-color-scheme/color-scheme (only the manual override is lost). No content or functionality ever depends on the theme layer.

**mobile_touch_behavior**: 

> Highly relevant for a mobile-heavy student audience: most students have OS-level dark mode on (especially at night — scholarship deadline crunch time), and a site that stays blinding white feels dated and hostile. Set theme-color meta per scheme so Android/iOS browser chrome matches. Ensure the toggle is a >=44px touch target in the header/menu, not hover-dependent. Native form controls styled by color-scheme keep correct dark keyboards/pickers on iOS (a dark input triggers the dark virtual keyboard in Safari). OLED phones get battery benefit from dark surfaces. Test sticky-header translucency/backdrop-filter in both themes.

### Applicability

**relevance_to_ensurecollege**: 

> Dark mode is the single most visible modernization the site can ship, and the memory notes it currently has none. The retrofit path fits the existing setup precisely: the 'Highlighter' brand with indigo palette maps cleanly to a token system (indigo has excellent dark-mode variants — indigo-300/400 text-on-dark, indigo-900-tinted highlight surfaces keep the highlighter metaphor working in dark: think highlighter-on-dark-paper). Because the site is FastAPI server-rendered with vanilla JS, the cookie-or-inline-script data-theme pattern drops straight into the base Jinja template, and every page inherits it — no per-page work. Doing the token audit first also pays forward: the same semantic tokens are the prerequisite for theming seasonal variants, high-contrast mode, or any future brand refresh, and it deduplicates color values in the 66KB stylesheet. Auth pages, matcher forms, and result cards are exactly the surfaces students use at night.

**current_gap**: 

> No dark mode at all; no color-scheme declaration (so even native form controls are locked light); 66KB hand-rolled CSS presumably has hard-coded hex colors throughout rather than semantic tokens; no theme-color meta variants; no toggle UI; brand palette has no documented dark-mode variants (indigo values need lightened counterparts chosen and contrast-checked).

**recommended_action**: 

> adopt. Concrete plan: (1) Add `color-scheme: light dark` to :root and ship it alone first — native controls and scrollbars go dark for OS-dark users immediately, zero risk. (2) Define ~20 semantic tokens (--surface, --surface-raised, --text, --text-muted, --brand, --brand-contrast, --highlight, --line, --focus-ring, plus status colors) using the base-then-light-dark() double-declaration pattern so pre-2024 browsers keep light mode; pick dark values as desaturated/lightened indigo (e.g. light #4f46e5 -> dark #a5b4fc for text-on-dark, highlight #eef2ff -> #312e81) and contrast-check every pair. (3) Sweep the stylesheet replacing hard-coded colors with tokens, starting with body/header/cards/forms (the 90% surface area), leaving long-tail colors for follow-up passes. (4) Add the three-state toggle (system/light/dark) to the header: 15 lines of vanilla JS, localStorage persistence, inline head script (or theme cookie read by FastAPI) to prevent flash. (5) Add per-scheme theme-color meta and a dark logo variant if the logo has dark strokes. Estimated effort: 1-2 days including the contrast audit.

### Uncertain Fields (skipped)

- baseline_status


---

## Faceted filtering and search-results UI (filter chips, re...

### Basic Info

**category**: filtering-ux

**description**: 

> The pattern set for letting users narrow a result list along multiple independent dimensions (award amount, deadline, state, major, grade level) and understand what happened: facet groups (checkboxes/radios/ranges) in a sidebar or sheet, applied-filter chips that can be removed individually, a live result count ('37 scholarships match'), sort controls, URL-reflected state so results are shareable/bookmarkable, and honest empty states. It solves the core matcher-results problem: users distrust or abandon lists they cannot narrow, and get lost when filtering happens silently.

**adoption_maturity**: 

> One of the most mature UX patterns on the web — every major e-commerce site (Amazon, Airbnb, Zillow), job boards, and scholarship databases (Fastweb, Scholarships.com, BigFuture, Appily) use it. Codified by NN/g and Baymard research since the 2000s; GOV.UK Design System publishes a tested 'filter a list' pattern. The underlying platform pieces (form GET semantics, URLSearchParams, history API, aria-live, <details>) are all long-stable. Library options exist (Algolia InstantSearch.js, MIT; Pagefind, MIT; List.js) but none is required — most production implementations on server-rendered sites are bespoke and small.

### Code

**license**: 

> n/a for the technique; GOV.UK/USWDS reference code MIT/public domain; Pagefind and InstantSearch.js MIT if ever used

**dependency_footprint**: 

> None for the recommended bespoke approach — plain HTML form + fetch against the existing FastAPI JSON endpoints. InstantSearch.js would add a hosted-service dependency (Algolia) and ~70KB+ of JS: incompatible in spirit with the no-build vanilla site and unnecessary at scholarship-database scale (hundreds to low thousands of rows filter fine server-side or even client-side).

**ssr_htmx_compat**: 

> Excellent, and this is the canonical HTMX use case: the facet form GETs to the results route, the server renders the filtered list + count as a partial, and HTMX (or a 10-line fetch wrapper) swaps it in while pushing the query string to the URL. Because state lives in the form and the URL rather than in JS objects, partial swaps are trivially safe; only the chip-remove and details-toggle listeners need delegation or re-binding. First render is fully server-side from request.query_params, so results pages work with JS disabled.

**maintenance_health**: n/a (pure technique); Pagefind and InstantSearch actively maintained as of 2026 if ever needed

**integration_effort**: 

> medium — the FastAPI matcher endpoints already accept criteria, so the work is UI: facet form, chips row, count line, sort select, URL sync, and a mobile filter sheet

### Design

**key_techniques**: 

> Facet form: one <form id="filters"> whose checkboxes/radios/selects carry proper name/value; serialize with `new URLSearchParams(new FormData(form))`. URL sync: `history.replaceState(null, '', '?' + params)` on every apply; on load, hydrate the form from `new URL(location).searchParams` so links/back-button restore state (listen to popstate). Result count: a single element `<p role="status" aria-live="polite">37 scholarships match</p>` updated after each fetch — role=status makes screen readers announce changes. Applied-filter chips: render each active filter as `<button type="button" class="chip" data-name data-value>Texas <span aria-hidden="true">×</span><span class="visually-hidden">Remove filter Texas</span></button>`; clicking unchecks the matching input and resubmits; add a 'Clear all' button when 2+ chips. Sort: a plain <select name="sort"> inside the same form (relevance/deadline/amount) — never unlabeled icon-only sort. Collapsible facet groups: native <details open> per group with the group's active-count in the <summary> ('Deadline (2)'). Debounce auto-apply ~300ms on desktop; on mobile use an explicit 'Show 37 results' apply button (batch filtering). Empty state: never a blank page — show 'No matches. Try removing filters:' followed by the chips. Loading: keep old results visible with reduced opacity + aria-busy rather than blanking (or reuse the site's future skeletons).

**visual_examples**: 

> BigFuture scholarship search (collegeboard.org) — the direct competitor reference; Fastweb and Appily scholarship filters; GOV.UK finders like https://www.gov.uk/search/news-and-communications (chips + count + sort, server-rendered); Airbnb (mobile filter sheet with 'Show N results' button); Amazon left-rail facets with counts per option; Baymard's e-commerce filtering research examples (https://baymard.com/blog/how-to-design-applied-filters).

**accessibility_notes**: 

> Announce result changes with a single polite live region (the count line) — do not make the whole results list a live region. Chips must be real <button>s with accessible names that include the word 'remove'. Keep focus sane: after removing a chip, move focus to the next chip or the count line, never lose it to <body>. Facet groups need <fieldset><legend> (or details/summary) so checkbox context is programmatic. The mobile filter sheet must trap focus while open and restore focus to the trigger on close (reuse the site's existing modal code). Auto-applying on checkbox change is fine, but auto-applying on every keystroke in a text/range facet violates predictability — debounce or batch. Ensure per-option counts ('Texas (12)') are inside the label text, not a separate unlabeled span.

**wcag_mapping**: 

> Satisfies when done right: 4.1.3 Status Messages (live result count), 1.3.1 Info and Relationships (fieldset/legend facet groups), 2.4.6 Headings and Labels, 3.2.2 On Input (explicit apply on mobile prevents unexpected context change), 2.5.8 Target Size Minimum (chips >= 24px, ideally 44px on touch), 1.4.1 Use of Color (chips convey applied state by shape+text, not color alone). Risks: unannounced result updates (4.1.3), focus loss on chip removal (2.4.3), sidebar filters hidden from keyboard users on mobile (2.1.1).

**progressive_enhancement_fallback**: 

> Because filtering is a plain GET form, the no-JS fallback is a full-page reload with server-rendered filtered results — identical functionality, slightly slower. Chips degrade to server-rendered links that hit the same route with the filter removed from the query string. <details> facet groups work without JS. This is the textbook progressive-enhancement architecture and fits FastAPI perfectly.

**mobile_touch_behavior**: 

> On small screens, move facets into a bottom sheet or full-screen overlay opened by a 'Filter' button that shows the active count ('Filter (3)'); apply via a sticky full-width 'Show 37 results' button in thumb reach — batch application avoids reflow-under-finger and repeated network churn on cellular. Chips row becomes horizontally scrollable (overflow-x:auto, scroll-snap optional) below the results heading. Keep the sort select native so it opens the OS picker. Mind sticky-header overlap when scrolling back to top after applying (scroll-margin-top on the results heading).

### Applicability

**relevance_to_ensurecollege**: 

> The matcher results pages are where students decide whether EnsureCollege is useful. Today a match run returns a list the student cannot interrogate; faceted filtering turns it into an explorable tool: filter by deadline proximity, award amount, essay/no-essay, state, major; chips make the active criteria visible and editable (which also builds trust in the matching logic); the live count gives instant feedback; URL-synced state lets students share 'my matches, no-essay, deadline < 60 days' with parents/counselors and lets the site email deep links. The same module is reusable across all three matchers (scholarships, programs, competitions), amortizing the build cost.

**current_gap**: 

> The site currently renders matcher results as a static list: no post-match refinement facets, no applied-filter chips, no live result count with screen-reader announcement, no sort control, and no URL reflection of filter state (results are not shareable/bookmarkable). Mobile has no filter sheet; the 133KB vanilla JS has modal code that could be reused for one.

**recommended_action**: 

> adopt — Build one shared vanilla module (~150-200 lines) used by all three matcher results pages: (1) wrap existing facet-able criteria in a GET <form> hitting the FastAPI results route, server-rendering the initial page; (2) enhance with fetch + partial swap of a results <section>, updating a role=status count line and history.replaceState; (3) render applied chips from the current URLSearchParams with remove buttons and 'Clear all'; (4) add a sort <select> (deadline soonest, amount highest, best match); (5) on <=768px move facets into a focus-trapped sheet reusing the existing modal JS, with a sticky 'Show N results' apply button; (6) style chips/facets in the indigo Highlighter language (chips as highlighter-swipe pills would be strongly on-brand). Skip third-party search libraries — data volume does not justify them.

### Uncertain Fields (skipped)

- code_sources
- bundle_size_kb
- baseline_status


---

## Form UX patterns (multi-step forms, inline validation, sm...

### Basic Info

**category**: form-ux

**description**: 

> A family of techniques for making long, high-stakes forms (profile intake, scholarship/program/competition matcher questionnaires) faster to complete and less error-prone: (1) multi-step / 'one thing per page' forms that chunk questions and show progress; (2) inline validation that flags errors at the field level as the user interacts, instead of only on submit; (3) smart defaults that pre-fill or pre-select the most likely answer (autocomplete tokens, remembered answers, sensible initial values); (4) customizable native form controls (styling real <select>, <input>, checkboxes) so forms look on-brand without throwing away built-in keyboard, screen-reader, and mobile behavior. Together they attack the two big form problems: abandonment on long forms and error-recovery friction.

**adoption_maturity**: 

> Very mature as UX practice: GOV.UK, USWDS, Shopify Polaris, Stripe Checkout, Typeform, and virtually every large e-commerce checkout use multi-step + inline validation. The Constraint Validation API (checkValidity/reportValidity/setCustomValidity) has been stable for a decade. :user-valid/:user-invalid pseudo-classes shipped in all engines by late 2023 and are used in production. accent-color and datalist are widely used. The newest piece — fully customizable <select> via appearance:base-select — shipped in Chrome/Edge 134 (March 2025) and is still rolling out in Firefox/Safari as of 2026, so it is early-adopter territory with graceful fallback. Community health is strong: these are platform features plus published patterns (GOV.UK, NN/g, web.dev), not a library that can be abandoned.

### Code

**code_sources**: 

> 1) web.dev 'Learn Forms' course (copy-paste vanilla HTML/CSS/JS): https://web.dev/learn/forms — validation, multi-step, autofill. 2) MDN Constraint Validation guide with full vanilla examples: https://developer.mozilla.org/en-US/docs/Web/HTML/Constraint_validation and ValidityState: https://developer.mozilla.org/en-US/docs/Web/API/ValidityState. 3) Customizable <select> tutorial with complete code: https://developer.chrome.com/blog/a-customizable-select and MDN customizable select guide: https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Customizable_select. 4) GOV.UK error summary + inline error message markup (MIT, copy-paste Nunjucks/HTML): https://design-system.service.gov.uk/components/error-summary/ and https://design-system.service.gov.uk/patterns/validation/. 5) MDN :user-invalid: https://developer.mozilla.org/en-US/docs/Web/CSS/:user-invalid. 6) HTML autocomplete token reference for smart defaults: https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/autocomplete. All are vanilla, no build step.

**license**: n/a (platform features and published patterns); GOV.UK example markup is MIT

**dependency_footprint**: 

> None. Pure HTML/CSS plus small amounts of hand-written vanilla JS (a step controller of ~50-150 lines, and a submit handler that maps ValidityState to inline messages). No script tags, npm, or framework required — fully compatible with the existing no-build FastAPI + vanilla-JS site.

**bundle_size_kb**: 

> 0 for CSS/HTML techniques; roughly 1-3 KB gzipped of hand-written JS for a multi-step controller + inline validation wiring

**ssr_htmx_compat**: 

> Excellent. All techniques work on server-rendered HTML. Constraint validation lives on the elements themselves, so fetch/HTMX partial swaps keep working as long as the delegated submit/blur listeners are attached at document level (event delegation) or re-bound after swap. Multi-step can even be done server-side (one page per step, POST between steps) which is the most robust pattern for partial-swap architectures. No shadow DOM involved, so no re-upgrade concerns.

**maintenance_health**: n/a (browser platform features; maintained by browser vendors and WHATWG/CSSWG)

**integration_effort**: 

> low (inline validation, smart defaults, accent-color) to medium (converting the existing matcher forms to multi-step with progress and per-step validation)

### Design

**key_techniques**: 

> Multi-step: one <form> with <fieldset data-step> sections toggled via hidden attribute; progress via <ol> step indicator or <progress>; validate only the current step with `[...fieldset.elements].every(el => el.reportValidity())`. Inline validation: native attributes (required, type=email, pattern, min/max, minlength) + CSS `input:user-invalid { border-color: var(--error) }` and `input:user-valid { border-color: var(--ok) }` (fires only after user interaction, unlike :invalid); JS refinement on blur: `el.addEventListener('blur', () => { el.setCustomValidity(''); if (!el.checkValidity()) show(el.validationMessage); })`; associate messages with `aria-describedby` and set `aria-invalid="true"`. Error summary on submit: focusable heading + list of anchors to failing fields (GOV.UK pattern). Smart defaults: `autocomplete="given-name family-name email postal-code"` etc. so browsers autofill; `inputmode="numeric"` + `pattern="[0-9]*"` for GPA/year fields; `<datalist>` for type-ahead suggestions (majors, states); preselect the statistically most common option; persist in-progress answers to localStorage keyed by form id. Customizable native controls: `accent-color: var(--indigo)` for checkboxes/radios/range; `select, ::picker(select) { appearance: base-select }` then style `::picker(select)`, `::picker-icon`, `::checkmark`, `option`, and use `:open`; `field-sizing: content` to auto-grow textareas (Chrome-only, harmless fallback).

**visual_examples**: 

> GOV.UK 'Apply for...' services (one thing per page, error summary): https://design-system.service.gov.uk/patterns/question-pages/; Stripe Checkout (inline validation + autofill); Typeform (one question at a time); USWDS form templates: https://designsystem.digital.gov/templates/form-templates/; Chrome team's customizable select demos: https://developer.chrome.com/blog/a-customizable-select; Common App and FAFSA (multi-step student-facing forms — FAFSA 2024+ redesign uses USWDS).

**accessibility_notes**: 

> Inline validation must not rely on color alone — pair red border with icon + text. Error text must be programmatically associated via aria-describedby and aria-invalid. Announce dynamic errors with a polite live region or move focus to an error summary on failed submit. Do not validate aggressively on every keystroke (punishes screen-reader and cognitive-load users); validate on blur or submit. Multi-step forms need: page/step title updates, focus moved to the new step's heading (tabindex="-1"), and a visible 'Step X of Y' that is also in the accessible name. Never remove focus outlines on custom-styled controls. appearance:base-select keeps the element a real <select> so it retains native semantics — far safer than div-based comboboxes.

**wcag_mapping**: 

> Satisfies: 3.3.1 Error Identification, 3.3.2 Labels or Instructions, 3.3.3 Error Suggestion, 3.3.7 Redundant Entry (smart defaults/persisted answers avoid re-asking), 1.3.5 Identify Input Purpose (autocomplete tokens), 2.4.6 Headings and Labels, 4.1.3 Status Messages (live-region error/success announcements). Risks if done badly: 3.2.2 On Input (auto-advancing steps on selection), 1.4.1 Use of Color (color-only error states), 2.4.3 Focus Order (steps shown/hidden without focus management).

**progressive_enhancement_fallback**: 

> Multi-step degrades to one long form (or true server-side per-step pages that need no JS at all). Native validation attributes work with JS off — the browser blocks submit and shows its own bubbles. :user-invalid unsupported → no inline color, but submit-time server validation still returns errors. appearance:base-select unsupported → browsers ignore the declaration and render the normal native select (explicitly designed to be progressive enhancement). datalist unsupported → plain text input. Nothing breaks hard.

**mobile_touch_behavior**: 

> Use correct type/inputmode so the right virtual keyboard appears (email, numeric for GPA/year, tel). Keep one column; place primary 'Continue' button full-width in thumb reach at the bottom. Beware the virtual keyboard covering inline error text — show errors above or adjacent to the field, and use scrollIntoView({block:'center'}) after failed validation. Native selects open the OS picker sheet on mobile, which is excellent UX — another reason to style natives rather than replace them. Multi-step strongly outperforms long scroll forms on phones for the student audience.

### Applicability

**relevance_to_ensurecollege**: 

> The matcher forms (scholarship, program, competition) are the core conversion surface of EnsureCollege: a student who abandons the intake form gets zero matches. Multi-step with a progress indicator makes the ~10-20-question intake feel short; inline validation prevents the frustrating submit-fail-scroll-hunt loop; autocomplete tokens speed up name/email/zip entry for teens on phones; persisted answers satisfy Redundant Entry across the three matchers (ask GPA once, reuse everywhere). Styling native controls with accent-color in the indigo palette keeps the editorial 'Highlighter' brand consistent without a component library, and appearance:base-select can later make the major/state dropdowns fully on-brand as browser support arrives.

**current_gap**: 

> The current site has hand-rolled CSS and vanilla JS with ARIA-labelled modals/tabs, but the matcher forms are single long pages with submit-time-only validation, no step indicator, no :user-invalid styling, no error summary, inconsistent autocomplete attributes, and default blue checkboxes/radios that clash with the indigo palette. Answers are not shared between the three matchers, so students re-enter GPA/grade/state.

**recommended_action**: 

> adopt — Highest-leverage item in this research set. Concretely: (1) add `accent-color: var(--indigo-600)` and :user-valid/:user-invalid styles to the existing 66KB stylesheet (minutes of work); (2) add autocomplete/inputmode/pattern attributes to every matcher field; (3) refactor each matcher form into 3-4 fieldset steps driven by a ~100-line shared step controller with per-step reportValidity(), focus management, and a 'Step X of Y' indicator styled like the GOV.UK/USWDS step indicator; (4) on submit failure render a GOV.UK-style error summary that links to fields; (5) persist answers to localStorage under a shared profile key so all three matchers pre-fill. Defer appearance:base-select styling until Firefox/Safari ship it; it degrades safely if added early.

### Uncertain Fields (skipped)

- baseline_status


---

## Government design systems as form-pattern code sources (G...

### Basic Info

**category**: component-library (task category: design-system)

**description**: 

> GOV.UK Frontend (alphagov/govuk-frontend, the code behind the GOV.UK Design System) and the U.S. Web Design System (uswds/uswds) are production design systems built specifically for high-stakes citizen forms — benefits, taxes, visas, FAFSA. They solve the 'where do I get battle-tested, accessible form markup' problem: both publish permissively licensed, WCAG-2.2-AA-tested HTML/CSS/JS for exactly the components a matcher flow needs — multi-step question pages, step indicators, error summaries, inline error messages, radios/checkboxes, date inputs, character counts, and task lists. They can be used as full frameworks or, more usefully here, as reference implementations to copy patterns and markup from without adopting the whole system.

### Code

**code_sources**: 

> GOV.UK: repo https://github.com/alphagov/govuk-frontend (npm 'govuk-frontend'); component docs with copy-paste HTML at https://design-system.service.gov.uk/components/ — key items: error-summary (https://design-system.service.gov.uk/components/error-summary/), error-message, radios, checkboxes, date-input, character-count, task-list, and the 'Complete multiple tasks' and 'Question pages' patterns (https://design-system.service.gov.uk/patterns/question-pages/), form validation pattern (https://design-system.service.gov.uk/patterns/validation/). Step-by-step navigation pattern: https://design-system.service.gov.uk/patterns/step-by-step-navigation/. USWDS: repo https://github.com/uswds/uswds; component docs with HTML at https://designsystem.digital.gov/components/ — key items: step indicator (https://designsystem.digital.gov/components/step-indicator/), form templates (https://designsystem.digital.gov/templates/form-templates/), validation (https://designsystem.digital.gov/components/validation/), combo box, input mask, character count. Every component page shows raw HTML you can paste into Jinja/FastAPI templates.

**dependency_footprint**: 

> Used as intended: npm + Sass build (both are Sass-first), which conflicts with the no-build constraint. However, both ship precompiled dist CSS/JS usable via a plain script/link tag (GOV.UK publishes govuk-frontend-<version>.min.css/js release assets; USWDS dist includes uswds.min.css/js), and — the recommended route here — the HTML patterns can be copied and restyled with the site's own CSS at zero dependency cost. Full-framework adoption would also drag in each system's opinionated typography/branding, which fights the Highlighter brand.

**ssr_htmx_compat**: 

> Both are server-rendered-HTML-first with progressive-enhancement JS — an excellent match for FastAPI. GOV.UK Frontend v5 initialises via data-module attributes with initAll()/createAll(), and both accept a scope/root element, so after an HTMX/fetch partial swap you can re-run initAll(swappedContainer) (or createAll(Component, config, container)) to re-bind. USWDS components expose behavior objects with .on(el)/.off(el) for the same purpose. No shadow DOM (except the new optional USWDS banner web component), so no DSD concerns.

**integration_effort**: 

> low (copy HTML patterns + adapt CSS to existing stylesheet) / medium-high (adopt either system wholesale with its build chain — not recommended for this site)

### Design

**key_techniques**: 

> Error summary: `<div class="error-summary" role="alert" tabindex="-1">` containing an h2 ('There is a problem') and an <ul> of anchors like `<a href="#gpa">Enter a GPA between 0 and 5</a>`; on failed submit, focus the container. Inline errors: error text in a <p> whose id is in the input's aria-describedby, plus a visible left border on the form group; input gets aria-invalid. Step indicator (USWDS): `<ol class="usa-step-indicator__segments">` with `usa-step-indicator__segment--complete/--current` and `aria-current="step"` on the current segment, counter text in a visually-hidden span. Question pages (GOV.UK): one question per page, `<h1><label for=…>` pattern so the question is both heading and label. Date input: three separate day/month/year text inputs with inputmode=numeric instead of a date picker. Character count: live-updated remaining-character message in an aria-live=polite region paired with maxlength. Task list: per-section status tags (Completed / Incomplete) — ideal for a 'complete your profile' hub. All markup is plain HTML + BEM-ish classes; behaviors are small vanilla-JS modules keyed off data-module attributes.

**visual_examples**: 

> https://design-system.service.gov.uk/components/ (live rendered examples of every component); GOV.UK prototype examples in real services like https://www.gov.uk/apply-first-provisional-driving-licence; https://designsystem.digital.gov/components/step-indicator/ live demo; the redesigned FAFSA (studentaid.gov) as a USWDS multi-step form aimed at the exact same student audience as EnsureCollege; VA.gov form flows.

**accessibility_notes**: 

> This is the main reason to copy from these systems: every component has been through repeated audits (GOV.UK ran a dedicated WCAG 2.2 programme, with DAC audits; USWDS tests against Section 508/WCAG 2.1-2.2 AA) and, uniquely, publishes the research behind decisions (e.g. why GOV.UK avoids native date pickers and select-heavy forms, why error messages are specific and prefixed with 'Error:'). Pitfalls when borrowing: keep the focus-management JS, not just the markup (error summary must receive focus; step changes must move focus); keep the visually-hidden text in step indicators; if you restyle, preserve the systems' 3:1 contrast on focus indicators and error borders.

**wcag_mapping**: 

> Components are explicitly built to satisfy WCAG 2.2 AA, including the new-in-2.2 criteria: 2.4.11 Focus Not Obscured (focus styles + spacing), 2.5.8 Target Size Minimum (44px-class touch targets), 3.2.6 Consistent Help, 3.3.7 Redundant Entry (task-list/save-and-return patterns), 3.3.8 Accessible Authentication. Also the classics: 1.3.1 Info and Relationships, 2.4.6 Headings and Labels, 3.3.1-3.3.3 error criteria, 4.1.3 Status Messages (character count, error summary).

**baseline_status**: 

> n/a as a whole (it is a library, not a platform feature); both systems deliberately restrict themselves to Baseline Widely available CSS/JS and support browsers per GDS/GSA support policies, so copied patterns are safe on a no-build site.

**progressive_enhancement_fallback**: 

> Core philosophy of both systems: every component works as plain HTML with JS disabled (forms submit, errors render server-side, step indicator is a static list, accordions render expanded/stacked). GOV.UK Frontend v5 dropped IE support but kept the no-JS baseline; USWDS removed IE polyfills in 3.10.0 while keeping server-rendered fallbacks. Copying their patterns therefore gives EnsureCollege free progressive enhancement.

**mobile_touch_behavior**: 

> Both are mobile-first with government-mandated small-screen testing: 44-48px touch targets, full-width buttons and inputs on small screens, single-column question pages, numeric inputmode on date/number fields, and step indicators that collapse to 'Step 2 of 4' text on narrow viewports (USWDS `usa-step-indicator--counters-sm` variants). GOV.UK research on mobile form completion directly informed the one-thing-per-page pattern — highly relevant to a phone-heavy student audience.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege's matcher intake is functionally a government-style eligibility form (the FAFSA is literally the adjacent product), so these systems are the best free source of proven, liability-reducing form UX: copy the error-summary + inline-error pattern for matcher validation, the USWDS step indicator for the multi-step matchers, the GOV.UK task list for a 'complete your profile' dashboard across the three matchers, and the question-page/date-input research to decide question phrasing and control choices. MIT/public-domain licensing means markup and CSS can be pasted into the FastAPI Jinja templates and restyled in the indigo Highlighter brand with zero legal or dependency cost.

**current_gap**: 

> The site currently has no error summary, no standardized inline error pattern, no step indicator, no task-list/progress hub, and its hand-rolled form CSS has not been audited against WCAG 2.2 (target size, focus obscured, redundant entry). Validation feedback is ad hoc per form rather than a single tested pattern.

**recommended_action**: 

> adapt — Do not adopt either system wholesale (Sass build chain + strong visual identity would fight the no-build constraint and the Highlighter brand). Instead: (1) port the GOV.UK error-summary + error-message markup and focus behavior into a shared Jinja macro + ~40 lines of CSS in the indigo palette; (2) port the USWDS step indicator markup for the multi-step matcher forms; (3) adopt the GOV.UK task-list pattern for the profile/matches hub; (4) adopt their content guidelines (specific error text, 'Step X of Y', one question per screen) verbatim; (5) keep a bookmark to both changelogs — when WCAG guidance shifts, these repos update first and serve as a free compliance watch.

### Uncertain Fields (skipped)

- adoption_maturity
- license
- bundle_size_kb
- maintenance_health


---

## HTMX and progressive enhancement for FastAPI

### Basic Info

**category**: progressive-enhancement

**description**: 

> HTMX is a dependency-free JS library that extends HTML with attributes (hx-get, hx-post, hx-target, hx-swap, hx-trigger) so any element can issue HTTP requests and swap server-rendered HTML fragments into the page — replacing hand-rolled fetch + innerHTML plumbing with declarative markup and keeping all rendering logic on the server (a natural fit for FastAPI + Jinja2). Companions/alternatives: Alpine.js (~7 kB) adds declarative client-side state and behavior (x-data, x-show, x-on) for the purely local interactivity HTMX doesn't cover (dropdowns, toggles, modals); Datastar (v1.0, 2025/2026) is a newer single library that merges both roles — hypermedia swaps plus reactive signals — with an SSE-first design, positioned as an htmx+Alpine replacement. All three implement the same philosophy: HTML over the wire, server as source of truth, minimal client JS, no build step.

### Code

**code_sources**: 

> HTMX: https://github.com/bigskysoftware/htmx and https://htmx.org/docs/ (excellent attribute-by-attribute docs with inline demos), examples gallery https://htmx.org/examples/ (active search, infinite scroll, inline validation, modal dialogs — all directly relevant patterns). FastAPI integration: https://github.com/volfpeter/fasthx (fasthx decorator library for Jinja2/HTMY partials), FastAPI+HTMX tutorials at https://testdriven.io/blog/fastapi-htmx/; core server pattern needs no library — check request.headers.get('HX-Request') and return either a full page or a fragment template. Alpine.js: https://github.com/alpinejs/alpine, https://alpinejs.dev (component patterns). Datastar: https://github.com/starfederation/datastar, https://data-star.dev, Python SDK https://pypi.org/project/datastar-py/ (has FastAPI/Starlette helpers for SSE responses). Copy-paste HTMX example: <input type="search" name="q" hx-get="/scholarships/search" hx-trigger="input changed delay:300ms" hx-target="#results" hx-swap="innerHTML"> with a FastAPI route returning a rendered results-partial template.

**license**: 

> HTMX: BSD Zero Clause (0BSD — public-domain-equivalent). Alpine.js: MIT. Datastar: MIT. fasthx: MIT. datastar-py: MIT.

**dependency_footprint**: 

> Single script tag each; no npm, no build step — all three are explicitly designed for no-build sites and can be self-hosted as one static file. HTMX and Alpine have zero dependencies. Server side: FastAPI needs only Jinja2 (already standard) — fasthx or datastar-py are optional conveniences. Nothing here is incompatible with the existing FastAPI + vanilla-JS single-page setup; HTMX can be adopted route-by-route alongside existing fetch code.

**integration_effort**: 

> low — HTMX is designed for incremental adoption in exactly this situation: add the script tag, pick one interaction (e.g. matcher search), add a fragment-returning branch to the FastAPI route, replace the fetch code for that interaction, repeat. No rewrite required; existing vanilla JS keeps working untouched. Datastar as a wholesale replacement would be medium effort (SSE endpoints, signals model rethink). Alpine is low effort for local widgets but overlaps with already-written modal/tab code, so adopt only where it deletes more code than it adds.

### Design

**key_techniques**: 

> 1) Core HTMX attributes: hx-get/post/put/delete (issue request), hx-target + hx-swap (innerHTML|outerHTML|beforeend...) (where the returned HTML lands), hx-trigger (input changed delay:300ms for debounced live search; revealed for infinite scroll), hx-indicator (auto-toggles .htmx-request class — pairs with skeleton screens), hx-push-url for history, hx-boost to progressively enhance normal <a>/<form> into AJAX navigation. 2) Server-side content negotiation: if 'HX-Request' in request.headers: return partial template else full page — one Jinja2 file using {% block %} reuse or separate _partial.html; fasthx wraps this as a decorator. 3) Response headers: HX-Trigger (fire client events from the server, e.g. show toast), HX-Redirect, HX-Retarget. 4) Out-of-band swaps (hx-swap-oob) to update the saved-count badge and the results list from one response. 5) Alpine for pure-client state: x-data="{open:false}" x-show="open" @click.outside="open=false" for dropdowns; x-model for instant client-side filter chips. 6) Datastar equivalents: data-on-click="@get('/endpoint')", data-signals, SSE patches via datastar-py's patch_elements/patch_signals. 7) View-transition integration: hx-swap="innerHTML transition:true" or htmx.config.globalViewTransitions = true.

**accessibility_notes**: 

> Server-rendered HTML is a strong a11y baseline, but partial swaps have known pitfalls: (1) Focus management — a swap that replaces the focused element silently drops keyboard focus to <body>; use idiomorph/hx-preserve for form regions, or move focus explicitly (autofocus in the fragment or an htmx:afterSwap handler). (2) Announcements — swapped-in results are not announced to screen readers by default; make the results container an aria-live="polite" region or include a visually-hidden status line ('12 scholarships found') in the fragment (also satisfies 4.1.3). (3) hx-boost preserves real links/forms, so semantics and no-JS behavior stay intact — prefer it over click-handlers-on-divs. (4) Alpine x-show toggles need aria-expanded/aria-controls managed manually. HTMX itself adds no ARIA — the server templates carry full responsibility, which suits a team already writing ARIA-labelled modals/tabs. Datastar's morphing preserves focus by default, an a11y advantage.

**wcag_mapping**: 

> Directly supports 4.1.3 Status Messages (live-region result announcements), 2.4.3 Focus Order (must be actively managed across swaps — the main risk), 3.2.2 On Input (debounced hx-trigger search must not move focus or change context unexpectedly), 3.3.1/3.3.3 Error Identification and Suggestion (inline server-side validation fragments are an htmx sweet spot), 3.3.7 Redundant Entry (server-rendered forms can re-populate previously entered data on every fragment), and 2.5.3 Label in Name (server templates keep visible text and accessible names in one place). Risk criteria if done carelessly: 4.1.2 (custom controls in swapped fragments) and 2.4.3.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege is FastAPI + Jinja2-style server rendering + 133 KB of hand-rolled vanilla JS whose biggest chunk is presumably fetch-and-render plumbing for the scholarship/program/competition matchers, auth flows, and forms — exactly the code HTMX exists to delete. Matcher filtering becomes a form with hx-get + hx-target="#results" returning a rendered results partial; inline field validation on signup posts to a FastAPI validator returning the field's error fragment; saved-scholarship toggles use hx-post with an oob badge update; infinite scroll on long result lists is one attribute. This consolidates truth on the server (matching logic already lives there), shrinks the JS the team must maintain, and pairs cleanly with the other researched patterns (skeletons via hx-indicator, view transitions via transition:true). Alpine (or the existing vanilla code) covers dropdowns/menus. For a small team, fewer moving parts beats client-side sophistication.

**recommended_action**: 

> adopt (HTMX 2.x now; watch v4) — concretely: (1) Self-host htmx 2.0.9 (~14 KB) with a plain script tag; set htmx.config.globalViewTransitions = true. (2) Establish the partial-template convention: each matcher page template extracts a _results.html partial; routes check the HX-Request header and return partial or full page (or adopt fasthx decorators). (3) Migrate one flow end-to-end as the pilot — scholarship matcher search/filter with hx-get, 300ms debounce, hx-indicator-driven skeleton cards, aria-live on the results container, hx-push-url for shareable filtered URLs. (4) Convert saves/bookmarks and inline form validation next; delete the corresponding hand-rolled fetch code as each flow moves (target: cut the 133 KB JS substantially). (5) Skip Alpine for now — the site already has working modal/tab JS; revisit only if new local-state widgets are needed. (6) Track Datastar with interest but don't adopt: v1.0 is young, the SSE-first model is a bigger architectural bet, and htmx's incremental path fits an existing site better. Defer any htmx v4 upgrade until it's stable and the migration guide is final.

### Uncertain Fields (skipped)

- adoption_maturity
- bundle_size_kb
- ssr_htmx_compat
- maintenance_health
- visual_examples
- baseline_status
- progressive_enhancement_fallback
- mobile_touch_behavior
- current_gap


---

## Landing and hero conversion patterns

### Basic Info

**category**: conversion

**description**: 

> The set of above-the-fold and landing-page patterns that turn first-time visitors into signups: a benefit-led hero (headline stating the outcome, subhead stating the mechanism, one primary CTA), social proof bands (partner/press logos, aggregate numbers like 'X scholarships matched', star ratings, testimonial cards with names/photos/schools), trust signals (privacy assurances, 'free forever' clarity, security cues, credible affiliations), and CTA design (visual hierarchy, action-specific labels, friction reduction like 'no credit card / takes 2 minutes' microcopy). For a student audience the pattern set skews toward peer proof (testimonials from students like them), skepticism-defusing honesty (students are wary of scholarship-scam sites), and mobile-first layout (sticky or early-repeat CTA within thumb reach). Solves the problem of high bounce on the landing page and low signup conversion despite a working product.

### Code

**license**: 

> n/a — pure technique and layout patterns; any icons/illustrations used carry their own licenses (choose MIT/CC0 sets like Lucide or Heroicons, both MIT).

**dependency_footprint**: 

> None — semantic HTML + the existing hand-rolled CSS. Optional 10-20 lines of vanilla JS for an IntersectionObserver-triggered stat count-up or testimonial rotation. No script tag, npm, build step, or framework required; fully compatible with the no-build FastAPI site. Real logos/testimonials require content assets and permission from the people quoted — the real dependency is editorial, not technical.

**ssr_htmx_compat**: 

> Perfect — these are static server-rendered sections with no client state, so they survive any rendering strategy. If the stat band pulls live numbers ('12,482 matches made'), render them server-side in the Jinja template (better for SEO and no flash of zero); an htmx hx-get with hx-trigger="revealed" can lazy-refresh them. Testimonial carousels, if used, should be the CSS scroll-snap pattern (see the CSS animation research item) so no re-binding is needed after swaps.

**maintenance_health**: 

> n/a (technique). The maintenance burden is content freshness: stale testimonials, dead partner logos, and outdated stats actively damage trust — schedule quarterly review of proof content.

**integration_effort**: 

> low technically (a day or two of template + CSS work per section). Medium overall because credible proof assets must exist: real student testimonials with permission, honest usage numbers, any school/organization affiliations. Fabricating or implying fake proof is both an ethics and (in the US) an FTC endorsement-guides problem — collect real proof first.

### Design

**key_techniques**: 

> 1) Hero formula: H1 = outcome in the student's words ('Find scholarships you actually qualify for'), subhead = mechanism + differentiator ('Free matcher for scholarships, programs, and competitions — built for students, no spam'), one primary CTA button + optional ghost secondary ('See how it works'); value prop visible without scrolling on a 360px viewport. 2) CTA design: action + outcome label ('Find my scholarships' beats 'Sign up'/'Submit'); one visually dominant button per view (solid indigo fill, ghost styles for everything else); friction microcopy directly under the button ('Free · No credit card · 2 minutes'); repeat the CTA after each major scroll section and as a mobile sticky bar. 3) Social proof band ordering: numbers band (scholarships indexed, matches made, total $ value) -> testimonial cards (photo/initials, first name + school year, one specific sentence: outcomes not adjectives) -> logo band (schools, clubs, press) with 'As used by students at…' framing if institutions aren't formal partners (must stay truthful). 4) Trust signals for a scam-wary scholarship audience: explicit 'Always free — we never charge for matches', a one-line privacy promise near the email field ('We never sell your data') linking to the policy, a real about/contact page, https padlock hygiene, and no dark patterns (no fake countdowns or fake scarcity — students share scam warnings). 5) Risk reversal: show sample results before requiring signup (a 'preview 3 matches' teaser), delaying the auth wall until value is demonstrated. 6) Visual: real student photography or on-brand highlighter-style illustration; avoid generic stock which measurably reduces trust (NN/g).

**accessibility_notes**: 

> Logo bands: each logo needs meaningful alt text ('University of X logo') or alt="" if purely decorative and named in adjacent text; grayscale-on-hover-to-color effects must not be the only information carrier. Testimonials: use <figure>/<blockquote>/<figcaption>, not ARIA-free divs; if rotating, provide pause control (2.2.2) and never auto-rotate faster than readers read. Stat count-ups: animate only with prefers-reduced-motion honored and ensure the final number is in the DOM immediately for screen readers (animate a visual layer, keep real text static, or set aria-hidden on the animating span with a visually-hidden static value). CTAs: 4.5:1 text contrast on the indigo fill (white on indigo-600+ passes; verify exact palette token), visible focus ring, minimum 24x24 target (aim 44px height on mobile). Sticky mobile CTA bars must not obscure focused inputs or content (2.4.11) and must respect safe-area insets. Headline text over hero imagery needs a contrast-guaranteeing overlay.

**wcag_mapping**: 

> 1.4.3 Contrast Minimum and 1.4.11 Non-text Contrast (CTA button on brand indigo, logo band on tinted background); 2.4.11 Focus Not Obscured - Minimum (sticky CTA bar overlapping focused fields — the classic new-WCAG-2.2 failure); 2.5.8 Target Size Minimum (mobile CTA and any carousel controls); 2.2.2 Pause Stop Hide (auto-rotating testimonials); 1.1.1 Non-text Content (logo alts, hero imagery); 2.4.6 Headings and Labels (benefit-led H1 is also the page's programmatic heading); 3.1.5-adjacent plain language for a teen audience (advisory); 4.1.2 if any custom carousel controls are added.

**progressive_enhancement_fallback**: 

> Fully functional with zero JS and zero modern CSS: the hero, proof bands, and CTAs are static server-rendered content; count-ups fall back to the final static number; testimonial 'carousels' fall back to a plain scrollable or stacked list; the sticky CTA degrades to an in-flow button. Nothing on a conversion-critical path should depend on JS — the signup CTA is a real <a>/<form> that works on first paint.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege's whole funnel starts at the landing hero: students (and parents) arrive from search/social with high scam-skepticism about anything scholarship-related, so trust signals and honest free-forever messaging are not decoration — they are the conversion mechanism. The matchers are the product's demonstrable value, which enables the strongest pattern available: a no-signup preview ('answer 3 questions, see 3 real matches') as the hero CTA, with the auth wall after value is shown. The editorial 'Highlighter' brand gives a distinctive proof-band treatment for free: highlighter-swipe underlines on key stats and testimonial pull-quotes styled like annotated notes, in the indigo palette. Numbers the site can honestly compute today (scholarships indexed, total award $ value in the database, matches run) make an immediate stat band without needing user testimonials on day one.

**recommended_action**: 

> adapt — a straight adoption of SaaS-landing tropes would clash with the editorial brand and the scam-wary audience, so adapt the patterns: (1) Rewrite the hero to outcome + mechanism + single CTA ('Find scholarships you actually qualify for' / free-matcher subhead / 'Find my scholarships'), with 'Free · No credit card · 2 minutes' microcopy. (2) Build a preview-first funnel: 3-question mini-matcher in or directly under the hero returning 3 real (partially blurred or capped) matches, signup CTA to unlock the rest. (3) Add a server-rendered stat band from real database counts (scholarships indexed, total $ value, matches run) with highlighter-underline styling; add an IntersectionObserver count-up gated by prefers-reduced-motion. (4) Collect 3-5 real student testimonials (name, school year, specific outcome) via an in-product prompt after a successful match; render as <figure> cards in a scroll-snap strip — no auto-rotation. (5) Add trust microcopy at every data-collection point ('We never sell your data') plus a human about page. (6) Add a dismissible sticky bottom CTA on mobile with safe-area padding and keyboard-aware hiding. Do NOT add fake urgency, fabricated counters, or implied partnerships — one detected fake destroys credibility with this audience permanently.

### Uncertain Fields (skipped)

- adoption_maturity
- code_sources
- bundle_size_kb
- visual_examples
- baseline_status
- mobile_touch_behavior
- current_gap


---

## Loading and perceived-performance patterns

### Basic Info

**category**: performance

**description**: 

> A family of techniques that make a site feel fast even when network or server work takes time: skeleton screens (placeholder shapes shown while content loads, replacing spinners), optimistic UI (update the interface immediately on user action and reconcile with the server response later), the CSS content-visibility property (skip rendering work for off-screen sections), the Speculation Rules API (declaratively prefetch/prerender likely next pages for near-instant navigation), and Core Web Vitals budgets — especially INP <= 200ms — as the measurable target that keeps interactions responsive on mid-range mobile hardware. Together they attack both actual latency (prerender, content-visibility) and perceived latency (skeletons, optimistic UI).

**adoption_maturity**: 

> All mainstream as of 2024-2026. Skeleton screens are ubiquitous (LinkedIn, YouTube, Facebook, Slack popularized them; every major design system has a Skeleton component). Optimistic UI is standard in social/todo-style apps (Twitter/X likes, Gmail archive) and is a first-class pattern in React 19 (useOptimistic), but the underlying idea is framework-agnostic. content-visibility shipped in Chrome 85 (2020) and became cross-engine when Safari 26 shipped it in September 2025 — now Baseline Newly available. Speculation Rules is deployed on large Chromium-traffic sites (used by WordPress core as of 6.8 for prefetch, and by many news/e-commerce sites); it remains Chromium-only in production (Safari 26.2 has it behind a flag, Firefox has not shipped). INP formally replaced FID as a Core Web Vital on March 12, 2024 and is the primary responsiveness metric in Search Console and CrUX.

### Code

**code_sources**: 

> Skeletons: https://css-tricks.com/building-skeleton-screens-css-custom-properties/ (pure-CSS shimmer), https://web.dev/articles/building-a-loading-bar-component; simple copy-paste pattern: .skeleton { background: linear-gradient(90deg, #eee 25%, #f5f5f5 50%, #eee 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; border-radius: 4px; } @keyframes shimmer { to { background-position: -200% 0; } }. content-visibility: https://web.dev/articles/content-visibility (canonical article with code), https://developer.mozilla.org/en-US/docs/Web/CSS/content-visibility — .below-fold-section { content-visibility: auto; contain-intrinsic-size: auto 480px; }. Speculation Rules: https://developer.chrome.com/docs/web-platform/prerender-pages and https://developer.mozilla.org/en-US/docs/Web/API/Speculation_Rules_API — <script type="speculationrules">{"prerender":[{"where":{"href_matches":"/*"},"eagerness":"moderate"}]}</script>. Optimistic UI in vanilla JS: pattern documented at https://www.smashingmagazine.com/2016/11/true-lies-of-optimistic-user-interfaces/ (concept) — implementation is app code: flip the DOM state first, fire fetch(), revert + toast on failure. INP: https://web.dev/articles/inp and https://web.dev/articles/optimize-inp (yield with scheduler.yield()/setTimeout, avoid long tasks); measurement via https://github.com/GoogleChrome/web-vitals (web-vitals.js).

**license**: 

> n/a for the techniques themselves (skeletons, optimistic UI, content-visibility, Speculation Rules are platform features/patterns). The optional web-vitals measurement library is Apache-2.0.

**dependency_footprint**: 

> None — every piece works on a no-build vanilla-JS site. Skeletons are pure CSS + a few lines of JS to swap them out. content-visibility is one CSS declaration. Speculation Rules is an inline JSON <script> tag. Optimistic UI is a coding style around existing fetch calls. Optional: web-vitals.js (~2 KB gzipped) via a plain <script type=module> from a self-hosted copy for RUM measurement. Fully compatible with FastAPI server rendering.

**ssr_htmx_compat**: 

> Excellent fit with server rendering. Skeletons: render skeleton markup in the initial HTML (or as the htmx indicator via hx-indicator / the .htmx-request class) and let the partial swap replace it — no re-upgrade concerns since it is plain HTML/CSS. content-visibility is pure CSS and survives any swap. Speculation Rules targets full-page navigations, which complements (rather than conflicts with) htmx partial swaps — use it for the marketing/browse pages and htmx for in-page updates; note prerendered pages should be idempotent GETs, and analytics should use the prerenderingchange event to avoid double-counting. Optimistic UI maps naturally onto fetch/htmx: with htmx, hx-swap with a settling class approximates it; hand-rolled fetch gives full control for revert-on-error.

**maintenance_health**: 

> n/a (platform features). web-vitals.js is actively maintained by the Google Chrome team (v4.x/v5.x line, regular releases through 2025-2026).

**integration_effort**: 

> low — skeletons and content-visibility are hours of work in existing CSS; Speculation Rules is a single script tag plus verification; optimistic UI is a per-interaction refactor (low per interaction, medium if applied across all matcher actions). Setting an INP/CWV budget requires only adding measurement and a checklist, not new infrastructure.

### Design

**key_techniques**: 

> 1) Skeleton screens: fixed-dimension placeholder blocks matching final layout (prevents CLS), CSS shimmer via animated gradient, swap on data arrival; keep skeleton visible a minimum ~300ms to avoid flash. 2) Optimistic UI: onclick -> mutate DOM immediately (e.g. 'Saved' state on a scholarship bookmark) -> fetch POST -> on !res.ok revert DOM + show non-blocking error toast; queue or disable only truly non-idempotent actions. 3) content-visibility: auto with contain-intrinsic-size: auto 480px on below-the-fold sections (results lists, footer clusters) so the browser skips layout/paint for off-screen content while keeping it findable (find-in-page and a11y tree still work, unlike display:none). 4) Speculation Rules: <script type="speculationrules"> with prefetch (safe, broad) and prerender with "eagerness": "moderate" (triggers on hover/pointerdown) for the top nav links; document rules with where/href_matches avoid hand-listing URLs. 5) INP <= 200ms budget: break long tasks (>50ms) with scheduler.yield() or await new Promise(r => setTimeout(r)) inside heavy matcher filtering loops; give instant visual feedback (pressed state) before heavy work; measure at 75th percentile on real mobile devices. 6) Companion CWV budgets: LCP <= 2.5s (preload hero image/font, fetchpriority="high"), CLS <= 0.1 (dimensioned images, reserved skeleton space).

**accessibility_notes**: 

> Skeletons: mark the loading region with aria-busy="true" while placeholder is shown and remove it when content lands; hide decorative skeleton blocks with aria-hidden="true"; announce completion for long loads via a polite live region rather than leaving screen-reader users guessing. Respect prefers-reduced-motion by stopping the shimmer animation. Optimistic UI: state changes must be conveyed to assistive tech (aria-pressed on toggle buttons, live-region toast on failure/rollback) — a silent visual revert is a WCAG failure mode. content-visibility keeps content in the accessibility tree (unlike visibility:hidden), which is exactly why it is the right tool; avoid it on elements containing the page's landmarks if testing shows AT navigation quirks. Prerendering is invisible to users but keep focus management sane on arrival. Fast INP directly benefits users with motor/cognitive disabilities who are disproportionately hurt by unresponsive UIs.

**wcag_mapping**: 

> Supports 4.1.3 Status Messages (loading/success/failure announced via live regions rather than visual-only), 2.2.2 Pause Stop Hide (shimmer must respect reduced motion; infinite animations that can't be paused risk failure only if they last >5s and are distracting — keep skeletons short), 3.2.2 On Input (optimistic updates must not cause unexpected context change), 1.4.13-adjacent stability via CLS control, and 2.3.3 Animation from Interactions (AAA — honor prefers-reduced-motion). No criterion is inherently violated by these patterns when live regions and reduced-motion are handled.

**progressive_enhancement_fallback**: 

> All patterns degrade to nothing-lost: without content-visibility support the page simply renders everything up front (slightly slower, identical output). Unsupported browsers ignore the speculationrules script entirely — navigation is just a normal page load. Skeletons are only shown by the loading code path; with JS off, FastAPI's server-rendered HTML arrives complete and no skeleton is needed (avoid shipping skeleton-only markup that requires JS to replace — render real content server-side wherever possible). Optimistic UI falls back to standard request/response if the enhancement layer is absent.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege's core loops — run a scholarship/program/competition match, browse a results list, save/bookmark items, fill auth and profile forms — are all latency-sensitive fetch round-trips on a mobile-heavy student audience. Skeleton cards shaped like the scholarship result cards would make matcher queries feel dramatically faster than the current blank-wait or spinner. Optimistic UI on save/bookmark and on filter toggles makes the app feel native. content-visibility: auto on the long results list and below-fold landing sections cuts initial render cost of a page already carrying 66KB CSS + 133KB JS. Speculation Rules (prefetch + moderate prerender) on the landing -> matcher and matcher -> detail navigations gives near-instant transitions in Chrome/Android — the dominant student browser — for one script tag. An INP <= 200ms / LCP <= 2.5s / CLS <= 0.1 budget gives the team an objective bar as the vanilla-JS bundle grows, and matters for SEO since scholarship discovery traffic is search-driven.

**current_gap**: 

> The site currently has no skeleton screens (listed explicitly as missing), no content-visibility usage, no speculation rules, and no performance budget or RUM measurement. The 133KB of hand-rolled vanilla JS likely contains long filtering/render loops that threaten INP on low-end devices. Loading states today are ad-hoc around fetch calls; failures and pending states are not standardized, and there is no optimistic path on save-type actions.

**recommended_action**: 

> adopt — in priority order: (1) Add a .skeleton utility to the existing 66KB CSS and render 5-6 skeleton result cards (with aria-busy on the container) whenever a matcher query is in flight; reserve exact card dimensions to keep CLS at 0. (2) Add content-visibility: auto; contain-intrinsic-size: auto 420px to result-card list items and below-fold landing sections — two lines of CSS, immediate render savings. (3) Drop one speculationrules script tag with prefetch (immediate) for the top 3 nav targets and prerender with moderate eagerness for internal links; verify in chrome://process-internals. (4) Convert bookmark/save buttons to optimistic toggles with revert-on-error toast. (5) Self-host web-vitals.js, log INP/LCP/CLS to a lightweight FastAPI endpoint, and adopt the budget INP<=200ms, LCP<=2.5s, CLS<=0.1 at p75 mobile as the merge gate for future UI work.

### Uncertain Fields (skipped)

- bundle_size_kb
- visual_examples
- baseline_status
- mobile_touch_behavior


---

## Micro-interactions and modern CSS animation

### Basic Info

**category**: animation

**description**: 

> A cluster of native web-platform features that deliver polished motion without any JS animation library: the View Transitions API (same-document via document.startViewTransition() for SPA-style state changes, and cross-document via the @view-transition CSS at-rule for animated page-to-page navigation in a classic MPA), scroll-driven animations (animation-timeline: scroll()/view() to tie keyframes to scroll position — reveal-on-scroll, progress bars, parallax), @starting-style + transition-behavior: allow-discrete (entry/exit transitions for elements appearing from display:none, including dialogs and popovers), and the CSS Overflow 5 carousel primitives (::scroll-button(), ::scroll-marker/::scroll-marker-group, and scroll-state() container queries) that produce fully functional, accessible carousels and snap-point UIs with zero JavaScript. Solves the problem of motion design historically requiring GSAP/Framer-Motion-class dependencies and heavy scroll listeners.

### Code

**license**: n/a — all are native browser features requiring no library.

**dependency_footprint**: 

> None. Pure CSS (scroll-driven animations, @starting-style, carousels, cross-document view transitions) or a few lines of vanilla JS (same-document startViewTransition wrapper). No script tag, no npm, no build step — ideal for a no-build vanilla-JS site. The only 'dependency' is feature-gating with @supports and if (document.startViewTransition).

**bundle_size_kb**: 

> 0 gzipped payload beyond your own CSS rules (typically <2 KB of CSS for all patterns combined). Main-thread cost is a key benefit: scroll-driven animations run compositor-side (unlike JS scroll listeners), view transitions are engine-managed snapshots; keep transitions to transform/opacity to stay off the main thread.

**ssr_htmx_compat**: 

> Very good, with one integration note. Cross-document view transitions are literally designed for server-rendered MPAs — FastAPI page navigations animate with CSS only. For htmx partial swaps, htmx 2.0 has built-in support: hx-swap="... transition:true" or the global htmx.config.globalViewTransitions = true wraps swaps in document.startViewTransition(). Scroll-driven animations, @starting-style, and carousel pseudo-elements are pure CSS and re-apply automatically to swapped-in HTML — no event re-binding, no web-component upgrade concerns. One caveat: view-transition-name values must be unique per page at snapshot time, so lists of cards need distinct names (e.g. inline style view-transition-name: card-42).

**maintenance_health**: 

> n/a (platform features; specs actively developed at CSSWG — View Transitions Level 2, CSS Overflow Level 5, Scroll-driven Animations in Interop 2026).

**integration_effort**: 

> low for @starting-style dialog/popover animation and scroll-reveal effects (pure additive CSS); low-medium for view transitions (cross-document is one at-rule + naming; wiring same-document transitions into the existing 133KB hand-rolled fetch/render code means wrapping each DOM-update entry point); medium for replacing any existing JS carousel with the CSS-only version while keeping a fallback for Firefox/Safari.

### Design

**key_techniques**: 

> 1) Cross-document view transitions (MPA): @view-transition { navigation: auto; } on both origin and destination pages; shared-element morphs via matching view-transition-name; customize with ::view-transition-group/old/new pseudo-elements; pair with Speculation Rules prerendering so the animated navigation is also instant. 2) Same-document: document.startViewTransition(cb) around DOM mutations; types via startViewTransition({update, types}) for direction-aware animation. 3) Scroll-driven: animation-timeline: view() (element's own visibility) or scroll() (container progress) with animation-range; classic uses — scroll progress bar (scaleX keyframe on scroll(root)), fade-and-rise card reveals, shrinking sticky header. 4) @starting-style for entry + transition-behavior: allow-discrete on display/overlay for exit — the pair that finally animates <dialog> and [popover] open/close in pure CSS. 5) CSS carousel kit: scroll-snap-type + scroll-marker-group generating focusable dot navigation (::scroll-marker, :target-current for the active dot), ::scroll-button(left/right) auto-disabled at scroll edges, scroll-state(snapped: x) container queries to style the snapped slide. 6) Always gate: @supports (animation-timeline: view()) { ... }, @supports (scroll-marker-group: after) { ... }, and @media (prefers-reduced-motion: no-preference) wrapping all of it.

**accessibility_notes**: 

> Motion must honor prefers-reduced-motion: wrap every animation-timeline, view-transition customization, and shimmer in @media (prefers-reduced-motion: no-preference); view transitions still occur logically but should reduce to a crossfade or nothing. The CSS carousel primitives are a major a11y win over hand-rolled carousels: ::scroll-button() and ::scroll-marker are browser-generated, keyboard-focusable, exposed with correct roles/states, and buttons auto-disable at scroll limits — but they still need author-provided accessible names (content: '' / attr() alternatives or aria-label via the originating element) and visible focus styles. Scroll-driven reveals must never hide content permanently for non-supporting browsers or reduced-motion users (start states belong inside the gated @supports/@media block, not on the base rule). During view transitions the old/new snapshots are non-interactive for a moment — keep durations under ~300ms so keyboard/AT users aren't blocked. Avoid parallax intensity that triggers vestibular disorders.

**wcag_mapping**: 

> 2.3.3 Animation from Interactions (AAA, the reduced-motion criterion — the main one to design for); 2.2.2 Pause Stop Hide (no auto-advancing carousel by default is a plus; if autoplay is added, provide pause); 2.1.1 Keyboard (native scroll buttons/markers keep carousels keyboard-operable, historically the top carousel failure); 2.4.3 Focus Order (view transitions must not strand focus — move focus to the new content region after same-document transitions); 4.1.2 Name Role Value (give scroll buttons/markers accessible names); 1.4.3/1.4.11 contrast for marker dots against the indigo palette; 2.4.11 Focus Not Obscured (sticky headers shrunk by scroll-driven animation must not cover focused elements).

**progressive_enhancement_fallback**: 

> Every feature has a clean built-in fallback: unsupported browsers get an instant page swap instead of a view transition (identical content), no scroll-linked motion (content simply visible, fully readable), dialogs/popovers that appear instantly instead of fading, and a plain horizontally scrollable snap list instead of buttons+dots (still swipeable on touch, which is the primary mobile gesture anyway). The discipline required: never put initial hidden/offset states outside the @supports/@media gates, and feature-detect startViewTransition before calling it.

### Applicability

**relevance_to_ensurecollege**: 

> The 'Highlighter' editorial brand needs motion that feels designed rather than bolted-on, and the site cannot afford a JS animation library on top of 133KB of hand-rolled code. Concrete wins: cross-document view transitions make landing -> matcher -> scholarship-detail navigation feel app-like on the FastAPI MPA for one at-rule, with an indigo-tinted crossfade matching the brand; a shared view-transition-name on the scholarship card title morphing into the detail-page heading is a signature micro-interaction. @starting-style animates the site's existing ARIA-labelled modals (convertible to <dialog>) opening/closing in pure CSS. Scroll-driven reveals give the landing page's social-proof and feature sections editorial polish, plus a reading-progress highlighter bar (on-brand) on guide pages. The CSS carousel primitives can drive a 'featured scholarships' or testimonial band with zero JS. All of it is deletable CSS — zero risk to the matcher logic.

**current_gap**: 

> The site has no view transitions (explicitly listed as missing), no scroll-driven animations, and modals/tabs that switch state instantly with no entry/exit motion. Any current motion lives in the 66KB hand-rolled CSS as basic transitions at most. There is no prefers-reduced-motion handling to audit against, and no carousel primitives in use. Page-to-page navigation is a hard cut, making the MPA feel dated next to app-like competitors.

**recommended_action**: 

> adopt — sequence: (1) Add @view-transition { navigation: auto; } plus a 250ms fade to all pages, and view-transition-name morphs on scholarship-card -> detail headings; feature-gate nothing (unsupported browsers just don't animate). (2) Wrap the existing fetch-driven DOM updates (matcher results render, tab switches) in a small helper: const vt = (fn) => document.startViewTransition ? document.startViewTransition(fn) : fn(); — one function, reused everywhere. (3) Convert modals to <dialog> with @starting-style fade/scale entry and allow-discrete exit. (4) Add @supports-gated scroll-driven card reveals and a scroll progress bar to landing/guide pages, all inside @media (prefers-reduced-motion: no-preference). (5) If a featured-scholarships band is wanted, build it as a scroll-snap list enhanced with ::scroll-marker dots and ::scroll-button arrows under @supports (scroll-marker-group: after). Skip nothing here except: don't adopt scroll-state() styling as anything load-bearing yet given its Limited availability.

### Uncertain Fields (skipped)

- adoption_maturity
- code_sources
- visual_examples
- baseline_status
- mobile_touch_behavior


---

## Modern CSS architecture primitives: container queries, :h...

### Basic Info

**category**: css-architecture

**description**: 

> Five native CSS capabilities that together replace what previously required preprocessors, JavaScript, or build tooling — the foundation of a modern no-build stylesheet architecture. (1) Container queries (@container + container-type + cqi/cqw units) let a component respond to the size of its container instead of the viewport, so the same card component works in a sidebar, a grid, or full-width without page-level media queries. (2) :has() is the 'parent/relational selector' — style an element based on its descendants or siblings (e.g. style a filter-chip label when its hidden checkbox is :checked, style a form field wrapper when its input is :invalid). (3) Native CSS nesting gives Sass-style nested rules (&:hover, nested @media/@container) with zero build step. (4) Cascade layers (@layer) impose explicit priority ordering (reset -> base -> components -> utilities), ending specificity wars in a growing hand-rolled stylesheet. (5) Subgrid lets nested grid items (card internals: image/title/meta/footer) align to the parent grid's tracks, solving the classic 'card contents don't line up across a row' problem. Together they determine how a no-build site implements cards, filter-chip state styling, and responsive layout.

**adoption_maturity**: 

> All five are cross-browser and in serious production use as of 2024-2026. In the State of CSS 2025 survey, :has() is both the most-used and most-loved recent feature; container queries and nesting show steep adoption curves. Shipped by every major design system that targets modern browsers (GitHub Primer, Open Props UI, Shoelace/Web Awesome internals use these). These are web-platform standards maintained by browser vendors, so there is no library-abandonment risk — adoption maturity is effectively 'permanent platform features'.

### Code

**code_sources**: 

> MDN reference docs with copy-paste examples: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment/Container_queries, https://developer.mozilla.org/en-US/docs/Web/CSS/:has, https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_nesting, https://developer.mozilla.org/en-US/docs/Web/CSS/@layer, https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid. web.dev deep dives: https://web.dev/blog/cq-stable (container queries), https://developer.chrome.com/blog/has-m105, https://developer.chrome.com/docs/css-ui/css-nesting, https://developer.chrome.com/docs/css-ui/cascade-layers. Practical patterns: Ahmad Shadeed's interactive guides https://ishadeed.com/article/css-container-query-guide/ and https://ishadeed.com/article/css-has-guide/; Miriam Suzanne (spec co-author) on layers https://css-tricks.com/css-cascade-layers/. Baseline status checks: https://web.dev/baseline and https://caniuse.com. All examples are plain CSS — directly usable in a hand-rolled stylesheet.

**license**: n/a — native web-platform features, no library involved.

**dependency_footprint**: 

> None. Pure CSS, no script tag, no npm, no build step. This is precisely their value for a no-build vanilla-JS site: they deliver what Sass (nesting), BEM discipline (layers), JS resize observers (container queries), and JS class-toggling (much of :has()) used to require.

**bundle_size_kb**: 

> 0. Pure CSS syntax. Using nesting and layers typically shrinks a stylesheet (less selector repetition). No main-thread cost; container queries and :has() are handled by the browser's style engine (a very broad :has() usage, e.g. body:has(*), can add style-recalc cost — scope selectors sensibly).

**ssr_htmx_compat**: 

> Perfect. Stylesheets apply to whatever HTML is in the document, so server-rendered pages and HTMX/fetch partial swaps restyle automatically with no re-binding, no hydration, no re-upgrade step. :has()-driven state styling (e.g. checked filter chips) keeps working on swapped-in content instantly — a major advantage over JS-added state classes, which must be re-applied after every swap.

**maintenance_health**: 

> n/a — browser-native. Maintained by Chrome/Firefox/Safari engine teams under W3C specs; interoperability actively tracked by the yearly Interop project.

**integration_effort**: 

> low to medium for an existing FastAPI + vanilla-JS site. Nesting and :has(): low — adopt incrementally in the existing 66KB stylesheet, one component at a time. Cascade layers: medium — worth a one-time reorganization (wrap existing CSS into @layer base, components, utilities; un-layered styles beat layered ones, which is a migration gotcha). Container queries: low per component (add container-type to card-grid wrappers). Subgrid: low, applied only where card-row alignment matters.

### Design

**key_techniques**: 

> Container queries (card that adapts to its slot): `.results { container-type: inline-size; container-name: results; } .card { display:grid; gap:.5rem; } @container results (min-width: 28rem) { .card { grid-template-columns: 6rem 1fr; } }` — plus container units: `font-size: clamp(1rem, 3cqi, 1.4rem);`. :has() filter-chip state (no JS): `label.chip:has(input:checked) { background: var(--indigo-600); color:#fff; }` and form UX: `.field:has(input:user-invalid) { border-color: var(--error); } .field:has(input:focus-visible) { outline: 2px solid var(--indigo-500); }` and layout switching: `.results:has(.card:nth-child(n+7)) { /* dense layout when 7+ results */ }`. Native nesting: `.card { border:1px solid var(--line); &:hover { box-shadow: var(--shadow-2); } & h3 { font-size: var(--step-1); } @container results (min-width:28rem) { grid-template-columns:6rem 1fr; } }`. Cascade layers: `@layer reset, base, components, utilities;` declared first, then `@layer components { .card { ... } }` — later layers win regardless of specificity; `@import url(pico.css) layer(base);` slots third-party CSS beneath your own. Subgrid (aligned card internals): `.grid { display:grid; grid-template-columns:repeat(3,1fr); } .card { display:grid; grid-row: span 3; grid-template-rows: subgrid; }` so title/meta/footer rows align across all cards in a row.

**visual_examples**: 

> Ahmad Shadeed's interactive articles (ishadeed.com) visually demonstrate container queries and :has() with live resizable demos. https://scroll-driven-animations.style-style sibling site https://has.style-like demos aside, the clearest galleries are web.dev/articles for each feature and Kevin Powell's YouTube walkthroughs. Real-world: GitHub's feed cards (container queries), many 2024+ marketing sites use :has() for menu/theme state. 12daysofweb.dev and Smashing Magazine 2024-2025 articles include live CodePens for every primitive.

**accessibility_notes**: 

> These primitives are a11y-neutral to a11y-positive. :has() enables styling real native controls (checkbox/radio inside a label) instead of ARIA-faked divs — keeping filter chips as genuine form controls preserves keyboard and screen-reader semantics for free. Container queries encourage components that reflow rather than truncate at small sizes (helps 1.4.10 Reflow and 1.4.4 Resize Text). Pitfalls: :has(input:checked) styling must keep a visible focus indicator on the label since the input is usually visually hidden (use :has(input:focus-visible)); don't hide content with container queries in ways that remove it from the accessibility tree unexpectedly; keep DOM order logical regardless of grid placement.

**wcag_mapping**: 

> Supports: 1.4.10 Reflow (container-responsive components at 320px), 1.4.4 Resize Text (cqi/rem-based sizing), 2.4.7 Focus Visible and 2.4.13 Focus Appearance (:has(:focus-visible) makes rich focus styling on wrappers trivial), 3.3.1 Error Identification (:has(:user-invalid) wrapper styling), 1.3.1 Info and Relationships (native checkboxes for chips keep programmatic state, aria-pressed not needed). Risks: none inherent; subgrid/dense grids can create visual-vs-DOM order mismatches (1.3.2 Meaningful Sequence) if abused.

**progressive_enhancement_fallback**: 

> Container queries: without support the component keeps its base (mobile/stacked) styles — content fully usable. :has(): unsupported browsers skip the rule — chips still function as real checkboxes, just without the enhanced selected styling, so pair it with a minimal JS class-toggle fallback only if pre-2023 browsers matter. Nesting: this is the one hard cliff — an unsupporting browser drops nested rules entirely, so either flatten critical styles or accept that only evergreen browsers are served (reasonable in 2026). Cascade layers: unsupported browsers ignore @layer blocks entirely (styles lost), but support is universal enough that this is theoretical. Subgrid: falls back to normal nested grid — cards work, internal rows just don't align across the row (purely cosmetic).

**mobile_touch_behavior**: 

> Container queries are the single best tool for a mobile-heavy student audience: cards adapt to their actual slot, so the matcher results look right whether in a single column on a phone or a 3-up grid on a laptop, without maintaining parallel media queries. :has()-styled native checkboxes keep the OS's built-in touch behavior (label tap targets — make the whole chip the label, >=44px). cqi-based type keeps card text proportional in narrow columns. No virtual-keyboard or sticky-header interactions to worry about; these are style-engine features with no scroll/touch side effects.

### Applicability

**relevance_to_ensurecollege**: 

> This is the architecture layer for everything else the site wants to do, and it costs zero bytes. Concretely: (1) Filter chips on the scholarship/program/competition matchers can be pure HTML checkboxes styled with label:has(input:checked) — removing the JS currently needed to toggle .active classes, and surviving any future HTMX-style partial updates for free; (2) result cards become container-query components, so the same card markup works on the dashboard, in matcher results, and in any future sidebar without new breakpoint CSS — directly attacking the 66KB hand-rolled CSS by deleting duplicated viewport media queries; (3) wrapping the existing stylesheet in cascade layers (reset, base, components, utilities) makes the indigo 'Highlighter' brand overrides predictable and lets any future drop-in CSS (e.g. Pico) be imported into a low-priority layer beneath brand styles; (4) native nesting keeps the hand-rolled stylesheet maintainable without ever introducing Sass or a build step, which matches the FastAPI + vanilla-JS no-build constraint exactly; (5) subgrid fixes ragged scholarship-card rows (title/deadline/amount aligned across a row) — a subtle mark of a professionally built site.

**current_gap**: 

> The current 66KB CSS predates these primitives: it presumably uses viewport media queries only (no container queries), JS class-toggling for interactive state (part of the 133KB JS), no @layer organization (specificity managed by convention), no nesting (flat, repetitive selectors), and no subgrid alignment on card grids. No dark mode also means no layered theming structure to hook into yet.

**recommended_action**: 

> adopt. Phase 1 (one sitting, zero risk): declare `@layer reset, base, components, utilities;` at the top of the stylesheet and progressively move existing rules into layers, flattening specificity hacks as you go. Phase 2: convert matcher filter chips to `<label class=chip><input type=checkbox hidden-visually>` + `:has(input:checked)` styling, deleting the equivalent JS toggle code; keep a 2-line JS fallback (toggle a class on change) only if analytics show pre-2024 browsers. Phase 3: add `container-type: inline-size` to the results wrapper and rewrite card breakpoints as @container rules; use subgrid on the results grid so card metadata rows align. Adopt nesting for all new CSS immediately. Net effect: less CSS, less JS, more robust responsive behavior — the highest leverage/effort ratio of any item in this research set.

### Uncertain Fields (skipped)

- baseline_status


---

## Native HTML interactive primitives

### Basic Info

**category**: native-primitives

**description**: 

> A cluster of browser-managed interactive components that ship with HTML/CSS and need zero JavaScript: the Popover API (popover attribute + popovertarget), Invoker Commands (command/commandfor on <button>), the <dialog> element for modals, exclusive accordions (<details name='group'>), customizable <select> (appearance: base-select with <selectedcontent>), field-sizing: content for auto-growing textareas/inputs, and accent-color for theming native checkboxes/radios/range/progress. Together they solve the problem that used to require hand-rolled ARIA JavaScript widgets: focus trapping, Escape-to-close, light-dismiss, top-layer stacking above all z-index contexts, mutually-exclusive disclosure, and styled form controls. The browser manages state, keyboard interaction, and accessibility semantics, eliminating whole categories of a11y bugs and shrinking JS payloads.

**adoption_maturity**: 

> Rapidly mainstreaming across 2024-2026. <dialog> and accent-color are Baseline Widely available and used in production by GitHub, and countless design systems. The Popover API reached Baseline Newly available in January 2025 and is used by GitHub's primer and Shopify. Exclusive accordions (details name) hit Baseline September 2024. Invoker Commands reached full cross-browser Baseline with Safari 26.2 in December 2025 (Chrome 135, Firefox 144). field-sizing completed Baseline in June 2026 with Firefox 152. Customizable <select> is the laggard: Chrome 135+ only, Safari 27 announced, Firefox prototyping behind a flag - production sites use it only as progressive enhancement via @supports. OpenUI community group (browser vendors + framework authors) drives this work, and the direction of travel is unambiguous: native primitives are replacing JS widget libraries.

### Code

**code_sources**: 

> MDN Popover API: https://developer.mozilla.org/en-US/docs/Web/API/Popover_API ; MDN Invoker Commands: https://developer.mozilla.org/en-US/docs/Web/API/Invoker_Commands_API ; MDN <dialog>: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog ; Chrome customizable select guide with full copy-paste CSS: https://developer.chrome.com/blog/a-customizable-select ; WebKit customizable select: https://webkit.org/blog/18117/the-golden-rule-of-customizable-select/ ; Exclusive accordion: https://developer.chrome.com/docs/css-ui/exclusive-accordion ; field-sizing use cases with demos: https://ishadeed.com/article/field-sizing/ ; Open UI explainers: https://open-ui.org/ ; CSS-Tricks invoker commands: https://css-tricks.com/invoker-commands-additional-ways-to-work-with-dialog-popover-and-more/ . All examples are plain HTML/CSS, e.g. <button popovertarget="menu">Menu</button><div id="menu" popover>...</div> and <button commandfor="dlg" command="show-modal">Open</button><dialog id="dlg">...</dialog>

**license**: n/a

**dependency_footprint**: 

> None - pure HTML/CSS platform features. No script tag, no npm, no build step. Fully compatible with a no-build vanilla-JS site; this is the ideal case. Optional tiny JS only for enhancement (e.g. closing a popover after a menu action, form handling on dialog close event).

**bundle_size_kb**: 0

**ssr_htmx_compat**: 

> Excellent - these are declarative HTML attributes, so server-rendered markup works immediately with no hydration or upgrade step. HTMX/fetch partial swaps that insert <dialog>, [popover], <details name>, or command buttons work without re-binding because the browser wires behavior from attributes, not from JS event listeners. One caveat: a dialog opened via JS (showModal()) that gets swapped out mid-open simply disappears; and popovers open at swap time are closed when their DOM node is replaced - both are graceful failures, not breakage.

**maintenance_health**: 

> n/a (browser platform features, maintained by Chrome/Firefox/WebKit teams and specified at WHATWG/CSSWG via Open UI)

**integration_effort**: 

> low - replace existing modal/accordion JS with attributes; customizable select is low-effort too when layered behind @supports (appearance: base-select)

### Design

**key_techniques**: 

> 1) Popover: <div id="tip" popover> + <button popovertarget="tip">, top-layer rendering, light-dismiss with popover="auto", styling via ::backdrop and :popover-open. 2) Invoker Commands: <button commandfor="myDialog" command="show-modal"> (also close, request-close, toggle-popover, show-popover, hide-popover, and custom --commands via the 'command' event) - declarative replacement for click handlers. 3) <dialog>: dlg.showModal() or command="show-modal", ::backdrop, built-in focus trap, Escape close, form method="dialog" for zero-JS close buttons, closedby="any" attribute for light-dismiss. 4) Exclusive accordion: <details name="faq"> - same name = only one open at a time; style with details::details-content and interpolate-size: allow-keywords for height animation. 5) Customizable select: select, ::picker(select) { appearance: base-select } then style ::picker(select), option, option::checkmark, selectedcontent - full CSS control incl. rich HTML in options. 6) field-sizing: content on textarea/input - auto-grows with typed content, capped with min/max-height. 7) accent-color: indigo (or a brand hex) on :root recolors checkboxes, radios, range sliders, progress bars in one line while keeping native a11y and forced-colors behavior.

**visual_examples**: 

> Open UI demo pages (https://open-ui.org/components/customizableselect/), Chrome DevRel demos on developer.chrome.com (customizable select gallery, exclusive accordion), MDN Popover API live examples, https://nerdy.dev/nice-select (Adam Argyle's styled base-select demo, Feb 2026), Ahmad Shadeed's field-sizing interactive article (ishadeed.com/article/field-sizing), popover.study and Una Kravets' popover demos on codepen.io/web-dot-dev

**accessibility_notes**: 

> These primitives bake in the semantics that hand-rolled widgets get wrong: <dialog> provides role=dialog, aria-modal, focus trapping, focus restore on close, and Escape handling automatically (still set an accessible name via aria-labelledby and manage initial focus with autofocus). Popover wires aria-expanded and aria-details on the invoker automatically. Exclusive <details> keeps content discoverable by find-in-page and exposes expanded state natively. Customizable select keeps the real <select> semantics for screen readers and keeps the OS-native picker on touch devices. accent-color preserves contrast adjustments the browser makes. Pitfalls: do not use popover=manual without providing a close affordance; do not nest interactive content inside <summary>; rich HTML inside customizable <option> must be limited to non-interactive content (the 'golden rule' - WebKit strips interactivity for a11y); field-sizing needs a max-height so a long answer does not push controls off-screen.

**wcag_mapping**: 

> Directly helps satisfy 2.1.2 No Keyboard Trap and 2.4.3 Focus Order (dialog's managed focus), 1.4.13 Content on Hover or Focus (popover light-dismiss + Escape), 4.1.2 Name Role Value (native roles/states instead of hand-maintained ARIA), 2.4.11 Focus Not Obscured Minimum (top layer means focused dialogs/popovers cannot be covered by sticky headers), 2.5.8 Target Size Minimum (native option/summary hit areas), 1.4.3 Contrast (accent-color: browser auto-adjusts the checkmark/foreground). Risks: styling ::picker(select) or option with insufficient contrast can break 1.4.3/1.4.11; removing focus outlines on summary/button breaks 2.4.7 Focus Visible.

**baseline_status**: 

> <dialog>: Baseline Widely available. accent-color: Baseline Widely available (newly available March 2022). Popover API: Baseline Newly available January 2025. Exclusive accordion (details name): Baseline Newly available September 2024. Invoker Commands (command/commandfor): Baseline Newly available December 2025 (Chrome 135, Firefox 144, Safari 26.2). field-sizing: Baseline Newly available June 2026 (Chrome 123, Safari 26.2, Firefox 152). Customizable select (appearance: base-select): Limited availability - Chromium 135+ only as of mid-2026, Safari 27 announced, Firefox behind a flag.

**progressive_enhancement_fallback**: 

> All degrade gracefully. Unsupported popover attribute: content renders inline (hide it with [popover]{display:none} fallback or feature-detect). Unsupported command/commandfor: button does nothing - keep popovertarget or a small JS fallback for older Safari/Firefox (pre-Dec-2025). <details name>: older browsers just allow multiple panels open - still fully functional. Customizable select: browsers ignore appearance:base-select and render the classic native select - the canonical progressive enhancement, gate custom CSS behind @supports (appearance: base-select). field-sizing: fixed-size textarea with scrollbar. accent-color: default blue controls. Nothing breaks; users only lose polish.

**mobile_touch_behavior**: 

> Strong story for a mobile-heavy student audience. <dialog> and popover render in the top layer so they are never trapped under sticky headers; pair with max-block-size: 90dvh and overflow:auto so the virtual keyboard does not hide inputs. Customizable select intentionally keeps the OS-native wheel/sheet picker on iOS/Android touch interaction (base-select styles the button, browsers may keep native pickers on touch) - a feature, since native pickers beat custom dropdowns for thumb reach. field-sizing:content prevents the tiny-scrolling-textarea problem when students type essays on phones. Exclusive accordions give large tap targets via <summary>; add padding for 44px targets. Popover light-dismiss works with tap-outside naturally.

### Applicability

**relevance_to_ensurecollege**: 

> This is the highest-leverage cluster for EnsureCollege. The site is FastAPI + vanilla JS with hand-rolled ARIA modals and tabs inside 133KB of JS - dialogs for auth, scholarship detail views, and confirmation flows can move to <dialog> + invoker commands and delete the focus-trap/Escape/overlay code entirely. FAQ and eligibility-criteria sections become <details name> exclusive accordions with zero JS. Filter dropdowns and sort menus on the scholarship/program/competition matchers become popovers. The matchers' many <select> filters (state, major, grade level) can adopt base-select styling behind @supports to match the indigo 'Highlighter' brand while keeping native mobile pickers. accent-color: indigo is a one-line win that brands every checkbox/radio in the eligibility forms. field-sizing improves essay/short-answer inputs in profile forms. Net effect: less JS to maintain, better mobile behavior, and accessibility guarantees that matter as scholarship sites serve students who may rely on assistive tech.

**current_gap**: 

> The site currently hand-rolls modals and tabs with ARIA attributes and custom JS (part of the 133KB vanilla JS), uses default-styled form controls with no accent-color, has no top-layer usage (custom overlays with z-index), no exclusive accordions, fixed-height textareas, and default <select> elements. None of the Baseline 2024-2026 primitives are in use, so the site pays a JS maintenance cost for behavior the browser now provides free.

**recommended_action**: 

> adopt - Migrate in three passes. Pass 1 (one afternoon, zero risk): add accent-color: var(--indigo) to :root; convert FAQ/eligibility sections to <details name> accordions; add field-sizing: content with a max-height to textareas. Pass 2: replace every custom modal with <dialog> - open via commandfor/command="show-modal" with a popovertarget/tiny-JS fallback for pre-2026 browsers, close via <form method="dialog">, style ::backdrop with the indigo brand at low opacity; delete the old focus-trap and scroll-lock JS. Pass 3: convert filter/sort menus on the matcher pages to popover="auto" panels, and layer @supports (appearance: base-select) styling onto matcher <select> filters so supporting browsers get branded dropdowns while everyone else keeps the reliable native control. Skip nothing in this cluster except treating base-select as required - it must stay enhancement-only until Safari 27 and Firefox ship.


---

## Navigation patterns (sticky headers, framework-free mobil...

### Basic Info

**category**: navigation

**description**: 

> The trio of navigation patterns a content-plus-tools site needs: (1) a sticky/condensing header that keeps primary nav and auth actions reachable during long scrolls without eating mobile viewport; (2) a mobile navigation menu (hamburger/disclosure or full-screen sheet) built with native platform primitives — the popover attribute, <dialog>, or <details> — instead of a JS framework; (3) breadcrumbs that orient users inside hierarchies (Home > Scholarships > STEM > Result) with proper semantics and structured data. Together they solve wayfinding and reachability on a site whose student users arrive deep-linked from search and social.

**adoption_maturity**: 

> Sticky headers and breadcrumbs are universal, decade-plus mature patterns (position:sticky Baseline Widely available for years). Framework-free mobile nav is the part that modernized recently: the popover attribute became Baseline Newly available (all engines) around January 2025 and is increasingly the recommended light-dismiss menu primitive; <dialog> is Widely available; <details>-based disclosure nav is long-stable. Production adoption of popover-based nav is growing fast through 2025-2026 (documented by web.dev, Chrome DevRel, CSS-Tricks) though many sites still ship hand-rolled button+aria-expanded menus, which remain perfectly valid.

### Code

**license**: 

> n/a (platform features and W3C/MDN example code; W3C samples are permissively licensed, GOV.UK breadcrumb markup MIT)

**dependency_footprint**: 

> None. Sticky header is pure CSS; breadcrumbs are pure HTML/CSS (+ optional JSON-LD script tag); mobile nav needs either zero JS (popover attribute's declarative popovertarget button, or <details>) or ~20-40 lines of vanilla JS for the classic button+aria-expanded version and scroll-direction header condensing. Fully compatible with the no-build FastAPI + vanilla-JS site.

**bundle_size_kb**: 0 for CSS/HTML; <1 KB gzipped of hand-written JS for scroll-condensing and menu fallback wiring

**ssr_htmx_compat**: 

> Excellent. All three are plain server-rendered HTML. The header/nav typically lives outside HTMX swap targets, so no re-binding needed; if a partial swap replaces the breadcrumb, it is inert HTML anyway. popover/popovertarget and <details> behavior is native and survives any innerHTML swap without JS re-initialization — a concrete advantage over framework menu components. Only caveat: a JS-driven aria-expanded menu needs delegated listeners if the header itself is ever swapped.

**maintenance_health**: n/a (browser platform features maintained by vendors; WHATWG/CSSWG specs)

**integration_effort**: 

> low — each of the three pieces is an afternoon-sized change to existing templates and the 66KB stylesheet

### Design

**key_techniques**: 

> Sticky header: `header { position: sticky; top: 0; z-index: 10; }` plus `:target, h2[id], [tabindex="-1"] { scroll-margin-top: var(--header-h); }` so anchors and focus targets are not hidden under it (this line is the WCAG 2.4.11 fix). Condense on scroll: toggle a .shrunk class from a scroll-direction listener (~15 lines, rAF-throttled), or CSS-only with `animation-timeline: scroll()` where supported. Mobile nav, three native options: (a) popover: `<button popovertarget="menu">Menu</button> <nav id="menu" popover>…</nav>` — zero JS, light-dismiss, Esc to close, top layer; style entry with `@starting-style` transitions; (b) `<dialog>` + showModal() for a full-screen sheet with built-in focus trap and inert background; (c) `<details class="nav-disclosure"><summary>Menu</summary><nav>…</nav></details>` — works everywhere, needs CSS only. Classic fallback: `<button aria-expanded="false" aria-controls="nav">` toggling a hidden attribute. Breadcrumbs: `<nav aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/scholarships">Scholarships</a></li><li><a href="…" aria-current="page">STEM Grants</a></li></ol></nav>` with CSS `li + li::before { content: "/" }` separators (decorative, not in DOM text order as characters that screen readers announce awkwardly — content via CSS is skipped by most SRs); add BreadcrumbList JSON-LD for rich results.

**visual_examples**: 

> GOV.UK (breadcrumbs + non-sticky minimal header as a restraint reference); Stripe docs and MDN (condensing sticky headers); The Verge / editorial sites for brand-forward sticky headers matching the Highlighter editorial vibe; web.dev's own popover-based mobile menu; BigFuture (collegeboard.org) sticky header + breadcrumb combo aimed at the same students; https://scroll-driven-animations.style demos for CSS-only header effects.

**accessibility_notes**: 

> Sticky headers are the top cause of WCAG 2.4.11 Focus Not Obscured failures — every focusable element and skip-link target needs scroll-margin-top/scroll-padding; test by tabbing through a long page. Keep a 'skip to main content' link as first focusable item. Mobile menu: the trigger must be a real <button> with an accessible name ('Menu', not a bare icon), state exposed via aria-expanded (or natively via popover/details); full-screen menus must trap focus (<dialog> gives this free; popover does not trap — acceptable for light-dismiss menus but pick <dialog> if the menu fully covers content); Esc must close and focus must return to the trigger (native for dialog/popover). Breadcrumbs: nav landmark with aria-label="Breadcrumb", ordered list, aria-current="page" on the last item; separators via CSS so they are not announced. Respect prefers-reduced-motion on header shrink/menu animations.

**wcag_mapping**: 

> Directly implicates: 2.4.11 Focus Not Obscured (Minimum) — sticky header must not cover the focused element (scroll-margin fix); 2.4.1 Bypass Blocks (skip link); 2.4.8 Location (breadcrumbs are the canonical technique, AAA but cheap); 1.3.1 Info and Relationships (nav/ol semantics, aria-current); 2.1.2 No Keyboard Trap (menu close behavior); 2.5.8 Target Size Minimum (44px hamburger and nav links on touch); 2.3.3/2.2.2 motion — reduced-motion on animated header. 4.1.2 Name/Role/Value on the menu toggle.

**progressive_enhancement_fallback**: 

> Sticky header degrades to a normal static header (position:sticky unsupported is ignored). popover-based menu in an old browser: feature-detect and fall back to the aria-expanded/hidden toggle, or simply render nav links inline (server-rendered nav list is visible when JS and popover are both unavailable — never hide the nav with CSS that only JS can undo). <details> menu needs nothing. Breadcrumbs are inert HTML. Scroll-driven header animation falls back to the JS scroll listener or to a permanently full-height header.

**mobile_touch_behavior**: 

> Budget the sticky header strictly (<= ~56px, or shrink after scroll) — on a 667px-tall phone a fat sticky header plus the virtual keyboard leaves almost no form visible, which matters on the matcher forms; consider unsticking the header while any input is focused. Hamburger button >= 44x44px in the top corner; menu as full-screen sheet with large tap targets and the primary CTA (Sign in / My matches) first. Breadcrumbs on mobile: allow horizontal scroll or collapse middle items to '…' rather than wrapping to three lines; alternatively show only the parent as a back-style link. Light-dismiss (tap outside) via popover matches native app expectations.

### Applicability

**relevance_to_ensurecollege**: 

> Students land deep on scholarship/program detail pages from Google and TikTok/Discord shares; breadcrumbs (+ BreadcrumbList JSON-LD, which also earns breadcrumb rich results in Google) orient them and pull them up into the matchers. A slim sticky header keeps 'My matches' and auth one tap away during long results lists and editorial content, supporting conversion. Native-primitive mobile nav fits the site's no-framework philosophy, costs ~0 KB against the existing 133KB JS, and survives fetch-based partial updates without re-initialization. The header is also prime real estate for the Highlighter brand treatment (e.g. highlighter-swipe underline on the active nav item via CSS).

**current_gap**: 

> Current site header behavior and breadcrumbs are absent or minimal: no breadcrumb trail on detail pages (and no BreadcrumbList structured data), header is not sticky (or is sticky without scroll-margin compensation — needs an audit against 2.4.11), and the mobile menu is hand-rolled JS rather than popover/dialog, without a documented no-JS fallback. No skip-link verification against a sticky header has been done.

**recommended_action**: 

> adopt — Three small, independent changes: (1) make the header position:sticky at <=56px height with a site-wide `scroll-margin-top` rule and verified skip link, adding a 10-line scroll-direction shrink only if the brand wants it; (2) rebuild the mobile menu on the popover attribute with a feature-detect fallback to the existing aria-expanded toggle (net JS deletion), full-screen sheet styling, 44px targets, and prefers-reduced-motion guards; (3) add a breadcrumbs Jinja macro (nav>ol, aria-current, CSS separators) to scholarship/program/competition detail and category pages plus BreadcrumbList JSON-LD for SEO. Total effort roughly one to two days and it removes hand-rolled JS rather than adding any.

### Uncertain Fields (skipped)

- code_sources
- baseline_status


---

## Vanilla-JS component libraries (Web Awesome / Shoelace an...

### Basic Info

**category**: component-library

**description**: 

> Framework-agnostic web-component libraries usable from a plain <script> tag without React or a build step. Flagship: Web Awesome (shoelace-style/webawesome), the 3.0 successor to Shoelace from Font Awesome - 50+ components (buttons, dialogs, drawers, selects, tooltips, tabs, cards, badges, spinners, form controls) as custom elements (<wa-button>, <wa-dialog>) with a new theming API and CSS custom properties. Peers include SAP UI5 Web Components, Vaadin Web Components, Wired Elements (sketchy style), and Google's Material Web (@material/web, now in maintenance mode). They solve the problem of getting polished, accessible, themeable components on a no-build vanilla-JS site where React-only libraries (shadcn/Radix, MUI) are unusable.

**adoption_maturity**: 

> Shoelace was the most popular independent web-component library (~13k GitHub stars) and is used in production widely; its creator Cory LaViska joined Font Awesome in 2022. Web Awesome ran a $737k Kickstarter (2024), went public beta early 2025, and shipped stable 3.0 on October 28, 2025; the Shoelace repo was archived May 14, 2026, making Web Awesome the sole successor. Active release cadence (v3.10.0, June 30, 2026). Free tier is MIT open source; a paid Pro tier funds development (Font Awesome's proven model). UI5 and Vaadin components are enterprise-backed and stable. Material Web halted new development in 2024 - avoid for new projects.

### Code

**code_sources**: 

> Web Awesome repo: https://github.com/shoelace-style/webawesome ; docs with copy-paste examples for every component: https://webawesome.com/docs/components/ ; CDN autoloader (no build): <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@awesome.me/webawesome@3/dist/styles/webawesome.css"> + <script type="module" src="https://cdn.jsdelivr.net/npm/@awesome.me/webawesome@3/dist/webawesome.loader.js"></script> then use <wa-button variant="brand">Save</wa-button>. Legacy Shoelace (archived, still on CDN): https://github.com/shoelace-style/shoelace and https://shoelace.style . Peers: https://github.com/SAP/ui5-webcomponents , https://github.com/vaadin/web-components , https://github.com/rough-stuff/wired-elements

**license**: 

> MIT (Web Awesome Free / Shoelace); Apache-2.0 (UI5 Web Components, Vaadin core components); Pro tier of Web Awesome is commercial

**dependency_footprint**: 

> A script tag is enough: Web Awesome ships an autoloader that watches the DOM and lazy-loads only the component modules actually used, from a CDN, as ES modules. No npm, no bundler, no framework required (built on Lit internally but that is bundled). Fully compatible with a no-build vanilla-JS FastAPI site. Optional npm install + cherry-picked imports for those who later add a bundler.

**ssr_htmx_compat**: 

> Good and explicitly a design goal: Web Awesome is advertised as ~98% SSR-compatible, with components able to render via Declarative Shadow DOM for server rendering. Crucially for HTMX/fetch partial swaps: custom elements auto-upgrade whenever their tag is inserted into the DOM (the autoloader observes mutations), so swapped-in <wa-*> markup just works with no re-binding - a major advantage over jQuery-style widget libraries. Caveats: FOUC before upgrade (mitigate with :not(:defined){visibility:hidden} or the provided preloading pattern), and form-associated custom elements participate in native <form> submission so FastAPI form posts work.

**maintenance_health**: 

> Web Awesome: very healthy - stable 3.0 Oct 2025, latest v3.10.0 June 30, 2026, backed by Font Awesome's commercial revenue and a dedicated team (Cory LaViska + Konnor Rogers et al.). Shoelace: archived May 14, 2026, succeeded by Web Awesome (clean migration path, mostly renaming sl- to wa- plus theming changes). Material Web: maintenance mode since mid-2024, not recommended. UI5/Vaadin: corporate-maintained, active.

**integration_effort**: 

> low - two CDN tags, then replace HTML; medium if migrating existing hand-rolled components and matching the Highlighter brand via the theming API

### Design

**key_techniques**: 

> Custom elements + Shadow DOM (style encapsulation - page CSS cannot leak in; theme via CSS custom properties and ::part() selectors). Web Awesome theming API: design tokens as --wa-color-brand-*, --wa-font-*, --wa-space-* custom properties; set them once on :root to rebrand every component (e.g. :root { --wa-color-brand-fill-loud: #4f46e5; }). Autoloader pattern: MutationObserver + dynamic import() per undefined tag. Slots for composition: <wa-dialog label="Filters"><p>...</p><wa-button slot="footer">Apply</wa-button></wa-dialog>. Form-associated custom elements (ElementInternals) so <wa-input>/<wa-select> submit with native forms and support constraint validation. Events use wa- prefixed CustomEvents (wa-show, wa-hide, wa-change) - bind with addEventListener as usual.

**visual_examples**: 

> https://webawesome.com (themed demos, theme builder) ; https://webawesome.com/docs/components/ live playground per component ; legacy https://shoelace.style demos ; https://wiredjs.com for Wired Elements' hand-drawn aesthetic ; SAP UI5 samples at https://sap.github.io/ui5-webcomponents/

**accessibility_notes**: 

> Web Awesome 3.0 touts improved accessibility as a headline feature: components ship with correct roles, keyboard interaction, and focus management (dialog focus trap, roving tabindex in menus/tabs, aria-live in toasts). Because semantics live inside the shadow DOM, you cannot accidentally break them - but you must still supply accessible names via label attributes/slots (e.g. <wa-icon-button label="Close">). Pitfalls: shadow DOM can complicate cross-root ARIA references (aria-labelledby across shadow boundaries does not work - use the provided label props); verify color-contrast after retheming brand tokens; test one or two key flows with a screen reader since library a11y claims still need verification in context.

**wcag_mapping**: 

> Satisfies out of the box: 4.1.2 Name Role Value (proper roles/states in components), 2.1.1 Keyboard (all components keyboard-operable), 2.1.2 No Keyboard Trap (dialog/drawer focus management), 2.4.7 Focus Visible (visible focus rings themed via tokens), 1.4.13 Content on Hover or Focus (tooltip dismiss/hover behavior). Risks to manage yourself: 1.4.3 Contrast Minimum and 1.4.11 Non-text Contrast when overriding brand tokens with the indigo palette; 3.3.2 Labels or Instructions (you must pass labels); 2.5.8 Target Size if you shrink size tokens.

**baseline_status**: 

> The underlying platform features are Baseline Widely available: Custom Elements, Shadow DOM, ES modules, constructable stylesheets, ElementInternals/form-associated custom elements. Declarative Shadow DOM (used for SSR) is Baseline Newly available since ~August 2024 (Firefox 123, Safari 16.4, Chrome 90). So the library runs on every current browser; the library itself is not a platform feature so Baseline applies only to its substrate.

**progressive_enhancement_fallback**: 

> If the script fails or JS is off, undefined custom elements render as inert inline elements: slotted text content is still visible (a <wa-button>Save</wa-button> shows 'Save' as plain text) but controls are not interactive - so keep native <form>/<a>/<button> for critical paths (auth, applying to a scholarship) and use library components for enhancement-level UI (dialogs, tooltips, toasts, tabs). SSR with Declarative Shadow DOM improves no-JS rendering of structure/styles but interactivity still requires the JS.

**mobile_touch_behavior**: 

> Components are responsive and touch-tested: wa-drawer gives a mobile-friendly slide-in filter panel pattern, wa-dialog handles small viewports (scrollable body), select/dropdown components use proper touch targets and reposition with Floating-UI-style logic to avoid keyboard/viewport clipping. Size tokens let you enforce 44px+ touch targets globally. Watch: custom selects on touch are not the OS-native picker (unlike native <select>), which some mobile users find worse - consider keeping native <select> for the matcher filters and using the library elsewhere.

### Applicability

**relevance_to_ensurecollege**: 

> EnsureCollege is exactly the target user: a FastAPI + vanilla-JS no-build site that needs polished dialogs, drawers, toasts, tabs, tooltips, and form controls without adopting React. Web Awesome could replace much of the hand-rolled 66KB CSS component styling and the modal/tab JS with maintained, accessible components, restyled to the indigo 'Highlighter' editorial brand through the token API in one :root block. HTMX-style partial swaps of matcher results keep working because custom elements auto-upgrade. Drawer = mobile filter panel for the scholarship matcher; wa-toast/callout = save-confirmation and deadline alerts; wa-tab-group = program/competition tabs; wa-skeleton = the loading skeletons the site currently lacks. Its theming API also has built-in light/dark color schemes that can plug into the site's existing token-based dark theme.

**current_gap**: 

> The site uses zero component libraries: all modals, tabs, dropdowns, and cards are hand-rolled (66KB CSS + 133KB JS), with no skeletons, no toasts, no drawer pattern, and a growing maintenance burden. It does have a token-based dark theme with a manual toggle (no prefers-color-scheme sync), which would need mapping onto Web Awesome's theme tokens. Nothing on the site auto-upgrades after fetch swaps; event re-binding is manual.

**recommended_action**: 

> adapt - Do not do a wholesale rewrite; the native-HTML primitives (dialog, popover, details) already cover modals/accordions with 0KB. Adopt Web Awesome selectively for the components that are genuinely expensive to hand-roll: drawer (mobile filters), toast/callout notifications, skeleton loaders, tooltip, and possibly tab-group. Load via the CDN autoloader (two tags in base.html), set the brand tokens to the indigo palette on :root, and keep native form controls for auth and application-critical forms. This adds roughly 20-40KB gzip only on pages that use the components, deletes more hand-rolled JS/CSS than it adds, and inherits dark-mode theming for a future Phase. Avoid Material Web (maintenance mode) and treat archived Shoelace only as a fallback pin if a Web Awesome bug blocks you.

### Uncertain Fields (skipped)

- bundle_size_kb


---

## Vanilla utility libraries for data-heavy pages (fuzzy sea...

### Basic Info

**category**: utility-library

**description**: 

> The rendering/search layer for matcher results and deadline UI, built from small framework-free libraries: client-side fuzzy search (Fuse.js - the standard, with scoring/weighted keys/extended search; microfuzz - a ~2KB gzip minimal alternative tuned for filtering short labels), vanilla data tables (Grid.js - lightweight display grid with search/sort/pagination; Tabulator - full-featured grid with grouping, tree data, editing, export; List.js - tiny progressive enhancement over existing HTML lists/tables), and accessible date pickers (Cally - ~8.5KB min+gzip calendar web components, the spiritual successor to Duet Date Picker; Duet - the older accessible Stencil-based picker, now dormant). They solve instant filter-as-you-type over a few thousand scholarship records, sortable deadline tables, and date input without shipping React or a build step.

**adoption_maturity**: 

> Fuse.js: the dominant client-side fuzzy-search library (~19k+ GitHub stars, millions of weekly npm downloads), active again with 7.x releases through June 2026. microfuzz: niche but credible (built by Nozbe, powers their production app); v1.0.0 since 2023, small community. Tabulator: mature (since 2015), very active (6.5.2 June 2026), widely used in dashboards/internal tools. Grid.js: popular (~4k+ stars) but release cadence has slowed (last stable 6.2.0, March 2024). List.js: historically popular but effectively unmaintained since 2021 - avoid for new work. Cally: rising - recommended by accessibility practitioners as the Duet successor, active releases into 2026, praised publicly (e.g. Wes Bos, 2025). Duet Date Picker: production-proven and accessibility-audited but last release June 2021.

### Code

**code_sources**: 

> Fuse.js: https://github.com/krisk/fuse and https://www.fusejs.io (CDN: https://cdn.jsdelivr.net/npm/fuse.js@7/dist/fuse.min.js ; usage: new Fuse(scholarships, { keys: ['name','sponsor','major'], threshold: 0.35 }).search(query)). microfuzz: https://github.com/Nozbe/microfuzz . Grid.js: https://github.com/grid-js/gridjs and https://gridjs.io (CDN script + new gridjs.Grid({ columns, data, search: true, sort: true, pagination: true }).render(el)). Tabulator: https://github.com/tabulator-tables/tabulator and https://tabulator.info (extensive vanilla examples). List.js: https://github.com/javve/list.js and https://listjs.com . Cally: https://github.com/WickyNilliams/cally and https://wicky.nillia.ms/cally/ (CDN: <script type="module" src="https://cdn.jsdelivr.net/npm/cally@0.9/dist/cally.js"></script> then <calendar-date> / <calendar-range> with <calendar-month>). Duet: https://github.com/duetds/date-picker

**license**: Fuse.js: Apache-2.0; microfuzz, Grid.js, Tabulator, List.js, Cally, Duet: MIT

**dependency_footprint**: 

> All usable from a script tag with no build step and no framework - the defining criterion. Fuse.js/microfuzz/List.js are single-file UMD/ESM scripts; Grid.js bundles its own tiny virtual-DOM (Preact-based) internally; Tabulator is self-contained JS+CSS; Cally is a self-contained web component (Lit-free, tiny); Duet ships Stencil-compiled web components. Fully compatible with the FastAPI + vanilla-JS no-build site. microfuzz is published primarily for npm/ESM use - trivially loadable as an ES module but has less CDN-oriented documentation.

**ssr_htmx_compat**: 

> Fuse.js/microfuzz are pure data utilities - no DOM, so fully SSR/HTMX-safe; re-run indexing after a swap replaces the dataset (rebuild the Fuse index in an htmx:afterSwap handler). Grid.js/Tabulator/List.js render into a container imperatively and must be re-initialized after any partial swap that replaces their mount node - classic re-binding burden; Tabulator instances also hold state (sort/filter/pagination) that is lost on re-init unless persisted. List.js progressively enhances existing server-rendered markup, which fits SSR best philosophically but the library is stale. Cally/Duet are web components: they auto-upgrade when swapped-in markup contains their tags, making them the most HTMX-friendly of the group; Cally works as a form-friendly component whose value can post with a hidden input.

**maintenance_health**: 

> Fuse.js: active - v7.4.2 released June 5, 2026. microfuzz: v1.0.0 (July 2023), minimal activity since (CI runs into 2025); stable-but-quiet. Grid.js: last release 6.2.0 (March 2024) - slowing, watch before adopting. Tabulator: very active - 6.5.2 (June 23, 2026). List.js: unmaintained (2.3.1, January 2021). Cally: active - 0.9.2 (February 5, 2026); pre-1.0 API (stability discussion tracked in repo issue #71). Duet Date Picker: dormant since 2021 (last release 1.4.0, June 2021) - Cally is its recognized spiritual successor.

**integration_effort**: 

> low - each library is a script tag plus a few lines; Tabulator is low-medium (config surface); replacing an existing hand-rolled results renderer with Fuse.js + your own render function is low

### Design

**key_techniques**: 

> Fuzzy search: build an index once (new Fuse(data, { keys: [{ name: 'name', weight: 2 }, 'sponsor', 'tags'], threshold: 0.3, ignoreLocation: true })), debounce input (150-250ms), render top-N results; Fuse extended search syntax ('=exact 'include !exclude) for power filtering; microfuzz alternative: createFuzzySearch(list, { getText: i => [i.name] }) returning ranked matches with highlight ranges via its Highlight helper. Data tables: Grid.js declarative config with server-side pagination hooks (server: { url }) matching a FastAPI JSON endpoint; Tabulator column definitions with sorters, responsive collapse mode (responsiveLayout: 'collapse') for mobile, and download/export (CSV) for deadline lists; List.js valueNames mapping onto existing HTML. Date UI: Cally composable markup <calendar-date value="2026-11-01" min=... max=...><calendar-month></calendar-month></calendar-date>, styled via CSS parts/custom properties, paired with a popover-wrapped text input for a picker; always also accept typed input (type=date fallback) per a11y guidance.

**visual_examples**: 

> https://gridjs.io/docs/examples (live grid demos); https://tabulator.info/examples/6.3 (extensive gallery incl. responsive and editable tables); https://www.fusejs.io/demo.html (interactive weighting playground); https://wicky.nillia.ms/cally/ (themed calendar demos incl. range and multi-month); https://duetds.github.io/date-picker/ (reference accessible picker UX); https://listjs.com (search/sort/filter over plain markup)

**accessibility_notes**: 

> Fuzzy search itself is invisible to AT - the a11y work is in the UI: announce result-count changes via aria-live=polite, keep the input a labelled <input type=search>, and follow the APG combobox pattern if you add a suggestion dropdown. Tables: prefer semantic <table> output; Grid.js renders real tables with sortable-header buttons (verify aria-sort is set); Tabulator historically renders div-based grids with role=grid - test with a screen reader and keep keyboard navigation enabled (its accessibility has known gaps; div-grids are a common audit finding). List.js enhances your own semantic markup, so a11y stays in your control. Date pickers are a11y minefields: Cally and Duet are the rare accessible options (Duet was formally audited with screen readers; Cally continues that lineage with labelled grid semantics, keyboard navigation, and localization) - but always allow direct typed date entry and never make the picker the only input method (WCAG 3.3.2 / usability).

**wcag_mapping**: 

> Relevant criteria: 4.1.3 Status Messages (announce '42 results' after filtering - commonly missed), 1.3.1 Info and Relationships (real <table> with <th scope> for deadline tables; div-grids risk failure), 2.1.1 Keyboard (sortable headers and calendar grids must be keyboard-operable), 1.3.2 Meaningful Sequence (responsive table collapse must keep reading order), 2.5.8 Target Size Minimum (calendar day cells >=24px), 3.3.2 Labels or Instructions (date format hints), 3.3.8 Accessible Authentication n/a here but 3.3.7 Redundant Entry applies if filters reset between steps, 1.4.13 (dismissable picker popover). Fuzzy tolerance also aids 3.3 input-error resilience for students who misspell scholarship names.

**baseline_status**: 

> n/a as libraries (Baseline applies to platform features). Their platform substrate is all Baseline Widely available: ES modules, custom elements/Shadow DOM (Cally, Duet), <input type=date> fallback (widely supported for years). Cally pairs naturally with the Popover API (Baseline Newly available January 2025) for anchored pickers.

**progressive_enhancement_fallback**: 

> Best-practice architecture for this site: server-render the first page of matcher results and deadline tables from FastAPI, then let JS enhance. If a search script fails, the server-rendered list plus a normal GET form to a FastAPI search endpoint still works (full-page reload). List.js-style enhancement of existing markup degrades perfectly by design; Grid.js/Tabulator render nothing without JS unless you keep a server-rendered table beneath and replace it on init. Date input: native <input type=date> is the fallback (and arguably the mobile-first default), with Cally as the desktop enhancement.

**mobile_touch_behavior**: 

> Critical for a mobile-heavy student audience. Search-as-you-type: debounce to avoid jank on low-end phones; keep the input above the fold so the iOS keyboard does not hide results; use inputmode=search for the proper keyboard action button. Tables: wide deadline tables need a strategy - Tabulator's responsiveLayout collapse mode or a card-list layout below a breakpoint beats horizontal scrolling; Grid.js needs manual overflow-x wrappers. Date pickers: on touch, native <input type=date> invokes the OS wheel/sheet picker which is usually the best mobile UX - reserve Cally for range selection and desktop; Cally's day cells are styleable to 44px targets; ensure the picker popover repositions when the virtual keyboard opens.

### Applicability

**relevance_to_ensurecollege**: 

> This is the working layer of EnsureCollege's core value: the scholarship/program/competition matchers and the deadline UI. Fuse.js (or microfuzz for a 2KB budget) gives instant, typo-tolerant filtering across scholarship names, sponsors, majors, and tags client-side - a large perceived-performance win over round-tripping every keystroke to FastAPI, and forgiving for students who type 'Natinal Merit'. A sortable deadline table (sort by due date, amount, match strength) is the natural deadline UI; Grid.js or a hand-rolled sorted <table> covers it without Tabulator's 100KB. Cally + the Popover API provides an accessible, indigo-themeable deadline/date-of-birth picker consistent with the Highlighter brand, replacing inconsistent native pickers on desktop while keeping type=date on mobile.

**current_gap**: 

> The site currently has no client-side fuzzy search (matcher filtering is exact/server-driven within the 133KB hand-rolled JS), no sortable data-table component for deadlines, no date-picker component (native inputs only, unstyled), no result-count live announcements, and no debounced search-as-you-type UX. Result rendering is bespoke JS with no reusable table/search layer.

**recommended_action**: 

> adapt - Adopt Fuse.js (CDN, Apache-2.0, ~7KB) for matcher filtering: fetch the user's matched records once as JSON from FastAPI, build a weighted Fuse index (name > sponsor > tags), debounce input, render into the existing card markup, and announce counts via aria-live; choose microfuzz instead only if every KB counts and matching short labels suffices. Skip Tabulator (100KB is disproportionate) and List.js (unmaintained); for the deadline table either hand-roll sort on a semantic <table> (it is ~50 lines) or use Grid.js if pagination/search-in-table is needed, accepting its slower maintenance. Adopt Cally for desktop date-range/deadline picking inside a [popover] panel, keeping <input type=date> as the mobile and no-JS path; do not adopt Duet (dormant). This yields an instant-feeling matcher for roughly 10-16KB of new gzip payload.

### Uncertain Fields (skipped)

- bundle_size_kb
