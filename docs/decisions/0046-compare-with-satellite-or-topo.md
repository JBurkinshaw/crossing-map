# 0046. Compare with satellite or Topo

Status: accepted (2026-11-16). Amends 0017.
Phase: P1

## Context

Compare split the view between the vintage map and satellite imagery (decision 0017). The owner wanted Topo on offer as the other side too: Topo's roads, place names and contours of today set against the vintage map show what has changed in a way imagery does not.

## Decision

- Compare stays one button on the Map switch. While it is on, a **With** row under the switch picks the map right of the swipe: Satellite or Topo.
- Compare starts with Satellite, and keeps the reader's choice when they leave Compare and come back.
- The Map switch shows Vintage and the chosen map as paired, and the swipe's accessible name says which map it compares.

## Alternatives

- **A second Compare button for Topo.** Five buttons crowd the switch on a phone, and two buttons with one icon read as the same thing.
- **Satellite and Topo on the Map switch pick the side while Compare is on.** Fewer controls, but the same button would mean "show this map" or "compare with this map" by mode, and leaving Compare for Satellite would take two clicks.

## Consequences

- Compare in Topo works in Flat and Tilted, as Compare in satellite does.
- The keyboard check of the Compare swipe (`tools/spoiler-leak.mjs`) covers satellite only.
