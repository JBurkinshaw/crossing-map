# 0032. Traced legs, and how each line was drawn

Status: accepted (2026-11-16). Owner's request after comparing J2 leg 2 with J3 leg 14.
Phase: P1

## Context

A journey leg is drawn one of three ways: traced along a road or river the book names (`method: narrated-path`), computed as a least-cost path (`modeled`, decision 0021), or drawn as a curve (`schematic`). The three look different on the map: a traced leg follows every bend of today's road, a curve is smooth. The card said why a leg goes where it does, but not how its line was made, so a reader could not tell a traced road from a guess. The tracing itself had no decision record, could follow only one line (not a turn from one road onto another), and had no source for Mexico except Natural Earth's rivers. A review of every curve against the book found legs on named Mexican roads and rivers, and two stops placed against their own reasoning.

## Decision

- **What a leg is traced on.** `pipeline/seeds/snaps.csv` names, for a leg, the lines it follows and the dataset that holds them:
  - a TIGER/Line 2023 road (`FULLNAME`), a USGS NHD flowline (`gnis_name`) or a Natural Earth 1:10m river (`name`);
  - a road in INEGI's Red Nacional de Caminos (`name`), today's roads and tracks in Mexico;
  - a river in INEGI's 1:50,000 hydrography. INEGI's stream lines carry no names, so the snap gives the river's name as INEGI writes it and a lowest Strahler order (`min_order`): the leg follows the streams of that order and up, and the build fails unless one of INEGI's toponym points with that name lies within 300 m of the channel it runs on. INEGI labels a river every 10 to 30 km, so the check takes the whole connected channel within about 15 km of the stops, not the leg alone.
- **How it is traced.** `crossing.build_story` reads every line the snap names and treats them as one network: lines meet where they share a vertex, and a loose end is joined to the nearest point on a piece it is not yet connected to, if that lies within about 1 km (200 m for INEGI's streams), closest first. The leg is the shortest way along the network between the points on it nearest each stop, so it can turn from one named road onto another at a junction. Straight lines join it to the stops, and the leg is simplified (Douglas-Peucker, 5 m), well under a pixel at the map's closest zoom, which keeps the journeys file near its earlier size. If two pieces of a road lie apart, the piece closest to both stops together is used. A traced leg is `certainty: approximate`.
- **When a leg is traced.** Only when the book names or clearly points to the road, river, track or railway the rider follows on that leg, and the dataset holds it between the two stops. A modern road that happens to join two stops is not enough.
- **The legs added.** J3 legs 10, 11, 13, 14 and 15; J4 legs 10 (the Arroyo Agua Prieta, INEGI streams of order 4 and up), 11, 19, 38, 39 and 40; J5 legs 1, 4 and 5; J7 legs 25, 41 (the Río Casas Grandes, order 6 and up; it was modelled under decision 0021) and 53. J7 leg 42 stays modelled: its far stop lies on a side channel and the trace ran three times the straight distance.
- **Three stops placed on the road their reasoning names,** each computed by `pipeline/measure/road_points.py`: the J3 pass at the highest point of Geronimo Trail over the Guadalupe Mountains (its reasoning named the trail, but the pin stood 7.8 km south on the Cloverdale Creek road); the SK Bar nine road miles north of the Parham house along the Animas Valley road (it stood nine straight-line miles away, 5.6 km further north); and the J4 camp on Apache Pass Road where it climbs into the Dos Cabezas foothills, 12.4 km south of the Bowie stop (it stood on the range's gazetteer point, 14 km west of the road the book has them on).
- **How this line was drawn.** Every route segment carries a `drawn` text, written by the build and shown on its card under "How this line was drawn": for a traced leg, the lines' names and dataset, the shortest way between the nearest points, the joins to the stops, and any gaps closed; for a modelled leg, the speed, the grid, the costs and the smoothing; for a curve, that its shape is not evidence. The `reasoning` field keeps the why: what the book says.

## Alternatives

- **Appending the method to `reasoning`.** One field fewer, but it mixes what the book says with what the pipeline did, and the reasoning texts already differ in length and form.
- **Picking INEGI's rivers by geometry alone** (the highest-order line through both stops). No check that it is the river the book names; the toponym check costs little.
- **OpenStreetMap's river and road names.** ODbL, and the project keeps OSM out of its data (design section 3).
- **Period roads** (Army Map Service 1:250,000 sheets, USGS historical topographic maps) instead of today's. Better for the 1940s, left for later (roadmap, as in decision 0021).

## Consequences

A reader can see how each line was made and so how far to trust its shape. Today's roads and rivers stand in for the 1940s ones; where they have moved, the traced line is wrong by that much, and INEGI's paved Casas Grandes road is straighter than the old one. Adding a traced leg is a row in `snaps.csv` and a rebuild. Legs on roads that TIGER does not hold (other counties) or that INEGI does not name stay curves until a source is found; `private/review/snap-candidates.md` lists them.
