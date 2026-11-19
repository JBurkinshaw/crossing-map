# 0055. The vintage map's text a fifth larger, and the credits kept clear of the cartouche

Status: accepted (2026-11-17)
Phase: P1

## Context

The type scale (decision 0027) follows the Wheeler sheets: a 10.5 px spot height as the unit, towns at about 1.4 times it, landform names about twice it. On screen the owner found every name on the map too small to read comfortably.

The map's credits open from the bottom left, and the title cartouche, with the layer key folded in it, sits at the bottom right. Opened, the credits ran under the cartouche, and the key's grouped-stops marker, at the map's own size, ran into its label.

## Decision

- **Every text size on the vintage map is multiplied by `TEXT_SCALE` (1.2)** in `site/src/map/tokens.ts`, through `textPx`: names of places, stops, passes, water, ranches and springs, landforms, states, contour and spot heights, vignette captions and the corridor label, and the frame's margin figures. The proportions of decision 0027 stay, so the scale keeps its hierarchy. MapLibre does not allow a zoom curve inside a multiplication, so each size value is scaled where it is written rather than wrapping the expressions.
- **Landform names keep their fit.** A name along a short ridge is still capped by the room along its line, so it may grow less than a fifth.
- **The vignette builder scales its captions too** (`TEXT_SCALE` in `crossing.build_vignettes`), so its clash checks measure the captions as drawn. Some drawings moved to another side as a result.
- **The key's sample spot height grows with the map.** The cartouche, key, inset, controls and the numbers in stop rings stay as they were: they are the interface, not the map.
- **The opened credits stop short of the cartouche and the inset.** `MapView.tsx` measures the room left of whichever reaches further left with a `ResizeObserver`, so the limit follows the key opening and closing and any screen size. The credits wrap upwards instead.
- **The key draws the grouped-stops marker as the map does, at nine tenths of its size** (32 px), so it sits centred on the key's 34 px column without running into its label. It uses the map's sans-serif, centres its count, and says "places", as nearly every marker on the map does.

## Alternatives

- **Scaling the whole map canvas** (a larger pixel ratio) would also enlarge lines, glyphs and drawings.
- **Reserving a fixed width for the cartouche** in CSS needs no script, but wastes room when the key is closed, as the cartouche is narrower then.
- **CSS anchor positioning** would tie the credits to the cartouche without a script, but browsers do not all support it yet.

## Consequences

- Names take more room, so MapLibre drops a few more of the lower-priority ones where the map is crowded.
- The text sizes on the satellite and topo maps' story layers (stop and place names) grow too, as those layers are shared.
