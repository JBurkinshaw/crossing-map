# Experiment: placing a stop at the right part of a landform

Status: **adopted on 18 November 2026** (decision 0059): the gazetteer tier, the hybrid divide and the check, with the check's window scaled to the landform. They now run for every stop with a position as `crossing.positions`, and the DEM-only tiers are review aids. This folder keeps the J1 trial and the calibration.

The book often puts a stop at one part of a landform: the head of a draw, the gap through a range, the high country between two draws, a valley floor. A gazetteer's point for that landform is somewhere else, usually a stream's mouth or a range's middle. The owner found four J1 stops placed on the gazetteer point instead (decision 0056). This experiment asks whether a fixed, reproducible process could have found the right points, and whether a terrain check could have caught the wrong ones.

## In short

- **The gazetteer tier answers most cases, and answers them exactly.** GNIS records every valley, canyon and stream with a source point at its head as well as its mouth, and gaps as their own features. It gave the head for both J1 draws and San Luis Pass for the gap. The pipeline had the data all along and read only the first coordinate.
- **NHD names none of J1's draws,** so the vector tier returned nothing for them. It does work where NHD carries the name: for Whitewater Creek its head is 0.45 km from GNIS's.
- **DEM-only heads are unreliable.** Over 159 GNIS valleys, streams and arroyos around J1, tracing the main stem up from the mouth landed a median 3.5 km from GNIS's head, and within 1 km only 22 % of the time. Almost all of the error is the trace climbing the wrong valley. Where it climbs the same valley as GNIS (39 of 159), 82 % land within 1 km, with a median of 0.39 km. The weak step is the choice of branch, and the mouth's snap on a flat valley floor, not the channel-head threshold.
- **DEM-only gaps are unreliable too.** For the San Luis Mountains the saddle search found a col 5.4 km from San Luis Pass, on a slope.
- **A hybrid works where a pure method does not.** For "the high country between Clanton and Foster draws", the DEM divide between the two catchments, aimed at GNIS's two heads, lands on a ridge at the 87th height percentile. The point now published (the midpoint of the two heads) sits in a valley at the 42nd percentile, and the checker flags it.
- **The terrain check (option C) caught every known mistake.** It flagged all four original placements (a flat at the 13th percentile for Foster Draw's mouth, a peak for the San Luis Mountains, and so on) and passed three of the four fixes. It flagged the fourth fix, stop 12, rightly. It raised two flags that need a person: the Animas Mountains stop sits on a peak while the book has her pass through the range, and the Animas Valley stop is a false alarm, because a 3 km window is too small for a 15 km wide valley.

My recommendation: adopt the gazetteer tier and the check now, and the hybrid "between". Keep the DEM tiers as a fallback that is always shown for review, never published on their own, until the branch choice is fixed (follow the channel nearest the named valley's line or toponym, not the largest catchment).

## J1, stop by stop

Distances are to the stop as now published. "Ground" is the geomorphon at 500 m and 2 km lookouts and the height percentile within 3 km.

| Stop | Position | Original | Gazetteer | NHD | DEM | Check on original | Check on published |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 San Luis Mountains | pass | 5.9 km | San Luis Pass, 0 km | none | 5.4 km, slope | flag: peak | ok: saddle |
| 6 Animas Mountains | pass | 0 km | no gap within 15 km | none | 9.7 km, ridge with a saddle | flag: peak | flag: peak (unchanged stop) |
| 7 Animas Valley | floor | 0 km | | | | flag: spur, pct 48 (window too small) | same |
| 8 Foster Draw | head | 12.4 km | GNIS head, 0 km | none | 6.2 km, wrong branch | flag: flat, pct 13 | ok |
| 10 Starvation Canyon | head | 6.4 km | GNIS head, 0 km | none | 0.35 km | flag: pct 35 | ok |
| 12 Clanton and Foster | between | 14.1 km | midpoint of heads, 0 km | none | 8.7 km (inherits stop 8's branch) | flag: valley, pct 9 | flag: valley, pct 42 |
| 12, hybrid | between | | | | DEM divide aimed at GNIS heads: 1.6 km, ridge, pct 87 | | ok |
| 2 Bavispe crossing | floor | 0 km | | | | ok | ok |

`img/` has a hillshade map of each stop with every candidate, and `calibration.png`.

## The tiers

1. **Gazetteer.** GNIS's source point for a head, its primary point for a mouth, and the GNIS gap (class Gap) within 15 km of the range nearest the straight way from the stop before to the stop after. For "between", the midpoint of the two heads.
2. **Vector.** NHD flowlines named as the feature: the upstream end of the named network that lies farthest from the mouth.
3. **DEM.** Copernicus GLO-30 on a local transverse Mercator grid (WGS 84), 60 m cells. Priority-flood fill (Barnes et al. 2014), D8 directions (O'Callaghan and Mark 1984), flow accumulation. A head is where the main stem, followed up from the mouth into the largest upstream catchment, drops below 0.1 km² of catchment (Montgomery and Dietrich 1988). Within the right valley, 0.02 to 0.5 km² gave medians of 0.4 to 0.6 km, and 2 km² stops too early. "Between" is the divide between the two catchments, on a ridge, spur, shoulder or peak cell nearest the midpoint of the heads. A gap is the saddle cell in the lower half of the range's ground that adds least to the way from the stop before to the stop after.

The check classifies the point with geomorphons (Jasiewicz and Stepinski 2013, the GRASS `r.geomorphon` lookup table, a 1° flat threshold), adds a saddle test and the height percentile, and compares the result with what the position expects (`EXPECT` in the module).

## Before rollout

- Add a `position` column to `pipeline/seeds/stops.csv` (head, mouth, between, pass, crest, floor, slopes-east and so on) and fill it for every stop whose text names a part of a landform: about 57 of 171 stops match a first search.
- Scale the check's window to the landform: a valley floor needs a window as wide as the valley.
- Fix the DEM branch choice before trusting tier 3 in Mexico, where GNIS has no heads. INEGI's toponym points name streams, and its 1:50,000 network has Strahler order, which gives a named channel to follow.
- Run the check in `crossing.validate` as a report, not a failure, so a flagged stop is reviewed rather than blocking a build.

## Files

- `pipeline/src/crossing/landform_points.py`: the tiers, the check and the calibration. Run: `uv run --project pipeline python -m crossing.landform_points` (about 15 minutes with the calibration, 2 minutes with `--skip-calibration`). It reads only local caches.
- `pipeline/src/crossing/landform_points_images.py`: the figures. Run: `uv run --project pipeline --with matplotlib python -m crossing.landform_points_images`.
- Outputs here: `results.csv` (J1), `calibration.csv` (159 GNIS features, the error at each channel-head area, and how far GNIS's head lies from the traced stem), `points.geojson` (every candidate, the traced stems, the divide and the least-cost paths), `img/` (not in git).
