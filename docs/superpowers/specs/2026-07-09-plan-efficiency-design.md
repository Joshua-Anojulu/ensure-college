# Plan Efficiency Changes — Design

Date: 2026-07-09. User-approved direction.

## 1. Recommendation letters: manual tracker → auto-derived rollup

The manual rec-letter tracker (name/relationship/due form + status rows) is removed.
Replacement: a **"Recommendation letters needed"** rollup in the Application Plan
view, computed entirely from data the app already has:

- Source: each saved opportunity's `application_requirements` whose `id` or
  `label` matches /recommend/i (also match "reference letter"). These steps
  already exist in the item's checklist and their completion state is already
  persisted via the existing checklist progress storage.
- Rendering: one consolidated list, sorted by the item's deadline: requirement
  label, the opportunity it belongs to (linked), deadline (with the existing
  estimated/verify labeling), and a checkbox that toggles the SAME underlying
  checklist step (reuse the existing checklist update path; no new storage).
- Header states the consolidated count ("3 recommendation letters across your
  saved items"). Empty state: "None of your saved items require recommendation
  letters."
- No manual input remains. Remove: the rec-letter form/list UI, `app.js` wiring,
  `/account/rec-letters` endpoints (all four), Pydantic/ORM models, and the DB
  table via a new Alembic migration (next number after the current head) that
  drops `recommendation_letters`. Remove their tests; add tests for anything
  server-side that changes.

## 2. Quick applies (instead of auto-submission)

Auto-submission was considered and rejected (no sponsor APIs, ToS/CAPTCHA
conflicts, PII liability, trust damage). The approved alternative:

- A **"Quick applies"** panel at the top of the Application Plan tab, visible
  whenever match results exist (logged in or out).
- Contents: matches from all three lanes where `eligibility.essay_required` is
  false AND the count of `required: true` application requirements is ≤ 3
  (items with no requirements data qualify but show "requirements not yet
  verified" labeling). Sorted by soonest real deadline (estimated after real,
  no-deadline last). Cap the list at 10 with the existing Show more pattern if
  longer.
- Each row: name (links to detail page), kind label, deadline, requirement
  count, "View and apply ↗" to the sponsor.
- A **"Copy profile summary"** button: writes a plain-text summary of the
  current profile (GPA, grade, citizenship, state, fields, activities) to the
  clipboard for fast form-filling. Confirmation state on the button
  ("Copied"), no toast framework.

## 3. Remove the .ics export

Remove the "Export verified deadlines (.ics)" button, the
`GET /account/saved/calendar.ics` route, `app/ics.py` (`build_calendar`), any
app.js wiring, related tests, and the README route-table row. Weekly reminder
emails remain the deadline-surfacing mechanism.

## Constraints

Copy voice (sentence case, no em dashes, no hype). Existing CSS classes where
possible. Asset `?v=` bump once at the end (controller). Full pytest suite
green. Match-lane batching, filters, and catalog code untouched except where
this spec requires.
