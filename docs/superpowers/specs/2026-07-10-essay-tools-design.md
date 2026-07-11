# Essay Tools (Non-AI) + Auto-Match Design

Date: 2026-07-10
Status: Approved pending user review

## Goal

Give students concrete, verified essay information and planning inside the
surfaces they already use, without AI features and without adding new Plan-tab
sections. Four pieces:

1. **Prompt library** — verified essay prompts and length limits attached to
   existing requirement steps.
2. **Start-by dates** — derived "start drafting by" dates in the existing
   deadline timeline and reuse map.
3. **Essay guide pages** — five public, server-rendered writing guides (one per
   reuse-map theme) with curated external example-essay links.
4. **Auto-match on session restore** — logged-in users with a complete saved
   profile get lanes populated without pressing match again.

Explicitly out of scope: any AI feature (the dormant `app/essay/` module stays
dormant), a draft-writing workspace, original example essays (we link out to
reputable published collections instead), and prompt data for entries with no
writing component.

## Anti-overwhelm rules (apply to every piece)

- No new Plan-tab sections. Everything renders inside existing surfaces.
- Prompt details are collapsed by default (native `<details>`).
- One guide link per reuse-map cluster, not per item.
- Gated prompts get a single muted line, never a panel.
- Homepage is untouched.

## 1. Prompt data model

Requirement steps in `scholarships.json`, `summer_programs.json`, and
`competitions.json` may carry one new optional key:

```json
"essay_prompts": {
  "status": "public" | "gated",
  "items": [
    { "prompt": "<verbatim official prompt text>", "length": "150-250 words" }
  ]
}
```

- `length` is a faithful string mirroring official wording ("650 words max",
  "2 pages"), or omitted when the sponsor states none. Never invented.
- `items` is a list; a step can have several prompts.
- `status: "gated"` with empty `items` records that prompts are only visible
  inside the sponsor's application portal. UI copy: "Prompts revealed after
  registration."
- Absent `essay_prompts` key = not yet verified. Absence stays meaningful.
- Pydantic requirement model gains the matching optional fields. Validator
  rules: `status` in enum; `public` requires >= 1 item with non-empty prompt
  text; `gated` requires empty items; `length` optional non-empty string.
- Prompt text is sourced from the step's existing `source_url` (or a corrected
  one recorded during the pass).

### Verification pass

Mirrors the deadline re-verification pattern: a Sonnet subagent sweep over only
the catalog entries whose requirement labels/details match the writing-step
regex (server-side equivalent of the reuse map's `isWritingRequirement`:
essay / short answer / short-answer / response / statement / writing /
problem set / solutions). For each entry: read the official page, record
public prompts verbatim with per-item length, mark portal-locked ones `gated`,
and touch nothing when the page is dead or ambiguous. No fabrication, no
paraphrase. Output is catalog-file edits in a reviewable commit.

## 2. Display surfaces

1. **Essay reuse map (Plan tab):** clustered items with public prompts gain a
   collapsed `<details>` expander showing prompt text + a length chip. Gated
   steps get one muted line. No JS needed; respects CSP `script-src 'self'`.
2. **Saved-item checklists:** the same prompt block renders under the matching
   checklist step.
3. **Public SEO detail pages:** the requirements section renders prompt text
   and length. (SEO value: "<sponsor> essay prompts" queries.)

## 3. Start-by dates

Client-side derivation only; no new data, no settings.

- For every saved essay-bearing item with a real or estimated deadline:
  `start_by = deadline - 21 days`. If already past: label "start now".
- Rendered as one "Start drafting by <date>" line on that item's existing
  deadline-timeline row, and one "Earliest start: <date>" per reuse-map
  cluster (minimum across its items).
- Fixed 21-day lead by design — no pseudo-smart scaling by word count or essay
  count; that would imply precision we do not have.
- Estimated deadlines keep their existing "estimated" labeling adjacent to the
  start-by so uncertainty carries through. No deadline = no start-by line.

## 4. Guide pages

- Routes: `/guides/essays` (index) plus five theme pages:
  `/guides/essays/identity`, `/guides/essays/why-fit`,
  `/guides/essays/leadership-service`, `/guides/essays/academic-research`,
  `/guides/essays/general-writing`. Slugs = `WRITING_REUSE_GROUPS` keys.
- Server-rendered Jinja2 following the `seo_pages.py` pattern: edge cache
  `s-maxage=86400`, sitemap entries (+6 URLs), WebPage JSON-LD, light-only.
- Content in `app/data/essay_guides.json`, one record per theme: title, intro,
  practical how-to (structure, dos/don'ts, tailoring advice for that theme),
  and curated external example links `{title, url, source}` to reputable
  published collections (e.g., Johns Hopkins Essays That Worked, College Essay
  Guy). Guide copy follows site copy rules (em-dash budget, no "unlock").
- Links verified live at authoring time; tests assert structure, not liveness.
  External links open in new tabs with `rel="noopener noreferrer"`.
- Cross-links: each reuse-map cluster links to its theme guide ("How to write
  this kind of essay"); guide pages link back to `/browse` and home; the
  guides index joins the footer nav.

## 5. Auto-match on session restore

- When a session restores (or immediately after login) and the account has a
  complete saved profile, the frontend silently runs the same three match
  calls the submit button triggers and populates all lanes, using the existing
  skeleton loading cards.
- "Complete" = the prefilled values pass the same per-step validation the
  manual submit path enforces (no new completeness concept).
- Incomplete profile: no auto-match; current behavior stands.
- No scroll-jumping on load; results render in place.
- Manual re-match with edited form values is unchanged.
- Cost note: adds three match requests per logged-in page load. Fine at
  current scale (in-memory matching); revisit if traffic grows.

## Error handling

- Validator rejects malformed `essay_prompts` at load time (same failure mode
  as other catalog errors).
- Auto-match failures degrade silently to today's behavior (empty lanes +
  form); no error toast on page load.
- Guide route for an unknown theme slug: 404, consistent with detail pages.

## Testing

- Validator tests: `essay_prompts` enum/shape rules, public/gated constraints.
- Model tests: optional fields round-trip.
- Page tests: six new guide routes 200 + content, sitemap count updated,
  prompt rendering on SEO detail pages, `<details>` markup present.
- JS-path coverage via existing page-test pattern: start-by labels (past and
  future deadlines, estimated labeling, no-deadline omission), auto-match on
  mocked session restore, no-auto-match on incomplete profile.
- Asset version bump asserted in `tests/test_pages.py` as usual.

## Build order (each independently shippable)

1. Data model + validator + display on SEO pages (no UI risk).
2. Reuse map + checklist prompt rendering, start-by dates.
3. Guide pages + content + cross-links.
4. Auto-match on session restore.
5. Prompt verification data pass (subagent), last — the UI handles absent data
   gracefully from step 1, so data can land incrementally.
