# 0018. Raised over the first two journeys, with the story raised

Status: accepted (2026-11-12). Extends 0017.
Phase: P1

## Context

Decision 0017 made Raised a preview of two 40 km test tiles around the Pilares. It hid the stops, areas and most base layers, because they could not move with the terrain. A reader could not follow a journey in Raised.

## Decision

- **Area.** `crossing.plan_oblique` builds every fine hachure tile in the corridor of J1 and J2 (20 tiles, about 160 by 240 km). The journeys are named in the code, so later journeys in `data/journeys.geojson` do not grow the area. The whole area uses one lowest height (463 m), so the tiles meet.
- **Strips.** The horizon is a running maximum along each north-south column. So the build runs one strip per column of tiles, in parallel. Each strip has its own smoothed DEM (`hachures.prepare_dem`). The DEM reaches 600 m past the strip to the east, west and north, and 6 km to the south, so that ground just outside the area can hide ground inside it. Strokes come from the cached fine tiles, and each tile keeps only the strokes on its own core. The rules for strokes, crests and ridgelines do not change.
- **Base layers.** These are shifted and hidden like the relief: the international, state and county lines, roads and railroads from the sources `tiles/build_base.py` uses, and the Mexico side as a polygon. Streams come from INEGI (order 3 and up) in Mexico and from USGS NHD in the US, each clipped to its own side of the border. NHD has no stream order here, so NHD's display scale stands in for it: lines shown at 1:500,000 or smaller, plus every named stream. The raised layers copy the classic layers' style, and Raised hides the flat versions.
- **Story layers.** The pipeline writes shifted copies of the stops, places, areas and journeys (J1 and J2) to `data/raised/`. Lines and area edges are sampled every 60 m, then shifted. Ground that is hidden is not cut from them. In Raised the app draws the story from these copies, so markers, popups and stepping between stops use the raised positions. Towns come from the places layer, so they are raised with it.
- The fly-in goes to the corridor only when the view is outside it, or closes in where the view is when it is below zoom 11.

## Alternatives

- **One DEM for the whole area**: simpler, but over 40 million cells for each grid that the build holds. Strips use less memory and run in parallel.
- **A lowest height per tile**: the tiles would not meet.
- **Raising J3 to J7 now**: their DEMs and hachures are not all ready. The corridor grows when they are.
- **Hiding the story lines behind ridges**: this is true to the view, but a journey would break into pieces. The story should read first.

## Consequences

- `oblique.pmtiles` is 36 MB (zoom 9 to 12). The build takes about 80 s. Strokes with `Rand` 7 to 9 are tiled only at zoom 12, because the style draws them only from 12.
- `data/raised/` is generated. It must be rebuilt when the story layers change, and it adds about 0.7 MB, loaded only in Raised.
- Outside the corridor, Raised still shows bare paper. The story layers outside the corridor are shifted with unsmoothed Copernicus heights.
- The attribution adds courtesy credits for USGS NHD and the US Census Bureau.
