# 0001. Story data as plain GeoJSON

Status: accepted (2026-11-11)
Phase: P1

## Context

The story data (places, routes, areas, stops, conversations, vignettes) is under 1 MB in total and the app always loads all of it. The Cloud-Optimized Geospatial Formats Guide frames cloud-optimized formats around partial reads of data too big to download, which does not apply here.

## Decision

One GeoJSON file per layer (WGS 84, RFC 7946) in `data/`, validated against `data/schema/story-layer.schema.json` in CI. Coordinates are rounded to 5 decimals.

## Alternatives

- FlatGeobuf or GeoParquet as the app format: built for partial reads of large data. No gain at this size, and an extra decoder in the bundle.
- Vector tiles for story data: lose easy filtering, editing, and diffs.

## Consequences

Files are readable, diff in git, preview on GitHub, and open in every GIS. MapLibre reads them natively. If the data grows past a few MB, revisit.
