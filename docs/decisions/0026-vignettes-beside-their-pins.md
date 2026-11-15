# 0026. Vignettes beside their pins

Status: accepted (2026-11-14). Amends design section 10's placement rules.
Phase: P1

## Context

Design section 10 placed each vignette in empty country near what it stands for, offset 11 to 20 km (the she-wolf 101 km), with a hairline leader for real located sites. Readers took the drawings as far from their places. The owner asked for them as close to their places as possible, with no leader lines, and a note in the key that their positions are approximate.

## Decision

- Each vignette's point is the stop or place it stands for (the seed's `ref`); only the Trinity cloud keeps its own position, the Trinity Site, which is not one of the book's places.
- The drawing is set beside the point on a `side` (one of eight, taken from where each drawing sat before) with a 16 px gap at the drawing's scale, by `icon-anchor` and `icon-offset`. It stays next to its pin at every zoom and never covers it. Its label sits under it.
- The drawing may sit under other labels, which draw over it, so every drawing shows in its zoom range and hides no name. Its caption is its own layer at the top of the label stack: it is placed first, and other labels make room for it.
- No leader lines. The key says a drawing is beside where its scene happens and its position is approximate.

## Alternatives

- **Geographic offsets a few kilometres out.** Close at one zoom, far at another.
- **Keeping empty-country anchors with more leaders.** Readers still read the drawing's place as the scene's place.

## Consequences

Drawings now crowd the busiest towns (Casas Grandes, San Diego) and can hide a place name under a drawing's paper; the place labels stay on top. The seed's `lon` and `lat` hold a position only for a subject that is not a stop or place.
