# 0068. The owner's review of the landform positions

Status: accepted (2026-11-19)
Phase: P1

## Context

Decision 0059 had the owner review, on the dev server (`?review=positions`), every stop whose ground the terrain check flagged, and left four named passes to that review. On 2026-11-19 the owner went through all 23 stops with a position and saved a verdict for each in `review/positions/review.csv`: 16 accepted, 4 moved to a candidate and 3 marked as needing work.

## Decision

- **Guadalupe Pass for J2's low pass** (`j2-guadalupe-pass`). The stop moves 3.3 km south-west from the range's east flank to Guadalupe Pass (GNIS 889650), the gazetteer candidate. The book puts its pass at the range's eastern end and names none. Guadalupe Pass is at the south-eastern end, the nearest named pass. The check still flags it ("slope, not saddle"), and the owner accepted it with that flag.
- **Whitmire Pass for the old Playas road** (`j7-playas-road`). The stop moves 6.7 km south to Whitmire Pass (GNIS 896568), the gazetteer candidate. A ranch road in Census TIGER 2023 runs within 20 m of the GNIS point. The check flags the point ("ridge or spur, not saddle"), as gazetteers often set a pass's point beside its col. The area keeps its rule (ground above 1,450 m within 2 km of TIGER roads), redrawn around the new point by `crossing.area_drafts`.
- **The Little Hatchets' lower slopes** (`j7-little-hatchets`). The stop had no point of its own and stood on the range's gazetteer point, its summit. It moves 1.6 km south-east to the DEM candidate, the nearest ground that reads as the lower slopes. This DEM point is published only because the owner chose it (decision 0059). Its height percentile is 71, one above the check's 10 to 70.
- **The plains camp** (`j4-plains-camp`). The stop moves 10 m to the DEM candidate on the valley floor. The move changes nothing a reader can see.
- **No other stop moves.** The 3 needing work stay where they are until the owner decides: `j1-animas-valley` (the stop lies about 11 km north of the stops either side of it), `j3-guadalupe-pass` (whether the old Cloverdale road is the Cloverdale Creek road, Co Rd C001, rather than Geronimo Trail) and `j4-dos-cabezas` (which county road the camp is on).
- **A move verdict is recorded as accepted at the new point**, with a note naming the candidate, so the verdict stays current for `crossing.validate`.

## Alternatives

- **Keep J2's pass at the eastern end, as the book reads.** There is no named pass there and no saddle the check finds. The owner preferred a named place.
- **The DEM saddle for the Playas road** (14 km from the stop). It is a review aid only, and further from the lake the book sets out from.

## Consequences

- Six stops are flagged after the moves, and each has a current verdict. The Playas road and the Little Hatchets stay flagged because the check's rules do not fit them, not because they are wrong.
- The legs into and out of the moved stops are redrawn as curves to the new points.
