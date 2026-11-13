# Data

Open data for the reading map: GeoJSON (WGS 84, RFC 7946) for story layers, JSON for episodes and translations, and JSON Schemas in `schema/`.

Each layer has a row below with its source and licence.

| File | Contents | Licence |
| --- | --- | --- |
| `places.geojson`, `stops.geojson`, `areas.geojson`, `journeys.geojson` | Part I places, stops, inferred areas and route segments, plus context towns | Our own work CC BY 4.0; each feature's `source_licence` gives its source's terms (GNIS public domain, GeoNames CC BY 4.0, Wikidata CC0, USGS NHD public domain) |
| `raised/*.geojson` | The same story layers as drawn in the map's Raised view: every point moved north by twice its height above the lowest ground of the first two journeys' corridor (decision 0018), and only J1 and J2 in `raised/journeys.geojson`. Built by `crossing.plan_oblique`; use the files above for analysis | As the files above; heights from Copernicus DEM GLO-30 (notice below) |
| `episodes.json` | The novel's 41 episodes: opening words and length | CC BY 4.0 |
| `mountain_glyphs.geojson` | 275 summits with at least 300 m prominence, plus the book's named summits, found in Copernicus GLO-30; names from GNIS and GeoNames | Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved |

Every feature carries `certainty`, `source`, `source_licence`, and `first_seen`. See `docs/plan.md`, section 6, for the property schema.
