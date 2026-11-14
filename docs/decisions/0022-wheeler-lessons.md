# 0022. Paper, ink and lettering after the Wheeler Survey sheets

Status: accepted (2026-11-14). Amends 0016 (paper and hachure ink).
Phase: P1

## Context

Two Wheeler Survey atlas sheets (70A, 1877; 83, 1876) were studied against the classic map (`review/stage-8/wheeler/README.md`), and the lab's Wheeler section tried seven of their lessons. On 14 November 2026 the owner adopted every recommendation and chose sheet 70A's cream paper.

## Decision

- **Paper.** Cream, after sheet 70A's under-tint, darkened a little for the screen: `#efe5c8` below zoom 10, `#e6d9b9` for Mexico, and a near-white `#f8f0d8` to `#f4ead0` from zoom 10. The sprite's knock-out paper (`art.PAPER`) and the side panels match.
- **Hachures.** Wheeler's brown-black (`#2e2010`) in place of 0016's sepia, with slope contrast at 0.5: a stroke's opacity is scaled from 0.7 on gentle ground to 1.23 on steep, and its width from 0.8 to 1.13. This starts the Wheeler look in the style; white crests, rim combs and shorter steep strokes need the hachure build (a test area in the lab).
- **Rivers.** Main rivers in spaced roman capitals along their smoothed lines, 11 to 16 px, 0.45 to 0.9 em apart; smaller rivers and creeks in italic. River widths follow Natural Earth's `scalerank`. Creeks keep their Strahler-order widths and lighter intermittent lines (tiles-v8): they already taper by rank, and Wheeler's dotted dry washes would undo that rule.
- **Spot heights.** From zoom 10, unnamed and small summits show their height alone, in the reader's units, at 10.5 px, under named summits' 12 px labels. Below zoom 10 they crowd the map.
- **Landform names** along each landform's axis, the type hierarchy, the graticule, the frame, water places and historic roads are tried in the lab's test area first.

## Alternatives

- **Grey paper (sheet 83)** or today's caliche. The owner chose cream: it suits the warm hachures.
- **Sepia hachures with more contrast.** Lighter beside the type and the journeys, but less like the sheets. Brown-black at contrast 0.5 holds the journey lines and labels on top in the views checked.

## Consequences

The map is warmer and its ranges have dark cores. The Imhof tint still covers the paper below zoom 10. A darker ink or higher contrast should be checked against the journeys again whenever either changes.
