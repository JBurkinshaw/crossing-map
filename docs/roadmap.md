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
4. **[owner]** A courtesy note to James Bell is optional. (Joe Hazelton gave permission on 2026-11-16, asking only for credit.)
5. **[owner]** Make the Tally feedback form and put its id in `FEEDBACK_FORM` (`site/src/pages/format.ts`). Until then the suggestion links stay hidden. The fields are in decision 0044: hidden `kind`, `feature`, `name`, `line`, `episode`; then "What should change, and why?", a source, a name for credit, and an email, the last two optional.
6. **[owner]** Soft launch to a few readers, testing spoiler mode and the inferred places. Send the McCarthy Society a link as a courtesy and offer the data back. Then post on r/cormacmccarthy (draft in `private/launch/reddit-post.md`; it needs the link and two screenshots, vintage and Compare) after reading the self-promotion rules, and reply in the 2024 Gaia-map thread. Log every correction in the changelog with credit.
7. **[build]** Once the Reddit post is up, link it from the About page as the place to discuss the map, with a note that it may hold spoilers (decision 0044).

## 2. Decisions pending

These were "open questions" in the build plan; they are project decisions, not questions about places. Questions about places are in `data/open-questions.json` and [`open-questions.md`](open-questions.md).

- **[owner] Licences.** CC BY 4.0 for the data and notes (decision 0045) and MIT for the code (except the GPL-3.0 hachure folder) are settled; the owner confirmed MIT on 2026-11-18. Left: tick the checklist in `review/licences/README.md`, and decide whether a portfolio link on How it's built keeps the site within MapTiler's non-commercial free plan. [`licensing.md`](licensing.md) explains both licences.
- **[decide] Name and domain.** "Map Enough" (from the trilogy's last line) or "The Crossing: A Reading Map"; a custom domain or `jburkinshaw.github.io/crossing-map`.
- **[decide] Portfolio framing.** Should How it's built carry the owner's name and links, or stay anonymous with a link in the footer?
- **[decide] Vignette drawing.** Draw or trace them, or commission an illustrator for a consistent set of about 30.
- **[decide] Relief tool (P2).** Is about $100 for Eduard acceptable if a test on the Peloncillos looks much better?
- **[decide] Analytics.** Cookie-free (GoatCounter or Cloudflare Web Analytics, no consent banner) or Google Analytics (acceptable, not preferred).
- **[decide] Spoiler mode.**
  - Almost every mountain glyph is dated 1-01. Is that fine?
  - 21 reasoning texts cite later episodes. Rewrite them, or keep the notice?
  - Rename the ids that name an event (`j4-shooting`, `j7-boyds-grave`, `vignette-taking-the-girl` and others, decision 0036)? They show in the published data and the sprite index.
- **[decide] The drawer.** It opens at half height on first load, on the stop's text (decision 0060). Open at peek instead? Which places count as "far" for off-map arrows: the next stop when off screen, or every place named in the current episode? Should the terrain tile size (WebP or 512 px) be taken on with the relief work?
- **Photos** (`review/stage-6/photos-README.md`). Settled 2026-11-18: aerial views stay dropped, and the places with no Wikidata link get none. The owner's 75 picks for 44 places are on the cards (decision 0067). Left: the "today" captions of design section 10, and a check of the hand-set authors in `pipeline/seeds/photo-text.csv`.
- **[decide] Vignettes** (`review/stage-6/vignettes/README.md`). 155 are drawn, and placement is decided (decisions 0026, 0066, 0073, 0075, 0077 and 0080). Of the candidates in design section 10, the Mormon store at Colonia Morelos, the oxen (the book's ox scene has no cart) and a Babícora Hereford are drawn. Four are left out as an existing drawing covers them or the book does not have them: Bird (Billy and the dog at Cloverdale), the one-eyed horse at Bacerac (the book has none, and Keno there is drawn), the Noroeste locomotive (the night train at Las Varas) and the guitar and the corrido (the corridero at Temósachic, as the book has no Bachíniva). The 14 journey vignettes the owner adopted on 2026-11-18 are drawn, each at a point along its leg (decision 0066). On 2026-11-19 the owner asked for 150 in all, the big scenes first: 79 more are drawn (decision 0073). Still open: redraw the ones that read only roughly at map size.
- **[decide] Relief.**
  - Full-region relief and Oblique, about 710 MB: Cloudflare R2, the preview only, or a thinner treatment?
  - Coarse relief and contours over the whole story box?
  - The corridor edge, where hachures stop in a hard line (Mesa Atravesada shows it): fade the last few kilometres, or wait for full-region relief?
  - Thinning pass labels, glyph thresholds, and Oblique details.

### Stage 4 questions

- **[decide]** The J3 sierra loop (stops 2 to 5) is the least certain part of Part II. Is it in the right country?
- **[decide]** J6: keep Bachíniva in the line, or show it as a separate reported point (the corrido) beside Quijada's account?
- **[decide]** Ash Wednesday: the book dates Billy's arrival at Animas with the bones to Ash Wednesday, after the 15 May date in 4-05. Note it on the stop, or leave it? Bell notes the same mismatch (stage 7, item 16).
- **[decide]** Soto Máynez and Santa Ana de Babícora are two place points at one spot and their labels overlap. One label with both names needs a small change to the app or the builder.

### Translations

Details and context are in `review/stage-5/README.md`, "Open questions for the owner".

1. **[decide]** Is a whole short line (five words or fewer) acceptable as its own incipit?
2. **[decide]** Episode page ranges: the page model could fill `pages` in `episodes.json`, which is null now.
3. **[decide]** Should an empty `ref` in `pipeline/seeds/where-spoken.csv` clear the heuristic? Today it changes nothing, and a `none` cell in `pipeline/seeds/translations.csv` does not survive a second build.
4. **[decide]** The spot-check list under "Pass 2", and the alguacil's house: `j3-colonia-oaxaca` (2-03) against `j2-mud-settlement` (1-09).

Seven more were settled as built on 2026-11-16, and the packet lists them under "Owner's answers".

### Stage 7: second sources

`review/stage-7/README.md` sets out each judgement call with the evidence and a recommendation. Items 1 (Sierra de la Madera: keep ours, disagreement on the card), 8 (De Baca County to 1-08), and 15 (Veracruz, added as the state) are done. The app lists the open ones as open questions.

- **[decide]** Items 2 to 7: Casas Grandes old town or new for the five town-scene stops; the Parham house 3–6 km north of Cloverdale (moving the SK Bar estimate with it); both Cloverdale Creek stops 7 km up the creek; Cajón Bonito on the upper canyon; the Clanton–Foster draws area and the Foster Draw stop onto the draws' middle reaches and head; Starvation Canyon at its head.
- **[decide]** Items 9 to 13: add the old Nations road, Fitzpatrick Wells, and Pendleton's ranch; leave Ciénega Springs, Government Draw, and Don Arnulfo's house unmapped.
- **[decide]** Item 14: street-level places in Deming, Silver City, El Paso, Casas Grandes, and Caborca, with `maxZoom` raised from 13 to 15 (about ten network lookups).
- **[decide]** Item 16: the "Local history" line on the cards is built (decision 0071). The 24 notes drafted from Bell, cited by page, wait for the owner's review together for spoilers.
- **[decide]** Item 17: raise five overrides from medium to high confidence where Hazelton's pins or Bell's distances agree.

### Stage 8 packets (2026-11-14)

- **[decide] Interface** (`review/stage-8/ui/README.md`). "Satellite tint" or "Ground colour"? Should a click on a stop's town also open the town's card? (The controls box covering a stop is settled: the box now folds under one Map button on desktop too.)
- **[decide] Hillshade** (`review/stage-8/lab-hillshade/README.md`; MapTiler-like adopted, decision 0025). Build and release the 76 MB `terrain-hi.pmtiles` (tile zoom 11), then make the site change? Add localhost to the MapTiler key so the lab can show Topo? (The lab stays dev-only.)
- **[decide] Wheeler study** (`review/stage-8/wheeler/README.md`; decisions 0022 to 0024 record what was adopted). Still open: long valley names, and the test-area questions in `review/stage-9/`.
- **[decide] Streams** (`review/stage-8/streams/README.md`). Zoom 12 density; the box for order 2 streams, or a corridor (which could hint at later journeys); fetching the missing US HU8 units for full creek coverage; the braid fix in `rivers.strahler`; Mexican stream labels from toponym points.
- **[decide] Tiles v8** (`review/stage-8/tiles-v8/README.md`). Clip creeks by the lakes where they cross the Babícora lake? Capitalised, letter-spaced names for the major rivers, as on the Wheeler sheets?
- **[research]** A hachure seam near 109.3° W, 32.0° N at zoom 10, west of the Peloncillos.

### The UX review of 17 November 2026

Decisions 0060 to 0062 record what was built. Still open:

- **[decide] A preview image for shared links.** The page has `og:title` and `og:description` and no `og:image`, so a link on Reddit or in a chat shows as text. Wanted: 1200 by 630 px from the vintage map. Which view should it show?
- **[decide] Zoom buttons on phones.** They were dropped with the scale (decision 0060). A pinch zooms, a double tap zooms in and Home zooms out to the journey, but nothing zooms out one step with a single tap, which WCAG 2.5.1 asks for. Bring back zoom out alone, both, or neither?
- **[decide] The base map's roads read as routes.** They are thin dashed lines, and with the other journeys hidden on a phone they look like faint journeys. Redraw them (dotted, or in the hachures' brown), or leave them?
- **[decide] Units.** They are in the Map menu with the views. They belong with the reader's tools, but the drawer has no spare place for them.
- **[build] How it's built: the content,** then links from each method to the map in the state that shows it (the Oblique view, the hachures at zoom 12, an inferred area with its reasoning). The page is now linked from the panel's header. The owner wants to work on what it says first.
- **[build] The first load on a phone.** `tools/first-load.mjs` on 18 November 2026, three runs with Lighthouse's mobile throttling: map ready in 14.7 s, drawn in 16.5 s, 2,135 kB in 35 requests. By size: the 2x sprite 740 kB, terrain tiles 578 kB, script 421 kB, story data 249 kB. Desktop, unthrottled: 1.6 s. The sprite is the first thing to cut: split the drawings from the summit glyphs so they load after the map, or quantise the PNG (needs `pngquant` or `oxipng`, and `spreet` to rebuild). The terrain tile size is the second (see "The drawer" above). The story data is already at five decimal places, and the translations are 30 kB gzipped, so neither is worth deferring.
- **[owner] In-app browsers.** Open the preview from a Reddit post and a Messenger chat on iOS and Android. Check the drawer's heights, that reading progress survives a second visit, and whether two fingers can turn the map (there is no control to turn it north again).
- **[owner] Usability tests before the Reddit post.** Three rounds, three readers from each audience (a first-time reader, a McCarthy reader, a map person), on their own phones, thinking aloud, with fixes between rounds. Tasks: say what the site is after five seconds, set the map for page 60 so it spoils nothing, find where the wolf crosses the border, say what a dashed line means, see a place on satellite, find out how sure the map is about a stop. Note whether each finds the key and the Map button unprompted.
- **[owner] A screen-reader test** with VoiceOver and NVDA, starting from the Itinerary page (decision 0062).
- **[owner] Check on the preview:** Compare's two step buttons and its spoken value, which localhost cannot show.

## 3. Unfinished stages

- **Stage 1.**
  - Inferred areas are drafts cut from each stop's circle by a rule (decision 0020), waiting for the hand finish in `pipeline/qgis/areas.qgs`. The four low-confidence drafts that miss their pins (the two escarpments, the river camps, the wagon-road crossing) want a look first.
  - The episode summaries are drafts for the owner to edit.
  - Stop synopses (decision 0051): all 171 are drafts for the owner to edit in `pipeline/seeds/stops.csv`. `review/synopses/part1.csv` to `part4.csv` mark which of them tell a later turn of their episode.
- **Stage 2.**
  - Where INEGI's or NHD's network breaks, a traced river runs along Natural Earth's line for a stretch. The base build prints the total (816 km, mostly the Fuerte, Rio Grande, and Colorado, far from the story). Joining broken channel ends was measured and dropped (1.6% less). The Río Batepito's 7.8 km above Colonia Morelos remains. A draft check of every river against the valley floor was dropped on 2026-11-16; its script, `private/parked/check_rivers.py`, can be deleted.
  - 60 fps panning on a phone is covered by the owner's phone test (section 1).
- **Stage 3.**
  - The mountain glyphs are generated shapes with a pen treatment (`art/pen.py`). Glyphs drawn wholly by hand were dropped on 2026-11-16.
  - Full-region relief is not decided (section 2).
- **Stage 4.**
  - The checklists are unsigned.
  - The Animas Valley and La Babícora regions are drafts from the DEM.
  - **[research]** La Babícora's real outline. No online source has a georeferenced boundary of the Hearst estate. The best lead is a hand-drawn outline of the estate (Fig. 21, about 1:5,000,000) in Palomares Peña's 1987 UNAM thesis on land reform in three US-owned estates in Chihuahua (author's copyright: trace and cite, do not republish), checked against the ejido polygons of the Registro Agrario Nacional and the lake basin, and marked "approximate, after Palomares Peña 1987". The Diario Oficial of 17 January 1942 gives the nine lots' areas (361,390 ha in all) but no boundaries; the survey plans are in the Archivo General Agrario, by request only. Notes in `private/research/babicora/README.md`.
  - Legs on a road or river the book names are traced on it (decision 0032); the sierra and valley legs are modelled (section 4); the flat and summary legs in Mexico stay curves by design.
- **Stage 5.**
  - The 916 translation drafts are unreviewed. Decided 2026-11-13: crowd review, through a link on each line.
  - Speaker names are inconsistent; a pass is needed before the UI shows speakers.
  - `episodes.json` has no page ranges.
  - The guide links have no deep page link: a lookup from Vintage page to PDF page is not built.
- **Stage 6.**
  - The 75 picked photos are on the place and stop cards and the Credits page (decision 0067). Their "today" captions are not written.
  - The 155 vignettes are research-based drawings in the glyphs' pen (section 2, Vignettes).
  - Accessibility leftovers: the drawer handle at full height is out of thumb reach, and there is no keyboard equivalent for hover names. The screen-reader test is in section 2.
- **Stage 7.** The open items in section 2, then `maxZoom` 15 for street-level places.
- **Stage 8.** Section 1, the stage 7 calls, street-level places, the declutter, and analytics, each as demand shows.

## 4. Modelled routes (built 2026-11-14, decision 0021)

20 sierra and valley legs are least-cost paths (`pipeline/seeds/modeled-legs.csv`, cost model lc-0.4); J7 leg 41 is now traced on the Río Casas Grandes (decision 0032). Left to do:

- **[research]** Period roads from the Army Map Service 1:250,000 sheets or the USGS historical topographic maps, to replace today's INEGI tracks as the road corridors on the important legs.
- **[decide]** A faint base layer of the roads the book names (the Douglas to Cloverdale road, Apache Pass Road, the Casas Grandes to Madera road and the rest in `snaps.csv`), drawn as dotted period trails, each cut to 10 km beyond its traced legs and shown from its first leg's episode. Scoped 2026-11-16 and held.
- **[decide]** `q-j4-one-day-ride`: the ride from San Diego to the opera camp, about 100 km in one day.

## 5. Build work, by size

- **Medium:**
  - the stage 7 data model and card lines
  - the stage 7 moves, once decided
  - the speaker-name pass
  - guide page links
  - episode page ranges
  - off-map arrows
  - drawer thumb reach and swipe-down
  - a keyboard equivalent for hover names
  - the combined Soto Máynez label
  - the corridor-edge fade
  - the hand finish of the regions and the drafted areas in QGIS
- **Large:**
  - street-level places (lookups, `maxZoom` 15)
  - shipping full-region relief and Oblique (hosting)
  - translation review by a speaker
  - more traced legs (decision 0032): roads in US counties with no cached TIGER file, roads INEGI does not name, J7 leg 42 (its stop sits on a side channel), and the rest of `private/review/snap-candidates.md`
- **Small:**
  - **[decide]** The Oblique view's lean is 4 (decision 0040). If the larger shift reads badly, or the story's pins jump too far between Flat and Oblique, try 3.
  - **[decide]** Land cover covers the Oblique corridor only (decision 0040). Extending it to the story box needs the DEM of `copernicus-region/` and makes `landcover.pmtiles` larger.
  - **[owner]** Review the Apache Pass glyph: its entry in `data/mountain_glyphs.geojson` is stale against what `crossing.peaks` now produces.
  - **[decide]** Stop `j2-colonia-oaxaca` is first seen in 1-09, before its place, which the book names in 1-10. `crossing.validate` allows it, because the stop's own name gives nothing away until then. Confirm, or date the stop 1-10.
  - **[decide]** The Oblique view's US streams come from NHD's display scale (`visibility`), not Strahler order as on the vintage map, so the two views rank streams differently.
  - **[decide]** Summits, landforms, regions, coarse hachures, and the Oblique view read only `private/cache/dem/copernicus/` (18 corridor tiles). Only `tiles.build_terrain_hi` and `crossing.full_region` read `copernicus-region/` (63 more tiles). Decide whether summits and coarse relief should cover the whole story box.
  - **[build]** The creek zoom table is written twice: `MIN_ZOOM` in `tiles/creeks.py` and the matching expression in `site/src/map/style.ts`. Derive the style's from the tiles, or test that they agree.
  - **[decide]** `data/oblique/*.geojson` repeats every property of the flat layers; only geometry differs. Slimming them to id and geometry changes the published format, so it waits for a decision.
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

- **The Oblique view's generator as its own repository.** The owner wants to break `crossing.plan_oblique` (about 700 lines) out into a separate, reusable repository. Today it leans on this project's modules: the tile grid, corridor and DEM preparation in `crossing.hachures`, the DEM notice in `crossing.dem`, land cover in `crossing.landcover`, the streams in `crossing.hydro` and `crossing.basemap`, `crossing.tiling.tippecanoe`, and the story data in `data/`. The split needs those passed in as inputs (a DEM, a region, line layers) instead of imported, and a licence for the new repository (MIT, as here, unless it takes in GPL code). Noted 2026-11-16.
- **Historic roads, traced.** Trace the roads the book's riders use (about 30 to 60 lines) from the USGS 1:62,500 sheets of 1917 to 1923, as the Wheeler test area did for 9 roads (`review/stage-9/wheeler-roads/`). About 24 to 48 hours by hand in QGIS for the 12 core sheets; by agent, about 1 to 2.5 million tokens. Mexico has no usable period source yet. Shelved by the owner on 14 November 2026 as a later improvement.
- **Land-cover marks** among the hachures (scrub stipple, tree marks) from a land-cover dataset such as ESA WorldCover, checking its licence.
- **Cloudflare R2** for larger tiles.
- **Blender or Eduard relief.**
- **Least-cost routes and constraint-built areas.** Section 4 covers the routes; areas would come from travel-time rings, bearing sectors, viewsheds, and slope classes.
- **Story mode:** a pinned map with scrolling episodes.
- **Illustrator vignettes** for the remaining candidates.
- **Speaker-reviewed translations.**
- **Analytics** (section 2).
- **Alternative readings on the map:** where readers disagree, such as the two Sierras de la Madera, draw the other reading faintly and let readers discuss or vote. A first step is built (2026-11-18): an open question can carry a ring for its other reading, shown on request from the card, and a folded "More about this". Only `q-eastern-escarpment` uses it so far. The J1 questions (`q-san-luis-gap`, `q-animas-crossing`, `q-clanton-foster`) are the next candidates.
- **Clue tests as data, run by one command.** Turn each one-off placement experiment (the escarpment viewshed, the landform position checks) into a small spec in `pipeline/seeds/clue-tests/`: the stop, the clue paraphrased, the episode, a test kind (view, position, distance or time, direction, order) and its parameters. One runner, `crossing.clues`, would run every spec and write the same outputs each time (results, a figure, a one-line verdict), with an input hash so `crossing.validate` can say when a result is stale. The experiment READMEs would follow one template (Question, Clue, Test, Result, Limits, Options, Decision). Worth doing only if outside interest in contributing tests is high. Shelved by the owner on 18 November 2026.
- **Outside contributions to placement.** Builds on the clue tests: a script that fetches only the open data a spec needs (Copernicus DEM tiles, GNIS, GeoNames, INEGI, Natural Earth) so contributors need neither the book nor `private/`, a pull-request template asking for the spec, its results and the proposed open-question wording, a CI job that reruns a changed spec and attaches its figure, and a short placement playbook for AI agents (the spec format, the rules on the novel's text and open data, never moving a stop). Needs a decision record, since the project merges stage branches without pull requests today. Shelved by the owner on 18 November 2026.
- **A general declutter** across map and panel, including whether every decision and placement note belongs on the map.

## 9. Acceptance criteria

The criteria are in [`design.md`, section 11](design.md#11-acceptance-criteria). Status on 2026-11-14 (ticking is the owner's sign-off):

| Criterion | Status | Evidence |
| --- | --- | --- |
| Every feature has `certainty`, `source`, `source_licence`, `first_seen` | Met | All 1,546 features in places, stops, areas, journeys, mountain glyphs, and vignettes; `crossing.validate` enforces it through the schemas |
| Nothing past the reader's progress shows anywhere; automated test | Met | `site/src/spoiler/leak.test.ts` runs the spoiler filters on the data at all 43 reading positions with the site's tests, and `tools/spoiler-leak.mjs` walks the site through all 41 episodes and checks story layers, map filters, markers, panel text, every stop, links and saved places past progress, "Read on", search, cards, translations, the layer key, glyphs, vignettes, the views, the phone drawer, the progress dialog, and every page (decision 0054). CI runs both before every deploy |
| Attribution where shown and on the Credits page; MapTiler logo on satellite | Mostly met | Each tile archive carries its credit, and each photo has a TASL credit on its card and on the Credits page (decision 0067). The MapTiler logo must be checked on the preview |
| No passage of the novel in the repo or the built site | Met | `crossing.echo_check` scans tracked text and the built site (it skips in CI, where the private text is absent) |
| Downloads validate and open in QGIS | Met | `crossing.validate`; every GeoJSON and GeoParquet file opens with `ogrinfo` |
| Vintage map works with MapTiler unreachable | Met | Locally MapTiler always refuses, and the vintage map, views, search, and pages work |
| One-handed phone test and keyboard-only use | Mostly met | 33 of 34 keyboard checks pass (the Compare swipe needs satellite). Open items are in section 3, stage 6. The phone test is the owner's |
| $0 a month at 10,000 visits | Met by design | Pages and release assets are free; MapTiler pauses at its limits. The tile set is about 285 MB per build, and Pages' 1 GB limit counts `main` and the preview together |
