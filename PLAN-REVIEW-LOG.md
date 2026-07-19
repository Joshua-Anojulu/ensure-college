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

---

# Plan Review Log: Deferred security hardening, 2026-07-14
Plan: docs/2026-07-14-security-hardening.md. MAX_ROUNDS=5. Codex gpt-5.5, read-only, thread 019f5fea-ee3e-70e1-85f6-731b23248792. Full round-1 critique preserved at tmp/codex-sec.txt.

## Round 1 - Codex
VERDICT: REVISE, 10 findings, all accepted:
(1) BackgroundTask for reset email is not durable on @vercel/python (waitUntil is Node/Edge only) AND the rev-1 shape inverted the timing oracle (known accounts fast, unknown slow). (2) "per-user guard prevents double sends" was false — mark-after-send means a timeout between Resend accept and commit re-sends next run; alerts have the same shape. (3) Bounded batch without a durable cursor can permanently starve the same skipped users, and weekly cadence makes "next tick" mean next week. (4) "unbounded" was inaccurate; maxDuration is a backstop, not the reliability mechanism, and must target api/index.py. (5) Login dummy-bcrypt fix fine but threat model dishonest — signup 409 still enumerates; say so. (6) Rate limiting can't be cited as a mitigation (in-memory fallback void on serverless, fails open on Upstash errors). (7) Unsubscribe POST must accept the token in the query string (RFC 8058 clients POST to the List-Unsubscribe URL itself), escape embedded tokens, and add headers to BOTH digest and alert emails. (8) CORS: don't overclaim — property is "no credentialed cross-origin reads," and production detection must include VERCEL_ENV. (9) href="#" fallback for bad schemes is a lie by affordance — render plain text, no link. (10) Missing item: CSRF posture for session-cookie mutations.

### Claude's response (rev 2)
Accepted all 10, nothing rejected. Reset: dropped BackgroundTask entirely — token write + send stay inline, both branches padded to a shared response floor; claims "signals removed," not constant time. Cron: Resend Idempotency-Key (reminder:{user_id}:{period} / alert:{user_id}:{period}) makes retries harmless, kept mark-after-send deliberately (missed reminder worse than duplicate for a deadline tool), bounded batch + done flag + cron moved weekly→daily so cut-off tails drain next day, maxDuration on api/index.py as backstop only. Signup-enumeration honesty statement added; rate limiting explicitly disclaimed as a control + startup warning when prod lacks Upstash. Unsubscribe: GET renders escaped confirmation form, POST accepts query-string token + form-body fallback, List-Unsubscribe + List-Unsubscribe-Post headers on both email kinds, identical response for bad tokens. CORS gated on is_production_deploy() OR VERCEL_ENV=="production" with the honest reads-only claim. Bad schemes rejected at model+validator and rendered as plain text (no link, no "#"). New item 7: CSRF posture — SameSite=Lax + JSON bodies documented per-route, plus Origin/Referer allowlist check on unsafe methods as defense in depth.

## Round 2 - Codex
VERDICT: REVISE, 6 remaining findings, all accepted. Codex independently verified the Resend Idempotency-Key claim against Resend's docs (real, 24h retention, HTTP header; custom email headers are separate body fields) before critiquing its use:
(1) "network-latency signals are removed" still an overclaim — a floor below the send path's worst case (urlopen timeout=10s) leaves known accounts slower; weaken the claim or set an absurd floor. (2) Daily cron still has no durable cursor — the same front-of-order skipped users can consume REMINDER_BATCH_LIMIT every run; MIN_DAYS_BETWEEN_SENDS is not a cursor. (3) Daily cron changes digest cadence: Monday's recipient is re-eligible Saturday (MIN_DAYS_BETWEEN_SENDS=5); "re-sends nobody" is false. (4) alert:{user_id}:{period} key too coarse — a legitimate second batch of alerts in the same period would be swallowed; key must identify one logical email (job + user + period + item-ids hash). (5) "no duplicates" contradicts the admitted 24h idempotency window. (6) "every mutating endpoint takes a JSON body" is false (logout has no body; new unsubscribe POST takes query/form) — document actual route classes instead.

### Claude's response (rev 3)
Accepted all 6. The load-bearing change: **cron delivery guarantees (old item 6) SPLIT OUT into their own future plan** — doing it right needs a durable outbox/cursor = a new table = a migration, and migrations in this repo do not auto-apply (CLAUDE.md non-negotiable: a schema plan must state how it reaches Neon). Everything review established about the cron (send-then-mark window, cursor need, cadence-vs-drain distinction, 24h idempotency limit, logical-email key shape) is recorded in the plan for that successor. This plan ships items 1-5 + CSRF only — self-contained, no schema change — with maxDuration on api/index.py as an interim backstop labelled as such. Reset claim weakened to "removes the trivial fast/slow split," residual leakage accepted and documented. CSRF section now documents the five real route classes in a table (JSON-body blanket claim removed).

## Round 3 - Codex
VERDICT: APPROVED. "No blocking findings in Rev 3." The scope split resolved the cron objections; reset/CORS/unsubscribe/URL-scheme/enumeration/rate-limiting/CSRF all "stated with the right threat boundaries." Three build-time cautions to honor during implementation: (a) the reset response floor must apply on error paths too, including EmailDeliveryError, or provider failures produce a sharper known-account signal; (b) the Origin/Referer check needs explicit tests for same-origin, allowed production origin, missing-origin-with-same-origin-referer, and hostile-origin-with-session-cookie; (c) use the actual Vercel function key api/index.py with a concrete supported maxDuration value.

Converged in 3/5 rounds. Awaiting user sign-off before any code.
(Session note: the tab hosting the original session closed mid-loop; a resumed session re-submitted rev 2 concurrently, producing a duplicate 4th turn that also returned no blocking findings — consistent with the round-3 approval. Full round transcripts in the Codex rollout, thread 019f5fea.)

## Act 3 - Build (Codex types, Claude verifies)

### Round 0 - Codex build (thread 019f5fff-83b5)
Full implementation of rev 3: 26 files. CORS production-gated (_is_production_runtime = is_production_deploy() or VERCEL_ENV==production); CsrfOriginMiddleware (Origin, then Referer, allowlist = hardcoded https://ensurecollege.com + request-host origin + PUBLIC_APP_URL; missing-both allowed for non-browser clients); login dummy-bcrypt (module-level $2b$12$ hash, cost-matched to gensalt default); reset floor 0.25s via try/finally covering success, unknown-email, config-503, and EmailDeliveryError-503 paths; unsubscribe split GET (escaped confirmation form, zero DB access) / POST (query-string token per RFC 8058 + urlencoded form fallback, identical completion page for bad tokens); List-Unsubscribe + List-Unsubscribe-Post as Resend body-payload headers on digest AND alert emails, token now percent-encoded; shared validate_http_url_string on all three lanes' MatchResult.verification_source_url (dataset-side fields were already HttpUrl); validate_dataset.py reports ValidationError as ERRORS + exit 1; app.js httpUrlHref renders non-http(s) sources as plain text, no link; Upstash warning fires once on any production deploy incl. VERCEL_ENV; vercel.json maxDuration 60; asset v bumped 20260714-1→-2 in all six lockstep locations. Tests: +20 covering the four-case CSRF matrix, floor on both branches, GET-no-mutate/POST-mutates, generic bad-token response, header payloads (and that they are NOT transport headers), CORS absence under production config, bad-scheme model/validator/browser rendering. Reported 384+41 green, no deviations.

### Claude's verdict (round 0)
Diff read in full; spec-faithful, all three round-3 build-time cautions honored (floor on EmailDeliveryError path; four-case Origin test matrix; api/index.py function key). ONE REAL DEFECT Codex's report missed: it added a functions block to vercel.json while keeping the legacy builds block — Vercel rejects configs with both (documented conflicting-configuration error), so the next deploy would have failed. Claude fixed directly per the anti-trivia rule (dropped builds; api/*.py is zero-config @vercel/python, which the functions block then configures). Caveat recorded: with builds gone, buildCommand may execute for the first time — the config MUST be proven on a throwaway preview-branch deploy before reaching main (this repo's vercel.json has bitten before: the 2026-07-06 static-CDN attempt). Proof run independently by Claude: 384 request + 41 e2e green (venv python), validate_dataset.py exit 0 with pre-existing notes only. No fix rounds spent. Awaiting diff sign-off + preview-deploy proof.

---

# Plan Review Log: quick-apply rule (docs/2026-07-17-quick-apply-rule.md)
Act 1 (grill-with-docs) complete — plan locked, CONTEXT.md updated with the
**Quick apply** term. MAX_ROUNDS=5. Codex model gpt-5.5 (config pins
gpt-5.6-sol; overridden per the box's known-good setting), read-only.

## Round 1 — Codex — VERDICT: REVISE
Eight findings. Verbatim critique in tmp/codex-verdict-qa.txt. Summary:
1. Panel is fed by lastResults/lastPrograms/lastCompetitions (all matches),
   not saved — glossary said "saved opportunity". VALID.
2. No cache-bust `?v=` bump for a frontend JS change — CLAUDE.md violation. VALID.
3. Unverified fallback + count copy: line 2178 asserts "3 or fewer
   requirements" for items line 2117 admits with empty requirements. VALID.
4. `activity_or_lifestyle` rows not honest Special checks; service commitment
   is a post-award stakes term, debt/clearance are legal/status gates. VALID (point).
5. TBP row omits the candidate-initiated-by-June-1 path. VALID.
6. "All three kinds": guard works (programs/competitions serialize the flag),
   but special_requirements.json is merged only by load_scholarships(). VALID.
7. One e2e assertion too thin for 3 payload kinds + count-copy + fallback. VALID.
8. Plan self-contradicts ("two verified rows" then four); only Nurse Corps
   reaches the panel (NHSC/SMART essay-required, TBP 4 steps). VALID.

### Claude's response (arbiter) — rev 2
Verified every code claim before acting:
- #1 confirmed: collectQuickApplyCandidates() walks the match sets, no saved
  filter. Fixed the CONTEXT.md glossary entry ("a match … not the saved set").
- #6 confirmed: loader.py:29-35 merges the sidecar only for scholarships;
  program_matcher.py:211 / competition_matcher.py:212 set the flag from their
  own eligibility. Guard works for all three; sidecar note added.
- Decisive finding: 16 opportunities already carry a special-check row AND
  currently leak into the panel (Posse, SHPE, NSBE, IEEE, +12). The guard
  ALONE fixes all 16 with no dataset change — so the four rows rev 1 bundled
  in were never needed for the panel goal.
ACCEPTED: #1 (glossary), #2 (cache-bust added), #3 (count-copy split; fallback
kept per the VERIFY rule), #6 (sidecar note), #7 (per-kind + count-copy tests),
#8 (rows removed → contradiction gone).
ACCEPTED THE POINT of #4 by REMOVING all four special-check rows from the plan:
the guard needs none of them, and the enum-taxonomy question they raise (no
honest `kind` for federal-service/clearance/debt gates) is deferred to the
follow-up audit rather than forced. #5 (TBP) becomes moot — row deferred.
Net: rev 2 is guard + count-copy fix + cache-bust + glossary + per-kind tests.
No dataset rows. Re-submitting to the same Codex session.

## Round 2 — Codex — VERDICT: REVISE (round-1 blockers resolved)
Codex confirmed the four questionable rows are gone, cache-bust is in, glossary
matches the match-based panel, and the guard is mechanically sufficient for all
three match shapes. Three new precision findings, no design flaws:
1. The exact "16" leak count is not reproducible — a catalog scan finds ~20
   scholarship + 4 program + (Codex) 3 competition potential leaks, profile-
   gated. VALID.
2. Plan said it was "unconfirmed" whether special-check programs/competitions
   exist live — they do (Boys State, ALA Girls State; JSHS, Zero Robotics). VALID.
3. "verified rows" in the count-copy split is ambiguous against the existing
   `verified` (source-audited) field; the real flag is `candidate.unverified`. VALID.

### Claude's response (arbiter) — rev 3
Verified both factual claims before acting:
- #2 confirmed: programs/competitions carry special checks INLINE in their own
  eligibility.special_requirements (15 programs, 25 competitions), not via the
  sidecar — which is why my round-1 sidecar-only scan wrongly found 0. Codex's
  named examples are real.
- #1 confirmed and self-demonstrating: my honest cross-lane recount is 16/4/0,
  Codex's is 20/4/3 — the divergence proves an exact count is fragile. Removed
  the number from the Goal; the e2e fixture is now the source of truth.
ACCEPTED all three: dropped the exact count (qualitative + test as truth);
corrected the false "unconfirmed" and named live examples while keeping
constructed fixtures for test stability; respecified the count copy in code
terms (knownRequirementCount = !c.unverified, unknownRequirementCount =
c.unverified, incl. the K==0/U>0 case). No design change. Re-submitting rev 3.

## Round 3 — Codex — VERDICT: REVISE (single residual)
One finding: a stray "fixes 16 real leaks" survived in Key decisions (line 84)
after the count was removed from the Goal. Everything else from round 2
confirmed resolved. Fixed: "16 real leaks" -> "the existing real leaks". Re-submitting rev 3.1.

## Round 4 — Codex — VERDICT: APPROVED
Confirmed the stray exact count is gone and the approximate scan language is
explicitly non-authoritative with the fixture as source of truth. No new
blockers. Plan converged at rev 3.1 after 4 rounds. Awaiting Josh sign-off
before any code.

---

## Act 3 — Build (codex-build)

### Round 1 — Codex build
Codex (gpt-5.5, --yolo, run under Josh's hand after the classifier blocked
the launch and self-granting the permission) implemented rev 3.1. Report:
- app/static/js/app.js: guard `if (item.requires_special_check) return null;`
  as the first check in quickApplyCandidate; count copy split into
  knownRequirementCount (!c.unverified) / unknownRequirementCount (c.unverified),
  joined with "; ", empty-string when both zero.
- tests/e2e/test_e2e.py: new TestQuickApplies class — per-kind constructed
  fixtures (scholarship/program/competition) via page.route interception,
  asserting a requires_special_check item never renders; plus a count-copy
  test asserting the unverified clause shows and "3 or fewer requirements"
  does not. Refactored fill_profile_and_submit -> submit_profile_form + wrapper.
- Cache-bust 20260715-2 -> 20260715-3 across index/journey/privacy/terms.html,
  base.html, and tests/test_pages.py.
- No app/data/*.json changes (spec-compliant).

### Claude's verdict — VERIFIED, PASS
Ran all proof myself (Codex's pasted output is advisory):
- tests/ (request): 398 passed.
- tests/e2e (full): 47 passed (43 prior + 4 new).
- tests/test_dom_contract.py: 7 passed (DOM contract intact).
- scripts/validate_dataset.py: no structural errors (3 pre-existing warnings).
Read the full diff: app.js guard + count split are exactly per spec and match
surrounding style; e2e fixtures are self-contained (no live-catalog dependence)
as the plan required. Scope clean — 8 files, none under app/data.
Reconciled Codex's stderr showing "4 failed": that was an intermediate build
iteration; the final tree and my independent re-run are fully green. The
pre-existing ?v=20260713-3 on journey.html's favicon + vendored three.min.js
predates this change (git HEAD confirms) and is correctly untouched — the repo
bumps app assets per change while vendored assets follow a slower cadence, and
test_pages.py only checks app assets. Not a regression.
Awaiting Josh's diff sign-off before commit. Codex does not commit; Claude does.

---

# Plan Review Log: special-check audit (docs/2026-07-18-special-check-audit.md)
Act 1 (grill-with-docs) complete — plan locked; CONTEXT.md "Special check"
sharpened to the affirmative-vs-passive criterion. MAX_ROUNDS=5. Codex model
gpt-5.5 (config pins gpt-5.6-sol; overridden per the box's known-good setting),
read-only.

## Round 1 — Codex — VERDICT: REVISE
Confirmed non-flaws: kind is inert (not scored, not rendered); TBP row valid
(kind=membership, label 31, details 327<400) and gate supported by sponsor.
Four findings:
1. (High) Out-of-scope is load-bearing: nabj/ans/chick-fil-a state hard gates
   with no row, still surface as ordinary matches.
2. (High) nih-undergraduate-scholarship-program is special-checked ONLY for a
   "Service payback commitment" — exactly what the new criterion says belongs
   in checklist details. Contradiction on day one.
3. (Med) "action" is too broad; national-space-club-keynote-scholarship treats
   a video audition / finalist rounds (application work) as special eligibility.
4. (Med) Proof skips e2e, but CLAUDE.md's proof command names both suites.

### Claude's response (arbiter) — rev 2
Verified all three data claims before acting:
- F2 CONFIRMED and fixed IN-plan: NIH's row cites service payback (wrong) and
  kind=no_direct_application (also wrong), but NIH UGSP has a REAL pre-existing
  gate — disadvantaged background + exceptional financial need, an unverifiable
  status (demographics list empty, matcher never gates on it). Re-justified the
  row to kind=identity_or_status citing that gate; NIH keeps its lane place
  (no behavioral change), now for the right reason.
- F3 ACCEPTED: tightened CONTEXT.md — "pre-existing eligibility status or
  channel", with an explicit carve-out that ordinary application work (essay,
  video, audition/interview in the award's own selection) is NOT a special
  check. national-space-club now visibly contradicts the tightened rule, so it
  is NAMED in Out-of-scope as a follow-on reclassification rather than hidden.
- F4 ACCEPTED: proof now runs validate + request + e2e.
- F1 PARTIALLY: verified — nabj reads clean, but ans is CONDITIONAL (freshmen
  exempt) and chick-fil-a is EMPLOYMENT (Team Member, no honest kind), so
  Codex's "add them now" over-generalizes. Kept deferred, but reframed
  Out-of-scope to name each one's actual shape and state plainly that these
  still surface as ordinary matches until the verification pass.
Net rev 2: TBP row + NIH re-justification (both data-only, existing kinds),
tightened glossary, both test suites, honestly-named backlog. No model change.

## Round 2 — Codex — VERDICT: REVISE
Confirmed TBP + NIH schema-safe; NIH's disadvantaged-background gate verified
against training.nih.gov. Three findings:
1. (High) national-space-club still contradicts the tightened glossary — the
   plan changed the rule but left the row, shipping a doc-vs-data conflict.
2. (Med) The follow-on candidate list is stale — several listed IDs already
   have rows.
3. (Med) chick-fil-a is not blocked by "no honest kind" — kfc-foundation-
   scholarship already models an employer gate as institution_channel.

### Claude's response (arbiter) — rev 3
Verified all three:
- F2 CONFIRMED, I was wrong: national-beta-club, nshss, naba, sons-of-norway,
  women-in-aviation carry EFFECTIVE special rows stored INLINE in
  eligibility.special_requirements (loader.py appends sidecar to inline);
  afcea-rotc has a sidecar row. My candidate list came from a sidecar-only
  grep that missed inline rows — the same mistake as the quick-apply grill.
  Re-verified with inline included: only 6 truly lack a row (nabj, ans,
  chick-fil-a, afcea-stem-majors, american-physical-society,
  courageous-persuaders). List corrected.
- F3 CONFIRMED: kfc-foundation-scholarship uses kind=institution_channel for
  "must be a participating-KFC employee" — the exact analog for chick-fil-a's
  Team Member gate. Fixed the plan's "no honest kind" claim; chick-fil-a fits
  institution_channel after verification.
- F1 ACCEPTED via Codex's own exit (b): do NOT ship the application-work
  clause in this plan. A mini-sweep showed it condemns at least TWO live rows
  (national-space-club AND ieee-lance-stafford-larson), i.e. it's a sweep, not
  a one-row fix. Reverted CONTEXT.md to the minimal change TBP+NIH actually
  need — the passive-condition carve-out only — which creates NO contradiction
  with a competition/audition row. The application-work refinement AND its row
  cleanup are bundled into the follow-on so they land together.
Net rev 3: TBP add + NIH re-justify (both existing kinds), minimal glossary
(passive carve-out only), corrected 6-item backlog, chick-fil-a=institution_channel.
No doc-vs-data contradiction shipped. No model change.

## Round 3 — Codex — VERDICT: APPROVED
Plan internally consistent: glossary adds only the passive-condition carve-out
(no longer condemns national-space-club pre-cleanup); TBP/NIH rows schema-safe
(membership / identity_or_status, details 326/329 < 400); NIH rationale
source-backed by UGSP materials; the six no-row IDs check out against sidecar
+ inline. Residual non-blocking nit: courageous-persuaders doesn't look
gate-shaped — addressed by softening its framing (queued for verification, may
need no row). Converged at rev 3 after 3 rounds. Awaiting Josh sign-off.

## Act 3 — Build (codex-build)

### Round 1 — Codex build
Codex (gpt-5.5, --yolo run under Josh's hand) implemented rev 3 steps 2-3.
Report: edited only app/data/special_requirements.json — added tau-beta-pi
(kind=membership) and replaced nih-ugsp (no_direct_application/"Service payback"
-> identity_or_status/"Disadvantaged-background"). Flagged an honest deviation:
validator now shows 4 warnings not 3, because sallie-mae-bridging-the-dream's
confirmed deadline (Jul 17) passed as of Jul 18 — unrelated to this change.

### Claude's verdict — VERIFIED, PASS
Read the full diff: exactly the two rows from the plan, verbatim, nothing else
touched (no CONTEXT.md, no .py, no scholarships.json). Ran all proof myself:
validator "No structural errors"; request suite 398 passed; e2e 47 passed.
Behavioral check via load_scholarships(): tau-beta-pi now special_reqs=1
(membership) so it moves Strong -> special-check lane; nih-ugsp special_reqs=1
(identity_or_status) so it stays in the lane for the corrected reason. The
extra validator warning is a real deadline-rollover on an unrelated scholarship,
not a regression. Awaiting Josh's commit sign-off. Codex does not commit.

---

# Plan Review Log: Forest-Journey redesign (docs/2026-07-18-forest-journey-redesign.md)
Act 1 (grill-with-docs) complete — plan locked; CONTEXT.md gains "Journey map";
ADR 0001 records the immersive-everywhere decision. MAX_ROUNDS=5. Codex gpt-5.5
(config pins gpt-5.6-sol; overridden per the box's known-good setting),
read-only.

## Round 1 — Codex — VERDICT: REVISE
Ten findings, all substantive; verified the two load-bearing factual claims
(F6: renderSaved merges 3 lanes; F10: journey-teaser.js hardcodes a separate
three.min.js ?v= outside the lockstep, 40 test defs not 47). Accepted all ten:
1. LCP hand-waved (blocking) -> added a hard LCP budget (no new render-blocking
   landing request, CSS growth cap, no data-URI scene art in inlined CSS, one
   preloaded mobile hero only if it's the LCP element, else lazy w/ dims,
   AVIF/WebP srcset, Lighthouse mobile as a release gate).
2. Mockup gate validated only aesthetics -> each mockup must carry mobile comp,
   asset inventory, LCP element, byte target, format, preload/lazy, RM fallback.
3. DOM contract only checks selector existence, not behavior -> freeze ids/data
   unless app.js changes; add semantic Playwright tests (tabs, 3-step form,
   .card-body containment, overlay clickability, saved-status re-render).
4. SEO list incomplete -> golden request tests for head tags + visible
   verification/deadline/source blocks per lane + JSON-LD escaping.
5. Legal copy under-tested -> snapshot-hash privacy/terms/footer/age-gate.
6. Journey map underspecified -> single computeJourneyMapState() aggregating all
   3 lanes, called from match flow + renderSaved + tracker refresh + status
   handlers.
7. Edge cases mislead -> explicit zero/all-rejected/awarded-only/unknown-status/
   logged-out-sample states; rejected excluded from active saved, shown as side
   count.
8. Branch strategy too casual -> daily rebase, Vercel preview-env parity,
   main-freeze window, full proof after final rebase.
9. Scope too big -> Phase 0 spike (landing hero + saved Journey map only) proves
   LCP/DOM/e2e before fanning out; explicit off-ramp to the ADR fallback.
10. Stale counts / cache-bust gap -> removed hardcoded test counts; assert every
   ?v= resolves to one central version; include dynamic loader URLs.
No push-back — the review materially strengthened the plan. Re-submitting rev 2.

## Round 2 — Codex — VERDICT: REVISE (round-1 blockers fixed in substance)
Four precision refinements, all accepted:
1. LCP gate lacked a deterministic protocol -> pinned: Lighthouse mobile vs the
   Vercel preview URL, median of 3 runs <2.5s AND no single run >2.7s.
2. LCP budget ignored JS/main-thread cost (map code lands in the synchronous
   eager app.js) -> added a JS budget: map byte cap, no eager SVG build before
   first paint, lazy-init on saved view / requestIdleCallback, TBT evidence.
3. Cache-bust test "every ?v= in the tree" was overbroad (would catch docs/log
   history) -> scoped to served HTML/templates + static JS loader URLs;
   excludes docs/, PLAN-REVIEW-LOG, logs, vendor contents.
4. `matches` milestone session-state ambiguous -> milestones read independent
   sources: saved/drafting/submitted/awarded light from persisted data
   regardless of lastResults; `matches` reads "not run this session" when there
   are no current results, never implying failure.
No push-back; these are precision, not design changes. Re-submitting rev 3.

## Round 3 — Codex — VERDICT: APPROVED
Rev 3 closes the material gaps: LCP gate measurable/repeatable, JS/main-thread
path budgeted, cache-bust scope enforceable, Journey map no longer depends on
current-session matches to show persisted progress. One non-blocking nit ("other
nine surfaces" vs the Phase 1 list) fixed to "remaining surfaces". Converged at
rev 3 after 3 rounds. Awaiting Josh sign-off before any code.

# Plan Review Log: Phase 0 LCP tuning (docs/2026-07-19-phase0-lcp-tuning.md)
Act 1 (grill-with-docs) complete — plan locked. Decisions: fixes on the branch;
CLS via CSS-reservation-first (app.js only if forced); LCP is the gate (median-of-5
<2500, no run >2700), CLS best-effort <0.1. No new CONTEXT.md terms; no new ADR
(fallback already ADR 0001). MAX_ROUNDS=5. Codex read-only, config default model.

## Round 1 — Codex (gpt-5.5) — VERDICT: REVISE
Ten findings, all substantive; accepted all ten (no push-back — they materially
sharpen the plan):
1. Don't treat Lighthouse opportunity savings as LCP causality — campus-quad is
   below-fold/lazy; classify as byte cleanup until the trace waterfall proves it
   delays the measured LCP candidate.
2. The custom Puppeteer/CDP script is for element ATTRIBUTION only, never a
   timing source; all pass/fail timings come from the pinned Lighthouse protocol
   (pin version, viewport, DPR, throttling, cache, URL, deployed commit).
3. CLS diagnosis too narrow (led with app.js) — collect ALL layout-shift entries
   w/ source nodes + timestamps; candidates also include font swap, auth/header
   reveal, deferred motion setup, hero/demo layout. Trace decides the category.
4. Responsive sizing underspecified — mobile ~100vw overstates (.main has side
   padding) and ignores DPR; derive srcset candidates + sizes from measured CSS
   widths (mobile calc(100vw - 3rem), desktop capped to the proof column) with
   1x/2x descriptors.
5. DOM-contract overconfidence — dom_contract.json does NOT track the proof
   image, so wrapping in <picture> can change CSS/e2e silently without a contract
   failure; add explicit assertions for picture/source/img, currentSrc,
   dimensions, alt, loading, decoding.
6. Cache-bust lockstep incomplete — test_pages.py checks app CSS/JS strings, not
   srcset candidates or image preloads; extend it to parse src/srcset/href and
   versioned landing asset URLs.
7. Hero-preload "exactly one" contradicts "desktop variant under its own media";
   the gate is mobile — preload ONLY the mobile variant, media matching the CSS
   breakpoint, and only if it is the LCP element.
8. Versioned preload won't dedupe against an unversioned CSS url() background —
   make the CSS background URL and the preload href byte-identical (incl. ?v=).
9. rel=prefetch isn't guaranteed non-competing — verify the priority/waterfall
   after the change; if it still competes with the LCP path, remove the landing
   stylesheet hint entirely.
10. No regression guard for the inlined-CSS non-negotiable — add a test that /
   contains inline CSS, uses no rel="stylesheet" for landing CSS, and carries
   only the intended prefetch/preload hint.

### Claude's response
Accepted all ten; revising to rev 2. Softened the campus-quad causality claim to
"top byte-cleanup + likely bandwidth competitor, confirmed by the step-1
waterfall"; split step 1 into attribution-only tooling vs the pinned-LH timing
source and broadened the CLS candidate set; specified measured-width srcset/sizes
with DPR; added explicit responsive-image + inlined-CSS-guard tests and extended
the ?v= lockstep test to image URLs; made the hero preload mobile-only + byte-
identical to the CSS url(); added the prefetch waterfall check with a remove-the-
hint fallback.

## Round 2 — Codex (gpt-5.5) — VERDICT: REVISE
Five findings — three consistency gaps where rev-2 softened the Goal but left the
step bodies stale, two genuine refinements. Accepted all five:
1. Step-1 attribution must run under the SAME viewport/DPR/cache/throttle as the
   gate (CDP device emulation alone can shift the LCP element, lazy-load, CLS
   race) — while Lighthouse stays the only pass/fail timing.
2. Step 5 still narrowed CLS to app.js-populated containers despite step 1
   broadening the candidate set — rewrite as culprit-specific branches (CSS
   reservation for DOM/layout causes; distinct fixes for font/header/motion).
3. Step 2 still called campus-quad "the dominant LCP bandwidth cost" that "still
   downloads in the critical window" before step 1 proves it — reframe as top
   byte-cleanup opportunity; LCP lever only if the trace confirms competition.
4. Step 2 self-contradicted on sizing (led with ~100vw/~48vw then said don't
   hand-wave vw) — remove the rough language; measured widths + DPR descriptors
   are the sole source of truth.
5. NEW: step 7 pins Lighthouse @11 but didn't state the failing baseline was @11
   — pin the baseline version for a valid comparison.

### Claude's response
Accepted all five; revising to rev 3. Step 1 now runs attribution under
gate-matching throttle/DPR/cache. Step 2 reframed as byte-cleanup-first and the
rough vw language removed. Step 5 rewritten as culprit-specific branches. Step 7
records that the 3548 ms baseline was measured with lighthouse@11, so @11 is the
consistent comparison version.

## Round 3 — Codex (gpt-5.5) — VERDICT: APPROVED
Rev 3 verified: step 1 attribution runs under gate-matching throttle/DPR/cache and
is not a timing source; step 2 is byte-cleanup-first (LCP lever only if the trace
proves contention) with the rough vw language gone; step 5 branches by actual CLS
culprit category; step 7 ties Lighthouse @11 to the baseline version. No new
blocking flaw. One non-blocking nit — the "CSS-reservation first" key-decision
wording was stale vs the branched step 5 — fixed to "fix by the trace-confirmed
culprit category, preferring the contract-safe fix per branch." Converged at rev 3
after 3 rounds. Awaiting Josh sign-off before any code.
