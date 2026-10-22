# Plan: EC-01, the landing page that "keeps loading"
_Written by Claude for Josh, 2026-10-17, alongside the fix on `fix/ec01-landing-load`. Terms per CONTEXT.md._
_Not grilled, and **`/codex-review` was not run**: the Codex CLI is not available in the environment this was built in. Run it on this doc before merging if the chain applies (see Process note)._

## Problem

Reported on Reddit on Oct 3 and never reproduced: "the landing page kept
spinning and the link did not work"; the visitor wondered whether traffic was
involved. The outreach link was later changed to explicit HTTPS. That change
is not a confirmed fix, and nothing found here depends on the scheme: an
`http://` link only adds a redirect to HTTPS.

**The visitor's exact failure has not been reproduced on the live site.**
There is no HAR, server log, or timing from their visit. What follows is a
mechanism that produces the same symptoms, proven in the e2e harness, plus
live measurements that show the trigger occurs in production.

## Evidence

### Live site (measured 2026-10-17 in desktop Chrome)

- Warm, the page renders and works. First load of the day: HTML TTFB 171 ms,
  DOMContentLoaded 1.05 s, but `GET /vocabulary` took **4,139 ms**. Warm
  `/vocabulary`, `/health`, and static files answer in about 80 to 100 ms, so
  that request hit a cold function.
- `vercel.json` routes every path, `/static/*` included, to `api/index.py`
  (maxDuration 60). Static files and `/vocabulary` come back with
  `cache-control: public, max-age=0, must-revalidate` (Vercel's default when
  the function sets none) and `x-vercel-cache: MISS`: every asset request on
  every page view is a function invocation.

### Code (main at c41e720)

`app.js` `init()` awaited `fetch("/vocabulary")`, with no timeout, before it
wired anything: the profile form submit, `wirePreviewForm`, `wireSiteNav`,
`wireAuthControls`, the step controls, tabs, filters, settings, and only then
`loadSession()`. Both `#auth-logged-out` and `#auth-logged-in` ship `hidden`,
so until `loadSession()` runs the header has no account controls at all.

### Reproduced in the e2e harness on main

Method: the app in-process exactly as `tests/e2e/conftest.py` runs it, real
Chromium, consent pre-set, and `page.route("**/vocabulary")` holding that one
request (released after 15 s, after 4.1 s, never, or answered 504). The new
tests in `tests/e2e/test_landing_load.py` encode the same reproduction.

| Landing control | main, while `/vocabulary` is pending | this branch |
|---|---|---|
| Log in / Sign up | not rendered (both auth groups stay `hidden`) | rendered; Log in opens the modal |
| Nav: Matches, Plan, Browse | click does nothing (0 px scroll, no view opens) | scroll to the form, open the plan view, open the catalog |
| Hero preview: "Show my 3 matches" | enabled over empty selects; a click is a native GET that reloads the page to `/?`, which issues a second `/vocabulary` request and lands in the same state | disabled and reads "Loading options..." until the options arrive; no reload |
| Profile form | typing a GPA leaves "0 of 6 essentials"; Next and the step tabs are inert; Enter in GPA reloads the page to `/?gpa=3.8&grade_level=&citizenship=&...` | progress counts, Next and step tabs validate, Enter goes through Next; status line reads "Loading form options..." |
| Plain links: "How it works" (nav and hero), "Build my profile" (`#profile-form` anchor) | work (native links) | work |

How long: the scripted controls on main were dead for exactly as long as the
request. Held 15 s: dead through 15.0 s, alive at 15.05 s. Held 4.1 s (the
measured cold start): alive at 4.2 s. Never answered: still dead at 2, 9, 18,
and 30 s, with nothing on screen and no console error. Answered 504 (what
Vercel would send at maxDuration 60 s; simulated at 20 s): main then shows
"The form options could not load. Refresh the page..." in `#form-error`, below
the profile form and off-screen from the hero, while the hero preview stays
enabled over empty selects. Recovery is a full refresh.

On this branch the same never-answered request shows the loading state at 2
and 9 s, attempt 1 at 0.2 s is cut off at about 8.2 s, the retry goes out at
9.2 s and is cut off at about 17.2 s, and both forms show the error with a
Try again button by 18 s. Account controls and nav work throughout.

## Root cause: what is proven and what is not

**Proven (harness, main):** while `/vocabulary` is pending, every scripted
control on the landing page is dead, for exactly as long as the request; the
page looks loaded the whole time; the hero preview submit and Enter in the
profile form fall through to a native GET that reloads the page and starts
over. A request that never answers leaves the page dead until the platform
times out.

**Proven (live):** `/vocabulary` can take over 4 s on a cold function while
the HTML is fast, and neither it nor any static asset is served from Vercel's
CDN today.

**Hypothesis (consistent, not proven):** the Reddit visitor arrived on a cold
or slow `/vocabulary` (or a slow static asset). "Kept spinning" fits the tab's
loading indicator during a native-submit reload or a slow `app.js`; "the link
did not work" fits a dead nav or account control, or the preview reloading.
Low traffic makes cold starts more likely, not less, so "traffic" fits only in
that inverted sense.

**Not established:** how slow cold starts get on this project (one live
measurement, 4.1 s) and which Starlette version production runs (see the
cookie note below).

## Design

### 1. Frontend: wire first, load options alongside (`app/static/js/app.js`)

- `init()` calls `loadFormOptions()` without awaiting it, then wires every
  handler and runs `loadSession()` at once.
- `loadFormOptions()` / `fetchVocabulary()` / `fetchVocabularyOnce()`: each
  attempt is cut off by an `AbortController` after 8 s (this also covers a
  body that stalls after the headers), with one automatic retry 1 s later.
  The promise resolves `true` or `false` and never rejects; the worst case
  reaches the error in about 17 s.
- `setFormOptionsState()`:
  - *loading*: `#preview-submit` disabled and labelled "Loading options...",
    `#submit-btn` disabled, `#profile-progress-status` reads "Loading form
    options...".
  - *ready*: both submits enabled, label restored, any options error cleared.
  - *failed*: label restored, both submits stay disabled, and `#preview-error`
    and `#form-error` (the existing form-error boxes) read "The form options
    did not load. Check your connection, then try again." with a Try again
    button. Try again reloads the options in place (no page reload), keeps
    keyboard focus in its form, and for a signed-in student re-runs the saved
    profile prefill and auto-match that found an empty form on page load.
- Dependency audit of everything `init()` wires against the DOM that
  `populateForm()` creates (`#grade-level`, `#citizenship`, `#state`,
  `#financial-need`, the `#fields-of-study` and `#demographic-tags`
  checkboxes, `#preview-grade`, `#preview-field`, `#catalog-field`):
  - `loadProfileIntoForm()` -> `prefillForm()` **needs the options** (select
    values, checkboxes). It now awaits the in-flight attempt before
    prefilling; that wait is bounded and happens after `renderAuthState()`, so
    account controls never wait. `autoMatchFromSavedProfile()` still runs
    after it. The same path serves `handleAuthSubmit()` and the password-reset
    confirm.
  - `wireCatalogFilters()` listens on the `#catalog-field` element itself,
    which `fillSelect()` keeps (it replaces options, not the element).
  - `wireProfileProgress()`, `wireFormSteps()` / `validateFormStep()`, and the
    preview submit handler read current values when they run; before the
    options arrive they report honestly ("Select your grade level.") and the
    submits are disabled.
  - `prefillFromPreview()` is reachable only from preview results, which need
    the options. `vocabLabel()` already tolerated a missing vocabulary.
  - Dormant AI: `handleResumeImport()` also calls `prefillForm()`; it is off
    (`AI_FEATURES_ENABLED=false`) and left untouched.
  - Auth, password reset, settings, tabs, filters, search, quick applies,
    site nav, and page motion have no dependency.
- **DOM contract unchanged.** No markup, id, or selector change, so
  `tests/dom_contract.json` does not move; `test_dom_contract.py` passes. The
  Try again button is created by `app.js` with the already-emitted
  `btn-secondary` class; one rule in `style.css` sets it on its own line
  inside `.form-error`.

### 2. Server: let the CDN answer shared, cookie-free responses (`app/main.py`)

- `_edge_cacheable()` plus the existing cache middleware (renamed
  `_world_asset_cache_headers` -> `_cache_headers`; the world branch is
  byte-identical) sets `Cache-Control: public, max-age=0, s-maxage=86400`
  only when all hold: GET or HEAD; status 200 or 304; path `/vocabulary` or
  `/static/*`; not `.html` and not `text/html` (StaticFiles can serve the raw
  page templates); no `Set-Cookie`; no `Vary` on `Cookie`.
- Why this is safe, per Vercel's docs (Cache-Control headers; CDN cache;
  Purging, cache keys): `s-maxage` is what makes a function response
  cacheable on the CDN, and when only `Cache-Control` is set Vercel consumes
  `s-maxage` and does not forward it, so browsers keep revalidating
  (`max-age=0`) exactly as today. The cache key includes the unique
  deployment URL, so each deploy starts empty and unversioned assets such as
  `hero-forest-mobile.webp` cannot go stale across deploys. Vercel will not
  cache a response that sets a cookie or varies on `Cookie`; the guard keeps
  the header from claiming otherwise.
- **Cookie note.** The installed Starlette (1.8.0) writes the session cookie
  only when the session is modified, so these routes never set one, signed in
  or not (tested). Production's Starlette is not pinned (it resolves through
  `fastapi>=0.115,<1.0` at build time), and older releases (checked: 0.41.3)
  re-sign the session cookie on every response while the session is
  non-empty, static files included. The guard withholds `s-maxage` from any
  such response instead of stripping the cookie, so session handling is
  unchanged.
- Untouched: HTML pages (`/`, `/journey`, `/privacy`, `/terms` keep
  `no-cache`; the template family already had its own edge policy), auth and
  account routes, every API response other than `/vocabulary`, the world art
  (`public, max-age=31536000, immutable`), and `vercel.json`.

### 3. Lockstep cache-bust

`app.js` and `style.css` changed, so `?v=20260721-6` became `?v=20261017-1`
everywhere it lives: `app/static/index.html`, `journey.html`, `privacy.html`,
`terms.html`, `app/templates/base.html`, the JS pins in `app.js`,
`journey.js`, and `journey-teaser.js`, and `ASSET_VERSION` in
`tests/test_pages.py`.

## Test plan

- `tests/e2e/test_landing_load.py` (new), each failing on main and passing
  here:
  - `test_landing_controls_work_while_options_load`: with `/vocabulary` held,
    the preview submit is disabled with the loading label and the status line
    says so; Log in opens the modal; Plan, Browse, and Matches work; GPA
    updates progress; Next validates; Enter does not reload. Then the options
    arrive, the submit re-enables, and a full three-question preview returns
    three cards. No console errors.
  - `test_failed_options_show_an_error_with_an_in_place_retry`: two 503s give
    exactly two attempts (one automatic retry), then the error in both forms
    with the label restored; Try again recovers in place, with focus in the
    form and no reload.
  - `test_hanging_options_request_ends_in_the_error_not_an_endless_wait`: a
    request that never answers ends in the error after at least 16 s (two cut
    off attempts), not an endless loading state.
  - `test_saved_profile_prefills_once_late_options_arrive`: a signed-in
    student's session renders while the options are held, and once they
    arrive the saved grade and field are prefilled and the auto-match renders
    results.
- `TestEdgeCacheHeaders` in `tests/test_pages.py` (new, 26 cases): the exact
  header on `/vocabulary` and on CSS, JS, vendor JS, font, image, and favicon
  responses, versioned or not; the same policy on a 304; world art still
  immutable; no `s-maxage` on `/`, `/journey`, `/privacy`, `/terms`, the raw
  HTML under `/static`, `/scholarships`, `/programs`, `/competitions`,
  `/health`, `/auth/me`, a missing asset, or `POST /match/preview`; signed in,
  `/vocabulary` and static set no cookie while `/auth/me`, `/account/profile`,
  `/account/saved`, and `/` stay without `s-maxage`; and the guard refuses a
  reply that sets a cookie or varies on `Cookie`.

### Results (2026-10-17; Linux sandbox with 2 CPUs, Playwright 1.56, Chromium 141)

| Check | main (c41e720) | this branch |
|---|---|---|
| `pytest tests/ --ignore=tests/e2e` | 431 passed | 457 passed (26 new) |
| `pytest tests/e2e` | 79 passed, 2 failed | 83 passed, 2 failed (4 new) |
| Same e2e suite, page told it has 8 cores | the 2 failures pass | 84 passed, 1 failed (a known flake, below) |
| `test_landing_performance_contract.py` | passes in the suite | 11 passed, three runs |
| `scripts/validate_dataset.py` | exit 0, no structural errors | identical output |
| New e2e tests run against main | all 4 fail | all 4 pass |
| New header tests run against main | the 11 positive checks fail, the 14 guards pass | all pass |

The two e2e failures are `test_landing_teaser_paints` and
`test_teaser_painting_first_and_same_box_swap`, on main and here alike: with
`navigator.hardwareConcurrency` at 2, `journey-teaser.js` classifies the
device as low-end and keeps the static painting, so three.js never loads. A
local, uncommitted pytest plugin that reports 8 cores to the page makes them
pass, so they are environmental, not regressions.

The one failure in the 8-core run, `TestCatalog::test_browse_catalog_and_search`,
is an existing intermittent flake: run alone and interleaved, it failed 3 of
21 times on main and 3 of 21 on this branch. It reads `innerText` 800 ms
after typing while the smooth scroll to the catalog can still be in flight,
and `.match-card` uses `content-visibility: auto`, so cards that are off
screen at that moment, or not yet through a rendering update, drop out of
`innerText`. Worth hardening separately (wait for a matching card, not a
fixed delay).

## Rollout

1. Merge and deploy. No migration, no environment variable, no `vercel.json`
   change. `/health` should report the new commit.
2. Edge caching, after deploy. Use GET with the headers dumped, not
   `curl -I`: the app answers HEAD on `/vocabulary` and `/` with 405. Run the
   loop twice; the first pass may be a MISS:
   ```
   for url in https://ensurecollege.com/vocabulary \
              'https://ensurecollege.com/static/js/app.js?v=20261017-1' \
              https://ensurecollege.com/static/fonts/Satoshi-Regular.woff2; do
     echo "$url"
     curl -s -o /dev/null -D - "$url" | grep -iE '^(x-vercel-cache|cache-control|set-cookie):'
   done
   ```
   Expect `x-vercel-cache: HIT` on the second pass, no `s-maxage` in what the
   client receives (Vercel strips it), and no `set-cookie`. Then confirm
   nothing else moved: `/` still answers `cache-control: no-cache` with a
   MISS, and a hashed `/static/img/world/` file still answers
   `public, max-age=31536000, immutable`. Signed in, open `/vocabulary` in
   DevTools: a `set-cookie` there would mean production runs an older
   Starlette, and that response must then show neither `s-maxage` nor a HIT
   (anonymous requests still fill the cache).
3. Cold first load: the next morning, before anyone has visited, open a fresh
   incognito window with DevTools Network open and cache disabled, load `/`,
   and record the `/` TTFB, the `/vocabulary` duration and its
   `x-vercel-cache`, and DOMContentLoaded. Compare with the 4,139 ms baseline.
   Whatever the timing, Log in, Sign up, and the nav must respond at once and
   the preview button must read "Loading options..." until the options land.
4. Failure path in production: DevTools, Network, block request URL
   `/vocabulary`, reload. The page stays usable; after about 17 s both forms
   show the error with Try again. Unblock, press Try again, and the options
   load without a reload.
5. Rollback: the frontend change and the edge-cache change are separate
   commits, so either can be reverted alone. No data or schema is involved.

## Risks / open questions

- **CDN eviction.** Vercel calls cache lifetimes best effort and warns that a
  rarely requested asset ("e.g. once a day") may be evicted. On a quiet day
  the first visitor can still miss and wait on a cold function; the frontend
  change is what keeps the page usable then.
- **The HTML is still a function call on every view** (`no-cache`, a
  per-request CSP hash, Save-Data, live counts). A cold start there delays
  first paint; out of scope here.
- **Before `app.js` runs, plain HTML applies**: the preview submit would still
  do a native GET. With static assets on the CDN that window is short. Starting
  `#preview-submit` disabled in markup (the `#age-gate-continue` pattern) would
  close it but changes the frozen markup; left as a follow-up.
- **8 s per attempt** comes from one 4.1 s measurement. A colder start aborts
  attempt 1, and the retry normally lands on the instance that warmed up.
- While options load, Next stays enabled and truthfully says "Select your
  grade level." over an empty select; the status line explains why.
- On failure both boxes are `role="alert"` with the same text, so a screen
  reader may announce it twice.
- CLAUDE.md's suite counts (369 request, 39 browser) are stale; baseline on
  main today was 431 and 81.
- Noticed, not changed: `HEAD /` and `HEAD /vocabulary` answer 405 (FastAPI
  routes do not add HEAD). Browsers never send it for page loads, but some
  link checkers and uptime monitors do.

## Process note

CLAUDE.md asks for `/grill-with-docs-codex` (or at least `/codex-review`)
before code. Neither ran: Josh asked for the fix directly, and the Codex CLI is
not available here. The change touches no auth logic, no schema, no matcher,
no digest, and no student data, and it never alters a cookie; it does add a
caching decision next to the session middleware, so run `/codex-review
plan=docs/2026-10-17-ec01-landing-load.md` before merging if that counts as
cookie handling.
