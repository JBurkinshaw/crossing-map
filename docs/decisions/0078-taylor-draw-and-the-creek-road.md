# 0078. The head of Taylor Draw, and the end of the Cloverdale Creek road

Status: accepted (2026-11-20). Amends 0056 (the Animas Mountains stop) and 0069 (the Animas Valley stop).
Phase: P1

## Context

A check of the site's text against the book found two stops placed on a misreading.

- **The Animas Mountains.** Decision 0056 put the she-wolf's crossing of the range on a saddle on its western ridge, reached up its east side, because the book seemed to name no pass. But Billy's father gives her route: north up the range's western flank to where Taylor's Draw heads, then across the valley (1-01). The book names a feature, and GNIS has it.
- **The trap on Cloverdale Creek.** The stop stood 8 km up the creek road from Cloverdale. In 1-08 Billy rides up the road past an old dance platform and then two hours more before he leaves it for the vaqueros' fire. At a walk two hours is about 12 km, and the road in Census TIGER ends 9.6 km out.

The owner asked for both to be fixed by the methods already in use.

## Decision

- **The Animas Mountains stop is on the head of Taylor Draw**, as decision 0056 does for Foster Draw and Starvation Canyon: GNIS 896882 (Hidalgo County), source point 31.52114 N, 108.81146 W, at 1,677 m on the range's western flank, 5.7 km above the draw's mouth on the valley floor (`pipeline/measure/draw_heads.py`). Its terrain check is now `head`, against the draw's GNIS point. The stop is named "Animas Mountains, where Taylor's Draw heads".
- **The Animas Valley stop is re-measured** by decision 0069's rule, the lowest ground on the line from the new Animas stop to the head of Foster Draw: 31.50936 N, 108.86798 W, at 1,563 m, near the mouth of Taylor Draw, 2.1 km north of where it was (`pipeline/measure/animas_valley_floor.py`). The legs either side, modelled least-cost paths, are redrawn, and the drawing of the wolves running the antelope moves with the stop.
- **The trap stop is at the end of the creek road**, 9.6 km from Cloverdale along Co Rd C001 and Co Rd C106 (Census TIGER 2023, geodesic length on WGS 84): 31.44984 N, 109.01217 W (`pipeline/measure/cloverdale_creek_road.py`). The dance platform is taken as Cloverdale Park, a historic site that GNIS (933623) puts on Cloverdale's own point, so the ride is measured from the town. The road's end is as near to two hours' ride as the road comes. J1's last stop and J2's first share the point, and their area follows it.
- **The open question `q-animas-crossing`** now asks where she leaves the range. It shows the draw's head, and gives the old saddle and the range's own point as the other readings.

## Alternatives

- **Keep the saddle and note the book's route in the question.** The book names the draw, and the map's rule is to stand on a feature the book names.
- **Put the trap 12 km out, past the road's end.** The book has Billy leave the road for the fire, so the fire is off a road, and the road the map can show ends at 9.6 km. A 1940s track may have run further, but nothing shows it.

## Consequences

J1's route now runs up the Animas range's western flank, not its east side, which is the route the book gives. `pipeline/measure/animas_crossing.py` measured the old saddle and is kept as the record of decision 0056's first answer. The trap site moves 1.5 km up the creek (1.6 km further along the road), and the drawings near it took new sides and zooms.
