# 0048. Regions held by their crests

Status: accepted (2026-11-17). Amends how `crossing.regions` drafts the regions.
Phase: P1

## Context

`crossing.regions` drafted each region as the ground below a height (1,600 m for the Animas Valley, 2,200 m for La Babícora) connected to the region's pin, inside a rectangle. The owner saw that the Animas Valley ran north round the Peloncillos and back south into the San Simon Valley on their west side. It also ran east past the north end of the Animas Mountains, and La Babícora ran up two side valleys to its rectangle's north edge.

No height fixes this. The Animas Valley floor rises from 1,340 m at Animas town to 1,544 m at J1's stop, and the San Simon Valley lies at 1,360 m. A height that reaches the stop also takes in the San Simon side, round the low north end of the range. The region was also drawn on top of every inferred area inside it, so it took the clicks meant for them (J7's old Playas road among them).

## Decision

- **Each region has a clip ring placed by hand** in `crossing.regions`. The floor is the same rule as before, the ground below the height connected to the pin, but only inside the ring.
- **Each edge of the ring is a crest or a cut.** A crest edge follows the high ground between this basin and the next, traced on the Copernicus DEM as the highest ground in each 0.03° band of latitude. A cut is a deliberate limit: the border, the line at Animas town, and a line across low ground with no crest.
- **The script stops if the floor reaches a crest edge** along more than about 0.9 km (10 cells at 90 m). That means the crest is misplaced or the floor has found a way past it, the leak this decision is about. The fix is to move the edge onto higher ground, or to mark it a cut if the floor may end there, and say why in the code.
- **The Animas Valley** is held by the crests of the Peloncillos on the west and of the Animas Mountains on the east. North of 31.75° N the divide with the Playas Valley is a line of knobs of 1,500 to 1,660 m, no higher than the floor, so the ring follows them as a cut. The ring crosses the low ground north of the Peloncillos (about 1,430 m at 31.93° N) as a cut from their north tip to the line at Animas town.
- **La Babícora** is cut at 29.5° N, the basin's north rim, which leaves out the side valleys that run north. The sierras hold the floor on the other three sides.

## Alternatives

- **A lower height.** No height works, for the reason above.
- **USGS watershed boundaries (WBD).** Authoritative north of the border, but they need a download and do not cover Mexico, so La Babícora would still need another rule.
- **Drainage basins from the DEM.** The Animas Valley is a closed basin. Filling its pits routes it out over its lowest rim, which may be the same saddle the floor leaks through.

## Consequences

- The Animas Valley region now lies between its two ranges, from the border to Animas town. La Babícora keeps its basin and loses the two side valleys.
- The rule cannot hold a valley where no crest stands above the floor. There the ring is a cut, placed by judgement, and the code says so.
- Inferred areas inside a region still sit under it, so a click there still opens the region. That is a separate problem.
