# 0043. MapTiler's logo and credits in the map's own controls

Status: accepted (2026-11-16). Amends 0005.
Phase: P1

## Context

The satellite and Topo basemaps are a MapTiler SDK map under the vintage map (decision 0005). The SDK adds its own logo and attribution control to that map, so the screen showed two attribution controls: the vintage map's, with "Credits" and each archive's credit, and MapTiler's, apart from it. The site pushed its own bottom-left controls 100 px to the right to clear MapTiler's logo. The owner wanted one attribution control, and the logo above the other bottom-left controls.

MapTiler's free plan requires its logo and its credit ("© MapTiler © OpenStreetMap contributors" and the imagery providers) wherever its maps show. The SDK turns both off together with one option, `forceNoAttributionControl`.

## Decision

- The SDK map is made with `forceNoAttributionControl: true`, so it draws no logo or attribution of its own.
- The SDK's own `MaptilerLogoControl` is added to the vintage map's bottom-left controls, first in the column, above the credits and the scale. It shows whenever the MapTiler map does (Satellite, Topo, Compare and Satellite tint) and hides when it doesn't.
- The credits of the MapTiler style's sources, read from the SDK map after each style loads, join "Credits" and the archives' credits in the vintage map's one attribution control while the MapTiler map shows.
- The bottom-left controls stack as a column, with the logo ordered first, so a new attribution control (made whenever its credits change) never lands above it.

## Alternatives

- **Keep MapTiler's controls and move them with CSS.** Two maps' controls in separate containers cannot share one stack, and the two attribution controls stay two.
- **Draw a logo of our own.** Simpler to place, but the free plan asks for MapTiler's logo, and the SDK's control is that logo with its link.
- **Hide the SDK's controls with CSS.** The SDK would still make them, and hiding MapTiler's required credit, even when repeated elsewhere, invites a terms question.

## Consequences

- One attribution control on screen, with MapTiler's and OpenStreetMap's credits in it only while their map shows.
- The logo and credits depend on our code, not the SDK's: a change to how `SatelliteMap` starts must keep both, or the site breaks MapTiler's terms.
- The dev-only hillshade lab shows the logo but not MapTiler's credits.
