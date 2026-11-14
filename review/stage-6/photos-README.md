# Stage 6 review: photo candidates from Wikimedia Commons

`photos.csv` lists candidate photos for the places and stops, up to five a place, ranked. Nothing is in the app or the data layers yet: you pick first (`docs/roadmap.md`, stage 6).

**The search is finished** (13 November 2026, evening): every one of the 139 places and stops in the story box is searched. Commons rate-limited the first runs (see "Requests" below); the last run asked once every 15 seconds and waited out each refusal, starting at a minute and doubling.

## Method

`pipeline/src/crossing/photos.py`, run from the repo root:

```
uv run --project pipeline python -m crossing.photos            # search, then write the CSV
uv run --project pipeline python -m crossing.photos --dry-run  # count the requests still needed
uv run --project pipeline python -m crossing.photos --offline  # write the CSV from the cache only
```

1. **What is searched.** Every place in `data/places.geojson`, and every stop in `data/stops.geojson` that has no `place_ref` (a stop with a `place_ref` shares its place's photos; the CSV lists its id under `stop_ids`). Not searched: tale places outside the story box (104°–113° W, 27°–36° N), and inferred or reported stops with a radius over 3 km, because a photo "near" a 10 km circle says nothing. That gives 135 places to search and 49 skipped stops.
2. **Wikidata.** The Wikidata item is the feature's own Wikidata id, or the one item that carries its GeoNames id (P1566) or GNIS id (P590). The links come from the Wikidata entities the gazetteer already cached in `private/cache/wikidata/`, with no new request. 80 of the 135 places link this way, 52 of them with an image (P18) and 47 with a Commons category (P373). Where two items claim one id, none is taken.
3. **Commons, in design order (section 10).** The item's image (P18), then up to 20 files in its Commons category (P373), then Commons geosearch for files within 5 km of the point (up to 30). One API call per step returns each file's licence, author, date, categories, coordinates and an 800 px thumbnail URL (`extmetadata`). No image is downloaded.
4. **Licences (design section 3).** Kept: public domain, CC0, CC BY and CC BY-SA, any version. Dropped: NC, ND, non-free, GFDL-only and anything unlabelled.
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
| To search | 139 |
| Searched | 139 |
| With candidates | 87 (330 rows) |
| Searched, no candidate | 52 |

Files seen with an allowed licence: 1,611; dropped as aerial views: 372; dropped as not a photo: 95; dropped for their licence ("No restrictions" or "Copyrighted free use", which need checking by hand): 17. Linked to Wikidata: 84 places, 54 of them with an image (P18) and 49 with a Commons category (P373).

**Licences in the CSV:** CC0 70, CC BY-SA 3.0 65, CC BY-SA 4.0 52, public domain 34, CC BY 2.0 32, CC BY-SA 2.0 29, CC BY 4.0 26, CC BY 3.0 17, CC BY-SA 2.5 3, CC BY-SA 3.0 IGO 2. **Kinds:** landscape 137, building 46, wildlife 5, other 142.

**Searched, no candidate** (52, mostly back-country stops, where geosearch finds only aerial views): the Part I stop places from the Sierra de la Madera to the Pilares de Teras, and Ascensión, the San Luis Pass, Black Point, Taylor's Draw, Cañón la Cabellera, Esqueda, Villa Hidalgo, the Llanos de Carretas, Tamichopa, Ojito, Animas Peak, the Dos Cabezas Mountains, Colonia Juárez, La Babícora, the Hacienda de San Diego, the Río Piedras Verdes, Las Varas, Mata Ortiz, La Boquilla, San José, La Norteña, La Pinta, the Hatchet Mountains, the Sierra del Nido, Corralitos, Duncan, nine places from the tales, and the stops `j1-clanton-foster` and `j7-boyds-grave`.

## Requests

The project asks before any network batch (`CLAUDE.md`). This run was in the overnight plan you approved (step 13), so it went ahead at one request a second with the User-Agent `crossing-map-pipeline/0.1 (reading-guide map; contact via repository)`, and every answer is cached in `private/cache/photos/`.

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

   `title`, `author`, `source` and `licence` (with `licence_url`) are the four TASL fields, shown under the photo and on the Credits page. `modified` becomes `true` if the photo is cropped, and the credit then says "cropped from the original". `alt` and the "today" caption (design section 10) are written by hand.
2. A script reads the picks, writes `data/photos.json`, fetches each picked file once at 800 px, converts it to WebP in `site/public/photos/`, and fills each feature's existing `photo_ids` list (already in `data/schema/story-layer.schema.json`).
3. A JSON Schema for `photos.json` makes the four TASL fields required, and `crossing.validate` checks the licence against the allowed list and that every `photo_ids` entry exists.

## Decisions made alone

- Aerial views are dropped, not ranked low: in the 13 places searched they were 62 of 98 allowed files and filled every slot in the back country.
- The Wikidata Query Service was not retried and the Wikidata action API was not used in its place; the links come from the gazetteer's cache only.
- After Commons' second 429 the run stopped for the night instead of slowing further.

## Questions for you

1. (Done: the search finished on 13 November.)
2. Drop aerial views (as now), or keep the USDA orthophotos and ISS photos as a last resort for the back-country places?
3. Should places with no Wikidata link (55 of 135) get one by a Wikidata search later, to reach their P18 and category files?
