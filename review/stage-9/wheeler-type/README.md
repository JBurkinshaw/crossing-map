# Wheeler card "type": a strict type hierarchy, in few faces

This card has two parts:

1. **Landform label lines for the whole story box** (`data/landforms.geojson`), built by a new pipeline module, `crossing.landform_axes`. The site can use them later.
2. **The shared type scale in the lab**, for the test area only (109.6 to 108.4° W, 30.5 to 31.6° N). It is the toggle "Type hierarchy (test area)" in the Wheeler section of the lab.

The study behind it is `review/stage-8/wheeler/README.md`, under Lettering and Data sources.

## How to see it

1. `cd site && npm run dev -- --port 5197`
2. Open `http://localhost:5197/lab.html#wheeler`.
3. Click **All as today**, then turn on **Type hierarchy (test area)**.
4. Use the place button **Test area: bootheel and Bavispe**.

"All Wheeler" also turns the card on.

Screenshots are in `private/review/stage-9/wheeler-type/` (git-ignored), made with `node tools/wheeler-type-shots.mjs` while the dev server runs:

- `desktop-z{9,10,11,12}-{before,after}.jpg` and `phone-z{9,10,11,12}-{before,after}.jpg`. "Before" is the lab with every parameter as today. "After" is the same with the card on. Zooms 9 and 10 show the middle of the test area, zoom 11 the Animas Mountains and Valley, and zoom 12 San Luis Pass.
- `landform-sheet.png`: every landform line in and around the test area, over a hillshade. The book's landforms are in dark red, GMBA lines in blue, GNIS valleys in green and DEM lines in black. Hand-edited lines are dashed. `sheet-bootheel.png` is the same for the bootheel. Rebuild them with `uv run --project pipeline python review/stage-9/wheeler-type/landform_sheet.py [W S E N] [OUT]`.

## 1. Landform label lines (pipeline)

**Run:** `uv run --project pipeline python -m crossing.landform_axes`. It takes about 90 s and makes no network requests. Then run `crossing.downloads`, `crossing.validate` and `crossing.echo_check`.

**What it writes:** 313 lines in the packet's box (112 to 104° W, 28 to 34° N): 216 ranges, 36 valleys, 20 plains, 40 mesas and 1 plateau. 21 of them are landforms the book names (from `places.geojson`): they use the book's name (the place's `name`) and the place's `first_seen`, and `place_ref` points to the place. All others have `first_seen` 1-01.

**Properties:** these are the shared story-layer properties (`id`, `name`, `kind`, `part`, `first_seen`, `certainty`, `method`, `source`, `source_id`, `source_licence`, `note_safe`, `reasoning`, `place_ref`), plus:

- `name_source` (`gnis:<id>`, `geonames:<id>` or `gmba:<id>`)
- `axis` (`gmba`, `gnis` or `dem`)
- `elongation`
- `len_m`
- `mpp0` (metres per pixel at zoom 0 for 256 px tiles, at the line's middle, as in the packet)

`source` and `source_licence` name the dataset that fixed the line: `gmba` (CC BY 4.0), `gnis` (public domain), or `copernicus-glo30` (Copernicus licence). The card asked for a `licence` field. The shared schema calls it `source_licence`, so the layer uses that name.

**Method** (decision 0020, `docs/decisions/0020-landform-label-lines.md`):

- **US ranges:** the principal axis of the GMBA polygon, where a GMBA range of the same name lies within 10 km of the gazetteer point. GMBA polygons larger than 3,000 km² are left out, because they are physiographic provinces.
- **US valleys:** the GNIS line from the mouth (primary point) to the head (source point).
- **Everything else:** the principal axis of the DEM region around the point, the method in `landform_axes.py`. A new fallback handles regions that run past their 30 km window, which is the normal case in the Sierra Madre. The region is cut to 12 km around the point, and the line follows the grain of the ground there: the structure tensor of the slope. These lines have certainty `inferred` (93 lines). Where a region is round (elongation under 1.5), the line is laid east to west.
- **Hand-edit table:** `pipeline/seeds/landform_axes.toml` is applied last. It supports `rotate`, `length`, `centre`, `curve`, `drop`, `keep` and `reason`. I added `centre` (in place of a shift) and `keep` (to bring back a line that the count rules left out). Each reason is published in `reasoning`.

**Which landforms, and the count rule** (`choose()`):

- Always kept: the book's ranges, valleys and plains.
- Other candidates:
  - GNIS: Range (names ending in "Mountains" or "Range"), Valley (names ending in "Valley", with a head point), Plain, and Summit records named "Mesa".
  - GeoNames: MTS (names starting "Sierra" or "Serranía"), VAL, PLN, PLAT and MESA.
  - GMBA: named basic and point-defined ranges.
- Ranking: GMBA and GNIS lines first, longest first. Then DEM lines: ranges by the height of their core above the valley floor, the others by length.
- Limits for each kind:
  - Minimum length: ranges 12 km, valleys 15 km, plains 10 km, plateaus 10 km, mesas 2.5 km. Mesas must also be at least 1.6 times as long as they are wide.
  - Cap: ranges 200, valleys 60, plains 30, plateaus 10, mesas 40.
  - Spacing: a line is dropped if its middle is within 15 km (or 0.3 of the longer line's length) of a kept line of the same kind.
- A gazetteer landform with the same name as one of the book's, within 60 km of it, counts as the same landform. For example, GeoNames' "Animas Valley" in Mexico is the book's Animas Valley.

**Hand edits in the test area:**

| Line | Edit | Reason (short) |
| --- | --- | --- |
| Peloncillo Mountains | Centre 31.85° N, 50 km, turned 28° | GMBA's outline runs 190 km north to the Gila. The book's Peloncillos are the southern ridge. |
| Animas Mountains | Centre 31.59° N, 42 km, turned 80° (north to south) | The GNIS point is on Animas Peak. The DEM finds only the round core, so the line was 14 km and east to west. |
| Sierra el Tigre | Kept | The spacing rule gave its ground to the Pilares de Teras. |
| Sierra San Luis | Kept | Without it, only the small US end of the massif has a name. |

**Schema and checks:**

- `data/schema/story-layer.schema.json` has a new `landforms` layer, the new properties, and two new kinds, `mesa` and `plateau`.
- `crossing.validate` checks the layer. It also fails if a line is first seen before its place.
- `crossing.downloads` writes `data/parquet/landforms.parquet`.
- `pipeline/tests/test_validate.py` has a test for the new check.
- Docs: a row in `docs/pipeline.md` section 2 and in the seeds table, decision 0020 with an entry in the index, and a row and a GMBA credit in `data/README.md`.

### Landform lines that look wrong

These are in or near the test area. The rest of the box has not been reviewed by eye.

- **Llanos de Carretas** (book, 2-01): an east-to-west line 58 km long. The GeoNames point (31.0, -108.5) is rounded, and the plain's DEM region is nearly round. The line runs east of the test area onto the hills by Janos. It is probably 20 km too long.
- **Sierra de los Pilares de Teras** (book, 1-09) and **Sierra de la Cabellera** (book, 1-09): `inferred` lines from the grain of the ground. The Pilares line is east to west (weak grain) and the Cabellera line runs north-west. I could not confirm either direction on the hillshade.
- **San Luis Mountains** (book, 1-04): a 13 km line, east-north-east, on the north tip of the San Luis massif, partly in Mexico. The US San Luis Mountains are short, so this may be acceptable.
- **Guadalupe Mountains** (book, 1-03): 40 km, from 31.24 to 31.60° N. The north end runs into the Peloncillos, so the line is probably about 10 km too long.
- **Sierra de la Ventana, Sierra El Palomo, Sierra el Pinito (Sonora), Sierra San Luis:** east-to-west lines, because the grain near the point is weak (strength under 1.5).
- **Mesa la Comisaría** (16 km) and **Mesa el Pilarar** (9 km): long, thin flat strips. These may be ridge tops that GeoNames calls "mesa" and not true table mountains. Drop candidates.
- **Valle La Isla** (49 km): plausible, because it follows the Fronteras valley, but not confirmed.
- **The rest of the box:** most Chihuahua plains and mesas are DEM lines 20 to 30 km long, and none were checked.
- **Small changes between runs:** the 5th decimal of some DEM lines changes from run to run (about 5 m), probably from GDAL's reads at window edges. The lines do not get worse, but each rebuild shows a diff.

### A correction to the stage 8 packet

The packet says GMBA v2 is "excellent" for the Animas, Florida, Big Hatchet and Little Hatchet. The **standard** inventory (the one download) does not have these ranges. They are only inside the "Animas Area" and "Southwest New Mexico Ranges" support polygons. In the test area, GMBA gives only the Peloncillo (as one 190 km outline) and Pedregosa ranges. So most bootheel ranges use the DEM method, and the hand-edit table matters more than the packet expected.

## 2. The lab: type hierarchy in the test area

The changes are in these files:

- `site/src/lab/wheeler/subset/type.ts`: the card's style.
- `wheelerStyle.ts`: a `type` parameter and one call.
- `WheelerLab.tsx`: the toggle and the test-area place button.
- `learnings.ts`: the "Try it" link on the hierarchy card.

Lab data is in `site/public/lab/wheeler/type-{landforms,rivers,passes}.geojson` (13 kB in total). It is made by `uv run --project pipeline python review/stage-9/wheeler-type/type_lab_data.py` from `data/landforms.geojson`, the base tiles (`base.pmtiles`, read through GDAL's PMTiles driver) and the DEM.

**Faces and sizes:** three faces (IM Fell roman, italic, and small capitals `IMFeENsc28P`) in one ink, the `ink` token. The sizes below are at zoom 11. Every size is multiplied by 0.85 at zoom 9 and 1.15 at zoom 13.

| What | Face | Size | Notes |
| --- | --- | --- | --- |
| Landforms (ranges, valleys, plains, mesas) | Roman capitals | 19 px | Along the line, letter gap set so the name fills 80% of it (0.1 to 4 em), and at most 460 px long (see below) |
| Big rivers (Bavispe, Batepito) | Roman capitals | 19 px | 0.6 em spacing, along the river's smoothed run |
| Towns | Roman | 13.5 px | Large towns in spaced capitals. "Large" means `kind: city` in `places.geojson`, which in the test area is Douglas and Agua Prieta |
| Ranches, stations, springs, crossings | Italic | 10 px | Opacity 0.7, with a small dot |
| Draws and canyons | Italic | 10 px | Opacity 0.7, along the line. GNIS files these as valleys, but they are not landform capitals |
| Passes | Small capitals | 10 px | From zoom 10, along the way over |

Spot heights (9.5 px) are the existing "Spot heights" parameter and are not changed here.

**What gives way inside the test area:**

- The base map's big-river label and the lab's river lettering.
- The italic names of pass glyphs. The glyphs themselves stay.
- The lab's demonstration landform lines that reach into the area.

These use MapLibre `within` filters, so a vector-tile piece that crosses the area's edge can still show the old label there. The card's layers go on top of the style, so their names are placed before every other label.

**Passes:** none of the six named passes in the test area has a base-map road within 1 km. These are San Luis Pass, which is in the book, and five Sonoran "Puertos" from GeoNames. So every pass line crosses the saddle along the direction of most negative curvature of the DEM (the way a path goes over), 5 km long. The road rule is in `type_lab_data.py` (`ROAD_M`) for when traced roads arrive (`pipeline/seeds/roads/`, another card).

**What does not work yet:**

- **Long label limit:** MapLibre draws a line label only where it fits in one tile's piece of the line. Long names therefore stop filling the line past about 460 px, and their letters close up at zoom 12.
- **Long valleys:** the lab clips each line to the test area, so the Animas Valley is lettered on the part in view. On the site, a 136 km line would put its name at the middle (32° N). Open question 5 of the stage 8 packet still applies.
- **Zoom 9:** few landform names fit at 16 px. They wait for zoom 10, as the smaller Wheeler names would.
- **Repeated river names:** the Bavispe can be named twice at zoom 11 (symbol spacing 300 px). A larger spacing let the towns block the river names altogether.
- **Spoilers:** the lab draws towns and places at every reading position. The card's data carries `first_seen` for a later filter.
- **Phone:** at zoom 11 and 12 a long spaced name runs past the edge of the screen.

## Credits needed

- **GMBA Mountain Inventory v2:** CC BY 4.0. "GMBA Mountain Inventory v2 (Snethlage et al. 2022), GMBA and EarthEnv". This is new for the Credits page.
- **GeoNames:** CC BY 4.0. Already credited.
- **USGS GNIS:** public domain, credited as a courtesy. Already credited.
- **Copernicus DEM GLO-30:** the existing notice.
- **INEGI:** not used. No INEGI toponym points are cached, and none were downloaded.

## Network log

| Date (UTC) | URL | Bytes | Result |
| --- | --- | --- | --- |
| 2026-11-14 21:07 | https://data.earthenv.org/mountains/standard/GMBA_Inventory_v2.0_standard.zip | 185,781,797 | 200, cached in `private/cache/gmba/` |

There were no other requests. The User-Agent was "crossing-map-research/0.1".

## Open questions for the owner

1. **Book names that differ from the gazetteer:** should the line use the map's name (as now: "Sierra de los Pilares de Teras", "Big Hatchet Mountains") or the book's own spelling (`name_in_text`: "Pilares Teras", "Hatchet Mountains")?
2. **Landforms the book never names:** the build keeps about 290. Is that too many for the reading map? A stricter cap, or a minimum zoom by size, would be easy to add.
3. **Draws and canyons the book names** (Foster, Clanton, Taylor's, Starvation): small italic along the line, as here, or point labels?
4. **Sierra Madre lines:** are the inferred lines (93, mostly in Sonora and Chihuahua) good enough to publish, or should the site letter only `approximate` lines until they have been reviewed?
5. **The Data page:** the parquet copy exists, but `site/scripts/site-facts.ts` and `site/src/pages/Data.tsx` do not list the layer yet. I left them for the lead's rollout.
