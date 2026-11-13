# Data

Open data for the reading map: GeoJSON (WGS 84, RFC 7946) for story layers, JSON for episodes and translations, and JSON Schemas in `schema/`.

Each layer has a row below with its source and licence.

| File | Contents | Licence |
| --- | --- | --- |
| `places.geojson`, `stops.geojson`, `areas.geojson`, `journeys.geojson` | Places, stops, inferred areas and route segments for all seven journeys (J1–J7, Parts I to IV), plus context towns. Each route segment's `travel` says how the leg was made (null for horseback; foot, truck, car, bus, train, or reported). Built by `crossing.build_story` | Our own work CC BY 4.0; each feature's `source_licence` gives its source's terms (GNIS public domain, GeoNames CC BY 4.0, Wikidata CC0, USGS NHD, Census TIGER and Natural Earth public domain) |
| `elsewhere.json` | Places the book names that lie outside the story box, listed in the panel rather than mapped | CC BY 4.0 |
| `raised/*.geojson` | The same story layers as drawn in the map's Raised view: every point moved north by twice its height above the lowest ground of the corridor of the stretches ridden or walked (decisions 0018 and 0019). `raised/archives.json` lists the Raised view's tile archives. Built by `crossing.plan_oblique`; use the files above for analysis | As the files above; heights from Copernicus DEM GLO-30 (notice below) |
| `parquet/*.parquet` | A GeoParquet 1.1 copy of `places`, `stops`, `areas`, `journeys` and `mountain_glyphs`, one file per layer, for DuckDB, GeoPandas and QGIS (decision 0009). One row per feature, one column per property, typed from `schema/story-layer.schema.json`, and the geometry as WKB in WGS 84. Built from the GeoJSON by `crossing.downloads`; CI checks they match | As the GeoJSON layer each one copies |
| `vignettes.geojson` | Anchors for the map's decorative drawings (plan section 10): thirteen points, each in empty country near the thing it stands for, with `stands_for`, `place_ref`, a zoom range (`min_zoom`, `max_zoom`), a `priority` for collisions, `first_seen`, a paraphrased note and the reasoning for the anchor. Two located sites (Paquimé and the Hacienda de San Diego) also get a hairline leader, a LineString of kind `vignette-leader`. The drawings now in the sprite are placeholders; the real ones will be the owner's or an illustrator's. Built by `crossing.build_vignettes` from `pipeline/seeds/vignettes.csv` | CC BY 4.0 |
| `episodes.json` | The novel's 41 episodes: opening words and length | CC BY 4.0 |
| `open-questions.json` | Judgement calls about where something is, in short: what the map shows, the other reading and why, with the features concerned and the episode from which each may be shown. The long form is `docs/open-questions.md` | CC BY 4.0 |
| `mountain_glyphs.geojson` | 767 summits with at least 200 m prominence, plus named mesas, buttes and cones from 100 m, unnamed mesas the DEM shows clearly, and the book's named summits, found in Copernicus GLO-30; 168 passes: GNIS gaps and GeoNames passes that lie on a key col, and the key cols of the most prominent summits; names from GNIS and GeoNames | Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30 |

Every feature carries `certainty`, `source`, `source_licence`, and `first_seen`. See `docs/plan.md`, section 6, for the property schema.

## No passages of the novel

Notes and reasoning are our own words, and Spanish appears only as an incipit of at most five words (plan section 3). `crossing.echo_check` checks the first rule. It compares every tracked text file, and `site/dist/` if it has been built, with the private text of the novel, and reports each run of 8 or more consecutive words that they share. Words are compared after folding case, accents, curly quotes and punctuation. Each report line gives the file, the line and only the first 8 words of the run. The check exits 1 on a match. The novel's text is not in the repo, so in CI the check skips with a message and exits 0. Run it locally from the repo root after a data change:

```
uv run --project pipeline python -m crossing.echo_check                # tracked files and site/dist/
uv run --project pipeline python -m crossing.echo_check data review    # only these paths
uv run --project pipeline python -m crossing.echo_check --words 7      # a shorter run
```

Place names and short stock phrases are shared with the novel by nature, so a match is a prompt to reword, not proof of copying. Binary files (the GeoParquet copies) are skipped; they hold the same text as the GeoJSON.
