# Experiment: drafted inferred areas and a QGIS project to finish them

**Adopted on 14 November 2026 (decision 0020).** The drafts are now built: `crossing.area_drafts` writes the seed `pipeline/seeds/areas.geojson`, which `crossing.build_story` reads, and the QGIS project is `pipeline/qgis/areas.qgs`, editing that seed. The files this packet lists (drafts, CSV, images, the old project) are in `private/parked/areas-experiment/`; the report and images of a new run go to `private/review/areas/`. The owner's answers to the questions at the end: research a historical source for La Babícora and keep the DEM draft until then; move the pins into their drafts where the draft follows the evidence better (nine stops); straight lines between towns are fine for the old Mexican roads, and the cards say they need a historical source; no draft grows beyond its circle; no confidence on the site.

Decision 0008 says each inferred area should be drawn by hand in QGIS from the book's clues. Today the 57 `inferred-area` polygons in `data/areas.geojson` are geodesic circles from each stop's `radius_km`. This experiment cuts each circle to the ground its stop's reasoning describes, as a starting point for that hand drawing, and sets up a QGIS project to finish them. Nothing in `data/`, `pipeline/seeds/` or the site was changed.

## What is here

| File | What it is |
| --- | --- |
| `areas-draft.geojson` | The 57 drafts. Each keeps the properties of its old feature and adds `draft_rule`, `draft_confidence`, `old_km2`, `new_km2`, `pin_inside`, `pin_km` and `draft_notes`. |
| `areas-draft.csv` | The same per area as a table: rule, confidence, old and new km², whether the stop's pin is inside. |
| `contact-sheet-1.png` to `-3.png` | Before and after for every area: old circle dashed, draft filled by confidence (green high, amber medium, red low, grey kept), over a hillshade with streams. |
| `examples-best.png`, `examples-doubtful.png` | Larger views, with places and roads, of four good cuts and four doubtful ones. |
| `babicora-compare.geojson`, `.json`, `.png` | La Babícora from the four municipios, against the DEM draft. |
| `areas.qgs` | The QGIS project (relative paths). `qgis-project.png` is a render of it over the bootheel. |
| `layers/dem.vrt` | A VRT over the cached Copernicus tiles, for the project's hillshade. |

Code: `pipeline/src/crossing/area_drafts.py` (drafts, La Babícora, support layers, images) and `pipeline/src/crossing/area_drafts_qgis.py` (the project, run with QGIS's Python).

```sh
uv run --project pipeline --with matplotlib python -m crossing.area_drafts --images   # about 3 minutes
PYTHONPATH=$QGIS_ENV/share/qgis/python QT_QPA_PLATFORM=offscreen \
  $QGIS_ENV/bin/python3.14 pipeline/src/crossing/area_drafts_qgis.py
```

`--inspect` prints what lies in each circle (height range, named streams, roads), which is what the rules were written from. Matplotlib is only needed for the images, so it is pulled in with `--with` rather than added to the pipeline's dependencies.

## How the drafts are made

Each area is worked in an azimuthal equidistant projection centred on its stop, so the old circle is an exact circle. The rule for each area is a short function in `RULES` with its plain-words description beside it. The rules combine a few tools:

- terrain from the Copernicus 30 m DEM (resampled to 30, 60 or 90 m by circle size): below or above a contour, slope under a limit, ground near the lowest in the circle (a playa), height above a chosen river (valley floor or promontory), ground that looks down a set drop to the east (an escarpment's edge), and a viewshed (`gdal_viewshed`);
- lines: INEGI 1:50,000 streams and NHD flowlines (main stem picked by Strahler order, or named), Census TIGER roads, straight lines between the book's places where no old road is mapped, and the boundary along 31°20′ N and 31°47′ N;
- sides: west of a river (by the direction to its nearest cell), east of a town, north of a line.

The circle stays the upper bound. Slivers under two cells wide and holes under 0.25 km² are dropped. If a rule leaves almost nothing, the circle is kept. Confidence means how sure the draft is to contain the place, given the circle: **high** (the clue names the ground and the data finds it), **medium** (a judgement on width, threshold or a proxy line), **low** (leans on a reading that could be wrong), **kept** (nothing to cut by).

## Results

| Confidence | Areas | Old km² | Draft km² |
| --- | --- | --- | --- |
| high | 9 | 1,335 | 452 |
| medium | 30 | 5,930 | 2,483 |
| low | 9 | 4,329 | 1,427 |
| kept | 9 | 2,951 | 2,951 |
| **all** | **57** | **14,545** | **7,313** |

What works well:

- **Rivers.** Where the book puts a stop on a river, a corridor along the channel replaces a disc that was mostly hills: the Bavispe crossing (905 to 146 km²), Boyd's shooting at San José (50 to 18), the Casas Grandes River and the attack on the river trail, the gravel bar below Mata Ortiz.
- **Lines on the ground.** The boundary monuments and Dog Springs become bands along the line (113 to 68, 313 to 60 km²); Emory Pass and the waystation follow NM 152 and NM 27.
- **Basins and playas.** Playas Lake's bed, the Animas Plain below 1,650 m and the Babícora plains are clean DEM cuts.
- **The viewshed.** For "the lights of Casas Grandes to the west", the ground in sight of a light at Nuevo Casas Grandes and east of the town drops the hidden valleys (313 to 183 km²).

What does not work, or needs a person:

- **Escarpments.** "Looks down 300 m to the east" finds broken ridge pieces, not one rim (`j3-eastern-escarpment`, `j4-escarpment-rim`, both low). A hand-drawn line along the edge will be better.
- **Mexican roads.** No open map of the 1940s roads in Chihuahua is to hand, so straight lines between towns stand in (Las Varas to Madera, Las Varas to La Boquilla, Casas Grandes to San Diego). These bands are as good as that guess. OpenStreetMap would help but is ODbL, which would bind the derived areas.
- **Clanton and Foster draws.** NHD does not name the draws here; the strip between the GNIS points runs along the circle's mean slope, which may not be the way the draws run.
- **Kept circles** (9): the trucks, the blind man's house, Quijada's remuda, the tracking camp, the dry camp, Álamo, Boyd's grave (already 3 km²) and the plains camp.

14 stops' pins fall outside their drafts (`pin_km` gives the gap). Most are a few hundred metres off a river corridor. Four are worth a look because the draft follows the evidence better than the pin:

- `j3-huisiachepic`, 6.1 km: the pin is the straight-line midpoint between Mesa Tres Ríos and Huachinera, not on the river; the draft is on the upper Bavispe's main stem.
- `j4-san-simon`, 4.1 km: the draft follows NHD's named San Simon River; the pin is on the plain east of it.
- `j4-escarpment-rim`, 5.0 km, and `j4-wagon-road-crossing`, 3.4 km: low-confidence cuts, so here the pin may be the better guess.

## La Babícora

Municipio boundaries come from geoBoundaries (gbOpen MEX ADM2, boundary MEX-ADM2-50627088: the World Bank's municipios of 2012, licence CC BY 4.0, attribution "Runfola et al. 2020, geoBoundaries"). INEGI's Marco Geoestadístico per state was not used: its download pages are large and the state packages hold many layers we do not need. The file is cached in `private/cache/boundaries/geoboundaries/` with its metadata.

| | km² |
| --- | --- |
| Temósachic + Namiquipa + Madera + Gómez Farías | 18,726 (4,275 + 4,860 + 8,737 + 853) |
| DEM draft (basin floor below 2,200 m) | 1,104 |
| DEM draft inside the four municipios | 817 |
| DEM draft outside them (a northern lobe, in Ignacio Zaragoza) | 287 |
| The estate, as the plan gives it (about 360,000 ha) | about 3,600 |

The four municipios are five times the estate. They take in Madera's sierra, Temósachic and Santa Ana, and 16 stops the DEM draft does not (Las Varas, Madera, Namiquipa, the Santa María stream). The DEM draft is a third of the estate and spills north out of the four municipios. Neither is the estate. The municipios polygon is in `babicora-compare.geojson` as `region-la-babicora-municipios`, labelled "La Babícora (Hearst)" as the plan asks, with its reasoning written so as not to claim the estate's bounds.

## The QGIS project: how to finish the areas

Open `review/experiments/areas/areas.qgs` in QGIS 4. Layers, top to bottom: stops, **Draft areas (edit these)**, old circles (faint dashed outline), journeys, regions, the four municipios, streams, hillshade. Only the drafts are editable. The hillshade (`layers/dem.vrt` into `private/cache/dem/`) and the streams (`private/overnight/areas/streams.gpkg`) point into `private/`, so they show only on your machine; everything else is in the repo. Snapping is on for vertices and segments of every layer at 12 px, with intersection snapping, so an edge can follow a stream, a road or the old circle.

For each area, worst first (filter the layer on `"draft_confidence" IN ('low', 'kept')`, or sort the attribute table by `pin_km`):

1. Select the area and open its form (Identify, or the attribute table's form view). The **Draft** tab shows the rule used and its notes; the **Book** tab shows the stop's reasoning.
2. Check the draft against the clue: does it hold the ground the book describes, and does it stay inside the circle unless the evidence reaches beyond it? Make it no smaller than the evidence allows.
3. Edit with the Vertex tool, or redraw with Reshape Features. The Advanced Digitizing panel helps for lines along a bearing.
4. If you change the reasoning behind it, rewrite `draft_rule` in your own words. Set `draft_confidence` to `checked` when done.
5. Save the layer's edits. The file stays GeoJSON in lon/lat.

How the edited file goes back into the build (not done here; for the lead to decide):

1. Copy the finished file to `pipeline/seeds/areas.geojson` (only `id`, the geometry and `draft_rule` need to stay).
2. In `crossing.build_story`, where it calls `circle(...)` for a stop with `radius_km`, use the seed geometry when `area-<id>`'s stop has one, and keep the circle otherwise. Put `draft_rule` into the feature's reasoning or a new property. `uncertainty_m` can stay as the radius.
3. If a stop's pin should move into its area (the four above), change `lat`/`lon` in its stops CSV.
4. For La Babícora, either replace `region-la-babicora`'s geometry in `pipeline/seeds/regions.geojson` with the municipios polygon, or keep both and add the municipios as a second region feature, with the CC BY 4.0 attribution in the site's sources.
5. Run `crossing.build_story`, `crossing.validate` and the echo check, then rebuild the site data.

## Found on the way

INEGI's 1:50,000 network draws wide rivers as double lines, and their channels are `ENTIDAD = 'LINEA CENTRAL'`, not `'CORRIENTE DE AGUA'`. `tiles/mexico_rivers.py`, `crossing.plan_oblique` and `crossing.least_cost` keep only `'CORRIENTE DE AGUA'`, so they miss the main stems of the biggest rivers. Near Colonia Morelos only 0.7 km of the order 8 Bavispe was left out of about 20 km. This experiment includes both.

## Open questions for the owner

1. Which La Babícora outline: the DEM basin floor (too small, partly outside the four municipios), the four municipios (five times the estate), or a hand-drawn estate from a historical source?
2. Should stop pins move into their drafts where the draft follows the evidence better (Huisiachepic, San Simon)?
3. Is a straight line between towns acceptable as a stand-in for the old Mexican roads, or should those bands stay circles until a road source is found?
4. Should a draft ever grow beyond its circle? None does here; the escarpment and the plains camp suggest the circles there may be in the wrong place rather than too small.
5. Should the site show confidence, for example as a fill strength?

## Sources and licences

Copernicus DEM GLO-30 (© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA); INEGI Red Hidrográfica 1:50,000 edición 2.0; USGS NHD (public domain); US Census TIGER/Line 2023 roads (public domain); Natural Earth (public domain); geoBoundaries MEX ADM2 (CC BY 4.0). All were already cached except geoBoundaries (one download of 149 MB, recorded in `private/overnight/areas/refs/refs.csv`).
