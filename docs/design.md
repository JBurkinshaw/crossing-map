# The Crossing reading map: design

What the site is for, the rules it keeps, and how each part is meant to work. Open work is in [`roadmap.md`](roadmap.md), and each technical choice has a record in [`decisions/`](decisions/).

Section numbers are stable. Code comments, decision records, and review packets cite them as "plan section N", from when this document was the build plan.

## 1. Purpose and principles

A free, self-hosted reading guide to Cormac McCarthy's *The Crossing*: a map that follows every journey in the book, places each named location on real geodata, and links the Spanish dialogue to where it was spoken.

**Audience.** Readers of the novel, from first-timers, who need spoilers hidden, to rereaders, students, and McCarthy Society members. A second audience is geographers and borderlands enthusiasts who want to see the real country.

**Principles**

- **The feel of the book first.** Spare type, wide empty country, ink on paper. The land is the main character and the interface stays quiet. The map may take poetic licence (a wolf drawn larger than a mountain range); the data under it may not.
- **Accuracy is visible.** Every point, line, and area carries a certainty (located, approximate, inferred, reported) and its source. Line style and fuzzy areas show doubt.
- **Spoilers are opt-in.** A reader sets how far they have read, and the site shows nothing past that point.
- **Paraphrase, don't quote.** Notes are our own words. The site republishes no text from the novel.
- **Open data out.** Everything we make ships as documented GeoJSON that others can reuse.

**Blurb**, for the About page and the launch post:

> I read *All the Pretty Horses* years ago, and only recently got to *The Crossing*. It left me wanting to know the country its characters travel through, and the geographer in me needed to see these places more closely. *The Crossing* moves through real country: the Animas Valley, the Peloncillos, the Bavispe, the Babícora. This is a map of where Billy, Boyd, "the girl" and the she-wolf went, built from real geographic data and marked honestly where the book leaves us guessing.

"The girl" is always written in inverted commas: she is unnamed in the novel.

### 1.1 Two phases

Every feature is tagged **P1** (first release) or **P2** (later, only if readers use the site). A feature moves from P2 to P1 only if it makes reading better for most visitors, not because it is interesting to build. The P2 list is in [`roadmap.md`](roadmap.md#8-phase-2-backlog).

| | Phase 1 | Phase 2 |
| --- | --- | --- |
| Goal | A complete, accurate, good-looking reading map of the whole book | A deeper research tool |
| Hosting | GitHub Pages only, $0 | Cloudflare R2 for large tiles; a paid MapTiler month around a launch |
| Geometry | Gazetteer points; routes snapped to the rivers and roads the text names, gentle curves elsewhere; inferred areas drawn by hand with written reasoning | Least-cost routes over terrain; areas built from viewsheds and travel time |
| Relief | Generated hachures, mountain glyphs, and a hillshade | Hand-tuned hachures for key ranges; Eduard or Blender shading |
| Historical maps | Style references and links | Georeferenced overlays with a swipe |
| Translations | Our own, each linked to its page in Campbell's guide | Speaker review, audio |
| Data out | GeoJSON and GeoParquet downloads | A STAC catalogue, only if the files multiply |

## 2. The book, read for places

The novel has four Parts and no chapter numbers. McCarthy opens each scene with words in small capitals. There are 41 of these **episodes** (10, 8, 14, and 9 by Part), and they are the site's unit for chapters, reading progress, and step-through. Pages are cited by the 1995 Vintage International paperback, which Campbell's translation guide uses.

### 2.1 Episodes

| Part | Episodes (opening words, in order) |
| --- | --- |
| I | When they came south · They rode · When Billy · The wolf · In the woods · When they ran · He left · Two days later · They crossed · The hacienda |
| II | Doomed enterprises · When he had · He would cross · He was all day · When he got back · The sheriff looked · The house · He found Boyd |
| III | It was all but dark · They made camp · In three days' riding · They rode on south · In the evening · Noon the following day · They sat · They left the road · It was near midnight · The doctor's mozo · When Boyd awoke · It was almost dark · The next day · Three days later |
| IV | He crossed the border · He camped that night · He signed · He'd not got clear · None in that town · Gray sky · In the evening · Four days later · He woke |

The one-line summaries in `data/episodes.json` are written by hand, never taken from the text. Each sets up the episode's opening situation and states no outcome, so a first-time reader can see every line in the progress list.

### 2.2 Journeys, stop by stop

Each journey is a route layer, with stops in the order the book tells them. "(area)" marks a place drawn as an inferred area, not a point. The stops files in `pipeline/seeds/` hold the full detail and the reasoning for each stop.

**J1. The she-wolf, north out of Sonora (Part I).** Sierra de la Madera (eastern slopes) → crosses the Bavispe → the border at the thirtieth minute of the 108th meridian → the old Nations road → Whitewater Creek → San Luis Mountains → Animas range → Animas Valley → Peloncillos: Foster Draw (the calf) → ranges west into Cochise County: the south fork of Skeleton Creek, Starvation Canyon, Hog Canyon Springs → back to the high ground between the Clanton and Foster draws → trapped near the vaqueros' fire on Cloverdale Creek.

**J2. Billy's first crossing, with the wolf (Part I).** Cloverdale → Cloverdale Creek road → Robertson's crossfence (area) → a low pass in the easternmost Guadalupes → a ranch house on the volcanic plain (area) → the boundary, a monument in sight → the Cajon Bonita (the book's spelling) trail south → passes of the Sierra de la Cabellera → the Bavispe valley → the river crossing where deputies take him (named Colonia de Oaxaca only in 1-10) → an unnamed mud-house settlement (area) → Colonia Morelos and the fair → the hacienda by the river (area; the book does not name it, and calls the river beside it the Batopito, which GeoNames spells Batepito) → the fight → into the Pilares Teras with the dead wolf.

**J3. Billy alone in the Sierras, and home (Part II).** The Bavispe from a promontory → deep into the Sierras among the Indians' rancherías (area, weeks) → El Tigre, a mining town → a view east over the Bavispe barranca and the Carretas plain → the heretic's house at Huisiachepic, the ruined church, and the tale of Caborca → Tamichopa → Bacerac → Bavispe → Colonia de Oaxaca → Morelos → the road north toward Ojito → the border at Douglas → the old Douglas–Cloverdale road and a pass in the Guadalupes → the Animas Plain → the Parham house → Animas → Lordsburg (the sheriff) → the Websters' (Boyd).

**J4. Billy and Boyd, for the horses (Parts II and III).** Lordsburg → the alkali flats → San Simon Valley → the highway east of Bowie → the old road over the Dos Cabezas → Apache Pass → route 666 down the Sulphur Springs Valley → Elfrida → McNeal → Douglas → Agua Prieta → Ojito → Morelos (midnight) → the river towns → Bacerac (the one-eyed horse) → along the western flank of the ranges that close the Bavispe valley → the trail to the plains of Chihuahua → Colonia Juárez and the Casas Grandes River bridge → the walled ruins of an ancient mud city (Paquimé, unnamed in the text) → Casas Grandes (the Ferrocarril Noroeste de México; Soto; La Babícora and Hearst named) → the road south toward San Diego → "the girl" rescued (area, on the road) → the Hacienda de San Diego ("L. T.", Luis Terrazas; the opera troupe) → south toward Mata Ortiz, Las Varas, and Babícora → the opera caravan on the Madera road below Las Varas (area) → river camps → the old wagon road from La Norteña across the Babícora plains and the Santa María valley → Las Varas → the road to Boquilla → the hacienda at Boquilla → Quijada → leave the road north of town for the river → San José → the river camp where Boyd is shot (area) → the workers' truck → the blind man's house, then Mata Ortiz → San Diego, where Billy finds Boyd → Casas Grandes at 3 a.m. for the doctor → back to San Diego → Boyd and "the girl" gone. The book's compass does not close between the wagon road and Las Varas; the stops keep the text's order (decision recorded in the roadmap's modelled-routes notes).

**J5. Billy looking for Boyd and "the girl" (Part III).** San Diego → Mata Ortiz → Boquilla → Santa Ana de Babícora (midnight) → the road west to Namiquipa, home of "the girl" → back through Santa Ana, La Boquilla, Las Varas → a camp on the river south of Mata Ortiz → south as far as Cuauhtémoc, north again to Namiquipa, the Buenaventura crossroads, Álamo, Galeana → Casas Grandes (December, broke).

**J6. Boyd and "the girl" (Parts III and IV, reported).** From the workers' truck north to San Diego → Namiquipa (her mother) → Bachíniva (the corrido's account) → Galeana → San Lorenzo, where Quijada says Boyd was shot → San Buenaventura, where he was buried. Every stop and segment is `reported`, each tagged with who tells it: the Mata Ortiz woman, the Muñoz woman, the woman at the Namiquipa wake, the singer at the Camino Recto hotel, and Quijada.

**J7. Billy's war years and third crossing (Part IV).** The border at Columbus → Deming (the recruiting sergeant) → bus to El Paso → Deming → Albuquerque (rejected again) → bus south past Socorro → Deming → the old road to Hermanas and Hachita → the Little Hatchet foothills → Gillespie Mountain in snow, the Animas Peaks → the old Playas road → Animas Valley → the Sanders ranch → camps on the Animas Plain → the Hashknife linecamp on the Little Colorado (reported) → Socorro, Magdalena, the plains of San Agustín → Silver City → a ranch out of Magdalena until March → south past Steins → the SK Bar gate → Mexican customs at El Berrendo (the text's "Berendo") → an abandoned ranch west of Ascensión → Janos → Casas Grandes → San Diego → Las Varas → La Boquilla (the red Waco plane) → Babícora and Santa Ana → Namiquipa (the road from Santa Ana runs north here, where 3-12 had it west) → the woman who says the bones lie at San Buenaventura → Temósachic (the corrido) → Madera (the April fair) → Babícora again → Casas Grandes (the singer's corrido) → the high country of the Babícora → Quijada → San Buenaventura (the grave) → the attack on the road, Niño stabbed (area) → the gypsies with the airplane → north past Casas Grandes, across the Guzmán–Sabinal road, along the Casas Grandes River → Hermanas → the Animas Valley with the travois → Animas on Ash Wednesday (the burial, in the cemetery south of town) → Silver City, Duncan, Glenwood, Reserve → July: Silver City, the old road east by the Santa Rita mines, San Lorenzo, the Black Range → the shed, the crippled dog, the false dawn. The false dawn is widely read as the Trinity test of 16 July 1945, seen from the south-west; the text names no place or event.

### 2.3 Places named in passing or in tales

The place seeds in `pipeline/seeds/` list every named place, in journey order with tale places after them, and record the book's own spellings where they differ (Batopite, Berendo, Hatchita, Window for Winslow, Fort Summer for Fort Sumner, Ignacio Zaragosa, "plains of Saint Augustine"). Not seeded: streets, buildings, roads and railroads, unnamed stops, broad regions, states, and countries. Roads and unnamed stops come back as route segments and inferred areas. Waco is the make of the red plane, not a place. Places outside the story box are listed in the panel from `data/elsewhere.json`, not mapped.

### 2.4 Facts checked against sources

| In the book | What it is | How it is placed |
| --- | --- | --- |
| Hacienda de San Diego, initials L. T. | Luis Terrazas's hacienda (1902) on the road from Casas Grandes to Mata Ortiz | A real site, with photos on Commons |
| La Babícora, "a señor Hearst" | William Randolph Hearst's ranch, about 360,000 ha across Temósachic, Namiquipa, Madera, and Gómez Farías, broken up in 1954 | A region polygon, labelled La Babícora |
| Boquilla, Boquilla y Anexas | The town by the Babícora lake on the road east from Las Varas (3-04, 4-04): La Boquilla in Gómez Farías municipio, GeoNames 8749710 | Not INEGI's Boquilla y Anexas in Guerrero municipio, 135 km from Las Varas, and not the Boquilla dam near Camargo |
| Berendo, Mexican customs | El Berrendo, Chihuahua: the Antelope Wells crossing at the foot of the bootheel | Not Palomas, which the book names separately |
| Colonia Juárez | The Mormon colony on the Casas Grandes River | A real place; Colonia Dublán nearby is not named |
| The walled ruins seen from the road | Paquimé, the Casas Grandes archaeological zone | A vignette |
| The railroad at Casas Grandes, the Las Varas crossing, the Madera tracks | The Ferrocarril Noroeste de México, Juárez–Casas Grandes–Madera | Natural Earth railroads |
| Mata Ortiz | Juan Mata Ortiz, about 23 km south-south-west of Casas Grandes (geodesic, Wikidata Q3867357 to Q4284456) | The railroad town of the book |
| The false dawn | Consistent with the Trinity test; the site is about 147 km north-east of the Black Range crest (geodesic from the Emory Pass marker, Q49487009, to the Trinity Site, Q19842077; read as 145–150 km, since where Billy stands is unknown) | A direction, `reported` |

Every distance here is computed by `pipeline/measure/distances.py` (pyproj, WGS 84 ellipsoid) from cited coordinates.

## 3. Copyright and licensing

The novel and Campbell's guide are under copyright, and the public site republishes neither. This is a working checklist, not legal advice.

| Material | Rule | Attribution |
| --- | --- | --- |
| The novel | No passages. Notes are paraphrase. Spanish appears only as an incipit of at most five words, with a page | Title, author, Vintage edition, page |
| Campbell's translation guide | Not copied. The site writes its own translations and links each to its page in the guide. No permission is sought for this | "Campbell's guide: Lt. Jim Campbell, cormacmccarthy.com", on each entry and on the Credits page |
| Our translations and notes | Ours, marked "Added by this site" with a confidence | CC BY 4.0 |
| The book text in the pipeline | The owner's own copy, on the owner's machine only. Never commit text, or offsets that would rebuild it | n/a |
| Wikimedia Commons photos | PD, CC0, CC BY, and CC BY-SA only. No NC, ND, or non-free files | Title, author, source, licence |
| Natural Earth; USGS GNIS, NHD, 3DEP; US Census TIGER | Public domain | Courtesy credit |
| Copernicus GLO-30 DEM (hachures, peaks, Raised) | Free licence; the exact notice is required | The notice, on the Credits page and in `data/README.md` |
| AWS Terrain Tiles (the hillshade and 3D terrain) | Mixed sources, each credited | "3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey" and "Source: INEGI, Continental relief, 2016", on the map wherever terrain shows and on the Credits page |
| INEGI | Free-use terms, attribution required | "Fuente: INEGI" and the dataset |
| GeoNames | CC BY 4.0 | "GeoNames", with a link |
| Wikidata | CC0 | Courtesy link |
| MapTiler | The free plan is non-commercial; logo and attribution required on screen | MapTiler logo and "© MapTiler © OpenStreetMap contributors" |
| Huffman's Hachures script | GPL-3.0, vendored with its licence in `pipeline/relief/hachures/`, whose README lists every change; called as a separate process (decision 0015). The generated lines are our data | Credits page and README |
| Reference images (Cartographers' Guild, Rumsey scans) | Not ours to republish. Images stay in `private/inspiration/`; the repo holds only indexes of titles and links (`docs/inspiration/`) | Links on the Credits page |
| Public-domain art traced for vignettes and glyphs | Only works with clear PD status (US government reports, pre-1929 plates) | Credits page |
| Bell (2000), *Contextualizing Cormac McCarthy's Border Trilogy* | Facts (where a place is, which page names it) are free to use; his prose is not, nor the novel passages he quotes. We paraphrase with a page citation. The PDF and anything extracted from it stay in `private/sources/`. His figures are road-atlas excerpts: we read positions off them and never reproduce them | Full citation with the page, on each card that uses it and on the Credits page |
| Joe Hazelton's Gaia GPS map of *The Crossing* | The positions are facts, but copying the set wholesale would relicense his compilation. His notes are copied from Bell, so they are never used. The waypoints were read in a browser and stay in `private/`. The permission request is drafted and not yet sent; until he replies, the site uses his points with credit, and any point with no other source must be removable if he declines | "Also placed by" with a link to his thread, on each card that uses it and on the Credits page |
| Library of Congress Sanborn maps (for street-level places) | Public domain up to 1929; later sheets checked one by one | Sheet title and date |
| OpenStreetMap | Not used in the data. If a feature ever comes from OSM, it carries the ODbL and `data/README.md` lists it | "© OpenStreetMap contributors" |

Every feature has a `source`. Prefer Wikidata, GNIS, GeoNames, and INEGI.

## 4. Architecture

### 4.1 The shape of the system

A static site, a folder of small GeoJSON files, a few PMTiles archives, and one third-party tile service for satellite. No server, no database, and no API key except MapTiler's public, origin-restricted one.

```text
 The owner's machine (private)               GitHub repo                       Browser
 ┌────────────────────────┐   GeoJSON,    ┌──────────────────────────┐   HTTPS   ┌─────────────────────────────┐
 │ Python pipeline (uv)    │──PMTiles────▶│ data/  *.geojson          │──────────▶│ React + MapLibre            │
 │ book copy, DEM, NE,     │   review CSV │ tiles: release assets     │  range     │  story layers (GeoJSON)     │
 │ GNIS, INEGI, Wikidata   │              │ site/  Vite build         │  requests  │  literary base (PMTiles)    │
 └────────────────────────┘              │ docs/decisions/*.md       │           │  satellite (MapTiler, lazy) │
                                          └──────────┬───────────────┘           └─────────────────────────────┘
                                                     │ GitHub Actions: validate, build, deploy to Pages
```

### 4.2 Decisions

Each choice is a record in [`decisions/`](decisions/README.md), checked against the Cloud-Native Geospatial Forum's [Cloud-Optimized Geospatial Formats Guide](https://guide.cloudnativegeo.org/). Applied to this project, the guide points to one cloud-optimized format, PMTiles for the basemap, and plain files for everything else, because the story data is small and always read whole.

| Area | Choice | Record |
| --- | --- | --- |
| Story data | Plain GeoJSON, one file per layer | 0001 |
| Basemap and relief | PMTiles archives built with tippecanoe | 0002 |
| Hosting | GitHub Pages, `main` at the root and the newest stage branch under `/preview/` | 0003 |
| Tile delivery | GitHub Release assets, pinned by `tiles/release.txt` | 0004 |
| Satellite | MapTiler SDK JS, created on demand | 0005, 0012 |
| Front end | React, TypeScript, Vite, MapLibre GL JS | 0006 |
| Pipeline | Python with uv | 0007 |
| Inferred areas | Drawn by hand, with reasoning | 0008 |
| Downloads | GeoJSON and GeoParquet | 0009 |
| Spoiler dates | Each feature dated by the episode that first names it | 0010 |
| Elevation | Terrain Tiles for display, Copernicus for analysis | 0011 |
| Relief | Vendored hachure generator, S5 style | 0015, 0016 |
| Views | Flat, Tilted, and Raised | 0017, 0019 |

State is a `useReducer` plus the URL hash. Search is MiniSearch over places, stops, and translations, built in the browser.

### 4.3 The "How it's built" page

The site explains itself at `#/about/how-its-built`:

1. **The architecture diagram** (4.1), drawn in the site's ink style.
2. **Decision records.** Vite imports `docs/decisions/*.md` at build time and the page lists them, so the page and the real decision log cannot drift.
3. **Data lineage.** Counts by `certainty`, `source`, and `method`, computed from the GeoJSON at build time.
4. **Numbers.** Each tile archive's size and the total data size, read at build time.
5. **Links** to the repository, the downloads and schemas, and the credits.

Every place card also shows its certainty, source, and method, so the craft is visible where readers look.

### 4.4 Maintainability rules

- One way to do each thing: one map library, one state library, one data format per layer. The one exception is MapTiler SDK JS, itself a MapLibre build, loaded as a lazy chunk for satellite only (decision 0005).
- Data is the source of truth. The UI reads the GeoJSON; nothing about a place lives in component code.
- Pin versions and record significant ones in a decision record.
- Dependabot is on; upgrades are merged deliberately.

## 5. Basemaps

The **classic map** is ours, self-hosted, and the default. Satellite and Topo come from MapTiler, and Compare splits the view between the classic map and satellite. The classic map has three views: Flat, Tilted, and Raised (decision 0017).

### 5.1 The classic map: design brief

The look is an endpaper map from a 1940s novel, drawn by a surveyor who also sketches: ink on toned paper, a hand-lettered feel, mountains drawn as mountains, rivers as living lines, and small drawings in the empty quarters. Everything under it is real geodata.

**References**, in three families:

| Family | Examples | Take from it |
| --- | --- | --- |
| Historical survey maps of this region | Ehrenberg's 1858 *Map of the Gadsden Purchase*; SCOP railroad maps of Mexico, about 1910; Mallery's 1876 *New map of the territory of Arizona … and Sonora*; the RGS 1912 *Sketch Map of part of Sonora and Arizona*; the 1890s US–Mexico Boundary Commission sheets; the Wheeler Survey sheets | Hachured ranges, spaced italic range names, dotted trails, the dash-dot international line, sparse towns, the look of blank desert |
| Pictorial maps of the Southwest | Fred Harvey's *Illustrated Map of the Great Southwest* (1946); Ruth Taylor White's *Arizona* (1935); 1930s Shell road maps | Vignettes placed with poetic licence; one hero drawing per region |
| Modern hand-drawn style (Cartographers' Guild and others) | The Guild tutorials indexed in `docs/inspiration/guild.md`; John Nelson's Tolkien-style map from real terrain | Profile mountains with a consistent light side; restraint in label density |

**Hachure styles.** Carl Churchill's [Variety in hachure](https://churchillgeo.com/variety-in-hachure/) separates systematic survey hachure (lines downslope, denser where steeper) from the caterpillar chains of many "Old West" maps. The map uses the systematic kind, generated from the DEM, so it is accurate by construction. It keeps Churchill's caution too: these survey styles grew up alongside conquest and extraction, and *The Crossing* is partly about land taken and held. So the map borrows the craft, draws the Mexican side from Mexican mapmakers as well as US surveys, and avoids the prospectus look: no resources drawn as prizes, no empty land waiting to be claimed.

**Design tokens** (`site/src/map/tokens.ts`). Cream paper after the Wheeler Survey's sheet 70A, brown-black hachures (decision 0022), iron-gall ink, the Mexico side a shade darker, water in blue-grey ink, and one ink per journey, after the hand-coloured tints of period atlas maps: indigo J1, vermilion J2, oxblood J3, sap green J4, ochre J5, violet J6, rose madder J7 (decision 0033). A route line's dash says how sure it is: solid where it follows the road or river the book names, long dashes for a modelled path, sparse short dashes, thinner and lighter, for a curve that only joins the stops. One light theme. Type: IM Fell English for labels and notes, IM Fell English SC for states and counties, both under the OFL.

Reference images are studied in a browser by hand. The Guild's `robots.txt` disallows automated agents, and the Rumsey catalogue serves a bot check. Nothing from either goes into the site or the repository; any style taken is redrawn in our own hand.

### 5.2 Relief

Relief is drawn as the 1850s–1880s survey maps drew it, with hachures, plus small drawn mountains on significant summits, as on a novel's endpaper. Both come from real elevation data. The style is S5 (decision 0016): an Imhof-style desert tint below zoom 10, then light hachures, contours, and a light hillshade above.

**Terms.** A *hillshade* is a raster image of the terrain lit from one direction, computed from a digital elevation model (DEM). *Hachures* are vector lines drawn downslope, closer and heavier where the ground is steeper. *PMTiles* is a container for map tiles, vector or raster, one kind per file.

**Hachures** (`crossing.hachures`, decisions 0015 and 0016). Daniel Huffman's [Hachures](https://github.com/pinakographos/Hachures) script, vendored with absolute slope limits in degrees and an absolute contour interval in metres, runs headless in QGIS on a fixed UTM 12N tile grid over the Copernicus GLO-30 DEM. Copernicus is used, not Terrain Tiles, because the method needs one uniform resolution (decision 0011).

- Fine strokes (30 m DEM) cover a corridor 20 km either side of the legs ridden or walked. Bus and train legs, ranch work told in summary, and the reported J6 get coarse relief only.
- Coarse lines (90 m DEM) cover wherever the cached DEM tiles reach.
- A denser set draws from zoom 12, cross-faded with the zoom 10–11 set.
- Inside the corridor the site draws Wheeler-style strokes in place of the fine and dense sets (decision 0024, `crossing.wheeler_hachures`): short strokes of one width, packed closer on steep ground, with crests, summits, mesa tops and valley floors left white and escarpments drawn as a comb of wedges. The fine and dense sets are still built and released, and one switch in the style (`HACHURE_SET`) brings them back.
- Basin floors stay blank, which is what makes the Animas Valley and the Chihuahua plains read as open country.

**Mountain glyphs** (`crossing.peaks`, `crossing.landforms`, `art/glyphs/`).

1. Peaks come from the DEM by topographic prominence (the key-col method). Kept: summits with enough prominence, named mesas, buttes, and cones from a lower threshold, and every summit the book names.
2. Each summit's landform family (peak, dome, mesa, butte, cone, ridge, pass) comes from what the gazetteer calls it: points for words in its name (Mesa, Cerro, Peak, Butte, Sierra, Loma and others) and for its feature code. A summit the gazetteer says nothing about is a peak. The DEM is measured but does not score (`use_dem = false`, the owner's decision of 14 November 2026). Every weight is in `pipeline/seeds/landforms.toml`, and `review/stage-3/landforms.csv` shows each summit's scores and what the DEM alone would have chosen.
3. Each glyph takes a stable shape, flip, scale, and rotation from a seed made from the summit's id, so the result varies but does not change between builds. Size follows prominence. MapLibre cannot mirror an icon, so the sprite carries a mirrored twin of each shape.
4. Glyphs draw over the hachures and knock them out with a paper-coloured fill inside each drawing.

The glyph families are still generated, now drawn with a pen treatment (`art/pen.py`, variant B of the glyph trial, chosen on 14 November 2026): each line is a tapered stroke whose width follows the pen's pressure and whose path wanders a little, the outline lifts and meets at the summit with a small gap or overshoot, and the hatching is loose and sometimes broken. The vignettes use the same pen, so the two read as one hand.

**Hillshade and 3D terrain** (`terrain.pmtiles`, decision 0011). AWS Terrain Tiles for the story box at zoom 5–10, repacked into our own raster-dem archive. MapLibre shades it in the browser and uses it for the Tilted view.

**The Raised view** (`crossing.plan_oblique`, decisions 0017 to 0019). Plan oblique relief: every point of the line work moves north in proportion to its height, so ranges stand up from a flat, north-up map. It covers the corridor of the legs ridden or walked, and the story layers are shifted to match in `data/raised/`.

### 5.3 Satellite and Topo: MapTiler

MapTiler gives satellite imagery and a modern topographic style through an SDK built on MapLibre, on a free non-commercial plan that pauses rather than bills.

| Item | Value (checked 2026-11-11) |
| --- | --- |
| Free plan | 5,000 map sessions and 100,000 API requests a month; the MapTiler logo required; one API key; the service pauses when the quota is used up |
| Session | A page load that creates a map. Sessions are counted only for maps made with MapTiler SDK JS; tiles fetched by plain MapLibre are billed per request, which a few hundred visitors would exhaust |
| Key security | Restricted by allowed HTTP origins |
| Paid fallback | Flex, about $30 a month, for a launch month. It bills overage instead of pausing, so downgrade after the spike |

Three rules protect the quota (decision 0005):

1. The classic map is the default and never touches MapTiler, so the site works in full without it.
2. The MapTiler map is created only when a reader first leaves the classic map or turns on Satellite tint, then kept, so switching back and forth costs one session.
3. A refused key or a paused quota shows a "satellite unavailable" notice, and the classic map carries on.

[ArcGIS Location Platform](https://location.arcgis.com/pricing/) (2 million basemap tiles a month free) is the alternative if the quota becomes a problem.

### 5.4 Historical maps: the David Rumsey Map Collection

The [David Rumsey Map Collection](https://www.davidrumsey.com/) holds period maps of this country, many of them hachured surveys. Its images are CC BY-NC-SA, so anything derived from them must be shared the same way, and none of it goes into this MIT repository.

- **P1:** style references. The shortlist and links are in `docs/inspiration/rumsey.md`; downloaded previews stay in `private/inspiration/rumsey/`. The catalogue cannot be fetched by script, so pages are opened in a browser by hand.
- **P2:** georeferenced overlays, shown through the same swipe as satellite, so a reader can compare an 1876 survey, the classic map, and today's imagery over one view.

## 6. Data model

All story data is GeoJSON (WGS 84, RFC 7946), one file per layer, with one shared property schema. A GeoParquet copy of each layer is generated for download. [`data/README.md`](../data/README.md) lists every published file and its licence, and the JSON Schemas in [`data/schema/`](../data/schema/) are the field-by-field data dictionary.

The main ideas behind the fields:

- **`certainty`:** `located` (a gazetteer match for the exact feature), `approximate` (the pin stands in for something larger, such as a range), `inferred` (no name; built from clues), or `reported` (a character's account).
- **`method`** on route segments: `narrated-path` (the text names the road, river, or trail, and the segment follows it), `modeled` (a least-cost path), or `schematic` (a gentle curve, for want of better evidence).
- **`first_seen`:** the earliest episode in which the feature may appear (decision 0010). The spoiler filter hides later features and cuts routes.
- **`reasoning`:** for inferred and judged features, the clues used, in plain words.
- **`source`, `source_id`, `source_licence`:** the dataset that fixed the coordinates, and its terms.

IDs are stable slugs. Reader-visible changes to the data go in [`CHANGELOG.md`](CHANGELOG.md).

## 7. Geodata pipeline

The pipeline runs locally in Python, keeps the book text private, and writes only GeoJSON, JSON, review CSVs, and logs to the repository. The owner decides everything a script cannot. The commands and run order are in [`pipeline.md`](pipeline.md).

1. **Episodes and mentions (private).** `crossing.extract` reads the owner's DRM-free EPUB. It splits the text into the 41 episodes at the capitalised scene openings, and finds the first episode that names each seed place, under any spelling the seeds list. It writes only episode numbers and counts, to `private/book/`.
2. **Resolve names.** `crossing.gazetteer` matches each seed against USGS GNIS, GeoNames, and Wikidata inside the story box (about 104°–113° W, 27°–36° N). It scores candidates by expected feature type and region and by distance to the neighbouring stops. A seed is resolved only when every candidate agrees; otherwise it goes to review, with every candidate listed.
3. **Review.** The owner checks picks against imagery and the text. Hand decisions are recorded in the place-override seeds, each with its reasoning.
4. **Build the story.** `crossing.build_story` writes the places, stops, areas, and journeys. A segment follows the NHD flowline, TIGER road, or Natural Earth river its snap names, and is a gentle curve elsewhere. Inferred areas are circles sized to the doubt until they are drawn by hand (decision 0008).
5. **Relief and glyphs.** `crossing.peaks`, `crossing.landforms`, `crossing.hachures`, and `crossing.plan_oblique`, as in section 5.2.
6. **Translations.** `crossing.translations`, as in section 8.
7. **Validate.** `crossing.validate` checks every published file against its schema, and the spoiler rules that link files. `crossing.echo_check` checks that no run of eight words is shared with the novel.
8. **Publish.** GeoJSON and GeoParquet to `data/`, and PMTiles to a GitHub Release that the deploy workflow downloads.

**Period data worth digitising** (public domain): USGS historical topographic sheets for the bootheel, and US Army Map Service 1:250,000 sheets of northern Chihuahua and Sonora (checking each sheet's status). From them: the Noroeste railroad, the old Douglas–Cloverdale road, and ranch headquarters.

**Accuracy targets.** Located: within 250 m of the gazetteer feature. Approximate: say what the pin stands for. Inferred: never smaller than the evidence; a large honest area beats a precise wrong pin.

## 8. Translations

The base is Lt. Jim Campbell's [A Translation of Spanish Passages in The Crossing](https://d41cfaf2-ac52-4400-a6e1-aaf2dee170dc.filesusr.com/ugd/842cf5_fac7639eeb8e4ed0812f996b15164ccd.pdf), hosted by the Cormac McCarthy Society: 15 pages keyed to Vintage pages 22–415, with about 400 entries. It has gaps (long stretches with no entries), scan errors, stripped accents, and some misprinted page numbers.

**Method** (`crossing.translations`). Every Spanish sentence and phrase in the text is found by language identification (lingua) plus a Spanish word list, accent- and case-folded, and matched to guide entries by fuzzy matching (rapidfuzz). Matched entries anchor page numbers. Every line gets our own English, never the guide's, with a confidence, and a link to the guide page where one exists. The guide's English is never stored or compared.

**Review.** Readers review translations: each line has a "Suggest a better translation" link to a prefilled GitHub issue, and accepted suggestions are credited in the changelog. A guide entry is never overwritten; a note sits beside it.

**Where it was spoken.** Each line points to a stop, place, or area where the text allows. Talk on the road points to a route segment, and the map outlines a corridor 2 km either side of it, labelled "on the road between X and Y". A selected place shows "Spoken here", and a selected line flies to its place.

**Search** covers Spanish, English, and place names, accent-insensitive, and obeys the reading progress ("Se murió" is itself a spoiler).

## 9. Interface

The map fills the screen, with a panel docked right on desktop (about 380 px) and a bottom drawer on phones (peek, half, and full heights). Pattern names follow [Map UI Patterns](https://mapuipatterns.com/).

| Pattern | Use |
| --- | --- |
| Onboarding | One dialog on the first visit (decision 0034). It says what the site is and how to use the map, then asks "Have you finished *The Crossing*?". "Yes" shows everything; "Not yet" asks where the reader is up to. It opens again on each visit until the reader answers; the panel's Introduction link and the About page bring it back |
| Timeline | Reading progress: the episodes' opening words, grouped by Part, plus "I haven't started". Shortcuts take a percentage (for ebooks) or, once `episodes.json` has pages, a Vintage page. A summary shows only for episodes up to the stored progress |
| Data dimming | Routes not in focus fade; once the reader goes to a stop, the legs after it fade |
| Route positioning | Back and Next through a journey's stops; the camera flies to each |
| Basemap switch and swipe | Classic, Compare, Satellite, Topo; Flat, Tilted, Raised |
| Layer key | Journeys by ink, how sure each line is, passing places, tale places, inferred areas and regions, vignettes |
| Feature selection | Tap to select; names on hover on desktop |
| Search | Places, stops, and translations in one box |
| Overview map | An inset of the whole region when zoomed in |
| Cluster marker | Only where the map is crowded, around Cloverdale and the Peloncillos |
| Home button | Back to the whole journey |
| How it's built | Section 4.3 |

Avoid the kitchen sink (every layer on) and desert fog (an empty view with no cue). Empty desert is part of the book, so every view keeps a faint label or a route.

**Spoiler mode.** On until the reader answers the first-visit question. A header badge always says what is hidden ("Showing everything", "Hiding what's after Part I, episode 5: In the woods", or "Not set") and opens "Where are you up to?". There, "Show everything" asks for confirmation; the first visit's "Yes" does not, as it answers a direct question. Setting progress to an episode brings the stop the reader reached most recently into focus. Progress is stored in `localStorage`.

**Usability targets.** Keyboard-reachable controls, safe-area insets, reduced motion respected, one-handed use on a phone, and smooth panning with every Part I layer on.

## 10. Illustrations: vignettes

On old maps the empty quarters hold drawings that are not to scale and not quite in place: a ship, a beast, a mission. Here they are the book's creatures, buildings, and objects, drawn in one ink style and placed near the thing they stand for. Each is tied to an episode, carries `first_seen`, and has a note.

**Style.** Drawn with the mountain glyphs' pen (`art/pen.py`): tapered ink strokes that wander a little, outlines that lift and meet with a small gap or overshoot, and loose, sometimes broken hatching on the south-east side. Two inks only, ink and paper, with a paper halo round every stroke; drawn on a 96 × 96 grid (`art/vignettes/`) and exported at 1x and 2x into the sprite with `spreet`. The light comes from the same direction as on the mountain glyphs. Each drawing looks roughly as its subject did around 1940, after the references its credit names, and carries a short italic label under it (the seed's `label`), after "The Trail of Blood Meridian" map. The Credits page lists each drawing's `credit`, for the drawings the reader has reached.

**Placement rules**

- Each vignette stands on the stop or place it is for, with a `side`, a `min_zoom` from which it shows at every closer zoom, and a `priority` (decision 0026).
- The drawing is set beside its pin on that side, a fixed gap away on screen, so it never covers the marker; no leader lines. Place labels draw over it; its caption is placed before every other label. The key says its position is approximate.
- Vignettes belong to the classic map only.
- Spoiler mode hides those first seen after the reader's progress.

**Candidates** (about 30; the anchors in `pipeline/seeds/vignettes.csv` are the current picks):

| Vignette | Anchor | Part |
| --- | --- | --- |
| The she-wolf, walking north | Peloncillos or the Animas Valley | I |
| A steel trap with the drag | Hog Canyon trail | I |
| The boundary obelisk | the line near the wolf's crossing | I |
| Antelope on the Animas Plains | Animas Plains | I |
| Bird, Billy's horse | Cloverdale | I |
| The cockpit at the hacienda | the hacienda near Colonia Morelos | I |
| A brick Mormon storehouse | Colonia Morelos | I |
| The ruined church | Huisiachepic | II |
| An ox cart | Bavispe valley | II |
| The one-eyed horse | Bacerac | II |
| Paquimé's mud walls | Casas Grandes | II |
| The Noroeste locomotive | Casas Grandes or Las Varas | II |
| The San Diego house front, "L. T." | Hacienda de San Diego | III |
| The opera caravan | the Madera road south of Las Varas | III |
| A Babícora Hereford | the Babícora plains | III |
| Sandhill cranes | the Chihuahua plains | III |
| The red Waco biplane | over La Boquilla | IV |
| The gypsies' wrecked airplane | the Casas Grandes River trail | IV |
| The guitar and the corrido | Bachíniva or Casas Grandes | IV |
| The crippled dog | the shed near the Black Range | IV |
| The Trinity cloud | the Trinity Site, shown from 4-09 | IV |

**Where drawings come from**, in order: traced public-domain sources (Boundary Commission monument photos, Biodiversity Heritage Library plates, period engravings, pre-1929 photographs), vectorised with `vtracer` or `potrace` and redrawn to one line weight; fresh drawings in the same style; image generation only as a sketch to trace over, never shipped as it is.

**Photos.** Commons files found through Wikidata (P18), then the item's Commons category (P373), then a geosearch within 5 km (`crossing.photos`). Only PD, CC0, CC BY, and CC BY-SA. The owner approves each in `review/stage-6/photos.csv`. Picked photos are 800 px WebP with a TASL credit under each and on the Credits page, and captions say "today".

## 11. Acceptance criteria

The site is ready to launch when all of these hold. [`roadmap.md`](roadmap.md#9-acceptance-criteria) tracks their status.

- Every feature has `certainty`, `source`, `source_licence`, and `first_seen`.
- With progress set to any episode, nothing later shows anywhere: map, panel, search, translations, vignettes, pages. An automated test checks it.
- Every photo, tile set, and dataset has visible attribution where shown and on the Credits page, and the MapTiler logo shows on satellite.
- No passage of the novel is in the repository or the built site, and Spanish appears only as incipits.
- The GeoJSON downloads validate against the schemas and open in QGIS.
- The classic map works with MapTiler unreachable.
- The panel and drawer pass a one-handed phone test and keyboard-only use.
- The site costs $0 a month at 10,000 visits, and satellite pauses rather than bills.

## Glossary

One name per thing. Code identifiers that predate a name are noted.

| Term | Meaning | Not |
| --- | --- | --- |
| Classic map | Our own basemap: paper, ink, relief, labels. Code and tile names call it `literary` | "literary map" in reader-facing text |
| Satellite, Topo | MapTiler's imagery and topographic basemaps | |
| Compare | The classic map and satellite side by side, split by a swipe | "swipe mode" |
| Satellite tint | The Ground option that puts faded satellite colour under the classic map | "Land colour" |
| Flat, Tilted, Raised | The three views of the classic map. Raised is plan oblique relief; its archives are `oblique-*.pmtiles` | "oblique view" |
| Episode | One of the novel's 41 scenes, written `part-number` (`3-09`) | chapter |
| Journey | One of the seven route layers, J1 to J7 | trip, route (a route segment is one leg of a journey) |
| Stop | A point in sequence on a journey | place (a place is a named location, which several stops may share) |
| Stage | One build stage of the project, 0 to 8, each on a `stage/*` branch | Part (one of the novel's four Parts), phase (P1 or P2) |
| Review packet | The folder under `review/` that a stage leaves for the owner to check | sheet (a sheet is one comparison image inside a packet) |
| Owner | The person who runs this project and makes its decisions | "you", "the author" (the author is McCarthy) |
| Tile release | A GitHub Release `tiles-vN` holding the PMTiles archives | |
