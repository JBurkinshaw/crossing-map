# 0028. Context places of the period on the map

Status: proposed (2026-11-15). Extends decision 0027's water places to the gazetteers' other period features. The review packet is review/stage-9/context-places/README.md.
Phase: P1

## Context

The water places (decision 0027) name the springs, ranches and stations a rider goes to. The owner asked for the rest of what the cached gazetteers hold that suits the book's years (1939 to 1945) and the Wheeler sheets: forts, ghost towns, mines, sawmills, churches and the like, in the same journeys corridor. None of the gazetteers dates a feature, and the current GNIS no longer holds its man-made classes: in 2021 USGS moved Locale, Mine, Well, Church, School, Cemetery, Post Office and Building out of Domestic Names. The last national file before that split, of 25 August 2021, is still published in USGS's archive (StagedProducts/GeographicNames/Archive/MainDomestic/), so its New Mexico and Arizona files were downloaded (public domain).

## Decision

- **A sibling layer.** `crossing.context_places` writes `data/context_places.geojson`, a story layer like `water_places`, rather than new kinds in `water_places`: the name stays true, and the two can be judged and switched apart. The map draws it as one symbol layer, `context-place`, from zoom 11, just under the water places, so every other name wins a collision. Its marks also give way, so a dense mining district thins out. The marks are registered with the water marks, so every map that draws one draws both.
- **What is taken.** From the current GNIS: Military (forts, camps, the army air fields), Populated Place marked "(historical)" (ghost towns), Lake and Flat (names only, in quiet italic, the lakes in the water labels' ink). From the 2021 file: Locale by its name (ranch, homestead or place; windmill; well; corral or pens; station, siding, stage station or depot; camp or cabin), with the modern sorts left out (weather, ranger and pumping stations, substations, campgrounds, trailheads, historic-site markers, shopping centres and so on); Mine when named as a mine, shaft, adit, tunnel, lode or group, not a prospect, pit, quarry, deposit or claim; Cemetery; Church and School outside towns; Post Office only when "(historical)"; Well only when named (not "Water Well", a number, or an oil or test well). From GeoNames Mexico: PPLQ and FRMQ (abandoned places), ANS (archaeological sites, drawn as ruins), MN, MNQ, MNAU, MNCU (mines), MLSW (sawmills), CMPL (a logging camp), CRRL (corrals), CH (a chapel), CSTM (customs houses), RSTNQ (an abandoned station) and SPUR (a siding); TNLRR (railway tunnels, a mark with no name) and RR (a railway's name) only within 2 km of a railway the map draws.
- **What is left out as modern.** Airfields (AIRF), schools named as modern ones (Elementary, High, Middle, College, Primary, Memorial ...), churches and schools within 1.5 km of a town (GNIS populated places and census places, and the book's towns), congregations with later names (Kingdom Hall, Fellowship, Center ...), current post offices (the town's name marks them), a 2026 garrison and a modern technical school in GeoNames, and four GNIS records by hand: Winslow Air Force Station (the Air Force dates from 1947), Fort Bayard Military Reservation (a second point for the fort), Harrison A Schmitt School (named for the astronaut) and Camp Thunderbird (a youth camp).
- **Air fields** are kept: Deming, Lordsburg and Douglas army air fields opened during the war. The gazetteer gives no date, so the map does not give one.
- **Names.** "(historical)" is dropped from the name and kept as `historical: true`. Every feature carries its source, source id, licence, `first_seen` 1-01 and a `note_safe` naming its class or code.
- **Duplicates** as for water places: a point within 1 km of any book place is dropped; so is one within 1 km of a water place or a kept context place of the same name; and an old post office within 2 km of a kept place of its town's name.
- **Marks**, tiny and in ink after Wheeler: a flag for a fort, crossed picks for a mine, a cross for a church and a cross on a ground line for a cemetery, a small open square for a ruin or abandoned place, a row of teeth for a sawmill, a small ring for a corral, a dot for a school, post office or customs house, a tent for a camp, the water places' square for a ranch and open square for a station, the well's dot in the water's ink for a well and the dot with sails for a windmill, and two brackets for a tunnel. Among themselves, the rarest names win: forts, then abandoned places and ruins, lakes and flats, stations, post offices, sawmills, and last the many mines, wells and windmills.

## Alternatives

- **New kinds in `water_places`.** One layer fewer, but a layer of mines and churches named for water.
- **Bare-name Locales as sidings.** Most railway sidings have no class word in their name, but only two such Locales lie within 1.5 km of a drawn railway, and both are mining works, so the rule was not used.
- **Every church and school.** Most are town buildings of the later twentieth century, under a town name that already marks the place.
- **Lakes and flats as shapes now.** The map is about to draw dry lakes and playas as shapes; until then they are names.

## Consequences

About 2,400 more names in the corridor, most of them mines (673), wells and windmills (763) and ranches (389). None is dated, so a place may be drawn that was gone by 1939 or came later; the How it's built page says so. The GNIS 2021 file is frozen: USGS no longer updates its man-made classes. Tunnel marks sit on the real line, which Natural Earth's generalised railway may miss by several hundred metres.
