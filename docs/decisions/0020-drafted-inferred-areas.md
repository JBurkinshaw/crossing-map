# 0020. Inferred areas drafted by rule from the stop's circle

Status: accepted (2026-11-14). Amends 0008.
Phase: P1

## Context

Decision 0008 has each inferred area drawn by hand in QGIS. Until that is done, every area is a geodesic circle of the stop's `radius_km`, which takes in hills for a river crossing and open plain for a roadside camp. An experiment (`review/experiments/areas/`) cut each circle to the ground its reasoning describes, and the owner adopted it on 14 November 2026.

## Decision

- **The rule.** `crossing.area_drafts` cuts each stop's circle with one short rule per stop, written out in plain words: a river corridor, a valley floor or playa from the Copernicus DEM, a road's verge from Census TIGER, the side of a line, a viewshed. The circle stays the upper bound: no draft grows beyond it. If a rule leaves almost nothing, or the evidence gives nothing to cut by, the circle stays.
- **A seed, not a hand copy.** The drafts are written to `pipeline/seeds/areas.geojson`, which `crossing.build_story` reads in place of the circle. The script refuses to overwrite the seed without `--force`, and with it keeps every area marked `checked` in the QGIS project (`pipeline/qgis/areas.qgs`), so hand edits survive a rerun. `build_story` stops if a draft reaches outside its stop's circle, which means a pin or radius changed after drafting.
- **Pins.** Where a medium- or high-confidence draft follows the evidence better than the pin (nine stops, among them Huisiachepic and San Simon), the pin moves to the point of the draft nearest its old place, and the draft is made again around it. The four low-confidence drafts that miss their pins keep the pin.
- **Old Mexican roads.** No open map of the 1940s roads of Chihuahua and Sonora is to hand, so in nine areas a straight line between the book's towns stands in for the road. The card says so.
- **Honesty on the card.** Each area's card says it is a draft made by a rule from data, not drawn from a source, gives the rule, and invites a correction through the existing issue link. Confidence is not shown.
- **La Babícora** keeps the DEM basin outline from `crossing.regions` until a historical source for the Hearst estate's boundary is found.

## Alternatives

- **Hand drawing all 59 areas first** (0008 as written). Better in the end, and still the plan: the drafts are its starting point.
- **Showing confidence as fill strength.** Rejected by the owner: a faint fill reads as "less likely here", which is not what it measures.
- **Letting drafts grow beyond the circle** where the evidence reaches further (the escarpment rim, the plains camp). Not now; there the circle itself may be misplaced.

## Consequences

The areas cover half the ground they did (14,566 to 7,322 km²) and sit on the ground the book describes. A changed pin or radius needs `crossing.area_drafts --force` before `crossing.build_story`. The rules are only as good as the data: escarpments come out as broken pieces, and the straight-line roads are guesses.
