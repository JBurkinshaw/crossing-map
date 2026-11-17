# Oblique looks: a side-by-side lab

The owner finds the Oblique view flat and asked for looks after the oblique maps in Carl Churchill's "Variety in hachure" (`docs/inspiration/churchill.md`), with land cover and local features in one of them. This experiment draws two test boxes in 25 looks and shows them two at a time in the lab. The second round, after the owner picked the Atlas of Oblique Maps look, adds combinations of it with Guanabara's stipple and the comic look's simpler parts, on the site's paper, and with mapped land cover. The third round tries the CEC's continental land cover, which has no seam at the border, alone and read with Brown's height bands.

**Outcome.** The owner chose `cec-brown` (classic tints), at lean 4. Decision 0040 records it, and `crossing.plan_oblique` and `crossing.landcover` now build it for the whole corridor. The lab section and its images were removed once the choice was made. `render.py` was written against the earlier `crossing.plan_oblique` (lean 2, Huffman's strokes, `po.FINE`), so it no longer runs as it stands; it is kept as the record of how each look was drawn. The sections below describe the experiment as it stood before the choice.

## How it was run

```sh
uv run --project pipeline python review/experiments/raised-styles/render.py                 # all looks, about 12 minutes
uv run --project pipeline python review/experiments/raised-styles/render.py comic           # one look
uv run --project pipeline python review/experiments/raised-styles/render.py border-current  # a look in the border box
```

The looks were shown side by side in a lab section, now removed. `crossing.fetch_landcover` fetches the CEC land cover once (below). `render.py` makes no network requests. It reads the Copernicus tiles, the production fine hachure cache (`private/cache/relief/production/fine-s2-4.5-split/`, the tiles under each box), the base map's sources, as `crossing.plan_oblique` does, and the land cover cached below. It caches the DEMs and each lean's line work in `private/cache/raised-styles/`, and writes `site/public/lab/raised/<look>.webp` (1600 px wide).

## The test boxes

Both are in UTM zone 12N (EPSG:32612, WGS 84), 36 by 34 km, drawn at 22.5 m per pixel (about zoom 11.5).

- **pilares**: 662,000 to 698,000 E, 3,380,000 to 3,414,000 N. The Sierra de los Pilares de Teras, El Tigre, and the Bavispe at Colonia Morelos and Colonia Oaxaca, all in Mexico. The ground runs from 801 to 2,441 m.
- **border**: 677,000 to 713,000 E, 3,451,000 to 3,485,000 N. The Guadalupe Mountains and Cloverdale, across the border, so that both land cover sources show. Its looks are named `border-<look>`.

## Land cover

### INEGI and NLCD

Fetched on 16 November 2026, four requests in all, each logged in the `requests.log` beside the data:

- **Mexico: INEGI's *Uso del suelo y vegetación*, 1:250,000**, as SEMARNAT's Atlas 2022 republishes it (ArcGIS service `Atlas_2022/Vegetacion_2022`, layer 2, "Vegetación actual"), queried by bounding box: `private/cache/landcover/inegi-s7/pilares.geojson` and `border.geojson`. INEGI's own download page builds its links in JavaScript, and CONAFOR's IDEFOR copy of the national Serie VII set returned 503, so this service stood in. It does not name its series; its classes and fields (`CLAVE`, `DESCRIPCIO`) are INEGI's. Before a look ships, the data should come from INEGI's Serie VII download itself.
- **US: NLCD 2021 land cover (MRLC)**, a clip of the border box from MRLC's WCS, returned in WGS 84 at about 33 m: `private/cache/landcover/nlcd/border.tif`.

Both are folded into one legend (`LEGEND` in `render.py`):

| Class | INEGI `CLAVE` | NLCD | Tint |
| --- | --- | --- | --- |
| water | H2O | 11 | blue |
| riparian | BG, VG (gallery forest and vegetation) | 90, 95 | bright green |
| pine | BP, BPQ | none | deep sage |
| oak | BQ, BQP, and secondary oak (VSA/BQ, VSa/BQ, VSa/BQP, VSa/BPQ) | 41, 42, 43 | olive |
| grass | PN, PI, PC, VSa/PN | 71 | straw |
| scrub | MDM, MDR, MK, ML | 52, 31 | adobe |
| fields | RA, RAS | 81, 82 | yellow-green |
| town | AH | 21 to 24 | brick |

The classes are rasterised on each box's 30 m grid, INEGI over NLCD, then sieved so that patches under 40 cells (3.6 ha) join their neighbours. The view's own surface lookup puts each class where its ground is seen, so the tints rise and hide with the relief.

**Two seams come from the data, not the drawing.** The tints change along the border, because NLCD classes most of the US side as shrub (52) and INEGI most of the Mexican side as grassland (PN). And NLCD changes along a north-south line at about 109.05° W, the Arizona–New Mexico line, likely a seam between its mapping zones.

### CEC

**The Commission for Environmental Cooperation's *North American Land Cover 2020*, 30 m, version 2** ([CEC atlas](https://www.cec.org/north-american-environmental-atlas/land-cover-30m-2020/)): one Landsat classification for Canada, the US and Mexico, in 19 classes. The CEC ships each country's GeoTIFF deflated inside a zip, so GDAL cannot read a window of it remotely. `crossing.fetch_landcover` (first `fetch_cec.py` here) reads the Mexico and US zips' directories and downloads only the two GeoTIFFs (four ranged requests, 1.1 GB, logged in `private/cache/landcover/cec/requests.log`) to `private/cache/landcover/cec/mex.tif` and `usa.tif` (1.4 GB inflated). The country files are clips of one map, so they meet without a seam; Mexico's part is from 2020 imagery and the conterminous US's from 2019 (per [Google Earth Engine's catalog](https://developers.google.com/earth-engine/datasets/catalog/USGS_NLCD_RELEASES_2020_REL_NALCMS)).

| Class | CEC codes, read alone (`cec`) |
| --- | --- |
| water | 18 |
| riparian | 14 (wetland) |
| pine | 1, 2, 6 (needleleaf and mixed forest) |
| oak | 3, 4, 5 (broadleaf forest) |
| grass | 9, 10, 12 |
| scrub | 7, 8, 11, 13, 16 (shrubland and barren) |
| fields | 15 |
| town | 17 |

In the Pilares box the CEC calls 44% of the ground temperate broadleaf deciduous forest, 37% shrubland, 13% grassland, and 3% needleleaf forest.

### CEC with Brown's bands

`cec-brown` reads the CEC map with the height bands `upolu` uses (after Brown's biotic communities; see the judgement calls). The CEC decides what height cannot: water, towns, fields, wetland, and grass against scrub. Height decides what the CEC cannot, which trees:

- CEC trees below the oak line are gallery forest; above it oak; above the pine line pine.
- CEC shrubland above the oak line, on a slope of 6° or more, is open Madrean woodland, so oak. On flatter ground it stays scrub.
- CEC trees and shrubland within 150 m of a stream of order 4 or more, below the oak line, are gallery forest.
- A north slope counts as up to 150 m higher, in proportion to how far it faces north.

## What every look shares

Each look calls `crossing.plan_oblique`'s own `Grid` and `build_strip`, so the shift (north by the lean times the height above the lowest ground), the hidden-ground cut, the crest outlines, the ridgelines, the rivers and the roads are the Oblique view's own. A look sets the lean and decides which strokes to draw and how.

The current look draws the production strokes with the site's paint (`obliqueLayers` in `site/src/map/relief.ts`), worked out at zoom 11.5. The other looks trace their own strokes down the fall line, from seeds on a jittered grid, so their density and weight can follow the light. Light and fall lines come from the smoothed 30 m DEM, smoothed again over 4 cells (120 m), so the strokes follow the main faces rather than every gully. Light comes from the north-west (azimuth 315°, altitude 45°).

## The looks

| Look | After | Lean | What changes |
| --- | --- | --- | --- |
| `current` | The site today | 2 | Nothing: the baseline |
| `steeper-toned` | Jenny and Patterson; Huffman's 3D hachures | 4 | The same strokes, over a hillshade shifted with the ground |
| `alpha` | Tau Rho Alpha, *Atlas of Oblique Maps* (1988) | 4 | Long strokes packed in shade, sparse in light; level dashes on the flats |
| `guanabara` | Holmes, *Estado da Guanabara* (1965) | 4 | Tapered stroke fans from the upper slopes, firm crests, stippled lowlands |
| `trentino` | AGS, Trentino block diagram (1918) | 3 | Pencil strokes on tan paper, blue rivers, red roads, the block's south wall |
| `comic` | Owens, *The Panama Canal* (1928) | 4 | Shade as solid black flames, middle tones hatched, lit faces blank |
| `upolu` | U.S. Ex. Ex., *Upolu* (1839) | 3 | Fine hachures and land cover in profile; towns as blocks |
| `atlas-paper` | Alpha, on the site's paper (`#f5edd3`) and ink (`#2b2118`) | 4 | Alpha's strokes as plain lines, not tapered polygons; the border dashed |
| `atlas-stipple` | Alpha and Guanabara | 4 | Stipple on the flats instead of level dashes |
| `atlas-comic` | Alpha and Owens | 4 | Lit faces blank, deepest shade packed with heavier strokes, heavier crests, rivers as two banks |
| `atlas-stipple-comic` | All three | 4 | Both of the above |
| `atlas-landcover` | All three, with land cover | 4 | Flat tints under `atlas-stipple-comic` |
| `atlas-landcover-cartoon` | All three, with land cover | 4 | Cel-shaded tints: two tones per class, edges in a darker tone |
| `cec`, `cec-cartoon` | All three, with the CEC's land cover | 4 | The CEC classes, read alone, in flat or cel-shaded tints |
| `cec-brown`, `cec-brown-cartoon` | All three, with the CEC read with Brown's bands | 4 | The CEC classes with the trees sorted by height |

The border box has `current`, `atlas-stipple-comic`, and every land cover look.

## Judgement calls

- **Lean 4.** Twice the site's lean. Over the box's 1,640 m of relief it moves the highest ground about 6.6 km north, so the DEM reaches 7 km south of the box for that ground to rise into view.
- **Land cover by height (`upolu`).** After Brown's biotic communities of the Madrean sky islands (Brown, ed., *Biotic Communities: Southwestern United States and Northwestern Mexico*, 1994): desert scrub and semi-desert grassland below about 1,250 m, oak woodland above, pine-oak above about 1,800 m, each about 150 m lower on slopes facing north, and cottonwood and sycamore within 150 m of the streams of order 4 and up. These are round numbers for a lab; the land cover looks use mapped classes instead.
- **The comic borrowings.** Only the parts that stay lines: blank lit faces (light above 0.72), a second set of seeds 30 m apart where the light is below 0.3, with strokes up to 0.9 px wider, crests at 1.7 px, and rivers as two ink banks with water between. The flames themselves are left out, because they are polygons.
- **Brown's bands with the CEC.** The 1,250 m oak line fits the Pilares box, but the basin floors in the border box (the Animas and San Luis valleys, 1,300 to 1,600 m) are above it and are grassland and desert scrub. So shrubland turns to oak only on slopes of 6° or more: Brown's Madrean woodland climbs the mountains and does not cover the basins. CEC trees in the valleys are taken as gallery forest, though some are likely mesquite bosque.
- **The legend.** NLCD's evergreen forest (42) goes to oak, not pine: in these ranges it is mostly oak, juniper and pinyon woodland. Secondary oak scrub (INEGI's `VSa/…`) goes to oak too.
- **The tints.** Flat school-atlas colours mixed 60% over the paper (classic) or 75% (cartoon); the cartoon's shaded tone is 82% of the lit one, and its edges 62%.
- **The block's wall** shows 500 m below the lowest ground, with a line every 100 m of height.

## What it would have taken to ship each

- `steeper-toned` is the smallest step: change `LEAN` in `crossing.plan_oblique` and add a pre-shifted shading raster (decision 0017 names it).
- `alpha`, `guanabara` and `comic` replace Huffman's generator in the Oblique view with this script's tracer. `alpha` stays as lines. Tapered strokes and flames are polygons, about three times the vertices.
- `upolu`'s symbols are points with icons, anchored at their base, which MapLibre draws well.
- The `atlas-*` combinations are lines plus, with stipple, points. The land cover tints need a raster shifted with the ground, like `steeper-toned`'s shading. With the CEC, the corridor's land cover is already in the cache; with INEGI and NLCD it needs a proper batch.
- `trentino`'s block suits a fixed image (the poster, or block diagrams on place cards, parked for Phase 2), not the slippy map.
