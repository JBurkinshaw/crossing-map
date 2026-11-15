# Stage 9: more vignettes, Parts I and II (J1, J2, J3)

Twelve new vignettes for the first two Parts of the book: the she-wolf's journey north (J1), Billy taking her south (J2), and his wandering in the Sierra Madre and ride home (J3). Five are character drawings (Billy, Bird, the wolf, the dog). With the 13 drawings already on the map, the set is now 25; the Parts III and IV agent adds its own.

## What to look at

All images are in `private/review/stage-9/vignettes-parts-1-2/` (git ignores them here).

| File | What it shows |
| --- | --- |
| `contact-sheet.png` | Each new drawing at 300 px, and at 52, 69 and 87 px (the map's sizes at zooms 6, 9 and 12) on the Mexico tint |
| `bootheel-z8.png`, `bootheel-z9.png`, `animas-z10.png` | The bootheel: wolves and antelope, Billy and the dog, with the trap and obelisk |
| `border-south-z9.png` | South of the line: the night camp, the wolf on the rope, the fair cart, the ford |
| `morelos-pilares-z9.png`, `morelos-pilares-z10.png` | Colonia Morelos to El Tigre: the cart, the pit, the ford, the dead wolf carried, the cairn, El Tigre, the bow |
| `sierra-z8.png`, `upper-bavispe-z9.png`, `bavispe-z11.png` | The Sierra and the upper Bavispe: El Tigre, the bow, Bavispe church, the escarpment road |

The site was run with `cd site && npm run dev -- --port 5291`, reading progress "all", and shot with `private/overnight/vignettes/tools-parts-1-2/shots.mjs`.

## The new vignettes

"Traced" means the outline comes from a public-domain photograph; "drawn" means by hand after the references. Zooms are `min_zoom` to `max_zoom`.

| Id | Subject | Why it matters (paraphrase) | First seen | Pin, side | Zooms | Label | Source and licence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wolves-antelope | Wolves running antelope in the snow, by moonlight | The book opens with the boy creeping out on a winter night to watch seven wolves harry the antelope on the snow | 1-01 | j1-animas-valley, nw | 8–12 | Wolves running antelope in the snow | Drawn; wolves are the traced she-wolf (USFWS, PD); pronghorn after BLM Utah and Great Sand Dunes NP photographs (PD) |
| billy-and-the-dog | Billy on Bird; the dog at the stockgate | Billy rides out alone after the wolf and the family dog watches him go; the dog is gone when he comes home | 1-04 | place-cloverdale, e | 8–12 | (none) | Rider traced from Muybridge, *Annie G. walking, saddled*, 1887 (PD); dog is the she-wolf trace, smaller |
| wolf-on-the-rope | Billy leading the muzzled wolf on the rope, through lechuguilla | The long ride south with the wolf hobbling behind | 1-09 | own point on J2 (Cajón Bonito to the Cabellera, halfway), e | 9–12 | (none) | Muybridge trace (PD) and the she-wolf trace (PD); lechuguilla drawn |
| wolf-by-the-fire | Billy wrapped in his blanket by the fire, the wolf beside him | After the turkey they share, he sits with her through the night | 1-09 | j2-cajon-bonito, w | 8–12 | Night camp, the wolf beside him | Drawn; wolf is the she-wolf trace, bent (PD) |
| wolf-ford | Billy chest deep holding the wolf's head above the river | She nearly drowns in the Bavispe ford, just before the deputies take her | 1-09 | j2-colonia-oaxaca, e | 8–12 | Fording the Bavispe | Drawn from the book; head after the USFWS wolf photographs (PD) |
| wolf-cart | The sheeted cart in which the wolf is shown for ten centavos | Billy finds her chained in the straw at the fair in the old Mormon town | 1-09 | j2-colonia-morelos, ne | 9–12 | The wolf shown at the fair | Drawn from the book |
| carrying-the-wolf | Billy riding with the dead wolf wrapped in a sheet across the saddle bow | The night ride from the hacienda to the Pilares, the end of Part I | 1-10 | own point on J2 (hacienda to the Pilares, halfway), e | 10–12 | Carrying her into the Pilares | Muybridge trace (PD); bundle and mountains drawn |
| wolf-cairn | A long low cairn of scree on a high pass | Where he buries her and the unborn pups, the first lines of Part II | 2-01 | j3-wolfs-grave, e | 9–12 | The wolf's grave, a high pass | Drawn from the book |
| billy-bow-hawk | Billy on Bird drawing a bow; the hawk with the arrow in it | Weeks alone in the high country with a holly bow and cane arrows | 2-01 | own point on J3 (El Tigre into the sierras, halfway), w | 9–12 | Holly bow, cane arrow | Muybridge trace (PD); bow, arm and hawk drawn (USFWS hawk photograph looked at only) |
| el-tigre | Jacales of sticks and mud on a slope, a small headframe above | He rides in starving and a woman feeds him | 2-01 | j3-el-tigre, sw | 8–12 | El Tigre, a mining town | Drawn after a 1940 US government photograph of a Yaqui jacal, Cortaro Farms, Arizona (NARA 522189, PD) |
| escarpment-road | Switchbacks down a granite face, junipers on the rim | The old wagon road down the eastern escarpment to the Bavispe | 2-01 | j3-eastern-escarpment, w | 9–12 | Wagon road down the escarpment | Drawn from the book |
| bavispe-church | San Miguel at Bavispe, a cypress and the meat-seller's cart | He rides through the plaza on his way home; the hermit's tale has the town ruined in 1887 | 2-03 | j3-bavispe, e | 8–12 | San Miguel, Bavispe | Drawn after LIMO 5's photograph (CC BY-SA 4.0); the drawing is shared under CC BY-SA 4.0 |

The `note`, `credit` and `reasoning` of each are in `pipeline/seeds/vignettes.csv` (the last 12 rows).

## How

- **Book.** Read Parts I and II in `private/book/text/` (1-01 to 2-06). Notes are in our own words. The echo check gives 0 shared runs.
- **Code.** `art/vignettes/subjects_parts_1_2.py` (new) exports `SUBJECTS`. Helpers in it: `rider()` (the traced horse and rider with a drawn hat), `wolf()` (the traced she-wolf, scaled, mirrored or bent), `juniper()`, `lechuguilla()`, `pronghorn()`. `make_vignettes.py` is not changed.
- **Traced outline.** `art/vignettes/traced/billy-on-bird.json`: the Muybridge plate traced with `private/parked/vignettes-experiment/tools/trace.py --mask rembg --flip --box 4,6,92,90 --tones 0.3`.
- **Data.** 12 rows at the end of `pipeline/seeds/vignettes.csv`; rebuilt `data/vignettes.geojson`, `data/parquet/vignettes.parquet` and the sprite.
- **Checks.** `crossing.validate` passes, `crossing.downloads` ran, `crossing.echo_check` gives 0 shared runs, ruff passes on the new module.
- **Tools** (private, not committed): `private/overnight/vignettes/tools-parts-1-2/` (`preview.py` for contact sheets, `shots.mjs`, `rows.py` and `refs_rows.py`, which added the seed and refs rows).

## Placement

- Character drawings without a place of their own (wolf-on-the-rope, carrying-the-wolf, billy-bow-hawk) have their own `lon`, `lat` on the route line halfway along a leg, with `ref` set to a stop of that leg.
- At zoom 8 the Colonia Morelos to El Tigre corridor was crowded (pit, cart, cairn, El Tigre, bow, carried wolf). So the cart, the cairn, the rope, the bow and the escarpment road start at zoom 9, and the carried wolf at zoom 10.
- wolves-antelope is on the `nw` side: on `n` its label fell on the stop's pin.
- In the z9 view south of the border, the cart's caption gives way to the Colonia Morelos and Ojito names. The drawing still shows.

## Doubtful, or for the owner

1. **Pins shown later than their drawings.** wolves-antelope (1-01) stands at the Animas Valley stop, shown from 1-04. billy-and-the-dog (1-04) stands at Cloverdale, shown from 1-05. The Parham house has no pin before 2-04, so until then these two drawings stand without one.
2. **Bird in Part II.** The brief suggested Niño for Part II. The text has Billy on Bird throughout J2 and J3 (Bird is named in 1-10 and again at 2-07), so every rider is Bird.
3. **Bavispe church.** It is drawn as it stands today: the white Gothic Revival tower from a 2020 photograph. I could not confirm how it looked in 1940. It is CC BY-SA 4.0, credited and shared alike, following the rule for the gypsy plane and the blind man.
4. **El Tigre.** The book has only huts of mud and sticks. The real mine had closed in 1938. A small headframe and spoil stand for the mine.
5. **Dropped:** a she-wolf howling on a rock above the Animas plains (1-04). Bending the traced wolf into a howl did not read, and the PD howl photograph is a head only.
6. **Weakest drawings at map size:** the ford (Billy is a simple bust) and the night camp (the wolf sits close to the flames). Both read as their subject at 69 px, but deserve a second pass.
7. **Sprite.** It is rebuilt here with these 12 drawings only. When merging with the Parts III and IV branch, rerun `make_vignettes` so that both sets are in it.

## Network log

19 requests (budget 60). One returned 400: the Commons thumbnail URL. All other requests returned 200. No 429s. All requests used the User-Agent "crossing-map-research/0.1" and were spaced at least 2.2 s apart. They are logged with time and bytes in `private/cache/vignettes-parts-1-2/requests.log`. Images are in `private/overnight/vignettes/refs/`, and each has a row in `refs.csv`. The Muybridge plate was already fetched by the Parts III and IV agent and reused without a request.

- Openverse searches (10): wolf howling, pronghorn running, red-tailed hawk flight, ranch dog standing, Bavispe, El Tigre Sonora, wolf swimming, dog standing side, jacal mexico, carreta oxcart mexico
- Commons API searches (2): El Tigre mine, jacal photograph
- Images (7): USFWS red wolf howl, two pronghorn (BLM Utah, Great Sand Dunes NP), USFWS red-tailed hawk, San Miguel Bavispe (the 400 thumbnail, then the full file), NARA 522189 jacal
