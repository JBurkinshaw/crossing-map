# 0024. Wheeler hachures in the journeys corridor

Status: proposed
Phase: P1

## Context

Decision 0022 brought the Wheeler Survey's paper and brown-black ink to the map, but left the strokes themselves as 0016 drew them: sepia-weight lines whose darkness comes from width and opacity. The Wheeler sheets darken steep ground by packing short strokes of one width closer, leave crests, spurs and summits as white partings, leave mesa tops and valley floors blank, and draw escarpments as one comb of wedges. A build of that look for one test box in the bootheel and the upper Bavispe (`crossing.wheeler_hachures`, `review/stage-9/wheeler-hachures/README.md`) was shown in the lab, and the owner liked it and asked for it on the site over the same ground as the fine hachures.

## Decision

- **Build.** `crossing.hachures --style wheeler --region corridor` runs the Wheeler build over the fine scale's region (`crossing.hachures.fine_region()`: the journeys buffered 20 km each side, where the DEM covers them), on the production 40 km tile grid, at the settings the test box used. Output goes to `private/cache/relief/wheeler/`, never the production cache.
- **Archives.** `tiles.build_relief --style wheeler --region corridor` packs the strokes (`hachure`), the rim wedges (`rim`) and a copy of the production coarse strokes (`coarse`) into `relief-wheeler.pmtiles` (zoom 10-11) and `relief-wheeler-12.pmtiles` (zoom 12), each under 100 MB. The coarse copy means the Wheeler set fetches no other hachure archive.
- **Style.** `HACHURE_SET` in `site/src/map/relief.ts` chooses the corridor's hachures, `'wheeler'` or `'production'`. Wheeler strokes draw as in the lab: the hachure ink (`#2e2010`), one width (0.42 px at zoom 10, 0.53 at 11, 0.8 at 12, 1.2 at 13), opacity 0.92, 70% of them at zoom 10. Their contrast comes from packing, so 0016's shading and 0022's slope contrast stay on the coarse strokes only. The rim wedges are filled polygons in the same ink.
- **Both sets kept.** The production fine and dense archives (`relief.pmtiles`, `relief-dense.pmtiles`) and their cache stay, are released with the Wheeler archives, and come back with one change to `HACHURE_SET`.

## Alternatives

- **Replace the production set outright.** Smaller releases and less code, but no way back without a rebuild of over an hour. The owner asked to keep both for now.
- **Draw the coarse strokes from `relief.pmtiles`.** No duplicated data, but in the corridor every tile of `relief.pmtiles` carries the fine strokes the Wheeler set does not draw, which would about double what a reader fetches there.
- **One archive per region instead of per zoom.** Also under 100 MB, and range requests fetch only the tiles in view either way. Splitting by zoom was chosen because the strokes cost about the same at every zoom, so the split point is easy to move, and each archive covers the whole corridor, so the style needs no region boundaries.
- **Retune before rolling out** (closer steep strokes, wider summit discs). Left for later: the owner liked the test box as it is, and the steep spacing doubles the run time of the Sierra tiles.

## Consequences

- The corridor reads like the Wheeler sheets at zoom 11 and 12. Zoom 10 is busier and more speckled than the production set.
- Steep ground draws about 26% ink at zoom 11, against Wheeler's 40 to 50% (the test box's open question 1 still stands).
- A tile release now carries two hachure sets, about 100 MB more. The GitHub Pages limit of 1 GB per artifact should be checked when both the root and the preview ship their own tiles.
- The Raised view still draws the production strokes (`crossing.plan_oblique`), so its hachures differ from the flat map's in the corridor.
- The Wheeler build cuts and clears strokes again on every run (a few minutes); only the generator tiles are cached.
