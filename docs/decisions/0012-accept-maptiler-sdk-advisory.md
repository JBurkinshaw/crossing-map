# 0012. Ship the MapTiler SDK despite its MapLibre advisory

Status: accepted (2026-11-11)
Phase: P1

## Context

Decision 0005 puts satellite imagery behind MapTiler SDK JS, because MapTiler counts sessions only for SDK maps. The latest SDK, 4.2.1, pins its own MapLibre GL JS 5.24. `npm audit` reports a critical advisory against that version: "MapLibre GL JS: XSS Sanitizer Bypass in DOM.sanitize() via Live NamedNodeMap Removal Skip". No SDK release with a fixed MapLibre exists yet. The literary map uses MapLibre 6.17, which is not affected.

## Decision

Ship SDK 4.2.1 as it is, in the satellite chunk only. The chunk (1.3 MB, 346 kB gzipped) loads when a reader first leaves the literary basemap. Revisit when MapTiler releases an SDK on a fixed MapLibre.

Exposure is low because the satellite map renders only MapTiler's own style, with no popups and no HTML from readers or from our data. The sanitiser handles HTML in popups and attribution.

## Alternatives

- Force the SDK onto MapLibre 6.17 with an npm override: removes the advisory, but the SDK is built and tested against 5.24.
- Plain MapLibre with MapTiler raster tiles: no advisory, but billed per tile request, which a few hundred visitors would exhaust.
- No satellite: loses the reader's check of places against imagery.

## Consequences

`npm audit` and Dependabot will report the advisory until the SDK updates. The site carries two MapLibre versions: 6.17 for the literary map, 5.24 in the satellite chunk. The satellite map is created once per page and then kept (hidden on the literary basemap), so a reader who switches back and forth costs one MapTiler session.
