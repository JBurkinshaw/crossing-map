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

Two formats, generated from one source. They can still drift if a layer changes and the copy is not rewritten: on 2026-11-17 three commits changed `stops`, `areas`, `journeys` and `vignettes` without it, and CI's `crossing.downloads --check` blocked every deploy until the copies were rewritten. So `crossing.build_story` and `crossing.build_vignettes`, which write those layers, now write each layer's copy with it. The other steps that write a layer still need `crossing.downloads` run after them, and the CI check still catches a copy left behind.
