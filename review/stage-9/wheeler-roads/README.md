# Wheeler card "Roads with their mileages": test-area trial

A small, hand-traced set of historic roads for the test area (109.6 to 108.4° W, 30.5 to 31.6° N), drawn in the lab's Wheeler section after the Wheeler sheets: wagon roads as a fine single line, trails dashed, names in small italic along the line, and the book's distances written on the line. The plan this follows is the "Roads plan" in `review/stage-8/wheeler/README.md`. Nothing on the published site or in `data/` has changed.

## What changed

| File | What |
| --- | --- |
| `pipeline/measure/roads_test_area.py` | The trace record: picked pixel vertices per road and sheet, the conversion to WGS 84, the Butterfield clip, and the lengths. Writes the seed and the lab copy. |
| `pipeline/seeds/roads/test-area.geojson` | The seed: 10 traced lines (9 roads, one split at the SK Bar) and the clipped Butterfield trail. 15 KB. |
| `site/public/lab/wheeler/roads-test-area.geojson` | The lab copy: the seed plus two label points for the mileages. |
| `site/src/lab/wheeler/subset/roads.ts` | The card's style: `historicRoads(style, halo, ink)` adds the source and layers and hides today's roads in the test area. |
| `site/src/lab/wheeler/wheelerStyle.ts` | Shared file, small edit: a `roads` parameter (on in "All Wheeler", off in "All as today") and one call to `historicRoads`. |
| `site/src/lab/wheeler/WheelerLab.tsx` | Shared file, small edit: the toggle "Historic roads (test area)" and the place button "Test area: bootheel and Bavispe". |
| `tools/wheeler-roads-shots.mjs` | The before and after screenshots. |

## How to see it

```sh
cd site && npm run dev -- --port 5241
# open http://localhost:5241/lab.html#wheeler, press "Test area: bootheel and Bavispe", zoom to 11 near Cloverdale,
# and switch "Historic roads (test area)" on and off.
cd tools && node wheeler-roads-shots.mjs http://localhost:5241/   # screenshots
uv run --project pipeline python pipeline/measure/roads_test_area.py  # rebuild the seed (needs the private cache)
```

Screenshots, all with the other parameters at "All Wheeler" (`private/review/stage-9/wheeler-roads/`):
- `roads-z10-before.jpg`, `roads-z10-after.jpg`: the Animas Valley from Cloverdale to the Gray Ranch.
- `roads-z11-before.jpg`, `roads-z11-after.jpg`: Cloverdale, the Cloverdale Creek road ("4 m.") and the road down to Guadalupe Pass.
- `roads-z12-before.jpg`, `roads-z12-after.jpg`: the road to Animas with "9 m.".
- `roads-butterfield-z10-before.jpg`, `roads-butterfield-z10-after.jpg`: north of the test area, the Butterfield trail through Stein's Pass.

## Sources fetched (11 requests of the 25 allowed)

User-Agent `crossing-map-research/0.1`, at least 2 s between requests, all cached under `private/cache/roads/` (log: `private/cache/roads/requests.log`). No 429s.

| # | Date (UTC) | URL | Bytes |
| --- | --- | --- | --- |
| 1 | 2026-11-14 21:08 | `https://tnmaccess.nationalmap.gov/api/v1/products?bbox=-109.6,30.5,-108.4,31.6&datasets=Historical%20Topographic%20Maps&prodFormats=GeoTIFF&max=200` | 192,652 |
| 2 | 2026-11-14 21:08 | `https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NM/NM_Animas%20Peak_189578_1918_62500_geo.tif` | 6,905,660 |
| 3 | 2026-11-14 21:08 | `https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NM/NM_Cienega%20Springs_189304_1918_62500_geo.tif` | 5,431,653 |
| 4 | 2026-11-14 21:08 | `https://irma.nps.gov/DataStore/Reference/Profile/2318550` | 102,104 |
| 5 | 2026-11-14 21:08 | `https://irma.nps.gov/DataStore/Reference/Profile/2238908` | 102,468 |
| 6 | 2026-11-14 21:09 | `https://irma.nps.gov/DataStore/Reference/GetBoundingBoxes?referenceId=2238908` | 285 |
| 7 | 2026-11-14 21:09 | `https://irma.nps.gov/DataStore/Reference/GetHoldings?referenceId=2318550` | 1,658 |
| 8 | 2026-11-14 21:09 | `https://irma.nps.gov/DataStore/DownloadFile/759133` (Butterfield metadata text) | 7,919 |
| 9 | 2026-11-14 21:09 | `https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/BUOV_Congressionally_Designated_Alignment/FeatureServer?f=json` | 6,063 |
| 10 | 2026-11-14 21:09 | `.../BUOV_Congressionally_Designated_Alignment/FeatureServer/0/query?where=1%3D1&geometry=-109.6%2C30.5%2C-108.4%2C32.4&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&f=geojson` | 102,532 |
| 11 | 2026-11-14 21:23 | `https://tnmaccess.nationalmap.gov/api/v1/products?bbox=-110.0,31.3,-106.4,32.5&datasets=Historical%20Topographic%20Maps&prodFormats=GeoTIFF&max=1000` (for the cost estimate) | 1,422,325 |

Choices:
- **Sheets.** The card suggested Animas Peak or Playas. Playas (31.75 to 32° N) lies wholly north of the test area, so I took **Cienega Springs, N. Mex., 1:62,500, edition of 1918** (surveyed 1917 to 1918), which holds Cloverdale, Fitzpatricks Well, San Luis Pass and Guadalupe Pass, and **Animas Peak, N. Mex., 1918** (a 1963 reprint of the 1918 sheet), which holds the Gray Ranch and the Animas Valley up to 31.75° N. Where TNM had several scans of one edition, I took the largest file.
- **El Camino Real de Tierra Adentro.** Its DataStore extent is 107.08 to 105.94° W, 31.77 to 36.07° N, all east of the test area, so it was not downloaded.
- **Butterfield.** The trail lies at 32.09 to 32.36° N, north of the test area. As the card asked, it is clipped to the test area widened north to 32.4° N (78 miles of line), not dropped. NPS classes it `TYPEOFROUTE: Trail`, so it is `class: trail`.

## Tracing

Method (in `pipeline/measure/roads_test_area.py`): crop the GeoTIFF with `gdal_translate -srcwin`, look at the crop, pick vertices by eye in full-resolution pixel coordinates, then convert with the GeoTIFF's geotransform. **CRS of both sheets:** American Polyconic on NAD27 (`+proj=poly +lat_0=0 +lon_0=-108.875 +datum=NAD27 +units=m`), 5.29 m pixels. NAD27 to WGS 84 uses the CONUS Helmert shift (EPSG:1173, about 10 m), because the NADCON grids are not installed and I did not fetch them.

Lines in the seed (`class` from the sheet: solid double line = wagon road, dashed double line = trail):

| id | class | certainty | first_seen | Book's name | Length |
| --- | --- | --- | --- | --- | --- |
| road-cloverdale-san-luis-pass | wagon-road | traced | 1-03 | road to Fitzpatrick Wells | 11.0 mi |
| road-cloverdale-creek | trail | traced | 1-04 | Cloverdale Creek road | 5.2 mi |
| road-animas-valley-south / -north | wagon-road | traced | 1-07 | road to Animas | 11.7 mi |
| road-guadalupe-pass | wagon-road | traced | 2-04 | old road from Douglas | 7.8 mi |
| road-guadalupe-cloverdale | trail | approximate | 2-04 | (none) | 2.4 mi |
| road-garcia | wagon-road | traced | 1-01 | (none) | 11.9 mi |
| road-lang-ranch | wagon-road | traced | 1-01 | (none) | 6.9 mi |
| road-skeleton-canyon | trail | traced | 1-01 | (none) | 7.5 mi |
| road-clanton-draw | trail | approximate | 1-01 | (none) | 6.1 mi |
| road-butterfield | trail | approximate | 1-01 | (none) | 77.7 mi (clipped) |

- `name` is null on every traced line: the 1918 sheets print no road names. The lab letters `book_name` instead (a field I added), the name the book uses for the road. Say if you would rather letter only sheet names.
- `first_seen` is the episode where the book first uses the road (the Fitzpatrick Wells road in 1-03, the Cloverdale Creek road in 1-04, the road to Animas in 1-07, the Douglas road in 2-04), and `1-01` for context roads.

**Measurements.**
- Cloverdale as traced (the bench mark by the name) is 120 m from Cloverdale in `data/stops.geojson`.
- The boundary on the Cienega Springs sheet converts to 31.3333° N, the 31°20′ line, to within 10 m.
- Where the valley road crosses from one sheet to the other, the two sheets agree to 15 to 45 m.
- Picked vertices are good to about 2 pixels (11 m). The sheets predate NAD27: the reprint says to move the projection lines 100 feet west for NAD27, and that offset is not applied. So a vertex is good to about 40 m, under the width of a road line at 1:62,500.
- Vertices are 660 m apart on average (171 vertices on 113 km). That is enough at zoom 12 but not past it.

**My timing.** Both sheets, 9 roads, took about 10 minutes of agent time (14:10 to 14:20 local time) for cropping, reading and picking. Converting, checking the sheet edges and fixing one wrong fork took about 10 minutes more. This is an agent reading crops, not a person in QGIS. I estimate a person in QGIS needs **2 to 4 hours per 15′ sheet** to trace every road and trail on it at a vertex every 100 to 200 m, with classes and edge-matching. That is an inference, not a measurement. Cienega Springs has about 20 roads; Animas Peak has about 40.

## Book distances

The book's distances along these roads, paraphrased. The book files have no page numbers, so each reference gives the episode and the line (paragraph) in `private/book/text/<episode>.txt`.

| Mileage on the map | Road | Reference | Context (paraphrase) | Check against the trace |
| --- | --- | --- | --- | --- |
| 9 m. | road-animas-valley-south (Cloverdale to the SK Bar) | 1-02, line 1 | The family rides from home to Sanders' SK Bar after dinner, a ride of nine miles. | 9.9 miles along the traced road from the Parham place (placed at Cloverdale) to the SK Bar point in `data/stops.geojson`. Good agreement, given that the house and the SK Bar are both placed points. |
| 4 m. | road-cloverdale-creek | 1-05, line 5 | Billy waters his horse at a spring beside the road; from there it is four miles on to Cloverdale. | The traced road is 5.2 miles from Cloverdale to the sheet edge, so a spring four miles out is on it. Where the spring is, is not known, so the label sits at the middle of the road, not on a measured stretch. |

Found but not drawn:
- 1-08, line 355: someone says it is about two miles to the first cattle guard. The road and its place are not known.
- 1-04, line 1: the Nations road, which the wolf crosses a mile north of the boundary. That is a place, not a distance along a road. The road itself runs near Whitewater Creek, east of these sheets on Antelope Wells (1917), which was not fetched.
- Times, not distances: seven hours on the road to Animas (1-07, line 1); an hour's ride to Cloverdale (1-08); two hours after dark from Animas to the Sanders ranch (4-01). These could go in a card later.

## Lab style

- Wagon roads: a single ink line, 0.9 px at zoom 11 (0.5 at 8, 1.3 at 13), 85% opacity. Trails: the same line dashed 4 to 2.5.
- Names: IM Fell italic (`fonts.italic`), 10 px at zoom 11 (8.5 at 9, 12 at 13). This is the size of the ranch and spring names in the shared scale. The names sit just above the line.
- Mileages: italic, 9.5 px at zoom 11 (the spot-height base unit). They are written on the line, turned to it, and the paper-coloured halo breaks the line around them, as Wheeler writes "13.5 m.".
- One ink: the site's `ink` token. The halo is the paper of the chosen preset.
- Today's Natural Earth roads (`road` layer) are hidden inside the test area by a `within` filter while the toggle is on. MapLibre tests each tile's piece of a road, so a road that crosses the box edge is cut at a tile edge near the box, not exactly on it.
- The mileage labels are points (with an angle) that the script computes into the lab file. A `line-center` label on the line repeats at every tile edge, because a GeoJSON source cuts lines at tile edges.

## What a full network would cost

**Sheets, US side** (TNM, request 11; corridor 110.0 to 106.4° W, 31.25 to 32.5° N, Douglas and Willcox to El Paso):
- **1:62,500 with an edition from 1945 or earlier: 51 sheets.**
  - Row 31.25° N: Bisbee (1902 to 1933), Stark 1932, Douglas 1914, College Peaks 1940, McDonald 1922, Cienega Springs 1918, Antelope Wells 1917, Dog Mountains 1918.
  - Row 31.5° N: Gleeson 1925, Fairbank 1932, Swisshelm 1922, Pedregosa 1926, Apache 1940, Animas Peak 1918, Walnut Wells 1918, Big Hatchet Peak 1918, Ysleta 1939.
  - Row 31.75° N: St. David 1922, Courtland 1926, Light 1926, Rucker 1926, Rodeo 1926, Pratt 1918, Playas 1918, Hachita 1918, Victorio 1918, Hermanas 1917, Columbus 1917, Camel Mountain 1917, Mt. Riley 1917, Noria 1917, Canutillo 1917, Fort Bliss 1942.
  - Row 32.0° N: Dragoon 1943, Cochise 1943, Dos Cabezas 1943, Cochise Head 1926, Chenoweth 1928, Aden 1941, Afton 1943, La Mesa 1943, Newman 1940.
  - Row 32.25° N: Winchester Mts. 1943, Willcox 1943, Fisher Hills 1944, Bowie 1928, Orange Butte 1926, Corralitos Ranch 1943, Las Cruces 1941, Organ Peak 1941, Parker Lake 1943.
- **The core where the book's riders go** (the bootheel, the Animas and Playas valleys, Hachita): 12 sheets. They are Rodeo, Pratt, Playas, Hachita, Apache, Animas Peak, Walnut Wells, Big Hatchet Peak, McDonald, Cienega Springs, Antelope Wells and Dog Mountains. Two of them are done here, and only in part.
- **Gap:** Lordsburg and Deming (109 to 107.25° W, 32.0 to 32.5° N) have no 1:62,500 sheet before 1956. Only 1:125,000 sheets cover them: Deming 1915, San Simon 1917 and Silver City 1909 to the north. North of 32.5° N, which the corridor leaves out, the book also goes to the Black Range and Silver City.
- **Cost.** At 2 to 4 hours a sheet, the 12 core sheets take 24 to 48 hours. All 51 sheets take 100 to 200 hours. A roads-the-book-names network (the plan's 30 to 60 lines) takes about 1 hour a sheet on the 12 core sheets.

**The Mexican gap.** The 1918 sheets stop at the boundary: south of 31.33° N the test area is blank on them, and nothing on the Sonora side was traced. The packet's sources:
- **AMS F401, 1:500,000, "Ciudad Juárez", 1933.** At UT GeoData, probably georeferenced. At 1:500,000 a 0.5 mm line is 250 m wide, so roads from it can only be `approximate`.
- **AMS F541, 1:250,000, Mexico (1941, 1947).** Its northern sheets are not confirmed.
- **A joint DCM/AMS 1:250,000 series** with Douglas and Nuevo Casas Grandes sheets. It is at Texas A&M and is catalogue-only: a bot check stops automated clients. The licence of joint Mexican sheets is uncertain.
- OpenStreetMap is ODbL, which the brief's licence rule does not allow for tracing.

So the Sonora half of the test area (Cajón Bonito, the Bavispe valley road, the Cabellera passes) needs F401 georeferenced by hand (about 1 to 2 hours for the sheet's corner of the test area, inferred) and the roads drawn as `approximate`. It could also wait for the F541 northern sheets.

**Licences.**
- USGS Historical Topographic Map Collection: public domain. Credit: U.S. Geological Survey, Historical Topographic Map Collection.
- NPS Butterfield Overland NHT: a US federal work. The DataStore record has no licence field; the service says `DATAACCESS: Unrestricted` and `PUBLICDISPLAY: Public Map Display`. Treated as public domain [inferred]. Credit: National Park Service, National Trails Intermountain Region. Its use constraint says the data are not intended for scales larger than 1:100,000. That is about zoom 11 here, and the lab draws the trail to zoom 13.
- AMS (US Army): public domain in the US. Joint DCM/AMS sheets: uncertain.

## What does not work yet

- Only the test area's US side, and only 9 roads on two sheets. The Douglas road is traced only to the Arizona line at Guadalupe Pass; it continues on McDonald, Ariz., 1922 (not fetched).
- Two lines are `approximate`: the last stretch of the Douglas road into Cloverdale, and the east end of the Clanton Draw road, where several dashed roads meet on the scan.
- The road north from Fitzpatricks Well, the Antelope Wells sheet (the Nations road, Whitewater Creek) and the railroads are not traced. No railroad crosses these two sheets.
- The "4 m." label marks the road, not a measured stretch.
- Roads are not in `PROGRESS_LAYERS` (spoiler mode). Every line carries `first_seen` for that.
- No `docs/decisions/` entry yet. The judgement calls are listed here (which sheets, `book_name` as label, where the 9 m. stretch starts and ends, the Helmert shift) for the owner to accept or change first.

## Open questions for the owner

1. **Labels.** Letter roads with the book's names ("road to Animas") when the sheet prints none, or leave unnamed roads unlettered, as the sheets do?
2. **Scale.** The plan's 30 to 60 lines over the 12 core sheets (about 12 to 24 hours), or every road on those sheets (about 24 to 48 hours)?
3. **Mexico.** Georeference F401 (1933, 1:500,000) now for approximate Sonora roads, or wait for the 1:250,000 sheets?
4. **The 1918 sheets against 1939 to 1944.** The story is twenty years later. Should the NM 1940 highway map (already in the plan) set the class, for example graded or unimproved?
