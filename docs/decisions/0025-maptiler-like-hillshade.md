# 0025. A MapTiler-like hillshade

Status: accepted (2026-11-14). Amends 0016 (the hillshade).
Phase: P1

## Context

The owner asked for a more pronounced hillshade, more like MapTiler Topo's, and a lab to try it (`review/stage-8/lab-hillshade/`). The site took the lab's "Pronounced" preset, which kept 0016's colours and method with stronger shade. On 14 November 2026 the owner chose the lab's "MapTiler-like" preset instead.

## Decision

`HILLSHADE` in `site/src/map/relief.ts` takes the MapTiler-like preset: MapLibre's standard method, light from 335 degrees, exaggeration 0.45 either side of the zoom fade, and MapTiler Topo's own opaque colours (its topo-v4 style: shadow `hsl(0, 0%, 50%)`, highlight `hsl(51, 12%, 83%)`, accent `hsl(51, 67%, 56%)`), which `tokens.ts` holds as `shadeLow` and `shadeHigh`. The Imhof tint below zoom 10 and the paper above it are unchanged.

## Alternatives

- **Pronounced** (the previous default): 0016's blue-violet and grey shade, stronger. Softer than MapTiler, and its colours changed across the zoom fade.
- **Sharper terrain** (`terrain-hi.pmtiles`, tile zoom 11, about 76 MB): the rest of MapTiler's look is its resolution above map zoom 10. Not built yet; it needs a tiles release and a second terrain source.

## Consequences

The ranges read as forms at every zoom, with a neutral grey shade that sits under the cream paper's tint. On our paper it is stronger than on MapTiler's white. Above map zoom 10 the shade is still soft until the sharper terrain ships.
