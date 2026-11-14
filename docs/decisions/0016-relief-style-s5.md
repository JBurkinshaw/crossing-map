# 0016. The relief style: Imhof at low zoom, light hachures and contours above (S5)

Status: accepted (2026-11-12); built in `tiles-v4` (2026-11-13), except focus mode, which is not built. Supersedes the style in 0014; the generator settings in 0015 change as below.
Phase: P1

## Context

The soft hachures of 0014 looked weak once published: most lines were thinner than a pixel, and at zoom 10 and up they sat 5–15 px apart. A local lab page, not committed, tested the style, density and zoom behaviour on two test tiles around the Pilares, with comparison sheets in `private/review/hachure-lab/`.

## How we got there

- **Width and shading first.** A thicker line (weight 0.9), darker ink on slopes facing away from a north-west light (Dufour's shadow hachures, Andy Woodruff's slope-plus-shadow), and a doubled stroke helped. But the gaps between lines at zoom 12–13 needed more lines, not more ink.
- **Density.** Spacing tests from the production 3–8 DEM cells down to Dufour-like 1–2.5. Dufour density matched Churchill's examples best, but was too busy for a story map.
- **Swiss references.** Churchill's three Swiss examples gave three directions: Dufour (dense shadow hachures), Siegfried (orange-brown contours, hachures on rock, bright paper) and swisstopo (contours over a grey hillshade). The pick combined Siegfried's colours and brightness with a light swisstopo hillshade, and more hachures than Siegfried.
- **Imhof for the low zooms.** An Imhof-style elevation tint, adapted to the desert (hazy grey-green valleys, pale sand plains, ochre high sierra), with a chromatic hillshade. It reads best below zoom 10, where hachures only speckle.
- **Avoiding the mesh.** Contours at 10–30 m plus hachures formed a grid at zoom 12–13. Light 50 m contours fixed it.
- **Short strokes, not long lines.** Lines split at each 10 m contour band (median 90 m long), at 2–4.5 cell spacing from 10° of slope.
- **Subtle, so the story leads.** A lighter sepia, 70% of strokes below zoom 12, and strokes fading in between zoom 10 and 13.

## Decision

- Below zoom 10: the Imhof desert tint and chromatic hillshade, with no hachures or contours.
- From zoom 9 to 10: a fade to a near-white paper, a light grey hillshade ("combined" method) and the line work.
- Hachures: short strokes (generator spacing 2–4.5 cells, minimum slope 10°, split at 10 m), in sepia `#6e5443` at weight 0.9 and opacity 0.65. Strokes on slopes facing away from the light are darker. A second stroke offset 0.35 px at 40% opacity adds body. Only 70% of strokes draw below zoom 12, and opacity rises from 55% at zoom 10 to full at 13.
- Contours: orange-brown `#b0622e`, 50 m with a heavier line every 200 m, at 45% opacity.
- A paper halo under the journeys clears the relief around the story. Focus mode (relief at 55% when a journey is selected) is planned and not built.

## Consequences

- The fine hachures and the corridor contours have to be regenerated. Tiles use two rounded attributes (`Slope`, `Aspect`) and are built to zoom 12, then shown at 13 by over-zooming. The test tiles suggest about 40 MB for the corridor.
- The local lab and its test caches are deleted once the style is in `site/src/map/relief.ts`.
