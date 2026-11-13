# Stage 6 review: photo candidates from Wikimedia Commons

`photos.csv` lists candidate photos for the places and stops, up to five a place, ranked. Nothing is in the app or the data layers yet: you pick first (plan section 11, stage 6).

**The search is not finished.** Commons rate-limited the run twice (see "Requests" below), and a polite retry at 3:33 am on 13 November was refused again after a few requests, so 20 of 135 places are searched. The other 115 wait for a rerun, listed in `TODO-prerequisites.md`.

## Method

`pipeline/src/crossing/photos.py`, run from the repo root:

```
uv run --project pipeline python -m crossing.photos            # search, then write the CSV
uv run --project pipeline python -m crossing.photos --dry-run  # count the requests still needed
uv run --project pipeline python -m crossing.photos --offline  # write the CSV from the cache only
```

1. **What is searched.** Every place in `data/places.geojson`, and every stop in `data/stops.geojson` that has no `place_ref` (a stop with a `place_ref` shares its place's photos; the CSV lists its id under `stop_ids`). Not searched: tale places outside the story box (104°–113° W, 27°–36° N), and inferred or reported stops with a radius over 3 km, because a photo "near" a 10 km circle says nothing. That gives 135 places to search and 49 skipped stops.
2. **Wikidata.** The Wikidata item is the feature's own Wikidata id, or the one item that carries its GeoNames id (P1566) or GNIS id (P590). The links come from the Wikidata entities the gazetteer already cached in `private/cache/wikidata/`, with no new request. 80 of the 135 places link this way, 52 of them with an image (P18) and 47 with a Commons category (P373). Where two items claim one id, none is taken.
3. **Commons, in plan order (section 10).** The item's image (P18), then up to 20 files in its Commons category (P373), then Commons geosearch for files within 5 km of the point (up to 30). One API call per step returns each file's licence, author, date, categories, coordinates and an 800 px thumbnail URL (`extmetadata`). No image is downloaded.
4. **Licences (plan section 3).** Kept: public domain, CC0, CC BY and CC BY-SA, any version. Dropped: NC, ND, non-free, GFDL-only and anything unlabelled.
5. **What a file shows**, roughly, from its categories and title: `landscape`, `building`, `wildlife` or `other`. Maps, coats of arms, flags and drawings are dropped, and so are aerial views (astronaut photos from the ISS and USDA orthophoto tiles), because the map already has satellite imagery.
6. **Rank.** The Wikidata image first; then landscape views, nearest first; then other, building and wildlife files, nearest first. Category files have no distance unless they carry coordinates, so they come after the geosearch files of their kind.

## The CSV

One row per candidate. Fill in `pick` (for example `y`) on the rows you want; leave the rest empty.

| Column | Meaning |
| --- | --- |
| `place_id`, `place_name`, `role`, `kind` | The place or stop, from the data layers |
| `stop_ids` | Stops that share this place |
| `wikidata` | The linked Wikidata item, if any |
| `rank`, `pick` | The proposed order, and your pick |
| `file_title`, `via` | The file's title (Commons `ObjectName`, else the file name); how it was found: `wikidata-p18`, `commons-category` or `geosearch` |
| `looks_like`, `distance_m` | The rough kind; metres from the point, where the file has coordinates |
| `author`, `licence`, `licence_url`, `date` | From the file's `extmetadata` |
| `commons_url`, `thumbnail_url` | The file page (the TASL source) and an 800 px thumbnail |

## Counts (cached run, 12 November 2026)

| | Places |
| --- | --- |
| To search | 135 |
| Searched | 20 |
| With candidates | 5 (19 rows) |
| Searched, no candidate | 15 |
| Not searched yet (rate limit) | 115 |

Files seen with an allowed licence: 36; dropped as aerial views: 62; dropped as not a photo: 1. No file in the searched places was dropped for its licence.

**Licences in the CSV:** CC0 10, CC BY-SA 3.0 4, CC BY 2.0 2, CC BY-SA 4.0 1, CC BY 4.0 1, public domain 1.

**Searched, no candidate** (geosearch found only aerial views here): Sierra de la Madera, Animas Mountains, Peloncillo Mountains, Foster Draw, Skeleton Creek, Starvation Canyon, Hog Canyon Spring, Clanton Draw, Cloverdale Creek, Cloverdale, Cajón Bonito, Sierra de la Cabellera, Colonia Oaxaca, Colonia Morelos, Sierra de los Pilares de Teras. All are stop places in Part I's country, where Commons has few ground photos.

**With candidates:** San Luis Mountains (3, views from the Puerto San Luis), Whitewater Creek (1, a kangaroo rat), Animas Valley (5, Lordsburg Mesa views), Casas Grandes (5, led by its Wikidata image of the town sign), Guadalupe Mountains (5).

**Not searched yet:** the other 115 places, from Cloverdale to Fort Sumner, and the stops `j1-border-108-30`, `j1-clanton-foster`, `j3-websters`, `j4-lordsburg`, `j7-boyds-grave`, `j7-cemetery` and `j7-black-range`. The script prints the full list.

## Requests

Plan section 11 asks before any network batch. This run was in the overnight plan you approved (step 13), so it went ahead at one request a second with the User-Agent `crossing-map-pipeline/0.1 (reading-guide map; contact via repository)`, and every answer is cached in `private/cache/photos/`.

1. The Wikidata Query Service answered 429 to the second SPARQL query: it was rate-limiting everyone to one request a minute during an outage (Retry-After 1,000 s). The run stopped using it and took the Wikidata links from the gazetteer's cache instead (step 2 above).
2. The Commons API answered 429 after 6 requests (Retry-After 7 s). After a 5-minute pause, one more try at one request every 3 seconds got a second 429 after 11 requests. The run then stopped asking, as decided, and wrote the CSV from the 21 cached answers.

A rerun on another day needs about 219 requests (`--dry-run` gives the current count), about 11 minutes at the 3-second interval. If Commons refuses again, the script stops asking on the first refusal and writes what it has.

## How a pick becomes data (proposed, not built)

1. Each picked row becomes a record in a new `data/photos.json`, an array of objects:

```json
{
  "id": "photo-casas-grandes-1",
  "place_ids": ["place-casas-grandes"],
  "title": "Stella nombre Casas Grandes, Chihuahua",
  "author": "MikSed",
  "source": "https://commons.wikimedia.org/wiki/File:Stella_nombre_Casas_Grandes,_Chihuahua.jpg",
  "licence": "CC BY 4.0",
  "licence_url": "https://creativecommons.org/licenses/by/4.0",
  "date": "2018-08-27",
  "file": "photos/photo-casas-grandes-1.webp",
  "alt": "",
  "caption": "",
  "modified": false
}
```

   `title`, `author`, `source` and `licence` (with `licence_url`) are the four TASL fields, shown under the photo and on the Credits page. `modified` becomes `true` if the photo is cropped, and the credit then says "cropped from the original". `alt` and the "today" caption (plan section 10) are written by hand.
2. A script reads the picks, writes `data/photos.json`, fetches each picked file once at 800 px, converts it to WebP in `site/public/photos/`, and fills each feature's existing `photo_ids` list (already in `data/schema/story-layer.schema.json`).
3. A JSON Schema for `photos.json` makes the four TASL fields required, and `crossing.validate` checks the licence against the allowed list and that every `photo_ids` entry exists.

## Decisions made alone

- Aerial views are dropped, not ranked low: in the 13 places searched they were 62 of 98 allowed files and filled every slot in the back country.
- The Wikidata Query Service was not retried and the Wikidata action API was not used in its place; the links come from the gazetteer's cache only.
- After Commons' second 429 the run stopped for the night instead of slowing further.

## Questions for you

1. Rerun the remaining 219 or so Commons requests on another day, at one request every 3 seconds?
2. Drop aerial views (as now), or keep the USDA orthophotos and ISS photos as a last resort for the back-country places?
3. Should places with no Wikidata link (55 of 135) get one by a Wikidata search later, to reach their P18 and category files?
