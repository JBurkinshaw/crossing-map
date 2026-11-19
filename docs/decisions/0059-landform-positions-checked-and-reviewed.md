# 0059. Where a stop sits on its landform: named points first, a terrain check, and the owner's review

Status: accepted (2026-11-18)
Phase: P1

## Context

The book often puts a stop at one part of a landform: the head of a draw, a pass through a range, the high country between two draws, a valley floor, the rim of an escarpment. A gazetteer's point for the landform is usually somewhere else, such as a stream's mouth or a range's middle. Five of J1's stops were placed on such a point (decision 0056). An experiment (`review/experiments/landform-points/`) tried three ways to find the right part, and a check of the ground at each stop:

- **Gazetteer.** GNIS gives every valley, canyon and stream a source point at its head as well as its mouth, and records gaps as features. It answered every J1 case exactly.
- **Vector.** NHD names none of J1's draws.
- **DEM.** Tracing a stream up from its mouth climbed the wrong branch three times in four, over 159 GNIS features (median error 3.5 km). Within the right valley it was accurate (82 % within 1 km).
- **Check.** Geomorphons (Jasiewicz and Stepinski 2013) at two lookouts, a saddle test and the height percentile flagged every known mistake in J1.

## Decision

- **Each stop whose text names a part of a landform has a position** in `pipeline/seeds/stop-positions.csv`: head, mouth, between, pass, floor, foot, rim, high or slopes, with the GNIS feature or range it refers to. 23 stops have one. The other 148 stops are towns, ranches, roads and crossings, or name a landform only in passing.
- **`crossing.positions` gives candidates by tier and checks each one.** These two tiers are trusted:
  - **Gazetteer.** GNIS's source point for a head and its primary point for a mouth. For a pass, the GNIS gap or GeoNames pass, gap or saddle (codes PASS, GAP and SDL) within 15 km that adds least to the way from the stop before to the stop after.
  - **Gazetteer and DEM together.** For "between" two draws, the drainage divide between their catchments at its high cell nearest the two GNIS heads.
- **NHD and DEM-only candidates are review aids.** They are shown in the review, labelled as aids, and never published on their own. A DEM-only point can become a stop only through the owner's verdict, with the stop's reasoning and a decision citing it.
- **The check's window grows with the landform.** It is 3 km for a head, mouth, pass or "between", 5 km for a foot, rim, high point or slopes, and 8 km for a valley floor. A valley floor also passes when the ground within 500 m slopes 3 degrees or less, because geomorphons read a wide, gently sloping floor as a spur. A pass also passes when a saddle lies within 300 m of its point, because gazetteers often set a gap's point beside the col (Apache Pass's GNIS point is 42 m off).
- **The owner reviews flagged stops on the dev server** (`?review=positions`), which shows each stop's published point, its candidates and the check. The verdicts are accept, move to a candidate, or needs work, with a note. They are saved to `review/positions/review.csv` with the point they were given for, so a verdict goes stale when the stop moves. `crossing.validate` lists flagged stops without a current verdict as a note, and never fails a build on one.
- **Nothing moves a stop automatically.** A stop moves only when its row in `stops.csv` is edited, with reasoning.

## Alternatives

- **A `position` column in `stops.csv`.** That would touch every row of a file other work edits at the same time. A separate seed keeps the positions in one place.
- **Publishing the DEM tiers where the gazetteer has nothing,** which is all of Mexico for heads. The calibration says they would be wrong three times in four.
- **Failing the build on a flagged stop.** Some flags are the check's limits, not mistakes (a plain whose stop sits on a bajada), and a person settles them in seconds with the map in front of them.

## Consequences

- Of the 23 stops, 18 pass the check and 5 are flagged for review: `j2-guadalupe-pass`, `j2-pilares-de-teras`, `j3-bavispe-promontory`, `j7-little-hatchets` and `j7-animas-plain`. The two rims passed once moved inside their areas (below). No other stop outside J1 moved in this change.
- The gazetteer offers a named pass for four stops whose points are not on it: Guadalupe Pass (GNIS 889650) for `j2-guadalupe-pass`, 3.3 km away, Puerto Pitaycachi for `j2-sierra-de-la-cabellera`, Puerto el Aire for `j3-wolfs-grave`, and Whitmire Pass (GNIS 896568) for `j7-playas-road`. Only Guadalupe Pass is named for its range, and the book puts J2's pass at the range's eastern end, while Guadalupe Pass is at its southern end. They wait for the owner's review.
- **A stop's point must lie inside its own area**, because the area is the stop and the point is the best guess within it. Four did not: `j3-eastern-escarpment` (2.0 km outside), `j4-escarpment-rim` (5.0 km), `j4-river-camps` (0.8 km) and `j4-wagon-road-crossing` (3.4 km). Each moved to the nearest ground at least 200 m inside its area, and for the two rims, the nearest that also passes the rim check (`pipeline/measure/points_in_areas.py`). Their areas were redrawn around the new points by the same rules. `crossing.validate` now fails a stop whose point lies outside its area.
- Run `crossing.positions` after a stop moves. `crossing.validate` says when its results are stale.
