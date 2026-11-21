# 0069. J1's Animas Valley stop on her way across the valley

Status: accepted (2026-11-19); the stop re-measured from the head of Taylor Draw by 0078
Phase: P1

## Context

The she-wolf's Animas Valley stop (`j1-animas-valley`) stood at 31.6 N, 108.88 W. Decision 0056 moved the stops either side of it: the Animas Mountains crossing to 31.50 N and the head of Foster Draw to 31.48 N. The valley stop did not follow, so her way ran about 11 km north to the valley and back south to Foster Draw. In the review of decision 0068 the owner asked why the stop was so far north, as the wolf seemed to go out of her way.

## Decision

- **The stop is the lowest ground on the line between its neighbours,** the Animas Mountains crossing and the head of Foster Draw: 31.49074 N, 108.86368 W, at 1,578 m, 8.6 km west of the crossing (`pipeline/measure/animas_valley_floor.py`, Copernicus GLO-30, sampled every 100 m on the WGS 84 geodesic). It passes the terrain check for a valley floor.
- **The Animas Mountains crossing stays where the owner accepted it.** It was measured as the saddle on the wolf's least-cost path towards the old valley stop (decision 0056). Measured towards the new one, it would move 2.8 km south to 31.47 N. `pipeline/measure/animas_crossing.py` keeps its old target, so it still gives the published crossing.
- **The drawing of the wolves running the antelope moves with the stop,** closer to the Parham house the book sets it by.

## Alternatives

- **Re-measure the crossing towards the new stop.** That moves a stop the owner had just accepted, and the valley point would then move again, as it depends on the crossing.
- **Keep the stop and say why in an open question.** Nothing in the book puts the wolf that far north.

## Consequences

- J1's leg from the crossing to the valley, a modelled least-cost path, is shorter and runs west, not north-west. The curve on to Foster Draw is short.
- The open question `q-animas-crossing` says the crossing is "about halfway to the Animas Valley", which still reads correctly as halfway along the range.
