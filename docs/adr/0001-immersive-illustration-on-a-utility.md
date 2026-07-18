# ADR 0001 — Immersive illustrated theme on a trust-critical utility

Date: 2026-07-18
Status: Accepted

## Context

EnsureCollege is a college-planning tool for U.S. high-school students and
their parents — a trust-critical utility with data-dense working surfaces
(matcher results, checklists, deadlines). Its existing look, **Forest Light**,
is a restrained token-driven design system.

The owner wants the whole site to feel like one cohesive, immersive illustrated
"forest-journey" world — the cohesion of a site like Hack the North — applied to
**every** surface, including the data-heavy tool pages, not just the marketing
ones. Two lighter alternatives were on the table and rejected: (a) immersive
only on narrative surfaces with motif-framing on tool surfaces; (b) motifs and
texture only, no full scenes.

## Decision

Go immersive **everywhere**: full illustrated scenes on every surface. To keep
the utility usable, the illustrated world is treated as a **stage**, and all
working content rides in high-contrast, legible panels layered over it — the
pattern Hack the North itself uses for its readable content zones. Illustrated
assets are optimized and lazy-loaded, and the landing keeps its inlined
critical CSS, so the theme does not silently break the mobile LCP budget.

## Consequences

- **Positive:** maximum cohesion and emotional pull; the "journey" metaphor the
  product is built around becomes literal and consistent; strong differentiation
  from every other scholarship tool.
- **Negative / risks (accepted, to be *measured* not assumed):**
  - **Legibility** of dense data over illustration is a real hazard; mitigated
    by the panel-over-stage pattern, and it is a pass/fail check per surface,
    not a matter of taste.
  - **LCP** (hard gate: 2.5s mobile on the landing) is threatened by heavy
    imagery; mitigated by optimized/responsive/lazy assets and inline critical
    CSS, and re-measured before release.
  - **Trust:** a heavily illustrated planning tool could read as unserious to
    an anxious parent. The panel pattern keeps the working surfaces sober; this
    is a watch-item for user feedback after launch.
- **Reversibility:** low. This is a site-wide reskin; backing it out means
  another full pass. Hence this record.

## Revisit if

Post-launch, the LCP gate cannot be met on a tool surface, or usability signals
show the illustration is hurting task completion for stressed users. In that
case, fall back to alternative (a): immersive narrative surfaces, motif-framed
tool surfaces.
