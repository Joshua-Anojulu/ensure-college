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
