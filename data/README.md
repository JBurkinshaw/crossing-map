# Data

Open data for the reading map: GeoJSON (WGS 84, RFC 7946) for story layers, JSON for episodes and translations, and JSON Schemas in `schema/`.

Each layer has a row below with its source and licence.

| File | Contents | Licence |
| --- | --- | --- |
| `places.geojson`, `stops.geojson`, `areas.geojson`, `journeys.geojson` | Part I places, stops, inferred areas and route segments, plus context towns | Our own work CC BY 4.0; each feature's `source_licence` gives its source's terms (GNIS public domain, GeoNames CC BY 4.0, Wikidata CC0, USGS NHD public domain) |
| `episodes.json` | The novel's 41 episodes: opening words and length | CC BY 4.0 |
| `mountain_glyphs.geojson` | 767 summits with at least 200 m prominence, plus named mesas, buttes and cones from 100 m, unnamed mesas the DEM shows clearly, and the book's named summits, found in Copernicus GLO-30; 168 passes: GNIS gaps and GeoNames passes that lie on a key col, and the key cols of the most prominent summits; names from GNIS and GeoNames | Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved |

Every feature carries `certainty`, `source`, `source_licence`, and `first_seen`. See `docs/plan.md`, section 6, for the property schema.
