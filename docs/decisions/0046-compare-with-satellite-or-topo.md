# 0046. Compare with satellite or Topo

Status: accepted (2026-11-16). Amends 0017.
Phase: P1

## Context

Compare split the view between the vintage map and satellite imagery (decision 0017). The owner wanted Topo on offer as the other side too: Topo's roads, place names and contours of today set against the vintage map show what has changed in a way imagery does not.

## Decision

- Compare stays one button on the Map switch. While it is on, Satellite or Topo on the same switch picks the map right of the swipe, and Compare stays on.
- Choosing the map already right of the swipe leaves Compare and shows that map on its own. Vintage leaves Compare too.
- Compare starts with Satellite, and keeps the reader's choice when they leave Compare and come back.
- The Map switch shows Vintage and the chosen map as paired, and the swipe's accessible name says which map it compares.

## Alternatives

- **A With row (Satellite or Topo) under the Map switch while Compare is on.** Built first, then dropped: the owner clicked Topo on the Map switch to compare with it, and that left Compare. Two controls for one choice invite the wrong one.
- **A second Compare button for Topo.** Five buttons crowd the switch on a phone, and two buttons with one icon read as the same thing.
- **Leave Compare only through Vintage.** One meaning per button in Compare, but Topo on its own would take two clicks.

## Consequences

- Satellite and Topo do two things on the Map switch: in Compare they pick the side, and otherwise they show their map. The line under the switch says so while Compare is on.
- Compare in Topo works in Flat and Tilted, as Compare in satellite does.
- The keyboard check of the Compare swipe (`tools/spoiler-leak.mjs`) covers satellite only.
