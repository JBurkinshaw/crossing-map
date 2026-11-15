# Changelog

Changes that readers and data users can see: the map, the published data in `data/`, and the tile releases. Code-only changes are in the git history. Corrections sent in by readers are listed with credit, unless the sender asks otherwise.

A change is **released** when it is merged to `main`, which the public site serves. Until then it is listed under Unreleased, in sections dated by when it reached the preview at `/preview/`. Tile releases are named by their tag; `tiles/release.txt` pins the one a branch uses.

## Unreleased

### 2026-11-14

#### Data

- Veracruz added to the places named elsewhere (3-01), read as the state, as Bell (2000) reads it.
- A GeoParquet copy of `vignettes`.
- The wolf's crossing of the Río Bavispe moved 1.7 km east, onto the river's real channel.
- The J5 camp at the edge of the Babícora lake moved 1.4 km onto the lake's north-west shore, as INEGI outlines it; it stood in the water.
- 21 legs across the sierras and up the long valleys are modelled paths instead of schematic curves: the way of least effort over the ground for a rider at a walk (the wolf on foot in Part I), `method: modeled` with a `cost_model` (lc-0.4, decision 0021). An open question asks whether the brothers' ride from San Diego to the opera camp, about 100 km, fits in one day.
- Inferred areas are drafts: each stop's circle cut by a written rule to the ground its reasoning describes (a river and its banks, a valley floor, a road's verge, a playa), which halves the ground they cover (14,566 to 7,322 km²). Each area's `outline_rule` gives the rule, and `straight_road` marks the nine where a straight line between towns stands in for an unmapped old road. Areas may be MultiPolygons. Nine stops moved onto their drafts, up to 7.3 km (Huisiachepic onto the upper Bavispe, San Simon onto its river).
- The wolf's trap (J1 stop 13, J2 stop 2) moved from the Cloverdale Creek point in GNIS, east of Cloverdale, to the creek road 8 km west of the town, with a 2 km circle: Billy rides west up the road for about two hours to reach it. Robertson's crossfence moved onto the road about halfway back. Both J2 legs between them follow the road in Census TIGER 2023 and are drawn solid.

#### Tiles

- `tiles-v8`: small streams on both sides of the border by one rule. Each stream appears from a zoom set by its Strahler order, widens with order, and intermittent streams are lighter rather than dashed, so drainage is as dense south of Colonia Morelos as north of it. Creek names show from zoom 11. River names show again: they follow a smoothed copy of each river, and minor rivers are named too. NHD's stream orders no longer climb along braided channels and ditches. Lakes in Mexico follow INEGI's water-body outlines, so the Babícora lake has its real shape.

#### Site

- Inside the journeys corridor the hachures are drawn as on the Wheeler Survey sheets (decision 0024): short strokes of one width, packed closer on steep ground, with crests, summits, mesa tops and valley floors left white and escarpments drawn as a comb of wedges. They come from two new tile archives, `relief-wheeler.pmtiles` and `relief-wheeler-12.pmtiles`, which need a tile release. The earlier hachures are kept and can be switched back.
- Modelled legs are drawn in long dashes, with a key entry; their cards say "Modelled path, not the book's". How it's built explains the model and its uncertainty.
- An inferred area's card says how it was drawn, by a rule from data rather than by hand from a source, and asks readers who know more to suggest a correction. How it's built explains the method and its limits.
- Ranges, valleys, plains and mesas are lettered in spaced roman capitals along their long axes, as on the Wheeler sheets (decision 0023): the landforms the book names from zoom 7, the gazetteers' from zoom 10. A new layer, `landforms.geojson`, holds 313 name lines.
- The map's paper is cream, after the Wheeler Survey's 1877 sheet 70A, and the hachures are a brown-black that is darker on steep ground and fainter on gentle slopes. The main rivers are named in spaced roman capitals and drawn wider the more important they are. From zoom 10, unnamed and small summits show their height.
- The hillshade is MapTiler Topo's: the standard method, light from 335 degrees, opaque grey shade and pale warm highlights (decision 0025).
- Each vignette sits right beside the stop or place it stands for, at every zoom, without leader lines; the key says its position is approximate (decision 0026). `vignettes.geojson` gains `side` and loses its leader lines.
- A summit's glyph shape now comes from what the gazetteer calls it (its name and feature code), not from the elevation model: 145 summits the model had drawn as domes or mesas are peaks, and six summits named as hills are domes.
- Summit names and heights, spot heights and vignette labels are a little larger. The side panels take the map's cream paper.
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
