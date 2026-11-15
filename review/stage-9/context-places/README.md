# Context places on the main map (stage 9)

The owner asked for "all of the more context": the gazetteers' other period features along the journeys, in the Wheeler manner, beside the water places. Decision: docs/decisions/0028-context-places.md (proposed).

## What changed

- `pipeline/src/crossing/context_places.py` (new) writes `data/context_places.geojson` (new story layer, 2,391 points, 1.3 MB; the map's trimmed copy is 444 KB) and its GeoParquet copy. Run it after `crossing.water_places`.
- The schema gains the layer, 15 kinds and a `historical` boolean; `crossing.validate` and so `crossing.downloads` list the layer.
- Site: `site/src/map/contextPlaces.ts` (new) draws the marks and the `context-place` layer from zoom 11, under the water places; `waterPlaces.ts` registers the new marks with its own; `style.ts` adds the source and layer; `spoiler/filter.ts` lists the layer (all 1-01); `scripts/copy-data.mjs` trims it; the Data page, site facts, How it's built's Caveats (one paragraph), CHANGELOG, data/README and docs/pipeline.md mention it.
- `tools/spoiler-leak.mjs` checks the layer as it checks the water places; `tools/context-places-shots.mjs` (new) takes the screenshots.

## Counts by kind and source

| Kind | GNIS (current) | GNIS 2021 file | GeoNames |
| --- | ---: | ---: | ---: |
| military (forts, camps, army air fields) | 7 | | |
| abandoned (ghost towns, PPLQ, FRMQ) | 22 | | 101 |
| ruin (archaeological sites, ANS) | | | 21 |
| mine | | 658 | 15 |
| sawmill | | | 10 |
| camp (cow camps, cabins, a logging camp) | | 41 | 1 |
| corral | | 69 | 4 |
| church | | 7 | 1 |
| cemetery | | 86 | |
| school | | 14 | |
| post-office (historical only) | | 31 | |
| customs | | | 2 |
| station (stage stations, an abandoned station, a siding) | | 7 | 2 |
| ranch (Locale ranches, homesteads, "places") | | 389 | |
| well | | 465 | |
| windmill | | 298 | |
| tunnel (railway, mark only) | | | 10 |
| railway (name only) | | | 1 |
| lake (name only) | 54 | | |
| flat (name only) | 75 | | |
| **Total** | **158** | **2,065** | **168** |

## What was dropped, and why

Printed by the build (rerun it to see each line):

- 178 town churches and schools (158 churches, 20 schools) within 1.5 km of a town: most are later buildings, and the town's name already marks the place.
- 25 points within 1 km of a book place (Santa Rita and Deming 4 each; Steins, Silver City, Reserve, Hermanas and Hachita 2 each; others 1).
- 35 with the same name as a water place or a kept context place within 1 km (mostly GeoNames ranches already in `water_places`, and wells named twice), or an old post office within 2 km of its own ghost town.
- 1 railway name (Ferrocarril Bosques de Chihuahua) 2.5 km from any drawn railway.
- By rule, before the corridor test: modern Locales (weather, ranger and pumping stations, substations, campgrounds, trailheads, historic-site markers and so on), prospects, pits, quarries, deposits and claims, wells named only "Water Well" or by number, current post offices, schools named as modern ones, congregations with later names, GeoNames airfields, a 2026 garrison (INSM) and a modern technical school (SCH).
- By hand (`GNIS_EXCLUDE`): Winslow Air Force Station (the Air Force dates from 1947), Fort Bayard Military Reservation (a second point for Fort Bayard), Harrison A Schmitt School (named for the astronaut), Camp Thunderbird (a youth camp).
- Not used: a rule to read bare-name Locales near the railway as sidings. Only two lie within 1.5 km of a drawn railway, and both are mining works (Peru Mining Company, Asarco Mill).

## The old GNIS national file

It can still be downloaded. USGS keeps the last national file before the 2021 split in its archive: `https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/Archive/MainDomestic/{NM,AZ}_Features_20210825.txt` (public domain; the archive also holds `NationalFile.zip`, `AllStates.zip` and the topical gazetteers, including `HIST_FEATURES.zip`). Both files are cached under `private/cache/gazetteer/Features_20210825/`; their MD5 sums match the bucket's ETags. It adds Locale, Mine, Well, Cemetery, Church, School, Post Office and Building in the corridor (1,147 Locales, 1,012 mines, 1,969 wells before the rules above).

Requests (User-Agent crossing-map-research/0.1, 2 s or more apart, 15 November 2026, UTC), 4 of the 7 allowed:

| Time | URL | Bytes |
| --- | --- | ---: |
| 18:28:06 | `https://prd-tnm.s3.amazonaws.com/?list-type=2&prefix=StagedProducts/GeographicNames/&delimiter=/` | 1,492 |
| 18:28:13 | `https://prd-tnm.s3.amazonaws.com/?list-type=2&prefix=StagedProducts/GeographicNames/Archive/` | 37,109 |
| 18:28:24 | `.../Archive/MainDomestic/NM_Features_20210825.txt` | 7,787,508 |
| 18:28:28 | `.../Archive/MainDomestic/AZ_Features_20210825.txt` | 6,827,809 |

The two listings are cached in `private/cache/gazetteer/old-gnis-probe/`.

## How to see it

`cd site && npm run dev`, then zoom to 11 or more anywhere along the journeys. Screenshots (whole book read, desktop) in `private/review/stage-9/context-places/`, from `node tools/context-places-shots.mjs <base-url>`:

- `silver-city-z9.jpg`, `silver-city-z10.jpg`, `hachita-playas-z10.jpg`: nothing new below zoom 11, as intended.
- `pinos-altos-z11.jpg`: the mining district north of Silver City, crossed picks thinning out where they crowd.
- `fort-bayard-z12.jpg`: the fort's flag, the national cemetery, mines.
- `lordsburg-shakespeare-z11.jpg`: Lordsburg Army Air Field, Barney Stage Station, the Pyramid Mountains' mines, windmills across the flats.
- `hachita-z12.jpg`, `animas-valley-z11.jpg`, `bavispe-z11.jpg`: the bootheel's ranches, wells and playas; Sonoran abandoned places and ruins.
- `cumbres-tunnels-z12.jpg`: the tunnel marks by the Chihuahua al Pacífico line near Cumbres.

## Checks

validate (18 files ok), downloads --check, echo_check (0 shared runs), ruff, pytest (22), `npx tsc -b`, lint, `npm test` (23), build, and the spoiler-leak test against a VITE_DEBUG=1 build: no leaks at all ten reading positions (run in two parts, unset to 2-04 and 3-08 to all, after the preview server stopped mid-run).

## Open questions for the owner

1. Lakes and flats begin at zoom 11 like the rest. They might show from zoom 10, since they name the land rather than a building.
2. Wells and windmills (763) are the biggest group. If they crowd the flats, they could start at zoom 12.
3. The church and school rule (more than 1.5 km from a town) keeps 7 churches and 14 schools in the US. Should any town church be kept as a landmark (for example the old adobe parishes)?
4. The tunnel marks sit on the real line, which Natural Earth's generalised railway may miss by several hundred metres. A traced period railway would fix it.
5. The decision is numbered 0028. If another branch has taken that number, renumber it on merge.
