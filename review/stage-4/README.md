# Stage 4 review packet: Parts II–IV places, first pass

This is the groundwork for stage 4 (plan section 9): the places of Parts II–IV, read from the text and placed. Routes, stops, areas and the map come next, once you have answered the questions below.

## What was done

1. **Reading.** Each Part was read in full, one reader per Part, against the plan's journeys (section 2.2). Every claim that changed the plan was checked against the text before the plan changed. The corrections are in `docs/plan.md`, sections 2.2 to 2.4, each marked v5.
2. **Seeds.** `pipeline/seeds/parts2-4.csv` lists 123 named places in journey order (J3–J7), followed by the places named only in tales. Each row gives the book's spelling where it differs, the first episode that names it anywhere in the book, its journey and its role. Streets, buildings, roads, railroads, unnamed stops, broad regions, states and countries are not seeded. The roads and unnamed stops return as route segments and inferred areas in the stops files.
3. **Gazetteer.** `places.csv` is the pipeline's first pass: 54 places resolved, 52 for review, 17 with no candidate. The 186 Wikidata searches it needed are cached.
4. **Picks.** Every place was then checked by hand, by region, against the journey's order and the distances the text gives. Distances are straight-line on WGS 84 (pyproj), and sources are named in each row. The result is `pipeline/seeds/parts2-4-place-overrides.csv`, with an action, a confidence and the reasoning for each place:

| Action | High | Medium | Low |
| --- | --- | --- | --- |
| use | 73 | 26 | 1 |
| exclude (draw as a line or area instead) | 5 | 5 | |
| unresolved | | | 13 |

The checks overturned many first-pass picks. Durango, Monterrey and Zacatecas had resolved to neighbourhoods of Ciudad Juárez with the same names. Torreón and Rodeo had gone to New Mexico. Dog Springs went to Socorro County, 279 km from the border where the text has Billy cross. The SK Bar went to a cemetery in Arizona, and the Hacienda de San Diego to the wrong San Diego, 200 km away.

## Your answers (11 November 2026)

1. La Boquilla: the lake town, as proposed.
2. Soto Máynez: one point with both names, with the doubt kept on the place and in `docs/open-questions.md`, open to readers' evidence later.
3. Nahuerichic: Nahuerachi, since its location fits the estate; the name difference is an open question.
4. to 6.: as proposed.

## The questions as asked

1. **La Boquilla.** The text calls the town Boquilla, La Boquilla and Boquilla y Anexas, and puts it by the Babícora lake on the road east from Las Varas. INEGI's "Boquilla y Anexas" is in Guerrero municipio, 135 km from Las Varas. I propose La Boquilla in Gómez Farías municipio (GeoNames 8749710), 10 km east of the lake, and have corrected the plan to match. Agree?
2. **Soto Máynez.** INEGI gives Soto Máynez as the official name of Santa Ana de Babícora, so the two share a point. But in 3-12 the girls are walking toward Soto Maynez after the riders have passed back through Santa Ana, as if it were another town. Show one point with both names (proposed), or follow the book and leave Soto Máynez as a tale place without a point?
3. **Nahuerichic.** Quijada's division of the Babícora. The nearest name match is Nahuerachi, a small place 7 km from Madera (GeoNames 13416932). The names differ by one vowel, and I have not found a source tying the two together. Use it, or leave the division unplaced?
4. **Unresolved places (13).** My proposal for each kind:
   - **Stops on a journey, drawn as inferred areas around a best estimate:**
     - Huisiachepic: on the upper Bavispe, about 28 km south of Tamichopa.
     - The SK Bar: about 14 km north of Cloverdale, from the text's nine miles.
     - Dog Springs: the boundary south of Hermanas.
     - Álamo: near Galeana.
   - **Ranches Billy works for, told only in summary:** no point. The panel names them. These are the Hashknife, the GS, the Carrizozo and the T Diamond.
   - **Tale places that cannot be placed:** no point; the panel names them. These are Trinidad, Los Horcones, La Quemada, Las Varitas and the Taliafero Ranch. Each has a best estimate in the overrides, in case you would rather show it.
5. **Tale places outside the story box.** Mexico City, Durango, Monterrey, Monclova, Torreón, Zacatecas, Parral, Ciudad Acuña, Chicago, McAllen, the Matador Ranch and Kwajalein have real coordinates but fall outside the map. The plan does not say how to show them. I propose a short "Named elsewhere" list in the panel, not map points.
6. **Summaries.** All 41 episode summaries are drafted in `data/episodes.json`. They're yours to edit, and the plan's rule is that you write them.

## Files

- `pipeline/seeds/parts2-4.csv`: the seeds.
- `pipeline/seeds/parts2-4-place-overrides.csv`: the picks, with reasoning.
- `review/stage-4/places.csv`: the gazetteer's first pass, with every candidate.
- Private, not committed: the per-Part place inventories and summary drafts in `private/book/`, and the per-region pick drafts in `private/review/`.
