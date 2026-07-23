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
An opportunity held back from ordinary results because the profile cannot verify a **pre-existing eligibility status or channel the student must already hold or go through** — nomination, membership (whether invitation-only or free-to-join), finalist or contest-winner status in a *separate* program, a required affiliation or channel. Surfaced in its own "special opportunities to check" group — never as a Strong match. Not selective-only: a free-to-join membership still qualifies because the profile can't confirm the student actually joined. Two things it is **not**: (1) a **passive, near-universal condition** the student meets by doing nothing (no federal debt, eligible to obtain a security clearance, no existing service obligation) — flagging it would wrongly demote a scholarship most students are eligible for; (2) ordinary **application or selection work every applicant performs** for *this* award (an essay, a submitted video, an audition, an interview, or entering the award's own contest) — that is application effort, not a pre-existing gate. Record both kinds of condition in the [[Checklist]] details instead.
_Avoid_: Edge case, manual review, gated match, selective-only

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

**Quick apply**:
A match nothing stands between the student and applying to: no essay, few requirement steps, and no **special check**. Drawn from the current match set, not the saved set. It names what is *actionable*, never what is easy — assembling an arts portfolio is a quick apply if nothing blocks the student from starting it, while a nomination-only award never is, however few its steps.
_Avoid_: Easy win, low effort, low-hanging fruit

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
The valley-overlook promo docked on the landing page, linking to the Journey: a painted overlook first, becoming the live miniature island on capable devices after load. A promotion for the Journey, not a second Journey.
_Avoid_: Widget, preview (that word means the three-question matcher demo)

**Journey map**:
The 2D illustrated progress map on the saved-applications view. Its geography is fixed — the world's established landmarks along the [[Trail]] — and it is personalized by the student's real [[Saved opportunity]] [[Status]] data, never fabricated: saved items appear as markers at the stage they are in, with the student's current frontier flagged. With nothing saved (or signed out) it shows a labeled generic sample path as an invitation. Distinct from the [[Journey]] (the 3D scroll flight) and the [[Teaser]] (the landing promo for it).
_Avoid_: Journey (that is the 3D flight), progress bar, roadmap

**Forest Light**:
The design system shipped 2026-07-13: light-only, token-driven, deep forest brand on a cool paper canvas with a single amber accent. All color, type, and depth come from the tokens in `style.css`; nothing hardcodes a hex.
_Avoid_: Theme, skin, palette (as a name for the whole system)

**World**:
The continuous illustrated forest environment every surface lives inside; working content always rides in legible panels over it. On the landing it deepens as you scroll, from morning trailhead to dusk treeline. The world decorates the journey; it never gates an action.
_Avoid_: Background, theme, scenery

**Trail**:
The marigold dotted path — the one persistent world element. It connects sections and waypoints and marks the student's route through the world.
_Avoid_: Path, line, connector

**World glyph**:
A hand-inked pictogram in the Forest style. Since Phase 2 there is one drawn glyph language across the whole site — illustrated moments and working controls alike — replacing the earlier split between world glyphs and a separate functional icon family. A purely decorative glyph still never poses as a control: anything clickable is a labeled control that carries a glyph, not a glyph acting alone.
_Avoid_: Icon set (there is only one), illustration
