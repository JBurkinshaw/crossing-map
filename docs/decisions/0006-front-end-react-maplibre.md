# 0006. React, TypeScript, Vite, and MapLibre

Status: accepted (2026-11-11)
Phase: P1

## Context

The interface has a panel, a mobile drawer, a journey stepper, a spoiler filter, and search, all kept in sync with the map.

## Decision

React 19, TypeScript, and Vite, with MapLibre GL JS 6. `@vis.gl/react-maplibre` wraps the map, as a trial: only files in `site/src/map/` may import it. If the swipe, the on-demand satellite map, or the PMTiles protocol need workarounds through the wrapper, `MapView` moves to plain MapLibre and a new record says so.

State is a `useReducer` plus the URL hash, which gives shareable links. Exact versions are pinned in `site/package-lock.json`.

MapLibre 6 loads its web worker from a file beside its own module. Vite bundles that module into an app chunk, so `MapView` passes the worker's emitted URL to `setWorkerUrl`.

## Alternatives

- Plain TypeScript: fine, but we would rebuild a small framework.
- Zustand or Redux: unnecessary at this size.

## Consequences

The wrapper is cheap to remove because it is confined to one folder.
