# Data

Open data for the reading map: GeoJSON (WGS 84, RFC 7946) for story layers, JSON for episodes and translations, and JSON Schemas in `schema/`.

The licences are in place, and the owner has yet to confirm them before launch (`docs/roadmap.md`, section 2).

## Files

Every file is validated against its schema in `schema/` by `crossing.validate`, which also checks the references between files. The schemas describe every field; `docs/design.md`, section 6, explains the main ones.

| File | Contents | Schema |
| --- | --- | --- |
| `places.geojson` | 132 named places, including context towns the book never names. 35 carry `name_in_text`, the book's own spelling | `story-layer` |
| `stops.geojson` | 171 stops, in order, on the seven journeys J1 to J7 | `story-layer` |
| `journeys.geojson` | 165 route segments between stops, each with its `travel` | `story-layer` |
| `areas.geojson` | 59 inferred areas and named regions, each with its reasoning | `story-layer` |
| `vignettes.geojson` | 13 anchors for the map's drawings, and 2 hairline leaders to real sites | `story-layer` |
| `landforms.geojson` | 313 label lines along ranges, valleys, plains, mesas and plateaus, for names set along the landform (decision 0023) | `story-layer` |
| `water_places.geojson` | 1,233 springs, tanks, ranches and stations within 20 km of the journeys ridden or walked, from GNIS and GeoNames, with the book's own 4 (they point at their place) | `story-layer` |
| `mountain_glyphs.geojson` | 836 summits and 168 passes found in the Copernicus DEM, each with its landform | `story-layer` |
| `episodes.json` | The novel's 41 episodes: opening words, length, and a spoiler-safe summary | `episodes` |
| `translations.json` | 916 Spanish lines: an incipit of at most five words, our English, and where each was spoken | `translations` |
| `open-questions.json` | 22 judgement calls about where something is, each shown from its own episode | `open-questions` |
| `elsewhere.json` | 16 places the book names outside the story box, listed in the panel | `elsewhere` |
| `raised/*.geojson` | The four story layers as drawn in the Raised view, each point moved north by its height (decisions 0018 and 0019). Use the flat files for analysis | `story-layer` |
| `raised/archives.json` | The Raised view's tile archives, in drawing order | `archives` |
| `parquet/*.parquet` | A GeoParquet 1.1 copy of each story layer, typed from the schema (decision 0009). CI checks they match the GeoJSON | |

Every feature carries `certainty`, `source`, `source_licence`, and `first_seen`.

## Licences and attribution

Our own data, notes, and translations are CC BY 4.0 (`LICENSE`). Each feature's `source_licence` gives the terms of the dataset that fixed its coordinates. The same credits appear on the site's Credits page and, for tiles, in each archive's attribution.

| Source | Used for | Licence | Credit |
| --- | --- | --- | --- |
| This project | Notes, reasoning, translations, inferred areas, routes | CC BY 4.0 | "The Crossing reading map, Joe Burkinshaw" |
| GeoNames | Places, summits, passes, springs, ranches, and stations in Mexico | CC BY 4.0 | "GeoNames" |
| USGS GNIS | Places, summits, passes, and springs in the US | Public domain | Courtesy of the U.S. Geological Survey (GNIS) |
| Wikidata | A few place locations | CC0 | Courtesy link |
| GMBA Mountain Inventory v2 | The axes of US ranges in `landforms.geojson` | CC BY 4.0 | "GMBA Mountain Inventory v2 (Snethlage et al. 2022), GMBA and EarthEnv" |
| Copernicus DEM GLO-30 | Summits, passes, hachures, contours, and the Raised view | Copernicus DEM licence | The notice below |
| AWS Terrain Tiles | The hillshade and the Tilted view | Public domain (USGS); INEGI free-use terms | "3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey. Source: INEGI, Continental relief, 2016." |
| INEGI Red Hidrográfica 1:50,000, edición 2.0 | Rivers, creeks, and lakes in Mexico; Mexican streams in the Raised view | INEGI free-use terms | "Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0" |
| USGS NHD | US rivers and streams, and the rivers some routes follow | Public domain | "USGS National Hydrography Dataset courtesy of the U.S. Geological Survey" |
| US Census Bureau | County lines (cartographic boundaries, 2023) and the roads some routes follow (TIGER/Line) | Public domain | Courtesy of the U.S. Census Bureau |
| Natural Earth | Borders, states, roads, railroads, lakes outside Mexico, and the choice and names of rivers | Public domain | "Made with Natural Earth" |

**Copernicus notice.** Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.

The tile archives are release assets, not files in this folder; their credits travel in each archive's metadata:

| Archive | Credit |
| --- | --- |
| `base.pmtiles` | INEGI (rivers, creeks, and lakes in Mexico), USGS NHD (US streams), US Census Bureau (county lines), Natural Earth |
| `relief.pmtiles`, `relief-dense.pmtiles`, `contours.pmtiles` | Copernicus DEM GLO-30 |
| `terrain.pmtiles` | AWS Terrain Tiles (USGS; INEGI) |
| `oblique-*.pmtiles` | INEGI streams, USGS NHD, US Census Bureau, Natural Earth, and Copernicus DEM GLO-30 |

## No passages of the novel

Notes and reasoning are our own words, and Spanish appears only as an incipit of at most five words (`docs/design.md`, section 3). `crossing.echo_check` checks the first rule. It compares every tracked text file, and `site/dist/` if it has been built, with the private text of the novel, and reports each run of 8 or more consecutive words that they share. Words are compared after folding case, accents, curly quotes and punctuation. Each report line gives the file, the line and only the first 8 words of the run. The check exits 1 on a match. The novel's text is not in the repo, so in CI the check skips with a message and exits 0. Run it locally from the repo root after a data change:

```bash
uv run --project pipeline python -m crossing.echo_check                # tracked files and site/dist/
uv run --project pipeline python -m crossing.echo_check data review    # only these paths
uv run --project pipeline python -m crossing.echo_check --words 7      # a shorter run
```

Place names and short stock phrases are shared with the novel by nature, so a match is a prompt to reword, not proof of copying. Binary files (the GeoParquet copies) are skipped; they hold the same text as the GeoJSON.
