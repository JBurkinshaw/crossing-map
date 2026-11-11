# 0005. Satellite through MapTiler SDK JS, created on demand

Status: accepted (2026-11-11)
Phase: P1

## Context

Readers need satellite imagery to check places. MapTiler's free plan gives 5,000 map sessions and 100,000 API requests a month, then pauses until the next month. Its docs (checked 2026-11-11) count sessions only for maps made with MapTiler SDK JS. Tiles fetched by plain MapLibre are billed per request (1 per 256 px raster tile, 4 per 512 px tile), which a few hundred visitors would use up.

## Decision

The satellite basemap is a MapTiler SDK `Map`, created only when the reader switches basemap or opens the swipe. The literary map is plain MapLibre and never loads the SDK. The SDK is a separate lazy chunk.

## Alternatives

- MapTiler tiles through plain MapLibre: per-request billing.
- Esri imagery: a fine fallback, kept behind one config value.
- Self-hosted imagery: licensing and size.

## Consequences

One stated exception to "one map library": the SDK is itself a MapLibre build, so styles and layers carry over. The site works in full without MapTiler; a paused quota shows a "satellite unavailable" state.
