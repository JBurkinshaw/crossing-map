# 0041. The classic map is called the Vintage map

Status: accepted (2026-11-16).
Phase: P1

## Context

The site's own basemap, paper and ink after the Wheeler Survey sheets, was called the classic map: "Classic" on the Map switch, "the classic map" in the interface, the pages and the docs. The owner asked for it to be called Vintage, which says what it looks like rather than that it came first.

## Decision

- The Map switch reads Vintage, Compare, Satellite, Topo, and the interface, the pages, the lab, the tools' scripts and the current docs say "the vintage map".
- The code keeps `literary` for the basemap's id and the tile names, as before (design glossary); `ClassicUnderlay` is renamed `VintageUnderlay`.
- Decision records and the changelog keep "classic" where they were written with it.

## Alternatives

- **Keep Classic.** It reads as "the default", not as a look.
- **Rename `literary` in the code and tiles too.** It changes the basemap's id and archive names for no reader-facing gain.

## Consequences

- Scripts that click the Map switch by name (tools/) use "Vintage".
