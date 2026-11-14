# Roadmap

Everything still open, in one place. [`design.md`](design.md) says how the site should work; this file says what is left to do and decide. When an item is done, delete it here and, if readers can see the change, add a line to [`CHANGELOG.md`](CHANGELOG.md).

Tags say who moves each item:

- **[owner]**: an action only the owner can take
- **[decide]**: a decision for the owner
- **[build]**: work that can be done once asked
- **[research]**: needs evidence not yet to hand

## 1. Launch

1. **[owner]** Merge into `main`, or launch on `/preview/`. `main` and the public root still show stage 2 with `tiles-v2`, and stages 3 to 8 are not merged.
2. **[owner]** Check the preview, which localhost cannot test: the MapTiler logo, Satellite, Topo, Compare (including in Tilted), and Satellite tint against the key's allowed origins; and a one-handed phone test.
3. **[owner]** Sign off the stage 4 place checklists (`review/stage-4/batch-a/checklist.md`, `review/stage-4/batch-b/checklist.md`) and tick the acceptance criteria (section 9 below).
4. **[owner]** Send the permission message to Joe Hazelton. A courtesy note to James Bell is optional.
5. **[decide]** How readers discuss. Cusdis was archived in July 2026. The options are Giscus (posting needs a GitHub account), Hyvor Talk (guest comments, about €50 a year), or a Tally form beside Giscus. The GitHub issue link stays for corrections.
6. **[owner]** Soft launch to a few readers, testing spoiler mode and the inferred places. Send the McCarthy Society a link as a courtesy and offer the data back. Then post on r/cormacmccarthy (draft in `private/launch/reddit-post.md`; it needs the link and two screenshots, classic and Compare) after reading the self-promotion rules, and reply in the 2024 Gaia-map thread. Log every correction in the changelog with credit.

## 2. Decisions pending

These were "open questions" in the build plan; they are project decisions, not questions about places. Questions about places are in `data/open-questions.json` and [`open-questions.md`](open-questions.md).

- **[decide] Licences.** MIT for code (except the GPL-3.0 hachure folder) and CC BY 4.0 for data and notes are in place but provisional. Confirm or change before launch.
- **[decide] Name and domain.** "Map Enough" (from the trilogy's last line) or "The Crossing: A Reading Map"; a custom domain or `jburkinshaw.github.io/crossing-map`.
- **[decide] Spoiler default.** On until set (as built) or ask on first visit only. "Show everything" confirms every time as built; the design once said once.
- **[decide] Interface language.** English only for launch, or Spanish too.
- **[decide] Portfolio framing.** Should How it's built carry the owner's name and links, or stay anonymous with a link in the footer?
- **[decide] Vignette drawing.** Draw or trace them, or commission an illustrator for a consistent set of about 30.
- **[decide] Relief tool (P2).** Is about $100 for Eduard acceptable if a test on the Peloncillos looks much better?
- **[decide] Analytics.** Cookie-free (GoatCounter or Cloudflare Web Analytics, no consent banner) or Google Analytics (acceptable, not preferred).
- **[decide] CI.** Bundle size and a Lighthouse score in the deploy workflow, written to a JSON the How it's built page reads.
- **[decide] Spoiler mode.**
  - Almost every mountain glyph is dated 1-01. Is that fine?
  - 21 reasoning texts cite later episodes. Rewrite them, or keep the notice?
- **[decide] The drawer.** It opens at half height on first load so the progress badge and search show. Open at peek instead? Which places count as "far" for off-map arrows: the next stop when off screen, or every place named in the current episode? Should the terrain tile size (WebP or 512 px) be taken on with the relief work?
- **[decide] Photos** (`review/stage-6/photos-README.md`). Drop aerial views (as now), or keep USDA orthophotos and ISS photos as a last resort for back-country places? Should the 55 places with no Wikidata link get one by search, to reach their images? And the picks themselves, in `review/stage-6/photos.csv`.
- **[decide] Vignettes** (`review/stage-6/vignettes/README.md`, questions 1–5 and 7): the she-wolf's position, an obelisk leader to a real monument, leader length at zoom 11 and over, orphan leaders, drawing size, and the next picks (the locomotive at Las Varas and the cranes are next in line).
- **[decide] Relief.**
  - Full-region relief and Raised, about 710 MB: Cloudflare R2, the preview only, or a thinner treatment?
  - Coarse relief and contours over the whole story box?
  - The corridor edge, where hachures stop in a hard line (Mesa Atravesada shows it): fade the last few kilometres, or wait for full-region relief?
  - Thinning pass labels, glyph thresholds, and Raised details.
- **[decide] Landform weights** in `pipeline/seeds/landforms.toml`: do the mesas and ridges land where expected? `review/stage-3/landforms.csv` lists each summit's scores.

### Stage 4 questions

- **[decide]** The J3 sierra loop (stops 2 to 5) is the least certain part of Part II. Is it in the right country?
- **[decide]** J6: keep Bachíniva in the line, or show it as a separate reported point (the corrido) beside Quijada's account?
- **[decide]** Ash Wednesday: the book dates Billy's arrival at Animas with the bones to Ash Wednesday, after the 15 May date in 4-05. Note it on the stop, or leave it? Bell notes the same mismatch (stage 7, item 16).
- **[decide]** Soto Máynez and Santa Ana de Babícora are two place points at one spot and their labels overlap. One label with both names needs a small change to the app or the builder.

### Translations

Details and context are in `review/stage-5/README.md`, "Open questions for the owner".

1. **[decide]** Is a whole short line (five words or fewer) acceptable as its own incipit?
2. **[decide]** A recurring word in the narration: one glossary entry for the book (as now), or one per Part?
3. **[decide]** Group a run of short lines in one exchange into one entry? It would about halve the count.
4. **[decide]** Episode page ranges: the page model could fill `pages` in `episodes.json`, which is null now.
5. **[decide]** Lines inside a tale (the blind man's wife's tale in 3-09, 32 lines) point at the place where the tale is told. Keep, or leave them null?
6. **[decide]** Two lines in 3-14 stay null. Give them the nearest stop of the search, or leave them?
7. **[decide]** Seven lines in 3-11 and 3-13 point at the Hacienda de San Diego place. Use the last San Diego stop instead?
8. **[decide]** Move `j2-volcanic-plain-ranch`'s `first_seen` to 1-08, so the eight lines spoken there (`tr-1-08-007` to `-014`) can point at it?
9. **[decide]** Should an empty `ref` in `pipeline/seeds/where-spoken.csv` clear the heuristic? Today it changes nothing, and a `none` cell in `pipeline/seeds/translations.csv` does not survive a second build.
10. **[decide]** The misprinted guide pages in Part IV (353–357 listed after 368): keep the guide's printed page in links, as now?
11. **[decide]** The spot-check list under "Pass 2", and the alguacil's house: `j3-colonia-oaxaca` (2-03) against `j2-mud-settlement` (1-09).

### Stage 7: second sources

`review/stage-7/README.md` sets out each judgement call with the evidence and a recommendation. Items 1 (Sierra de la Madera: keep ours, disagreement on the card), 8 (De Baca County to 1-08), and 15 (Veracruz, added as the state) are done. The app lists the open ones as open questions.

- **[decide]** Items 2 to 7: Casas Grandes old town or new for the five town-scene stops; the Parham house 3–6 km north of Cloverdale (moving the SK Bar estimate with it); both Cloverdale Creek stops 7 km up the creek; Cajón Bonito on the upper canyon; the Clanton–Foster draws area and the Foster Draw stop onto the draws' middle reaches and head; Starvation Canyon at its head.
- **[decide]** Items 9 to 13: add the old Nations road, Fitzpatrick Wells, and Pendleton's ranch; leave Ciénega Springs, Government Draw, and Don Arnulfo's house unmapped.
- **[decide]** Item 14: street-level places in Deming, Silver City, El Paso, Casas Grandes, and Caborca, with `maxZoom` raised from 13 to 15 (about ten network lookups).
- **[decide]** Item 16: about 20 notes paraphrased from Bell, cited by page, reviewed together for spoilers.
- **[decide]** Item 17: raise five overrides from medium to high confidence where Hazelton's pins or Bell's distances agree.
- **[build]** The data model for second sources: `bell-2000` and `reddit-gaia` source ids with licence and credit lines; a `leads` array naming any second source that points to or agrees with a feature; "Also placed by" lines on cards; "Readers disagree" where readings conflict. Points that rest on Hazelton's map alone must be tagged so they can be removed if he declines.

### Stage 8 packets (2026-11-14)

- **[decide] Interface** (`review/stage-8/ui/README.md`). The desktop controls box can cover a stop in the top-right corner: more padding in `frameStops`, or let the box fold on desktop too? "Satellite tint" or "Ground colour"? Should a click on a stop's town also open the town's card?
- **[decide] Hillshade** (`review/stage-8/lab-hillshade/README.md`). Is "Pronounced" right beside the journeys, and does it need a new decision record after 0016? Build and release the 76 MB `terrain-hi.pmtiles` (tile zoom 11), then make the site change? Add localhost to the MapTiler key so the lab can show Topo? Publish the lab, or keep it dev-only?
- **[decide] Wheeler study** (`review/stage-8/wheeler/README.md`; decision 0022 records what was adopted). Still open: spot-height format (Wheeler's bare feet, 7268, or the site's 7,268 ft), landform spelling (book or gazetteer) and whether to letter landforms the book never names, long valley names, and the test-area questions in `review/stage-9/`.
- **[decide] Streams** (`review/stage-8/streams/README.md`). Zoom 12 density; the box for order 2 streams, or a corridor (which could hint at later journeys); fetching the missing US HU8 units for full creek coverage; the braid fix in `rivers.strahler`; Mexican stream labels from toponym points.
- **[decide] Tiles v8** (`review/stage-8/tiles-v8/README.md`). Clip creeks by the lakes where they cross the Babícora lake? Capitalised, letter-spaced names for the major rivers, as on the Wheeler sheets?
- **[research]** A hachure seam near 109.3° W, 32.0° N at zoom 10, west of the Peloncillos.

## 3. Unfinished stages

- **Stage 1.**
  - Inferred areas are drafts cut from each stop's circle by a rule (decision 0020), waiting for the hand finish in `pipeline/qgis/areas.qgs`. The four low-confidence drafts that miss their pins (the two escarpments, the river camps, the wagon-road crossing) want a look first.
  - The episode summaries are drafts for the owner to edit.
- **Stage 2.**
  - Where INEGI's or NHD's network breaks, a traced river runs along Natural Earth's line for a stretch. The base build prints the total (816 km, mostly the Fuerte, Rio Grande, and Colorado, far from the story). Joining broken channel ends was measured and dropped (1.6% less). The Río Batepito's 7.8 km above Colonia Morelos remains. A draft check of every river against the valley floor was never run to the end and is parked in `private/parked/check_rivers.py`.
  - 60 fps panning on a mid-range phone is measured only by a desktop proxy (`review/experiments/stage-2/README.md`, section 3): the CPU side has room to spare; a real phone GPU is untested.
- **Stage 3.**
  - Landform weights need tuning (section 2).
  - The mountain glyphs are generated shapes with a pen treatment (`art/pen.py`); glyphs drawn wholly by hand remain open.
  - Full-region relief is not decided (section 2).
- **Stage 4.**
  - The checklists are unsigned.
  - The Animas Valley and La Babícora regions are drafts from the DEM.
  - **[research]** La Babícora's real outline. No online source has a georeferenced boundary of the Hearst estate. The best lead is a hand-drawn outline of the estate (Fig. 21, about 1:5,000,000) in Palomares Peña's 1987 UNAM thesis on land reform in three US-owned estates in Chihuahua (author's copyright: trace and cite, do not republish), checked against the ejido polygons of the Registro Agrario Nacional and the lake basin, and marked "approximate, after Palomares Peña 1987". The Diario Oficial of 17 January 1942 gives the nine lots' areas (361,390 ha in all) but no boundaries; the survey plans are in the Archivo General Agrario, by request only. Notes in `private/research/babicora/README.md`.
  - The flat and summary legs in Mexico stay schematic curves by design; the sierra and valley legs are modelled (section 4).
- **Stage 5.**
  - The 916 translation drafts are unreviewed. Decided 2026-11-13: crowd review, through a link on each line.
  - Speaker names are inconsistent; a pass is needed before the UI shows speakers.
  - `episodes.json` has no page ranges.
  - The guide links have no deep page link: a lookup from Vintage page to PDF page is not built.
- **Stage 6.**
  - No photos are picked, and the photo pipeline after the picks is not built (the proposal is in `review/stage-6/photos-README.md`).
  - The thirteen vignettes are research-based drawings in the glyphs' pen; the other candidates in design section 10 are not drawn.
  - Accessibility leftovers: the drawer handle at full height is out of thumb reach; no keyboard equivalent for hover names; no real screen-reader test.
- **Stage 7.** The open items in section 2, then `maxZoom` 15 for street-level places.
- **Stage 8.** Section 1, the stage 7 calls, street-level places, the declutter, and analytics, each as demand shows.

## 4. Modelled routes (built 2026-11-14, decision 0021)

21 sierra and valley legs are least-cost paths (`pipeline/seeds/modeled-legs.csv`, cost model lc-0.4). Left to do:

- **[decide]** Draw a modelled leg as a band (the spread between the full model and slope alone) to carry its doubt, if the line reads as too certain.
- **[research]** Period roads from the Army Map Service 1:250,000 sheets or the USGS historical topographic maps, to replace today's INEGI tracks as the road corridors on the important legs.
- **[decide]** `q-j4-one-day-ride`: the ride from San Diego to the opera camp, about 100 km in one day.
- **[build]** The local review mode (`?review=routes`) still shows the lc-0.3 experiment's lines from `review/experiments/least-cost/` (not in git), not the built ones.

## 5. Build work, by size

- **Medium:**
  - the stage 7 data model and card lines
  - the stage 7 moves, once decided
  - the photo pipeline
  - the speaker-name pass
  - guide page links
  - episode page ranges
  - off-map arrows
  - drawer thumb reach and swipe-down
  - a keyboard equivalent for hover names
  - a screen-reader test
  - the combined Soto Máynez label
  - the corridor-edge fade
  - the hand finish of the regions and the drafted areas in QGIS
- **Large:**
  - street-level places (lookups, `maxZoom` 15)
  - shipping full-region relief and Raised (hosting)
  - the remaining vignettes (design section 10)
  - hand-drawn glyphs
  - translation review by a speaker
  - road snaps for the Mexican legs
- **Small:**
  - **[owner]** Rebuild and release the Raised archives. The hachure strokes in `oblique-*.pmtiles` now take the same `Rand` and `Slope` as `relief.pmtiles`, so the Raised view thins strokes as the flat view does once rebuilt ([`releasing-tiles.md`](releasing-tiles.md)).
  - **[owner]** Review the Apache Pass glyph: its entry in `data/mountain_glyphs.geojson` is stale against what `crossing.peaks` now produces.
  - **[decide]** Stop `j2-colonia-oaxaca` is first seen in 1-09, before its place, which the book names in 1-10. `crossing.validate` allows it, because the stop's own name gives nothing away until then. Confirm, or date the stop 1-10.
  - **[decide]** The Raised view's US streams come from NHD's display scale (`visibility`), not Strahler order as on the classic map, so the two views rank streams differently.
  - **[decide]** Summits, landforms, regions, coarse hachures, and the Raised view read only `private/cache/dem/copernicus/` (18 corridor tiles). Only `tiles.build_terrain_hi` and `crossing.full_region` read `copernicus-region/` (63 more tiles). Decide whether summits and coarse relief should cover the whole story box.
  - **[build]** The creek zoom table is written twice: `MIN_ZOOM` in `tiles/creeks.py` and the matching expression in `site/src/map/style.ts`. Derive the style's from the tiles, or test that they agree.
  - **[decide]** `data/raised/*.geojson` repeats every property of the flat layers; only geometry differs. Slimming them to id and geometry changes the published format, so it waits for a decision.
  - **[decide]** Rewrite git history to drop about 102 MB of deleted `review/stage-3/sheet/` images, most of the repository's size. It needs a force-push to every branch, so it is the owner's call, and is cheapest while the history is short.
  - **[owner]** Install Inkscape and `potrace` or `vtracer`, needed for real vignettes.
  - **[build]** Revisit decision 0012 when MapTiler ships an SDK on a fixed MapLibre: `npm audit` reports the advisory until then.
  - **[owner]** The agent worktrees under `.claude/worktrees/` each have uncommitted files; look before removing them.

## 6. Places shown with a doubt

[`open-questions.md`](open-questions.md) lists each place the evidence does not settle, with what would settle it. `data/open-questions.json` holds the short form the app shows.

## 7. Prerequisites

Work does not wait for these. Where one is missing, the work builds up to that point and leaves a stub that fails loudly with the name of what is missing.

| Needed | For | State |
| --- | --- | --- |
| Inkscape, `potrace` or `vtracer` | Real vignettes | Missing |
| QGIS 4 in a micromamba environment, found through `QGIS_ENV` | Hachures (decision 0015) | Installed |
| DRM-free EPUB in `private/book/` | Episodes, mentions, translations | Present |
| MapTiler key, as the repository variable `VITE_MAPTILER_KEY` and in `site/.env.local` | Satellite and Topo | Present; restricted to the Pages origin |

## 8. Phase 2 backlog

Pick by demand, not in order.

- **Land-cover marks** among the hachures (scrub stipple, tree marks) from a land-cover dataset such as ESA WorldCover, checking its licence.
- **Cloudflare R2** for larger tiles.
- **Blender or Eduard relief.**
- **Least-cost routes and constraint-built areas.** Section 4 covers the routes; areas would come from travel-time rings, bearing sectors, viewsheds, and slope classes.
- **Rumsey overlays** with the swipe.
- **Story mode:** a pinned map with scrolling episodes.
- **A Spanish interface.**
- **Illustrator vignettes** for the remaining candidates.
- **Speaker-reviewed translations.**
- **A paid MapTiler month** around a traffic spike.
- **Analytics** (section 2).
- **Reader feedback beyond the issue link:** a form, from the card, that carries the feature id, with each accepted correction credited in the changelog.
- **Propose a different location:** from any stop, place, or area, a reader drops a pin or draws a rough area and says why (a page of the book, a source, local knowledge). Proposals carry the feature id, the geometry, and the reason, and arrive in one queue (a prefilled GitHub issue with GeoJSON at first). The owner reviews them in the local review mode, and an accepted one becomes a seed edit with the reader credited.
- **Alternative readings on the map:** where readers disagree, such as the two Sierras de la Madera, draw the other reading faintly and let readers discuss or vote.
- **"What Billy saw":** a line-drawn panorama from a chosen stop, peaks labelled, computed by marching rays over the 30 m DEM with the Earth's curvature corrected. Parked: it may be clutter.
- **Block diagrams on place cards:** pen-and-ink diagrams of key landscapes from the map's own strokes and contours, with hidden lines removed (a test renderer took about 3 s and 200–800 KB each).
- **A general declutter** across map and panel, including whether every decision and placement note belongs on the map.

## 9. Acceptance criteria

The criteria are in [`design.md`, section 11](design.md#11-acceptance-criteria). Status on 2026-11-14 (ticking is the owner's sign-off):

| Criterion | Status | Evidence |
| --- | --- | --- |
| Every feature has `certainty`, `source`, `source_licence`, `first_seen` | Met | All 1,546 features in places, stops, areas, journeys, mountain glyphs, and vignettes; `crossing.validate` enforces it through the schemas |
| Nothing past the reader's progress shows anywhere; automated test | Met | `tools/spoiler-leak.mjs` runs in CI on every deploy at four reading positions (all ten locally) and covers story layers, markers, panel text, stepping, search, cards, translations, the layer key, glyphs, vignettes, the views, the phone drawer, the progress dialog, and every page |
| Attribution where shown and on the Credits page; MapTiler logo on satellite | Mostly met | Each tile archive carries its credit; no photos are shown yet. The MapTiler logo must be checked on the preview |
| No passage of the novel in the repo or the built site | Met | `crossing.echo_check` scans tracked text and the built site (it skips in CI, where the private text is absent) |
| Downloads validate and open in QGIS | Met | `crossing.validate`; every GeoJSON and GeoParquet file opens with `ogrinfo` |
| Classic map works with MapTiler unreachable | Met | Locally MapTiler always refuses, and the classic map, views, search, and pages work |
| One-handed phone test and keyboard-only use | Mostly met | 33 of 34 keyboard checks pass (the Compare swipe needs satellite). Open items are in section 3, stage 6. The phone test is the owner's |
| $0 a month at 10,000 visits | Met by design | Pages and release assets are free; MapTiler pauses at its limits. The tile set is about 285 MB per build, and Pages' 1 GB limit counts `main` and the preview together |
