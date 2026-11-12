# 0014. The relief treatment: soft hachures over a sepia hillshade

Status: accepted (2026-11-11)
Phase: P1

## Context

The relief experiment (plan section 5.2, stage 3) compared eleven treatments on three test areas at zoom 7, 9 and 11 (`review/stage-3/sheet/`). Ink hachures at full weight competed with the hillshade, or smudged into dark patches at zoom 7. Filtering them to the steepest slopes left the ranges looking sparse.

## Decision

The map uses the "Swiss, full, soft" treatment:

- MapLibre's multidirectional hillshade over `terrain.pmtiles`, tinted sepia.
- Every hachure line from Huffman's script, with no slope filter, drawn in pale sepia (`rgba(90, 66, 44, 0.55)` at line opacity 0.75) at half the stroke width (0.12–0.65 px, heavier on steeper ground).
- Mountain glyphs on the summits, as in the experiment.

Coarse hachures (90 m DEM) draw below zoom 9.5, fine whole lines (30 m DEM) from 9.5.

## Alternatives

- Survey (ink hachures, no hillshade): the most engraved look, but busy at zoom 11 and smudged at zoom 7.
- Swiss accent and Swiss, dense (ink hachures on the steeper ground only): too sparse, and the hachures fight the shading.
- Swiss, full, in ink at full or half weight, or in sepia at full weight: either too bold, or the hachures fade out at zoom 9.

## Consequences

Production relief needs the adapted, vendored hachure script with absolute slope limits in degrees (decision 0013), run over the journeys corridor, and new tiles in a release. Because the soft hachures stay faint at zoom 7, they can draw from the hillshade's first zoom without the zoom 8 cut-off the ink treatments needed.
