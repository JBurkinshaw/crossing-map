# 0072. Land cover is the default ground, and Tilted terrain stands a quarter higher

Status: accepted (2026-11-19). Amends 0040 (the default ground) and 0017 (the Tilted view's exaggeration).
Phase: P1

## Context

Decision 0040 added Land cover to the map's Ground switch and kept Paper as the default. Land cover shows the country the riders cross, forest, oak woodland, grass, scrub and fields, and it works in all three views, but a reader saw it only after finding it in the Map menu. Paper led the switch, so the menu also suggested that land cover was an extra.

The Tilted view draws MapLibre's 3D terrain at 2.5 times its height (decision 0017). The owner asked for the terrain to stand a quarter higher.

## Decision

- **Land cover is the vintage map's default ground.** The Ground switch lists Land cover first, then Paper, then Satellite tint. Where land cover is not available (the Satellite and Topo basemaps), the switch shows Paper, as before.
- **The Tilted view's terrain is exaggerated 3.125 times,** 25% more than 2.5. `TERRAIN_EXAGGERATION` in `site/src/map/setup.ts` holds it for every map that draws the terrain, including the Compare view's satellite side.

## Alternatives

- **Keep Paper as the default, and point to Land cover in the key.** A reader who never opens the Map menu would never see the land cover.
- **A larger step in exaggeration.** A further step is a later change if the hills still read flat.

## Consequences

- The first map load adds the land cover's tiles (`landcover.pmtiles`, read by range requests), so first load fetches a little more than on Paper.
- Paper is still one click away for readers who want the plain sheet.
- Hills in the Tilted view stand higher, and labels and stops on slopes rise with them.
