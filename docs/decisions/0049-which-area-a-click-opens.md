# 0049. Which area a click opens

Status: accepted (2026-11-17)
Phase: P1

## Context

Areas overlap. A region (the Animas Valley, La Babícora) holds many inferred areas, and inferred areas overlap one another: north of the Laguna de Babícora (about 29.6° N, 107.75° W) eight J4, J5 and J7 areas each overlap at least one other. A click opened whichever area came last in `data/areas.geojson`, which draws on top. So a region took the click from all 19 inferred areas inside it (J7's old Playas road among them), J4's dry camp took 84% of J4's tracking north, and J7's high country of the Babícora took 74% of J4's steer herd, even with J4 in focus.

## Decision

When a click falls on several areas, and on no stop, place or route above them, it opens one by these rules, in order (`areaPick` in `site/src/story/select.ts`):

1. **An edge before an inside.** Every area has an unseen strip along its edge, 12 px wide for an inferred area (`areas-edge-hit`) and 14 px over a region's line and band (`regions-hit`). A click on any area's edge opens that area, even inside a larger or nearer one, so every outline can be picked.
2. **The journey in focus.** Its areas are the strongly tinted ones, so the click opens what the reader sees. Stops follow the same rule.
3. **The smallest.** The most specific area wins. Size is worked out in the browser from the geometry, in square degrees scaled by the cosine of the latitude, which is enough to rank areas this close together.

A region is still clickable anywhere inside. It has no journey and is far larger than any inferred area, so it opens only where no inferred area lies, or from its edge.

## Alternatives

Kept here for when the question comes back.

- **A region opens from its edge only.** Built first. The owner wanted regions clickable inside as well, with the edges taking precedence.
- **Edges only, for every area.** An inferred area is a tinted shape that invites a click, a small one would be a thin target (worse on phones), and around the Babícora the edges cross and run side by side, so edge clicks would collide too.
- **Ask when a click is ambiguous.** A short list of everything under the click to choose from. The most honest, but every click inside a region would take two steps.
- **Regions drawn under the inferred areas.** Rests on file order and settles nothing between inferred areas.
- **Size from the build** (an `area_km2` property). Exact, but a data change for a ranking the browser can make alone.

## Consequences

- Every inferred area wins somewhere: J4's steer herd everywhere it is drawn, J4's tracking north over J4's dry camp.
- An area under a larger one of its own journey is reached from its own inside. A larger area under a smaller one is reached from its edge strip or its uncovered ground.
- A click near an edge picks that edge's area, so an area that touches another's edge gives up a 6 to 7 px strip there.
