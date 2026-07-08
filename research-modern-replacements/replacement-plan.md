# Modern Replacement Plan — de-AI-ing the EnsureCollege UI

Date: 2026-07-08. Synthesizes `results/*.json` (8 items, ~120 sources, all validated).
Companion to `research-ai-design-tells/cross-reference.md` (what was flagged and where).

The eight recommendations converge on one coherent direction — call it **"printed
dashboard"**: flat paper surfaces, hairline rules, a mono data voice, real numbers and
real screens, with the entire motion budget spent on a single hero moment. Every
recommendation is vanilla-CSS/JS, light-only, CSP-safe.

## 1. Header → flush full-width app bar  (OWNER DIRECTION, do first)
Replace the floating blurred pill (`.site-header`/`.header-inner`, `style.css:157-180`) with:
- Single bar, **56–64px**, `position: sticky; top: 0`, full-bleed edge to edge.
- **Solid** paper background (`--surface`, not white, not translucent — delete `backdrop-filter`).
- `1px solid var(--line)` border-bottom. **No border-radius** on the bar (radius allowed on inner buttons/menus only).
- Inner **max-width wrapper** so brand + account cluster align with the page's content column (existing `.header-inner` markup already provides this; change is CSS-only).
- Grid regions: Fraunces wordmark left · account/saved/settings cluster right (Space Mono for the numeric saved-count badge).
- Optional: border/shadow intensifies slightly after scroll — the existing `.has-scrolled` hook (`style.css:1437`) already does this; keep it, without blur/opacity changes.
- Rejected by research: two-tier GOV.UK/Stripe enterprise chrome (overkill at this scale, "enterprise cosplay").
- A11y: sticky header needs `scroll-padding-top` kept in sync (already present per WCAG fix) and solid background guarantees text contrast.

## 2. Section motion → none below the hero; one hero moment
- Delete `reveal-on-scroll` from all 7 sections; sections render instantly (Linear/Stripe/Vercel behavior below the fold). The IntersectionObserver reveal code in `app.js:254+` can go.
- Spend the whole motion budget on **one load-time hero animation**: draw on the marigold marker behind "fit you." (the existing `.mark` highlight) via plain CSS `@keyframes` — a wipe of the highlight, not another fade+rise. `prefers-reduced-motion` guarded. Zero JS.
- Optional later: one `animation-timeline: view()` element below the fold (e.g. a real-stats divider), never more than one — porting fade-ins to `view()` everywhere would recreate the tell in new syntax.

## 3. Card interactions → tiered, no transforms
- Clickable cards (match/preview/catalog): border deepens + very light background tint on `:hover` **and** `:focus-visible` (parity), no shadow growth, no translateY. Optional trailing arrow reveal on the card *title* for pure-navigation cards.
- Stat tiles / dense rows: no decorative hover at all (dashboard consensus).
- All interactive cards: brief inset press state on `:active` for click feedback.
- Uniformity was the tell — varying treatment by card type is itself the fix.

## 4. Backgrounds → flat paper + grain + rules + banding
- Remove both body radial glows (`style.css:107-108`) and the hero orb (`style.css:412-414`, `@keyframes hero-orb`).
- Flat `--canvas`, overlaid with **2–4% opacity feTurbulence grain** (tiny inline SVG data URI in CSS — CSP-safe, no JS) for tactile paper quality.
- Depth via **hairline rules** (1px `--line` dividers between sections) and **solid section banding** (alternate `--canvas`/`--surface`; consider a dark `--brand` footer band).
- Marigold reserved for flat rules/underlines/one color-blocked moment, never diffused tints. (FT Origami / Kinfolk / Swiss-grid vocabulary.)

## 5. Card accents & status → typographic, single-hue
- Delete the 4px colored left borders (`.preview-card` `style.css:1732`, `.rec-letter-row` `style.css:1814-1819`) → hairline top rule or no accent; whitespace + Fraunces carry hierarchy.
- Routine statuses: **Space Mono uppercase text in neutral ink** — no chips.
- Reserve **one marigold dot + label** for the single "needs attention" state (deadline overdue etc.) — Vercel Geist dot convention restricted to one hue.
- Multi-fact metadata (deadline / amount / status): compact key:value definition-list rows (Hanken labels, Space Mono values) instead of scattered badges.
- A11y: never color alone — the dot always pairs with text.

## 6. Microcopy → specific, budgeted
- **Specificity-first**: lead with real numbers the site actually has (225 scholarships, 60 programs, 37 competitions, real deadlines/amounts) instead of adjective triads; set stats in Space Mono.
- **Rhythm budget**: max one em dash and one three-item list per page of copy.
- **Verb audit**: remove "unlock" (×2) and kin; plain declarative verbs. Rewrite "More than a list of links" family constructions as direct statements of what it does.
- Voice note (one line, not a system): "plainspoken, specific, a little dry, no hype verbs."

## 7. Eyebrows → edited, not looped
- Keep the mono eyebrow in the **hero + at most 1–2 sections** where the label names something real (rewrite so no label could be pasted onto another section unchanged).
- Convert the rest to a plain hairline rule/whitespace break or standalone heading.
- Numbering (`01/02/03`) only for genuine sequences — the 3-step profile form qualifies; the trust strip and difference cards do not (research: numbered markers are "the AI editorial scaffold one tier deeper").

## 8. Hero visual → real screenshot, one real stat
- Replace the fabricated "Match review" card (pulsing dot, animated meter, float) with **one real, static screenshot** of the actual match-results screen in a minimal frame (thin border + soft shadow; simplified two-dot window bar at most).
- Annotate with exactly **one real statistic** in Space Mono tabular numerals (e.g. live catalog count) and one sparing marigold accent (underline on a headline word or thin rule under the stat).
- No ambient orb, no idle animation. (Combines with items 2 and 4: the hero's remaining motion is just the marker draw-on.)

## Suggested implementation order
1. Header (owner priority; CSS-only, high visibility)
2. Backgrounds + motion removal (deletes code; items 2+4, they share the hero)
3. Card interactions + accents/status (items 3+5, same files)
4. Hero visual (needs a real screenshot asset; item 8)
5. Copy pass + eyebrow edit (items 6+7, content-only)

Remember: cache-bust versions in `index.html` asset URLs are asserted in
`tests/test_pages.py` — bump both when changing static assets. Site is light-only;
do not reintroduce dark tokens.
