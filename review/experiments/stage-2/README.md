# Stage 2 leftovers: state names, the Cloverdale Creek road, a 60 fps proxy

An experiment on its own branch, for the owner to review before anything is merged. It takes the three items left open in `review/stage-2/README.md` ("Not done yet in stage 2"): state names in small capitals, a snapped road for the Cloverdale Creek legs, and a frame-rate measure standing in for a mid-range phone.

The branch starts from `stage/4-rest-of-book` (96aa22b). Two commits change the map; a third adds this folder and the two measuring scripts.

**Merged on 14 November 2026.** The owner took the defaults for the open questions below: the trap stays on the creek road, the crossfence stays on the road, each journey keeps its own circle, and the state labels start at zoom 5 as a base layer at 55% opacity. The seed rows now live in the unified `pipeline/seeds/stops.csv` and `snaps.csv`, and the state labels run as `python -m tiles.state_labels`. The images named below are in `private/review/stage-2-leftovers/`, because git no longer tracks review screenshots.

## 1. State names in small capitals

**What it does.** Arizona, New Mexico, Texas, Sonora and Chihuahua are named in IM Fell English SC (the self-hosted small capitals, `site/public/fonts/IMFeENsc28P`), with 0.6 em letter spacing, at 12 px (zoom 5) to 16 px (zoom 8), in ink at 55% opacity, fading out between zoom 7.5 and 8.5. The Mexican states take their Spanish names from Natural Earth's `name_es`. For these two states that is the same as the English name. Baja California, Baja California Sur and Sinaloa have only slivers in the story box (928, 6,620 and 106 km²), so they get no label.

**Where the labels go.** `tiles/state_labels.py` tests points on a 5 km grid over each state's part of the story box. A label fits at a given zoom when the box of its lettering (size and spacing as the style draws it, glyph widths measured from the font with fontTools), plus an 8 px margin:

- lies inside the state's part of the box, and
- touches no journey, area, stop or place, and no place label (estimated as a box under the point).

Zoomed out (zoom 5 to 6.5) each state gets one label: the point that fits from the lowest zoom, with at least 30 px clear, and then the point nearest the state's pole of inaccessibility. From zoom 6.5, each state gets up to six labels at least 300 px apart, so a closer view still shows a state name. That gives 18 points: 5 overview labels (Arizona and New Mexico from zoom 5, Sonora and Texas from 5.5, Chihuahua from 5) and 13 closer-in labels. Each point carries `min_zoom` and `max_zoom`, and the style reads them. The state-label layer is the last base layer, so the story's own labels, which are added above it, win any collision. It hides with the other base layers in Satellite, Topo and Compare.

**Why a GeoJSON file, not the base tiles.** The 18 points are a 4 KB file in `site/public/labels/states.geojson`, which the style reads as its own source. To put them in `base.pmtiles` instead, `tiles/build_base.py` would have to be rerun and a new tiles release published. Only the owner publishes releases. A GeoJSON file also has three other advantages:

- The placement depends on the story layers, which change with every data fix. The tiles would go stale. The file can be rebuilt in 3 seconds.
- A GeoJSON source keeps exact float properties (`min_zoom` 5.5).
- The file is small enough that tiling it gains nothing.

The cost is one extra 4 KB request at load.

**Images.**

- `states-z5-before-after.png` and `states-z6-before-after.png`: the opening views, before and after.
- `states-closer-in.png`: zoom 7.2 (Sonora and Chihuahua at the edges), zoom 7.5 (Chihuahua in the empty country east of Casas Grandes), and the phone at zoom 6 over the bootheel. There the story fills the screen, so no state name shows. That is intended.

**What does not work well yet.**

- The story fills the middle of the box, so the overview labels end up near its edges. New Mexico is at 35.58° N, close to the top of the box. Chihuahua is at 27.50° N, at the bottom, where the cartouche covers it at some desktop views (for example zoom 6.2 centred on the bootheel).
- The phone opens at about zoom 4.6, below the label range, so a phone reader sees no state names until they zoom in.

## 2. The Cloverdale Creek road

**TIGER has the road.** In Census TIGER 2023 for Hidalgo County (`tl_2023_35023_roads`), the road west up the creek from Cloverdale has three names:

- Cloverdale Rd C001, through the village
- Co Rd C001, up the creek for 5.9 km to a fork
- Co Rd C106, west from the fork for 2.6 km to the road's end

The road runs 7.0 km from Cloverdale to the fork and 9.6 km to its end. NHD's Cloverdale Creek runs beside it.

**What the text says (paraphrased, 1-08).** At first light Billy rides through Cloverdale and turns up the creek road. The sun rises behind him, so he rides west, up the creek. About two hours later he leaves the road and crosses a pasture to the vaqueros' old fire, where the wolf is in the trap. Later he leads her back down the road. After an hour he stops at Robertson's crossfence, with Cloverdale an hour's ride further on. From there he turns south.

**The problem with the old stops.** The trap (J1 stop 13 and J2 stop 2) sat on the GNIS point for Cloverdale Creek (887693), 1.7 km downstream and east-south-east of Cloverdale. A ride west could not reach it. The crossfence (J2.3) was 4.5 km south of the road. `data/open-questions.json` already asked where the trap was ("q-cloverdale-creek").

**What changed** (commit 3923edc):

- **Trap (J1.13 and J2.2):** moved to the road 8 km out of Cloverdale (31.45106, -108.99695), with a 2 km circle, certainty `inferred`. Two hours at a walk is about 8 to 12 km, and the road ends at 9.6 km, so the circle covers the road's upper reach and the pastures either side. The reasoning is on J1.13; J2.2 points to it.
- **Crossfence (J2.3):** moved onto the road about halfway, 4 km from Cloverdale (31.43001, -108.96525), with a 1.5 km circle. The Robertson ranch reasoning is kept.
- **Snaps:** J2 legs 1 (Cloverdale to the trap) and 2 (the trap back to the crossfence) now follow the road and are drawn solid (`narrated-path`, source `census-tiger`). Two rows were added to `pipeline/seeds/part1-snaps.csv`. That file gains a `source` column like the later batches, so the Whitewater Creek row now says `nhd`.
- **`build_story.py`:** a snap may now name several TIGER road names, separated by semicolons (`WHERE FULLNAME IN (...)`), as it already could name several county files.
- **Not snapped:** J1 leg 12 (the wolf's way to the trap) and J2 leg 3 (the crossfence to the Guadalupe pass) stay schematic. They follow no road.
- **Open question:** `q-cloverdale-creek` now lists the road position as shown and the GNIS point as the other reading.

**Rebuilt and checked:**

- `build_story` changed 3 stops, 3 areas (2 of them new) and 4 journey segments, and nothing else.
- `build_vignettes` made no change.
- `downloads` refreshed the three parquet files.
- `validate`: all 9 files are fine.
- `echo_check`: 0 shared runs.

**Raised copies.** The moved legs are in the raised corridor, and the corridor (20 km each side) gains 0.04 km² and no tiles. So no relief or oblique tiles change, and no release is needed. Running the full `plan_oblique` takes hours, so `raise_some.py` in this folder (run from the repo root, with `data/` from before the change in `.scratch/before/`) did a narrower job instead:

1. It rebuilt the smoothed DEMs of the 2 strips (of 12) that hold the changed features.
2. It ran `raise_story` with base height 0.0, as the published run did.
3. It spliced only the changed features into `data/raised/`.

As a check, an unchanged stop (Cloverdale) came out at exactly its published raised position. Every other raised feature is byte-identical.

**Images:** `cloverdale-z11-before-after.png` and `cloverdale-z13-before-after.png`, with J2 in focus.

## 3. 60 fps proxy

**Method** (`tools/frame-time.mjs`):

- **Site:** the built site (`npm run build`, then `npx vite preview --port 5186`), opened in Chromium through Playwright.
- **Screen:** a mid-range Android phone, 412 × 915 CSS px at a device pixel ratio of 2.625.
- **CPU throttling:** set through the DevTools protocol (`Emulation.setCPUThrottlingRate`) to 1, 4 and 6. A fixed loop took 13.3 / 50.9 / 77.9 ms at those rates, so the throttle works.
- **Place:** the bootheel at -108.85, 31.5, which has hachures, contours, creeks, glyphs and four journeys' stops.
- **Motion:** pan 160 px right, 240 px down and back (1 s each), then zoom in one level and out again (1 s each).
- **Warm and cold:** a "warm" row follows an unthrottled pass over the same path, so it times drawing only. A "cold" row is the first pass on a fresh page, so it includes loading, parsing and uploading tiles.
- **What is recorded:** requestAnimationFrame intervals (median, p95, dropped vsyncs), and MapLibre's own main-thread draw time per frame (its `_render`).
- **Layer costs:** one layer group at a time is switched off, at 4×.

There are two GPU settings:

- **Metal:** the Mac's GPU (Apple M4 Pro). The CPU is throttled but the GPU is not, so this isolates the CPU side.
- **SwiftShader:** Chromium's software GL. It is not throttled by CDP and is much slower than any phone GPU, but it shows which layers cost the GPU most.

Raw rows: `frame-times-metal.json` and `frame-times-swiftshader.json`. Chart: `frame-times.png`.

**Results with the Mac GPU.** Every run holds 60 fps. Across all 49 runs, only one frame dropped (zoom 8, 6×, cold). MapLibre's main-thread draw time per frame, median / p95, in ms:

| View | Zoom | 1× warm | 4× warm | 6× warm | 4× cold | 6× cold |
|---|---|---|---|---|---|---|
| Flat | 8 | 0.8 / 1.1 | 3.0 / 4.1 | 4.4 / 6.2 | 3.6 / 5.4 | 5.1 / 7.1 |
| Flat | 10 | 0.6 / 0.8 | 2.2 / 3.1 | 3.2 / 4.9 | 2.3 / 3.9 | 3.3 / 5.8 |
| Flat | 12 | 0.6 / 0.8 | 2.2 / 2.9 | 3.4 / 4.9 | 2.7 / 4.0 | 4.0 / 5.8 |
| Raised | 10 | 0.6 / 0.8 | 2.1 / 2.9 | 3.4 / 5.0 | 2.6 / 3.6 | 3.8 / 5.2 |
| Raised | 12 | 0.5 / 0.7 | 1.9 / 2.9 | 3.6 / 5.1 | 2.3 / 3.2 | 3.5 / 5.0 |

The frame interval was 16.7 ms median and at most 16.8 ms p95 in every row. The worst p95 draw time, 7.1 ms at 6×, uses under half the 16.7 ms budget. On the CPU side, the map has room to spare.

**Which layers cost most.** With the Mac GPU, the median draw time at 4× (warm) drops when a layer group is off:

- **Zoom 8:** text labels cost most (3.0 down to 1.2 ms without them), then glyphs and vignettes (to 1.8), then roads, rail and boundaries (to 1.9).
- **Zoom 10:** labels (2.2 to 1.3) and the story (to 1.5) cost most.
- **Zoom 12:** contours cost most (2.2 to 1.5). The other groups are within noise, about ±0.3 ms.

**Results with software GL** (frame rate at 4×, warm):

| View | Zoom | All layers | Without the relief shading | Without hachures | Without contours |
|---|---|---|---|---|---|
| Flat | 8 | 24.0 fps | 35.7 | 23.8 | 23.9 |
| Flat | 10 | 14.2 fps | 18.0 | 17.1 | 17.4 |
| Flat | 12 | 20.1 fps | 29.5 | 22.0 | 21.3 |
| Raised | 10 | 10.5 fps | | | |
| Raised | 12 | 55.1 fps | | | |

In the flat views the GPU spends most on the relief shading (the Imhof tint, the plain paper and the hillshade), which fills every pixel. At this screen's density that is 1,082 × 2,402 pixels a frame. The Raised view at zoom 10 is the slowest case (about 10 fps), because the oblique archives draw every raised hachure stroke and crest line at once. At zoom 12 it is the fastest (55 fps), because it has no hillshade.

**What this does and does not show.**

- **CPU:** a phone whose CPU is 4 to 6 times slower than this Mac's should keep up with MapLibre's main-thread work in every case measured.
- **GPU:** the measure says nothing reliable about a phone GPU. The Metal runs are far faster than a phone. The SwiftShader runs are far slower than a phone and only show relative costs.
- **Missing from the measure:** pinch gestures, the HTML stop markers, the Tilted (3D terrain) view, Satellite and Land colour.

**Suggestions** (not done):

1. **Test on a real phone** to settle the GPU question: an Android device with Chrome remote debugging and a performance trace on the same path. A BrowserStack-style real-device session would also do.
2. **Relief shading:** if a phone struggles, try two cheaper options first:
   - drop `relief-paper` or `relief-tint` where the other already covers the ground;
   - draw the hillshade at a lower resolution (`resampling` / `tileSize`), or cap the device pixel ratio for the map canvas (`pixelRatio: Math.min(devicePixelRatio, 2)`).
3. **Raised view at zoom 9 to 11:** thin the raised strokes below zoom 11, as the flat hachures already do below 12, or start the Raised view at zoom 11.
4. **Labels at low zoom:** at zoom 8, labels are the largest CPU cost. On phones, `text-optional` or a higher `minzoom` for minor labels (contour labels, glyph heights) would cut it.

## Open questions for the owner

1. **Trap position.** Is the trap on the creek road, 8 km out of Cloverdale, the reading you want? The `inferred` 2 km circle replaces the GNIS creek point. Did the earlier "Up the creek, about 7 km north-west" note come from Bell or Hazelton? If so, the open question could credit them.
2. **Crossfence.** Is moving it onto the road halfway acceptable? The text puts it on the road, an hour from each end.
3. **Duplicate circles.** J1.13 and J2.2 now carry identical 2 km circles at the same point. Keep both (one per journey, as now), or give J2.2 none?
4. **State labels: zoom range and phone.** Should the labels start at zoom 4.5, so the phone's opening view shows them?
5. **State labels: look.** Are 55% opacity and 0.6 em spacing right, or should they be fainter still?
6. **State labels: base layer or story layer?** Should the labels stay a base layer, hidden in Satellite and Compare?
7. **Frame-rate test.** Is a real-device run worth scheduling before launch, given the GPU caveat?

## Rolling it out

- **Commit fc45976 (state names).** Merge or cherry-pick it. It adds `tiles/state_labels.py` and `site/public/labels/states.geojson`, and changes `site/src/map/style.ts` (source and layer) and `site/src/map/tokens.ts` (`fonts.smallCaps`). No tiles release is needed.
- **When the story layers change.** Rerun `uv run --project pipeline python tiles/state_labels.py`, which takes about 3 seconds. A CI check could compare its output with the committed file.
- **Commit 3923edc (Cloverdale road).** Merge or cherry-pick it. It changes:
  - `pipeline/seeds/part1-stops.csv` (CRLF line endings kept)
  - `pipeline/seeds/part1-snaps.csv`
  - `pipeline/src/crossing/build_story.py`
  - `data/` (stops, areas and journeys, their parquet copies, the raised copies, and `open-questions.json`)
  - `review/stage-1/checklist.md`

  No tiles release is needed. A later full `plan_oblique` run would recreate the same raised features.
- **The measuring scripts** (`tools/frame-time.mjs`, `tools/stage2-shots.mjs`) are optional review tooling. Neither is needed at run time.
