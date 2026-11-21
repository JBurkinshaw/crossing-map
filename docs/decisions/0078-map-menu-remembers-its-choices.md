# 0078. The Map menu remembers its choices

Status: accepted (2026-11-20).
Phase: P1

## Context

The Map menu offers four choices: the map (Vintage, Compare, Satellite or Topo), the view (Flat, Tilted or Oblique), the ground (Paper, Land cover or Satellite tint) and the units. Only the units lasted past a page refresh. A reader who preferred the Oblique view on paper had to choose it again on every visit. Reading progress, the reader's place and the folds in the panel already last, in `localStorage`.

## Decision

- **Each choice is stored in `localStorage`**: `crossing-map.basemap`, `crossing-map.compare-with`, `crossing-map.view`, `crossing-map.ground`, and `crossing-map.units` as before. One hook, `useStoredState` in `site/src/storage.ts`, keeps all five.
- **Only what the reader chose is stored.** Until the reader picks something, nothing is written, so a later change of default (as decision 0072 made for the ground) still reaches them.
- **The chosen view and ground are stored, not the ones in force.** A reader who chooses Oblique and then Satellite has Oblique again on returning to Vintage, as within a visit.
- **A stored value the site no longer offers falls back to the default.** The Raised view, since renamed Oblique (decision 0040), is the kind of change this covers. No migration is needed when a choice is renamed or dropped.

## Alternatives

- **In the address, beside `#map=` and `#stop=`.** A shared link would then set the recipient's map, view and units to the sender's. The camera and the stop are a place to look at, and the menu's choices are how one reader likes to look. The address also changes with every move of the map.
- **Store every value on load, defaults included.** Simpler, but it would fix each visitor's defaults at their first visit, and a better default later would reach only new readers.

## Consequences

A reader on a new browser or device starts from the defaults. Opening with a stored Tilted or Oblique view lands on the reader's stop as usual: the browser check on 2026-11-20 found the opening flight finished in both, with Oblique closing in to zoom 11.5 as it does when chosen. When MapTiler refuses its maps (no key, or the quota spent), the site falls back to Vintage, and that fallback is stored as the reader's map. The next visit then opens on Vintage, and the reader picks Satellite or Topo again once MapTiler answers.
