# 0056. The head of a draw, and the gap through a range, for the she-wolf's journey

Status: accepted (2026-11-17, amended 2026-11-18); the Animas Mountains stop amended by 0078
Phase: P1

## Context

Five of J1's stops were on the gazetteer's point for a landform when the book places the wolf at one part of it:

- **Foster Draw (stop 8).** The book has the calf killed at the head of the draw, in the Peloncillos. The stop was on the draw's GNIS point, its mouth, on the Animas Valley floor.
- **Starvation Canyon (stop 10).** The book has her work west to the head of the canyon. The stop was on the canyon's mouth.
- **Between Clanton and Foster draws (stop 12).** The book has her in the high country between the draws. The stop was between their mouths, on the valley floor.
- **The San Luis Mountains (stop 5).** The book has her cross the range and go north through its gap. The stop was on the range's GNIS point.
- **The Animas Mountains (stop 6).** The book has her pass through the range on her way north. The stop was on the range's point, a peak by Animas Peak, 20 km north of San Luis Pass.

The open questions `q-starvation-canyon` and `q-clanton-foster` already named the doubt, but the stops stayed at the mouths.

GNIS records every linear feature (a valley, canyon, draw or stream) with two points: a primary point at its mouth and a source point at its head. The pipeline read only the primary point.

## Decision

- **"The head of" a draw or canyon is the GNIS source point.** Stop 8 is at the head of Foster Draw (GNIS 889164), 12.4 km west of its mouth and 216 m higher. Stop 10 is at the head of Starvation Canyon (GNIS 11797), 6.4 km south-east of its mouth. The calf's drawing moves with stop 8.
- **"The high country between" the two draws is on the drainage divide between them, near their heads.** The midpoint of the heads, adopted first, lies in a valley at the 42nd height percentile of the ground within 3 km, and the terrain check flagged it. The stop is the divide's high cell (ridge, spur, shoulder or peak) nearest the two GNIS heads: a ridge at 1,807 m, at the 87th percentile, 1.6 km from the midpoint. The divide comes from flow routing on the Copernicus DEM (`crossing.landform_points`). The outline cut between the mouths is dropped, and the area keeps its 3 km circle.
- **"Its gap" is San Luis Pass** (GNIS 894461), the named gap through the San Luis Mountains on her way north, 5.9 km north of the range's point. The leg from the pass to the Animas Mountains is now modelled (decision 0021) instead of a curve.
- **"Through the Animas range" is a saddle on its western ridge, halfway to the Animas Valley** (the owner's reading). From San Luis Pass she goes north along the valley east of the ridge, then west over the ridge to the Animas Valley stop. GNIS has no gap on that stretch, so the crossing is measured on the DEM: from the lowest point of the east-side valley on the parallel halfway between stops 5 and 7, the wolf's least-cost path to stop 7 crosses the ridge at a saddle at 2,020 m (31.49629 N, 108.77309 W), which the terrain check confirms. Both legs either side of it are modelled. `pipeline/measure/animas_crossing.py` gives the numbers, and `q-animas-crossing` records the reading. A plain least-cost path would cross sooner, over the low ridge just north of San Luis Pass, about 40 minutes quicker for her, but that is not how the owner reads the book.
- All five stops are `inferred`. `pipeline/measure/draw_heads.py` gives the distances and heights. A new open question, `q-san-luis-gap`, records the reading of the gap.

## Alternatives

- **The middle reach of each draw**, which the open question offered. The book says the head, and GNIS has the head.
- **Stop 6 on the range's point by Animas Peak.** It sits on a peak, and the book has her pass through the range.
- **A head found on the DEM** by tracing the channel upstream. GNIS's source point is the named feature's own head, recorded by USGS from its maps, so it comes first. A DEM method for features that have no source point (all of Mexico) is being tried separately.

## Consequences

- J1's legs into and out of these stops are redrawn. They are still curves, except the modelled legs from San Luis Pass to the Animas Valley.
- The Whitewater Creek trace (leg 4) now ends at the creek's nearest point to the pass and runs straight from there to the stop, as every traced leg joins its stops. That last straight stretch is drawn solid like the rest of the leg.
