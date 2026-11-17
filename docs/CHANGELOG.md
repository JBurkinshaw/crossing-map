# Changelog

Changes that readers and data users can see: the map, the published data in `data/`, and the tile releases. Code-only changes are in the git history. Corrections sent in by readers are listed with credit, unless the sender asks otherwise.

A change is **released** when it is merged to `main`, which the public site serves. Until then it is listed under Unreleased, in sections dated by when it reached the preview at `/preview/`. Tile releases are named by their tag; `tiles/release.txt` pins the one a branch uses.

## Unreleased

### 2026-11-16

#### Data

- Episode summaries: 3-01 says "“the girl”" and "travelling"; 3-11 no longer hints at what the servant brings ("Billy follows a servant into the hills"); 4-01 says Billy "goes to enlist".
- The Parham house shows from 2-05, not 2-04 (decision 0038): its stop, drawing and open question, the SK Bar stop after it on J3, and the three legs between the Guadalupe pass and Animas.
- The drawings' `stands_for` no longer tells what happens (decision 0038): 16 are rewritten after their place, such as "The river camp near San José (J4)".
- One spelling per place in the reasoning, names and summaries (decision 0037): the Cajón Bonito ("Down the Cajón Bonito"), the Sierra de la Madera, and La Boquilla, which two episode summaries (3-06, 3-07) and a stop had called Boquilla y Anexas, the other town the open question rules out. UK spelling throughout ("towards", "grey"), and "railway" for the railroad, except in a company's name.
- Inferred areas' rules say "area", not "circle", as does a stop's reasoning; "Kept the circle" is now "Kept the whole area". Working notes are gone from the published text: "To be checked by hand in QGIS" from the two regions, "Worth a look by hand" from an area's rule, and "is a separate seed" from San Lorenzo's reasoning.
- The drawings' `reasoning` no longer contradicts itself about zoom: a drawing that waited one step says it still covers something there but waits no longer, and one that never waits says no closer zoom would clear it.
- New field `drawn_detail` on traced and modelled legs: the technical side of `drawn` (dataset and features, Strahler order or NHD watershed, grid, smoothing, cost model), for data users. `drawn` and the modelled legs' `reasoning` are now in plain words, without the model's version, Douglas-Peucker, Strahler orders or watershed codes: 20 modelled legs, 2 legs traced on INEGI rivers and the Whitewater Creek leg.
- Stop names and drawing captions no longer give away what happens in the episode the reader is in (decision 0036): 21 stops (and the 32 legs and 9 areas named after them) and 8 drawings are renamed after their place, such as "The river camp where Boyd is shot" to "The river camp near San José" and "Turned away by the army" to "The army recruiting office". The event stays in the reasoning. Two drawings move to another side of their pin with their shorter captions, and Billy riding into the Pilares shows from zoom 11.
- “The girl” is in inverted commas wherever the data names her, as the About page does: 3 stop names, 6 leg names, 12 stop reasonings, an episode summary, and the drawings' captions and notes (which had straight quotes or none). The journey picker and the key name J5 and J6 the same way.
- `translations.json` has a new field, `common`: true for the 76 lines that are only "Sí", "No", "Gracias", "Bueno", "Adiós", "Buenas noches" or "Señor" (decision 0035). Set by `crossing.translations`.
- Traced legs are simplified to 5 m, which halves `journeys.geojson` (1.1 MB to 497 KB) with no visible change on the map.
- `vignettes` no longer has `max_zoom`: a drawing shows from its `min_zoom` at every closer zoom.
- `vignettes` has a `journey`, the journey each drawing belongs to. Each drawing's `side` is now the side of its pin where it covers the fewest stops, route lines and other drawings, and its `min_zoom` waits one zoom step, no more, where it would cover a stop or a route line further out (decision 0026, amended): 34 sides and 27 first zooms changed, and its `reasoning` says why.

#### Site

- While the map hides what you have not read, a leg's "How this line was drawn" text that cites a later episode is replaced by a notice, as "How this was placed" already was.
- The site speaks in one voice (decision 0037): "I" only in the owner's note at the top of About, and "this site" or "the map" elsewhere, not "we" or "our". The Classic map is "This site's own map, in ink on paper", not "The book's map", and How it's built runs the pipeline on "the owner's computer".
- An inferred area's card calls it an area, not a circle, as does How it's built.
- The Data page says the drawings sit beside their place, not on it, and not to scale, and its water places line reads plainly.
- The key says "Railway" and "Railway tunnel". The Open questions page uses curly apostrophes and calls Bell's work an annotated dissertation and Hazelton's the reader's map; How it's built writes "a mesa or a butte" in lower case.
- A modelled leg's card says how its line was worked out in plain words and links to How it's built, which explains the model.
- How it's built is up to date: the modelled legs' coarser grid on the two longest legs, the two parts of the elevation model, and a new Relief section on the hachures, Wheeler-style within 20 km of the journeys.
- A stop says what happens there: its Part and episode ("Part I · *Two days later*") and the episode's summary.
- Stops and place cards say how sure the map is in plain words: "Named and found", "Roughly here", "Worked out from clues" and "Someone in the book says so" (decision 0035), after the kind of place on a card ("Inferred area · Worked out from clues"). The source moves under "How this was placed", which on a card now holds the reasoning too.
- "Spoken here" is now "Spanish here", and "Spoken on this road" "Spanish on this road". Very common lines ("Sí", "Gracias", "Buenas noches" and the like) are left out of these lists; search still finds them.
- Each translation shows its Spanish, page, English and "Suggest a better translation"; the episode, confidence and Campbell's guide link fold under "About this translation".
- Search's Part filter has a visible label, "Search in:".
- The About page is rewritten: why a map, how to use it, how sure each place is, and how routes are drawn.
- The panel opens with a header, "The Crossing · a reading map", with About and Introduction links. On phones, under the stepper, this slim header comes first, then the reading-progress badge, then the journey picker.
- The vignettes stay on the map when zoomed in past 12; they used to disappear there, and the she-wolf past 11.
- The key no longer runs off the bottom of a laptop screen: it is split into two tabs, "The story" and "The land", and scrolls if the screen is still too short. Journeys are listed in two columns under short names ("J2 First crossing").
- The key now explains the international boundary, state lines, grouped stops, spot heights, and the small marks for forts, mines, churches, cemeteries, ruins, stations, ranches, camps, springs, wells, tanks and windmills. They are drawn the same way as on the map.
- The key's drawing is twice as large and is a person or animal from the book once the reader has reached one. Its text now reads "People, animals and things from the book, set just beside their place, not on it. Not to scale."
- Grouped-stop markers say what they hold ("9 stops", "9 places") instead of "+9", and a click or tap zooms in until all of them come apart.
- The map's switches fold under one Map button on desktop as on phones, so the box no longer covers a stop. A line under each switch says what the chosen option does. Compare is labelled with its name.
- On phones, the key opens as a sheet from the bottom of the screen with a Close button; a tap outside it or Escape closes it too, the "Where you are" inset is hidden, and the scale bar is shorter, so it no longer covers the first stop of J1.
- The first visit opens one dialog, not two: the introduction, a line on how to use the map, and the question "Have you finished *The Crossing*?". "Yes" shows everything; "Not yet" asks where you are up to (decision 0034).
- "Where are you up to?" lists the episodes by their opening words, grouped by Part, in place of the slider. You can also enter how far through the book you are as a percentage.
- The reading-progress badge says what the map is hiding, such as "Hiding what's after Part I, episode 5: In the woods", and opens "Where are you up to?" directly.
- Setting your progress to an episode opens the map at the stop you reached most recently.
- Opening the Map menu closes the key, and opening the key closes the menu, so neither covers the other.
- While the map hides what you have not read, How it's built hides its decision records too, as they name places and events from the whole book. A button shows them after a warning, as "Show everything" does.
- Drawings no longer sit on the stops and route lines: each is set on the side of its pin with the least under it, and those in the busiest country, around Casas Grandes, San Diego, Cloverdale and the Peloncillos, show from one zoom closer, never more, so they stay in view. At each drawing's first zoom, none now covers another drawing (7 pairs did), and 5 cover a stop marker (26 did).
- The drawings of the journey in focus are at full strength; those of other journeys are lighter, as their route lines are, in Compare too.

### 2026-11-15

#### Data

- New layer `context_places`: 2,391 period places within 20 km of the journeys, from GNIS (with its national file of 2021) and GeoNames: forts and army air fields, ghost towns and abandoned places, mines, sawmills, churches, cemeteries, schools, old post offices, corrals, camps, ranches, named wells and windmills, railway tunnels, dry lakes and flats. A GeoParquet copy too.
- Every journey leg has a `drawn` text saying how its line was made: traced along a named road or river (which one, in which dataset, and how it was cut), computed as a least-cost path, or drawn as a curve (decision 0032).
- 17 more legs follow the road or river the book names instead of a curve (decision 0032): in the US, the old Douglas to Cloverdale road over the Guadalupes (Geronimo Trail) and on down the Animas Valley road, and US 180 and NM 152 from Silver City past the Santa Rita mines (Census TIGER 2023); in Mexico, the Bavispe from Colonia Oaxaca to Morelos (Natural Earth), the roads from Morelos to Ojito, San Diego to Mata Ortiz and Casas Grandes, and Boquilla to Santa Ana de Babícora (INEGI's road network), and the Arroyo Agua Prieta and the Río Casas Grandes (INEGI's 1:50,000 streams, checked against INEGI's river names). A traced leg can now turn from one named road onto another at a junction.
- Three stops moved onto the road their reasoning names: the J3 pass in the Guadalupes to the highest point of Geronimo Trail (7.8 km north); the SK Bar (J3 and J7) to nine road miles north of Cloverdale, not nine straight-line miles (5.6 km south); and the J4 camp in the Dos Cabezas onto Apache Pass Road (14 km east), with a new inferred area along the road.

#### Tiles

- `tiles-v11`: reservoirs whose dams were finished after 1945 are left off the base map, using the dam years in the Global Dam Watch database (decision 0031): 24 lakes, among them El Novillo on the Yaqui and Abiquiu on the Chama. The river under each one shows instead.
- `tiles-v10`: the US streams of six more watersheds, the closed valleys the river data had missed (the Animas Valley, Willcox Playa, the Jornada and Tularosa valleys, the Rillito and the San Francisco), so the Animas Valley's washes no longer stop at a watershed's edge. US dry lakes and intermittent lakes of 1 km² or more are drawn, so the washes of the closed valleys end in their playa. The Raised view rebuilt with the same streams.

#### Site

- The Tilted view's terrain is exaggerated 2.5 times (was 1.8).
- A leg's card has a "How this line was drawn" section (decision 0032).
- The key's faded-line entry reads "Legs after the stop you are on" instead of "The road ahead, when stepping through".
- Each journey has its own ink: indigo, vermilion, oxblood, sap green, ochre, violet and rose madder (decision 0033).
- A route line's dash shows how sure it is: solid where it follows the road or river the book names, long dashes for a modelled route, and sparse short dashes for a curve that only joins the stops. The key groups these three under "How sure the line is", and a leg's card uses the same wording.
- Inferred areas are a tint in their journey's ink with a dotted edge. Regions have no fill, just a fine line with a soft band inside it.
- Lakes are drawn over the rivers, so a river ends at the shore instead of running through the water (decision 0030).
- A place's pin that stands more than 1 km from every stop at it, such as the Guadalupe Mountains' gazetteer point beside the J2 pass, keeps its dot and its name but no longer opens the stop (decision 0029).
- Everything off the map (the frame's margin, the panel, the cards and the pages) is a lighter cream than the map, as on the Wheeler sheets.
- How it's built explains how the mountain glyphs are found and drawn, and a new Caveats section says the gazetteer's springs, ranches and stations are undated and the hydrography is today's.
- From zoom 11 the map names the context places in quiet italic, each with a tiny mark after Wheeler (a flag for a fort, crossed picks for a mine, a cross for a church, an open square for an abandoned place), below every other name. The Caveats say they are undated too.

### 2026-11-14

#### Data

- New layer `water_places`: 1,233 springs, tanks, ranches and stations within 20 km of the journeys ridden or walked, from GNIS and GeoNames, with the book's own four pointing at their place. A GeoParquet copy too.
- Veracruz added to the places named elsewhere (3-01), read as the state, as Bell (2000) reads it.
- A GeoParquet copy of `vignettes`.
- The wolf's crossing of the Río Bavispe moved 1.7 km east, onto the river's real channel.
- The J5 camp at the edge of the Babícora lake moved 1.4 km onto the lake's north-west shore, as INEGI outlines it; it stood in the water.
- 21 legs across the sierras and up the long valleys are modelled paths instead of schematic curves: the way of least effort over the ground for a rider at a walk (the wolf on foot in Part I), `method: modeled` with a `cost_model` (lc-0.4, decision 0021). An open question asks whether the brothers' ride from San Diego to the opera camp, about 100 km, fits in one day.
- Inferred areas are drafts: each stop's circle cut by a written rule to the ground its reasoning describes (a river and its banks, a valley floor, a road's verge, a playa), which halves the ground they cover (14,566 to 7,322 km²). Each area's `outline_rule` gives the rule, and `straight_road` marks the nine where a straight line between towns stands in for an unmapped old road. Areas may be MultiPolygons. Nine stops moved onto their drafts, up to 7.3 km (Huisiachepic onto the upper Bavispe, San Simon onto its river).
- The wolf's trap (J1 stop 13, J2 stop 2) moved from the Cloverdale Creek point in GNIS, east of Cloverdale, to the creek road 8 km west of the town, with a 2 km circle: Billy rides west up the road for about two hours to reach it. Robertson's crossfence moved onto the road about halfway back. Both J2 legs between them follow the road in Census TIGER 2023 and are drawn solid.

#### Tiles

- `tiles-v9`: the Raised view rebuilt for the drafted areas and the modelled legs, and the Wheeler hachures over the journeys corridor (`relief-wheeler.pmtiles`, `relief-wheeler-12.pmtiles`), with the production hachures kept beside them.
- `tiles-v8`: small streams on both sides of the border by one rule. Each stream appears from a zoom set by its Strahler order, widens with order, and intermittent streams are lighter rather than dashed, so drainage is as dense south of Colonia Morelos as north of it. Creek names show from zoom 11. River names show again: they follow a smoothed copy of each river, and minor rivers are named too. NHD's stream orders no longer climb along braided channels and ditches. Lakes in Mexico follow INEGI's water-body outlines, so the Babícora lake has its real shape.

#### Site

- The classic map takes three more features from the Wheeler Survey sheets (decision 0027). A 15′ graticule in faint ink from zoom 8, labelled in a margin band inside a thin-thick rule round the map (the rule alone on phones); the cartouche gets the same rule. Springs, tanks, ranches and stations within 20 km of the journeys, from zoom 11, each with a small mark and its name in quiet italic. Names on one type scale: towns in roman at about 1.4 times the spot heights, cities in capitals, ranches and springs in small italic, and named passes in small capitals laid across the saddle or along the road through it, in place of their glyph.
- Inside the journeys corridor the hachures are drawn as on the Wheeler Survey sheets (decision 0024): short strokes of one width, packed closer on steep ground, with crests, summits, mesa tops and valley floors left white and escarpments drawn as a comb of wedges. They come from two new tile archives, `relief-wheeler.pmtiles` and `relief-wheeler-12.pmtiles`, which need a tile release. The earlier hachures are kept and can be switched back.
- Modelled legs are drawn in long dashes, with a key entry; their cards say "Modelled path, not the book's". How it's built explains the model and its uncertainty.
- An inferred area's card says how it was drawn, by a rule from data rather than by hand from a source, and asks readers who know more to suggest a correction. How it's built explains the method and its limits.
- Ranges, valleys, plains and mesas are lettered in spaced roman capitals along their long axes, as on the Wheeler sheets (decision 0023): the landforms the book names from zoom 7, the gazetteers' from zoom 10. A new layer, `landforms.geojson`, holds 313 name lines.
- The map's paper is cream, after the Wheeler Survey's 1877 sheet 70A, and the hachures are a brown-black that is darker on steep ground and fainter on gentle slopes. The main rivers are named in spaced roman capitals and drawn wider the more important they are. From zoom 10, unnamed and small summits show their height.
- 24 new vignettes (37 in all), drawn the same way after public-domain and openly licensed references: scenes, landmarks and animals from all four Parts, and the characters riding the long empty stretches of their journeys (Billy on Bird with the dog, the wolf on the rope, the brothers with "the girl", Billy with the travois). Character drawings carry no label where the subject is plain.
- A short introduction opens on the first visit, saying what the site is, before the reading-progress question; the panel's Introduction link and the About page bring it back. The About page explains how the book is bound to real places yet has no map.
- The Tilted view leans 50 degrees (was 40) over terrain exaggerated 1.8 times (was 1.5).
- Stop and area notes no longer call an inferred area a circle: they speak of the area and the estimate, as the areas are now drawn from the ground the clues describe.
- The hillshade is MapTiler Topo's: the standard method, light from 335 degrees, opaque grey shade and pale warm highlights (decision 0025).
- Each vignette sits right beside the stop or place it stands for, at every zoom, without leader lines; the key says its position is approximate (decision 0026). `vignettes.geojson` gains `side` and loses its leader lines.
- A summit's glyph shape now comes from what the gazetteer calls it (its name and feature code), not from the elevation model: 145 summits the model had drawn as domes or mesas are peaks, and six summits named as hills are domes.
- Summit names and heights and spot heights are a little larger; the vignettes are 1.3 times their size and their labels larger, placed before every other label so they always show. The side panels take the map's cream paper.
- The mountain glyphs look hand-drawn: tapered pen strokes that wander a little, outlines that lift at the summit, and loose, sometimes broken hatching. The shapes, names and sizes are unchanged.
- The thirteen vignettes are real drawings, in the same pen as the mountain glyphs and two inks: each looks roughly as its subject did around 1940, after public-domain or openly licensed references, and has a short italic label under it. The Credits page lists how each was made, for the drawings reached. `vignettes.geojson` gains `label` and `credit`; two drawings are renamed for what the book describes (the San Diego house front, the cockpit at the hacienda).
- The states are named in widely spaced small capitals from zoom 5, fading out by zoom 8.5, placed clear of the story.
- Each translation has a "Suggest a better translation" link that opens a prefilled GitHub issue.
- The map's controls are one framed set: Map (Classic, Compare, Satellite, Topo), View (Flat, Tilted, Raised), Ground (Paper or Satellite tint, formerly Land colour) and Units (Imperial or Metric). Compare sits between Classic and Satellite and works in Flat and Tilted. On phones the controls fold behind one button.
- The key is inside the title cartouche, folded until opened, and shows the railroad.
- The overview inset says what it shows ("Where you are") and draws the current view as a proper box.
- The Home button is named "Show the whole journey".
- The panel runs: reading progress, search, journey, Back and Next, all stops, then the card. "How this was placed" stays open or closed as the reader left it.
- Clicking a route or a stop on the map goes to that stop, staying in the current journey when it passes there.
- The lines spoken on a road have their own block and open the road's card, grouped by episode when they span several.
- The hillshade is more pronounced.

### 2026-11-13

#### Data

- `open-questions.json`: 22 judgement calls, each with what the map shows, the other reading and why. Shown on the cards they concern and on the Open questions page.
- Places checked against James Bell's dissertation (2000) and Joe Hazelton's Gaia GPS map. Pilares Teras and Skeleton Creek moved; Hidalgo County, Cochise County, Taylor's Draw and Cañón la Cabellera added; first sightings of Animas Peak, Ascensión and De Baca County corrected.
- The wolf's Río Bavispe crossing moved onto the river's western arm.
- A vignette for the Trinity test (4-09).

#### Tiles

- `tiles-v7`: every named river is now traced through INEGI's 1:50,000 network in Mexico and the USGS NHD in the US, keeping to each river's main stem, so the lines follow their valleys instead of Natural Earth's generalised courses. The Raised view now draws the main stems of wide rivers, such as the Bavispe, which were missing.
- `tiles-v6`: Mexico's named rivers traced through INEGI's 1:50,000 network, and the Bavispe named down to its confluence with the Aros. Natural Earth labels that stretch "Yaqui".
- `tiles-v5`: the S5 relief style at zoom 12 density, and Raised over every journey.
- `tiles-v4`: the S5 relief style and the first Raised preview.

### 2026-11-12

#### Data

- Parts II to IV: every journey, stop, area and place, and the Spanish translations.

#### Tiles

- `tiles-v3`: production hachures.

## 2026-11-11

### Data

- Part I: the wolf's journey and Billy's ride south, with places, stops and areas.

### Tiles

- `tiles-v2`: the base map with creeks, and terrain.
- `tiles-v1`: the literary base map, first look.
- `tiles-v0`: a test archive.
