# Plan: Phase 0 LCP tuning — pass the mobile gate while keeping the immersive hero
_Locked via grill-with-docs — by Claude + Josh, 2026-07-19. Terms per CONTEXT.md._
_Rev 3 APPROVED (Codex rounds 1–3) → step 1 executed → **rev 4** retarget (hypothesis refuted)._
_**Rev 5** after Codex round 1 on rev 4 (REVISE, 9 findings, all accepted)._
_**Rev 6** after Codex round 2 on rev 5 (REVISE, 4 findings, all accepted)._

## Goal

The Phase 0 Forest-Journey landing **fails the mobile LCP gate as-built**: pinned
Lighthouse mobile gave median LCP **3548 ms** (2939 / 3548 / 3591) against a gate
of **<2500 ms median and no single run >2700 ms**.

Rev 1–3 assumed image debt was the lever. **Step 1 measured it and both
assumptions were wrong.** The LCP element is the **age-gate consent modal**; the
CLS is the **deferred motion init blanking already-painted content**. Neither is
an image problem, and **both reproduce identically on production `main`** — the
redesign caused neither.

## Step 1 findings (executed — evidence, not hypothesis)

Attribution harness: `puppeteer-core` driving installed Chrome under gate-matching
conditions (412×823 @ DPR 1.75, Moto G Power UA, CPU 4×, applied throttling
equivalent to Lighthouse `mobileSlow4G`, cold cache + fresh profile per run).
Attribution only; step 7 is the sole pass/fail timing source. Coherence check: the
harness cold median (3540 ms) matches the pinned Lighthouse baseline (3548 ms) to
within 8 ms.

### F1 — LCP is the age gate, not any image (2144 ms of it)

| Condition | Median LCP | LCP element |
|---|---|---|
| Cold, gate opens (what Lighthouse measures) | **3540 ms** | `<p>` inside `#age-gate` |
| `localStorage.site_consent_v1` pre-seeded | **1396 ms** | `h1.hero-headline` |

`#age-gate` (`app/static/index.html:867`) ships with `hidden`;
`app.js::wireAgeGate` (`app/static/js/app.js:1318`) unhides it whenever
`site_consent_v1 !== "yes"`. **Lighthouse uses a fresh profile every run**, so the
flag is never set and the modal opens on every measured load, painting a large
centred text block at ~3.5 s that outsizes the hero headline (35708 px² vs
35112 px²) and takes LCP.

### F2 — CLS 0.906 is deferred motion blanking painted content
Bisection: blocking `landing-motion.js` moves CLS **0.9491 → 0.0432**, LCP
unchanged at 3480 ms. `landing-motion.js:75-88` adds `.reveal-on-scroll` to five
sections then `motion-ready` to `<html>`; CSS sets `opacity: 0`. Those sections
**paint at FCP and are then blanked**, 44–82 ms after whichever of `app.js` /
`landing-motion.js` lands last — hence the timing-variable 0.949 / 0.906 / 0.

**F1 and F2 are independent** — each bisection left the other metric unmoved.

### F3 — the rev 1–3 hypotheses, as measured
`campus-quad.jpg` is **not** the LCP lever: real debt (285 KB, Low priority,
1412→3939 ms, starving the `VeryHigh` font requests) but not the LCP element. Its
`<img>` has `sizes` but **no `srcset`**, so `sizes` is inert. Measured
`.proof-photo` box: **380 px CSS at 412 vw** (~665 px at DPR 1.75) vs **1200 px**
shipped. **Hero preload dropped** — LCP is text.

### F4 — pre-existing production debt, not redesign debt
`ensurecollege.com` (`main`) measures median LCP **3544 ms**, same age-gate
element, same CLS **0.9491**. **The ADR 0001 fallback would have cost the redesign
and fixed nothing.**

### F5 — measurement confounds
The preview injects a never-completing `/_next-live/feedback/feedback.js` toolbar
(present in the baseline too, so before/after on the preview stays valid); one prod
run spiked to 6068 ms.

### F6 — constraints discovered in Codex round 1 (verified independently)
- **CSP forbids inline script.** `app/main.py:78` sends `script-src 'self'` with
  no `'unsafe-inline'` and no hashes (`style-src` *does* carry `'unsafe-inline'` —
  that is how `_inline_css` works). There are **zero** inline `<script>` tags in
  the app today. Verified live on the preview response header.
- **`/` is served `Cache-Control: no-cache`**, so a per-visitor decision computed
  at request or paint time is not contradicted by caching.
- **`init()` awaits `/vocabulary` before `wireAgeGate()`**, so today the gate
  cannot be wired until that fetch resolves.
- **The e2e `page` fixture is an override** (`tests/e2e/conftest.py:67-84`) that
  always navigates to `/` and clicks through the gate — it structurally cannot
  observe cold first paint or `app.js`-failure behaviour.

## Approach

Both fixes share one principle: **never change what has already been painted.**

### 2. LCP: one self-contained consent boot that owns the gate
Josh's call: decide consent before first paint. Rev 4 proposed a bare inline
`<head>` script that only set a class; **that is CSP-blocked (F6) and leaves the
modal inert until `app.js` finishes `/vocabulary`**. Rev 5 replaces it with a
single boot script that owns the gate end to end.

**Behaviour**
- Reads consent through a **storage-safe helper** (`try/catch`; any throw ⇒ treat
  as *not consented*), sets a class on `<html>` (e.g. `has-site-consent`).
- `#age-gate` **drops `hidden`**; CSS hides it for consented visitors
  (`html.has-site-consent .age-gate { display: none; }`).
- **Wires the gate itself** — checkbox `change`, Continue `click`, and the hide —
  with **no dependency on `app.js` or `/vocabulary`**. This closes both the
  `app.js`-fails case and the normal-path window where the modal is painted but
  dead (F6).

**Boot timing — the mechanism that makes "never dead" true.** A synchronous
`<head>` script runs *before* `#age-gate` (`index.html:867`) is parsed, so it
cannot attach listeners to those elements or focus them directly. Specify:
- **Delegated handlers attached to `document` immediately**, in the head script —
  `change` and `click` are captured by document-level delegation regardless of
  whether the target exists yet, so the gate is **interactive from the instant it
  paints**. This, not element-bound wiring, is what closes the dead-modal window.
- **Focus + inertness applied at the earliest moment the gate exists** — a
  `MutationObserver` hit or `DOMContentLoaded`, whichever fires first — since
  those genuinely require the node. State that focus may therefore land a few ms
  after the gate's first paint, and that this is acceptable where a dead *button*
  would not be.
- **Alternative considered:** move the gate markup to immediately after `<body>`
  so it parses early and can be wired and focused directly. Cleaner for focus
  order, but it is a real DOM restructure; the contract tracks ids not order, so
  it is permitted — the builder may choose it if delegation proves awkward. Record
  which was chosen.

- On accept: persist via a **storage-safe setter**. **Storage-blocked fallback is
  defined narrowly and consistently:** if `localStorage` throws, hide the gate for
  the **current document only** and do **not** silently persist anywhere else. No
  second storage mechanism and no cookie — a cookie would be a new persistence
  category requiring a privacy-policy update, which this plan does not cover.
  Consequence, accepted and documented: a storage-blocked visitor sees the gate
  again on the next navigation. **Test:** in a storage-blocked context, accept →
  navigate → assert the gate reappears (expected behaviour, not a bug).
  **Signed off by Josh, 2026-07-20**: current-document-only confirmed, over a
  `sessionStorage` or cookie fallback.
- `app.js::wireAgeGate` is reduced or removed so there is exactly **one** owner of
  the gate lifecycle. `app.js:1319` and `:1331` must stop reading/writing
  `localStorage` unguarded.

**CSP (blocking prerequisite)**
- Permit exactly this script via a **`sha256-` hash** in `script-src` — never
  `'unsafe-inline'`, never a blanket relaxation.
- **Drift-proof by construction:** the hash must be derived from the actual served
  bytes (compute at import/response time from the single source of truth), not
  hand-maintained. A hand-copied hash is a lockstep hazard on par with `?v=`.
- **Where the header is applied (verified).** `_SECURITY_HEADERS`
  (`app/main.py:73`) is static and `SecurityHeadersMiddleware` only **`setdefault`s**
  it (`app/main.py:158`); `serve_index()` currently returns just `Cache-Control`
  (`app/main.py:340`). So: **`serve_index()` sets a landing-specific
  `Content-Security-Policy` derived from the bytes it just inserted**, and the
  middleware's `setdefault` preserves it untouched. This fits the function's
  existing `html.replace()` shape. Every other route keeps the global CSP.
- **Required tests:** (a) extract the inline script from the served `/`, hash it,
  and assert the **served** `/` CSP admits *that* hash — a test that cannot drift;
  (b) `script-src` on `/` still contains no `'unsafe-inline'`; (c) a non-landing
  route still returns the global CSP, proving the override is scoped.
- A same-origin external `consent-boot.js` was considered and **rejected**: a
  render-blocking `<head>` request costs ~one RTT (~560 ms at the gate's latency),
  which defeats the purpose.

**Accessibility (first-paint modal)**
The gate is a plain `div[role=dialog][aria-modal=true]` near the end of the DOM
(`index.html:867`), not a native `<dialog>`. Painting it before JS wires it means
keyboard/SR users can reach content behind it. Specify and test:
- focus moves into the dialog on first paint (and where it lands),
- background is inert (`inert` attribute or equivalent) while the gate is up,
- `Tab` stays trapped; define `Escape` behaviour explicitly (a consent gate
  arguably must **not** be Escape-dismissible — state the choice),
- Playwright keyboard assertions for **both** cold and consented states.

**Contract**
`tests/dom_contract.json` tracks `ids` / `selectors` / `element_types` /
`emitted_classes`; `age-gate`, `age-gate-agree`, `age-gate-continue` stay. It does
**not** track `hidden`, so removing that attribute needs no manifest change — but
its silence proves nothing, so the assertions above are mandatory. Any new
`<html>` class is a deliberate `emitted_classes` addition.

**Tests**
- Split the e2e fixtures (F6): keep the auto-dismissing `page` for existing suites,
  add a **cold** fixture that does not dismiss, plus an **accepted** fixture.
- **"Visible on first paint" cannot be proven at `domcontentloaded`** — that can
  pass after scripts ran. Prove it with request-level markup/CSS assertions **plus**
  a browser test that **blocks `/static/js/app.js`** and still observes the correct
  initial gate state *and* a working dismiss.

### 3. CLS: don't hide what is already on screen
Culprit category is **deferred motion** (F2), so the fix lives in
`landing-motion.js` — not `app.js`, not the DOM contract.
- Before applying `.reveal-on-scroll`, **skip targets already in or near the
  viewport** and mark them revealed.
- **A one-shot `getBoundingClientRect()` at init is not sufficient** (Codex, F8):
  compute **after scroll restoration and a first `rAF`**, and use a **near-viewport
  margin** rather than strict intersection, so restored scroll, hash navigation
  (`/#browse` is a real link in the footer), late layout, and resize/orientation
  cannot turn a "not intersecting" target into a visible-but-hidden one.
- Preferred over adding `motion-ready` before paint, which would fix the flash but
  leave above-fold content invisible forever if the reveal never fires.
- **Browser CLS assertions** for: cold top load, hash/restored scroll, and mobile
  resize/orientation.
- Residual 0.0432 (`.hero-demo` / `.hero-copy` at ~1.5 s) is in-budget; revisit only
  if the post-fix number misses <0.1.

### 4. `campus-quad.jpg` — byte cleanup (demoted from LCP lever)
Worth doing (it starves the link, F3) but **not** counted on to move LCP.
- **Generate with a committed generator, not an undocumented offline step.** No
  `cwebp`/ImageMagick/ffmpeg on this box, but **Pillow 12.3.0 with WebP support is
  already in `.venv`** — so add `scripts/` generator run via
  `.venv/Scripts/python.exe`, and record the exact invocation here and in the log.
  This retires the plan's "no repo image pipeline" risk instead of restating it.
- Convert to **`srcset` + measured `sizes`**; sole source of truth is F3's measured
  box (380 px CSS at 412 vw → `calc(100vw - <.main padding>)` at mobile, not the
  current inert `100vw`). Emit 1× and 2× candidates.
- **WebP only, not AVIF** — 285 KB → ~30–45 KB is already ~8×.
- Keep `width`/`height`, `loading="lazy"`, `decoding="async"`.
- The DOM contract does not track this image: add **explicit** request + browser
  assertions for `picture`/`source`/`img`, resolved `currentSrc` per viewport,
  rendered dimensions, `alt`, `loading`, `decoding`.

### 5. Reclaim the `style.css` preload bandwidth (landing only)
Unchanged, but **now expected to be marginal** — hygiene, not a lever. Change the
`style.css` `preload` (`index.html` line 27) to **`prefetch`**; verify in the
waterfall that it lands at Lowest priority off the LCP path; if it still competes,
**remove the landing hint entirely**.

### 6. Cache-bust in lockstep
Bump `?v=` together across `app/static/index.html`, `journey.html`,
`privacy.html`, `terms.html`, `app/templates/base.html`, `tests/test_pages.py`,
plus new `campus-quad` variant URLs and the prefetch URL. **Extend
`tests/test_pages.py`** (today it only checks app CSS/JS version strings) to parse
`src`, `srcset`, and `href`. Vendored `three.min.js` / favicon stay exempt.

### 7. Prove, then re-measure (the gate)
- **Proof suite green:** `tests/ --ignore=tests/e2e` + `tests/e2e` + DOM contract +
  `validate_dataset.py`. Frontend changes are proven in the **browser** suite.
- **Guard the inlined-CSS non-negotiable:** `/` still contains the inline `<style>`,
  no `rel="stylesheet"` for landing CSS, only the intended hints — the head is under
  active edit this rev.
- **Re-measure — one authoritative protocol.** Pinned **Lighthouse `@11`** (11.7.1
  installed; the baseline version), `--form-factor=mobile`, default simulated
  throttling, headless Chrome, **cold cache per run**, exact preview URL + deployed
  SHA. **Median of 5. GO** iff median LCP <2500 ms **and** no run >2700 ms.
- **LCP attribution after the fix is mandatory, not optional** (Codex, F9): record
  the **LCP element**, render/load breakdown, and trace or screenshot for **all five
  runs**, or a companion gate-matched harness run. A passing number with an
  unexpected element is not a pass.
- **Pin the immutable deployment URL, not the branch alias** — the alias moves on
  the next push and would silently invalidate the comparison.
- Baseline: preview `https://scholarship-matcher-f6ddpldsj-josh-s-team2.vercel.app`,
  SHA `bdacbae`, deployment `dpl_CjSfWprY2UWdfu2qnQBxMng92Xm3`.

**Corrected prediction (rev 4's was wrong).** Rev 4 predicted LCP would become
`h1.hero-headline` at ~1396 ms. That is unsound: 1396 ms came from *suppressing*
the gate, but the fix **paints the gate earlier** rather than removing it. For a
cold Lighthouse run the honest prediction is:
- the gate is **visible at first paint**;
- the LCP element **remains `#age-gate p`** (it still outsizes the headline);
- LCP lands **at ≈FCP, ~1400–1700 ms**, i.e. well under 2500 ms.
The 1396 ms consented run is a **separate comparison only**. If the post-fix
element is neither `#age-gate p` nor the headline, stop and re-attribute.

**Prediction-fail rule (the prediction must bite, not just be recorded).** The GO
rule alone would accept a 2499 ms median, which is ~800 ms worse than this fix
predicts and would mean something else is wrong. So, independently of the release
gate: **if cold median LCP exceeds 1800 ms, or the LCP−FCP delta exceeds 250 ms,
stop and re-attribute even if the gate technically passes.** A pass we cannot
explain is not a pass.

## Key decisions & tradeoffs

- **Fixes land on `redesign/forest-journey`; prod benefits on merge.** Josh's call
  with F4 known.
- **One inline consent boot owns the gate, admitted by a derived CSP hash** —
  buys a 2.1 s LCP win, no pop-in, and a modal that works before `app.js`; costs a
  first-ever inline script and a CSP exception that must be drift-proof.
- **CLS fixed by skipping in/near-viewport reveal targets after rAF + scroll
  restoration** — contract-safe, degrades safely if motion never initialises.
- **`campus-quad` demoted to byte cleanup; hero preload dropped** (F3).
- **WebP via a committed Pillow generator**, not an offline step.

## Risks / open questions

- **The CSP exception is the sharpest risk this rev.** A hand-maintained hash
  silently breaks the gate the first time the snippet changes by one byte. The
  derived-hash + self-verifying test requirement is mandatory, not advisory.
- **Painting the gate at FCP changes the first impression** for every new mobile
  visitor: the first thing rendered is a consent modal over the hero. Accepted as
  correct for a consent gate and strictly better than a 3.5 s pop-in — but it is a
  visible **product** change, not a pure perf change.
- **Consent semantics must stay equivalent.** Moving ownership out of `app.js`
  must not change *what* is consented to or when it is recorded.
- **Storage-blocked browsers: gate hides for the _current document only_.** Rev 5
  said "current page" in step 2 and "for the session" in this section — different
  consent semantics, now resolved to the narrower one. Such a visitor is
  re-prompted on each navigation. Chosen over a cookie or a second storage
  mechanism because either would be a new persistence category needing a
  privacy-policy update. **Signed off by Josh, 2026-07-20** — a consent decision,
  taken deliberately rather than as a side effect of the perf work.
- **Preview-only toolbar confound** (F5).

## Out of scope

- **Cherry-picking these fixes to `main` ahead of the redesign** — declined this
  rev; revisit after the gate passes.
- `students-walking.jpg`, `campus-hall.jpg` — not on the landing.
- **Phase 1 fan-out** — gated on this passing.
- Reducing inlined CSS / changing `_inline_css` — F1 removes the motivation.
- Matcher gates/scoring, auth, digest cron, dataset, dormant AI — untouched.
- Whether the age gate should block at all (vs a dismissible bar) — a product
  question Josh deferred; this rev keeps the existing blocking behaviour.
