# 0030. Lakes drawn over the rivers

Status: proposed (2026-11-15). Owner's request after the Bavispe review.
Phase: P1

## Context

The base map drew the lakes as a 25% water tint under the creeks and rivers. INEGI's and NHD's networks run flow lines through water bodies, so the river and every tributary crossed the lake to its centre line, as on the Bavispe at La Angostura. The owner wants the river under the lake.

## Decision

- The `lake` layer is drawn after `river` and before `road` in `site/src/map/style.ts`, with an opaque fill: `lake` (`#cbc9b6`, the water at 25% over the paper) and `lakeDry` (`#ded7bf`, 12%) for intermittent water bodies. A river now ends at the shore. This follows the owner's judgement: the Wheeler notes (review/stage-8/wheeler/README.md) and docs/inspiration/ say nothing on how a river meets a lake. The river's name is still set over the lake.
- The hillshade, hachures and contours are under the lake.
- The Raised view is unchanged: its lake stays flat while its streams are raised, so the raised streams stay over it.

## Alternatives

- **Clip the creeks and rivers to the lakes when the tiles are built.** Cleaner, and it would serve the Raised view, but it needs a tile release, and a river's name would lose the line it follows across the lake.
- **A semi-opaque lake over the rivers.** The channel would show faintly through the water, which reads as neither.

## Consequences

- The lake's colour is fixed, not a tint over what is under it. It is the same on the Mexico side, which is a shade darker, and it hides the relief tint below zoom 10.
- A road that crosses a lake (a causeway) still draws over it.
