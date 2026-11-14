# Stage 3 review packet: the relief experiment

> **Since this packet (13 November 2026).** The glyph counts here are from the first run: there are now 1,004 glyphs at 200 m prominence, in seven families. The lamplight theme has been removed.

## What was built

- **Elevation.** 13 Copernicus GLO-30 tiles (493 MB) under the journeys corridor and the Casas Grandes–Babícora country, and AWS Terrain Tiles repacked to `terrain.pmtiles` (decision 0011).
- **Peaks.** `pipeline/src/crossing/peaks.py` finds 274 summits with at least 300 m topographic prominence, 186 of them named from GNIS or GeoNames, plus 70 named mesas and cones from 100 m (see Landforms), and the book's Animas Peak, Gillespie Mountain and Black Point: 345 glyphs. As a check against published values: Chiricahua Peak 1,563 m prominence, Big Hatchet Peak 1,110 m, Animas Peak 967 m. Result: `data/mountain_glyphs.geojson`.
- **Mountain glyphs.** Six landform families of 12 shapes, each with a mirrored twin (see Landforms below), lit from the north-west, with paper fill so they knock out the hachures behind them. Each peak takes a stable shape, flip, scale and rotation from its id; size follows prominence. `art/glyphs/make_glyphs.py` generates them and builds the sprite with `spreet`. **These are generated stand-ins.** The plan wants about 12 drawn by hand, traced from the Wheeler, Ehrenberg or Guild references.
- **Hachures.** Huffman's script, run unmodified in headless QGIS 4 (decision 0013), on three test areas at two scales: fine (30 m DEM, 90–240 m spacing, for zoom 10 and up) and coarse (90 m DEM, 270–720 m spacing, for zoom 7–9). Each run takes 14–101 seconds.
- **Hillshade.** MapLibre's multidirectional hillshade over `terrain.pmtiles`, tinted sepia.
- **The comparison sheet.** `sheet/peloncillos.jpg`, `sheet/pilares.jpg`, `sheet/babicora.jpg`: eleven treatments at zoom 7, 9 and 11 for each test area, captured at 2x pixel density and laid out at full size (5,920 x 15,842 px), so you can zoom in to individual strokes. The sheets were removed from the repository on 12 November 2026, once decision 0016 replaced this treatment; they remain in git history (`git show dc59888:review/stage-3/sheet/pilares.jpg > pilares.jpg`). The scripts that made them are gone too: the unmodified generator they ran no longer runs.

The public site shows **glyphs only** until you choose. The hachure tiles are a local review file and are not published.

## The eleven treatments

| Treatment | What it shows |
| --- | --- |
| Survey | slope-weighted hachures plus glyphs; fine detail from the script's short split pieces |
| Survey, whole lines | the same, with fine detail from the script's whole lines, each weighted by its mean slope |
| Survey, no glyphs | hachures alone |
| Sierra | the same hachures, dashed and heavier, with stipple on steep ground, plus glyphs |
| Swiss accent | sepia hillshade, hachures only on each scale's steepest ground (fine lines 25° and up, coarse 18° and up), plus glyphs |
| Swiss, dense | the same, with hachures on about half the slopes at each scale (fine 18° and up, coarse 12° and up) |
| Swiss, full | hillshade with every hachure line, plus glyphs |
| Swiss, full, light | the same, with hachures in pale sepia (about 40% effective opacity) instead of ink |
| Swiss, full, thin | the same, in ink, at half the stroke width (0.12–0.65 px) |
| Swiss, full, soft | light and thin combined: pale sepia at half the stroke width |
| Control | hillshade only |

Hachures exist only inside the three 45 km test areas, which is why they end in square edges, and why at zoom 7 they show as two or three dark patches in an otherwise unhachured view (a zoom 7 view is about 450 km across). A production run would cover the journeys corridor.

## What I see

- **Zoom 7.** The coarse hachures pack into dark smudges: too dense and too heavy at this scale. Production should start them at zoom 8, or draw them much lighter at 7. The glyphs carry the relief here, and without them the map looks empty.
- **Zoom 9.** The coarse Survey hachures read as engraved relief around the Pilares and the Cabellera. The hillshade treatments read more clearly, but look modern next to the ink.
- **Zoom 11.** At full resolution the fine hachures are short strokes with varied directions, not the orderly downslope strokes of a survey sheet. Whole lines look almost the same as split pieces: a whole line averages about three pieces (median about 270 m, 5 px at this zoom). A test on the Pilares with a smoother DEM (Gaussian of 3 cells) and 60 spacing checks instead of 125 made lines only about 20% longer. On these dissected desert ranges, at 30 m, this is what the method produces. The hillshade turns blurry, because the terrain archive stops at zoom 10 and MapLibre stretches it.
- **Sierra** comes out almost identical to Survey. A dash pattern on Huffman's lines is not the short, dense hatching of the SCOP and Graves maps. A true Sierra look would need its own line generator.
- **Swiss** now shows hachures at every zoom. Whole lines get a mean slope sampled from their DEM, and each scale has its own steep threshold, because the 90 m DEM is smoother (median line slope 11–16° against 18–22° at 30 m).

## Your pick

**Swiss, full, soft** (decision 0014): every hachure, in pale sepia at half the stroke width, over the sepia hillshade, with glyphs. At zoom 7 it stays a faint texture, with none of the ink treatments' smudging.

## My recommendation

Two candidates, and the choice is about taste more than accuracy:

- **Survey, mixed by zoom:** glyphs alone at zoom 6–8, glyphs with coarse hachures at 9, glyphs with fine hachures from 10. All ink, no raster. At zoom 11 the hachures read as dense engraved texture rather than neat strokes.
- **Swiss accent, dense:** a light sepia hillshade carries the landform at every zoom, with hachures on the steeper half of the ground and glyphs on the peaks. The hachures follow the ridges the shading shows. Calmer than Survey at zoom 11, but the hillshade blurs there and reads more modern. (Plain Swiss, with only the steepest 10–30%, looked too sparse.) The full-density rows keep every line. In ink they compete with the shading at zoom 11. Pale sepia sinks them into the hillshade, so they read as texture, not as drawing. Half-width ink keeps the engraved look and stays quiet: of the three, it is the closest to a finished map.

Either can be refined later by hand for key ranges (plan Phase 2).

## Production relief

- **Vendored generator.** `pipeline/relief/hachures/` holds an adapted copy of Huffman's script under GPL-3.0, with absolute slope limits in degrees and an absolute contour interval in metres, so tiles match at their seams (decision 0015). Its README lists every change from upstream.
- **The run.** `crossing.hachures` runs it on a fixed UTM 12N tile grid:
  - fine: 30 m DEM, 20 tiles of 40 km over a corridor 20 km either side of the Part I journeys (15,900 km²).
  - coarse: 90 m DEM, 59 tiles of 60 km wherever the Copernicus tiles cover (139,000 km²).
- **The tiles.** `tiles/build_relief.py` packs the lines into `relief.pmtiles` (8.2 MB): 44,532 fine lines and 34,262 coarse ones. Inside the corridor, coarse lines show to zoom 9 and fine ones from zoom 10. Outside it, the coarse lines carry on to the last zoom, as the plan asks. The coarse lines fade in from zoom 6 to 8, so the Sierra Madre does not read as speckle.
- **On the map.** The soft treatment is now the site's default.
- **Small glyphs** wait until zoom 10, and the generated glyph families stay until hand-drawn ones replace them.

## Landforms

Each glyph now belongs to one of six families: peak, dome, mesa, butte, cone or ridge. `landforms/glyphs.png` shows all 144 shapes, 12 per family plus their mirrored twins. The map views in `landforms/` are centred on the densest clusters of mesas, domes and ridges, at zoom 9.5 with the soft relief. Rebuild them with `tools/landform-sheet.mjs`.

**How a summit gets its family.** `pipeline/src/crossing/landforms.py` gives every summit points for each landform, and the landform with the most points wins. All weights and thresholds are in `pipeline/seeds/landforms.toml`, with comments that explain each one:

- **Prior.** Every summit starts with 1 point for peak, so a summit with no other evidence stays a peak.
- **Name words.** A word that states the shape scores about 4 (mesa, butte, cuchilla, volcán), a weaker word less (loma 3, hill 1, cordón 2).
- **Feature codes.** The matched name's GeoNames code or GNIS class: MESA +3 mesa, HLL +1 dome, RDGE +2 ridge, VLC +3 cone.
- **DEM rules.** Measurements of the 30 m Copernicus DEM around the summit, each turned into points by a ramp: the share of the upper slopes that is flat top, the slope of the top and of the flanks, the top's width against its relief, and the top's elongation. A rule can have a `gate`, a second ramp its points are multiplied by. The butte rule only counts where the top is flat, for example.

`landforms.csv` lists every summit's measurements, each rule's points, the scores, and the winner. Where a name states a shape, it also gives the DEM's own pick beside the name's.

**Results:** 216 peaks, 86 mesas, 25 domes, 14 ridges, 3 buttes and 1 cone. 94 summits lead by less than 1 point and are marked for review. As a check, where a name states the shape, the DEM alone agrees for 17 of 18 peaks and 40 of 68 mesas, but only 5 of 23 lomas. Many Mexican "lomas" are as steep as peaks, so for domes the name does most of the work. Cones come only from names: at 30 m, a cinder cone looks like any small, steep peak.

**More summits.** `crossing.peaks` now matches names from hills, mesas, ridges and volcanoes as well as summits, and keeps a summit or mountain name when one is in range. It adds 70 named mesas and cones down to 100 m prominence, which brings the total to 345 glyphs. 28 previously unnamed summits now have names, and no existing name changed.

## Questions for you

1. ~~Which treatment?~~ Answered: Swiss, full, soft.
2. ~~Glyph density.~~ Small glyphs now start at zoom 10.
3. ~~Glyph drawings.~~ The generated families stay.
4. **Landform weights.** Do the mesas and ridges on the views land where you expect? The weights are yours to tune in `pipeline/seeds/landforms.toml`.

## Not done in this stage

- Fine hachures for Parts II–IV: the corridor follows the journeys, so it grows when their routes are drawn in stage 4. The fixed tile grid adds tiles without redoing these.
- The lamplight (dark) theme's glyph sprite.
