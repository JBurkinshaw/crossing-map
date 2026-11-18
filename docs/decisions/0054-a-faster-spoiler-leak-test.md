# 0054. The spoiler-leak test in two halves: the data at every position, the site in one walk through the book

Status: accepted (2026-11-17)
Phase: P1

## Context

The spoiler-leak test (design section 11) loaded the site at each of ten reading positions, four in CI, and checked everything at each one. CI's four positions took about seven minutes there and 31 minutes on the owner's machine. The owner paused the CI job on 2026-11-14 because it slowed every deploy.

Two loops took most of that time. At early positions, the test went to every glyph, landform, pass, water place and vignette first seen later, about 130 places, and waited for the map's tiles at each. At late positions, it stepped through every stop reached, up to 171, so each position checked again the stops the one before had checked. Positions in between, such as 2-01, were never checked.

Every base-map layer is hidden by one filter, `layerFilterUpTo` in `site/src/spoiler/filter.ts`, and every story layer, translation and search result by `storyUpTo` and `translationsUpTo`. Search indexes only what it is given.

## Decision

- **The data half** is `site/src/spoiler/leak.test.ts`, run by Vitest with the other site tests. At all 43 positions (not started, each of the 41 episodes, finished) it runs the spoiler filters on the published data. Nothing first seen later may pass `storyUpTo` (flat and oblique copies), `translationsUpTo`, or any base-map layer's filter, which the test applies with MapLibre's own `featureFilter`. No text kept in a story feature may cite a later episode. No open question shown may name a place the reader has not met. It takes under a second.
- **The browser half**, `tools/spoiler-leak.mjs`, checks that the site shows only what those filters pass. It walks the book once: from 1-01 it presses "Read on" (decision 0053) from the stop reached most recently, to the last episode, using the progress dialog before the first stop. At each episode it checks the live map's progress filters, the story data the map holds and the features it draws, the panel, and the journeys offered. It then opens each stop the episode adds, and the stop before it, whose road now leads on. At the first episode of each Part it checks every page and the progress dialog.
- **What the walk leaves out is checked once**, after moving progress back from the end to 1-08: that the saved place moved back too, a link to a later stop with a later place saved, search and the cards it opens, the layer key, one later glyph, landform, pass name, water place and vignette gone to and looked for on the map, and the Tilted, compare and Oblique views. A first visit, a first visit straight to each page, and the phone drawer are checked as before.
- **`SPOILER_POINTS` is gone.** The walk covers every episode, so there is nothing to choose.
- **After "Read on" the walk waits two frames, not for tiles.** Reading on only adds features, so a frame drawn before the change holds nothing past the new progress. Moving back is checked once the map has settled, since the frame before still holds later features for a moment.
- **The CI job runs again before every deploy**, as a need of `build`.

## Alternatives

- **Running positions in parallel**, in a pool of browsers or a CI matrix. It cuts the wall time but not the work, and still leaves episodes unchecked.
- **Going to every later feature at fewer positions.** It keeps the pixel-level check, but the time goes into waiting for tiles to prove what one filter already decides.
- **The walk with every surface at every episode** (search, views, pages). It would check each surface 41 times through the same filtered data that the data half already checks at every position.

## Consequences

- The test checks all 41 episodes instead of four in CI or ten locally. On its first run it found a leak that no checked position had covered: the open question `q-huisiachepic`, shown from 2-01, placed Huisiachepic "about 28 km south of Tamichopa", which the book first names in 2-03. The question now says only that the area is on the upper Río Bavispe. No place the reader has reached by 2-01 lies near enough to give a useful bearing, and the map outlines the area.
- The browser half no longer goes to every later feature on the map. It trusts the data half for which features each filter lets through, checks that the live map carries the filter, and goes to one feature of each kind to see that MapLibre applies it.
- Search, the views and the layer key are checked at one position, 1-08, not four. They draw from the same filtered data at every position.
- Measured on the owner's machine against `VITE_DEBUG=1` builds served by `vite preview`, one run after the other:

  | Test | Reading positions | Time |
  | --- | --- | --- |
  | Before: CI's four (unset, 1-08, 3-08, all) | 4 | 1,889 s (736, 684, 340 and 129) |
  | After: the browser half | all 41 episodes, a first visit, and a move back | 220 s |
  | After: the data half, in `npm test` | 43 | under 1 s |

  CI ran the four positions in about seven minutes, so the walk should take about a minute there.
- `@maplibre/maplibre-gl-style-spec`, which `maplibre-gl` already installs, is now a direct development dependency of the site, pinned to the same version.
