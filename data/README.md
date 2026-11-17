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
| `areas.geojson` | 60 inferred areas and 2 named regions, each with its reasoning | `story-layer` |
| `vignettes.geojson` | 54 anchors for the map's drawings, each on the stop or place it stands for, with the `side` of the pin it is drawn on, the zoom it shows from, and its `journey` | `story-layer` |
| `landforms.geojson` | 313 label lines along ranges, valleys, plains, mesas and plateaus, for names set along the landform (decision 0023) | `story-layer` |
| `water_places.geojson` | 1,233 springs, tanks, ranches and stations within 20 km of the journeys ridden or walked, from GNIS and GeoNames, with the book's own 4 (they point at their place) | `story-layer` |
| `context_places.geojson` | 2,391 forts, ghost towns, mines, sawmills, churches, cemeteries, schools, old post offices, corrals, camps, ranches, named wells and windmills, dry lakes and flats within 20 km of the journeys, from GNIS (with its national file of 2021) and GeoNames; none dated (decision 0028) | `story-layer` |
| `mountain_glyphs.geojson` | 836 summits and 168 passes found in the Copernicus DEM, each with its landform | `story-layer` |
| `episodes.json` | The novel's 41 episodes: opening words, length, and a spoiler-safe summary | `episodes` |
| `translations.json` | 916 Spanish lines: an incipit of at most five words, this site's English, and where each was spoken. `common` marks 76 short replies and greetings ("Sí", "Gracias", "Buenas noches") that the panel leaves out of a place's lines; search still finds them | `translations` |
| `open-questions.json` | 22 judgement calls about where something is, each shown from its own episode | `open-questions` |
| `elsewhere.json` | 16 places the book names outside the story box, listed in the panel | `elsewhere` |
| `oblique/*.geojson` | The four story layers and the drawings' anchors as drawn in the Oblique view, each point moved north by its height (decisions 0018, 0019 and 0039). Use the flat files for analysis | `story-layer` |
| `oblique/archives.json` | The Oblique view's tile archives, in drawing order | `archives` |
| `parquet/*.parquet` | A GeoParquet 1.1 copy of each story layer, typed from the schema (decision 0009). CI checks they match the GeoJSON | |

Every feature carries `certainty`, `source`, `source_licence`, and `first_seen`.

## Licences and attribution

This site's own data, notes, and translations are CC BY 4.0 (`LICENSE`). Each feature's `source_licence` gives the terms of the dataset that fixed its coordinates. The same credits appear on the site's Credits page and, for tiles, in each archive's attribution.

| Source | Used for | Licence | Credit |
| --- | --- | --- | --- |
| This project | Notes, reasoning, translations, inferred areas, routes | CC BY 4.0 | "The Crossing reading map, Joe Burkinshaw" |
| GeoNames | Places, summits, passes, springs, ranches, and stations in Mexico | CC BY 4.0 | "GeoNames" |
| USGS GNIS | Places, summits, passes, and springs in the US | Public domain | Courtesy of the U.S. Geological Survey (GNIS) |
| Wikidata | A few place locations | CC0 | Courtesy link |
| GMBA Mountain Inventory v2 | The axes of US ranges in `landforms.geojson` | CC BY 4.0 | "GMBA Mountain Inventory v2 (Snethlage et al. 2022), GMBA and EarthEnv" |
| Copernicus DEM GLO-30 | Summits, passes, hachures, contours, and the Oblique view | Copernicus DEM licence | The notice below |
| CEC North American Land Cover 2020 (30 m) | The land cover in `landcover.pmtiles` and the Oblique view, its classes re-read with height (decision 0040) | CC BY 4.0 | The CEC citation below |
| AWS Terrain Tiles | The hillshade and the Tilted view | Public domain (USGS); INEGI free-use terms | "3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey. Source: INEGI, Continental relief, 2016." |
| INEGI Red Hidrográfica 1:50,000, edición 2.0 | Rivers, creeks, and lakes in Mexico; Mexican streams in the Oblique view | INEGI free-use terms | "Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0" |
| Global Dam Watch v1.0 (with GRanD v1.3) | The dam years in `pipeline/seeds/later_reservoirs.csv`, which leave reservoirs built after the book off the base map | CC BY 4.0 | "Global Dam Watch database v1.0 (Lehner et al. 2024)" |
| USGS NHD | US rivers and streams, and the rivers some routes follow | Public domain | "USGS National Hydrography Dataset courtesy of the U.S. Geological Survey" |
| US Census Bureau | County lines (cartographic boundaries, 2023) and the roads some routes follow (TIGER/Line) | Public domain | Courtesy of the U.S. Census Bureau |
| Natural Earth | Borders, states, roads, railways, lakes outside Mexico, and the choice and names of rivers | Public domain | "Made with Natural Earth" |

**Copernicus notice.** Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.

**CEC citation.** Commission for Environmental Cooperation (CEC). 2024. "North American Environmental Atlas - Land Cover 2020 30m". North American Land Change Monitoring System. Canada Centre for Remote Sensing (CCRS), U.S. Geological Survey (USGS), Comisión Nacional para el Conocimiento y Uso de la Biodiversidad (CONABIO), Comisión Nacional Forestal (CONAFOR), Instituto Nacional de Estadística y Geografía (INEGI). Ed. 2.0, Raster digital data [30-m]. Available at https://www.cec.org/north-american-environmental-atlas/land-cover-30m-2020/. The map's eight classes are this project's reading of it (decision 0034).

The tile archives are release assets, not files in this folder; their credits travel in each archive's metadata:

| Archive | Credit |
| --- | --- |
| `base.pmtiles` | INEGI (rivers, creeks, and lakes in Mexico), USGS NHD (US streams), US Census Bureau (county lines), Natural Earth |
| `relief-wheeler.pmtiles`, `relief-wheeler-12.pmtiles`, `contours.pmtiles` | Copernicus DEM GLO-30 |
| `terrain.pmtiles` | AWS Terrain Tiles (USGS; INEGI) |
| `oblique-*.pmtiles` | INEGI streams, USGS NHD, US Census Bureau, Natural Earth, Copernicus DEM GLO-30, and CEC land cover |
| `landcover.pmtiles` | CEC land cover |

## No passages of the novel

Notes and reasoning are this site's own words, and Spanish appears only as an incipit of at most five words (`docs/design.md`, section 3). `crossing.echo_check` checks the first rule. It compares every tracked text file, and `site/dist/` if it has been built, with the private text of the novel, and reports each run of 8 or more consecutive words that they share. Words are compared after folding case, accents, curly quotes and punctuation. Each report line gives the file, the line and only the first 8 words of the run. The check exits 1 on a match. The novel's text is not in the repo, so in CI the check skips with a message and exits 0. Run it locally from the repo root after a data change:

```bash
uv run --project pipeline python -m crossing.echo_check                # tracked files and site/dist/
uv run --project pipeline python -m crossing.echo_check data review    # only these paths
uv run --project pipeline python -m crossing.echo_check --words 7      # a shorter run
```

Place names and short stock phrases are shared with the novel by nature, so a match is a prompt to reword, not proof of copying. Binary files (the GeoParquet copies) are skipped; they hold the same text as the GeoJSON.
