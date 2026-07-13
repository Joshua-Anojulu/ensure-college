# Plan: /journey, a real-time 3D scroll-world (free replication of scroll-world)
_Scoped with Josh 2026-07-13 (user-directed scope-then-build; Codex review skipped
per Josh's explicit process for this task; static page, cheap to revert)._

## Goal
A standalone `/journey` page where scroll drives a camera through four low-poly
Forest Light diorama scenes rendered live in Three.js (no AI video, no credits):
THE PROFILE (desk, one glowing form) -> THREE LANES (three districts, converging
paths) -> THE PLAN (deadline war-room board) -> THE GATE (campus arch at dawn,
award envelope, CTA). Continuous forward camera spline, never reversing.

## Decisions (user)
- Placement: new route `/journey`; "How it works" link ADDED to header nav on the
  landing page and server templates (addition, no renames, DOM contract intact).
- Art: Forest Light diorama, flat-shaded low-poly, site palette exactly.
- Camera: continuous forward flight (architecture-A equivalent), expressive
  in-scene moves, no seam reversals; scrubs cleanly both directions by construction.
- Scenes: the four beats above.

## Approach
1. `app/static/js/vendor/three.min.js` (r160 UMD, self-hosted, CSP-clean).
2. `app/static/journey.html`: standalone page reusing style.css tokens/chrome
   (header with brand + "Find my matches" CTA, site footer) + inline page CSS.
   All copy server-rendered in real markup (SEO by construction), title/meta/
   canonical/OG. Zero em dashes, no eyebrows.
3. `app/static/js/journey.js`: procedural scenes (Box/Cylinder/Cone primitives,
   flat shading, palette hexes), camera + lookAt CatmullRom splines, GSAP
   ScrollTrigger scrub over a tall scroll track (consistent with landing stack;
   no window scroll listeners), copy sections fading per camera band, progress
   rail, DPR cap, resize handling, canvas fog to soften depth.
4. Fallbacks: `prefers-reduced-motion` OR no WebGL -> canvas hidden, sections
   render stacked as a static page. Phones get the full 3D (low-poly is cheap)
   with DPR capped at 1.75.
5. `app/main.py`: GET /journey serving the file (same pattern as privacy/terms),
   sitemap gains /journey.
6. Tests: /journey 200 + canonical + sitemap entry; nav link present on index.
7. style.css untouched (journey CSS is inline) so no cache-bust churn.

## Out of scope
Sound, pointer parallax, WebGL post-processing, portrait-specific camera,
localization. AI-generated assets (the point is $0).
