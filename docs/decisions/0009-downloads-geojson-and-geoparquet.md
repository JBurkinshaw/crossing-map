# 0009. Downloads as GeoJSON and GeoParquet

Status: accepted (2026-11-11)
Phase: P1

## Context

The data is meant for reuse by readers, students, and analysts.

## Decision

The published GeoJSON is the download. Each layer also gets a GeoParquet copy (written with pyarrow by `crossing.downloads`, one file per layer, typed from the JSON Schema) for DuckDB, GeoPandas, and QGIS users.

## Alternatives

- FlatGeobuf: duplicate effort for the same audience.
- A STAC catalogue: suited to collections of thousands of files; we have about ten.

## Consequences

Two formats, generated from one source, so they cannot drift.
