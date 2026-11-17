# 0042. Land cover drawn in ink over its colour

Status: accepted (2026-11-16). Extends 0040.
Phase: P1

## Context

Decision 0040 draws the land cover as flat tints. An r/mapmaking thread on "land cover hachures" ([Example of Land Cover Hachure Lines](https://www.reddit.com/r/mapmaking/comments/1w1xxt1/example_of_land_cover_hachure_lines/), u/lost-my-glasses, after u/TheCountVonZeppelin's [An experiment in land cover hachures](https://www.reddit.com/r/mapmaking/comments/1w1pr3x/an_experiment_in_land_cover_hachures/)) points to the *Carte générale de la Martinique* (M. Monnier and C. G. Le Bourguignon-Duperré, Dépôt général de la Marine, 1831; [David Rumsey Map Collection](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~372081~90137794:Carte-Generale-De-La-Martinique)), which draws what grows on the ground in the same ink as its hachures: woods as dots, plantations as marks in rows, fields as ruled parcels, buildings as small blocks. The lab section "Land cover ink" tried the land cover as ink textures, as tiny drawn icons in the pen of the glyphs and vignettes, and both over a wash of the tints from 0 to 60%. The owner chose the textures over the full tints.

## Decision

- When the ground is Land cover, every view draws the tints of 0040 (60% over the paper) and, over them, an ink texture per class: pine as close dark dots, oak woodland as small open crowns, gallery forest and wetland as the densest dots, grassland as sparse tufts, desert scrub as a fine stipple, fields as ruled parcels that turn from one parcel to the next, towns as small black blocks, and water as close level lines in the water's ink.
- The textures are drawn in the browser (`site/src/map/landcoverInk.ts`) with a fixed seed, so they are the same on every load, and repeat every 96 px. Nothing is traced or copied from the Martinique chart; it is a reference for the kind of mark, not a source.
- On the ground the ink sits over the hillshade, so the hillshade does not grey it, and under the contours and hachures; the colour stays under the hillshade. In the Oblique view the ink fills the shifted land cover polygons, under the strokes.
- The layer key shows each class's colour with its texture.
- The thread and the chart are credited on the Credits page (style references) and listed in `docs/inspiration/`.

## Alternatives

- **Ink without colour.** One ink, as on the chart, but grass and scrub read as an even speckle and classes are hard to tell apart.
- **Tiny drawn icons**, in the pen of the glyphs and vignettes (tried in the lab, then removed). They read as trees and houses at once, but oak and gallery forest look alike, the icons do not grow with the zoom, and as a repeating fill they show their grid. Placing each icon as a point in the pipeline would fix the last two at the cost of more tile data.
- **A lighter wash** (35%). Closer to a hand-coloured engraving, but the owner kept the site's tints.
- **Outlining patches, leaving scrub bare, and keeping the ink off steep ground.** Not wanted.

## Consequences

- No new data: the textures fill the same polygons as the tints.
- A repeating texture keeps one size at every zoom and shows its grid on large patches.
