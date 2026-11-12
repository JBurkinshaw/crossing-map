# Stage 3 review packet: the relief experiment

## What was built

- **Elevation.** 13 Copernicus GLO-30 tiles (493 MB) under the journeys corridor and the Casas Grandes–Babícora country, and AWS Terrain Tiles repacked to `terrain.pmtiles` (decision 0011).
- **Peaks.** `pipeline/src/crossing/peaks.py` finds 275 summits with at least 300 m topographic prominence, 159 of them named from GNIS or GeoNames, plus the book's Animas Peak, Gillespie Mountain and Black Point. As a check against published values: Chiricahua Peak 1,563 m prominence, Big Hatchet Peak 1,110 m, Animas Peak 967 m. Result: `data/mountain_glyphs.geojson`.
- **Mountain glyphs.** 12 shapes plus 12 mirrored twins, lit from the north-west, with paper fill so they knock out the hachures behind them. Each peak takes a stable shape, flip, scale and rotation from its id; size follows prominence. `art/glyphs/make_glyphs.py` generates them and builds the sprite with `spreet`. **These are generated stand-ins.** The plan wants about 12 drawn by hand, traced from the Wheeler, Ehrenberg or Guild references.
- **Hachures.** Huffman's script, run unmodified in headless QGIS 4 (decision 0013), on three test areas at two scales: fine (30 m DEM, 90–240 m spacing, for zoom 10 and up) and coarse (90 m DEM, 270–720 m spacing, for zoom 7–9). Each run takes 14–101 seconds.
- **Hillshade.** MapLibre's multidirectional hillshade over `terrain.pmtiles`, tinted sepia.
- **The comparison sheet.** `sheet/peloncillos.jpg`, `sheet/pilares.jpg`, `sheet/babicora.jpg`: six treatments at zoom 7, 9 and 11 for each test area, captured at 2x pixel density and laid out at full size (5,920 x 7,298 px), so you can zoom in to individual strokes. Rebuild with `tools/relief-sheet.mjs`.

The public site shows **glyphs only** until you choose. The hachure tiles are a local review file and are not published.

## The six treatments

| Treatment | What it shows |
| --- | --- |
| Survey | slope-weighted hachures plus glyphs; fine detail from the script's short split pieces |
| Survey, whole lines | the same, with fine detail from the script's whole lines, each weighted by its mean slope |
| Survey, no glyphs | hachures alone |
| Sierra | the same hachures, dashed and heavier, with stipple on steep ground, plus glyphs |
| Swiss accent | sepia hillshade, hachures only on each scale's steepest ground (fine lines 25° and up, coarse 18° and up), plus glyphs |
| Control | hillshade only |

Hachures exist only inside the three test areas, which is why they end in square edges.

## What I see

- **Zoom 7.** No hachure treatment reads at this scale; the lines are too small. The glyphs carry the relief, and without them the map looks empty. That is a point in favour of keeping glyphs.
- **Zoom 9.** The coarse Survey hachures read as engraved relief around the Pilares and the Cabellera. The hillshade treatments read more clearly, but look modern next to the ink.
- **Zoom 11.** At full resolution the fine hachures are short strokes with varied directions, not the orderly downslope strokes of a survey sheet. Whole lines look almost the same as split pieces: a whole line averages about three pieces (median about 270 m, 5 px at this zoom). A test on the Pilares with a smoother DEM (Gaussian of 3 cells) and 60 spacing checks instead of 125 made lines only about 20% longer. On these dissected desert ranges, at 30 m, this is what the method produces. The hillshade turns blurry, because the terrain archive stops at zoom 10 and MapLibre stretches it.
- **Sierra** comes out almost identical to Survey. A dash pattern on Huffman's lines is not the short, dense hatching of the SCOP and Graves maps. A true Sierra look would need its own line generator.
- **Swiss** now shows hachures at every zoom. Whole lines get a mean slope sampled from their DEM, and each scale has its own steep threshold, because the 90 m DEM is smoother (median line slope 11–16° against 18–22° at 30 m).

## My recommendation

Two candidates, and the choice is about taste more than accuracy:

- **Survey, mixed by zoom:** glyphs alone at zoom 6–8, glyphs with coarse hachures at 9, glyphs with fine hachures from 10. All ink, no raster. At zoom 11 the hachures read as dense engraved texture rather than neat strokes.
- **Swiss accent:** a light sepia hillshade carries the landform at every zoom, with hachures only on the steepest ground and glyphs on the peaks. Calmer at zoom 11, but the hillshade blurs there and reads more modern.

Either can be refined later by hand for key ranges (plan Phase 2).

## Questions for you

1. **Which treatment, or which mix by zoom?** The choice becomes a decision record, and production relief follows: the adapted, vendored hachure script with absolute slope limits, run over the journeys corridor.
2. **Glyph density.** Small peaks appear from zoom 9, and at that zoom the map gets busy. Should they wait until zoom 10?
3. **Glyph drawings.** Keep the generated set, or will you draw or trace the 12 shapes?

## Not done in this stage

- Production relief tiles: these wait for your pick.
- The lamplight (dark) theme's glyph sprite.
