# Stage 1 review packet: Part I, right

## What was built

- **Gazetteer resolver** (`pipeline/src/crossing/gazetteer.py`). It matches the 30 Part I names in `pipeline/seeds/part1.csv` against USGS GNIS (New Mexico, Arizona), GeoNames (Mexico), and Wikidata, within the story box. It keeps candidates of the expected feature type in the expected state, then picks the one nearest the settled stops beside it on the same journey. Output: `places.csv`, with every candidate listed.
- **Part I layers** in `data/`: 29 places, 26 stops on J1 and J2, 7 inferred areas, and 24 route segments, all valid against the schema.
- **The app** shows them on the plain paper base: routes in each character's ink, numbered stops, a panel with the stop's evidence, and a Back/Next stepper that flies to each stop. Click a place dot or an area for its source.
- **Dates from the book:** `pipeline/src/crossing/extract.py` read your EPUB privately. It found 41 episodes, not 40, and the first appearance of every Part I name. Every `first_seen` now comes from the text (decision 0010), and `data/episodes.json` lists the episodes with blank summaries for you to write.
- **Measurements:** every distance quoted in the reasoning is computed in `pipeline/measure/distances.py` (pyproj, WGS 84).

## What to look at

This is the most important review in the project.

1. Open `checklist.md`. Each row links to OpenStreetMap and to satellite imagery.
2. Start with the 13 rows marked **check**. These were picks among several same-named candidates.
3. Then read each stop in the app (https://jburkinshaw.github.io/crossing-map/preview/) and compare its reasoning with the book.

## Questions for you

1. **Episode summaries.** `data/episodes.json` has a blank `summary` for each of the 41 episodes. They are yours to write, spoiler-safe and in your own words.
2. **The 12 rows marked check** in `checklist.md`, on imagery.

## Settled by research (11 November 2026)

- **Sierra La Madera.** The USDA abstract on the range's mammals (Bermudez-Enriquez et al. 2013) puts it in the municipios of Cumpas, Granados, Huásabas, Moctezuma and Villa Hidalgo. The pick lies between Cumpas (27 km west) and Huásabas on the Bavispe (21 km east). That fits a wolf on its eastern slopes crossing the Bavispe. The crossing area moved to the Granados–Villa Hidalgo reach.
- **The volcanic plain** is read as the Geronimo–San Bernardino volcanic field, south-west of the Guadalupe pass. It is supported, not proven.
- **Robertson's crossfence.** The Robertson family ran the Cloverdale Ranch from the early 1900s (Range Magazine). The fence is likely theirs; the ranch's bounds are unknown.

Open threads from these are on the private follow-up list, `private/follow-ups.md`.

## Network use

Approved batch: GNIS for New Mexico and Arizona (2.5 MB), GeoNames Mexico (15 MB), and 82 Wikidata API requests. I estimated about 45: the search runs once for each alternate name, which I did not count, and 3 were repeated after a cache-naming fix. All answers are cached in `private/cache/`, so reruns make no requests. I did not download INEGI's locality catalogue: GeoNames covered every Mexican name in Part I.

## Known limits

- **Routes are schematic.** Every segment is a gentle dashed curve: the plan's fallback when no road or river line is available. Snapping to the Cloverdale Creek road and the Bavispe waits for the river and road lines in stage 2.
- **Inferred areas are circles**, sized to the evidence. They are stand-ins until they are redrawn by hand in QGIS (decision 0008), and QGIS is blocked for now (see `TODO-prerequisites.md`).
- **No satellite yet.** There is no MapTiler key, so you check against the linked imagery instead.
- **The Bavispe has no point.** GeoNames puts its single point at the river's mouth, about 100 km south of the story. Crossings are stops instead.
- **The book corrected the plan.** It never names Batepito, so the hacienda is now an unnamed area near Colonia Morelos. It spells Cajon Bonita with an a. It first names De Baca County and Ascensión in Part IV, so they are dated 4-07 and 4-03.
- **Places named in passing** from section 2.3 are in, except Texas and Pennsylvania, which are off the map.
