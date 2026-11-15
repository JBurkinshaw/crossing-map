# Wheeler hachures over the journeys corridor

The Wheeler hachures from the test box (`review/stage-9/wheeler-hachures/README.md`) now cover the same ground as the production fine hachures (the journeys corridor, 20 km either side of the legs ridden or walked), and the site's main map draws them there. The coarse hachures outside the corridor are unchanged. The production fine and dense hachures are kept, one switch away. Decision record: `docs/decisions/0024-wheeler-hachures.md` (proposed).

## What changed

- `pipeline/src/crossing/hachures.py`. `--style wheeler` takes `--region corridor` in place of `--bbox`. The fine scale's region is now `fine_region()`, used by both production and the Wheeler corridor build, so the two cover exactly the same ground. Production behaviour does not change.
- `pipeline/src/crossing/wheeler_hachures.py`. `build()` takes a region (UTM polygon) instead of a box; `bbox_region()` turns a box into one, so `--bbox` works as before. `stats.json` names the region under `extent` (it was `bbox`). The settings are unchanged.
- `tiles/build_relief.py`. `--style wheeler --region corridor` writes `relief-wheeler.pmtiles` (zoom 10-11) and `relief-wheeler-12.pmtiles` (zoom 12), each with the layers `coarse` (a copy of the production coarse strokes), `hachure` and `rim`. `--style wheeler` alone still writes the lab archive.
- `site/src/map/relief.ts`. `HACHURE_SET = 'wheeler' as HachureSet`; set it to `'production'` to get the old set back. Only `reliefSources` (through a new `hachureSources`) and the hachure layers of `s5Lines` changed, plus the new `WHEELER_PARTS`, `WHEELER_WIDTH`, `WHEELER_OPACITY`, `wheelerLines` and a module-level `strokes` helper (moved out of `s5Lines` unchanged). One comment line at the top of the file changed ("hachures (HACHURE_SET)").
- `tools/wheeler-corridor-shots.mjs` (new). The screenshots below.
- Docs: `docs/pipeline.md`, `docs/releasing-tiles.md`, `docs/design.md` (5.2), `docs/roadmap.md`, `docs/CHANGELOG.md`, `docs/decisions/README.md`, `docs/decisions/0024-wheeler-hachures.md`.

## Layers on the site (Wheeler set)

| Layer id | Source | Zooms | What |
| --- | --- | --- | --- |
| `hachure-coarse`, `hachure-coarse-copy` | `relief-wheeler` | 10 to 12 | coarse strokes outside the corridor, paint as before |
| `hachure-wheeler` | `relief-wheeler` | 10 to 12 | Wheeler strokes |
| `rim-wedge` | `relief-wheeler` | 10 to 12 | rim wedges (fill) |
| `hachure-coarse-12`, `hachure-coarse-12-copy`, `hachure-wheeler-12`, `rim-wedge-12` | `relief-wheeler-12` | 12 and up | the same at zoom 12, over-zoomed above |

The wedge layer is not named `hachure-*`, because the labs (`lab/hillshade/settings.ts`, `lab/wheeler/wheelerStyle.ts`) restyle every `hachure-*` layer as a line. The Raised view hides all of these (they are not in `KEPT_IN_RAISED`), and Tilted and Compare draw them as in Flat. Checked in a browser: Raised hides them, Tilted and Flat show them, no console errors (`views-*.jpg`).

## How to run

```sh
QGIS_ENV=/Users/jb/mamba/envs/qgis uv run --project pipeline python -m crossing.hachures \
  --style wheeler --region corridor --out private/cache/relief/wheeler --jobs 9
uv run --project pipeline python -m tiles.build_relief --style wheeler --region corridor
uv run --project pipeline python -m tiles.install
cd site && npm run dev
```

The 16 test-box tiles were copied from `private/cache/relief/wheeler-test/tiles/` (same grid, same settings, so the same files), so 71 of the 87 tiles ran.

## Measurements

**Run time.** 4,068 s wall (68 min) at 9 jobs, of which 3,496 s was the generator and about 570 s cutting, clearing and writing the strokes. Peak memory 6.3 GB. The 71 new tiles took 28,716 tile-seconds; 11 of them over 15 min, the longest 700e-3280n at 2,940 s and 700e-3240n at 2,562 s (Sierra Madre). Packing took 55 s.

**Region.** 87 tiles of 40 km, 81,722 km² (the corridor where the DEM covers it).

**Strokes:** 2,789,500 strokes and 1,560 rim wedges.

| Class | Strokes | Median length |
| --- | --- | --- |
| flat (stroke ends under 6°) | 20,772 | 45 m |
| gentle (6 to 15°) | 837,768 | 45 m |
| moderate (15 to 25°) | 1,129,562 | 55 m |
| steep (25° and over) | 801,398 | 60 m |
| rim wedges | 1,560 | |

**Ink cover** (share of each ground class, at the site's widths): gentle 7.1 / 5.7 / 4.1% at zooms 10 / 11 / 12; moderate 15.9 / 12.9 / 9.3%; steep 32.0 / 26.1 / 18.9%; within the combs 23.3%. These match the test box to within a few tenths.

**Archives** (in `tiles/out/` and `site/public/tiles/`):

| Archive | Zooms | Size |
| --- | --- | --- |
| `relief-wheeler.pmtiles` | 10-11 | 64.4 MB |
| `relief-wheeler-12.pmtiles` | 12 | 35.4 MB |

The GeoJSON is 679 MB of strokes, 0.4 MB of wedges and 6.5 MB of coarse strokes. The production archives (`relief.pmtiles` 41 MB, `relief-dense.pmtiles` 25 MB, `contours.pmtiles` 50 MB) and `private/cache/relief/production/` were not touched.

## Release

The next tile release must upload `relief-wheeler.pmtiles` and `relief-wheeler-12.pmtiles` with every archive the site already reads (`base`, `relief`, `relief-dense`, `contours`, `terrain`, `oblique-1`, `oblique-2`), so both hachure sets are in one tag (`docs/releasing-tiles.md`). Until then the deployed site, which pins `tiles/release.txt`, has no `relief-wheeler*` archives: merging this with `HACHURE_SET = 'wheeler'` before the release would leave the corridor and the coarse strokes without hachures. Either release first, or merge with `'production'`.

## Screenshots

In `private/review/stage-9/wheeler-hachures-corridor/`, desktop (1400 × 900), named `<place>-z<10|11|12>-<before|after>.jpg`. `before` is the production set; `after` the Wheeler set. Places: `peloncillos` (-109.013, 31.667), `animas` (-108.77, 31.56), `sierra-el-tigre` (-109.165, 30.55), `babicora` (-107.75, 29.25). Also `views-raised.jpg`, `views-tilted.jpg`, `views-flat.jpg` at the Animas, zoom 11.

What I see:
- Zoom 11 and 12 in the ranges read as in the lab: dense dark rows on steep sides, white crest partings, blank valley floors (`sierra-el-tigre-z12-after`, `animas-z11-after`).
- Zoom 10 is speckled (`peloncillos-z10-after`), as the test box packet said.
- The corridor edge shows the change of style: Wheeler strokes inside, the sepia coarse strokes outside (the Chiricahuas in `peloncillos-z10-after`). It was a change of density before; now it is a change of look too.
- Near Babícora the plain is blank and the sierra to the south carries strokes. No rim comb shows in the views taken.

## What looks wrong or is open

1. **Merge order** (see Release): the site needs the new archives before `'wheeler'` goes live.
2. **Raised view** still draws the production-style strokes from `oblique-*.pmtiles`, so Flat and Raised differ in the corridor.
3. **Corridor edge** is now a change of style as well as density; the roadmap's corridor-edge question matters more.
4. **Steep ground** is at 26% ink at zoom 11 against Wheeler's 40 to 50% (unchanged from the test box; settings not retuned as asked).
5. **Few rims**: 1,560 wedges over the whole corridor, so the comb is rare.
6. **Design latitude** is fixed at 31.05° N: stroke sizes are set in metres there, so at 28° N they are about 3% larger on screen and at 34° N about 3% smaller. Not visible, but noted in the code.
7. **Release size** grows by about 100 MB while both sets are kept; check the 1 GB Pages limit if the preview ships its own tiles.

## Sources and licences

As in the test box packet: Copernicus DEM GLO-30 (© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA), already cached; the vendored hachure generator (Daniel Huffman, GPL-3.0, decision 0015), run unchanged. No network requests were made. No Rumsey scan was used.
