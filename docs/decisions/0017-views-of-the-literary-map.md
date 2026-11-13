# 0017. Views of the literary map: Flat, Tilted and Raised

Status: accepted (2026-11-12)
Phase: P1 (Flat and Tilted); Raised is a preview around the Pilares

## Context

The relief reads as a flat pattern of strokes. Carl Churchill's plan oblique maps and the block diagrams made in the hachure lab show ranges standing up from the paper, which reads at a glance. MapLibre can tilt the map over 3D terrain, but a tilted map hides the far ground and makes the map harder to read as a map. Plan oblique relief (Jenny and Patterson, *Cartographic Perspectives* 57, 2007) keeps the map flat and north-up, and moves each point north in proportion to its height.

## Decision

The literary map has three views, switched beside the basemap switch. Satellite and Compare always use Flat.

- **Flat**, the default: the map seen straight down.
- **Tilted**: MapLibre's 3D terrain at 1.5 times exaggeration, tilted 40 degrees.
- **Raised**: plan oblique line work from `oblique.pmtiles`, built by `crossing.plan_oblique`. Each point moves north by twice its height above the lowest ground. Ground hidden behind a nearer ridge is cut away, and the edges of the cut-away ground are drawn as crest outlines. Ridgelines are traced on the DEM, where the ground peaks across its strongest downward curvature, and drawn where they are not hidden and no crest outline runs. Hachure strokes are trimmed by a fifth at each end, so that once stretched they do not join into long lines. Strokes are dropped where the shift squeezes the ground to under half its depth.

A **Land colour** option, for Flat and Tilted, puts the satellite map under the classic map: the imagery is brightened, saturated and faded over white, and the classic map is multiplied over it, so the paper takes the land's colour while ink and water keep theirs. In Tilted the satellite map turns on MapTiler's terrain so the imagery stays under the relief. **Compare** draws the classic base on a second, non-interactive map clipped left of the swipe, so the story layers run over both halves, as in Satellite.

Raised hides the base layers that cannot move with the terrain (hillshade, flat hachures, water, roads and glyphs) and the story's stops and areas. Only the journeys are shifted so far.

## Alternatives

- **Blender or rayshader renders**, as on Churchill's maps: a better look, but a raster image per area and a rebuild for every style change.
- **Pre-generated block diagrams on place cards**: parked for Phase 2.
- **Shifting in the browser**: MapLibre cannot move a vertex by a value read from another source, so the shift happens in the pipeline.
- **Keeping the folded strokes as ridgelines**: they read as ridges, but come with long strokes crossing each other on squeezed slopes.

## Consequences

- Raised covers two test tiles around the Pilares (108.9 to 109.7 W, 30.7 to 31.1 N), about 5 MB. The whole corridor needs the shift run per tile, and the story layers need shifting in the pipeline.
- The flat hillshade cannot be used in Raised. A pre-shifted shading layer would bring the tone back.
- `oblique.pmtiles` ships in the tiles release, built by `crossing.plan_oblique`.
- Land colour is a third way to create the MapTiler SDK map (decision 0005), so each reader who turns it on uses one session. Its terrain loads inside that session.
