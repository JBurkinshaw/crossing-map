# Stage 4, batch A: Part II on the map (J3 and the start of J4)

Part II's journeys are drawn: J3, Billy alone in the Sierras and home (19 stops), and J4 from Lordsburg to the Hacienda de San Diego (19 stops). Part III's half of J4 comes in batch B.

## What was built

- **Builder.** `crossing.build_part1` is now `crossing.build_story`. It reads each batch's stops and snaps and the Parts built so far (`BATCHES`, `PARTS_BUILT`). Part I's output is unchanged byte for byte.
- **Stops.** `pipeline/seeds/part2-stops.csv`, from the plan's journeys (section 2.2), the picks in `parts2-4-place-overrides.csv` and the text. Every stop carries its reasoning; inferred stops are circles sized to the doubt.
- **Snaps.** `pipeline/seeds/part2-snaps.csv`. Where the text names the way, the route follows it: the Bavispe through the river towns (J3 from Huisiachepic to Colonia Oaxaca; J4 from Colonia Morelos up to Bacerac), and route 666, today's US 191, from Elfrida to Douglas (Census TIGER). Elsewhere a route is a gentle curve between stops, marked `schematic`.
- **App.** Journey inks for J3–J7 (Billy oxblood, Boyd green, "the girl" plum, per plan 5.1), the journey list shows only journeys with data, and a "Named elsewhere" list in the panel (so far only Mexico City).
- **Raised.** `data/raised/` now includes J3 and J4's stops and places; their routes are not raised yet (decision 0018).

## Decisions I made alone

1. **Mexican rivers snap to Natural Earth, not INEGI.** INEGI's 1:50,000 network has no river names, and a shortest path over it took long detours (63 km between Bacerac and Bavispe, 14 km apart). Natural Earth's Bavispe is the line the map already draws, so the route sits on the drawn river. INEGI stays in the Raised streams.
2. **Stops on the J3 sierra loop are areas.** The text names El Tigre and Huisiachepic and nothing else for weeks of riding; the promontory, the Indians' rancherías and the eastern escarpment are circles placed from the text's directions (see each stop's reasoning).
3. **The Parham house is Cloverdale,** as in Part I, and the SK Bar is the open-questions estimate, nine miles north.
4. **J4's mud towns are not separate stops.** The text passes "one by one through the squalid mud towns along the river" over seven days; the route follows the river and names Bacerac, where the text stops.

## For you to check

- `checklist.md`: every new stop and Part II place, with links to check each on imagery.
- `shots/`: J3 and J4 whole, and close-ups (upper Bavispe, the ride home, Arizona, the escarpment). Satellite views are not included: MapTiler refuses localhost, so check them on the preview.
- Questions: is the J3 sierra loop (stops 2 to 5) in the right country? It is the least certain part of the batch.
