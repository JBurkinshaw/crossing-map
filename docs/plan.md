# The Crossing reading-guide map: build plan and Claude Code handoff (v5)

11 November 2026. Supersedes v4.

**What changed in v5.** A verification pass before the build starts; no change of scope. Checked against live documentation, the npm registry, the hachure script's source and this machine. The corrections: (1) MapTiler counts sessions only through its own SDK, so satellite uses MapTiler SDK JS in a lazily created map (5.3); (2) PMTiles cannot be both git-ignored and deployed from the repo, so tiles ship as GitHub Release assets that the deploy workflow downloads (4.2, 11); (3) Huffman's script takes slope as a percentage of each raster's own range and spacing in pixels, so the headless copy needs more than a path argument (5.2); (4) the Cartographers' Guild robots file disallows all automated agents, so the Playwright route is dropped and reference images stay out of the public repo (5.1, 5.4); (5) GeoParquet is one file per layer; (6) the Vite glob for decision records pointed outside the app root; (7) the Trinity distance was wrong; (8) leftover "milestone" references now name stages; (9) a prerequisites list (11). Details are marked "v5" where they change a decision.

**v5 revision, same day, after your review.** (a) The Guild is browsed by an automated headed browser with its own profile, at your direction (5.1). (b) Distances are computed with pyproj on the WGS 84 ellipsoid from cited coordinates, by a script kept in the repo (2.4, 11). (c) `@vis.gl/react-maplibre` is a trial with a stated fallback to plain MapLibre GL JS (4.2). (d) QGIS comes from your micromamba environment (11). (e) Work starts without waiting for prerequisites: each missing one becomes a stub and a line in `TODO-prerequisites.md` (11). (f) Fine hachures start with the corridor proposal; the full-region run is deferred (5.2). (g) Elevation is split by use: AWS Terrain Tiles, repacked into our own archive, for the browser hillshade; Copernicus GLO-30 for hachures and peaks (3, 4.2, 5.2). (h) Reader feedback on content is a Phase 2 item (11).

**What changed in v4.** Hachure styles from Carl Churchill's typology, with a revised relief experiment. A decision record for using Huffman's GPL-3.0 hachure script. Relief is now generated hachures plus hand-style mountain glyphs on significant peaks, with hillshade kept only as an option in a side-by-side experiment. The build plan is restructured into seven stages, each ending in a review packet you can check in under half an hour.

**What changed in v3.** A two-phase plan: a quick, good-quality first release, and a list of upgrades held back until the site earns them. Every technical choice checked against the Cloud-Native Geospatial Forum's [Cloud-Optimized Geospatial Formats Guide](https://guide.cloudnativegeo.org/), with the reasoning written as decision records the site itself publishes on a "How it's built" page (this is a portfolio piece). Historical maps from the David Rumsey Map Collection added as style references and, later, as overlays. "The girl" is always written in inverted commas, as she is unnamed in the novel. Earlier changes (v2): full read of the book, MapTiler, React, illustrated mountains and vignettes, Cartographers' Guild references and how to browse them.

## 1. Purpose and principles

Build a free, self-hosted reading guide to Cormac McCarthy's *The Crossing*: a map site that follows every journey in the book, places each named location on real geodata, and links the Spanish dialogue to where it was spoken. The Part I prototype ([live page](https://claude.ai/artifact/QA95QAvy8YyhnUQo26ojay)) set the tone: an endpaper-style literary map with paw-print and ink routes, numbered stops and short notes.

**Audience.** Readers of the novel, from first-timers (who need a spoiler-free mode) to rereaders, students and McCarthy Society members. A secondary audience is geographers and borderlands enthusiasts who want to see the real country.

**Design principles**

- **Feel of the book first.** Spare type, wide empty country, ink on paper. The land is the main character; the interface stays quiet. The literary map is allowed poetic licence (a wolf drawn larger than a mountain range); the data under it is not.
- **Accuracy is visible.** Every point, line and area carries a certainty level (located, approximate, inferred, reported) and the source it came from. Line style and fuzzy areas show doubt; nothing hides it.
- **Spoilers are opt-in.** A reader sets how far they have read, and the site shows nothing past that point.
- **Paraphrase, don't quote.** Notes are our own words. The site does not republish the novel's text.
- **Open data out.** Everything we make ships as documented GeoJSON that others can reuse.

**Working blurb** (for the about page and the Reddit post):

> The geographer in me needed to see these places more closely. *The Crossing* moves through real country: the Animas Valley, the Peloncillos, the Bavispe, the Babícora. This is a map of where Billy, Boyd, "the girl" and the she-wolf went, built from real geographic data and marked honestly where the book leaves us guessing.

### 1.1 Two phases

The site is meant to be quick to build and good to look at, then grow only if people use it. Claude Code does the heavy lifting; you review and decide. Every feature in this plan is tagged **P1** (first release) or **P2** (later, only if traffic or interest justifies it).

| | Phase 1: quick and good | Phase 2: if it earns it |
| --- | --- | --- |
| Goal | A complete, accurate, beautiful reading map of the whole book that you can share and show in a portfolio | A deeper research tool |
| Effort | A few focused weekends with Claude Code | Open-ended |
| Hosting | GitHub Pages only, $0 | Add Cloudflare R2 for big tile files; paid MapTiler month around a launch |
| Geometry | Gazetteer points; routes snapped to rivers and roads where the text names them, gentle curves elsewhere; inferred areas drawn by hand in QGIS with written reasoning | Least-cost routes over terrain, viewshed- and travel-time-built areas |
| Relief | Generated hachures plus mountain glyphs on significant peaks; hillshade only if the relief experiment says it helps | Hand-tuned hachures for key ranges; Eduard or Blender shading if hillshade earns a place |
| Historical maps | Style references and links | Georeferenced overlays with a swipe |
| Translations | Campbell guide (with permission) or links, plus gap-fill | Speaker review, audio |
| Concepts | One concept (Endpaper), informed by two static mockups | Story mode |
| Data out | GeoJSON and GeoParquet downloads, documented | A STAC-style catalogue only if the dataset grows to many files |

The rule for moving anything from P2 to P1: it must make the reading experience better for most visitors, not just be interesting to build.


## 2. The book, read for places

The novel has four Parts and no chapter numbers. McCarthy marks scene breaks with small-capital openings; there are 41 of these "episodes" (10 + 8 + 14 + 9; v5: counted from the text, which has a ninth Part IV opening, "Gray sky", that earlier versions missed). They are the site's unit for chapters, spoiler progress and step-through. Pages are cited by the 1995 Vintage International paperback, the edition the Campbell translation guide uses.

### 2.1 Episodes

| Part | Episodes (opening words, in order) |
| --- | --- |
| I | When they came south · They rode · When Billy · The wolf · In the woods · When they ran · He left · Two days later · They crossed · The hacienda |
| II | Doomed enterprises · When he had · He would cross · He was all day · When he got back · The sheriff looked · The house · He found Boyd |
| III | It was all but dark · They made camp · In three days' riding · They rode on south · In the evening · Noon the following day · They sat · They left the road · It was near midnight · The doctor's mozo · When Boyd awoke · It was almost dark · The next day · Three days later |
| IV | He crossed the border · He camped that night · He signed · He'd not got clear · None in that town · Gray sky · In the evening · Four days later · He woke |

Spoiler-safe one-line summaries for `episodes.json` are written by you, not pulled from the text.

### 2.2 Journeys, stop by stop

Each journey below is a route layer. Stops are in narrative order. "(area)" marks a place that will be an inferred polygon, not a point. Towns and named features resolve through the gazetteer pipeline in section 7.

**J1. The she-wolf, north out of Sonora (Part I).** Sierra de la Madera (eastern slopes) → crosses the Bavispe → border at the 30th minute of the 108th meridian (the book gives this exactly) → old Nations road → Whitewater Creek → San Luis Mountains → Animas range → Animas Valley → Peloncillos: Foster Draw (the calf) → ranges west into Cochise County: south fork of Skeleton Creek, Starvation Canyon, Hog Canyon Springs → back to the high country between Clanton and Foster draws → trapped near the vaqueros' fire on Cloverdale Creek.

**J2. Billy's first crossing, with the wolf (Part I).** Cloverdale → Cloverdale Creek road (vaqueros' fire) → Robertson's crossfence (area) → low pass in the easternmost Guadalupes → ranch house on the volcanic plain (area) → boundary, a monument in sight → the Cajon Bonita (the book's spelling) trail south → Sierra de la Cabellera passes → Bavispe valley; colonia lights at ten miles → river crossing where deputies take him (the hacendado names it: Colonia de Oaxaca) → unnamed mud-house settlement (area) → Colonia Morelos, the fair → the hacienda, unnamed, by the river (area; v5: the book does not name Batepito) → the fight → carries the dead wolf into the Pilares Teras.

**J3. Billy alone in the Sierras, and home (Part II).** Bavispe seen "running backwards" from a promontory → deep into the Sierras among wild Indians (area, weeks) → looks east over the Bavispe barranca and the Carretas Plain → the Mormon-born heretic's house in Huisiachepic, ruined church, the tale of Caborca (tale places: Caborca on the Altar River, Bavispe, Batepito, the earthquake) → Tamichopa → Bacerac (old Santa María, founded 1642) → Bavispe → Colonia de Oaxaca → Morelos → road north toward Ojito → border crossing at Douglas, Arizona (John Gilchrist) → old Douglas–Cloverdale road, pass in the Guadalupes → Animas Plain → the Parham house (parents dead) → Animas → Lordsburg (sheriff) → the Websters' (Boyd).

**J4. Billy and Boyd, for the horses (Parts II–III).** Lordsburg → alkali flats 15 miles west → San Simon Valley → highway east of Bowie → old road south through the Dos Cabezas → Apache Pass → route 666 down the Sulphur Springs Valley → Elfrida → McNeal → Douglas → Agua Prieta → Ojito → Morelos (midnight) → Bacerac (the one-eyed horse Keno) → river towns → mountains "shutting in the Bavispe River Valley under the western slope" → trail over to the plains of Chihuahua; a station called Las Ramadas named by an arriero → Colonia Juárez (Mormon settlement, Casas Grandes River bridge) → ruins of Paquimé → Casas Grandes (Mexico Northwestern railroad; the ganadero Soto; Gillian; La Babícora named, Hearst) → road south toward San Diego → "the girl" rescued from two men (area, on the road) → Hacienda de San Diego ("L. T.", Luis Terrazas; the opera troupe) → south along the road to Mata Ortiz, Las Varas and Babícora → opera caravan broken down a few miles south of Las Varas on the Madera road (area) → river camps → the old wagon road from La Norteña crossing the Babícora plains and the Santa María valley to Namiquipa → Las Varas (railroad, adobe warehouses) → road to Boquilla; vaqueros driving steers to the Naco pens from La Quemada at the south end of La Babícora → the hacienda at Boquilla (Guardia Blanca, señor Lopez) → riders; Quijada, superintendent of the Nahuerichic → Boquilla y Anexas (the manco) → leave the road a mile north of town, west to the river → upcountry, a night ride → San José (pueblito) → shootout at the river camp, Boyd shot (area) → workers' truck → Billy to Mata Ortiz (blue tienda) → Casas Grandes at 3 a.m. (the doctor, Alameda Street) → ejido of San Diego (Boyd treated) → Boyd and "the girl" gone.

**J5. Billy looking for Boyd and "the girl" (Part III).** San Diego → Mata Ortiz → Boquilla (train whistle for the Las Varas crossing) → Santa Ana de Babícora (midnight) → road west to Namiquipa (home of "the girl"; her story of Socorro Rivera and the Guardia Blanca) → back through Santa Ana, La Boquilla, Las Varas → three days to San Diego; camp on the river south of Mata Ortiz → Boyd gone → rides as far south as Cuauhtémoc, north again to Namiquipa, Buenaventura crossroads, Alamo, Galeana → Casas Grandes (December, broke) → north to the border.

**J6. Boyd and "the girl" (Parts III–IV, reported).** Leave the ejido of San Diego together → Namiquipa (her mother) → in the corrido: Bachíniva, April, six riders → Quijada's account: Boyd killed two Babícora men at Galeana, was shot dead at San Lorenzo (not Ignacio Zaragoza as rumoured), buried at San Buenaventura under a board; "the girl" taken away covered in blood, then went back to her family. Everything here is `reported`, each segment tagged with its source (the blind man's wife, the Mata Ortiz women, the singer, Quijada).

**J7. Billy's war years and third crossing (Part IV).** Border at Columbus → Florida Mountains → Deming (midnight; the recruiting sergeant) → bus to El Paso (recruiting office; San Antonio Street, the Splendid Cafe; Fort Bliss named) → Deming → Albuquerque (rejected again) → bus south past Socorro → Deming → old road to Hermanas and Hachita → Little Hatchet foothills, Phelps Dodge railroad → Gillespie Mountain in snow, Animas Peaks → old Playas road west into the mountains → Animas Valley, road south from Animas → the Sanders ranch (Mr Sanders; Miller) → camps on the Animas Plain → works for the Hashknives in Arizona (linecamp on the Little Colorado) → Socorro, Magdalena, plains of San Agustín → Silver City (Palace Hotel, snowing) → ranch out of Magdalena until March → south past Steins → the SK Bar gate (the old man, the radio from Ciudad Juárez) → Mexican customs at El Berrendo (McCarthy's "Berendo": the tiny Antelope Wells crossing in the bootheel) → abandoned ranch west of Ascensión → Janos (lights on the plain; the Pilares and Bavispe country seen beyond the western Sierras) → the drinking soldiers (Torreón, Zacatecas tales) → Casas Grandes → Hacienda de San Diego → Las Varas → road east to La Boquilla (lake; dust off Babícora; the red Waco plane) → Babícora and Santa Ana de Babícora → Namiquipa (now a mining camp) → the woman who says the bones lie at San Buenaventura → Temósachic (first hears the corrido) → Madera (late April fair; the horse's eyes; railtracks) → road south from Madera toward Temósachic → Babícora again → Casas Grandes (Camino Recto Hotel; the singer's corrido of Bachíniva) → high country of the Babícora, the vaqueros called mascareñas → Quijada, now gerente of the Nahuerichic division → San Buenaventura (the grave; old road toward Gallego; Sierra del Nido to the south) → exhumes Boyd → attacked on the road, Niño stabbed (area) → the gypsies with the airplane (tale places: the Papigochic gorge, Madera, Mesa Tres Ríos road, Nuri, San Nicolás, Yécora, Palomas) → two nights north past the lights of Casas Grandes; crosses the Guzmán–Sabinal road; trail north along the Casas Grandes River → the horsemen who help; Hermanas → Animas Valley with the travois → Animas on Ash Wednesday (the burial on the Parham land; the Lordsburg sheriff) → Silver City, Duncan (Arizona), Glenwood, Reserve; the Carrizozos and GS ranches → July: Silver City, old road east past the Santa Rita mines, San Lorenzo, the Black Range → the shed, the crippled dog, the false dawn (the Trinity test, 16 July 1945, seen from the southwest).

### 2.3 Places named only in passing or in tales

Part I's list stands from the prototype (Albuquerque, Grant County, Texas, Pennsylvania, Agua Prieta, Casas Grandes, San Luis Pass, Black Point, Animas). v5: De Baca County and Ascensión were on that list, but the text first names them in Part IV (episodes 4-07 and 4-03), so they belong to Part IV. The later Parts add, in passing: Lordsburg's bank, Utah, California, Texas, Guatemala and Trinidad (in the heretic's tale), Durango, Monclova, Monterrey (the opera company's jealousy), Parral, Rodeo on the Río Oro, Torreón, Chihuahua city and its alameda, Durango's cárcel (the blind man's story), Naco, La Quemada, Cuauhtémoc, Zacatecas, Ciudad Juárez, Roswell, Fort Bliss, the Little Colorado, Kwajalein Atoll (a soldier's fate), Waco (the plane), Bachíniva, Ignacio Zaragoza, Gallego, Sierra del Nido, Guzmán, Sabinal, Nuri, San Nicolás, Yécora, Mesa Tres Ríos, the Santa Rita mines, the Black Range.

### 2.4 Facts checked against sources

| In the book | What it is | Note for the gazetteer |
| --- | --- | --- |
| Hacienda de San Diego, initials L. T. | Luis Terrazas's hacienda (1902) on the road from Casas Grandes to Mata Ortiz, municipio Nuevo Casas Grandes | Real site with photos on Commons; a landmark vignette candidate |
| La Babícora, "a señor Hearst" | William Randolph Hearst's ranch, about 360,000 ha across Temósachic, Namiquipa, Madera and Gómez Farías, broken up in 1954 | Draw as a region polygon from the four municipios, labelled "La Babícora (Hearst)" |
| Boquilla y Anexas | A locality in Guerrero municipio, Chihuahua (INEGI) | Not the Boquilla dam near Camargo; pick by municipio |
| Berendo, Mexican customs | El Berrendo, Chihuahua: the Antelope Wells crossing at the foot of the New Mexico bootheel, the smallest on the border | Not Palomas, which the book names separately |
| Colonia Juárez, the Mormon settlement | Real Mormon colony on the Casas Grandes River; Colonia Dublán nearby | Both real; Dublán is not named |
| The walled ruins of the ancient mud city | Paquimé (Casas Grandes archaeological zone) | Real; vignette candidate |
| Mexican Northwestern Railroad at Casas Grandes; Las Varas crossing; Madera railtracks | The Ferrocarril Noroeste de México line Juárez–Casas Grandes–Madera | Digitise from AMS sheets or Natural Earth railroads where it still exists |
| Mata Ortiz | Juan Mata Ortiz, about 23 km south-south-west of Casas Grandes (v5: geodesic, Wikidata Q3867357 to Q4284456, straight line not road distance) on the Palanganas (upper Casas Grandes) river | Real; the railroad town of the book |
| The false dawn at the end | Consistent with the Trinity test, 16 July 1945; the site is about 55 km south-east of Socorro and about 147 km north-east of the Black Range crest (v5: geodesic distance on the WGS 84 ellipsoid, pyproj 3.8 / PROJ 9.8, from the Emory Pass marker, Wikidata Q49487009, to the Trinity Site, Q19842077; initial bearing 54°. The Emory Pass coordinate is rounded to about 1 km, and where Billy stands is not known, so read this as 145–150 km. Script: `pipeline/measure/distances.py`) | The site is inside the story box, so mark the flash as a direction arrow from Billy's position, `reported` |

## 3. Copyright and licensing guardrails

Unchanged from v1 in substance. The novel and the Campbell guide are under copyright; the public site republishes neither. This is a checklist, not legal advice.

| Material | Rule | Attribution shown |
| --- | --- | --- |
| Novel text | No passages. Notes are paraphrase. Spanish appears only as an opening phrase (incipit) with a page number. | Title, author, Vintage edition, page |
| Campbell translation guide | Written permission before its translations go in the app; otherwise our own translations plus a link per guide page. | "Translation: Lt. Jim Campbell, cormacmccarthy.com" on each entry |
| Our own translations and notes | Ours. Marked "Added by this site" with a confidence level. | CC BY 4.0 |
| Book text in the pipeline | Your own legally owned copy, on your machine. Never commit text or offsets that rebuild it. | n/a |
| Wikimedia Commons photos | Only PD, CC0, CC BY, CC BY-SA. Reject NC, ND and non-free files. | Title, author, source, licence (TASL) |
| Natural Earth, USGS (GNIS, NHD, 3DEP/NASADEM, historical topos), US Census TIGER | Public domain | Courtesy credit |
| Copernicus GLO-30 DEM (the pipeline DEM for hachures and peaks; v5) | Free licence, attribution notice required; copy the exact wording from the dataset licence. No login needed (AWS open data, COG tiles). NASADEM needs a free Earthdata login | Credits page |
| AWS Terrain Tiles (Mapzen/Tilezen, for the browser hillshade; v5) | Mixed sources; the tile docs require credit for each. Public domain for the USGS parts; INEGI under Mexico's free-use terms | "3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey" and "Source: INEGI, Continental relief, 2016", on the map wherever hillshade shows and on the Credits page |
| Reference images (Cartographers' Guild screenshots, Rumsey scans) | Not ours to republish in an MIT repository. Images stay in `private/inspiration/` (git-ignored, on your disk only); the repo holds only an index of titles and links | Links on the Credits page |
| INEGI (Mexico) | Free-use terms, attribution required | "Fuente: INEGI" plus dataset |
| Wikidata | CC0 | Courtesy link |
| GeoNames | CC BY 4.0 | "GeoNames" with link |
| OpenStreetMap via Nominatim | ODbL: attribution, share-alike on derived data | "© OpenStreetMap contributors"; ODbL-derived features listed in the data README |
| MapTiler tiles | Free plan is non-commercial; MapTiler logo and attribution required on screen | MapTiler logo + "© MapTiler © OpenStreetMap contributors" |
| Huffman's Hachures script (vendored, adapted) | GPL-3.0; kept in `pipeline/relief/hachures/` with its LICENSE and a NOTICE of changes; called as a separate process | Credits page and README; the generated lines are our data |
| Public-domain art traced for vignettes and mountain glyphs | Only works with clear PD status (US government reports, pre-1929 plates) | Credits page |
| Eduard relief output (if used) | Check the app's licence for use of its output in a public web map | Credits page |

Keep a `source` field on every feature. Prefer Wikidata, GNIS and INEGI; use Nominatim last.

## 4. Architecture and decisions

### 4.1 The shape of the system

A static site, a folder of small GeoJSON files, a few PMTiles archives, and one third-party tile service for satellite. No server, no database, no build-time API keys except MapTiler's public, origin-restricted key.

```
 Your machine (private)                      GitHub repo                       Browser
 ┌────────────────────────┐   GeoJSON,    ┌──────────────────────────┐   HTTPS   ┌─────────────────────────────┐
 │ Python pipeline (uv)    │──PMTiles────▶│ data/  *.geojson          │──────────▶│ React + MapLibre            │
 │ book copy, DEM, NE,     │   review CSV │ tiles/ *.pmtiles (<100 MB)│  range     │  story layers (GeoJSON)     │
 │ GNIS, INEGI, Wikidata   │              │ site/  Vite build         │  requests  │  literary base (PMTiles)    │
 └────────────────────────┘              │ docs/decisions/*.md       │           │  satellite (MapTiler, lazy) │
                                          └──────────┬───────────────┘           └─────────────────────────────┘
                                                     │ GitHub Actions: validate, build, deploy to Pages
```

### 4.2 Decisions, checked against the cloud-native guide

The [Cloud-Optimized Geospatial Formats Guide](https://guide.cloudnativegeo.org/) solves a specific problem: datasets too big to download, read in parts over HTTP. Its own framework starts by asking about data shape, intended use and how much is read at once, and it is explicit that it does not prescribe a single answer. Applied honestly to this project, it points to **one** cloud-optimized format (PMTiles, for the basemap) and to plain files for everything else, because the story data is tiny and is always read whole.

| Decision | Choice | Why | Rejected, and why | Phase |
| --- | --- | --- | --- | --- |
| Story data (places, routes, areas, stops) | Plain GeoJSON, one file per layer | Under 1 MB in total, always loaded whole, so one request beats many range requests. Human-readable, diffs in git, previews on GitHub, opens in every GIS, and MapLibre reads it natively | FlatGeobuf and GeoParquet (built for partial reads of large data; no gain here and an extra decoder in the bundle); vector tiles for story data (would lose easy filtering and editing) | P1 |
| Literary basemap vectors (borders, rivers, labels) | PMTiles vector archive, built with tippecanoe | The guide's choice for "tiled web delivery": one static file, read by HTTP range requests, no tile server | A tile server (needs hosting); raw GeoJSON for Natural Earth and INEGI layers (megabytes and no level of detail) | P1 |
| Relief | Hachures as vector lines and peak glyphs as points, both in the literary vector PMTiles; hillshade, if kept, shaded in the browser by MapLibre's `hillshade` layer from a raster-dem PMTiles archive (v5) | Hachures are lines, so they belong with the other vectors: crisp at every zoom, styleable in ink, small. PMTiles is a container that holds vector or raster tiles, so one approach covers both | Hillshade as the main relief (reads as modern and digital next to ink); pre-rendered hillshade images (each light or tint change is a rebuild); linking the browser straight to the Terrain Tiles bucket (its docs say the S3 tiles are "meant for efficient networking with EC2 resources only", with no CDN and no updates since 2017). The pipeline DEM stays a COG, the right format for processing | P1 |
| Hosting | GitHub Pages | Free, supports HTTP range requests and CORS so PMTiles works with no extra setup, deploys from Actions. Limits (GitHub docs, checked 11 November 2026): 1 GB published site, 10-minute deploy timeout, soft 100 GB/month bandwidth. Pages states no per-file limit; 100 MB is git's push limit, which is why tiles are not committed (next row). v5: neither GitHub's nor Protomaps' docs state range-request support, so stage 0 tests it with `curl -r 0-99` against a deployed test archive before anything depends on it | Cloudflare Pages (25 MiB file limit; range-request support not stated in its docs); S3 or R2 (more setup than P1 needs) | P1 |
| Tile delivery (v5) | PMTiles are built locally, git-ignored, and uploaded as assets on a GitHub Release (`tiles-vN`). The deploy workflow downloads the pinned release into the Pages artifact. Clip to the story region and cap zooms so all archives together stay under about 500 MB | The relief build needs QGIS and can run for hours, so CI cannot build tiles; committing them would bloat git history on every rebuild. Release assets are free, versioned, and allow 2 GB per file. One repo, one deploy | Committing tiles (history bloat, 100 MB push limit); Git LFS (quota, extra setup); building in CI (QGIS, DEM downloads, run time). Cloudflare R2 (free tier, no egress fees) is the P2 move if files outgrow Pages | P1 / P2 |
| Satellite | MapTiler `satellite`, through MapTiler SDK JS, in a map instance created only when the reader asks (v5, see 5.3) | Ready imagery and style, MapLibre-native SDK, free non-commercial tier that pauses rather than bills | Self-hosting imagery (licensing and size); Esri (a fine alternative, kept behind one config value) | P1 |
| Downloadable data | The same GeoJSON, plus one GeoParquet file per layer (one `ogr2ogr` line each; a Parquet file holds one layer) | GeoJSON for everyone; GeoParquet (maturity L4 in the guide) for analysts using DuckDB, GeoPandas or QGIS | FlatGeobuf (duplicate effort); a STAC catalogue (the guide frames catalogues as necessary at tens of thousands of files; we have about ten) | P1 |
| Front end | React 19 + TypeScript + Vite, `@vis.gl/react-maplibre` | State-driven UI (panel, drawer, stepper, spoiler filter, search) kept in sync with the map. On npm at 11 November 2026: react 19.3, vite 8.3, typescript 7.0, maplibre-gl 6.17, @vis.gl/react-maplibre 8.1 (peer: maplibre-gl 4 or later), pmtiles 4.5, @maptiler/sdk 4.2. Stage 0 pins exact versions and confirms the SDK and maplibre-gl 6 work side by side. v5: `@vis.gl/react-maplibre` is a trial. If the swipe, the lazy satellite map or the PMTiles protocol need workarounds through the wrapper, the map moves to plain MapLibre GL JS inside one `MapView` component, and the switch is recorded as a decision. Nothing outside `site/src/map/` may import the wrapper, so the switch stays cheap | Plain TypeScript (fine, but you would rebuild a small framework); Svelte (your call) | P1 |
| State | React `useReducer` + the URL hash as the single source of truth | Shareable links for free (a place, a stop, a reading position), nothing else to learn | Zustand or Redux (unnecessary at this size; add later if needed) | P1 |
| Search | MiniSearch over places and translations, built at deploy time | Client-side, accent-folding, tiny | A search service | P1 |
| Pipeline | Python 3.12 with uv; GDAL, geopandas, shapely, rasterio, tippecanoe | The standard geospatial toolchain; reproducible from one `make`. uv installs Python 3.12 itself (the system Python here is 3.9) | Notebooks as the pipeline (hard to rerun); cloud processing (nothing big enough) | P1 |
| Hand-drawn inferred areas | Drawn in QGIS, saved to GeoJSON with a `reasoning` field | Fast, honest and reviewable | Constraint modelling (viewsheds, travel-time rings) is better but slower; P2 | P1 / P2 |

### 4.3 The "How it's built" page (portfolio)

Because this is also your portfolio piece, the site explains itself. A page at `#/about/how-its-built` renders:

1. **The architecture diagram** (4.1), as an SVG in the site's ink style.
2. **Decision records.** Each row of 4.2 is a short Markdown file in `docs/decisions/` (context, decision, alternatives, consequences). Vite imports them at build time and the page lists them. v5: the app root is `site/`, and a leading `/` in a glob means that root, so the pattern is relative (`import.meta.glob('../../../docs/decisions/*.md', { query: '?raw', import: 'default', eager: true })` from `site/src/pages/`), with the repo root added to `server.fs.allow` for the dev server. The same applies to `data/`: a small script copies it into the build so the app and the downloads read one set of files. The same files are the project's real decision log, so the page cannot drift from the truth.
3. **Data lineage, live.** Counts by `certainty`, by `source` and by `method`, computed from the GeoJSON at build time, and a short note on the accuracy targets.
4. **Numbers.** Bundle size, each tile file's size, total data size, and a Lighthouse score, written by the CI job into a small JSON the page reads.
5. **Links** to the repository, the data downloads and schemas, and the credits.

In the map itself, every place card already shows its certainty, source and method, so the craft is visible where readers look, not just on an about page.

### 4.4 Maintainability rules

- One way to do each thing. No second map library, no second state library, no second data format for the same layer. One stated exception (v5): MapTiler SDK JS, itself a MapLibre build, loaded as a separate lazy chunk for the satellite map only.
- Data is the source of truth. The UI reads the GeoJSON; nothing about a place lives in component code.
- Everything rebuilds from `make all` in the pipeline and `npm run build` in the site.
- Pin versions (MapLibre, react-maplibre, pmtiles, tippecanoe, GDAL) and record them in `docs/decisions/`.
- Dependabot on, but upgrades merged deliberately.

## 5. Basemaps

The site has two basemaps behind one basemap toggle, plus a swipe to compare them over one view:

1. **The literary map** (ours, self-hosted, default).
2. **Satellite** (MapTiler), with our labels on top; MapTiler's own labels only on an optional "modern names" switch.

### 5.1 The literary map: design brief

The look is an endpaper map from a 1940s novel, drawn by a surveyor who also sketches: ink on toned paper, a hand-lettered feel, mountains drawn as mountains, rivers as living lines, and small illustrations in the empty quarters. Everything under it is real geodata, so the map is honest at every zoom.

**Reference points** (what to study, in three families):

| Family | Examples | Take from it |
| --- | --- | --- |
| Historical survey maps of this exact region | Ehrenberg's 1858 *Map of the Gadsden Purchase* (relief by hachures); Cram's 1887 *Railroad and county map of Arizona* (an example of the caterpillar style to avoid as a base); SCOP railroad maps of Mexico, around 1910, at the INAH Mediateca; Mallery's 1876 *New map of the territory of Arizona … and Sonora*; Riecker's 1879 map; the RGS 1912 *Sketch Map of part of Sonora and Arizona*; Colton 1873 and Gray 1876 state maps; the 1890s US–Mexico Boundary Commission sheets | Hachured ranges, italic spaced range names, dotted trails, the dash-dot international line, sparse towns, the look of blank desert |
| Pictorial maps of the Southwest | Fred Harvey's *Illustrated Map of the Great Southwest* (1946); Ruth Taylor White's *Arizona* (1935); Liozu's *Arizona* (1946); 1930s Shell road maps | Vignettes of cattle, ranch gates, missions, trains and wildlife placed with poetic licence; borders as decorative frames; one hero illustration per region |
| Cartographers' Guild and modern hand-drawn style | Guild tutorials: Gidde's *Hand-Drawn Map Tutorial (for the Artistically Challenged)*, Ironmetal250's *Hand-drawn mountains and other stylistic map elements*, RobA's *Creating old weathered paper* and *Simple Mountains in GIMP*, Tear's *Saderan* inked style, Herwin Wielink's style; Jonathan Roberts's fantasticmaps.com mountain tutorials; Tolkien-style real-world maps by Dan Bell and Callum Ogden; John Nelson's Esri blog on building a Tolkien-style map from real terrain | Profile mountains with a consistent light side; hills as scaled-down mountains, never surrounding them; paper texture and vignette edge; restraint in label density |

**Browsing the Cartographers' Guild (v5).** The site's `robots.txt` (read 11 November 2026) is `Disallow: /` for every agent except Googlebot and Bingbot, so Claude Code's fetch tool gets nothing. Your decision: browse it with an automated real browser that behaves as you would. The risk is yours and small: a forum may treat this as a breach of its rules and block the session or the account.

1. `tools/guild-browse/` runs Playwright in headed mode with a persistent profile kept in `private/browser-profile/` (git-ignored). It uses an installed browser (Chrome Canary on this machine), so the user agent, cookies and any login are those of a normal visit. The forum shows nothing to logged-out visitors (checked 11 November 2026: `forum.php` returns a login page), so you log in once with `npm run guild-login` in `tools/`; the profile keeps the session.
2. It opens one page at a time, waits 8–20 seconds between pages, scrolls as a reader does, and stops after a fixed page budget per run (40). No parallel tabs, no attachment downloads, no search endpoint.
3. It saves a screenshot of each thread to `private/inspiration/guild/` and appends the thread title and URL to `docs/inspiration/guild.md`. The index is committed; the images are not.
4. If the site shows a challenge or a block page, the run stops and reports it. It does not try to defeat it.

`private/` is private in one sense only: it is git-ignored, so nothing in it reaches GitHub. It is an ordinary folder on your disk, not encrypted and not backed up by the repo. A CI check fails the build if any file under `private/` is ever tracked.

Rules: this is reading for inspiration, not scraping. No mirroring, and nothing from the Guild goes into the site or the public repository. Guild members own their images; any style we take is redrawn in our own hand. Threads to start with: Gidde's and Ironmetal250's hand-drawn tutorials, RobA's weathered paper, the Saderan tutorial, the Finished Maps forum browsed for "western", "desert", "Mexico" and "Arizona", and the Map Challenge archives for "old map" and "treasure map" entries.

**Hachure styles: what to borrow, and what not to.** Carl Churchill's [Variety in hachure](https://churchillgeo.com/variety-in-hachure/) shows that "hachure" covers many distinct styles, and that strictly it is a systematic survey technique: lines follow slope and aspect, and their spacing and weight carry information about steepness. The styles that matter for this map:

| Style (Churchill's grouping) | What it looks like | Relevant examples | Use here |
| --- | --- | --- | --- |
| Systematic survey hachure | Lines drawn downslope, denser and heavier where steeper; flats left blank | Wheeler sheets (section 5.4); Huffman's generated hachures | **The base.** Accurate by construction, because it comes from the DEM |
| Caterpillar | Fuzzy chains of hachure along a ridgeline, with little real terrain knowledge behind them | Many "Old West" and railroad maps, such as George Franklin Cram's *Railroad and county map of Arizona* (1887) | **Not as the base.** It is inaccurate, and Churchill notes these maps were often made to guide the exploitation of the land they show. Useful only at the smallest zooms, where a whole range is a few pixels |
| Short, dense hatches with stippling | Packed short strokes and dots for rugged, non-glacial terrain | Mexican railroad maps of the Secretaría de Comunicaciones y Obras Públicas, such as *Carta del Ferrocarril Oaxaca a Ejutla* (1910, INAH Mediateca); W. H. Graves, *Map of Utah Territory* (1878, Rumsey) for desert in dense pecked rows | **Test** for the Sierra Madre barrancas and the desert ranges |
| Hachure with land cover | Bushes, trees or boulders peppered among the hachures, in the same ink | French Dépôt général de la Marine maps of the 1830s; the 1839 US Exploring Expedition map of Upolu | **P2**: mesquite and creosote stipple on the plains, oak and pine marks in the sierras, from a land-cover dataset such as ESA WorldCover (check its licence) |
| Horizontal hachure | Strokes along the slope, forming terraces that read like contours | British naval charts of the 1870s–80s; Norwegian county maps mixing both directions | **Not used.** It suggests elevation bands the reader does not need |
| Hachure as accent over shading | Light shaded relief does the work; hachures only on the steepest, rockiest slopes | Swiss topographic maps (Dufour, Siegfried, Imhof); the Chevalier map of San Francisco (1911) | **Test.** The modern, restrained option; Esri publishes a tutorial on recreating the Chevalier look |

Two lessons carry through to the design. First, light from the north-west and steepness shown by density and weight, never decoration for its own sake. Second, Churchill's caution about value judgements: these survey styles grew up alongside conquest and extraction, and *The Crossing* is partly about land taken and held (Hearst's Babícora, the Terrazas haciendas). The map borrows the craft, draws the Mexican side with references from Mexican mapmakers as well as US surveys, and avoids the "prospectus" look: no resources drawn as prizes, no empty land waiting to be claimed.

**Design tokens.** Paper (a warm caliche, not cream), iron-gall ink, Mexico side a shade darker, water in blue-grey ink, routes in slate (wolf), oxblood (Billy), and two further colours for Boyd and "the girl". A dark "by lamplight" theme keeps the same lines on a near-black paper. Type: IM Fell English (labels, notes), IM Fell English SC (states, counties), both OFL.

### 5.2 Relief: hachures, mountain glyphs, and an optional hillshade

Relief on the literary map is drawn the way 1850s–1880s survey maps drew it, and the way the Wheeler sheets in section 5.4 do: with hachures. Big named peaks also get small drawn mountains, as on a novel's endpaper. Both are generated from real elevation data, so they are in the right places.

**A note on terms.** A *hillshade* is a raster: a grey image of the terrain lit from one direction, computed from a digital elevation model (DEM). *Hachures* are vector lines drawn downslope, closer together and heavier where the ground is steeper. *PMTiles* is only a container for map tiles; it holds vector tiles (our borders, rivers, hachures and glyph points) or raster tiles (a hillshade image), one kind per file.

**Layer 1: hachures (vector, P1).**

1. Mosaic and clip the DEM (Copernicus GLO-30 at 30 m, reprojected to a local equal-area or UTM grid) for the story region; keep it as a COG. v5: Copernicus, not Terrain Tiles, because the hachure method needs one uniform resolution. Terrain Tiles switch between 3 m, 10 m, lidar and 30 m sources (checked from each tile's source header on 11 November 2026), which would change hachure texture at every source boundary, including along the border. Copernicus tiles are 1° COGs of about 38 MB; start with the 20–30 under the journeys corridor, about 81 for the whole story box.
2. Smooth it lightly (a Gaussian of 2–3 cells) so hachures follow landforms, not noise.
3. Generate hachures with Daniel Huffman's [Hachures](https://github.com/pinakographos/Hachures) QGIS script, run headless from the pipeline as a standalone PyQGIS run. It builds slope, aspect and contours from the DEM, starts lines on each contour at spacings set by slope, grows them downslope, and drops or adds lines as they converge or drift apart. Its main knobs are the contour interval, minimum and maximum spacing, and the slope range that gets hachures at all. The script is GPL-3.0 and runs only inside QGIS's Python console (it reads the selected layer through `iface.activeLayer()`), so it is used in two steps: first unmodified in QGIS to find settings, then as a lightly adapted headless copy kept under GPL in its own folder. See decision record D-relief-hachures below. Huffman warns that large areas or dense settings can run for hours, so settings are tuned on small test areas first. v5, from reading the script (`Hachure Generator.py`, 898 lines): spacing is set in DEM pixels, and `min_slope_val` and `max_slope_val` are percentages of the lowest and highest slope found in that raster, not degrees. Settings tuned on a test area therefore do not carry over to a different extent or cell size, and a region run in tiles would not match at the seams. The headless copy must take absolute slope limits in degrees and a fixed cell size. The script also has a `thickness_layer` option that splits lines and weights them by slope, which covers most of step 4.
4. Attach each line's mean slope as an attribute, filter out stubs, and simplify.
5. Build two generalisations: coarse (zoom 6–9, wider spacing, steep ground only) for the whole story region, and fine (zoom 10–13) only inside a corridor of about 40 km around the journeys (v5). The story box is 811–893 km wide (north edge to south edge) and 998 km tall (geodesic, pyproj), about a billion 30 m cells; fine hachures over all of it are expected to be slow and large, though that is an estimate, not a test. Outside the corridor the coarse set over-zooms. The 40 km width is a starting choice, not a measurement. Agreed order: build the corridor first, then return to the full-region run and time it.
6. Style in MapLibre as ink lines: `line-width` by slope (steeper is heavier), slight opacity, the same ink colour as everything else. Basin floors stay blank, which is what makes the Animas Valley and the Chihuahua plains read as open country.

**Layer 2: mountain glyphs (vector points + sprite, P1).**

1. Find peaks from the DEM with topographic prominence (local maxima, then prominence by the key-col method, or the `prominence` tool from Kirmse and de Ferranti's work if available). Keep only significant peaks: prominence above about 300 m, plus every summit the book or GNIS/INEGI names (Animas Peak, Gillespie Mountain, Black Point).
2. Draw about 12 mountain shapes by hand in one ink style (traced from the Wheeler and Ehrenberg hachure maps or the Guild references), in three sizes, with the light from the north-west and hatching on the south-east flank. v5: one family of shapes per landform (peak, dome, mesa, butte, cone, ridge), since the corridor has tablelands and rounded lomas as well as peaks. `crossing.landforms` picks each summit's family by points from its name (Mesa, Loma, Picacho, Cuchilla...), its gazetteer feature code, and DEM measurements of its top and flanks; every weight and threshold is in `pipeline/seeds/landforms.toml`, and `review/stage-3/landforms.csv` shows each summit's measurements, rule points and winner. Named mesas, buttes and cones are kept down to 100 m prominence, since few reach 300 m. The families are generated stand-ins until the hand-drawn set exists.
3. For each peak, choose a shape and a small random variation from a seed made from the peak's id (so the result is varied but stable between builds): which of the 12 shapes, a horizontal flip, a scale jitter of ±15%, a rotation of ±3°. Size class follows prominence. MapLibre can scale and rotate an icon per feature but cannot mirror it, so the sprite carries a mirrored copy of each shape (v5). A mirrored shape keeps its hatching redrawn on the south-east flank.
4. Render as a symbol layer from the sprite: `symbol-sort-key` by negative prominence (lower keys are placed first, so the biggest win collisions), `icon-allow-overlap: false`. Glyphs sit on top of the hachures and knock them out with an opaque paper-coloured fill drawn into each glyph (v5: `icon-halo-color` works only on single-colour SDF icons, so a halo is not available here). The lamplight theme needs its own sprite with the dark paper fill.

**Layer 3: hillshade (raster-dem, experiment only; v5).** MapLibre shades the terrain in the browser with a `hillshade` layer using `hillshade-method: "multidirectional"` (available in MapLibre 6), tinted sepia at 10–20% opacity under the hachures. The elevation comes from AWS Terrain Tiles (Terrarium PNG), downloaded once for the story box and repacked into our own raster-dem PMTiles at zoom 5–10: 1,171 tiles, about 63 MB, one batch of about 1,200 requests. MapLibre over-zooms beyond 10, which is fine for a soft tone under ink. Light direction, tint and opacity are style settings, so the experiment can tune them live. It stays out unless the experiment in stage 3 picks a treatment that uses it (the Swiss accent, or the control). The same archive could later drive 3D terrain (P2).

**The relief experiment** (stage 3 of the build). Three test areas at three zooms (7, 9, 11): the Peloncillos and Animas Valley; the Pilares and the Bavispe barranca; the Babícora plains. Five treatments on one comparison sheet, each named after the style it follows:

1. **Survey:** systematic hachures (Huffman's method) + mountain glyphs on significant peaks.
2. **Survey, no glyphs:** systematic hachures alone, to see whether the glyphs earn their place.
3. **Sierra:** short, dense hatches with light stippling on rugged ground (the SCOP and Graves look) + glyphs.
4. **Swiss accent:** light sepia hillshade, with hachures only on slopes above a steepness threshold (the Imhof and Chevalier look) + glyphs.
5. **Control:** hillshade only.

Each treatment uses the same paper, ink and labels, so only the relief differs. A mix by zoom is allowed (for example Survey at zoom 7–9, Swiss accent at 10–11). Land-cover marks are not in this round; they are P2.

You pick one, or a mix by zoom, and the choice goes into a decision record.

**Decision record D-relief-hachures: how the hachure script is used**

- **Context.** Hachures come from Daniel Huffman's [Hachures](https://github.com/pinakographos/Hachures) script, licensed GPL-3.0. It is a QGIS console script, not a plugin, and expects a DEM selected in the QGIS interface, so it cannot run headless without a small change. The rest of the project's code is MIT.
- **Decision.**
  1. Stage 3 runs the script unmodified in QGIS on the three test areas to find settings (spacing, slope range, contour interval, smoothing). The settings are recorded in `pipeline/relief/hachure-settings.json`. v5: done this way. The production settings, converted to absolute degrees and metres, are in `SCALES` in `pipeline/src/crossing/hachures.py`, and the vendored copy is in `pipeline/relief/hachures/` (decision 0015). Production runs on a fixed UTM tile grid: fine over the corridor, coarse wherever the DEM covers.
  2. If the result is chosen, an adapted headless copy is vendored. The changes (v5, wider than a path argument): DEM path as an argument instead of `iface.activeLayer()`; absolute slope limits in degrees instead of percentages of the raster's range; spacing tied to a fixed cell size; `iface.messageBar()` calls and the layers it adds to `QgsProject.instance()` replaced with logging and file output. It is vendored at `pipeline/relief/hachures/`, pinned to an upstream commit, with the upstream LICENSE file and a NOTICE saying what was changed. That folder stays GPL-3.0.
  3. The pipeline calls it as a separate step: a standalone PyQGIS run using the Python bundled with QGIS. (`qgis_process` runs Processing algorithms, and this is a console script, so it is not an option without wrapping it.) No other code imports from it, so the boundary between GPL and MIT code is a process boundary.
- **Licensing consequences.** GPL covers the script, not data made by running it, so the generated hachure lines are published with the rest of the map data. The repository README and the Credits page say which folder is GPL and why. Huffman's method is credited on the Credits and "How it's built" pages. (A practical reading, not legal advice.)
- **Alternatives considered.** A close port to plain Python (still a GPL derivative, more work for no gain); a fresh implementation from his published description of the method (MIT-clean, but days of work; P2 only if the vendored copy becomes a problem); hand-drawn hachures (beautiful, far too slow for this area).
- **Consequences.** One GPL folder to keep separate and documented. QGIS becomes a pipeline dependency for the relief step only.


### 5.3 Satellite: MapTiler

Chosen because it has a ready satellite and hybrid style, terrain-RGB for optional 3D, an SDK built on MapLibre, and a free non-commercial plan that pauses rather than bills.

| Item | Value |
| --- | --- |
| Styles | `satellite` (imagery only, our labels on top; default) and `hybrid` (their labels) behind the "modern names" switch |
| Free plan | 5,000 map sessions and 100,000 API requests a month, for "testing, PoC, prototyping, personal, or non-commercial use"; MapTiler logo required; 1 API key; the service pauses when the quota is used up (checked 11 November 2026) |
| Session | A page load that initialises a map. A reload, 6 hours, or 10,000 requests starts a new one. Interaction inside a session is free |
| Client (v5) | Sessions are counted **only** with MapTiler SDK JS (or its Leaflet plugin). Tiles fetched by plain MapLibre are billed per request: 1 per 256 px raster tile, 4 per 512 px tile, 10–16 for one raster view by MapTiler's own estimate, more with every pan and zoom. 100,000 requests would last a few hundred browsing visitors. So the satellite map is a MapTiler SDK `Map`; `@vis.gl/react-maplibre` accepts it through its `mapLib` prop |
| Key security | Restrict the key by **Allowed HTTP origins**. The free plan has one key, so the Pages origin and `localhost:<port>` share it (MapTiler notes that allowing localhost is weak protection; remove it after launch or accept it) |
| Attribution | MapTiler logo and "© MapTiler © OpenStreetMap contributors" visible on the satellite view |
| Paid fallback | Flex ($30 a month, 25,000 sessions, 500,000 requests) for a launch month if needed. Flex does not pause: overage is billed automatically at $2.50 per 1,000 sessions, so downgrade after the spike |

**Session budget.** 5,000 a month is about 160 a day. A Reddit post can bring more than that in an afternoon. Three mitigations, all in the plan:

1. The literary map is the default and never touches MapTiler, so the site works at full value even if the satellite quota is gone.
2. The satellite map does not exist until the reader switches basemap or opens the swipe (v5). MapTiler's docs count a session at the page load that initialises a map, and do not say it waits for the first tile, so the plan does not rely on that: the SDK chunk is imported and its `Map` created on demand. The literary map is plain MapLibre and never loads the SDK. The swipe is two synchronised map instances with a clipped divider, which is also how the usual compare plugins work.
3. A "satellite temporarily unavailable" state in the UI, so a paused quota looks intentional rather than broken.

If you later want no quota at all, Esri's ArcGIS Location Platform gives 2 million basemap tiles a month free; the provider sits behind one config file so it can be swapped.

### 5.4 Historical maps: the David Rumsey Map Collection

The [David Rumsey Map Collection](https://www.davidrumsey.com/) holds the period maps the literary style should learn from, many of them hachured surveys of this exact country. Its images are licensed CC BY-NC-SA, which fits a free, non-commercial site with attribution, and requires that anything derived from them (a traced overlay, a cropped detail) is shared under the same licence.

**Shortlist to pull first:**

| Map | Date | Why |
| --- | --- | --- |
| Wheeler Survey, Atlas Sheet 83, *Parts of Eastern and South Eastern Arizona, Western and South Western New Mexico*, 1:506,880 | 1876 | Hachures with a light grey under-tint over the bootheel, Peloncillos and Animas: the Part I country, in exactly the target style |
| Wheeler Survey, sheets 84B and 84C (land classification, southern and south-western New Mexico) | 1879 | Same survey; shows grazing and timber land, useful for the Animas Plains |
| Mallery and Ward, *New Map of the Territory of Arizona, Southern California and Parts of Nevada, Utah and Sonora*, 1:1,013,760 | 1877 | Reaches into Sonora; lettering and range treatment |
| Eckhoff and Riecker, *Official Map of the Territory of Arizona*, 1:823,680 | 1880 | Cochise County detail |
| Rand McNally, *New Mexico* pocket map | 1880 | Relief by hachures at a small scale; a model for the zoomed-out view |
| Mitchell and Gray state maps; General Land Office *New Mexico* | 1866–1891 | Lettering, county tints, borders |

Also search the collection for northern Chihuahua and Sonora sheets (the 1890s Boundary Commission maps, Mexican Northwestern railroad surveys) to cover Parts II–IV.

**How it is used.** P1: as style references. Catalogue links and notes go in `docs/inspiration/rumsey.md` (committed) and are linked from the credits; downloaded images go in `private/inspiration/rumsey/` (v5: CC BY-NC-SA scans do not belong in an MIT repository). P2: as georeferenced overlays (use Rumsey's own georeferenced versions where they exist; otherwise georeference in QGIS), exported as raster PMTiles and shown through the same swipe control as satellite, so a reader can compare 1876 survey, literary map and today's imagery over one view. The catalogue pages and images can be fetched normally; no headed browser is needed for Rumsey.

## 6. Data model and GeoJSON layers

All story data lives in GeoJSON (WGS 84, RFC 7946) with one shared property schema, split by geometry and theme. GeoJSON is deliberate (see decision 4.2): the whole story dataset is small and always read whole. A GeoParquet copy of each layer is generated for download. Readers can download it from a Data page with a README, schemas and licence.

| File | Geometry | One feature per | Main filters |
| --- | --- | --- | --- |
| `places.geojson` | Point | Named place with a known location | role (stop, passing, tale), Part, episode |
| `areas.geojson` | Polygon | Inferred place (cabin, ranch, camp, grave, unnamed settlement) and named regions (La Babícora, Animas Valley) | certainty, Part |
| `journeys.geojson` | LineString | Route segment between consecutive stops | journey (J1–J7), character, Part, episode, method |
| `stops.geojson` | Point | A stop in sequence on a journey (references a place or area) | journey, sequence |
| `conversations.geojson` | Point or Polygon | Where a Spanish exchange happens | Part, page, translation ids |
| `vignettes.geojson` | Point | Anchor for a decorative illustration | first_seen, priority, zoom range |
| `mountain_glyphs.geojson` | Point | Generated mountain or hill glyph (section 5.2) | prominence, range |
| `episodes.json` | none | 41 episodes: Part, opening words, length in words, Vintage page range, spoiler-safe summary | n/a |
| `translations.json` | none | Spanish line or exchange with its English | Part, page, source |

**Shared properties** (on every story feature):

```json
{
  "id": "place-colonia-morelos",
  "name": "Colonia Morelos",
  "name_in_text": "Morelos",
  "kind": "town",
  "role": "stop",
  "characters": ["billy", "wolf"],
  "journey": "J2",
  "part": 1,
  "episode": "1-09",
  "first_seen": "1-09",
  "pages": ["101", "105"],
  "certainty": "located",
  "uncertainty_m": 500,
  "method": "gazetteer",
  "source": "wikidata",
  "source_id": "Q…",
  "source_licence": "CC0",
  "note_safe": "An old Mormon settlement on the Bavispe.",
  "note_full": "Billy follows the wolf to the fair here.",
  "reasoning": null,
  "photo_ids": [],
  "vignette": "settlement"
}
```

- `certainty`: `located` (gazetteer match for the exact feature), `approximate` (the pin stands in for something, such as a range's high point), `inferred` (no name; built from clues), `reported` (a character's say-so).
- `method` on route segments: `narrated-path` (text names a road, river or trail; snapped to it), `modeled` (least-cost path), `schematic` (gentle curve, no better evidence).
- `first_seen`: earliest episode the feature can appear in. The spoiler filter hides later features, cuts routes, and swaps `note_full` for `note_safe`.
- `reasoning`: for inferred areas, the clues used, in plain words.

IDs are stable slugs. Each data release gets a version and a CHANGELOG entry.

## 7. Geodata pipeline

Eight steps (called steps here so that "stage" always means a build stage in section 11). Runs locally in Python, keeps the book text private, writes only GeoJSON, review CSVs and logs to the repo. You approve everything a script cannot decide.

```
1 Extract mentions  ->  2 Page anchors  ->  3 Resolve names  ->  4 Review (you)
  ebook (private)        Campbell guide      Wikidata, GNIS,       review/places.csv
  spaCy + name list      ~400 anchors        INEGI, GeoNames,      approve or override
                                             Nominatim                    |
                                                                          v
8 Publish          <-  7 Validate        <-  6 Routes          <-  5 Inferred areas
  GeoJSON + PMTiles      schemas,             snap / least-cost     rings, bearings,
  GitHub Pages           licence, spoilers    / curve               viewsheds, slope
```

1. **Extract mentions (private).** Parse your copy with `ebooklib`, which reads only DRM-free EPUB (v5: done 11 November 2026 with `pipeline/src/crossing/extract.py` on a Picador EPUB, ISBN 9780330511247, which has no print pages; Vintage pages still come from the Campbell anchors in step 2); split into the 41 episodes by the small-capital openings (the regex in the v1 scan worked: an all-caps run of 4+ letters at a paragraph start followed by lower case). Find names with spaCy NER (`en_core_web_trf`) plus the seed list in section 2 and Spanish forms ("la colonia", "Sierra de la …", "Río …"). Output `mentions.csv`: name, Part, episode, Vintage page; no surrounding text.
2. **Page anchors.** The ebook has no print pages. Each Campbell entry gives a page and a phrase; matching about 400 phrases gives about 400 anchors; interpolate between them. Sanity-check against the Part boundaries (Part Two starts about page 131, Three about 215, Four about 342, from the guide).
3. **Resolve names**, in order, inside the story box (about 104°–113° W, 27°–36° N; widen for Durango, Parral, Torreón, Zacatecas, Albuquerque, El Paso): Wikidata SPARQL (P625, CC0) → USGS GNIS and INEGI localities and names → GeoNames dump (CC BY 4.0) → Nominatim (1 request/s, identifying User-Agent, cached, a one-off run) → manual digitising from historical maps.
4. **Disambiguate and review.** Score candidates by feature class (peak for "Sierra", stream for "Draw"/"Creek", locality for "colonia"), by municipio or county when the text or context gives one (Boquilla y Anexas is in Guerrero municipio), and by distance to neighbouring stops. Ties go to `review/places.csv` with all candidates and a map link each.
5. **Inferred areas.** P1: draw each area by hand in QGIS from the clues and write them into `reasoning`. P2: each clue becomes a constraint, intersected in UTM 12N/13N: travel time → ring (horseback about 6 km/h at a walk, 30–50 km a day; state it in `reasoning`); direction → bearing sector; "in sight of X" → viewshed (`gdal_viewshed`); terrain words → slope class or river buffer. Output: polygon, label point (centre of the largest inscribed circle), `uncertainty_m`.
6. **Routes segment by segment.** Named road, river or trail → snap and shortest path along it (`networkx`) as `narrated-path` (for example the Douglas–Cloverdale old road, the Casas Grandes River, route 666, the road Mata Ortiz–Las Varas–Madera, the Namiquipa wagon road). Overland with no named way → P1: `schematic`; P2: least-cost path on a slope-cost raster (`skimage.graph.MCP_Geometric`), forced through named passes (Apache Pass, Guadalupe pass) as `modeled`. Else `schematic`. Flag any segment whose implied speed from a narrated duration is above 8 km/h.
7. **Validate.** JSON Schema per file; route endpoints equal their stops; source and licence on every feature; coordinates rounded to 5 decimals; a spoiler check that fails the build if any `note_safe` names a place or person first seen later (a script can match names; events it cannot, so those stay in your read-through at stage 5).
8. **Publish.** GeoJSON and the GeoParquet copy to `data/`, PMTiles to a GitHub Release that the deploy workflow pulls into the Pages artifact (all served by GitHub Pages in P1; R2 only if files outgrow it), a data README with per-layer licences.

**Period data worth digitising** (public domain, georeferenced with QGIS): USGS historical topo sheets (topoView) for the bootheel; US Army Map Service 1:250,000 sheets of northern Chihuahua and Sonora from the Perry-Castañeda Library (confirm each sheet's PD status); from these, the Mexico Northwestern railroad, the Nacozari and Phelps Dodge lines, the old Douglas–Cloverdale road, and ranch headquarters.

**Accuracy targets.** Located: within 250 m of the gazetteer feature. Approximate: say what the pin stands in for. Inferred: never smaller than the evidence; a large honest blob beats a precise wrong pin.

## 8. Translations

Base: [A Translation of Spanish Passages in The Crossing](https://d41cfaf2-ac52-4400-a6e1-aaf2dee170dc.filesusr.com/ugd/842cf5_fac7639eeb8e4ed0812f996b15164ccd.pdf) by Lt. Jim Campbell, 15 pages, hosted by the Cormac McCarthy Society, keyed to Vintage pages 22–415, about 400 entries from single words to long speeches abbreviated with "…".

**What a first read shows.** A lone "70" where "Page 70" should be; Part Four's pages 353–357 listed after 368; scan errors ("Aiguien", "gruilas Ilegan", "tam bien", "corn i", "apagario"); accents stripped throughout; long stretches with no entries (Part One 51–69, Part Two 161–182, Part Three 245–259, Part Four 343–352 and 384–388). A heuristic count of Spanish-heavy paragraphs in the ebook gave about 53, 24, 99 and 56 for the four Parts; the gap check below gives the real figure.

**Gap check.** Language-ID every dialogue line and sentence (`lingua-py`, installed as `lingua-language-detector`), plus a Spanish word list for single terms in English sentences; fold accents and case; match guide entries with `rapidfuzz` (partial ratio ≥ 85); unmatched spans go to `review/translation-gaps.csv` with a draft translation and confidence. Review by hand, ideally with a speaker who knows northern Mexican usage. Never overwrite a guide entry; add a note beside it.

**Record per translation** (`translations.json`): `id`, `part`, `episode`, `page`, `es_incipit` (opening words only), `es_search` (accent-folded, index only), `en`, `source` (`campbell` or `site`), `confidence`, `speaker`, `listener`, `location_ref`, `first_seen`.

**Where it was spoken.** Each entry points to a stop, place or area. Talk on the road links to a corridor: the route segment buffered 2 km, labelled "on the road between X and Y". Selecting a place shows "Spoken here"; selecting a translation flies to its place and outlines the area. Search covers Spanish, English and place names, accent-insensitive, filtered by Part and source, and obeys the spoiler setting ("Se murió" is itself a spoiler).

**Permission.** Write to the Society (and Lt. Campbell if reachable) before launch. Until a yes arrives, the public build shows only site translations and links each guide page.

## 9. Interface

Full map with an info panel docked right on desktop (about 380 px) and a bottom drawer on mobile. Pattern names follow [Map UI Patterns](https://mapuipatterns.com/).

| Pattern | Use |
| --- | --- |
| Splash page + onboarding | Blurb and "How far have you read?" before the map |
| Timeline slider | Reading progress, one step per episode, labelled by Part |
| Data dimming | Routes not in focus fade; in step-through the road ahead fades |
| Route positioning | "Follow a journey": Back / Next through stops, camera flies to each |
| Visited marker | Passed stops change style |
| Basemap toggle + swipe | Literary / satellite, with a drag handle to compare over one view |
| Layer list + legend | One key: journeys by character, passing places, tale places, inferred areas, conversations, vignettes |
| Feature selection + MapTip | Tap to select; hover names on desktop |
| Search | Places and translations in one box |
| Extent-driven content | The panel's "In view" list follows the map |
| Overview map | Inset of the whole region when zoomed in; off-map arrows for far places |
| Cluster marker | Only around Cloverdale and the Peloncillos |
| Home button | Back to the whole journey |
| Scroll to pan | Story mode (P2) |
| (custom) How it's built | Architecture, decision records, data lineage, numbers (section 4.3) |

Avoid the kitchen sink (every layer on) and desert fog (an empty view with no cue). Empty desert is part of the book, so every view keeps a faint label or a route.

**React component plan.** `App` (hash router, reducer) → `MapView` (`@vis.gl/react-maplibre` `Map`; `LiterarySources`, `SatelliteSources`, `StoryLayers`, `GlyphLayer`, `VignetteLayer`, `SwipeControl`) · `Panel` / `Drawer` (same children, different shell; drawer heights peek 96 px, half 50%, full 92%) · `JourneyStepper` · `PlaceCard` · `TranslationList` · `SearchBox` · `ProgressSlider` · `LayerKey` · `OverviewInset` · `HowItsBuilt`. Keyboard-reachable controls, safe-area insets, reduced motion.

**Spoiler mode.** On by default until progress is set; a header badge always shows the setting and opens the slider; "Show everything" confirms once; stored in `localStorage`.

**Concepts.** P1 builds one, Endpaper, after two static mockups (the desktop mockup already made, plus a phone mockup with the drawer). The other two stay as P2 ideas: **Endpaper** (literary map is the page; satellite only through the swipe lens), **Field notebook** (desaturated satellite base, journeys inked on top, a geographer's notebook panel), **Crossings** (story mode: pinned map, scrolling episodes, free exploring at the end). Judge any concept on feel, 30-second comprehension, one-handed phone use, and 60 fps panning with all Part I layers on.

## 10. Illustrations: vignettes

The sea-monster idea, grounded. On old maps the empty quarters hold drawings that are not to scale and not in the exact place: a ship, a beast, a mission. Here they are the book's creatures, buildings and objects, drawn in one ink style and placed on the literary map near the thing they stand for. They are decoration with a source: each one is tied to an episode, carries `first_seen`, and has a note.

**Style.** Single-weight ink line (about 1.5 px at 1x), paper fill, light hatching for shadow on the south-east side only, no colour, drawn on a 96 × 96 grid, exported at 1x and 2x into the MapLibre sprite with `spreet`. Same light direction as the mountain glyphs.

**Placement rules** (so it never clutters):

- Each vignette has a geographic anchor and a zoom range (`min_zoom`, `max_zoom`) and a `priority`. MapLibre's symbol collision plus `symbol-sort-key` keeps at most one vignette per screen region; expect 3–6 in view at any zoom.
- Vignettes never sit on a stop marker or a label; the anchor is offset into empty country, with a hairline leader only if the thing is a real site (a church, a hacienda).
- They are part of the literary map only. Satellite view shows none.
- Spoiler mode hides those whose `first_seen` is later than the reader's progress.
- A reader can switch them off in the key.

**Candidate set** (about 30; the first dozen are enough for launch):

| Vignette | Anchor | Part |
| --- | --- | --- |
| The she-wolf, walking north | Peloncillos / Animas Valley | I |
| A steel trap with the drag | Hog Canyon trail | I |
| The boundary obelisk | the line near 108°30′ W | I |
| Antelope on the Animas Plains | Animas Plains | I |
| Bird, the horse (Billy's) | Cloverdale | I |
| The hacienda gate and the dog pit | the hacienda near Colonia Morelos | I |
| A brick Mormon storehouse | Colonia Morelos | I |
| The ruined church | Huisiachepic | II |
| La Purísima Concepción, half standing | Caborca (off-map arrow or inset) | II |
| An ox cart | Bavispe valley | II |
| The one-eyed horse Keno | Bacerac | II |
| Paquimé's mud walls | Casas Grandes | II |
| The Mexico Northwestern locomotive | Casas Grandes / Las Varas | II |
| The San Diego gate, "L. T." | Hacienda de San Diego | III |
| The opera caravan with its gilt | Madera road south of Las Varas | III |
| A Babícora Hereford (the mascareñas) | the Babícora plains | III |
| Oxen at the river | Santa María valley | III |
| The blind man with his cane | Parral road (inset) | III |
| Sandhill cranes | Chihuahua plains | III |
| The yellow bus / recruiting office | Deming (small) | IV |
| The red Waco biplane | over La Boquilla | IV |
| The gypsies' wrecked airplane | Casas Grandes River trail | IV |
| The guitar and the corrido | Bachíniva / Casas Grandes | IV |
| The crippled dog | the shed near the Black Range | IV |
| The false dawn | off-map arrow to the north-east | IV |

**Where the drawings come from**, in order: traced public-domain sources (1890s Boundary Commission photos of the monuments, Biodiversity Heritage Library plates for wolf, antelope and crane, period locomotive engravings, pre-1929 photographs of Paquimé), vectorised with `vtracer` or `potrace` and redrawn to one line weight in Inkscape; fresh drawings in the same style; image generation only as a sketch to trace over, never shipped as is.

**Photos.** Unchanged from v1: Commons by Wikidata P18 → category (P373) → geosearch within 5 km; licence from `extmetadata`; keep PD, CC0, CC BY, CC BY-SA only; you approve each in `review/photos.csv`; 800 px WebP in the repo with TASL credit under every photo and a Credits page. Captions say "today". Also check the Library of Congress ("no known restrictions") and the USGS photo library.

## 11. Build plan for Claude Code

**Repository layout**

```
crossing-map/
  site/                 Vite + React + TypeScript app
    src/components  src/map  src/store  src/data
    public/fonts/  public/glyphs/  public/sprites/  public/photos/
  data/                 Published GeoJSON + JSON (the open data)
    places.geojson  areas.geojson  journeys.geojson  stops.geojson
    conversations.geojson  vignettes.geojson  mountain_glyphs.geojson
    episodes.json  translations.json  schema/  README.md  LICENSE
  art/                  Vignette and mountain-glyph SVG sources, Inkscape files
  pipeline/             Python (uv): extract, pages, geocode, areas, routes, relief, glyphs, photos
    vendor/hachures/    Adapted copy of Huffman's Hachures script; GPL-3.0, with LICENSE and NOTICE
  review/               CSVs you approve (places, gaps, photos, glyph placements)
  tiles/                Build scripts; PMTiles output git-ignored, published as GitHub Release assets
  private/              Your book copy, extracted text, and inspiration/ images; git-ignored
  docs/                 This plan, decisions/ (one Markdown file per decision, rendered in the app), CHANGELOG, inspiration/ (link indexes only: guild.md, rumsey.md)
```

**How the work runs**

The work is split into seven stages. Each stage is a vertical slice: it ends with something visible and working, not a finished layer that nothing uses yet. Each stage is one branch and one pull request, merged and deployed when you accept it.

Three principles keep it quick without losing control:

- **Right before beautiful.** Geography is checked on satellite imagery in a plain style before any styling work, so you never polish a wrong map.
- **Part I is the template.** Everything is built and approved on Part I first; Parts II–IV then reuse the same pipeline, schema and style.
- **Decide on evidence, once.** Where taste or a trade-off is involved (relief, vignette placement, concept), Claude Code produces a comparison sheet and you pick. The pick is recorded and not reopened unless something breaks.

**The review packet.** Every stage ends with a packet in `review/stage-N/`, so you can review from your phone in 15–30 minutes:

1. `README.md`: what was built, what to look at, the questions that need your answer (no more than five), and what is left for later.
2. Screenshots from Playwright, desktop and phone, of the same named views every time (the bootheel, the Bavispe, Casas Grandes, the Babícora), so you can compare stage to stage.
3. For data stages, a checklist of places with their source, certainty and a link to the spot on the satellite view.
4. The CI result: schema checks, topology checks, spoiler check, bundle and tile sizes.
5. The live site, deployed from the branch to a `/preview/` path on GitHub Pages. Pages hosts one site per repository, so the deploy workflow builds `main` at the root and the current stage branch under `/preview/` in the same artifact: one preview slot, which is all a one-person project needs. v5, two details: the preview build sets Vite's `base` to `/crossing-map/preview/`; and the `github-pages` environment is normally limited to the default branch, so its deployment-branch rule must also allow `stage/*` for a branch run to deploy.

Inside a stage Claude Code works on its own; it stops early only for a blocking question or a decision the plan says is yours.

**Prerequisites (v5): work does not wait for them.** Claude Code builds everything that needs no prerequisite, across stages, in stage order. Where a prerequisite is missing it builds up to that point, leaves a stub that fails loudly with the name of what is missing, and adds a line to `TODO-prerequisites.md` at the repo root. You clear that list when you have time; each stage's review packet says what was stubbed.

| Needed | For | State on 11 November 2026 | Until it arrives |
| --- | --- | --- | --- |
| Node 22, npm 10, uv, GDAL 3.13 (Parquet and PMTiles drivers), tippecanoe 2.79, `pmtiles` CLI, `gh` | Stages 0–2 | Installed | n/a |
| Python 3.12 | Pipeline | uv installs it | n/a |
| Part I prototype data (places, stops, notes) | Stage 1 | In a claude.ai artifact | Places rebuilt from section 2.2 and the gazetteer; notes left empty |
| MapTiler account and origin-restricted key | Stage 1 | Yours to create; goes in a repository variable and `site/.env.local` | Satellite shows its "unavailable" state; the literary map does not need it |
| `spreet` | Stage 2 (sprites) | Missing | Installed by Claude Code when needed (cargo or brew) |
| QGIS, from your micromamba environment (`micromamba run ... qgis`) | Stage 3 | micromamba fails here with a missing `libnettle.8.dylib` (Homebrew moved to nettle 4.0); needs `brew reinstall micromamba` or similar | Glyphs and the hillshade control are built; hachure treatments wait |
| DRM-free EPUB of the novel | Stage 4 | In `private/` when you add it | Mentions come from section 2.2, without page anchors |
| Inkscape, `potrace` or `vtracer` | Stage 6 | Missing; you install when needed | Vignette anchors and placement rules only |

**Stage 0. Foundations** (about half a day)

- Build: repository, licences, `.gitignore` for `private/`, Vite + React + TypeScript, `@vis.gl/react-maplibre`, pinned versions, GitHub Actions (validate, build, deploy, preview path, tile download from a release), a small test PMTiles archive with a range-request check against the live site, JSON Schemas, the first decision records from 4.2, the review-packet script.
- You check: the live page opens on your phone; the repo layout makes sense.
- Done when: an empty map deploys from a pull request to the preview path and from `main` to the site, and the test archive answers a range request with `206`.

**Stage 1. Part I, right** (one to two sessions)

- Build: Part I places and stops in the schema from the prototype and the gazetteer; J1 and J2 routes (snapped where the text names a river or road, curves elsewhere); hand-drawn inferred areas with reasoning; displayed on MapTiler satellite in a plain style with the basic panel and stepper.
- You check: every stop and area against the imagery and the book, using the place checklist. This is the most important review in the project.
- Done when: you have signed off every Part I feature and its certainty.
- Meanwhile (you): fill `private/inspiration/` and the two index files from the Guild and the Rumsey shortlist.

**Stage 2. The literary base, first look** (one to two sessions)

- Build: Natural Earth, TIGER and INEGI vectors to PMTiles; NHD and INEGI rivers; self-hosted IM Fell glyphs; paper, ink, border and label styling; cartouche, compass, scale; Part I routes in their final ink; basemap toggle and swipe to satellite.
- You check: the bootheel and Bavispe views against the desktop mockup and the inspiration folder; type, colour and line weights.
- Done when: the base looks right at zoom 6–11 with no relief yet, and stays at 60 fps on a mid-range phone.

**Stage 3. Relief experiment, then relief** (one session for the experiment, one to build)

- Build: hachure settings found by running Huffman's script unmodified in QGIS on the three test areas; glyph generator; the hillshade test layer (Terrain Tiles repacked to raster-dem PMTiles; MapLibre shades it); the five-way comparison sheet from section 5.2. If hachures are chosen, the headless vendored copy as set out in D-relief-hachures. After your pick: production relief tiles for the whole story region, each PMTiles file under 100 MB.
- You check: the comparison sheet, then the chosen relief on the named views.
- Done when: relief is in, and a decision record says what was chosen and why.

**Stage 4. The rest of the book** (two batches, one to two sessions each)

- Batch A: Part II (J3, start of J4). Batch B: Parts III–IV (rest of J4, J5, J6 as reported, J7), tale places, La Babícora and Animas Valley regions, `episodes.json`.
- Build per batch: pipeline run (mentions, gazetteer, disambiguation), `review/places.csv` with candidates, routes, inferred areas; then the map in the approved style.
- You check: the review CSV for each batch (the pipeline only asks about ties and doubts), then the place checklist on satellite.
- Done when: all seven journeys are drawn and every feature is signed off.

**Stage 5. Reading features** (one to two sessions)

- Build: spoiler mode (progress slider, `first_seen` filtering, `note_safe`, cut routes) with the automated spoiler-leak test; translations (Campbell import or links, gap check, site translations with badges, place links); search; the full panel and the mobile drawer.
- You check: the gap list and draft translations; read the site as a first-time reader at three progress points.
- Done when: the spoiler test passes and the drawer works one-handed.

**Stage 6. Art, photos, and the "How it's built" page; launch** (one to two sessions)

- Build: the first dozen vignettes with placement rules; the photo pipeline with credits; About, Data (GeoJSON and GeoParquet) and Credits pages; the "How it's built" page from 4.3; accessibility and performance passes.
- You check: the vignette placements and the photo picks (both from review CSVs), then the whole site end to end.
- Done when: the acceptance criteria below are met. Soft launch, then Reddit.

**Phase 2 backlog** (pick by demand, not in order): land-cover marks among the hachures (scrub stipple, tree marks) from a land-cover dataset; Cloudflare R2 for larger tiles; Blender or Eduard relief; least-cost routes and constraint-built areas; Rumsey overlays with the swipe; story mode; a Spanish interface; more vignettes by an illustrator; speaker-reviewed translations; a paid MapTiler month around a spike; privacy-friendly analytics (for example GoatCounter) to see what people use; reader feedback on content (v5, revisit after launch): a way to report a wrong place, date, translation or note from the card it appears on, such as a prefilled GitHub issue form or a mail link that carries the feature id, with each accepted correction credited in the CHANGELOG.

**Acceptance criteria**

- [ ] Every feature has `certainty`, `source`, `source_licence`, `first_seen`.
- [ ] With progress set to any episode, nothing later shows anywhere (map, panel, search, translations, vignettes). Automated test.
- [ ] Every photo, tile set and dataset has visible attribution where shown and on the Credits page; the MapTiler logo shows on satellite.
- [ ] No passage of the novel is in the repo or the built site; Spanish appears only as incipits.
- [ ] GeoJSON downloads validate against the schemas and open in QGIS.
- [ ] The literary map works with MapTiler unreachable.
- [ ] Panel and drawer pass a one-handed phone test and keyboard-only use.
- [ ] $0 a month at 10,000 visits; satellite pauses rather than bills.

**How Claude Code should work with you**

- Plan mode at the start of each stage; list the files it will touch.
- Ask before any network batch (Nominatim, Commons, Wikidata) and show the request count. While you are away, a batch waits in `TODO-prerequisites.md` with its request count; single lookups of a few requests go ahead and are logged.
- Measurements (distances, areas, bearings) are computed with open-source tools (pyproj, GDAL, shapely) by a script in `pipeline/measure/`, stating the ellipsoid or projection, the coordinates and their source. Estimates are labelled as estimates.
- Never read `private/` into a commit, fixture or log.
- Every judgement call (which Sierra de la Madera, horse speed, a glyph's shape) goes in `docs/decisions/` with the reason. Technical choices get a decision record in the 4.2 format, because the site publishes them.
- Prefer the simplest thing that meets the acceptance criteria. If a step looks like P2 work, say so and ask before doing it.
- For style work, read `docs/inspiration/` and `private/inspiration/` first and name which reference each choice follows.

## 12. Open questions and launch

Settled: satellite provider (MapTiler), UI (React), illustrations (vignettes plus mountain glyphs), formats (GeoJSON for story data, PMTiles for the basemap, GeoParquet as a download), hosting (GitHub Pages in P1).

- [ ] **Translation permission.** Will you write to the Society and Lt. Campbell? Blocks the public build of stage 5's translations otherwise.
- [ ] **Relief tool (P2).** Hachures in P1; is $100 for Eduard acceptable later if a test on the Peloncillos looks much better?
- [ ] **Vignette drawing.** Will you draw or trace, or commission an illustrator for a consistent set of 30?
- [ ] **Name and domain.** "Map Enough" (from the trilogy's last line) or "The Crossing: A Reading Map"; custom domain or `username.github.io/crossing-map`.
- [ ] **Spoiler default.** On until set (proposed) or ask on first visit only.
- [ ] **Interface language.** English only for v1, or Spanish too.
- [ ] **Licences.** MIT code (except the GPL-3.0 hachure folder); CC BY 4.0 data and notes; ODbL noted where OSM-derived.
- [ ] **Reddit thread.** Paste the link so the launch post can reply there.
- [ ] **Portfolio framing.** Should the "How it's built" page carry your name and links (GitHub, LinkedIn, personal site), or stay anonymous with a link in the footer?
- [ ] **Inspiration folder.** Fill `private/inspiration/` and the `docs/inspiration/` indexes before stage 2, by hand as described in section 5.1.

**Launch.** Soft launch to a few readers (spoiler mode and inferred places are what to test); send the Society a link with the permission request and offer the data back; post on Reddit after reading the self-promotion rules, with the blurb, two screenshots (literary and the swipe) and a plain ask for corrections; reply in the existing thread with a short note and a link; log every correction in the CHANGELOG with credit.

## Sources

As of 8 November 2026, rechecked 11 November 2026 for v5 (MapTiler pricing, key and sessions-versus-requests pages; GitHub Pages limits; Protomaps cloud storage; Cloudflare Pages limits; the Hachures repository and script; the Guild `robots.txt`; npm versions). Pages opened or searched while writing this plan:

- [A Translation of Spanish Passages in The Crossing, Lt. Jim Campbell (PDF)](https://d41cfaf2-ac52-4400-a6e1-aaf2dee170dc.filesusr.com/ugd/842cf5_fac7639eeb8e4ed0812f996b15164ccd.pdf)
- [Map UI Patterns](https://mapuipatterns.com/)
- [Cloud-Optimized Geospatial Formats Guide](https://guide.cloudnativegeo.org/) and its [Format Selection Decision Framework](https://guide.cloudnativegeo.org/decision-framework/index.html) (maturity levels: COG L5, GeoParquet L4, FlatGeobuf L3; PMTiles for tiled web delivery; STAC for collection-level discovery at scale)
- [Protomaps: Cloud Storage for PMTiles](https://docs.protomaps.com/pmtiles/cloud-storage) (GitHub Pages works if the files fit) and [a note on Cloudflare Pages lacking range requests](https://staging-blog.pages.dev/writing/static-protomaps-on-cloudflare) (not rechecked in v5)
- [David Rumsey Map Collection: Wheeler Atlas Sheet 83 (1876)](https://davidrumsey.com/maps5853.html) and related catalogue records (Mallery and Ward 1877, Eckhoff and Riecker 1880, Rand McNally 1880); images CC BY-NC-SA
- [MapTiler Cloud pricing](https://www.maptiler.com/cloud/pricing/) (free plan: 5,000 sessions, 100,000 requests a month; session = a page load that initialises a map) and [MapTiler API key security](https://docs.maptiler.com/cloud/api/authentication-key/) (allowed HTTP origins)
- [MapTiler SDK JS](https://github.com/maptiler/maptiler-sdk-js) (styles `SATELLITE`, `HYBRID`; built on MapLibre)
- [ArcGIS Location Platform pricing](https://location.arcgis.com/pricing/) (2M basemap tiles a month free; alternative provider)
- [react-map-gl / @vis.gl/react-maplibre](https://github.com/visgl/react-map-gl) (v8.x, MapLibre-only endpoint)
- [Eduard relief shading](https://eduard.earth) and [Jenny et al., Cartographic Relief Shading with Neural Networks (arXiv 2020)](https://www.arxiv.org/abs/2010.01256); [Monash project note on Eduard's limits on mesas and plains](https://research.monash.edu/en/projects/national-geographic-relief-shading/)
- Cartographers' Guild tutorials (`robots.txt` disallows automated access; browse by hand): Gidde, *Hand-Drawn Map Tutorial (for the Artistically Challenged)*; Ironmetal250, *Hand-drawn mountains and other stylistic map elements*; RobA, *Creating old weathered paper* and *Simple Mountains in GIMP*; the *Saderan* tutorial; fantasticmaps.com mountain tutorials
- Historical maps: Ehrenberg, *Map of the Gadsden Purchase* (1858, relief by hachures); Mallery, *New map of the territory of Arizona, southern California and parts of Nevada, Utah and Sonora* (1876, Yale); RGS *Sketch Map of part of Sonora and Arizona* (1912); Fred Harvey *Illustrated Map of the Great Southwest* (1946); Ruth Taylor White *Arizona* (1935); Liozu *Arizona* (1946)
- [Hacienda de San Diego, Casas Grandes (Terrazas, 1902)](https://magicaltowns.mx/actividades/visita-la-hacienda-de-san-diego); [INAH note on the Babícora colonies and Hearst's 360,000 ha](https://www.inah.gob.mx/images/suplementos/20210301_gacetinah_009.pdf); [Boquilla y Anexas, Guerrero municipio (INEGI via citypopulation.de)](https://citypopulation.de/en/mexico/chihuahua/guerrero/080310024__boquilla_y_anexas); [El Berrendo, Chihuahua (Wikipedia)](https://en.wikipedia.org/wiki/El_Berrendo,_Chihuahua)
- [Variety in hachure, Carl Churchill (June 2025)](https://churchillgeo.com/variety-in-hachure/): a typology of hachure styles with archive links (Cram 1887 Arizona; SCOP *Ferrocarril Oaxaca a Ejutla* 1910; Graves *Map of Utah Territory* 1878; Chevalier San Francisco 1911; Imhof)
- [Hachures, Daniel Huffman (GitHub, GPL-3.0)](https://github.com/pinakographos/Hachures) and [Automated Hachuring in QGIS](https://somethingaboutmaps.wordpress.com/2024/07/07/automated-hachuring-in-qgis/)
- [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)
- Part I prototype: [The Crossing, Part I: a map of the two roads](https://claude.ai/artifact/QA95QAvy8YyhnUQo26ojay)
