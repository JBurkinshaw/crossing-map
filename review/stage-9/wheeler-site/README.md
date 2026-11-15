# Wheeler rollout to the site: frame, water places and type scale (stage 9)

The owner adopted the Wheeler lab's improvements for the site, except historic roads. Three test-area cards were still lab-only. This packet rolls them out over the whole classic map (Flat and Tilted views; hidden in Satellite, Topo, Compare and Raised like the other base layers). Decision 0027 records the choices.

Packets behind it: `review/stage-9/wheeler-places/README.md`, `review/stage-9/wheeler-type/README.md`, `review/stage-8/wheeler/README.md`.

## How to see it

1. `cd site && npm run dev -- --port 5241`, then open the site.
2. Zoom to 8 or more for the graticule and its margin labels, 11 or more for the water places. San Luis Pass (zoom 12, 31.39° N, 108.75° W) shows a pass name; the Bavispe valley near Colonia Morelos (zoom 11) shows the Sonoran ranches.
3. Screenshots: `cd tools && node wheeler-site-shots.mjs <label> http://localhost:5241/` writes `private/review/stage-9/wheeler-site/<view>-<label>.jpg`.

Rebuild the data (local caches only, no network):

```
uv run --project pipeline python -m crossing.water_places
uv run --project pipeline python -m crossing.graticule
uv run --project pipeline python -m crossing.pass_lines
uv run --project pipeline python -m crossing.downloads
```

## 1. Graticule and frame

- `crossing.graticule` writes `site/public/labels/graticule.geojson` (74 lines over the story box), beside `states.geojson`. The lab reads the same file. Layer `graticule` in `style.ts`: faint ink from zoom 8, over the line work and under all type.
- `site/src/map/MapFrame.tsx` and `map.css` draw the frame of sheet 70A: thin-thick-thin rule (1, 2, 4, 2, 1 px), a 20 px margin band with the graticule's labels (15′, 30′, 109°), and a 1 px neatline, 31 px in all. It shows when the map area has the class `framed` (classic basemap, not Raised). Labels hide while tilted.
- Everything set on the map moves inside the neatline by `--frame`: the switches, the inset, the cartouche, the notices, MapLibre's zoom, scale and credits (and the satellite map's logo, for the satellite tint), and the canvas's focus ring (offset to sit just inside the neatline).
- **Phones (720 px and narrower):** the rule alone, 1, 1, 2, 1, 1 px (6 px), no band, no neatline, no labels. The lab's 15 px band would cost 46 px of a 390 px width. The graticule lines still show.
- **Cartouche:** a thin neatline inside a thin-thick rule (box shadows 3, 6, 7.5, 8.5 px), as the places packet set out; 2, 4, 5, 6 px on phones. It sits 5 px further in (17 and 33 px), and the inset 5 px higher (146 px; 84 px on phones).
- Keyboard: the frame is `aria-hidden` and takes no pointer events; the tab order is unchanged. Checked by tabbing to the map and panning with the arrow keys (`desktop-focus-after.jpg`).

## 2. Water places and stations

`crossing.water_places` now covers the journeys corridor (`crossing.hachures.corridor()`: the legs ridden or walked, 20 km each side) instead of the test box, with the same kinds and rules, and writes `data/water_places.geojson` with the shared story-layer schema.

| Kind | GNIS | GeoNames | Book | Total |
| --- | --- | --- | --- | --- |
| spring | 687 | 19 | 1 (Hog Canyon Spring) | 707 |
| ranch | 2 | 480 | 3 (La Babícora, Hacienda de San Diego, Nahuerichic) | 485 |
| station | 0 | 39 | 0 | 39 |
| tank | 0 | 2 | 0 | 2 |
| well | 0 | 0 | 0 | 0 |
| **Total** | 689 | 540 | 4 | **1,233** |

- 21 points were dropped: 3 within 1 km of a book place (Hog Canyon Spring in GNIS, the Nuevo Casas Grandes railway station, Rancho Tres Potrancas by Janos), 18 as same-name twins. The script prints each.
- Gazetteer points have `first_seen` 1-01, `method: gazetteer`, `source_id` (the GNIS or GeoNames id) and a `note_safe` naming the class or code. The book's four keep the place's `first_seen`, `certainty`, `source` and `note_safe`, and `place_ref` points at the place. `crossing.validate` fails if one shows before its place (new test in `test_validate.py`).
- Schema: new `water_places` layer; kinds `station`, `tank` and `well` added. `crossing.downloads` writes `data/parquet/water_places.parquet`. Listed on the Data page, in `data/README.md`, `docs/pipeline.md`; the GNIS and GeoNames "use" lines on the Credits page name springs, ranches and stations.
- The map (`waterPlaces.ts`, layer `water-place`): `copy-data.mjs` writes `public/data/map/water_places.geojson` (1,229 gazetteer points, 228 kB). From zoom 11, a mark per kind drawn in code (ring spring, dot well, ringed dot tank, solid square ranch, open square station) and the name in 10.5 px italic at 0.72 opacity. It is the lowest symbol layer, so every other name wins. `WaterMarks.tsx` adds the marks to the site's map when it is made; `addWaterMarks` does it for the compare underlay and the lab maps.
- Spoilers: `water-place` is in `PROGRESS_LAYERS` with the 1-01 floor. `tools/spoiler-leak.mjs` goes to every water place first seen after the reader's position and checks the map draws none.

## 3. Type hierarchy

- `tokens.ts`: `typeScale` (spot 10.5, town 14.5, quiet 10.5, pass 10.5 px at zoom 11), `QUIET_OPACITY` 0.72 and `zoomedSize()` (0.85 at zoom 9, 1.15 at 13). The unit is the site's spot height, 10.5 px, not the lab's 9.5 px: the site enlarged its small type on purpose (commit 9fe6445), and the hierarchy scales from it.
- **Towns** (`StoryLayers.tsx`): towns, cities and locales in roman at 14.5 px; `kind: city` in capitals spaced 0.08 em (the type packet's rule). There are no town labels in the base style (`style.ts`); all place names come from the story layers.
- **Ranches and springs** the book names: 10.5 px italic, quiet (0.72) unless the journey stops there.
- **Passes:** `crossing.pass_lines` (from `type_lab_data.py`, which now calls it) finds a line through each of 162 named passes: 5 along a Natural Earth road within 1 km, 157 across the saddle. `site/public/labels/passes.geojson` holds one point per pass with its angle. Layer `pass-label` (`relief.ts`) sets the name in small capitals turned to that line; the book's passes from zoom 7, the rest from 9. Named pass glyphs are no longer drawn. The book's pass places keep their ring and lose their point label while the pass name shows; the name sits 0.9 em beside the ring.
- `landform-label` is unchanged, and the vignette captions still go to the top of the stack.
- Spoilers: `pass-label` is in `PROGRESS_LAYERS`; a pass the book names takes the place's `first_seen`. The leak test checks every pass name first seen later.

## Screenshots

In `private/review/stage-9/wheeler-site/`, all with the whole book read. Desktop is 1400 × 900, phone an iPhone 14 (390 × 844).

| View | Before | After |
| --- | --- | --- |
| Zoom 8, bootheel | `desktop-z8-before.jpg` | `desktop-z8-after.jpg` |
| Zoom 10, Cloverdale and the San Luis Mountains | `desktop-z10-before.jpg` | `desktop-z10-after.jpg` |
| Zoom 12, Guadalupe Mountains springs | `desktop-z12-before.jpg` | `desktop-z12-after.jpg` |
| Zoom 12, San Luis Pass | `desktop-z12-pass-before.jpg` | `desktop-z12-pass-after.jpg` |
| Zoom 11, Sonoran ranches by Colonia Morelos | `desktop-z11-bavispe-before.jpg` | `desktop-z11-bavispe-after.jpg` |
| Zoom 10, phone | `phone-z10-before.jpg` | `phone-z10-after.jpg` |
| Tilted, zoom 10; keyboard focus | | `desktop-z10-tilted-after.jpg`, `desktop-focus-after.jpg` |

## Checks

`npx tsc -b`, `npx oxlint`, `npm run build`, `npm test` (23 tests), ruff, pytest (22), `crossing.validate`, `crossing.downloads --check`, `crossing.echo_check` (0 shared runs), contrast (`tools/contrast.mjs`: water place names 5.77:1 on the paper and 5.24:1 on the Mexico side, quiet book names 5.56:1, pass names 12.53:1, margin labels 14.31:1), and the spoiler-leak test against a `VITE_DEBUG=1` build under `vite preview` (result in the final report).

The three new GeoJSON files load with the style: 228, 31 and 15 kB, about 30 kB gzipped in all.

## Left out

- Historic roads (tracing is shelved). Pass lines follow today's Natural Earth highways where one is near.
- Margin labels in the Tilted view.
- The layer key does not list the water marks or the pass names.
- Tanks and wells: the lab's rules find only 2 tanks and no wells in the corridor (GNIS "... Tank" reservoirs and GeoNames "Bordo" dams stay out, as in the lab).

## Open questions for the owner

1. The frame costs 31 px of view on each side on a desktop. Keep it, or only the rule (as on phones)?
2. Should named passes keep a small glyph under their name, as the lab did, at the cost of losing more collisions?
3. 480 GeoNames ranches carry no date; some postdate the 1940s. Keep all as context, or only those on a period map?
4. Water marks and pass names in the layer key?
