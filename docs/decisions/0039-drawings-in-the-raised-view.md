# 0039. Drawings in the Raised view

Status: accepted (2026-11-16). Owner's decision, after the drawings were found missing from the Raised view. Extends 0026.
Phase: P1

## Context

The Raised view hides every layer of the classic style that cannot move with the terrain, and keeps only the paper and the lakes (`KEPT_IN_RAISED` in `site/src/map/style.ts`). The drawings are classic layers, so they vanished in Raised. They could not simply be shown: in Raised every story point is moved north by its height (`crossing.plan_oblique`, decisions 0018 and 0019), so a drawing at its flat position would stand south of its raised pin, by up to a few kilometres in the sierras.

## Decision

- **Raised copies.** `crossing.plan_oblique` raises `data/vignettes.geojson` with the story layers into `data/raised/vignettes.geojson`. Each drawing moves north by the height under its own point, by the same rule and the same DEM as the stops, so a drawing on its stop lands exactly on the raised stop (38 of the 54), and one with a point of its own (16, such as the Trinity cloud or Billy leading the wolf) moves by its own height. The side, the first zoom and every other property are the flat copy's.
- **A cheap run.** `crossing.plan_oblique --vignettes` prepares the strips' DEMs, raises every story layer into a scratch folder, and writes only the drawings, in under a minute. It stops if the other layers come out more than 0.0001 degrees (about 10 m) from their published copies, which would mean the DEM or the story has changed and the full run is needed. `--properties` copies the drawings' properties too.
- **The site.** In Raised the drawing and caption layers stay, and MapView points their source at the raised copy; back in Flat or Tilted it points at the flat copy again. The spoiler filter and the journey opacity act on the layers, not the source, so they hold in both. `crossing.validate` checks that the raised copy holds the same drawings with the same properties as the flat one, and the spoiler-leak test looks for later drawings at their raised points in Raised.

## Alternatives

- **Hide the drawings in Raised** (as before). Simple, but the view loses the book's people and things.
- **Shift the drawings in the browser** by the raised stop's offset. Wrong for the 16 drawings with their own points, and a second copy of the rule in TypeScript.

## Consequences

A drawing shows in Raised from its own first zoom, but never before zoom 9, where the Raised view starts. The sides were chosen for the flat map; in the sierras, where the raised pins move most, a drawing may sit on raised line work it would not cover flat. A change to a drawing's point needs `--vignettes` before committing. `crossing.validate` checks the raised copy's features and text, not its points, so a stale point would pass it unnoticed.
