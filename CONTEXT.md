# EnsureCollege

A college-planning web app for U.S. high-school students. One profile matches against three curated opportunity catalogs, and a planning layer turns saved opportunities into a tracked application plan. This file is the shared vocabulary: when a plan or a conversation uses one of these words, it means exactly what is written here.

## Opportunities

**Opportunity**:
Any item a student can apply to. The umbrella term over the three lanes.
_Avoid_: Listing, item, result, record

**Lane**:
One of the three opportunity categories — scholarships, elite summer programs, competitions. Each has its own dataset, matcher, and filters, but shares one profile.
_Avoid_: Category, vertical, type, tab

**Catalog**:
The full curated set of opportunities across all lanes, stored as JSON in `app/data/`. Curated and manually verified, not scraped.
_Avoid_: Database, index, directory

**Sponsor**:
The organization offering an opportunity, and the authority for its facts. The sponsor's official page is the only acceptable verification source.
_Avoid_: Provider, issuer, org

## Verification and data honesty

**Verified**:
An entry whose key facts (award, eligibility, current-cycle deadline where published) were checked against the sponsor's official page. Recorded as `verified: true`.
_Avoid_: Confirmed, validated, checked

**VERIFY placeholder**:
The literal string `VERIFY` in an unknown field. It means "we do not know," never "no requirement." The matcher must treat it permissively and never gate on it; the UI must label it.
_Avoid_: Null, missing, unknown, TBD

**Estimated deadline**:
A projection of the *upcoming* cycle, inferred from the most recent published one, shown explicitly as an estimate ("~Feb 15, 2027 · Estimated; confirm on sponsor site"). Never presented as a real deadline, never gates a match, never fires a closing-soon badge, and always sorts behind every confirmed deadline. Once the projected date passes it is stale: roll it to the next cycle or replace it with the sponsor's published date. A wrong deadline is worse than an honest placeholder.
_Avoid_: Approximate deadline, past-cycle date

**Fact audit**:
A fresh re-check of an entry against its sponsor page, stamped in `last_verified_at`. Audits older than 90 days enter the re-verification queue.
_Avoid_: Refresh, update, recheck

## Matching

**Profile**:
The student's answers — GPA, grade level, citizenship, state, financial-need level, fields of study, demographic tags, target schools, activities. One profile drives all three lanes.
_Avoid_: User data, form data, inputs

**Gate**:
A hard eligibility filter that excludes an opportunity outright (GPA, grade, state, citizenship, passed deadline). Gates apply **only** when the dataset holds a real value — never on a `VERIFY` placeholder.
_Avoid_: Filter, requirement, cutoff (reserve "filter" for the user-facing result controls)

**Signal**:
An additive scoring component that raises fit without ever excluding (field overlap, demographic overlap, target-school match, activity keywords, need, financial access).
_Avoid_: Weight, factor, score bump

**Special check**:
An opportunity held back from ordinary results because it carries a niche gate the profile cannot verify (nomination, membership, finalist status, first-generation-only). Surfaced in its own "special opportunities to check" group — never as a Strong match.
_Avoid_: Edge case, manual review, gated match

**Match quality**:
The bucket a scored result lands in: **Strong**, **Possible**, or **Special check**. These three words are the only correct names for the buckets.
_Avoid_: Good/fair, high/low, tier

**Preview**:
The three-question hero demo (GPA, grade, interest) that runs the real matcher with no account and flags residency gates rather than applying them.
_Avoid_: Demo, trial, quick match

## Planning layer

**Saved opportunity**:
An opportunity a signed-in student has added to their plan, carrying status, notes, and a checklist. Distinct from a match, which is transient.
_Avoid_: Bookmark, favorite, pinned item

**Status**:
Where a saved opportunity stands: interested, drafting, submitted, awarded, rejected.
_Avoid_: Stage, state, progress

**Checklist**:
The persistent, source-linked list of application requirements derived for a saved opportunity. Feeds the recommendation-letters rollup.
_Avoid_: Todo, tasks, steps

**Digest**:
The opt-in weekly email covering saved items closing within 14 days plus strong-match alerts for newly added opportunities. Sent by Vercel cron, guarded by `CRON_SECRET`.
_Avoid_: Newsletter, notification, reminder email

## Platform

**Dormant AI**:
The Anthropic-powered essay/resume code that remains in the tree but is gated behind `AI_FEATURES_ENABLED` (default `false`). No student data reaches any AI provider unless deliberately enabled. Treat as off unless a plan says otherwise.
_Avoid_: Disabled features, legacy AI, dead code

**Opportunity page**:
The server-rendered, indexable public page for a single catalog entry (e.g. `/scholarships/coca-cola-scholars`), carrying honest verification labeling and JSON-LD.
_Avoid_: Detail page, landing page, SEO page

**Journey**:
The `/journey` page: one continuous scroll-driven camera flight through four rendered scenes (the profile, the three lanes, the plan, the gate). It explains the product; it is never where a student works. Reached from "How it works".
_Avoid_: Demo, tour, animation, 3D page

**Teaser**:
The live miniature island docked on the landing page, linking to the Journey. A promotion for it, not a second Journey.
_Avoid_: Widget, preview (that word means the three-question matcher demo)

**Forest Light**:
The design system shipped 2026-07-13: light-only, token-driven, deep forest brand on a cool paper canvas with a single amber accent. All color, type, and depth come from the tokens in `style.css`; nothing hardcodes a hex.
_Avoid_: Theme, skin, palette (as a name for the whole system)
