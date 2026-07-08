# Per-Opportunity SEO Pages — Design

Date: 2026-07-08. Status: approved direction, pending user review of this spec.
Roadmap context: Tier 1 item 2 ("per-opportunity indexable SEO pages"), after the
de-AI restyle (e075ed2). Follow-ups after this project: matcher improvements,
essay tools (separate cycles).

## Goal

Give every catalog opportunity (currently 225 scholarships / 60 summer programs /
37 competitions) its own server-rendered, indexable page so search traffic can
land directly on opportunities instead of only the homepage. Secondary win:
users get shareable URLs for individual opportunities.

## Decisions (user-approved)

1. **All entries get pages, honestly labeled.** Unverified entries and estimated
   deadlines carry the same explicit "confirm on sponsor site" labeling the app
   already uses. No noindex carve-outs.
2. **Card titles link to detail pages** in match results and catalog. "View and
   apply ↗" continues to go straight to the sponsor.
3. **Rendering: Jinja2 server-side templates** (approach A). Rejected: string
   substitution (hand escaping, unmaintainable conditionals) and build-time
   static generation (touches the shelved/risky Vercel static-serving area).
4. **Catalog render batching ("Show more")** is in scope: the client-side
   Browse-all view renders in batches; SEO directory pages never paginate.

## Routes

| Route | Response |
|---|---|
| `GET /scholarships/{slug}` | HTML detail page (slug = existing `id`, e.g. `coca-cola-scholars`) |
| `GET /programs/{slug}` | HTML detail page |
| `GET /competitions/{slug}` | HTML detail page |
| `GET /browse` | HTML hub linking the three directories |
| `GET /browse/scholarships` etc. | HTML directory: full list of links (name, award, deadline) — never paginated |
| `GET /sitemap.xml` | Generated from `app.state`: homepage, /browse pages, all detail pages |

- Existing JSON APIs (`GET /scholarships`, `/programs`, `/competitions`) are
  untouched; detail routes coexist under the same prefixes.
- Unknown slug → styled 404 page (shared template), correct 404 status.
- `robots.txt` gains a `Sitemap: https://ensurecollege.com/sitemap.xml` line.
- Homepage footer gains a "Browse all opportunities" link to `/browse` so
  crawlers have a link path from `/` to every detail page (the JS catalog is
  invisible to crawlers).

## Detail page content

Rendered with the existing design system (style.css, Highlighter identity,
precision-product register — no new visual language):

- `<title>`: `{Name}: ${award} scholarship | EnsureCollege` pattern (adapted
  per kind; no hype verbs, no em dashes). Meta description generated from real
  data fields, specificity-first.
- Canonical URL, OG/Twitter tags (existing og-image).
- Header/footer identical to the app shell (shared Jinja base template).
- Breadcrumb: Browse › Scholarships › {Name}.
- H1 name + sponsor/host line.
- Stat blocks (reuse `.stat` styles): award (gold treatment), deadline —
  estimated deadlines labeled "Estimated; confirm on sponsor site", urgent
  styling only when a real verified deadline is near.
- Description paragraph.
- Eligibility summary: grade levels, citizenship, GPA minimum, fields of
  study, special requirements (reuse the app's special-requirements panel
  conventions).
- Application requirements checklist (from `application_requirements`).
- Verification line: "Verified {date} · View official source" linking the
  sponsor page, or the explicit not-yet-verified labeling.
- CTAs: primary "View and apply ↗" (sponsor URL, rel="noopener"), secondary
  "See your fit" → `/#profile-form`.
- JSON-LD structured data, honest types only: `MonetaryGrant` (scholarships),
  `EducationalOccupationalProgram` (summer programs), `Event` for competitions
  with real dates, plain `WebPage` otherwise. No fabricated fields.

## Rendering & infrastructure

- Add `jinja2` to requirements. Templates in `app/templates/`:
  `base.html`, `detail.html` (parameterized by kind), `browse.html`,
  `browse_index.html`, `404.html`.
- Autoescape on. All data fields escaped by the engine.
- Data source: `request.app.state.*` (already loaded at startup) — no DB.
- Slug lookup via a dict built once at startup (`app.state.scholarships_by_id`
  etc.) rather than linear scans.
- Cache headers on detail/browse/sitemap responses:
  `Cache-Control: public, s-maxage=86400, stale-while-revalidate=604800` so
  Vercel's edge serves most hits without invoking the function. Data changes
  only at deploy, and deploys naturally invalidate the edge cache.

## App integration (client)

- `app.js`: card titles in match results, catalog, and saved views become
  `<a href="/{kind}/{id}">` links. Styling: ink text, underline on hover/focus
  (consistent with the interaction language; no new hover effects).
- Catalog "Show more" batching: Browse-all renders the first 30 items per
  view, a "Show more" button appends the next 30 (button, not infinite
  scroll). Search/filter/sort operate over the full in-memory dataset and
  reset the window. Match-result lanes are unchanged (tier grouping already
  segments them).
- Asset cache-bust version bumped in `index.html` + `tests/test_pages.py`.

## Testing

- Detail routes: 200 + expected content for one entry of each kind; HTML
  escaping (inject a fake entry name in a unit test with markup); 404 unknown
  slug; unverified entry shows the labeling; estimated deadline shows the
  labeling; canonical + JSON-LD present.
- Browse pages: list counts match `app.state` sizes; every link resolves.
- Sitemap: URL count = 5 + total entries (home, /browse, 3 directories, then
  every detail page); all URLs absolute with the production host.
- robots.txt includes the Sitemap line.
- Existing suites keep passing (252 tests today).

## Error handling

- Unknown slugs 404 with the styled page (no stack traces).
- Entries with missing optional fields (no award amount, no deadline, no
  requirements) render with those sections omitted — no empty scaffolding.
- Sitemap and browse pages must not 500 if a kind's list is empty.

## Out of scope

- Pagination/lazy-loading of directory pages (SEO-hostile).
- Per-page OG images, related-opportunities modules, breadcrumb JSON-LD —
  possible later polish.
- Matcher improvements and essay tools (next cycles).
