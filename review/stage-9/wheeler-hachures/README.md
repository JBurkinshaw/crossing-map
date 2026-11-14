# Wheeler hachures for the test area

This packet covers the Wheeler cards "Ridges, flat tops and valley floors left white" and "Escarpments as a single comb" (`review/stage-8/wheeler/README.md`, Relief findings 6 to 8). They are built as hachures for the test area only (109.6 to 108.4° W, 30.5 to 31.6° N) and shown in the lab. The production build does not change.

## What changed

- `pipeline/src/crossing/wheeler_hachures.py` (new). The test build: the vendored generator on the production 40 km tile grid at Wheeler settings, then strokes cut, cleared and measured in numpy.
- `pipeline/src/crossing/hachures.py`. New options `--style wheeler --bbox W S E N --out DIR`. The default (`--style production`) takes the same path as before: the new code is one early branch after the arguments are read. `--out` inside `private/cache/relief/production/` is refused.
- `tiles/build_relief.py`. New options `--style wheeler [--src DIR]`, which pack `hachure` and `rim` into `tiles/out/lab-wheeler-hachures.pmtiles`. The default builds the three production archives as before.
- `site/src/lab/wheeler/subset/hachures.ts` (new). `subsetHachures(style)` adds the archive and two layers. Inside the box it hides the site's `hachure-*` layers with a `within` filter (a stroke that crosses the box edge still draws).
- `site/src/lab/wheeler/wheelerStyle.ts`. A `subsetHachures` parameter (off in both presets) and one call.
- `site/src/lab/wheeler/WheelerLab.tsx`. The toggle "Wheeler hachures (test area)" and a place button, "Test area: bootheel and Bavispe". The toggle list's type now comes from `Params`, so the toggle does not need a learning card.
- `tools/wheeler-hachures-shots.mjs` (new). The screenshots below.

## How to run and see it

```sh
QGIS_ENV=/Users/jb/mamba/envs/qgis uv run --project pipeline python -m crossing.hachures \
  --style wheeler --bbox -109.6 30.5 -108.4 31.6 --out private/cache/relief/wheeler-test --jobs 6
uv run --project pipeline python -m tiles.build_relief --style wheeler
cp tiles/out/lab-wheeler-hachures.pmtiles site/public/tiles/   # or: python -m tiles.install
cd site && npm run dev -- --port 5194
```

Open `/lab.html#wheeler`, press "Test area: bootheel and Bavispe", then tick "Wheeler hachures (test area)". To make the screenshots, run `node tools/wheeler-hachures-shots.mjs http://localhost:5194/` with the dev server running.

Delete a tile's `*-main.geojson` in `private/cache/relief/wheeler-test/tiles/` to run that tile again. Everything after the generator runs again on every call.

## How it works

**Scale.** Wheeler's sizes are set in millimetres at zoom 11 (the shared type scale's zoom) on a 96 dpi screen. MapLibre zooms use 512 px tiles, so 1 px = 78,271.5 m × cos(lat) / 2^z = 32.74 m at zoom 11 and 31.05° N, and 1 px = 0.2646 mm.

| Wheeler | px at z11 | metres |
| --- | --- | --- |
| stroke width 0.14 mm | 0.53 | 17 |
| stroke length 0.45 mm (gentle) | 1.70 | 56 |
| stroke length 0.72 mm (steep; 0.65 to 0.8) | 2.72 (2.46 to 3.02) | 89 (80 to 99) |
| comb spacing (card: 3 px) | 3 | 98 |
| wedge top 0.37 mm | 1.40 | 46 |
| wedge length 0.5 to 1 mm | 1.9 to 3.8 | 62 to 124 |

The lab draws strokes at 0.42 px at zoom 10, 0.53 px at 11, 0.8 px at 12 and 1.2 px at 13. At zoom 10 it draws only 70% of them (by `Rand`). The wedges are polygons drawn to scale.

Note: the stage 8 packet says sheet 83 is "about our zoom 10" and 70A "about zoom 11". That matches 256 px tile zooms. In MapLibre zooms, 70A (1:253,440, 67 m per px) is zoom 9.9 and sheet 83 is zoom 8.9. So at zoom 11 our strokes are Wheeler's size on screen, but cover half the ground they cover on 70A.

**Strokes.**
- The generator (decision 0015, unchanged) runs from 6° of slope. Its spacing goes from 4.5 cells (135 m) at 6° down to 1 cell (30 m) at 25° and steeper. It writes whole fall lines.
- Each line is taken downhill and cut into strokes, one per row. A stroke runs 56 m (10° and gentler) to 89 m (25° and steeper), or stops at 92% of its row, whichever comes first.
- A row is a stroke length over its duty: 0.55 on gentle ground (broken strokes) to 0.85 on steep ground. Rows come from a field, height ÷ (row length × tan of the slope smoothed over about 300 m). Strokes on neighbouring lines start on the same rows, so they line up along the contour as Wheeler's do.
- `Slope`, `Aspect` and `Rand` come from `crossing.hachures.stroke_properties`, as in production. `cls` gives the slope class.

**Ridge lines: D8 flow accumulation on the upside-down DEM.**
- Method: each cell passes its count to its steepest-rising neighbour. A ridge cell is one with at least 150 cells (0.135 km²) draining to it this way, and at least 40 m above the lowest ground within 500 m. Strokes are cleared within one stroke length (56 to 89 m) of a ridge cell, so each crest is a white parting about two stroke lengths wide.
- Why this method: it gives connected lines one cell wide (no skeletonising), it reaches into the spurs, and one threshold (the area that rises to a crest) sets how minor a spur may be. On the Animas tile, ridge cells stand on average 2.8 m above the mean height within 75 m (0.4 m for all hill ground), so they are on crests.
- Why not the alternatives:
  - `private/cache/geomorphons/` holds only small chips around candidate peaks (for the summit search), not rasters of the whole area. No GRASS or WhiteboxTools is installed for `r.geomorphon`.
  - The Raised view's `plan_oblique.ridges()` needs 100 m of relief and 500 m of line, which drops most spurs.

**Summits.** A clear disc one stroke length across goes around each summit glyph in `data/mountain_glyphs.geojson` (not passes). The same goes for each DEM cell that is the highest within 600 m and at least 60 m above the ground within 500 m.

**Flat tops and valley floors.** Strokes are cleared where all of these hold:
- the slope (DEM smoothed again, σ 1 cell) is under 4°;
- the relief within 150 m is under 15 m;
- the cell is in the top or bottom 35% of the relief within 1.5 km;
- the flat patch is at least 0.05 km².

The generator already stops at 6°, so this mostly trims stroke ends on mesa tops and floors.

**Rims.**
- Detection: the edge of flat ground (under 6°) is traced with `gdal_contour`, on a version smoothed by σ 2 cells, so specks of flat ground do not count. A run of that edge is a rim where all of these hold:
  - slope over 25° lies within 100 m;
  - the flat side is higher than the steep ground (the top of a scarp, not its foot);
  - the ground drops at least 30 m within 300 m;
  - the run is at least 300 m long.
- Wedges: along each rim, one wedge every 98 m (3 px). Each is 46 m wide at the rim, tapers to a point down the fall line of the face, and is as long as the face (62 to 124 m). The rim itself is not drawn.
- Ordinary strokes are skipped within 154 m of the rim.

## Measurements (clean run, all tiles, `stats.json`)

**Run time for the box** (13,971 km², 16 tiles, 6 jobs): 1,726 s wall, of which 1,599 s is the generator.
- Per tile: 20 s to 1,597 s.
- The Sierra tiles 660e-3360n and 700e-3360n took 27 and 21 min.
- The tile times add up to 6,902 s.

**Strokes:** 599,690 strokes and 75 rim wedges.

| Class (slope of the stroke) | Strokes | Median length |
| --- | --- | --- |
| flat (under 6°, stroke ends) | 4,350 | 45 m |
| gentle (6 to 15°) | 166,764 | 45 m |
| moderate (15 to 25°) | 244,437 | 55 m |
| steep (25° and over) | 184,139 | 60 m |
| rim wedges | 75 | |

**Ink cover**, as a share of each ground class in the box. Stroke bodies plus round caps at the lab's widths; overlaps are counted twice.

| Ground (km²) | z10 | z11 | z12 | Wheeler (packet) |
| --- | --- | --- | --- | --- |
| gentle 6 to 15° (3,261) | 7.0% | **5.6%** | 4.0% | about 5% |
| moderate 15 to 25° (2,284) | 15.7% | 12.7% | 9.1% | |
| steep 25° and over (969) | 31.7% | **25.9%** | 18.7% | 40 to 50% |
| within the combs | 23.3% | 23.3% | 23.3% | about 23% |

A first run at 1.3 to 7 cells spacing, with stroke lengths tied to the row, gave 1.6% gentle and 18.3% steep at zoom 11, so those settings were changed.

**Archive:** `lab-wheeler-hachures.pmtiles` is 20.9 MB (146 MB of GeoJSON), zooms 10 to 12. For comparison, the site's `relief.pmtiles` is 41 MB for the whole corridor.

**Production corridor estimate.** Production has 207,181 of its 1,090,120 fine strokes in this box, on 12,303 km² of the corridor's 105,999 km². So the box holds about 19% of the corridor's relief work, and the corridor is about 4.6 times this box (corrected for the box reaching outside the corridor).
- Generator: about 32,000 tile-seconds (8.9 h). That is about 1 to 1.5 h wall at 9 jobs, with single Sierra tiles of 25 min or more setting the tail.
- Archive: about 97 MB. It would need splitting to stay under 100 MB per file, and it would replace `relief.pmtiles` and `relief-dense.pmtiles` (66 MB together).

These are scaled by stroke counts and assume the corridor's terrain is like this box.

## What I see (screenshots)

The screenshots are in `private/review/stage-9/wheeler-hachures/`, named `<place>-z<10|11|12>-<before|after|story>.jpg`:
- `before`: the site's hachures.
- `after`: the toggle on.
- `story`: "All Wheeler" lettering plus the journeys drawn over, in the site's route inks.

Places: `peloncillos` (south end, Kilmer Peak), `animas` (Animas Peak), `mesas` (Mesa la Chata and Mesa el Güérigo by the Bavispe), `rim` (an escarpment south of Cerro Agua Zarca).

- **Zoom 12** reads closest to Wheeler (`animas-z12-after`, `rim-z12-after`). Steep sides are dark, packed rows; gentle ground is a light broken stipple; crests and spurs show as white veins; valley floors and plains are blank.
- **Zoom 11** reads well in the ranges. Crest partings give the Animas Mountains a clear structure that the sepia strokes lack (`animas-z11-before` against `animas-z11-after`).
- **Zoom 10** is speckled and busy (`peloncillos-z10-after`), even with 70% of the strokes drawn. The ranges read as grey texture rather than form. Option: draw only the steep class there, or keep the site's coarse look below 10.5.
- **Ink #2e2010 against the type.** Spaced roman capitals of a landform name lose out where they cross the dense rows, because their halo is only 1 px and the text is at 78% opacity: "ANIMAS MOUNTAINS" in `animas-z11-story` breaks up. Summit glyphs and their italic names also sink into the strokes (`peloncillos-z11-story`, `animas-z11-after`). The brown-black is right for the strokes, but the type over it needs a wider paper halo (about 2 px), or the summit discs need to be larger than the glyphs.
- **Ink #2e2010 against the journeys.** The route lines hold up well. Oxblood and slate at 1.8 px stay clear over the strokes at every zoom, and the paper casing separates them (`peloncillos-z11-story`). The site's paper halo around the journeys (not drawn in the lab) would help further.
- **Contours.** These stay on (the card swaps only the hachures). At zoom 12 the orange-brown lines do not fight the brown-black strokes, but they add little where the rows already follow the contour.

## What does not work yet

- **Steep ground is too light:** 26% at zoom 11 against Wheeler's 40 to 50%. The width is fixed at 0.14 mm by the card, so the remaining levers are closer lines (the generator at 0.7 cells, which would roughly double the run time of the Sierra tiles) or longer steep strokes. Steep strokes have a median of 60 m against the 80 to 99 m target, because ridge clearances, summit discs and row ends cut many of them short.
- **Summit dots hardly show.** The ridge network runs up to every summit, so the summit disc (one stroke length across) sits inside the crest parting, which is about two stroke lengths wide. Wheeler's dot-in-a-rosette needs a disc wider than the parting (about three stroke lengths). It is not done here because the card asks for one stroke length; it is the `SUMMIT_DISC` setting.
- **Few rims.** The detector finds 75 wedges in the box, in short runs of 3 to 10. The GLO-30 DEM, smoothed by σ 1.5 cells for the generator, softens the breaks, and the box has few true table-lands. The combs it draws look right in kind (`rim-z12-after`), but they are short. Mesa el Malpaís has no rim detected. Babícora (outside the box) would test the comb better.
- **The wedges look heavy at zoom 12.** They are drawn to scale, so they double in size with each zoom while the strokes do not.
- **Valley floors** are blank where they are flat. Narrow canyon floors still carry strokes from both sides, so the drainage does not yet read as Wheeler's "white tree". A channel clearance (the same accumulation run on the DEM the right way up) would do it, but the card did not ask for it.
- The `within` filter keeps site strokes that cross the box edge, so a thin seam of double strokes shows along the box edge.

## Open questions for the owner

1. Is 26% on steep ground enough, or should the steep spacing go to 0.7 cells (longer runs)?
2. Should summit discs be wider than the crest partings, so the summit dot shows?
3. Zoom 10: keep these strokes thinned, show only the steep class, or keep the site's look below 10.5?
4. Type over brown-black: widen the paper halo on landform names and summit labels to about 2 px?
5. Try the rim comb on the Babícora mesas, where the escarpments are real?

## Sources and licences

- Copernicus DEM GLO-30, © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA. Already cached: no network requests were made.
- The vendored hachure generator: Daniel Huffman, GPL-3.0 (decision 0015). It is run unchanged, and the GPL code and the MIT code meet only inside one process run.
- The Wheeler measurements are from the stage 8 packet. No Rumsey scan was used, traced or copied.
