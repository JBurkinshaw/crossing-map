# 0066. Vignettes along a leg

Status: accepted (2026-11-18). Amends 0026.
Phase: P1

## Context

Decision 0026 anchors every drawing to a stop or place (the seed's `ref`). Many of the book's scenes happen between stops: a rider seen across a playa, a hailstorm on a road, a wedding cart on the way into a town. Fourteen of the 54 drawings already stood on a route line, but each did it by hand: the seed gave its own `lon` and `lat`, worked out somewhere else, and pointed its `ref` at the nearer stop of the leg. Nothing kept the point on the line when the line moved, and nothing dated the drawing by its leg. The owner adopted 14 journey vignettes on 2026-11-18, each on a named leg.

## Decision

- **A seed row may name a leg instead of a stop or place.** `pipeline/seeds/vignettes.csv` has two more columns: `leg`, a `route-segment` id in `data/journeys.geojson`, and `along`, a fraction from 0 to 1. A row gives either a `ref` or a `leg`, never both. `crossing.build_vignettes` stops on a row with both, neither, or a leg that is not a route segment.
- **The point is interpolated along the leg's line by length.** The length of each part of the line is the geodesic distance on the WGS 84 ellipsoid (pyproj `Geod`). The build finds the part where `along` times the leg's whole length falls, and moves that far along the part's geodesic from its start. The coordinates are the leg's, as published in `data/journeys.geojson`. Each drawing's `reasoning` says which leg and how far along.
- **The rest is 0026's.** The drawing takes its side and first zoom by the same script, clear of the stops, route lines and other drawings, with the same one-step cap. Its `place_ref` is the leg's id and its `journey` the leg's journey.
- **A drawing is never shown before its leg.** Its `first_seen` is the later of its scene's episode and the leg's, as for a pin. `crossing.validate` accepts a route segment as a vignette's `place_ref` and fails if the drawing shows before the leg does.
- **The key's wording holds.** The point stands for roughly where on the journey the scene happens, so the drawing is still set just beside its place and not on it, its position approximate.

## Alternatives

- **Keep giving `lon` and `lat` by hand.** It works, but the point drifts off the line when a leg is redrawn, and the drawing could show before its leg.
- **A fraction by vertex count, or by planar length in degrees.** Simpler, but a leg's vertices are not evenly spaced (the modelled legs have many, the schematic ones few), and a degree of longitude is shorter than a degree of latitude here.
- **A new stop for each scene.** A stop is a place the reader travels through, with a card and an area. These scenes are moments on the way, and the stops would crowd the journey.

## Consequences

The 14 older drawings with their own points on a route line keep them: moving them to `leg` and `along` would change nothing a reader sees. A drawing on a leg moves with the line when the leg is redrawn, and its side and zoom may change with it, as 0026 already says of drawings beside a stop.

With the 14 journey drawings and three of design section 10's first candidates added, `pipeline/measure/vignette_clashes.py` gives, at each drawing's own first zoom:

| | Before (54 drawings) | After (71 drawings) |
| --- | --- | --- |
| Drawings that clash (a stop, or more than their width of route line) | 25 | 32 |
| Drawings on a stop marker | 11 | 12 |
| Stop markers covered | 22 | 27 |
| Route line covered | 4,681 px | 6,260 px |
| Pairs of drawings on each other | 0 | 0 |

At zoom 10, 52 drawings showed before and 65 after: they cover 12 and 15 stop markers and 4,618 and 6,126 px of route line, and 22 and 26 clash. Of the 17 new drawings, seven clash at their first zoom, one of them on stop markers (the Model A, beside the bootheel's crowded Cloverdale Creek stops). The red plane, placed after the new drawings of higher priority, moves from the south-west side of its pin to the east.
