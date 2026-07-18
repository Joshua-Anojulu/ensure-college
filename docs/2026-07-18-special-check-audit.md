# Plan: special-check audit — the passive-condition carve-out (rev 3)
_Locked via grill-with-docs — by Claude + Josh, 2026-07-18. Terms per CONTEXT.md. Rev 3 after Codex rounds 1-2 (REVISE)._

## Goal

Sharpen what belongs in the **Special check** lane, then fix the two rows the
sharpened rule demands. The audit started from four scholarships with
unverifiable eligibility gates and no `special_requirements` row
(nurse-corps, nhsc, smart, tau-beta-pi). The grill established the one
criterion this plan adds to CONTEXT.md: a **passive, near-universal condition**
the student meets by doing nothing (no federal debt, clearance-eligible, no
existing service obligation) is **not** a special check — it belongs in the
checklist details. Membership, nomination, and finalist status (a status the
student must actually hold) remain special checks as before. Of the four
starting scholarships, only Tau Beta Pi belongs in the lane; and applying the
carve-out surfaced one existing row (NIH UGSP) that is in the lane for the
wrong reason and must be re-justified.

A second, tempting refinement — excluding ordinary *application work* (essays,
videos, auditions that are the award's own selection) — is deliberately **not**
made here. Codex round 2 showed it would condemn live rows
(`national-space-club-keynote-scholarship`, `ieee-lance-stafford-larson-student-award`)
that this plan does not clean, shipping a doc-vs-data contradiction. That
refinement and its row cleanup are bundled into the follow-on sweep so they
land together.

## Approach

1. **CONTEXT.md — done inline during the grill.** The **Special check** entry
   now states the affirmative-vs-passive test and its carve-out, with the
   federal-service conditions named as the canonical *non*-examples. No further
   glossary work.

2. **Add one row to `app/data/special_requirements.json`** — `tau-beta-pi-scholarship`:
   ```json
   "tau-beta-pi-scholarship": [
     {
       "kind": "membership",
       "label": "Tau Beta Pi membership required",
       "details": "These scholarships are restricted to initiated members of the Tau Beta Pi Association on the date the award is made; candidates for membership may apply if they will be initiated by June 1. Tau Beta Pi is an invitation-based engineering honor society — you cannot simply join, so confirm your standing before counting on this."
     }
   ]
   ```
   `kind: membership` is an existing enum value (39 precedents). This moves TBP
   from a possible Strong match into the special-check lane, which is correct:
   it is genuinely membership-gated and the profile never asks about TBP
   membership.

3. **Re-justify the NIH UGSP row** in the same file. It currently reads
   `kind: no_direct_application`, label "Service payback commitment", details
   about post-graduation service payback — which is exactly the passive
   post-award commitment the criterion says belongs in the checklist, not the
   lane, and the kind does not match the content either. But NIH UGSP *does*
   carry a real pre-existing gate: it is for **disadvantaged-background**
   undergraduates with exceptional financial need (a status the profile cannot
   verify; its `demographics` list is empty so the matcher never gates on it).
   Re-point the row at that gate:
   ```json
   "nih-undergraduate-scholarship-program": [
     {
       "kind": "identity_or_status",
       "label": "Disadvantaged-background eligibility",
       "details": "UGSP is limited to students from a disadvantaged background (as NIH defines it) with exceptional financial need — a status the profile does not capture. Confirm you meet NIH's definition before applying. The post-graduation service payback is a condition of accepting the award, tracked in the checklist, not an eligibility gate."
     }
   ]
   ```
   NIH stays in the special-check lane (it already carries a row, so
   `requires_special_check` does not change) — this corrects *why*, not
   *whether*. No behavioral change; a data-honesty fix.

4. **Prove it.** `scripts/validate_dataset.py` (schema + the 400-char details
   cap), the request suite (`pytest tests/ --ignore=tests/e2e`), AND the
   browser suite (`pytest tests/e2e`). The change is data-only, but the
   special-check lane is a rendered surface and CLAUDE.md's proof command names
   both suites, so run both rather than argue the exception.

## Key decisions & tradeoffs

- **`kind` is inert — no new enum value, no model change.** Code exploration
  during the grill confirmed `SpecialRequirement.kind` is never rendered
  (`specialRequirementText` at app.js:3169 shows `label`/`details` only) and
  never branched on in matching or scoring (`requires_special_check` is just
  `bool(special_requirements)` at matcher.py:402). So the "does the enum need a
  federal-service/clearance value" question that opened the audit is moot —
  adding a `kind` would buy nothing behavioral or visible. The meaning lives in
  `label`/`details`.
- **Nurse Corps / NHSC / SMART stay Strong matches.** Their gates (no federal
  judgment liens, no overdue federal debt, eligible to obtain a security
  clearance, no existing service obligation) are passive and near-universal —
  most students satisfy them by doing nothing. Flagging them would demote three
  legitimate scholarships for conditions almost everyone meets. The genuinely
  consequential part — the multi-year post-graduation service commitment — is
  an obligation you take on *if you win*, not an eligibility gate, and it is
  already recorded in each one's checklist details from the 2026-07-17 pass.
- **"Selective" was rejected as the criterion.** It read cleanly but would have
  disqualified ~15 existing open-membership rows (SHPE — "free for students" —
  NSBE, AISES, DECA, FBLA, JACL, NAACP, AIAA), wrongly moving them back to
  Strong. Free-to-join membership is still a special check: the profile can't
  confirm the student joined, and they may not realize they must. The
  affirmative-vs-passive test keeps every existing membership row valid.
- **No ADR.** The decision's non-obvious part ("why isn't a federal-service
  commitment a special check?") is answered directly by the CONTEXT.md entry,
  which names those conditions as the non-examples. A separate ADR would
  duplicate the glossary.

## Risks / open questions

- Adding TBP's row moves it from Strong to the special-check lane — a visible
  ranking change for that one scholarship, and the intended effect.
- The criterion is now the standing bar for every future special-check
  decision. It is **normative going forward**: this plan applies it to the two
  rows it directly implicates (TBP, NIH) but does not sweep every existing row
  into line — that is the systematic follow-on. The known un-reconciled rows
  are named below rather than hidden, so the glossary and the data are honest
  about the gap.

## Out of scope (follow-on)

- **The application-work refinement + the rows it reclassifies, together.**
  Tighten the glossary to exclude ordinary application work (essay, video,
  audition/interview that is the award's own selection) *and* clean the rows
  that only describe such work — at least
  `national-space-club-keynote-scholarship` (video audition + keynote, no
  pre-existing gate: US citizen / HS–grad / STEM intent) and
  `ieee-lance-stafford-larson-student-award` (a paper submitted to the award's
  own October contest). Doing the wording and the cleanup in one pass avoids
  shipping a rule the rendered data contradicts. Verify each sponsor page
  before removing or re-justifying.
- **Six scholarships that truly carry no row** (verified against sidecar *and*
  inline `eligibility.special_requirements`), most membership- or
  employment-shaped, each to be confirmed against its sponsor page before any
  row is added (`courageous-persuaders-scholarship` in particular does not look
  gate-shaped from current data and may need no row at all):
  `nabj-scholarship` (reads as a clean member-only gate),
  `ans-scholarships` (conditional — incoming freshmen are exempt from
  membership until funds are disbursed, so not a clean gate),
  `chick-fil-a-remarkable-futures` (current *Team Member* employment — an
  employer gate, which the repo already models as `kind: institution_channel`
  for `kfc-foundation-scholarship`, so it fits an existing kind after
  verification), `afcea-stem-majors-scholarship`,
  `american-physical-society-scholarships`, and `courageous-persuaders-scholarship`.
  Each still surfaces as an ordinary match until verified and given a row.
  (The other candidates first suspected — `national-beta-club`, `nshss`,
  `naba`, `sons-of-norway`, `women-in-aviation`, `afcea-rotc` — already carry
  effective rows, most stored inline; an earlier sidecar-only scan missed them.)
- **A systematic gate audit of all 223 scholarships** against the criterion —
  the umbrella for both bullets above.
- No code, no model, no enum change in this plan. Both fixes here reuse
  existing `kind` values (`membership` for TBP, `identity_or_status` for NIH).
