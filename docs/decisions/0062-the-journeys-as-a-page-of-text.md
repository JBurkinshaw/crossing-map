# 0062. An Itinerary page is the map's text alternative, and Compare moves without a drag

Status: accepted (2026-11-18)
Phase: P1

## Context

MapLibre draws routes, places and areas on a canvas. A screen reader gets nothing from it but the map's name. The panel does say everything about one stop at a time, and All stops lists a journey's stops, but no single place held the journeys as text. WCAG 1.1.1 asks for a text alternative that serves the same purpose, and guidance on story maps (Esri's for StoryMaps, the UK Government Analysis Function's for maps) says to offer the content in another form beside the map.

Compare's dividing line moved by a drag or by the arrow keys. WCAG 2.5.7 asks for a way to do with single taps anything done by dragging, and a keyboard alone does not meet it.

## Decision

- **A page, `#/itinerary`,** lists each journey the reader has reached, its stops in order, and for each stop its synopsis and the Spanish spoken there with this site's English. It is linked from the panel's footer and the pages' header.
- **It keeps the panel's spoiler rules.** It is given the stops and the translations already cut to the reader's progress. A stop in the episode being read folds its synopsis under "What happens here", as the panel does (decision 0051). `tools/spoiler-leak.mjs` checks it with the other pages.
- **The Spanish is the list the panel shows under "Spanish here":** the lines placed at that stop, without the common ones. Lines placed on a road, or nowhere, are not on the page. Search finds every line.
- **Compare's handle carries two buttons** that move the line a step either way. Home and End take it to either edge, and its value is read as "Vintage map 60%, satellite 40%".

## Alternatives

- **Hidden buttons over every feature on the map**, as Mapbox's accessibility plugin did. The plugin is archived, and a list in reading order is easier to use than several hundred unordered buttons.
- **A table of stops for download.** The data page already offers the stops as GeoJSON and GeoParquet. A reader wants prose in order, not a file.
- **A tap on the map to move Compare's line there.** A tap on the map already picks a place.

## Consequences

- The site can be read from start to finish without the map.
- The page does not show how each place was placed, or the open questions. Those are the craft (decision 0060), on the map's cards and the Open questions page.
- Nobody has yet used the site with a screen reader. That test is on the roadmap, and this page is where it should start.
- Compare cannot run on localhost, where MapTiler refuses the key, so the handle's buttons are checked on the preview.
