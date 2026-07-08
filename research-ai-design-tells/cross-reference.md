# AI Design Tells × EnsureCollege — Cross-Reference

Date: 2026-07-08. Research: 8 categories, 63 flagged features, ~130 sources (see `results/*.json`).
Site audited: `app/static/index.html`, `app/static/css/style.css`, `app/static/js/app.js` (live Highlighter restyle).

Strength = how strongly the community associates the feature with AI-generated sites
(strong / moderate / weak, from the research). Every source stresses that single tells
are meaningless — clusters of co-occurring tells are the real signal.

## Flagged features PRESENT on the site

| # | Flagged feature (category) | Strength | Where on the site |
|---|---|---|---|
| 1 | Scroll-triggered fade-in-up on every section (animation) | strong | `.reveal-on-scroll` on all 7 landing sections, staggered `data-reveal-delay` 0–170ms; `style.css:1439` (opacity 0 + translateY(16px) → visible), IntersectionObserver in `app.js:254` |
| 2 | Hover lift + shadow on cards (animation + component) | strong/moderate | `.difference-card:hover` `style.css:621` and `.match-card:hover` `style.css:1031` — translateY(-3px) + shadow; buttons/`.card-link` lift -1px |
| 3 | Drifting blurred gradient orb / aurora background (animation + imagery) | strong | Hero orb `style.css:412-414` (radial-gradient circle, 18s infinite drift); fixed twin radial glows on `body` `style.css:107-108` |
| 4 | Glassmorphism / frosted-glass panel (color) | moderate | Floating sticky header: translucent surface + `backdrop-filter: blur(16px) saturate(150%)` `style.css:179`; modal overlays blur(4px) |
| 5 | Colored left-border "side-tab accent" on cards (component) | strong | `.preview-card` `style.css:1732` (4px marigold left border); `.rec-letter-row` `style.css:1814-1819` (4px left border, color switches by status) |
| 6 | Status-colored badge set trending "rainbow" (component) | moderate | Multiple tint families (success/amber/violet/danger tokens) power match-quality and status badges across cards |
| 7 | Em-dash-heavy copy (copywriting) | strong | ~15+ em dashes: `index.html:273,685`, terms/privacy, many UI strings in `app.js` (1607, 2326, 4165, 4974…) |
| 8 | Rule-of-three / triad phrasing (copywriting) | moderate | Title triad ("Scholarships, summer programs, and competitions"), 3 proof-point pills, 3 trust-strip items, 3 difference cards, 3-step form, hero-note triad |
| 9 | Power-verb "Unlock" (copywriting) | strong (as cluster; single verb here) | "unlocks every match" `index.html:233`, "unlock the planning layer" `index.html:709` |
| 10 | Small uppercase/mono "eyebrow" label above hero headline (typography) | moderate | `.eyebrow` mono labels above hero and every section ("A clearer path to opportunity", "60-second preview", …) |
| 11 | Monochrome-plus-single-accent palette (color) | weak | The Highlighter identity is literally ink + one marigold accent |
| 12 | Uniform card sizing/spacing system-wide (layout) | moderate | Token-driven radius/spacing/shadow scale applied to every card/panel |

## Borderline / partial matches

| Flagged feature | Verdict |
|---|---|
| Generic SaaS landing anatomy + 3-feature-card grid (layout, strong) | Partial — hero is asymmetric (copy/visual/photo), not the flagged centered hero; but the 3-card `difference-grid` and the hero→proof→features→CTA section flow rhyme with the template |
| "It's not just X, it's Y" false-contrast (copywriting, strong) | Partial — "More than a list of links." and "Elite summer programs, not an afterthought" are the same rhetorical family |
| Fake product mockup in hero (imagery, moderate) | Partial — the hero "Match review" visual is a fabricated stylized UI card, though abstract rather than a fake screenshot |
| Stat/KPI counter rows (component, moderate) | Partial — hero card has label/value stat rows + animated meter, but no count-up numbers |
| Huge tight-tracked hero headline (typography, strong) | Weak — headline is large but serif (Fraunces) with only -0.01em tracking; the tell targets tight geometric sans |
| "Animate everything" tendency (animation, moderate) | Partial — hero runs 4 concurrent ambient animations (orb drift, card float, status pulse, meter settle) plus ring-draw on results, though easing is restrained, `prefers-reduced-motion`-gated via `motion-ready` |
| Nested cards / "Cardocalypse" (component, moderate) | Borderline — bordered `.panel` sections containing bordered cards is one nesting level |

## Flagged features ABSENT (the restyle actively dodges these)

- **All framework/provenance fingerprints** (strongest category): no Tailwind, no shadcn/Radix, no Next.js scaffold, no Lovable/v0/Bolt artifacts, hand-written semantic CSS/JS — detector tools would score this site low.
- Indigo/purple palette, blue→purple gradients, gradient hero text, neon glows (site is light-only, warm paper).
- Inter/Geist/Space Grotesk defaults (Fraunces + Hanken Grotesk + Space Mono instead).
- Emoji or Lucide icon rows (numbered mono `01/02/03` instead), gradient pill buttons, testimonial cards/fake avatars, logo clouds, pricing trio, bento grid, footer mega-columns.
- AI-generated imagery, corporate-Memphis illustration, 3D renders (real campus photography with one art direction).
- Typewriter text, marquee strips, scroll-jacking.

## Read

The site's overlap clusters in **motion** (staggered scroll reveals, hover lifts, ambient orb — the three strongest animation tells all present) and **microcopy rhythm** (em dashes, triads, "unlock"). Its provenance, palette, type, and imagery — the categories observers check first — read as deliberately un-AI. Per the research's own false-positive guidance, most individual hits here predate AI tooling; the one cluster worth acting on, if the goal is to not read as AI-built, is the animation trio, plus thinning em dashes and "unlock".
