# Experiment: least-cost paths for the schematic legs in Mexico

Status: **adopted on 14 November 2026** (decision 0021) for the 21 legs on the "works" list, as cost model lc-0.4: INEGI's unpaved tracks (Red Nacional de Caminos 2024) replace Natural Earth's modern highways as the road corridors. `crossing.least_cost` is now a build module that `crossing.build_story` calls, the legs are in `pipeline/seeds/modeled-legs.csv`, and the J4 one-day ride is an open question. The images and the renderer are parked in `private/parked/least-cost-experiment/`; the outputs below stay in this folder (not in git) for the review mode.


## Reviewing in the app

Run the site locally and open the review mode, which steps through the legs on the real map:

```bash
cd site && npm run dev
# then open http://localhost:5173/?review=routes
```

Each leg shows the modelled path (blue), the schematic curve drawn now (black, dashed), the slope-only path (orange, dotted) and the rest of its journey (faint, dotted), with the model's numbers and flags. Mark it Accept, Needs work or Reject (keys `a`, `n`, `r`), add a note (`e`), and move on with the arrow keys or `j` and `k`. The filter shows every leg, the modelled ones, the flagged ones, or those not yet reviewed. Verdicts save to `review.csv` in this folder (id, verdict, note, updated) through the dev server, and to the browser as a backup. The review mode exists only on the dev server; the published site does not include it. Satellite and Topo need the MapTiler key's allowed origins to include localhost.

## In short

- Of the 94 schematic route segments that run through Mexico (10 % or more of their length), 86 were modelled as least-cost paths for a rider at a walk (the wolf on foot for J1). The other 8 stay schematic: the 7 legs of J6, which the book only reports, and Billy's ride in the doctor's car (J4 40).
- 14 of the 86 are "summary" legs: weeks of riding that the text gives only as turning points (J3 02 to 04, J5 13 to 19, J7 31 to 33 and 35). A path of least effort between two turning points says nothing about the ride, so they should stay schematic. They are modelled only so you can see them (purple in the images).
- Of the other 72: the median modelled path is 5 % longer than the straight line (largest 1.83), and the median distance from the schematic curve to the modelled path (Hausdorff) is 1.9 km. 38 legs are within 2 km of the curve; 17 are more than 5 km away, nearly all where a leg crosses a sierra (J1, J2 07 and 08, J4 13, J7 36 and 37) or follows a long valley (the Madera road, the Casas Grandes river).
- 62 legs pass every check ("candidate"). 10 are flagged for review; most flags are about the stops and the text, not the model (below).
- The model is sensitive to its weights where the ground gives a choice: a run with Tobler's slope speed alone differs by a median of 0.7 km, but by 5 to 11 km on 11 legs (J4 13 over the sierra: 10.9 km).
- Road corridors barely work, because there is no period road data: Natural Earth's railroad (the line through Mata Ortiz, Las Varas and Madera) carries 10 of the 35 legs the text puts on a road; on the Babícora plain there is no road data at all.

My recommendation: worth adopting for the sierra and valley legs listed under "What works", with the line drawn in its own style and labelled as modelled; not worth it for the flat legs, where the modelled line is the schematic curve with wiggles.

## What was built

- `pipeline/src/crossing/least_cost.py`: the model and checks. Run: `uv run --project pipeline python -m crossing.least_cost` (about 15 seconds on 6 workers; the first run also builds the caches in `private/cache/least-cost/`, about 30 seconds). `--only j4-seg-13 ...` runs single legs.
- `pipeline/src/crossing/least_cost_render.py`: the images. Run: `uv run --project pipeline --with matplotlib python -m crossing.least_cost_render` (matplotlib is not a pipeline dependency, so the run adds it).
- `tools/least-cost-shots.mjs`: screenshots of the modelled lines in the real site, injected as an extra GeoJSON source through `window.__map` (the site's `?debug` handle). Run with `cd site && npx vite --port 5182`, then `cd tools && node least-cost-shots.mjs`.
- Outputs here: `routes-modeled.geojson` (86 lines, the segments' own properties with `method: modeled`, `certainty: inferred`, a new reasoning text, and `cost_model`, `detour_ratio`, `modeled_km`, `straight_km`, `model_hours`, `flags`, `review_status`), `routes-plain.geojson` (the slope-only sensitivity run), `results.csv` (every segment, every number), `img/`.

## The cost model (lc-0.3)

Each leg is routed between its two stop points (a stop with an area uses its point) on a grid in a local transverse Mercator projection, 90 m cells (120 to 240 m for the five legs over about 100 km), padded 12 km or 40 % of the leg's length on each side. The grid is a directed graph with eight neighbours per cell, solved with scipy's Dijkstra; no new dependency was needed. The DEM is Copernicus GLO-30 from the cache, averaged to the grid.

An edge costs the time to cross it:

| Part | Rule | Source |
| --- | --- | --- |
| Speed | Tobler's hiking function, v = 6 exp(-3.5 \|s + 0.05\|) km/h on the slope s along the edge, so uphill and downhill differ. For a rider, scaled so that flat ground gives 6 km/h, the walking pace the plan assumes for a horse (plan 7, step 5). For the wolf, unscaled. | Tobler (1993), NCGIA technical report 93-1 |
| Steep ground | Along-edge slope over 30 % costs up to 3 times more at 50 %, and 10 times beyond (a horse does not climb a cliff). Not for the wolf. | this experiment's assumption |
| Canyon walls | A cell whose gradient is over 25 % costs more even along the contour (sidehill), up to 3 times at 50 % and 6 times at 60 % and over. Cells on an INEGI stream of order 4 and up, and their neighbours, are exempt: the canyon floor is where the trail runs. | this experiment's assumption |
| River crossings | Entering an INEGI stream cell (RH09, RH34, 1:50,000) costs a ford delay by Strahler order (`ORDER_1`): 0.5 min for orders 3 and 4, 1 min for 5, 2 for 6, 4 for 7 and up. Halved for the wolf. Riding along a river does not pay it again. | INEGI |
| Lakes | Natural Earth's lakes (Babícora, Bustillos, Guzmán, Santa María) cost 5 times more: shallow, seasonal and boggy rather than open water. | Natural Earth |
| Named corridors | Only where the stop reasoning names one for that leg: a road (Natural Earth roads and railroads within 1 km, times 0.8) or a riverside trail (INEGI streams of the leg's given order and up within 300 m, times 0.8). | Natural Earth, INEGI |
| Gates | A rider in Mexico may not cross into the United States, except within 2 km of a stop on or over the line: Douglas and Agua Prieta, the boundary stops of J2 and J7. Not for the wolf. | Natural Earth admin areas |
| Towns (wolf) | Cells within about 2 km of a town in `data/places.geojson` cost 5 times more for her. | this experiment's assumption |

**Period roads.** Natural Earth's Mexican roads are modern highways (routes 2, 10, 16, 45), so they are used only lightly (a 20 % discount) and only on legs whose text names a road. Its railroads are of the period: the book itself has the riders cross the tracks at Las Varas and Mata Ortiz. INEGI's road network was not tried; it would also be modern. The real fix is to digitise the roads on the 1:250,000 Army Map Service sheets (plan section 7, "Period data worth digitising").

**How the model got here.** lc-0.1 charged up to 30 minutes for each entry into a river cell. At 90 m a meandering river fills its valley floor, so a path up the valley "enters" it dozens of times (62 times on J4 20): the paths left the valleys for the ridges, the wrong way round for a rider. lc-0.2 also exempted canyon floors from the canyon penalty (at 90 m the floor cells take the gradient of the walls beside them); lc-0.3 cut the ford delays to minutes. Larger delays would need a crossing test that ignores meanders (for example, counting only crossings of a river's smoothed centreline).

## Checks per segment

- **Detour.** Modelled length over straight-line length (pyproj, WGS 84); over 1.6 is flagged. Only J5 09 (1.83): the lake camp's stop point lies inside Natural Earth's coarse outline of the Babícora lake, so the path goes round the lake and wades back in. A better lake outline (INEGI's water bodies) or moving the stop to the shore would fix it.
- **Direction.** Where the text gives a heading for the leg (north, south and so on, 47 legs), a leg is flagged if more than 20 % of the modelled path runs more than 90 degrees from it. No modelled path tripped this. Two legs are flagged because the stops themselves run against the text: J4 23 (the brothers ride south and reach Las Varas, which is north; batch B question 1) and J5 17 (Buenaventura to Álamo, told as passing back north, but the Álamo estimate is south-west of the town; open question on which Álamo).
- **Places the text rules out.** J7 39 must keep east of Casas Grandes (Billy sees its lights to the west): the path stays more than 5 km from both Casas Grandes and Nuevo Casas Grandes. J4 20 passes 0.8 km from Las Varas, where the text has the brothers arrive for the first time days later; that comes from the stops (the opera camp is placed a few miles south of the town), not from the model. Each leg also lists the towns within 1.5 km of its path that are not its own stops: Las Varas (J4 20), La Pinta (J5 08), Mata Ortiz (J5 12, J7 26), Boquilla (J7 36) and Galeana (J7 39), and some on the summary legs. Apart from Las Varas on J4 20, none of these contradicts the text.
- **Time.** For 30 runs of legs the text gives a time (a day, two nights, from noon to midnight), written as riding hours with a day's ride taken as about 10 hours in the saddle. The check compares the length with that time, and the model's own Tobler time with it.

**What a day's ride is.** At a walk a horse covers about 6 km/h on the flat (the plan's figure). A working day of 7 to 9 hours in the saddle, with a noon halt, gives 40 to 55 km, and a horse ridden day after day cannot keep up much more than that. So the flags are: "brisk" above 6 km/h over the text's time (60 km in a 10-hour day), "too fast" above 8 km/h (the plan's rule, step 6), and "the model needs X h" where Tobler's time along the path is more than 25 % over the text's. Night riding and the travois (J7 43) are slower, which the numbers below do not allow for.

| Text's time | Legs | Length | Implied | Model's time | Reading |
| --- | --- | --- | --- | --- | --- |
| All day south from San Diego, the opera camp late in the day | J4 19, 20 | 100 km | 8.3 km/h | 19 h | Too far for one day. The text has them ride all day and halt at the troupe a few miles below Las Varas; either the text compresses the ride or the opera camp belongs north of Las Varas (batch B question 1 again). |
| Agua Prieta after shopping, Ojito by evening | J4 10 | 58 km | 7.2 km/h | 10 h | Brisk; possible if they left Agua Prieta early. |
| Santa Ana near noon, the lake camp after dark | J5 08, 09 | 70 km | 7.0 km/h | 12 h | Brisk; half of it is the lake detour of J5 09. |
| Mata Ortiz, all day and the evening | J5 02 | 76 km | 6.3 km/h | 15 h | Brisk; he also rides on into the night, so it fits. |
| An hour north of Corralitos | J7 42 | 6 km | 6.1 km/h | 1 h | Fits: the stop was placed at an hour's ride. |
| Three days with the travois | J7 43 | 120 km | 4.0 km/h | 20 h | Fits for a horse, slow going for a travois (40 km a day). |
| Three days' riding to the wagon-road crossing | J4 22 | 12 km | 0.4 km/h | 2 h | The stops are much closer than the time; the river camps or the crossing may be misplaced (the crossing's circle is already 15 km wide for that reason). |
| Two days to Las Varas | J4 23 | 24 km | 1.2 km/h | 4 h | As above, and the compass does not close. |
| Two days from the wolf's grave to the promontory | J3 01 | 21 km | 1.1 km/h | 5 h | Fits: two days of rough riding need not be 40 km of progress. |

The other 21 timed runs fit (1.5 to 5.4 km/h). All are in `results.csv`, column `budget`.

## Images

All in `img/`. The modelled path is orange, the schematic curve dashed grey, summary legs purple; red labels mark legs with a flag.

- `overview-j1.png` to `overview-j7.png`: each journey's Mexican legs over hillshade. J6 shows only its schematic curves (not modelled).
- Close-ups, with the slope-only run dotted blue:
  - `closeup-bacerac-rim.png` (good, and a warning): J4 13 to 15. The model climbs out of Bacerac to the south-east and crosses the sierra by a southern line; slope alone takes a northern line close to the curve. 10.9 km apart, both plausible, and the text names no pass. The text's "rough trail" is what decides it, and we have no trail data.
  - `closeup-river-north.png` (good): J7 40 to 43, up the Casas Grandes river to the border. The path keeps to the river where the valley is narrow and cuts the meanders on the open plain, as a rider would.
  - `closeup-wolf.png` (good): J1, the wolf from the Sierra La Madera across the Bavispe, up the river's eastern arm about 2 km from Bacerac (the town cost keeps her off it) and across the Carretas plain to the line at 108° 30′ W.
  - `closeup-las-varas-road.png` (mixed): J4 19 to 23. The model follows the valley south from Mata Ortiz and passes through Las Varas, which the text does not have them reach until later; the stops' own order (J4 21 to 23) loops back north.
  - `closeup-babicora.png` (mixed): J4 24 to 33 around the lake. The modelled lines are almost the curves: on flat ground the model has nothing to say.
  - `closeup-lake-camp.png` (bad): J5 08 to 10. The camp stop is inside Natural Earth's lake outline, so J5 09 goes round the lake (detour 1.83).
- In the real site (Classic, the modelled lines drawn over the site's own schematic lines): `site-bacerac-rim-j4.png`, `site-madera-road-j4.png`, `site-babicora-j4.png`, `site-casas-grandes-river-j7.png`. The Babícora view shows how crowded the plain already is.

## What works and what does not

Works:
- Sierra and canyon legs, where the curve crosses a range blind: J1 01 and 02 (the wolf), J2 06 to 08 and 12, J3 12, J4 13 to 15, J7 23, 24, 36, 37. Here a modelled line reads as a ride, not a diagram.
- Long valley legs: J4 20, J5 02 and 11, J7 26 (the Madera road), J7 41 to 43 (the Casas Grandes river).
- The checks: they surface the same tensions batch B found by reading (J4 21 to 23, the Álamo pick) and a new one (J4 19 and 20 in one day).

Does not work, or not yet:
- Flat legs (most of the Babícora plain, Casas Grandes to San Diego): the modelled line is the curve with wiggles, and the wiggles suggest a precision the book does not have.
- Roads: no period road data, so the "road the text names" is a corridor only where the railroad runs.
- Lakes: Natural Earth's outline is too coarse for stops on a shore.
- Weights: they are assumptions, and on 11 legs the answer moves by 5 km or more when they change. A modelled line should carry that doubt (for example as a corridor rather than a line).

## The US legs and the wolf

**US legs.** The method carries over; the inputs do not, yet. The DEM cache already covers the bootheel and southern New Mexico. Needed: (1) a stream order for NHD flowlines (NHD in the cache has none; `plan_oblique` stands in the display scale for it), either from NHDPlus HR's value-added attributes (`StreamOrde`, a download) or a Strahler order computed over the NHD network's flow direction; (2) period roads from the USGS historical topo sheets (topoView) for the bootheel, since TIGER is modern and the old Douglas to Cloverdale road is not in it; (3) the border mask reversed (US legs may enter Mexico only at the text's gates); (4) a fence term: the bootheel legs are ranch country, and the text has Billy follow and cross fences (Robertson's crossfence), which no dataset here records. The US schematic legs are fewer and shorter; most of J7's US legs are already narrated on TIGER roads.

**The wolf.** J1 01 and 02 use a first guess: Tobler unscaled, no steep-ground penalty, half the ford delays, and towns avoided. Tobler is a human walking function; a wolf is barely slowed by slope and travels at night along ridges, valley floors and trails. A defensible model would need a published resistance surface for wolves in this region (Mexican wolf connectivity studies are the place to look) and a 1940s settlement and ranch layer. Her US legs (Whitewater Creek, the San Luis and Animas mountains, the draws and canyons) are short hops between named features; there the order of stops already says most of what a model could.

## Rolling it out

What would change:

1. A seed list of the legs to model: `pipeline/seeds/modeled-legs.csv` (journey, from_seq, mode, corridor, heading), in place of the `LEGS` dictionary in `least_cost.py`.
2. `pipeline/src/crossing/build_story.py`: for a leg in that list, call `least_cost.route()` instead of `curve()`, with `method: modeled`, `certainty: inferred`, `source: this-site` and the modelled reasoning text. Simplify harder first (one Chaikin round, 150 m tolerance): the 86 lines are 16,700 vertices and 474 KB, about as much as the whole of `data/journeys.geojson` today.
3. `data/schema/story-layer.schema.json` already allows `method: modeled`, but has `additionalProperties: false`, so `cost_model`, `detour_ratio` and `flags` would need adding there, or folding into `reasoning`.
4. `site/src/map/StoryLayers.tsx`: today every segment that is not `narrated-path` is drawn in the schematic style. A modelled line needs its own style and a key entry, and the card should say "modelled path, not the book's". `site/src/map/corridor.ts` buffers segments for talk on the road and assumes gentle curves; check it on the wigglier lines.
5. Rebuild: `uv run --project pipeline python -m crossing.build_story`, then `crossing.validate`, the raised data, and the spoiler-leak test (the lines keep their segments' `first_seen`).
6. A CHANGELOG entry and a decision record for the cost model and its version.

## Questions for you

1. Adopt modelled lines at all, and if so only for the sierra and valley legs listed under "What works", leaving flat and summary legs as curves?
2. Show a modelled line as a line, or as a band (the spread between the full model and slope alone) to carry its doubt?
3. J4 19 and 20: about 100 km in one day by the text. Move the opera camp, or note on the leg that the text compresses the ride?
4. Is it worth digitising period roads from the AMS 1:250,000 sheets? It is the one input that would make the road legs better than the curve.
5. The J5 lake camp: move the stop onto the shore, or replace Natural Earth's lake with INEGI's water bodies?

## Every segment

Straight: geodesic distance between the stops. Off schematic and off slope-only: Hausdorff distance from the modelled path to the schematic curve, and to the slope-only path. "Candidate": no flag; "review": a flag (see notes); "keep schematic (summary)": modelled for comparison only; "not modelled": the text does not have the rider choose the way.

| Segment | Leg | Travel | Result | Straight km | Schematic km | Modelled km | Detour | Off schematic km | Off slope-only km | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J1 01 | Sierra de la Madera (eastern slopes) to Crossing of the Bavispe | wolf | candidate | 21.9 | 22.1 | 25.7 | 1.17 | 5.1 | 6.2 |  |
| J1 02 | Crossing of the Bavispe to The border at 108°30′ W | wolf | candidate | 165.7 | 166.8 | 177.8 | 1.07 | 9.1 | 1.3 |  |
| J2 06 | The boundary, a monument in sight to Down the Cajon Bonita | horse | candidate | 24.7 | 24.8 | 25.9 | 1.05 | 1.8 | 1.3 |  |
| J2 07 | Down the Cajon Bonita to Passes of the Sierra de la Cabellera | horse | candidate | 33.1 | 33.3 | 38.6 | 1.17 | 7.3 | 6.1 |  |
| J2 08 | Passes of the Sierra de la Cabellera to The river crossing (the deputies) | horse | candidate | 21.5 | 21.7 | 28.5 | 1.32 | 8.3 | 8.3 |  |
| J2 09 | The river crossing (the deputies) to The mud-house settlement | horse | candidate | 9.6 | 9.7 | 10.1 | 1.06 | 1.0 | 0.1 |  |
| J2 10 | The mud-house settlement to Colonia Morelos (the fair) | horse | candidate | 9.6 | 9.6 | 9.9 | 1.04 | 0.6 | 0.4 |  |
| J2 11 | Colonia Morelos (the fair) to The hacienda | horse | candidate | 0.9 | 0.9 | 0.9 | 1.04 | 0.1 | 0.0 |  |
| J2 12 | The hacienda to Into the Pilares Teras | horse | candidate | 17.9 | 18.1 | 20.1 | 1.12 | 3.9 | 3.6 |  |
| J3 01 | The wolf's grave, a high pass in the Pilares to A promontory above the Bavispe | horse | review | 18.8 | 18.9 | 21.4 | 1.14 | 1.1 | 1.8 | stops closer than the text's time suggests (1.1 km/h) |
| J3 02 | A promontory above the Bavispe to El Tigre | horse | keep schematic (summary) | 16.7 | 16.8 | 24.0 | 1.44 | 2.4 | 1.5 |  |
| J3 03 | El Tigre to Among the Indians in the Sierras | horse | keep schematic (summary) | 33.9 | 34.1 | 40.4 | 1.19 | 6.3 | 1.3 |  |
| J3 04 | Among the Indians in the Sierras to The eastern escarpment above the Bavispe barranca | horse | keep schematic (summary) | 36.3 | 36.5 | 39.7 | 1.10 | 3.2 | 1.8 |  |
| J3 10 | Colonia Oaxaca (the alguacil's house) to Colonia Morelos | horse | candidate | 19.1 | 19.3 | 20.0 | 1.04 | 1.0 | 0.3 |  |
| J3 11 | Colonia Morelos to The road north toward Ojito | horse | candidate | 7.5 | 7.5 | 7.7 | 1.03 | 0.2 | 0.7 |  |
| J3 12 | The road north toward Ojito to The border at Douglas | horse | candidate | 57.8 | 58.2 | 60.3 | 1.04 | 4.2 | 1.3 |  |
| J4 09 | Douglas to Agua Prieta | horse | candidate | 2.5 | 2.5 | 2.5 | 1.02 | 0.2 | 0.0 |  |
| J4 10 | Agua Prieta to Ojito | horse | review | 55.6 | 56.0 | 57.7 | 1.04 | 5.5 | 1.6 | brisk for the text's time (7.2 km/h) |
| J4 11 | Ojito to Colonia Morelos at midnight | horse | candidate | 7.5 | 7.5 | 7.7 | 1.03 | 0.9 | 0.6 |  |
| J4 13 | Bacerac (Keno) to The eastern rim of the escarpment at sunrise | horse | candidate | 46.3 | 46.6 | 53.2 | 1.15 | 10.3 | 10.9 |  |
| J4 14 | The eastern rim of the escarpment at sunrise to The plains, with the Tarahumaras | horse | candidate | 19.5 | 19.6 | 20.8 | 1.07 | 1.3 | 0.5 |  |
| J4 15 | The plains, with the Tarahumaras to Colonia Juárez | horse | candidate | 16.8 | 16.9 | 20.1 | 1.20 | 2.8 | 0.3 |  |
| J4 16 | Colonia Juárez to Casas Grandes | horse | candidate | 14.1 | 14.2 | 14.5 | 1.03 | 0.7 | 0.6 |  |
| J4 17 | Casas Grandes to The girl, at a fire in an oak grove | horse | candidate | 7.5 | 7.6 | 7.6 | 1.02 | 0.1 | 0.0 |  |
| J4 18 | The girl, at a fire in an oak grove to The Hacienda de San Diego | horse | candidate | 8.8 | 8.8 | 9.9 | 1.13 | 2.2 | 0.6 |  |
| J4 19 | The Hacienda de San Diego to Mata Ortiz, on the road south | horse | review | 7.2 | 7.3 | 7.4 | 1.02 | 0.5 | 0.5 | the model needs 19 h where the text allows about 12; too fast for the text's time (8.3 km/h over 19+20) |
| J4 20 | Mata Ortiz, on the road south to The opera company stranded on the Madera road | horse | review | 82.2 | 82.8 | 92.2 | 1.12 | 7.1 | 4.9 | passes 0.8 km from las-varas, where the text does not have the rider pass; the model needs 19 h where the text allows about 12; too fast for the text's time (8.3 km/h over 19+20); passes within 1.5 km of: las-varas |
| J4 21 | The opera company stranded on the Madera road to Camps by the river | horse | candidate | 12.8 | 12.9 | 13.7 | 1.06 | 2.9 | 2.7 |  |
| J4 22 | Camps by the river to Crossing of the old wagon road to Namiquipa | horse | review | 11.0 | 11.1 | 11.8 | 1.08 | 1.9 | 0.6 | stops closer than the text's time suggests (0.4 km/h) |
| J4 23 | Crossing of the old wagon road to Namiquipa to Las Varas | horse | review | 23.5 | 23.7 | 24.0 | 1.02 | 0.4 | 0.1 | the stops themselves run against the text's direction; stops closer than the text's time suggests (1.2 km/h) |
| J4 24 | Las Varas to The steer herd on the road to Boquilla | horse | candidate | 13.4 | 13.5 | 14.2 | 1.05 | 0.8 | 0.5 |  |
| J4 25 | The steer herd on the road to Boquilla to Their horses, up from the lake | horse | candidate | 9.3 | 9.4 | 12.2 | 1.30 | 2.9 | 3.8 |  |
| J4 26 | Their horses, up from the lake to The manco's riders, the Boquilla hacienda in sight | horse | candidate | 5.9 | 5.9 | 6.1 | 1.04 | 0.7 | 0.3 |  |
| J4 27 | The manco's riders, the Boquilla hacienda in sight to Following the horses' tracks north | horse | candidate | 20.8 | 20.9 | 21.8 | 1.05 | 2.4 | 0.0 |  |
| J4 28 | Following the horses' tracks north to Quijada's remuda | horse | candidate | 15.6 | 15.7 | 16.3 | 1.04 | 1.7 | 0.4 |  |
| J4 29 | Quijada's remuda to Boquilla y Anexas (the manco falls) | horse | candidate | 29.2 | 29.4 | 30.0 | 1.03 | 0.9 | 0.9 |  |
| J4 30 | Boquilla y Anexas (the manco falls) to Off the road north of Boquilla, west to a river | horse | candidate | 7.2 | 7.2 | 7.3 | 1.01 | 0.3 | 0.0 |  |
| J4 31 | Off the road north of Boquilla, west to a river to The dry camp after the night ride | horse | candidate | 21.4 | 21.6 | 22.8 | 1.06 | 4.3 | 0.0 |  |
| J4 32 | The dry camp after the night ride to San José | horse | candidate | 20.9 | 21.0 | 21.6 | 1.04 | 0.7 | 0.2 |  |
| J4 33 | San José to The river camp where Boyd is shot | horse | candidate | 0.4 | 0.4 | 0.4 | 1.06 | 0.1 | 0.0 |  |
| J4 34 | The river camp where Boyd is shot to The road where the workers' truck takes Boyd | horse | candidate | 7.5 | 7.6 | 8.1 | 1.07 | 1.3 | 0.6 |  |
| J4 35 | The road where the workers' truck takes Boyd to The blind man's house | horse | candidate | 11.1 | 11.2 | 11.6 | 1.04 | 0.9 | 1.5 |  |
| J4 36 | The blind man's house to The desert crossroads on the main road north | horse | candidate | 10.1 | 10.2 | 12.9 | 1.28 | 2.5 | 3.9 |  |
| J4 37 | The desert crossroads on the main road north to Mata Ortiz, the blue tienda | horse | candidate | 22.3 | 22.4 | 24.7 | 1.11 | 2.7 | 0.7 |  |
| J4 38 | Mata Ortiz, the blue tienda to San Diego, where he finds Boyd | horse | candidate | 7.2 | 7.3 | 7.4 | 1.02 | 0.5 | 0.5 |  |
| J4 39 | San Diego, where he finds Boyd to Casas Grandes at 3 a.m., for the doctor | horse | candidate | 15.8 | 15.9 | 16.6 | 1.05 | 1.4 | 0.4 |  |
| J4 40 | Casas Grandes at 3 a.m., for the doctor to Back to San Diego, in the doctor's car | car | not modelled | 15.8 | 15.9 |  |  |  |  | by car on the road: the leg is a road, not a choice over terrain |
| J5 01 | San Diego, leaving at dusk to Mata Ortiz | horse | candidate | 7.2 | 7.3 | 7.4 | 1.02 | 0.5 | 0.5 |  |
| J5 02 | Mata Ortiz to Within earshot of the Las Varas crossing | horse | review | 69.9 | 70.4 | 76.1 | 1.09 | 7.1 | 2.5 | brisk for the text's time (6.3 km/h) |
| J5 03 | Within earshot of the Las Varas crossing to Boquilla at noon | horse | candidate | 32.8 | 33.0 | 33.3 | 1.02 | 1.6 | 0.9 |  |
| J5 04 | Boquilla at noon to La Pinta by moonlight | horse | candidate | 15.1 | 15.2 | 15.6 | 1.04 | 0.5 | 0.1 |  |
| J5 05 | La Pinta by moonlight to Santa Ana de Babícora at midnight | horse | candidate | 29.4 | 29.6 | 29.9 | 1.02 | 1.5 | 1.1 |  |
| J5 06 | Santa Ana de Babícora at midnight to A stream of the Santa María headwaters | horse | candidate | 3.8 | 3.9 | 4.0 | 1.03 | 0.5 | 0.0 |  |
| J5 07 | A stream of the Santa María headwaters to Back through Santa Ana, with the girl | horse | candidate | 3.8 | 3.9 | 4.0 | 1.03 | 0.5 | 0.0 |  |
| J5 08 | Back through Santa Ana, with the girl to La Boquilla after dark | horse | review | 43.8 | 44.0 | 45.3 | 1.03 | 5.4 | 0.6 | brisk for the text's time (7.0 km/h); passes within 1.5 km of: la-pinta |
| J5 09 | La Boquilla after dark to Camp at the edge of the lake | horse | review | 13.8 | 13.9 | 25.2 | 1.83 | 6.2 | 6.2 | detour 1.83; brisk for the text's time (7.0 km/h) |
| J5 10 | Camp at the edge of the lake to Las Varas | horse | candidate | 19.0 | 19.1 | 19.6 | 1.03 | 2.2 | 1.1 |  |
| J5 11 | Las Varas to Camp on the river south of Mata Ortiz | horse | candidate | 68.7 | 69.1 | 78.7 | 1.15 | 7.1 | 3.5 |  |
| J5 12 | Camp on the river south of Mata Ortiz to San Diego, on a feast day | horse | candidate | 16.2 | 16.3 | 16.8 | 1.03 | 1.5 | 1.1 | passes within 1.5 km of: mata-ortiz |
| J5 13 | San Diego, on a feast day to Cuauhtémoc, as far south as he rides | horse | keep schematic (summary) | 232.0 | 233.4 | 241.9 | 1.04 | 23.9 | 6.1 | passes within 1.5 km of: ignacio-zaragoza |
| J5 14 | Cuauhtémoc, as far south as he rides to Namiquipa | horse | keep schematic (summary) | 107.7 | 108.4 | 113.0 | 1.05 | 15.2 | 3.5 |  |
| J5 15 | Namiquipa to La Norteña, as far west as he rides | horse | keep schematic (summary) | 109.7 | 110.5 | 117.7 | 1.07 | 17.6 | 13.7 |  |
| J5 16 | La Norteña, as far west as he rides to The crossroads at Buenaventura | horse | keep schematic (summary) | 98.3 | 99.0 | 105.5 | 1.07 | 8.7 | 0.2 | passes within 1.5 km of: san-jose |
| J5 17 | The crossroads at Buenaventura to Álamo | horse | keep schematic (summary) | 14.6 | 14.7 | 15.6 | 1.07 | 0.9 | 1.0 | the stops themselves run against the text's direction |
| J5 18 | Álamo to Galeana | horse | keep schematic (summary) | 40.6 | 40.9 | 42.6 | 1.05 | 2.2 | 2.8 |  |
| J5 19 | Galeana to Casas Grandes, December | horse | keep schematic (summary) | 43.6 | 43.9 | 43.8 | 1.01 | 2.5 | 0.8 |  |
| J6 01 | Boyd lifted onto the workers' truck to Mata Ortiz, the truck passing | reported | not modelled | 42.5 | 42.8 |  |  |  |  | reported: the book only hears of this leg, so no way can be modelled |
| J6 02 | Mata Ortiz, the truck passing to San Diego, the Muñoz house | reported | not modelled | 7.2 | 7.3 |  |  |  |  | reported: the book only hears of this leg, so no way can be modelled |
| J6 03 | San Diego, the Muñoz house to Namiquipa, the girl's mother | reported | not modelled | 124.4 | 125.2 |  |  |  |  | reported: the book only hears of this leg, so no way can be modelled |
| J6 04 | Namiquipa, the girl's mother to Bachíniva, in the corrido | reported | not modelled | 56.0 | 56.4 |  |  |  |  | reported: the book only hears of this leg, so no way can be modelled |
| J6 05 | Bachíniva, in the corrido to Galeana, two men killed | reported | not modelled | 153.6 | 154.6 |  |  |  |  | reported: the book only hears of this leg, so no way can be modelled |
| J6 06 | Galeana, two men killed to San Lorenzo, where Boyd fell | reported | not modelled | 61.8 | 62.2 |  |  |  |  | reported: the book only hears of this leg, so no way can be modelled |
| J6 07 | San Lorenzo, where Boyd fell to San Buenaventura, the grave | reported | not modelled | 37.3 | 37.6 |  |  |  |  | reported: the book only hears of this leg, so no way can be modelled |
| J7 23 | Mexican customs at Berendo to Janos | horse | candidate | 58.8 | 59.2 | 61.3 | 1.04 | 7.3 | 5.2 |  |
| J7 24 | Janos to Casas Grandes | horse | candidate | 61.2 | 61.6 | 64.7 | 1.06 | 10.4 | 3.5 |  |
| J7 25 | Casas Grandes to San Diego, the families gone | horse | candidate | 15.8 | 15.9 | 16.6 | 1.05 | 1.1 | 0.7 |  |
| J7 26 | San Diego, the families gone to Las Varas | horse | candidate | 84.6 | 85.2 | 94.8 | 1.12 | 5.7 | 5.6 | passes within 1.5 km of: mata-ortiz |
| J7 27 | Las Varas to Camp on the plain by the lake, the red plane | horse | candidate | 24.6 | 24.7 | 28.5 | 1.16 | 3.2 | 4.7 |  |
| J7 28 | Camp on the plain by the lake, the red plane to Babícora | horse | candidate | 15.2 | 15.3 | 16.9 | 1.11 | 2.4 | 2.5 |  |
| J7 29 | Babícora to Santa Ana de Babícora | horse | candidate | 36.3 | 36.5 | 36.9 | 1.02 | 1.9 | 0.4 |  |
| J7 30 | Santa Ana de Babícora to Namiquipa, now a mining camp | horse | candidate | 25.0 | 25.2 | 25.8 | 1.03 | 2.5 | 0.5 |  |
| J7 31 | Namiquipa, now a mining camp to Temósachic | horse | keep schematic (summary) | 52.3 | 52.6 | 55.3 | 1.06 | 2.5 | 0.6 |  |
| J7 32 | Temósachic to Madera, the late April fair | horse | keep schematic (summary) | 40.4 | 40.6 | 42.9 | 1.06 | 2.3 | 1.3 |  |
| J7 33 | Madera, the late April fair to Babícora before dawn | horse | keep schematic (summary) | 39.0 | 39.2 | 41.0 | 1.05 | 5.4 | 4.6 |  |
| J7 34 | Babícora before dawn to Casas Grandes, the Camino Recto hotel | horse | candidate | 126.5 | 127.3 | 132.8 | 1.05 | 3.5 | 2.7 |  |
| J7 35 | Casas Grandes, the Camino Recto hotel to The high country of the Babícora | horse | keep schematic (summary) | 119.8 | 120.6 | 125.2 | 1.04 | 7.9 | 3.9 | passes within 1.5 km of: san-jose |
| J7 36 | The high country of the Babícora to Quijada's cabin | horse | candidate | 25.6 | 25.7 | 39.7 | 1.55 | 7.9 | 8.6 | passes within 1.5 km of: boquilla |
| J7 37 | Quijada's cabin to San Buenaventura | horse | candidate | 47.3 | 47.6 | 55.3 | 1.17 | 7.2 | 9.1 |  |
| J7 38 | San Buenaventura to Boyd's grave, on the Gallego road | horse | candidate | 1.6 | 1.6 | 1.6 | 1.00 | 0.1 | 0.0 |  |
| J7 39 | Boyd's grave, on the Gallego road to Past the lights of Casas Grandes, to the west | horse | candidate | 70.6 | 71.1 | 73.3 | 1.04 | 5.8 | 6.1 | passes within 1.5 km of: galeana |
| J7 40 | Past the lights of Casas Grandes, to the west to The Casas Grandes River, across the Guzmán road | horse | candidate | 26.2 | 26.4 | 27.7 | 1.06 | 4.4 | 0.7 |  |
| J7 41 | The Casas Grandes River, across the Guzmán road to Corralitos before dawn | horse | candidate | 9.7 | 9.7 | 10.3 | 1.07 | 1.0 | 1.6 |  |
| J7 42 | Corralitos before dawn to The attack on the river trail, and the gypsies' camp | horse | review | 5.8 | 5.8 | 6.1 | 1.06 | 0.8 | 0.6 | brisk for the text's time (6.1 km/h) |
| J7 43 | The attack on the river trail, and the gypsies' camp to The border, west of Dog Springs | horse | candidate | 114.9 | 115.7 | 119.7 | 1.04 | 2.8 | 5.3 |  |
