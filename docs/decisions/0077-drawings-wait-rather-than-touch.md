# 0077. Drawings wait rather than touch

Status: accepted (2026-11-20). Supersedes the moves in decision 0075. Amends 0026. Amended by 0080 (checked every half zoom).
Phase: P1

## Context

Decision 0075 moved a crowded drawing's point up to 190 screen px away at its first zoom, up to 51 km on the ground, so that no two drawings overlapped. On the preview the owner found most drawings had been fine where they were before, and the long moves took them away from their scenes. The real fault was narrower: zoomed in close, some places still had drawings stacked on each other. The owner does not mind drawings hidden until zoom 11.5 or 12, as long as each shows by zoom 12 and none touches or overlaps another wherever both show.

## Decision

- **Back to each drawing's own point**, as before decision 0075, with the side and first zoom chosen as decision 0026 has them.
- **No drawing touches another.** A drawing, with its caption, keeps at least 4 screen px from every other at every zoom where both show, up to zoom 12, past which nothing grows. Every whole zoom is checked, because two drawings on one point do not spread apart as the map zooms in.
- **A drawing waits rather than touch.** Where every side would touch a drawing already placed, it shows from a closer zoom, as far as 12, where the points have spread out. Higher priority drawings are placed first.
- **Short moves only where drawings share a point.** Where no side of its own point is free at a zoom, a drawing may move its point a little: 12 to 120 px at zoom 12, about 0.2 to 2 km on the ground, the nearest free spot winning, never across the international boundary from its scene (decision 0075's rule).
- **The rest of decision 0075 stands**: every drawing has a caption, and the reasoning says how far a moved drawing moved.

## Alternatives

- **Decision 0075's long moves.** They cleared the map at every zoom, but at the cost of the drawings' places, which the owner judged the wrong trade.
- **Let drawings overlap and rely on the map's collision.** The drawing layer draws every icon (`icon-allow-overlap`) so that drawings stay in view as context; turning that off would hide drawings at random by priority at each zoom, and drawings on one point would never both show.
- **Wait with no moves at all.** Drawings that share a point, such as the San Diego hacienda's, can touch on every side at every zoom: waiting alone never separates them.

## Consequences

Checked at every half zoom from 7 to 12 and at 13 and 14, no two drawings shown together touch. 118 of the 150 drawings stand on their own points; 32 that share a point with another move 0.2 to 2 km. Drawings first show at zoom 7 (2), 8 (20), 9 (58), 10 (30), 11 (34) and 12 (6). At their first zoom, 65 drawings still cover some route line or a stop marker, as before decision 0075, since a drawing waits for the story's sake at most one zoom step. The build takes about a minute.
