# 0015. A vendored hachure generator with absolute settings, run in tiles

Status: accepted (2026-11-11)
Phase: P1

## Context

Decision 0014 picks hachures for the map, so the production run needs Huffman's script beyond the three test areas (plan section 5.2, "D-relief-hachures"). Run unmodified (decision 0013), the script sets two values from the extent it is given. The slope limits are percentages of the lowest and highest slope in the DEM, and the contour interval is the DEM's elevation range divided by `spacing_checks`. The same settings therefore mean different slopes in different places, and tiles would not match at their seams. The script's spacing step also tests each contour against every hachure, so its run time grows faster than the area.

## Decision

- `pipeline/relief/hachures/hachure_generator.py` is a lightly adapted copy of the script at upstream commit `3170a3f`, kept under GPL-3.0 with its licence in that folder. It takes absolute slope limits in degrees and an absolute contour interval in metres, reads its settings from the harness, seeds its one shuffle, and calls the QGIS 4 algorithm names. The folder's README lists every change.
- `pipeline/relief/run_hachures.py` (MIT) runs it headless, as in decision 0013.
- `crossing.hachures` runs it on a fixed UTM 12N tile grid with overlapping margins, and clips each tile's lines to its core:
  - fine: 30 m DEM, 40 km tiles, inside a corridor 20 km either side of the journeys, slopes 10–40°.
  - coarse: 90 m DEM, 60 km tiles, wherever the Copernicus tiles cover, slopes 5–38°. Tiles of 120 km ran for over 30 minutes each over the Sierra Madre, because the spacing step grows faster than the area.
  - both: spacing 3–8 cells and contours every 10 m. These are the experiment's settings, converted to absolute values from the test areas' slope ranges.
- `tiles/build_relief.py` packs the clipped lines into `relief.pmtiles`, published as a release asset like the other tiles. Inside the corridor, coarse lines stop at zoom 9 and fine ones start at 10. Outside it, the coarse lines carry on to the last zoom.

## Alternatives

- One run over the whole region: no seams, but the run time grows faster than the area, and the region would be one very large DEM.
- Tiles with the unmodified script: each tile would get its own slope limits, and the density of hachures would jump at the seams.
- Writing our own generator: more control, but Huffman's method is the one the experiment chose.

## Consequences

Tiles match at their seams except where a line crosses one: there it is cut, and the neighbour's lines start on their own spacing. With the soft style this is hard to see. The fixed grid means a wider corridor, for Parts II–IV, adds tiles without redoing the existing ones. The run needs a local QGIS 4 install (`QGIS_ENV`). The GPL copy and the MIT code meet only inside one process run.
