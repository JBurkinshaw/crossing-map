# Stage 9: the owner's decisions of 14 November 2026, rolled out

This packet covers the seven decisions in the handoff of 14 November 2026, carried out in its suggested order on `stage/4-rest-of-book`. Each section says what changed, where to look, and what is still open. Screenshots are in `private/review/stage-9/` (git ignores review images).

**The plan has moved.** The repository cleanup merged before this work started. It split `docs/plan.md` into `docs/design.md` (how the site works) and `docs/roadmap.md` (open work and decisions), and deleted `review/outstanding.md`. Decisions are recorded in those two files and in `docs/decisions/`; records 0020 to 0023 are new.

## How to test

```bash
cd site && npm run dev
```

- `/`: the classic map. Look at the cream paper, the brown-black hachures, the river capitals, landform names along their axes, spot heights from zoom 10, the modelled legs (long dashes), an inferred area's card ("How this area was drawn"), the vignettes and their labels, and the Credits page's Drawings.
- `/?review=routes`: the least-cost review mode. It still shows the lc-0.3 experiment's lines from `review/experiments/least-cost/`, not the built ones.
- `/lab.html#wheeler`: the Wheeler lab. Press "Test area: bootheel and Bavispe", then the four test-area toggles.

Checks run before the last commit: `crossing.validate`, `crossing.echo_check` (0 shared runs), `crossing.downloads --check`, ruff, pytest, `tsc`, oxlint, `npm run build`, `npm test`, and the spoiler-leak test (see the end).

## 1. Stage 2 leftovers: merged

The state names and the Cloverdale Creek road are in (`3a142dd`). The cleanup had merged the Part I seeds into `pipeline/seeds/stops.csv` and `snaps.csv`, so the trap, the crossfence and the two road snaps moved there. The packet's defaults stand: the trap and the crossfence stay on the creek road, each journey keeps its own circle, and the state labels start at zoom 5 as a base layer at 55% opacity. `tiles.state_labels` runs with the story build (`make story`).

## 2. Areas and least-cost routes

**Areas** (decision 0020, `90ba31e`, hardened in `7279b98`). `crossing.area_drafts` cuts each stop's circle by a written rule and writes `pipeline/seeds/areas.geojson`, which `crossing.build_story` reads. A rerun needs `--force` and keeps any area marked `checked`. The QGIS project for hand edits is now `pipeline/qgis/areas.qgs`, and it edits the seed. 59 areas cover 7,322 km² instead of 14,566.

- **Pins.** Nine medium- or high-confidence stops moved onto their drafts, by 1.4 to 7.3 km: the mud-house settlement, Huisiachepic, the Guadalupe pass, San Simon, the horses, the J7 lake camp, the Casas Grandes River, the attack, and the waystation. The four low-confidence drafts that miss their pins keep the pin: the two escarpments, the river camps, and the wagon-road crossing.
- **Cards.** Each area's card says it is a draft made by a rule from data, not drawn by hand from a source, and gives the rule. Nine areas say a straight line between towns stands in for an old road that needs a historical source. Every card invites a correction through the existing issue link. No confidence is shown.
- **La Babícora.** The DEM draft stays. A research pass found no georeferenced boundary online. The best lead is the hand-drawn outline in Palomares Peña's 1987 UNAM thesis (Fig. 21, about 1:5,000,000, author's copyright: trace and cite, do not republish), checked against the agrarian registry's ejido polygons. The Diario Oficial of 17 January 1942 gives the nine lots' areas (361,390 ha) but no boundaries. The survey plans are in the Archivo General Agrario, by request only. Notes: `private/research/babicora/README.md`; roadmap section 3.

**Least-cost routes** (decision 0021, `5c32dba`). The 21 legs on the experiment's "works" list are modelled paths. `crossing.least_cost` is a build module, the legs are in `pipeline/seeds/modeled-legs.csv`, and results are cached by their inputs. Cost model lc-0.4 is the experiment's lc-0.3 with INEGI's unpaved tracks and footpaths (Red Nacional de Caminos 2024, a 720 MB download, credited) as the road corridors in place of today's highways. A modelled leg is drawn in long dashes, has a key entry, and its card says "Modelled path, not the book's". How it's built explains the model and its doubt.

- **J4 legs 19 and 20** follow the story. The leg's note and a new open question (`q-j4-one-day-ride`) say the ride is about 100 km in one day, some 16 hours at a walk by lc-0.4. The experiment's 19 hours came from lc-0.3.
- **Stops moved by the areas work** (the attack, the Casas Grandes River) are routed from their new pins.

## 3. Glyphs and vignettes

**Glyphs** (`96c4b42`). Variant B's pen is in `art/pen.py` and `art/glyphs/make_glyphs.py`. The 168 SVGs came out byte-identical to the reviewed variant B. One glyph has since changed, `peak-04-flip`, where a short hatch no longer overshoots its end.

**Vignettes** (`10ec657`). There are 13 research-based drawings in two inks, drawn with the same pen (`art/vignettes/ink.py`, `make_vignettes.py`, the traced outlines in `art/vignettes/traced/`). The seed gains `label` (italic, under each drawing) and `credit`. The Credits page lists credits only for the drawings the reader has reached, because a subject can give the story away. The build needs the new `art` extra (svgelements). A contact sheet is at `private/review/stage-9/main/vig-sheet.png`.

These keep the packet's defaults (listed for the owner in the summary below):

- present size, not 1.3x;
- the labels as written;
- the traced Trinity cloud with rays;
- Paquimé closer to today's walls;
- the San Diego and pit renames (done: "The San Diego house front, L. T." and "The cockpit at the hacienda");
- the bent wolf outline for the dog;
- the two drawings after CC BY-SA 3.0 images treated as derivatives, so their credit says the drawing is shared under CC BY-SA 3.0.

## 4. Wheeler rollout on the site

Decision 0022 (`f09873f`) covers the following.

- **Paper.** Sheet 70A's cream for the paper, the Mexico side and the paper above zoom 10. The sprite's knock-out paper matches. The site's panels keep their own paper.
- **Hachures.** Wheeler's brown-black (`#2e2010`) with slope contrast at 0.5. At zooms 9 to 11 around the Peloncillos, the Animas and the Pilares, the journey lines and labels stay on top (`private/review/stage-9/main/`).
- **Rivers.** The main rivers are in spaced roman capitals and drawn wider by Natural Earth rank. Creek labels are a size smaller.
- **Spot heights.** These show from zoom 10 only, a change from the packet: at zoom 9 every unnamed summit's numeral crowded the map.
- **Creeks** keep their Strahler-order widths and lighter intermittent lines from tiles-v8. They already taper by rank, and Wheeler's dotted washes would undo that rule.

**Landform names along their axes** (decision 0023, `fca9914`). The type agent built `crossing.landform_axes` and `data/landforms.geojson` (313 lines). The site letters the 17 landforms the book names from zoom 7, with the reader's progress, and their point labels step aside. It letters the gazetteers' landforms from zoom 10. It leaves out the 93 Sierra Madre lines guessed from the DEM until someone reviews them. The type agent found the stage 8 packet's GMBA claim wrong: the standard download has no separate Animas, Hatchet or Florida ranges, so most ranges are placed from the DEM and the hand-edit table (`pipeline/seeds/landform_axes.toml`) matters more than expected.

## 5. The Wheeler test area, in the lab only

Four cards, each built by a subagent in its own worktree and merged. Each has its own packet:

- `wheeler-type/`: the type hierarchy in three faces. None of the six named passes has a base-map road within 1 km, so pass names run across the saddle.
- `wheeler-places/`: 60 water places and stations from zoom 11 (26 springs, 29 ranches, 5 stations), a 15′ graticule with labels in a margin band, and the frame and cartouche rule as CSS ready to move into the site.
- `wheeler-roads/`: 9 roads traced by hand from the 1918 Cienega Springs and Animas Peak sheets (USGS, public domain), and the Butterfield trail clipped from the NPS data, in `pipeline/seeds/roads/test-area.geojson`. Two book mileages are on the lines.
- `wheeler-hachures/`: a Wheeler-style hachure build for the test area (`crossing.hachures --style wheeler --bbox ... --out ...`; production unchanged). It leaves crests as white partings (ridges by flow accumulation on the inverted DEM), keeps flats blank, packs shorter strokes on steep ground, and draws rim combs. It covers 13,971 km² in 29 minutes, with 600,000 strokes and a 20.9 MB archive (`tiles/out/lab-wheeler-hachures.pmtiles`, installed locally, not released). Ink cover at zoom 11 is 5.6% on gentle ground (Wheeler about 5%) and 23% in the combs (23%), but only 26% on steep ground (40 to 50%). Summit dots hide inside the partings, and there are few rims. The whole corridor would take about 1 to 1.5 hours at 9 jobs and make about 97 MB, which would need splitting. With the full brown-black build, landform names and glyph labels sink into the dense strokes and want a 2 px halo; the site's milder contrast (0.5) does not show this.

**Has the historical road dataset made progress?** Until today, only research: the roads plan in the Wheeler packet listed sources and licences, with nothing downloaded or traced. Today the test area has its first traced roads (above) and a cost estimate for a full network: about 2 to 4 hours per 1:62,500 sheet in QGIS. That is 24 to 48 hours for the 12 core sheets where the riders go, or 100 to 200 hours for all 51 pre-1946 sheets from Douglas to El Paso. Mexico has nothing yet: the 1918 sheets stop at the border, and the Army Map Service sheets are coarse (F401, 1:500,000) or not confirmed. Separately, INEGI's modern road network now serves as the least-cost corridors.

## 6. Landforms: the trial is dropped

The DEM tuning trial is removed from the working tree: `landform_trial.py`, `geomorphons.py`, `tools/landform-trial-sheet.mjs`, the packet `review/experiments/landforms/`, and the stray `review/stage-3/landforms/` sheet. All are parked in `private/parked/landforms-experiment/`. None of them was ever committed.

`data/mountain_glyphs.geojson` is **not rebuilt**. The handoff asks for a one-line confirmation first (see the open questions).

## 7. Housekeeping

- Experiment outputs that the build no longer needs are parked under `private/parked/` (areas, glyphs, vignettes, least-cost, landforms), together with `tiles/check_rivers.py`, which never ran to the end.
- The roadmap, the changelog, the design document, the pipeline guide and the data sources are updated. `review/outstanding.md` no longer exists, so its role is the roadmap's.
- An independent review of the committed code found no spoiler leaks and no style-expression errors. Its edge cases are fixed in `7279b98`.

## The owner's answers (14 November 2026, evening) and what followed

- **Landform glyphs:** yes. A glyph's shape now comes from the gazetteer's name and feature code (`use_dem = false` in `pipeline/seeds/landforms.toml`; Cerro and Sierra added; the prior lowered so any gazetteer word wins). 145 summits the DEM had made domes or mesas are now peaks, and six summits named as hills are domes. Glyph names are a size larger (12 px), and spot heights are marginally larger (10.5 px).
- **Vignettes:** the defaults stand; the labels are a size larger (11 to 13 px).
- **Wheeler:** the site's height format stays, every landform line is published (the Sierra Madre lines included), and the side panels take the cream paper. Landform names get a wider halo over dense hachures.
- **Hachures:** the Wheeler build covers the whole journeys corridor (87 tiles, 81,722 km², 2.8 million strokes, 68 minutes at 9 jobs), packed into `relief-wheeler.pmtiles` (zooms 10 and 11, 64 MB) and `relief-wheeler-12.pmtiles` (35 MB). The site draws them inside the corridor (decision 0024; packet `wheeler-hachures-corridor/`). The production hachures are kept, cache and archives, and come back with `HACHURE_SET = 'production'` in `site/src/map/relief.ts`. Still weak, as in the test box: steep ground at 26% ink against Wheeler's 40 to 50%, a speckled zoom 10, few rims; the Raised view keeps production-style strokes, and the corridor edge is now a change of style.
- **Hillshade:** the lab's MapTiler-like preset (decision 0025). The sharper 76 MB terrain is not built.
- **Vignettes:** each drawing stands on the stop or place it is for and is set beside the pin on its side, close at every zoom, with no leader lines; the key says its position is approximate (decision 0026). Near Casas Grandes and San Diego drawings sit under place names, which draw on top.
- **Historic road tracing:** shelved as a Phase 2 improvement (roadmap section 8).
- **Spoiler fixes:** How it's built no longer names places the reader may not have reached, and the spoiler test treats gazetteer landforms dated 1-01 as it treats glyphs.
- **The hillshade lab** is still at `/lab.html#hillshade`. Its questions are still open (roadmap section 2): a record for "Pronounced", the 76 MB sharper terrain, localhost on the MapTiler key, and publishing the lab.

## Open questions still open

1. **Test-area cards:** the questions in each packet in `review/stage-9/wheeler-*/`.
2. **La Babícora:** trace the 1987 thesis outline as an approximate region, or request the lot plans from the Archivo General Agrario.
3. **Routes:** draw modelled legs as a band to carry their doubt?
4. **Hachures:** push steep ground towards Wheeler's 40 to 50% ink (about twice the Sierra run time), widen summit dots, and decide what zoom 10 should show. Retire the production set once the Wheeler one has been seen on the preview.
5. **Sharper terrain:** build and release `terrain-hi.pmtiles` (76 MB) for the rest of the MapTiler look above zoom 10?
