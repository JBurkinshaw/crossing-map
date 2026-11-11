# 0007. Python pipeline with uv

Status: accepted (2026-11-11)
Phase: P1

## Context

The data comes from gazetteers, elevation models, and the author's private copy of the novel. The steps must rerun reproducibly, and the book text must never leave the author's machine.

## Decision

A Python 3.12 package in `pipeline/`, managed by uv (which installs Python itself), using GDAL, geopandas, shapely, rasterio, pyproj, and tippecanoe. It writes only GeoJSON, review CSVs, and logs to the repo. `private/` is git-ignored, and CI fails if any file under it is tracked.

Measurements (distances, areas, bearings) are computed by scripts in `pipeline/measure/` with open-source tools, stating the ellipsoid or projection and the source of every coordinate.

## Alternatives

- Notebooks as the pipeline: hard to rerun.
- Cloud processing: nothing is big enough to need it.

## Consequences

Anyone can rerun the public steps. Steps that read the book run only on the author's machine.
