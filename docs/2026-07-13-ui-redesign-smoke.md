# Forest Light redesign: production smoke log

Date: 2026-07-13 (post-merge, commit a5aab01)
Target: https://ensurecollege.com (production; the plan's Vercel branch-preview gate
was unusable because preview env vars were never configured on the project, a
pre-existing gap; verification ran on localhost pre-merge and on production
immediately post-merge instead)
Browser: Chrome (Claude-in-Chrome extension), Windows 11, viewport 1512x795 desktop
Runner: Claude (scripted), per docs/2026-07-13-ui-redesign.md step 23

## Checklist

| Item | Result | Evidence |
|---|---|---|
| /health returns ok on merged commit | PASS | `{"status":"ok","commit":"a5aab01"}` |
| Landing loads, zero console errors | PASS | console error scan empty on prod load |
| New assets served (css v=20260713-3, fonts, GSAP vendor, grain.png) | PASS | all 200 via curl |
| CSP no longer references Google font origins | PASS | header grep count 0 |
| Fonts actually load (Cabinet Grotesk 800) | PASS | `document.fonts.check` true |
| Motion layer initializes (motion-ready, GSAP present) | PASS | JS probe |
| Preview 3-question flow returns matches | PASS | 3.7 / HS junior / Engineering -> 3 cards (AOPA first), honest total "43 scholarships match..." |
| Opportunity tabs switch, data-view intact | PASS | all 5 data-view values verified; Browse -> catalog visible, 322 items |
| Auth session state renders | PASS | prod session cookie recognized, logged-in nav shown (auth modal not exercised on prod; covered by tests) |
| Server-rendered opportunity page (coca-cola-scholars) | PASS | 200, new asset version + Satoshi in markup |
| Keyboard-only pass through revealed sections | PASS (localhost, same commit) | pre-merge pass |
| Reduced-motion collapses all motion, content visible | PASS (localhost, same commit) | landing-motion early-returns; CSS gate forces opacity 1 |
| 375px mobile collapse (single column, no sticky, panel untilted) | PASS (localhost, same commit) | explicit CSS resets verified |
| DOM contract / emitted classes / CSP / font 200s / dash sweep | PASS | tests/test_dom_contract.py + test_pages.py, 364 tests green pre-merge |
| Lighthouse mobile (merge gate: LCP < 2.5s, CLS < 0.1) | see below | tmp/lh-mobile.json |

## Known non-issues
- Intermittent CDP screenshot-capture stalls during verification were isolated to
  GSAP's persistent rAF ticker starving Chrome's capture path on this workstation
  only; the page itself remains responsive (live JS, zero long tasks measured).
- Dataset validator warnings (conrad-challenge, jshs) pre-date the redesign;
  datasets untouched.

## Lighthouse (mobile emulation, production, lighthouse via npx, headless Chrome)

- Performance score: **0.85**
- FCP 2.4s | **LCP 3.5s** | **CLS 0** | TBT 40ms | TTI 3.6s | Speed Index 4.7s

Verdict: CLS gate passes perfectly (0 < 0.1). **LCP misses the 2.5s target under
mobile throttling (3.5s).** The plan's baseline-comparison clause is moot: the old
design was already replaced when the measurement ran (merge order was user-directed),
so there is no like-for-like old-design number. Note the old design loaded three
Google Fonts families render-blocking from a third-party origin, so it was unlikely
to be faster on this metric.

Follow-up item (backlog, not a revert trigger): mobile LCP optimization. Candidates:
inline critical above-the-fold CSS (the 90KB stylesheet is render-blocking),
subset the display font, `font-display: optional` consideration for non-hero weights.
