# ADR 0002: Level 2 diegesis on tool surfaces

Date: 2026-07-22
Status: Accepted

## Context

Phase 1 shipped the forest as an environment layer: world art behind and beside
the working UI. Josh's verdict was that it reads as pasted-on decoration — the
match results and tools look unchanged, and the site does not feel like one
world (the Hack the North / Hook'em Hacks bar he set). The opposite failure is
also real: ADR 0001's genre boundary says stressed students revisit weekly to
manage deadlines, so a fully illustrated UI where data itself becomes drawn
objects would tax scanning and comprehension.

Three depths were considered for the working surfaces:
1. Motif accents on existing panels (what Stage B did — judged insufficient).
2. Drawn containers, clean content: every container is a physical drawn object
   (paper card, carved marker, trail sign, clipboard), while typography,
   spacing, and data layout inside stay the current clean system.
3. Full diegesis: the data itself illustrated (deadlines as sundials, fit
   rings as compasses).

## Decision

Level 2 is the law for tool surfaces: containers are drawn objects, content
stays clean. Level 3 moments are allowed only as single accents in the landing
hero and the Journey map, never in match lanes or other working lists. Level 1
is no longer an acceptable end state for a treated surface.

## Consequences

- Component chrome must be authored (SVG/vector, token palette), not raster,
  so containers stretch, stay crisp, and never read as pasted images.
- The DOM contract gains a small set of sanctioned decoration/wrapper nodes,
  updated deliberately in the manifest.
- Legibility and hit-testing e2e gates apply to every chromed component; a
  cohesion mismatch against the signed comps is a blocking failure, not a
  logged minor.
- Reversing this (either back to flat panels or forward to full diegesis)
  means reworking every treated surface — hence this record.
