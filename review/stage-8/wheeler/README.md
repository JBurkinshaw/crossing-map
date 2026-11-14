# Wheeler Survey study: lessons for the classic map

Two Wheeler Survey atlas sheets were studied at full resolution, against the classic map at the same kinds of places. This packet has the findings. The lab section `site/src/lab/wheeler/WheelerLab.tsx` lets you try the main ones on our real map. Nothing on the published site or in the tiles has changed; everything below is a proposal.

**The sheets.** Both are from the David Rumsey Map Collection, licensed CC BY-NC-SA. The scans are in `private/inspiration/rumsey/{70A,83}/` (git-ignored, with the catalogue text). No image, crop or tracing of them is in the repository. The descriptions and measurements here are our own.

| Sheet | Title | Issued | Scale | List no. | Catalogue |
| --- | --- | --- | --- | --- | --- |
| 70 (A) | Parts of Southern Colorado and Northern New Mexico | 7 May 1877 | 1:253,440 | 2738.076 | [search](https://www.davidrumsey.com/luna/servlet/view/search?q=2738.076) |
| 83 | Parts of Eastern and South Eastern Arizona, Western and South Western New Mexico | 18 March 1876 | 1:506,880 | 2738.097 | [search](https://www.davidrumsey.com/luna/servlet/view/search?q=2738.097) |

The links are catalogue searches by list number. The collection puts a bot check in front of its record pages, so the exact record URLs were not fetched. Sheet 83 covers our northern edge: the Peloncillos ("Peloncillo Range"), the San Simon valley ("San Simeon Plains"), Railroad Pass by Bowie, the Gila and Silver City. `docs/inspiration/rumsey.md` lists sheet 83 as list no. 2738.088 (an issue in the geological atlas). The copy the owner downloaded is the topographical issue, 2738.097.

**How it was measured.** The scans are about 115 px/cm (70A) and 119 px/cm (83), worked out from the graticule. Sizes below are on the printed sheet. The method:
- Tones are medians of sampled windows.
- Hachure statistics come from connected ink strokes in 1 to 2 cm windows; dense areas merge strokes, so lengths there are approximate.
- Type sizes were read off 1:1 crops.

At its printed size, sheet 83 is about our zoom 10 on a 96 dpi screen, and sheet 70A about zoom 11.

**How to see it.** The section is the Wheeler tab of the lab page:
1. Run `cd site && npm run dev -- --port 5193`.
2. Open `/lab.html#wheeler`.

Screenshots are in `shots/`, made with `tools/wheeler-shots.mjs`:
- `now-*`: the site today.
- `lab-<place>-today` and `lab-<place>-wheeler`: the lab with every parameter as today, then with all of them on.
- `lab-page-*`: the whole section on desktop and phone.

## What Wheeler does (by topic)

### Lettering

1. **Big rivers in spaced roman capitals.**
   - PURGATORY RIVER and CANADIAN RIVER (70A) are about 2.2 mm high, letter pitch about 43 px on the scan. That is roughly 0.9 em of space between letters.
   - The name follows the river's general run, not each bend, and appears once or twice per sheet.
   - On sheet 83, SALT RIVER and GILA RIVER use the same spaced capitals (the Salt in sloping capitals).
2. **Small rivers and creeks in italic upper and lower case**, about two-thirds the river size and close-set along the stream: Chicoso Creek, Tenaja Creek, Reilly's Cañon, Burro Cañon, Duck Creek. Forks are abbreviated (Middle Fk., North Fk.).
3. **Landform names set along the landform.**
   - Examples: TRINIDAD MESA, RATON PLATEAU, MANCO BURRO PASS and MORENO V'Y. (70A); PRIETO PLATEAU, SAN FRANCISCO RANGE, PELONCILLO RANGE, SAN SIMEON PLAINS, PUEBLO VIEJO VALLEY and GILA PLAINS (83).
   - All are roman capitals laid on a straight or gently curved baseline along the long axis. PRIETO PLATEAU bends with the plateau's outline.
   - The spacing is set by the feature, not by a style. Measured gaps: TRINIDAD about 0.5 em, MESA 1.2 em, the range names about 2.5 em, RATON PLATEAU up to about 4.5 em, with its letters spread over the whole plateau.
   - Cap height is 1.9 to 2.6 mm, the largest type inside the frame. The two words of TRINIDAD MESA are staggered so that together they span the mesa.
   - Pass names run along the road through the pass, even vertically (RATON PASS).
4. **Heights without names.**
   - Unnamed points carry only a small numeral, about 0.9 mm, in feet without a unit or comma (7268, 6070, 5994). These are rim points, road summits, junctions and spring sites.
   - The Raton rim has eight within a few miles (8332, 8150, 9760, 9210, 8875, 9040, 9030, 8756).
   - Named peaks have the name over the height (TRINCHERA PK 13611, CULEBRA PK 14049, Graham Peak 10516). Towns have a height beside the name (TRINIDAD 6043, Silver City P.O. 5946).
5. **Hierarchy.** Measured cap heights, from largest to smallest:
   - Landform and range names 1.9 to 2.6 mm; big rivers 2.2 mm.
   - Bigger towns in roman capitals, about 1.2 mm (TRINIDAD, CIMARRON). Smaller towns, peaks and buttes in roman upper and lower case, about 1.5 mm and a little heavy (Elizabethtown, Camp Grant, Orange Butte).
   - Ranches, stations, springs and post offices in italic, about 1 mm (Arm's R., Crow Cr. Sta., U.S. Forage Sta., Chicoso Spr., Water Holes, Whitlock's Ciénega).
   - Spot heights 0.9 mm.
   - Railroads in capitals along the line (DENVER & RIO GRANDE R.R.).
   - The largest type is about 2.8 times the smallest. All of it is in one ink.

### Relief (hachures)

6. **Contrast follows the slope.** Ink cover:
   - About 5% on gentle flanks: short broken strokes in rows that follow the contour, close to a stipple.
   - About 8% on the plains: a scatter of dots.
   - About 23% on an escarpment comb.
   - 40 to 50% on steep mountain sides (Culebra, Graham).

   Stroke width hardly changes (about 0.14 mm everywhere). Length does change: median about 0.45 mm on gentle ground, 0.65 to 0.8 mm on steep ground, up to about 1.6 mm. So the darkness comes from packing and length, not width.
7. **Lines left white.**
   - Every crest and spur is a thin white parting between the hachures of its two sides.
   - Summits are white dots at the centre of a rosette of radial strokes (Eagle-tail Mt, Laughlin's Pk, Rose Peak).
   - Mesa and plateau tops are pure paper inside a hard rim.
   - Valley floors are blank, so the drainage reads as a white tree cut into the shading.
8. **Escarpments as one comb.**
   - The Raton and Trinidad rims and the Prieto Plateau edge are a single row of short heavy wedge strokes, perpendicular to the rim. The strokes are 0.5 to 1 mm long, about 0.25 mm apart, thick at the top and tapering downslope.
   - The rim is never a drawn line; it is the top edge of the comb.
   - Re-entrants and canyon heads are drawn with the same comb, which gives the lobed outline of the Raton Plateau.
9. **Shading.** Hachures alone: slope-proportional (Lehmann-style), with no clear oblique light. Hills and buttes have radial rosettes, darker on the steeper side.

### Drainage

10. **Line weight.**
    - Main rivers are a heavier wavy line, often with a stippled bank.
    - Tributaries thin to a hairline toward their heads.
    - Dry creeks and washes are fine dotted lines.
    - Canyons are drawn by their walls (a comb on each side) with the stream between them (the Gila and Prieto canyons on 83).
    - Ditches are labelled along the line (Mining Ditch, Elizabethtown).

### Roads, railroads and places

11. **Roads.**
    - Wagon roads are a fine single line; trails are dashed.
    - Road names are italic along the road (Dry Cimarron Road, Simpson's to Trinidad, C. Bowie & Silver Cy Road, "Cimarron to Arm's R.").
    - The mileage between stations is written on the line: 13.5 m., 21.05 m., 27.5 m.
12. **Railroads.** A line with the company name in capitals along it.
13. **Water and stations as places.** Springs, water holes, ciénegas, water pockets and tanks are named, as are stage and forage stations, ranches, ruins and sawmills. In dry country these are the map's real "towns".
14. **Settlements.** A small block plan of streets for towns (TRINIDAD, Elizabethtown), a dot or small square for ranches, a flag for a fort (Ft. Bayard, outside the frame on 83).

### Paper, frame and lettering of the sheet

15. **Tones.**
    - 70A: margin #f7f6e3, map under-tint #f9eecf (catalogued as "gray cream"). Mountain areas average #e5d9c0, and the darkest ink is #110600 to #221802.
    - 83: margin #f6f3de, under-tint #efead4 (catalogued as "light gray"), mountains #e8e2d1.
    - The tint stops at the neatline, so the map sits as a panel on the sheet.
16. **Frame.**
    - A thin neatline inside a heavy thin-thick double rule.
    - Graticule lines every 15′ (70A) or 30′ (83) across the map, labelled in the margin.
    - "West from Washington" longitudes as well as Greenwich.
    - The title is in spaced capitals with small "of the". The issue date ("Issued May 7th 1877") and the draughtsmen are in small italic under the frame.
    - The scale bar is in miles, with a sectional diagram of the atlas sheet.

## What we do (seen on the site)

Screenshots: `shots/now-*.jpg` (flat at zooms 9 to 12, and tilted).

- **River names do not show on the traced rivers.** The site's river lines follow every meander of the 1:50,000 networks (`tiles/rivers.py`), and the label layer uses MapLibre's default angle limit. So the Bavispe shows no name at zoom 9 (`now-bavispe-z9`), and neither does the Santa María at zoom 11 (`lab-babicora-today`). The Santa María is also a `river_minor` line, which has no label layer at all.
- **The smaller rivers are never labelled.** Natural Earth's `river_minor` layer carries names in `base.pmtiles` (Aros, Casas Grandes, ...) but has no label layer.
- **Landform names are point labels.** Ranges, valleys and plains come from `places.geojson` as horizontal italics, 14 px, 0.15 em, wrapped onto two lines ("Sierra de los Pilares de Teras").
- **Some summits draw no text.**
  - The 199 unnamed summits in `mountain_glyphs.geojson` have a height but draw no text.
  - Small named summits draw neither name nor height (`glyphText` in `relief.ts` only labels medium and large summits and passes).
- **Hachures are sepia (#6e5443) and appear only from zoom 10.** The strokes are fewer and longer than Wheeler's, and gentle slopes carry nearly as much ink as crests. The ranges lack Wheeler's dark cores and white crest partings (`lab-hatchets-today`).
- **Rivers have one weight per class** (0.9 to 2 px and 0.5 to 1.2 px). Intermittent NHD creeks are dashed 3-2.
- **Paper:** caliche #e4ddcc below zoom 10 (under the Imhof tint), near-white #f1ede2 above. The Mexico side is a shade darker.
- **Roads are today's Natural Earth roads.** There is no graticule.
- **In the tilted view** (`now-animas-tilted-z11`), the hachures and labels drape on the terrain. Hachures fade with distance, and horizontal range labels sit flat on the ground at odd angles to the ranges. Labels set along a landform's axis read better there, because they line up with the ridges you see.

## Proposal

The lab parameters, each with exact rollout steps. Each "today" value reproduces the site as it is now, so you can judge one change at a time.

| # | Parameter in the lab | What it does | Default proposal |
| --- | --- | --- | --- |
| 1 | River lettering | Main rivers in spaced roman capitals on smoothed lines; small rivers italic; creek labels a size smaller | Adopt |
| 2 | Spot heights | Height alone (9.5 px italic) on unnamed and small named summits | Adopt |
| 3 | Landform names along axis | Spaced roman capitals along each range, valley, plain and mesa axis, spaced to fill about 80% of it | Adopt, with reviewed data (see Data sources) |
| 4 | Hachure contrast (0 to 1) | Opacity from −60% on gentle ground to +45% on steep; width −40% to +25% | Try 0.5 to 0.75; the real fix is in the hachure build |
| 5 | Hachures in brown-black | #2e2010 instead of #6e5443 | Try with 4; keep sepia if the contours fight it |
| 6 | Drainage by rank | Rivers 1.3 to 3.6 px by scalerank, creeks hairline, intermittent creeks dotted 0.5-2 | Adopt |
| 7 | Paper | Today, cream (70A) or grey (83) | Owner's call; cream suits the warm hachures |

Lab views to compare: `lab-bavispe-*` (river names), `lab-animas-*` (landform names and spot heights), `lab-hatchets-*` (contrast and ink), `lab-babicora-*` (dense hachures, a small river), `lab-tigre-*` and `lab-peloncillos-*`.

**Rollout steps** (one commit each, `site/src/map` unless noted):

1. **River lettering.**
   - In `tiles/rivers.py`, write a third layer, `river_label`: each named Natural Earth river, its parts merged, simplified at 0.03° and smoothed with two passes of Chaikin's algorithm (`review/stage-8/wheeler/river_label_lines.py` does exactly this). Add it to `tiles/build_base.py`.
   - In `style.ts`, point `river-label` at `river_label`:
     - text in `['upcase', name]` with `fonts.roman`
     - `text-size` 11 at zoom 7, 14 at 10, 16 at 12; `text-letter-spacing` 0.45 to 0.9 em; `text-max-angle` 30; `symbol-spacing` 500
     - filter `scalerank` to choose capitals or italic, or carry a `rank` property as the lab does
   - Add `river_label` to `BASE_LAYERS` and `NOT_RAISED`.
   - Creek labels: 10.5 to 11.5 px, 0.04 em.
2. **Spot heights.**
   - In `relief.ts` `glyphText`, return `heightLabel(elevation_m, units)` alone where the summit is unnamed or small (not passes). Use a `text-size` of `['case', bare, 9.5, 11]`. This is the `spotHeights()` function in `wheelerStyle.ts`, with units added.
   - `mountain-glyph` keeps its collision order and its spoiler filter (`spoiler/filter.ts`), so nothing new leaks.
   - Check the Raised view, where glyphs are hidden.
3. **Landform names.**
   - Build `data/landforms.geojson` in the pipeline (a `crossing.landform_axes` module from `review/stage-8/wheeler/landform_axes.py`). Give each line `name`, `kind`, `len_m`, `mpp0`, `source`, `licence`, `first_seen`. Take `first_seen` from the matching place in `places.geojson`; landforms the book does not name get `1-01`.
   - Add it to the data schemas and `crossing.validate`.
   - Add a symbol layer like `landformLayer()` in `wheelerStyle.ts`, above `mountain-glyph`, with the `areas`/`places` spoiler clause.
   - Drop the point labels of ranges, valleys and plains in `StoryLayers.tsx` where a line exists (keep the point and its click target).
   - Add the layer to `PROGRESS_LAYERS` and to the spoiler-leak test.
4. **Hachure contrast and ink.**
   - Short term: in `relief.ts` `strokePaint`, multiply opacity by `1 + t·k(slope)` as in `hachure()` in `wheelerStyle.ts`, with t = 0.5 to start. If you take the darker ink, change the `hachure` token in `tokens.ts`.
   - Longer term, in the hachure build (`pipeline/src/crossing/hachures.py` / `tiles/build_relief.py`):
     - (a) shorter, denser strokes on steep ground;
     - (b) no strokes within one stroke length of a ridge line (the geomorphons or the Raised view's ridge lines are already computed), so crests show as white partings;
     - (c) a "rim" class: one row of wedge strokes where slope breaks from under 6° to over 25° within 100 m, replacing the ordinary strokes there.
5. **Drainage by rank.**
   - The `taper()` widths in `style.ts` for `river`, `river-minor` and `creek`.
   - A true taper along each river needs a Strahler order on the river lines. `tiles/rivers.py` already computes it for the trace (INEGI `ORDER_1`, NHD order from the joins); keep it on each traced piece and use it as `line-width` input.
6. **Paper.** Change `paper`, `paperMexico` and `reliefPaper` in `tokens.ts` (cream: #efe5c8, #e6d9b9, #f8f0d8 to #f4ead0). Recompute `paperShown` and the halo colours, and run `tools/contrast.mjs` for the italic labels.
7. **Not in the lab, proposed:**
   - A graticule every 15′ in faint ink from zoom 8 (a small generated GeoJSON).
   - Springs and water holes (GNIS Spring, GeoNames SPNG, aguajes) in the corridor from zoom 11.
   - Pass names in small capitals along the road through the pass (`IMFeENsc28P` is already built).
   - Roads, below.

## Data sources: landform names with geometry

Local counts are from `private/cache/gazetteer` (GNIS AZ and NM, GeoNames MX) in the box 112° to 104° W, 28° to 34° N. The rest was researched on the web on 13 to 14 November 2026. [V] means checked on the page or by downloading the data; [I] means inferred.

| Source | Geometry | Our area | Licence | Notes |
| --- | --- | --- | --- | --- |
| **USGS GNIS DomesticNames** ([download](https://www.usgs.gov/us-board-on-geographic-names/download-gnis-data), [field spec](https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/GNIS_file_format.pdf)) | Point, plus a **source point for Valley** (and streams): primary = mouth, source = head [V, all 4,240 Valley records in the box] | US. Range 176, Ridge 207, Summit 2,144 (mesas and buttes are filed here: 179 "Mesa" names), Flat 263, Basin 142, Cliff 68, Bench 22, Plain 3 (includes **Prieto Plateau** and **Natanes Plateau**, Wheeler's names on sheet 83) | Public domain (federal) | Valleys get an axis for free (Animas Valley 32.57 to 31.35° N). The FullModel GDB/GPKG stores each feature as a multipoint, one per 7.5′ quad it crosses [V]; principal component analysis (PCA, finding the long axis of a point cloud) of those points gives a coarse axis for big ranges. `map_name` is the quad of the primary point. |
| **GMBA Mountain Inventory v2** ([data](https://data.earthenv.org/mountains/standard/GMBA_Inventory_v2.0_standard.zip), [repo](https://github.com/GMBA-biodiversity/Inventory)) | **Polygons** | 144 polygons in the box [V]. US sky-island ranges are excellent: Chiricahua, Peloncillo, Animas, Florida, Big and Little Hatchet. Mexico is coarse: one Sierra Madre Occidental polygon, INEGI physiographic subprovinces; Sierra el Tigre, Huachinera, Carcay, de la Madera and Pilares are missing [V] | CC BY 4.0 (repo; not seen on the EarthEnv page) | The best source for US range axes: PCA of the polygon. Has a Wikidata field. |
| **GeoNames MX** ([MX.zip](https://download.geonames.org/export/dump/MX.zip)) | Point | MT 4,321, HLL 3,550, **MESA 1,536**, **MTS 1,008**, PASS 756, HLLS 485, RDGE 320, CNYN 295, PLN 46, VAL 23, PLAT 2 [V, local] | CC BY 4.0 [V] | All the novel's sierras are present, with duplicates (several "Sierra la Madera"). "Mesa" in the Sierra Madre often names a high flat or a rough summit area, not a table mountain (Mesa la Sierra by the Babícora is a rugged massif). |
| **INEGI** ([registry of geographic names](https://www.inegi.org.mx/app/geo2/cng/), [1:250k data dictionary](https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/889463842620.pdf)) | **Point only**: orographic names are the "Referencia geográfica" object, PUNTO, with NOMBRE, TÉRMINO GENÉRICO (Sierra, Serranía, Cordón, Mesa, Meseta, Llano, Bolsón, Cañón, Puerto) and a position qualifier [V] | Mexico; about 86,800 orographic names nationally [V, press note] | [INEGI free-use terms](https://www.inegi.org.mx/inegi/terminos.html): attribution "Fuente: INEGI, product, date", say that it was transformed [V] | No toponym line layer at 1:250k; 1:50k assumed the same [I]. Authoritative spelling for Mexico. |
| **OpenStreetMap** | Lines: natural=ridge (1,808 ways, 1,493 unnamed; 32 distinct names), natural=valley (about 175 ways), mountain_range (9 named) [V, one Overpass query] | Sparse, mostly US | ODbL | Too thin to rely on. Share-alike applies to a derived database; keep any OSM lines in a separate layer with attribution. |
| **Natural Earth** geography regions ([10m physical](https://naciscdn.org/naturalearth/10m/physical/)) | Polygons | Sierra Madre Occidental, Mogollon Rim, Chihuahuan and Sonoran Deserts, Alti-planicie Mexicana [V] | Public domain | Only for the largest labels at zooms 5 to 7. |
| **Wikidata** | Point (P625); no geoshape (P3896) or extreme-point properties on any range, ridge, valley or plain item in the box [V] | 1,189 ranges, 410 ridges, 2,553 valleys (mostly GNIS imports) | CC0 | For joining IDs and multilingual names, not geometry. |

**Deriving an axis when only a point exists** (implemented in `landform_axes.py`):
1. Read the Copernicus GLO-30 DEM (`private/cache/least-cost/dem.vrt`) around the point:
   - ranges: radius 30 km at 150 m cells;
   - mesas: radius 12 km at 90 m;
   - plains: radius 30 km at 150 m.
2. Mask the landform:
   - Ranges: height above the local valley floor (the lowest ground within 8 km, smoothed) greater than 25% of that height near the point. This separates a range from a higher neighbour across a valley; a plain percentile threshold labelled the Animas Mountains as the Peloncillos.
   - Mesas: flat cells (slope under 8°) within 80 m of the top near the point.
   - Plains: flat cells low in the window.
3. Keep the connected region containing, or nearest to, the point.
4. Run PCA of the cell positions, weighted by height above the base. The major axis gives the direction. The line runs ±1.8 standard deviations along it through the weighted centroid, flipped to read left to right. The ratio of the eigenvalues measures elongation; below about 1.5, use a horizontal label.
5. For GNIS valleys, use the mouth-to-head line instead.
6. Possible improvements:
   - clip ranges to GMBA polygons where they exist;
   - fit a curved line through strip centroids for bent ranges (PRIETO PLATEAU style);
   - for long valleys, use `symbol-placement: line` with wide spacing instead of `line-center`, so the name repeats where you are looking.

The demo set (`site/src/lab/wheeler/landforms.ts`, 23 lines) shows what works and what needs review:
- **Plausible axes** (elongation 1.9 to 4.2; checked on the map for the Peloncillo, Animas, Big Hatchet and el Tigre): the Peloncillo, Little Hatchet, Pyramid, Chiricahua and the Sonoran sierras; the GNIS valleys.
- **Short axis:** the Animas Mountains comes out at 16 km for a 40 km range. The GNIS point is at Animas Peak, and the PCA finds the high core. GMBA's polygon would fix it.
- **Few mesas:** only 4 named mesas from the glyphs pass the length test (2.5 km and elongation 1.6). GeoNames "mesas" in the Sierra Madre are mostly not table mountains.

**Recommendation.**
- US ranges: GMBA polygons, with the axis by PCA.
- US valleys: GNIS mouth-to-head lines.
- Mexican sierras and mesas: GeoNames or INEGI names with DEM-derived axes.
- Everything is reviewed in a sheet like `tools/landform-sheet.mjs`, with a hand-edit table (`pipeline/seeds/landform_axes.toml`: name, rotate, length, curve) for the few dozen names that matter to the book.

Credits needed on the Credits page:
- GeoNames (CC BY 4.0)
- GMBA (CC BY 4.0)
- INEGI ("Fuente: INEGI ...")
- GNIS (public domain, credit as courtesy)

## Roads plan

Historic roads of the story's years (1939 to 1944) or earlier, both sides of the border. Research by a sub-agent on 13 to 14 November 2026; [V] checked on a page or API, [I] inferred. Two library sites (UT Austin PCL and GeoBlacklight at BTAA) and the Texas A&M catalogue put bot checks in front of automated clients, so those holdings were not listed.

| Source | Coverage | Period | Format | Licence | Effort |
| --- | --- | --- | --- | --- | --- |
| **USGS Historical Topographic Map Collection** ([topoView](https://ngmdb.usgs.gov/topoview/); TNM API) | US side. 1:62,500 bootheel sheets 1917 to 1923: Animas Peak, Antelope Wells, Walnut Wells, Playas, Hachita, Big Hatchet Peak, Columbus, Hermanas. Cochise 1:62,500 1922 to 1928: Rodeo, Orange Butte. El Paso and Doña Ana 1939 to 1945. 1:125,000 Chiricahua, Perilla, San Simon 1917 to 1919. 1:250,000 Douglas 1955, El Paso 1953, Silver City 1954 [V]. **No 1930s to 40s sheets for Animas, Cloverdale or Lordsburg.** | 1917 to 1955 | GeoTIFF and GeoPDF, georeferenced [V] | Public domain | Hand-trace in QGIS |
| **NPS National Historic Trails** | Butterfield Overland NHT (designated January 2023; Lordsburg, Stein's Pass) [V] ([data](https://irma.nps.gov/DataStore/Reference/Profile/2318550)); El Camino Real de Tierra Adentro (El Paso, Doña Ana) [V] ([data](https://irma.nps.gov/DataStore/Reference/Profile/2238908)) | 1540s to 1880s | Shapefile or feature service | Public domain [I] | Download and clip |
| **State highway maps** | NM 1930, 1932, 1936, 1940, 1941 ([1940 PDF](http://gstore.unm.edu/apps/rgisarchive/datasets/5c296e73-a054-45e3-8051-b9e1efd29baa/1940Map.original.pdf), "Use Constraints: None") [V]; Texas 1936 to 1940 ([ROSAP](https://rosap.ntl.bts.gov/collection_srm)) [V]; Arizona 1935, 1939, 1940 (scans on [AARoads](https://www.aaroads.com/arizona/historical-maps-arizona); check the State Library originals) [V] | 1930 to 1941 | Unreferenced scans | US works 1929 to 1963 without renewal are public domain; state maps rarely renewed [I] | Use to classify roads (paved, graded, unimproved), not to place them |
| **Army Map Service** | F401 1:500,000 "Ciudad Juárez" 1933 (UT GeoData, probably georeferenced) [V]; F541 1:250,000 Mexico (1941, 1947), northern sheets not confirmed; a joint DCM/AMS 1:250,000 series with Douglas and Nuevo Casas Grandes sheets (Texas A&M) [V, catalogue only] | 1933 to 1950s | Scans | US Army: public domain in the US; joint Mexican sheets uncertain | Georeference and trace |
| **Mexican railways** | Noroeste de México (Juárez to Casas Grandes to Madera, about 1910 to 1914): OSM "Línea QA" (128 abandoned ways, 29 to 31.6° N); the Nacozari line ("Línea TA") [V]. A Noroeste map of about 1912 to 1916 at [UT exhibits](https://exhibits.lib.utexas.edu/spotlight/mexicos-fight-for-democracy/catalog/168-5799) [V] | 1897 to 1940s | Vector (OSM), scans | ODbL (OSM); map scan rights to check | Use OSM as geometry guide, check against the period map |
| **US railways** | Atack, [railroads 1826 to 1911](https://my.vanderbilt.edu/jeremyatack/data-downloads/) (shapefile, "Lower 48"; territories not confirmed; no licence, citation asked) [V]; OSM abandoned El Paso & Southwestern segments [V] | to 1911 | Shapefile | Ask or cite | Clip |
| **Mexican roads** | No online SCOP road map of the 1930s to 40s found. Salgado Granados (2016, WU Vienna) has historical GIS of Mexican roads 1900 to 1925, highways 1925 to 2010 and railways by decade ([record](https://research.wu.ac.at/de/publications/historical-dataset-on-market-access-urbanization-and-multimodal-t-3/); no download or licence) [V] | 1900 to 2010 | Shapefile (on request) | Unknown | Write to the author |
| **OpenHistoricalMap** | About 360 features in the box, mostly urban: dated US 80 and US 666, SP segments, the Mexican Central, a 1900 Cochise to Willcox road. Nothing for the Noroeste or the bootheel wagon roads [V] | Dated | Vector | CC0 since 2022 [V] | Optional supplement; contribute back |
| Roads the novel names: the old Cloverdale road, the old Playas road, the Madera road, the Gallego road, the Guzmán road, the wagon road to Namiquipa, the road to Boquilla | | | | | No GIS found for any of them. They are in our own `areas.geojson` as inferred areas. |

**Recommended plan** (in order):
1. **Ready-made trails.** NPS Butterfield and Camino Real, clipped, styled as "old trail" (fine dashed, italic name along the line).
2. **US roads and railways of about 1940.** Trace in QGIS from the USGS GeoTIFFs:
   - the 1917 to 1923 15′ sheets for the bootheel (they show the ranch roads and trails of the Animas and Playas valleys that the book's riders use);
   - the 1939 to 1945 sheets for El Paso and Doña Ana;
   - the 1953 to 1955 1:250,000 sheets for the regional network.

   Classify each road from the NM 1940 and 1941 and Texas 1940 highway maps. Tag each line with `source` (sheet and year), `class` (highway, graded, wagon road, trail) and `certainty`. Write a small `pipeline/seeds/roads/` GeoJSON by hand: about 30 to 60 lines, not a network.
3. **Railways.** Atack plus the USGS sheets for the US; the EP&SW through Douglas, Hachita and Columbus, and the SP through Lordsburg.
4. **Mexican railways.** The Noroeste (Juárez, Casas Grandes, Madera) and the Nacozari line. Use the OSM geometry as a guide, check it against the UT Noroeste map, and keep ODbL attribution if OSM geometry is kept. Write to Salgado Granados for the 1940 railways.
5. **Mexican roads.** Only the few that are documented: Agua Prieta to Fronteras and Nacozari, Juárez to Casas Grandes, Janos to Casas Grandes, the Bavispe valley road, and the roads the book names, which our inferred areas already place. Draw them as dashed "approximate" lines with a source note in their card (for example, "after AMS F401, 1933, approximate"). Leave the Sierra Madre unroaded except for trails we can source.
6. **Style, after Wheeler:**
   - fine single line for wagon roads, dashed for trails;
   - italic names along the line;
   - the book's distances on the line where it gives them;
   - railroads named in capitals.

   Hide today's Natural Earth roads in the classic map, and keep them for Topo.
7. **Spoiler mode.** Give each road `first_seen` (the episode where the book first uses it; `1-01` for unnamed context roads), and add it to `PROGRESS_LAYERS`.

## Open questions

1. **Paper.** Cream (sheet 70A), grey (sheet 83) or today's caliche? The lab shows all three. Cream lightens the low zooms a lot; the Imhof tint over it may need retuning.
2. **Hachure ink.** Brown-black reads like Wheeler but competes with the type and the journey lines. Sepia with more contrast may be enough. The real gain is in the hachure build (white crests, rim combs, shorter strokes on steep ground). Should that be the next relief stage?
3. **Spot heights.** Wheeler prints feet with no comma (7268). The lab uses the site's format (7,268). Which do you prefer? And should spot heights show only where no glyph is drawn?
4. **Landform names on the reading map.** Should a range named in the book take its label from the book's spelling (places.geojson) or the gazetteer's? Should landforms the book never names be lettered at all, or only from zoom 10?
5. **Long valleys.** `line-center` puts the name at the middle of a 135 km valley, often off screen. Repeat it along the line, or split valleys into reaches?
6. **Roads.** Is a hand-traced, sourced network of about 30 to 60 lines the right scale, or only the roads the book names?
7. **Tile seam (unrelated).** There is a vertical striped band in the hachures west of the Peloncillos, near 109.3° W, 32.0° N, at zoom 10 (visible in `now-peloncillos-z10` and `lab-peloncillos-*`). It looks like a seam in `relief.pmtiles`. Not investigated.

## Files

- `site/src/lab/wheeler/WheelerLab.tsx`: the section (default export, no props). It has its own MapLibre map and registers the pmtiles protocol itself. Its only imports from the site are `map/style.ts` and `map/tokens.ts`.
- `site/src/lab/wheeler/wheelerStyle.ts`: the parameters and the style transform. Every value is documented in the code.
- `site/src/lab/wheeler/learnings.ts`: the cards (our descriptions and measurements) and the sheet links.
- `site/src/lab/wheeler/landforms.ts` and `riverLines.ts`: generated demo data, from `review/stage-8/wheeler/landform_axes.py` and `river_label_lines.py`.
- `site/src/lab/wheeler/wheeler.css`: the section's styles, prefixed `wheeler-`.
- `tools/wheeler-shots.mjs`: the screenshots.
- Not committed: `private/inspiration/rumsey/` (the scans).
