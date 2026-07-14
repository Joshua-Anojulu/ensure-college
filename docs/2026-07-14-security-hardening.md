# Plan: deferred security hardening (the 2026-07-12 review items)

_Rev 3, after two Codex adversarial review rounds (16 findings, all accepted).
Touches auth, so it goes through review before any code (CLAUDE.md)._

## Goal

Close the hardening items deferred from the 2026-07-12 review, **claiming only
properties we can actually deliver**. Two review rounds killed four claims that
sounded good and were false; what remains is what survives scrutiny.

## Scope split (the important decision)

**Ship now (this plan): items 1-5 + CSRF.** All are self-contained, need no
schema change, and are independently testable.

**Deferred to its own plan: the digest cron's delivery guarantees (old item 6).**
Doing it *properly* — never double-send, never strand a student — needs a durable
outbox or scan cursor, i.e. **a new table, i.e. a migration**. In this repo
migrations do not auto-apply in production (`RUN_MIGRATIONS_ON_STARTUP=false`;
0006/0007/0008 were never applied, and 0008 took auth down on 2026-07-08). A
schema change deserves its own plan that states how it reaches Neon, not a
footnote in a security patch. What review established, recorded for that plan:
- `reminders.py:195-200` sends **then** marks: a timeout in between duplicates
  the email on the next run.
- A bounded batch without a cursor can spend every run on the same front users.
- A daily drain and a weekly *cadence* are different things; conflating them
  would let a Monday recipient be re-sent on Saturday (`MIN_DAYS_BETWEEN_SENDS=5`).
- Resend's `Idempotency-Key` (verified: real, 24h retention) suppresses
  duplicates **only within 24h** — it is not exactly-once.
- The key must identify one *logical email* (job + user + period + a hash of the
  exact item ids), or a legitimate second batch of alerts gets swallowed.
- **Interim, in this plan:** set `functions["api/index.py"].maxDuration` as a
  backstop so the current serial run has the longest budget available. That is a
  mitigation, not a fix, and is labelled as such.

## The items

1. **CORS allows localhost in production.** `main.py:207` sets
   `allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?"` **with**
   `allow_credentials=True`, unconditionally. A page on `http://localhost:<port>`
   can make credentialed calls and read the responses: profile, plan, email.
   **Fix:** register `CORSMiddleware` only when the deploy is not production
   (`is_production_deploy()` or `VERCEL_ENV == "production"`).
   **Property claimed:** no credentialed cross-origin *reads* in production. CORS
   never stopped the request being *sent*; it stops script reading the response.

2. **Login timing oracle.** `auth_routes.py:243` short-circuits, so an unknown
   email skips bcrypt (~1ms) and a known one pays ~100ms.
   **Fix:** verify against a module-level dummy hash when the user is missing or
   has no password, so every attempt runs exactly one `verify_password`.

3. **Password-reset timing oracle.** `auth_routes.py:303` returns instantly for an
   unknown email; a known one writes a token and sends mail first.
   **Fix:** keep the send inline (rejected: `BackgroundTask` — FastAPI runs it
   in-process after the response and @vercel/python has no `waitUntil`, so account
   recovery would become best-effort), and pad **both** branches to the same
   response floor.
   **Property claimed (deliberately weak):** this removes the trivial
   fast/slow split. It does **not** make the endpoint constant-time: if Resend is
   slower than the floor, a registered email is still slower. Setting the floor
   above the email client's 10s timeout would be absurd, so residual timing
   leakage is **accepted and documented**, not hidden.

4. **Unsubscribe mutates on GET.** `main.py:542` flips `reminders_enabled` on GET;
   mail scanners and prefetchers follow links.
   **Fix:**
   - `GET` renders a confirmation page with a POST form; reads nothing, changes
     nothing; the token is HTML-escaped in the hidden field.
   - `POST /reminders/unsubscribe` accepts the token **in the query string** (RFC
     8058 clients POST to the `List-Unsubscribe` URL itself) *and* from a form
     body, so both the mail client and the page work.
   - `List-Unsubscribe` + `List-Unsubscribe-Post: List-Unsubscribe=One-Click` on
     **both** the digest and the new-match alert emails.
   - Identical response whether or not the token matched (no membership oracle).

5. **Unvalidated URL scheme.** `verification_source_url` is a bare `str` and the
   frontend assigns it to `link.href`; a `javascript:` value would execute.
   **Fix:** validated URL fields (http/https only) on the models; the dataset
   validator errors on a bad scheme; the frontend renders a non-http(s) value as
   **plain text, not a link** (rejected: `href="#"`, which still shows a
   clickable "official source" that goes nowhere — a lie by affordance).

6. **CSRF posture.** Session cookies are `SameSite=Lax`, which browsers do not
   attach to cross-site POSTs. That is the real protection today.
   **Fix:** add an `Origin`/`Referer` allowlist check on unsafe methods when a
   session cookie is present, as defense in depth. Route classes documented
   explicitly rather than hand-waved (the blanket "every mutation takes JSON" is
   **false**: `POST /auth/logout` has no body, and the new unsubscribe POST takes
   a query/form token):
   | Route class | Auth | CSRF reachable? |
   |---|---|---|
   | Authenticated JSON mutations (`/account/*`, `/auth/change-password`, …) | session cookie | No: Lax blocks cross-site cookie send; Origin check added |
   | `POST /auth/logout` (no body) | session cookie | No: same, and the effect is only self-logout |
   | `POST /reminders/unsubscribe` (token) | token, no session | Not CSRF: the token *is* the authorization; an attacker who has it can already unsubscribe |
   | `GET /reminders/run` (cron) | `CRON_SECRET` bearer | No: no cookie path |
   | Google OAuth callback | state param | Out of scope |

## Honesty statements (what this plan does NOT fix)

- **Account enumeration remains via signup**: `POST /auth/signup` answers 409 for
  an existing email, by design (a student must be told their email is taken).
  Items 2-3 close *timing* oracles only. The app is not enumeration-proof.
- **Rate limiting is not a security control here.** `rate_limit.py` falls back to
  per-instance memory (void on serverless) and fails open on Upstash errors, so it
  is not cited as a mitigation anywhere in this plan. Add a **startup warning**
  when a production deploy has no Upstash configured.
- **The digest cron can still double-send** in the send-then-crash window. That is
  the deferred plan's job; it is stated, not papered over.

## Verification

- Tests: login runs bcrypt on both branches; reset returns above the floor on both
  branches; GET unsubscribe does not mutate and POST does; both respond identically
  for a bad token; non-http(s) rejected by model + validator and rendered as text;
  no CORS middleware under production config; Origin check rejects a cross-origin
  authenticated POST and allows a same-origin one; startup warns without Upstash.
- `pytest tests/ --ignore=tests/e2e` (370) and `pytest tests/e2e` (40) stay green.
- E2E: reminders toggle, password reset, and login/logout still work end to end.

## Out of scope

Auth rewrite, email verification, the outbox/cursor work (its own plan), WAF, the
matcher, the datasets.
