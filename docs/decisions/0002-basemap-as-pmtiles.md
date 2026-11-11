# 0002. Literary basemap as PMTiles

Status: accepted (2026-11-11)
Phase: P1

## Context

The literary basemap draws borders, rivers, labels, and relief from Natural Earth, US Census TIGER, INEGI, and elevation data. As raw GeoJSON these are megabytes, with no level of detail.

## Decision

Build vector tiles with tippecanoe into PMTiles archives: one static file per archive, read by HTTP range requests through the `pmtiles` protocol in MapLibre. A hillshade, if one is used, is a separate raster PMTiles archive (WebP).

## Alternatives

- A tile server: needs hosting and upkeep.
- Raw GeoJSON for base layers: too large, no generalisation by zoom.

## Consequences

No server. The host must support range requests; stage 0 tests that against the live site with a small archive (`tiles-v0`) before anything depends on it.
