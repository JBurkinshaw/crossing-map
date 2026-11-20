# 0075. Drawings moved apart, and a caption on each

Status: accepted (2026-11-19). Amends 0026 and 0066.
Phase: P1

## Context

With 150 drawings (decision 0073), the placement of decision 0026 left 110 pairs of drawings on top of each other at their first zoom, and 44 drawings on stop markers. It could only pick a side of each drawing's own point and wait one zoom step, so where many scenes share a place, such as the Hacienda de San Diego, the drawings piled up. Decision 0073 said the map hides the lower-priority drawing of an overlapping pair. It does not: the drawing layer allows overlap, so both drew, one over the other. The owner asked for them to be moved further apart, and said accuracy matters less than a map that reads well. Ten drawings also had no caption, which decision 0026 had allowed where the subject seemed plain.

## Decision

- **A drawing may move its point** when its own point is crowded. `crossing.build_vignettes` tries the point itself and points 40, 80, 130 and 190 screen px away at the drawing's first zoom, in eight directions, each with every side. A clear spot always beats a crowded one. Among spots as clear, each pixel moved costs half a pixel of covered route line, so a drawing moves no further than it must, and a drawing clear on its own point stays there.
- **A drawing never moves across the international boundary.** Every drawing and its point stay on the side of the scene, moved or not, so a scene in New Mexico stays in New Mexico, so the map does not put an event on the wrong side of the line the book is about. The build carries the boundary as a short line: 31°20′ N and 31°47′ N joined along 108°12.5′ W (the Gadsden Purchase lines, as `crossing.area_drafts` has them), the diagonal west to the Colorado River, and the Rio Grande to the east, which it follows only roughly.
- **The published point is the moved one.** The drawing's `reasoning` says how far it moved and in which direction (geodesic distance on WGS 84), and that it moved to clear the stops, lines and drawings crowded at its place. Its `place_ref` still names what it stands for.
- **Waiting for a closer zoom is unchanged**: at most one zoom step, and only if a closer zoom would be clearer (decision 0026, amended).
- **Every drawing has a caption.** The ten without one now say what they show, so a drawing moved away from its place still says what it is.

## Alternatives

- **Leader lines from each moved drawing back to its point.** They would keep the link exact, but 134 leaders would cross the map, and MapLibre cannot hide a leader when its drawing loses a collision (the stage 6 vignette packet, question 4).
- **Screen-space offsets only**, a larger fixed gap on each side. A gap in pixels does not separate two drawings whose points are close: both move the same way.
- **Fewer drawings in the crowded places.** It would undo the owner's call for 150.

## Consequences

`pipeline/measure/vignette_clashes.py`, at each drawing's first zoom:

| | Before (decision 0073) | After |
| --- | --- | --- |
| Drawings that clash | 82 | 0 |
| Stop markers covered | 95 | 0 |
| Route line covered | 16,824 px | 523 px |
| Pairs of drawings on each other | 110 | 0 |

134 of the 150 drawings move, by 21 km at the median and 51 km at most, none across the boundary. A drawing now stands roughly near its scene rather than beside its pin, which the key already says ("its position approximate"). The build takes about 30 seconds. A drawing's point moves again whenever the stops, legs or other drawings around it change.
