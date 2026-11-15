# Vignettes for Parts III and IV (14 November 2026)

Twelve new vignettes for J4 (the brothers ride into Chihuahua), J5 (Billy alone), J6 (Boyd and "the girl", reported) and J7 (Billy's last journey). Five are character vignettes on long, empty stretches of those journeys. The set brings the map from 13 to 25 vignettes, before the Parts I and II agent's share.

## What changed

- `art/vignettes/subjects_parts_3_4.py`: the twelve subjects, exporting `SUBJECTS`. `make_vignettes.py` is unchanged.
- `art/vignettes/traced/rider-annie-g.json`: one traced horse and rider, from Eadweard Muybridge's Animal Locomotion plate 580 (1887, public domain). Every rider in the set reuses it at a different size and facing, with hats, a slicker, a shotgun, a second rider or a travois drawn on by hand.
- `pipeline/seeds/vignettes.csv`: twelve rows appended at the end. Then the rebuilt `data/vignettes.geojson`, `data/parquet/vignettes.parquet` and the sprite in `site/public/sprites/`.

Checks: `crossing.build_vignettes`, `art.vignettes.make_vignettes`, `crossing.validate`, `crossing.downloads` and `crossing.echo_check` (0 shared runs), `ruff check art/vignettes/`. No site code changed.

## The vignettes

Contact sheet (each drawing large, then at about 53 px and 72 px on the map's paper): `private/review/stage-9/vignettes-parts-3-4/contact-sheet.png`.

"On the line" means the seed row gives its own `lon`, `lat` on the route in `data/journeys.geojson`, and `ref` is the nearest stop of that leg.

| id | Subject and why it matters | Placed | Side, zooms, priority | first_seen | Label | Source and licence |
| --- | --- | --- | --- | --- | --- | --- |
| brothers-and-the-girl | Billy and Boyd ride south from San Diego, "the girl" riding double behind Boyd | On the line, j4-seg-20 at 85% (Mata Ortiz to the opera camp) | w, 9 to 12, 3 | 3-01 | none | Muybridge plate 580 (PD), traced; "the girl" and hats drawn |
| boyd-and-the-girl | Boyd and "the girl" gone from San Diego together; Billy never sees them ride again | On the line, j6-seg-03 at 25% | e, 9 to 12, 3 | 3-14 | none | Muybridge (PD), traced; Boyd's straw hat and "the girl" drawn |
| billy-searching | Billy alone in grey weather, shotgun across the saddle, looking for Boyd for weeks | On the line, j5-seg-13 at 60% (towards Cuauhtémoc) | e, 9 to 12, 3 | 3-14 | none | Muybridge (PD), traced; hat and shotgun drawn |
| billy-in-the-rain | Billy riding north on a wet horse in the rain, in his slicker, towards San Buenaventura | On the line, j7-seg-37 at 50% | sw, 9 to 12, 3 | 4-06 | none | Muybridge (PD), traced and mirrored; slicker, hat and rain drawn |
| bones-travois | Billy rides north three days with his brother's remains on a travois of sapling poles | On the line, j7-seg-43 at 50% (river trail to the border) | e, 8 to 12, 2 | 4-08 | North with Boyd's bones | Muybridge (PD), traced; travois after a photograph of a mule travois, about 1876, Little Bighorn Battlefield NM (PD) |
| windmill-tank | The brothers water Niño and Bailey at a limestone trough under a turning windmill whose shadow wheels over the prairie | On the line, j4-seg-29 at 40% (the book gives no place; it falls between Quijada's remuda and Boquilla) | e, 9 to 12, 2 | 3-05 | Windmill and stone tank | After SteveStrummer's Aermotor windmill, New Mexico (CC0) and an 1895 Aermotor advertisement (PD) |
| corriente-steers | Vaqueros trailing a thousand wild corriente steers from the Babícora north to the Naco pens | j4-steer-herd | n, 9 to 12, 2 | 3-04 | Corriente steers, bound for Naco | After longhorn photographs by Carol M. Highsmith (PD) and Clinton and Charles Robertson (CC BY 2.0) |
| sandhill-cranes | Camped on a gravel bar with "the girl", Billy watches the cranes go south in the night (they come back in 3-13, 4-06, 4-08) | j5-river-camp | w, 9 to 12, 2 | 3-12 | Sandhill cranes going south | After a USFWS photograph of cranes in flight (PD) |
| cottonwood-camp | The camp under the river cottonwoods near San José where Boyd is shot at dawn | j4-shooting | e, 9 to 12, 2 | 3-08 | Cottonwood camp on the river | Drawn |
| workers-truck | The old flatbed full of farmworkers that takes the wounded Boyd away | j6-truck | sw, 10 to 12, 2 | 3-08 | Farmworkers' flatbed truck | After Alf van Beem's 1930 Ford Model AA (CC0) |
| boyds-grave | Billy lifts the board cross from Boyd's cairn in the walled burial ground and digs into the night | j7-boyds-grave | e, 9 to 12, 1 | 4-06 | Boyd's grave, Gallego road | Drawn from the book's description |
| madera-fair | The April fair beyond the railway at Madera: strung lights, pitch tents, pine smoke and the sawmill | j7-madera | sw, 9 to 12, 3 | 4-05 | Madera fair, late April | Drawn |

Each row's `note` (a paraphrase), `credit` and `reasoning` are in the seed. Labels follow the brief: the riders carry none, because they are plain at sight; the travois carries one, because a travois is not plain at 53 px.

## On the map

Dev server on port 5193, progress "all" (stopped since). Screenshots in `private/review/stage-9/vignettes-parts-3-4/`:

| File | Zoom | Vignettes drawn (mine in bold) |
| --- | --- | --- |
| `las-varas-babicora-z8.png` | 8 | (mine start at 9, except the travois) |
| `las-varas-babicora-z9.png` | 9 | **cottonwood-camp, sandhill-cranes, billy-in-the-rain, boyd-and-the-girl, brothers-and-the-girl, boyds-grave, madera-fair, corriente-steers, windmill-tank**, blind-man, red-plane, opera-caravan |
| `mata-ortiz-z9.png` | 9 | **sandhill-cranes, brothers-and-the-girl, boyd-and-the-girl, cottonwood-camp**, san-diego-gate, paquime, blind-man |
| `san-jose-z10.png` | 10 | **workers-truck, cottonwood-camp, brothers-and-the-girl, boyd-and-the-girl**, blind-man |
| `buenaventura-z9.png`, `namiquipa-z9.png` | 9 | **billy-in-the-rain, boyds-grave, billy-searching** and the rest of the Babícora group |
| `madera-z10.png`, `travois-z9.png`, `grave-z11.png`, `windmill-z11.png` | 9 to 11 | one each, close up |

Nothing collided away at zoom 9 in these views. `max_zoom` is exclusive in the layer filter, so "9 to 12" means up to zoom 11.99, as for the existing set.

## References and requests

- 10 reference images, recorded in `private/overnight/vignettes/refs/refs.csv` (rows appended), files in the same folder.
- 28 network requests (all Wikimedia Commons: 18 API searches, 10 file downloads), User-Agent `crossing-map-research/0.1`, 2.2 s apart, no 429. Log with URL, date and bytes: `private/overnight/vignettes/tools-parts-3-4/requests.log`; responses cached in `private/cache/vignettes-2/`.
- Tools (preview, screenshots, fetch, the copy of the tracing script): `private/overnight/vignettes/tools-parts-3-4/`. The rider trace: `trace.py private/overnight/vignettes/refs/rider-muybridge-580a7.jpg out.json --mask rembg --flip --box 4,8,92,90 --tones 0.3`.

## Doubtful, or for the owner

1. **Muybridge's rider is a jockey.** The trace keeps his short stirrups and upright seat; the cowboy hat and the leg line make him read as a stock rider at map size, but close up he is still a racetrack figure. A Russell Lee FSA photograph of a cowboy (also public domain) would be truer to 1940, if the owner wants a second trace.
2. **Boyd and "the girl" (J6) overlap.** The two horses side by side make one busy shape at 53 px. A version with them in single file would read more cleanly.
3. **"the girl" in the brothers' drawing** is small: at 53 px she reads as a dark mark behind Boyd. The ride south from San Diego in 3-01 is the book's image of the three of them, so I kept her.
4. **The cranes trace was dropped.** Traced as a paper-filled silhouette, the crane read as a white shape with a ragged edge; the drawn cranes (ink neck, legs and wings) read better. The trace is parked as `private/overnight/vignettes/traced/crane-dropped.json`.
5. **Labels on Boyd's death.** "North with Boyd's bones" and "Boyd's grave, Gallego road" are blunt. Both are hidden until 4-06 and 4-08, so they do not spoil, but the owner may want softer wording.
6. **No reference for the grave, the cottonwoods or the Madera fair.** Commons searches for wooden-cross graves and for cottonwoods found nothing usable inside the request budget, so these are drawn from the book and general knowledge, and credited as "Drawn".
7. **Shared files.** The other agent also appends to the seed and rebuilds `data/vignettes.geojson`, the parquet and the sprite, so those four will conflict on merge. Rerun `crossing.build_vignettes` and `art.vignettes.make_vignettes` after merging both seeds.
