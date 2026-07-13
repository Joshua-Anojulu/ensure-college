# Plan Review Log: Niche-requirement special checks + honest guidance placeholders

Act 1 (grill) complete — plan locked with the user. MAX_ROUNDS=5.
PLAN_FILE=docs/2026-07-12-niche-requirements.md

Grill decisions:
- Special-check everything; no new profile questions (privacy posture). First-gen profile question dropped.
- Guidance gap fixed with honest placeholder; verified prompt-expansion pass queued separately.

## Round 1 — Codex (gpt-5.5 via -c override; config's gpt-5.6-sol needs a newer CLI than 0.142.4)

VERDICT: REVISE — 10 findings:
1. tests/test_dataset.py asserts real-catalog warnings == [] — heuristics must be catalog-clean; test warnings with synthetic fixtures.
2. Guard exists only in scholarship audit; plan covers programs/competitions — extract shared guard, call from all three audits.
3. Several survey candidates are not hard gates (Burger King, JKC, Scholastic, AIGA, MALDEF, Point/ASA "allies", Wharton) — explicit skip list with rationale before encoding.
4. identity_or_status conflicts with existing family_or_affiliation usage (already holds first-gen/family ties) — define kind-reuse rule before adding kinds.
5. "Special check" is not an API tier (match_tier stays strong|possible; frontend groups by requires_special_check) — fix plan language/tests.
6. Loader concatenates inline+sidecar special requirements without dedupe — add duplicate guard.
7. buildPromptBlock change affects checklist rows AND reuse map; checklist rows sit inside <label> — test both surfaces, confirm no checkbox toggling.
8. Opportunity-page context is built in app/seo_pages.py, not just detail.html — pass special_requirements explicitly + rendering test.
9. Plan claimed the special-check lane is "collapsible" — it is a plain section; remove assumption, glance-check weight.
10. Heuristics need negative-pattern tests ("regardless of immigration status", "LGBTQ+ and allies").

### Claude's response
Accepted all 10; verified #1 (tests/test_dataset.py:25) and #4 (family_or_affiliation holds 15 entries incl. first-gen; military_affiliation holds 8) against the repo before revising. Plan updated: kind-reuse rule (reuse military_affiliation/family_or_affiliation; new kinds only for identity/status, program content, activity/lifestyle; no data migration), skip list with named likely-skips, shared validator guard across all three audits with synthetic-fixture + negative tests and catalog-clean constraint, loader dedupe guard, seo_pages.py context + test, both-surface browser verification incl. label-forwarding check, API-contract language fixed (requires_special_check flag, not a tier), collapsible claim removed. Nothing rejected.

## Round 2 — Codex

VERDICT: APPROVED. Prior findings materially addressed. Three non-blocking hygiene notes:
1. Add placeholder-text wiring assertion to tests/test_essay_prompts.py (not just browser verification).
2. Dedupe guard should compare normalized (kind, label), not exact strings.
3. If CSS changes, bump base.html cache-bust too, not just index.html.

### Claude's response
All three folded into plan step 7. Converged in 2 rounds.

## Act 3 — Build

### Round 1 — Codex build (gpt-5.5, --yolo, user-authorized)
Implemented the full spec in one round: 3 new SpecialRequirement kinds; 23 entries encoded (21 scholarships sidecar + 2 programs + 1 competition inline), 9 skipped with rationale (JKC/Taco Bell/Scholastic military mentions = context or alternate path; AIGA/MALDEF = inclusive immigration wording; Point/ASA-Pride = "and allies"; Burger King = alternative applicant group; Wharton = sports as subject matter); shared niche-requirement validator guard across all three audits + trap phrases + normalized (kind,label) duplicate errors; special requirements rendered on opportunity pages via seo_pages context; "Essay prompts not yet verified" placeholder in buildPromptBlock; 7 new tests; asset bump v=20260712-2. Deviation: Codex could not browser-verify (no browser backend) — left to Claude.

### Claude's verdict
Full diff read. Data honesty verified entry-by-entry: all 23 encodings restate verified description prose, no invented facts; all 9 skips justified. Proof run independently: 345 tests pass (was 338), validator no structural errors, zero new-guard warnings on live catalog (2 pre-existing competition warnings remain), special-check lane 116 -> 134. Browser-verified: opportunity page renders "Special eligibility to verify" (SWE); saved checklist + essay reuse map both show the unverified-prompts note (3 each on probe account); clicking the note does NOT toggle the checklist checkbox; no console errors. Styling reuses existing .special-requirements classes. PASS — no fix rounds needed.

---

# Plan Review Log: UI redesign (Forest Light), 2026-07-13
Act 1 (grill-with-docs) complete - plan locked at docs/2026-07-13-ui-redesign.md, no CONTEXT.md changes needed. MAX_ROUNDS=5.


## Round 1 - Codex (gpt-5.5, read-only)
VERDICT: REVISE. 20 findings, highlights: app.js already has a window scroll listener (wirePageMotion, line 391) contradicting the plan's own rule; #profile-form is a live form (CTA must anchor, not replace); #browse-catalog-btn must stay a button; 181-selector extraction misses required data-view values and JS-EMITTED class names (CSS contract); plan file paths were wrong (app/templates/, app/static/index.html); amber #c98d2c fails 3:1 on canvas for focus/indicators; ScrollTrigger pinning CLS + refresh discipline; font-swap CLS needs metric overrides; byte budget demanded; grain overlay paint cost; reduced-motion/no-JS must not blank content; keyboard pass through pinned sections; keep photo alt; dash sweep too broad for consent/legal strings; CSP change needs explicit absence tests + asset 200 checks; wanted Playwright smoke; og-image must ship same release.

### Claude's response (rev 2)
Accepted 19 of 20: frozen DOM map section added (queried selectors + data-* values + emitted-class CSS contract + element types), new tests/test_dom_contract.py, paths corrected, amber split into --accent-deep (AA text/indicators) vs decorative --accent with forest focus ring, ScrollTrigger init/refresh/mobile-pin rules, font metric overrides + preload limited to 2 files + byte budgets, grain measured-or-dropped, visible-by-default .motion-ready gating, keyboard-only pass added, alt kept, dash sweep rescoped (legal excluded, app.js strings reviewed individually), CSP absence tests + font 200 tests, og-image regenerated in-release, sanctioned app.js touch replacing the scroll listener with sentinel IntersectionObserver.
REJECTED: Playwright CI infra (new dependency + runner scope this repo never carried); mitigated by Claude-driven scripted browser smoke on the Vercel preview covering the identical checklist; Playwright to Tier 3 backlog.

## Round 2 - Codex
VERDICT: REVISE. Playwright rejection accepted conditional on a merge-blocking evidence log. 8 residuals: DOM-contract test must cover the full 181-selector manifest + element types (not just IDs/data-view/field names); emitted classes must be harvested from ALL assignment patterns or an explicit manifest; smoke run needs a dated committed evidence log; add an opportunity-page SEO test (title/meta/canonical/JSON-LD/verification labeling); proof image lazy/responsive stance explicit; do not preload display weight on server-rendered pages; sans fallback metrics (not Georgia); Lighthouse mobile-throttled as the merge blocker.

### Claude's response (rev 3)
Accepted all 8: committed tests/dom_contract.json manifest (queried selectors + attributes + element types) with a hand-audited emitted-class section asserted against the stylesheet; smoke evidence log at docs/2026-07-13-ui-redesign-smoke.md, merge-blocking; test_seo_pages.py extended for an opportunity page; proof image stays lazy/async with reserved dims (hero is LCP, verified); base.html preloads body 400 only, display 800 preload is index.html-only; Arial/system-ui fallback metrics; Lighthouse mobile+desktop with mobile as merge blocker.

## Round 3 - Codex
VERDICT: APPROVED. All eight round-2 findings confirmed addressed (manifest-backed DOM contract, emitted-class extraction breadth, merge-blocking smoke evidence log, SEO test coverage, image treatment, preload scope, sans fallback metrics, mobile-first Lighthouse gate). One non-blocking doc-hygiene note: rev label corrected to Rev 3.

Converged in 3/5 rounds. Awaiting user sign-off before any code.

## Act 3 - Build (Codex types, Claude verifies)

### Round 0 - Codex build (thread 019f5a2d-922a)
Full Forest Light implementation: 21 files (tokens, fonts self-hosted, landing recomposition, motion layer, CSP tightening, DOM-contract manifest + tests, og-image via Pillow). Reported 364 tests green; deviations: 184 selectors locked (not 181), preview/Lighthouse deferred, no subagent.

### Claude's verdict (round 0)
Scope exact, tests verified independently (364 passed; validator warnings pre-existing, datasets untouched). Code review: CSP/app.js/base.html per spec; tokens hex-for-hex. Browser review found 3 critical defects (hero IO+GSAP double-animation leaving preview form unusable; H1 3-line wrap colliding with preview panel; proof-band photo escaping section) + 4 minor (numeric eyebrow prefixes pre-existing, dead marker code, eager decode of lazy image on mobile, duplicate count-pop keyframes).

### Round 1 - Codex fixes (user-authorized resume)
All 7 items fixed: hero out of IO targets w/ 600ms font-gate race + transform-only entrance; H1 shortened + clamp reduced; pin dropped for contained scrub; eyebrows de-numbered; marker code removed; decode desktop-gated; keyframes deduped. 364 tests green.

### Claude's verdict (round 1) + takeover fix
6.5/7 verified fixed in browser. Residual: proof-band full-bleed used transform: translateX(-50%), which the scroll-reveal transform overrides, shifting the band half a container right (copy off-screen). Fix rounds spent; Claude applied the 2-line fix directly (margin-left: calc(50% - 50vw), no transform) per takeover rule. Re-verified in browser: hero instant + 2 lines + no collision; proof band contained with copy visible; preview flow returns real matches end-to-end; 364 tests green run by Claude.

### Design escalation pass (Claude, post-review by Josh)
Josh judged the first build "super basic, not complex or modern" (correct: it shipped at variance ~5 vs the 9/8 brief; the pointed-to taste-skill was byte-identical to the one already installed, so this was execution, not spec). Claude rebuilt the landing to the dials: oversized editorial hero type (clamp 3.2-5.9rem) spanning the grid, preview panel pulled up into the headline zone with resting -1.2deg rotation (straightens on focus-within) and deep layered shadow, film grain overlay, asymmetric numbers band with dominant forest cell + GSAP count-up, difference section rebuilt as a CSS sticky-stack with scale scrub (forest/paper/green-tint cards), decorative hairline removed, hero centering min-height dropped.
Two defects found and fixed during browser verification: (1) the SVG feTurbulence grain overlay stalled Chrome's compositor for tens of seconds (screenshot timeouts, frozen reveals) - replaced with a pre-rasterized 128px noise PNG (app/static/img/grain.png, Pillow-generated); (2) stack scrub animated opacity, making overlapping cards translucent with colliding text - now scale-only. Also recovered from a PowerShell UTF-8 corruption incident (Get-Content/Set-Content re-encoding) by restoring from git and re-applying via encoding-safe edits; tests could not catch it because the test file's own dash literals were equally corrupted.
Proof: 364 tests green (run by Claude), full browser pass on localhost. Asset version 20260713-2.

### Elevation pass 2 (Claude, per Josh: "match the level throughout")
Hero left dead zone fixed (headline-to-copy gap tightened, copy pulled under headline, bottom padding cut). The tilt/stack language carried through every section: numbers band is three stepped cards with the forest cell interlocking up into the hero; the campus photo gets the hero panel treatment (tilted bezel frame breaking its band edges); profile form gains a rotated stacked-paper backdrop + inner bezel + mono step numerals; footer rebuilt at display scale (ghost wordmark, asymmetric layout, mono uppercase links, middle-dot separators removed per dot-rationing rule); primary buttons gain hover lift physics; brand selection color. Mobile resets for all of it.
Verification note: recurring CDP screenshot timeouts were isolated to GSAP's persistent ticker starving Chrome frame CAPTURE on this box only; page itself stays responsive (JS live, zero long tasks) so no code change needed. 364 tests green. Asset version 20260713-3.
