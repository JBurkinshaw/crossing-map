# Stage 9: vignettes, round 3

The owner asked: "Do the vignette suggestions, checked against the text." This round adds 17 vignettes across all four Parts, so the map now has 54. Each candidate was checked against `private/book/text/` before it was drawn: does the scene exist, where is it, and which episode first shows it (`first_seen`). Where the text did not support a candidate as given, it was moved to where the book puts it, folded into another drawing, or dropped. The list below says which.

## What to look at

All images are in `private/review/stage-9/vignettes-round3/` (git ignores them here).

| File | What it shows |
| --- | --- |
| `contact-sheet.png` | Each new drawing at 220 px, and at 69 and 87 px (the map's sizes at zooms 9 and 12) |
| `bootheel-z9.png`, `bootheel-z10.png` | The bootheel: Echols' cabin, the calf, the wolf in the cholla, the empty house (all from zoom 10) |
| `animas-z10.png` | Don Arnulfo's house south of Animas |
| `sierra-j3-z9.png`, `bacerac-z9.png` | Billy in his rags with the bow, Keno at Bacerac |
| `casas-grandes-z9.png`, `casas-grandes-z10.png` | Colonia Juárez; taking "the girl" (from zoom 10) |
| `babicora-z9.png`, `babicora-z10.png`, `west-las-varas-z9.png` | Quijada, the remuda, the night train, Billy riding west to La Norteña |
| `buenaventura-z10.png` | The waterfowl at dawn |
| `temosachic-z9.png` | The corridero and Billy with his packhorse |
| `el-paso-z9.png` | The recruiting office |

The site was run with `cd site && npm run dev -- --port 5293`, reading progress "all", and shot with `private/overnight/vignettes/tools-round3/shots.mjs`.

## The new vignettes

Zooms are `min_zoom` to `max_zoom`. "Muybridge" is the traced horse and rider from Animal Locomotion plate 580, 1887 (public domain); "Muybridge horse" is the same outline with the rider cut away above the saddle (new in this round, `horse()` in the module).

| Id | Subject | Why it matters (paraphrase) | First seen | Pin, side | Zooms | Label | Source and licence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| echols-cabin | Echols' cabin, and old traps hanging on the smokehouse wall | The Parhams borrow the old wolfer's traps and baits; the hunt's tools come from here | 1-02 | j3-sk-bar, w | 10–12 | Echols' cabin, SK Bar | Drawn from the book |
| dead-calf | The calf's remains on the bloody snow, coyote tracks, junipers | Billy and his father look at the wolf's kill at the head of Foster Draw, the start of the hunt | 1-03 | place-foster-draw, se | 10–12 | The calf at Foster Draw | Drawn from the book |
| arnulfo-house | A low mud house on the plain, a horse tied at the cornerpost | The old man Don Arnulfo talks to Billy about wolves | 1-07 | place-animas, own point 4 km south, e | 9–12 | Don Arnulfo's house | After Russell Lee's adobe house at Peñasco, about 1940 (LoC, PD); Muybridge horse |
| wolf-in-the-cholla | The she-wolf in the trap, the drag snagged in a cholla | Billy finds her caught by the forefoot and ropes her | 1-08 | j1-cloverdale-creek, w | 10–12 | Caught, the drag in a cholla | Traced she-wolf (USFWS, PD); cholla after a White Sands NP photograph (PD) |
| parham-house | The house and barn at night, every window dark, the gate open | Billy comes home to find the house empty and his family gone | 2-04 | j3-parham-house, sw | 10–12 | The house, found empty | Drawn from the book |
| keno-bacerac | Keno and a roan standing head down under an elder before a whitewashed house | The brothers find Boyd's stolen horse and take him back | 2-07 | j4-bacerac, w | 9–12 | Keno, found at Bacerac | Muybridge horse (PD); house and tree drawn |
| taking-the-girl | Boyd galloping in with the shotgun and Billy's horse, the fire, "the girl" with her bundle | The brothers take "the girl" from the two men in the oak grove | 2-08 | j4-the-girl, se | 10–12 | Taking "the girl" from the fire | Muybridge and Muybridge horse (PD); the rest drawn |
| colonia-juarez | A brick house with a tin roof, the orchard rows, the plank bridge | The Mormon colony where the brothers pick apples and cross the river | 2-08 | j4-colonia-juarez, nw | 9–12 | Colonia Juárez, a Mormon colony | Drawn from the book |
| quijada | Quijada sitting his horse, smoking, the remuda's dust down the road | The superintendent who meets the brothers at a crossroads | 3-04 | own point on j4-seg-28 (40%), ref j4-tracking-north, n | 9–12 | Quijada at the crossroads | Muybridge, mirrored (PD); pines drawn |
| remuda | Horses bunched in the road among pines, Boyd throwing his loop | Boyd ropes Niño, Bailey and the Tom horse out of the Babícora remuda | 3-04 | own point on j4-seg-28 (80%), ref j4-quijada-remuda, ne | 9–12 | Roping Niño from the remuda | Muybridge and Muybridge horse (PD); pines drawn |
| night-train | A locomotive and tender with its headlight cone, smoke trailing, a horse watching | Billy wakes to a train going south that whistles for the Las Varas crossing | 3-12 | j5-las-varas-night, e | 9–12 | Night train for Las Varas | After a 1901 photograph of PRR locomotive 5075 (Internet Archive Book Images, PD) |
| recruiting-office | A crenellated brick armory with a flag, Billy walking away | Billy is turned down by the army for his heart at Deming, El Paso and Albuquerque | 4-01 | j7-el-paso, e | 8–12 | Turned away by the army | Drawn from the book |
| corridero | A singer under a hanging bulb, guitar on his knee, raising his glass | Billy first hears the corrido of the güero in a bodega at Temósachic | 4-05 | j7-temosachic, s | 9–12 | The corrido, Temósachic | Pose after a public-domain photograph of a migratory worker playing a guitar (Flickr) |
| waterfowl | Billy on his horse at dawn, skeins of birds over the sunrise and the water | Searching for Boyd, he watches waterfowl over the river at Buenaventura | 3-14 | j5-buenaventura, nw | 10–12 | Waterfowl at dawn, Buenaventura | Muybridge (PD); birds drawn |
| billy-in-rags | Billy, ragged, the holly bow across his back, among madroño and oak | His weeks alone in the Sierra after the wolf (J3, Indians' country to the escarpment) | 2-01 | own point on j3-seg-04 (40%), ref j3-indian-rancherias, e | 9–12 | (none) | Muybridge (PD); bow and trees drawn |
| billy-to-the-watershed | Billy riding west towards a sawtooth ridge, hat pulled low | His search for Boyd as far west as La Norteña (J5) | 3-14 | own point on j5-seg-15 (85%), ref j5-la-nortena, n | 9–12 | (none) | Muybridge, mirrored (PD) |
| billy-and-packhorse | Billy leading his packhorse through the pines | Weeks asking after his brother between Namiquipa, Temósachic and Madera (J7) | 4-05 | own point on j7-seg-31 (50%), ref j7-namiquipa, s | 9–12 | (none) | Muybridge and Muybridge horse with a drawn pack (PD); pines drawn |

The `note`, `credit` and `reasoning` of each are in `pipeline/seeds/vignettes.csv` (the last 17 rows).

## The candidates, checked against the text

| Candidate | Verdict |
| --- | --- |
| Parham ranch house at Cloverdale | Drawn as the house found empty (2-04), the scene the book makes of it. Before that the house is only the place Billy leaves from, and Cloverdale already has Billy and the dog |
| A calf or heifer killed by the wolf | Drawn. The first kill is reported in 1-01 and shown in 1-03, so first_seen is 1-03 |
| Echols' house hung with traps | Drawn, corrected. The traps they are after are not hung up; the book has jars of baits in the back room and a few old coyote traps hanging on the smokehouse wall, so the drawing hangs them there |
| Don Arnulfo's hut | Drawn as a low mud house (the book's word), on the plain south of Animas, not a hut |
| Billy and Boyd taking "the girl" from the two men | Drawn (2-08) |
| The horses Keno and Niño | Keno drawn alone at Bacerac (2-07). Niño is in the remuda drawing, the moment Boyd ropes him |
| The Babícora horse herd | Drawn as the remuda in the road (3-04) |
| Quijada on the road | Drawn at the crossroads where the brothers meet him (3-04) |
| Singers of the corrido | Drawn as the corridero at Temósachic (4-05), the first singer the book shows |
| Billy turned away at the recruiting office | Drawn at El Paso (4-01) |
| Ocotillo and cholla on the bootheel flats | Cholla drawn with the trapped wolf: the book's only cholla is at the trap on Cloverdale Creek (1-08). **Ocotillo dropped**: the book's one ocotillo is in the hills south of the line (1-09), and the boundary monument drawing there already has one |
| Pine forest in the high Sierra Madre | Folded into the Quijada, remuda and packhorse drawings: the book's pines are along the road up to Las Varas and the Babícora (3-04, 4-05). The Sierra Madre of J3 is madroño, oak and ilex in the book, and billy-in-rags draws those |
| Waterfowl on the Laguna de Babícora | **Moved**: the book has no waterfowl on the Babícora lake (only birds calling at dawn in 3-12). Its waterfowl are at the Buenaventura crossroads (3-14), so the drawing is there |
| Javelinas | **Dropped**: the book has no javelina or peccary |
| A vaquero roping | Folded into the remuda drawing: the roper in the book is Boyd, with the vaqueros watching (earlier that day one of the manco's riders ropes the Tom horse) |
| The empty Mormon colony at Colonia Morelos | **Moved**: the book never shows Morelos empty (1-09 has it full for the fair; 2-07 passes it at midnight), and it already has two drawings. The Mormon colony the book describes is Colonia Juárez (2-08), so the drawing is there |
| A train at Nuevo Casas Grandes | **Moved**: at Casas Grandes the book shows only the tracks and the depot. Its one train is the night train whistling for the Las Varas crossing (3-12) |
| Character vignettes: J5 Cuauhtémoc, Namiquipa, La Norteña | One, on Namiquipa to La Norteña. The Cuauhtémoc to Namiquipa leg is left empty because billy-searching, 35 km away on the San Diego to Cuauhtémoc leg, already shows this search |
| J7 Namiquipa, Temósachic, Madera | One, Billy with his packhorse, halfway from Namiquipa to Temósachic; the corridero stands at Temósachic |
| J3 El Tigre into the sierra | That leg already has billy-bow-hawk, so this one is on the next empty leg, from the Indians' country to the eastern escarpment |

## How

- **Code.** `art/vignettes/subjects_round3.py` (new) exports `SUBJECTS`. It imports `rider`, `place`, `blob`, `pine` and `cottonwood` from the Parts III and IV module and `wolf` and `juniper` from the Parts I and II module, and adds `horse()` (the Muybridge outline minus a box round the rider, done with shapely, with an optional lowered head, saddle or pack), `figure()`, `fire()`, `cholla()` and `chevrons()`. `make_vignettes.py` is not changed.
- **Data.** 17 rows at the end of `pipeline/seeds/vignettes.csv`; rebuilt `data/vignettes.geojson`, `data/parquet/vignettes.parquet` and the sprite (`site/public/sprites/`).
- **Checks.** `crossing.validate` passes, `crossing.downloads` ran, `crossing.echo_check` gives 0 shared runs (three first drafts of notes shared 8-word runs and were reworded), ruff passes on the new module, `npx tsc -b`, `npm run lint` and `npm run build` pass.
- **Spoiler leak.** `node tools/spoiler-leak.mjs http://localhost:5294/` against a fresh `VITE_DEBUG=1 npm run build` served by `vite preview`: "No spoiler leaks" at all ten reading positions (unset, none, 1-03, 1-08, 2-04, 3-08, 3-12, 4-05, 4-08, all; 846 map features, 171 panel steps).
- **Tools** (private, not committed): `private/overnight/vignettes/tools-round3/` (`fetch.py`, `preview3.py`, `rows.py`, `shots.mjs`).

## Doubtful, or for the owner

1. **Crowding.** The bootheel at zoom 9 cannot take four more drawings with labels, so echols-cabin, dead-calf, wolf-in-the-cholla and parham-house start at zoom 10, as does taking-the-girl (at zoom 9 it would sit on Paquimé).
2. **Pins shown later than their drawings.** echols-cabin (1-02) refers to the SK Bar pin, shown from 2-04; dead-calf (1-03) uses the Foster Draw place (1-01), so it is fine. Until 2-04 the cabin stands without a pin, as the Cloverdale drawings did in round 2.
3. **Where Echols' cabin is.** The book says only that it is at the SK Bar, so it stands west of the Sanders' pin.
4. **Don Arnulfo's house** is placed by the book's words (on the plain south of the town, no road to it) at a point 4 km south of Animas. The distance is a guess.
5. **The corridero reference.** The Flickr photograph is marked public domain and titled as an FSA migratory worker; its photographer is not given on the page I used. Only the pose was drawn after it.
6. **The riderless horse** is the walking Muybridge horse with the rider cut away. Lowering the head for a grazing or standing horse bends the neck, which reads at map size but is stiff close up (keno-bacerac, the remuda).
7. **Weakest at map size:** the dead calf (the ribcage reads as a carcass only at 87 px), the recruiting office's figure, and the corridero, whose head merges with his coat at 69 px.
8. **colonia-juarez** keeps its drawing at zooms 9 and 10, but its label gives way to the town's name.

## Network log

12 requests (budget 40), all HTTP 200, no 429s, User-Agent "crossing-map-research/0.1", at least 2.5 s apart. Logged with time and bytes in `private/cache/vignettes-round3/requests.log`; images in `private/overnight/vignettes/refs/round3/`, each with a row in `refs.csv`.

- Openverse searches (8, public domain and CC0 only): steam locomotive night, guitar player mexico, recruiting station, cholla cactus, cane cholla, Russell Lee guitar, adobe house New Mexico Lee, enlistment 1942 recruiting
- Images (4): White Sands NP cane cholla, the FSA guitar player, Russell Lee's adobe house at Peñasco, the 1901 PRR locomotive
