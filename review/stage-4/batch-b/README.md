# Stage 4, batch B: Parts III and IV on the map (J4 to J7)

All seven journeys are now drawn. This batch adds the rest of J4 from the Hacienda de San Diego (22 stops), J5, Billy looking for Boyd and the girl (20 stops), J6, Boyd and the girl as reported (8 stops), and J7, Billy's war years and third crossing (57 stops).

## What was built

- **Stops.** `pipeline/seeds/part3-4-stops.csv`, from the plan's journeys (section 2.2), the picks in `parts2-4-place-overrides.csv` and a full reading of Parts III and IV. Every stop carries its reasoning in paraphrase; inferred stops are circles sized to the doubt. The file has a new column, `travel`: how the leg arriving at the stop was made (empty for horseback, or foot, truck, car, bus, train, reported).
- **Travel.** Each route segment carries `travel` from its arriving stop (`null` for horseback), and `data/schema/story-layer.schema.json` allows it. J6 is reported throughout: its stops and segments have certainty `reported`, travel `reported`, and each stop names who tells it.
- **Snaps.** `pipeline/seeds/part3-4-snaps.csv`, eight segments of J7, all Census TIGER 2023 roads in New Mexico. The table gives each snap's straight-line distance, route length and longest step (pyproj, WGS 84):

| Segment | Road (TIGER full name) | Straight | Route | Longest step |
| --- | --- | --- | --- | --- |
| Columbus to Deming | State Hwy 11 | 50.2 km | 51.9 km | 0.5 km |
| Deming to Hermanas | Hermanas Grade SW | 49.8 km | 51.2 km | 2.2 km (joining Deming) |
| Hermanas to Hachita (twice) | State Hwy 9, Luna and Grant | 35.6 km | 39.4 km | 1.7 km |
| Animas to the SK Bar | State Hwy 338 | 45.6 km | 49.0 km | 2.3 km (joining the SK Bar estimate) |
| Santa Rita to San Lorenzo | State Hwy 152 | 13.2 km | 15.1 km | 1.7 km |
| San Lorenzo to Emory Pass | State Hwy 152, Grant and Sierra | 18.1 km | 29.4 km | 1.7 km (switchbacks) |
| Emory Pass to the waystation | State Hwy 152 | 23.1 km | 34.6 km | 2.0 km |

- **Builder.** `crossing.build_story` reads the batch (a batch now names a set of Parts, so batch B covers III and IV) and builds all four Parts' places. A snap may name one TIGER file per county, separated by semicolons, and gaps under about 1 km between TIGER pieces are bridged (the Hermanas Grade has two). Part I's and batch A's features are unchanged apart from the new field (checked feature by feature).
- **Places.** 63 more places: Part III and IV stops and passing places, and the tale places inside the story box (the gypsies' Sonora towns, Bachíniva, Gallego, Guzmán and others). `elsewhere.json` now lists 15 places outside the map.
- **Raised.** `data/raised/` is rebuilt, so it includes the new stops and places; its routes are still J1 and J2 only.

Downloads: TIGER 2023 roads for Luna (35029), Grant (35017), Hidalgo (35023) and Sierra (35051) counties, into `private/cache/roads/tiger/`.

## Decisions I made alone

1. **`car` is a travel value.** Billy rides back to San Diego in the doctor's car (3-10); the brief's list had no word for it.
2. **J6 starts at the workers' truck (3-08), not at the ejido.** The Mata Ortiz woman at the blue tienda and the Muñoz woman report Boyd's ride north to San Diego, so it belongs to his journey. The blind man's wife, named in the plan as a source, says nothing about Boyd: Billy only tells the couple he lost his brother.
3. **J6's order follows the plan** (Namiquipa, Bachíniva, Galeana, San Lorenzo, San Buenaventura), though the singer's Bachíniva and Quijada's San Lorenzo are rival accounts of the same death. Namiquipa is the weakest stop: the book never shows the pair there; it rests on Boyd saying the girl wanted to see her mother.
4. **Mexican legs are curves.** Natural Earth's Casas Grandes river runs 30 to 50 km west of the real one at Casas Grandes and Corralitos, so it cannot carry the river trail in 4-06. Natural Earth's railroads have no named Noroeste line, and its Mexican roads are modern highways. Its Santa María fits the towns, but no leg is told as following it. INEGI's road network was not tried.
5. **Bus legs are curves.** The text names no road; only Socorro on the way north, which is a stop.
6. **The wagon-road crossing (J4.23) is south of the river camps.** After it the brothers ride south and reach Las Varas two days later, but Las Varas is to the north: the book's compass does not close here. The circle is wide (15 km) and the reasoning says so.
7. **Not separate stops:** the Florida Mountains (J7 snaps Columbus to Deming on NM 11, past them), the windmill tank (3-05), the ciénega camp (4-05), the Santa María watershed (4-06, a direction only).
8. **J5 ends at Casas Grandes.** Part III does not tell the ride north; Part IV opens at the Columbus gate.
9. **The Black Range stop is Emory Pass** (GNIS 906157), where the old road east crosses the range; the waystation is a circle on the plain east of Hillsboro.
10. **Quijada's cabin is a day's ride south of San Buenaventura** (Billy rides north all day from it), 57 km from Nahuerachi, the pick for the Nahuerichic division's name.
11. **Winslow is a stop with travel `reported`,** standing for the Hashknife linecamp. The ranch itself has no point. The same goes for the ranch out of Magdalena and the months before Silver City in July.

## For you to check

- `checklist.md`: every new stop and Part III and IV place, with links to check each on imagery.
- `shots/`: J4 to J7 whole on Classic, and close-ups: J4 and J5 around the Babícora lake, J7 in the bootheel, from Casas Grandes to the border, and over the Black Range. Satellite views are not included (MapTiler refuses localhost). Every journey was stepped through in the browser with no console errors.

## Questions for you

1. **J4 in 3-01 to 3-04.** The text puts the opera camp a few miles south of Las Varas, then has the brothers reach Las Varas for the first time two days after the wagon-road crossing. Keep the text's order with a loop back north (as drawn), or read 3-01's Las Varas as a slip and put the opera camp and river camps north of the town?
2. **J6.** Keep Bachíniva in the line, or show it as a separate reported point (the corrido) beside Quijada's account?
3. **Ash Wednesday.** The book dates Billy's arrival at Animas with the bones Ash Wednesday, after the 15 May date in 4-05. Note it on the stop, or leave it?
4. **Soto Máynez and Santa Ana** are two place points at the same spot, as the answer of 11 November asked. The labels sit on top of each other; one label with both names would need a small change to the app or the builder.

## Plan corrections I would make

- 2.2, J4: the stops between San Diego and Las Varas are in the text's order but its compass does not close (question 1).
- 2.2, J6: the sources are the Mata Ortiz woman, the Muñoz woman, the woman at the Namiquipa wake, the singer at the Camino Recto hotel and Quijada; not the blind man's wife.
- 2.2, J7: the Namiquipa woman (4-05), before Temósachic, is the first to say the bones lie at San Buenaventura; Quijada confirms it later.
- 2.2, J7: the road from Santa Ana to Namiquipa runs north in 4-04, where 3-12 had it west.
- 11, stage 4: the regions (La Babícora, the Animas Valley) and the false-dawn arrow are not in this batch.

## Note on the tiles

`crossing.plan_oblique` copies its archive to `site/public/tiles/oblique.pmtiles`. In this worktree that path was a symlink to the main checkout's `tiles/out/`, so the first run overwrote the main checkout's `tiles/out/oblique.pmtiles` with this branch's build. Rebuild it there if it matters; the symlink is now a plain copy.
