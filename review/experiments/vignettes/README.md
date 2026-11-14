# Experiment: research-based vignettes (13 November 2026)

**Adopted on 14 November 2026, two inks, in the mountain glyphs' pen.** The owner dropped the accent red and asked for glyph variant B's pen (wobble, outline weight, hatching), so `art/vignettes/ink.py` now draws every line with `art/pen.py`. The drawing code is `art/vignettes/make_vignettes.py`, the traced outlines are in `art/vignettes/traced/`, labels and credits are in `pipeline/seeds/vignettes.csv`, and the site draws the labels and lists the credits. The other questions below keep this packet's defaults for now: present size (not 1.3x), the labels as written, the traced Trinity cloud with rays, Paquimé closer to today's walls, the San Diego and pit renames (done), the bent wolf outline for the dog, and the two drawings after CC BY-SA 3.0 images treated as derivatives (credited, and shared under CC BY-SA 3.0). The trial's images, test sprites and tools (including the tracing script, `trace.py`) are in `private/parked/vignettes-experiment/`.

**Status: experiment, not rolled out.** Nothing in `art/`, `data/`, `pipeline/seeds/`, `site/` or `site/public/sprites/` has changed. The new drawings, a test sprite, the screenshots and the tools are all in this folder. The references are in `private/overnight/vignettes/refs/` (git-ignored), with `refs.csv`.

The task was to replace the 13 placeholder vignettes (plan section 10, stage-6 packet) with drawings that look roughly as the book describes each subject, informed by reference images, each with a short label, in a style that takes its cue from "The Trail of Blood Meridian" map.

## What to look at

| File | What it shows |
| --- | --- |
| [contact-sheet-1.png](contact-sheet-1.png), [contact-sheet-2.png](contact-sheet-2.png) | Each subject: the placeholder, the new drawing, the drawing at map size (53 px, at 1x and 2x), the accent-ink version where there is one, the label, how it was made, the credit and a paraphrase of the book |
| `shots/<view>-before.png` and `shots/<view>-new.png` | The real site (dev server, port 5185) with the current sprite, then with the test sprite and labels. Views: `part-i-border` z9, `casas-grandes` z9, `las-varas-babicora` z9, `black-range-trinity` z7.6, `paquime-close` z11 |
| `shots/las-varas-babicora-accent.png` | The accent-ink version (red Waco, red opera wagon) |
| `shots/part-i-border-large.png`, `shots/black-range-trinity-large.png` | The same drawings at 1.3 times the present icon size |
| `svg/` | The 13 new SVGs, named as now (`vignette-<id>.svg`), on the 96 x 96 grid, two inks only |
| `svg-accent/` | The same set with the optional third ink (only two files differ) |
| `sprite-svg/`, `sprite-svg-accent/` | Test sprites: the unchanged mountain glyphs plus the new vignettes, built with spreet |

Start with the contact sheets, then `shots/casas-grandes-new.png` and `shots/las-varas-babicora-new.png`.

## How the drawings were made

The source order in plan section 10: traced public-domain sources, then fresh drawings, image generation only as a sketch. No image generation was used.

1. **Book.** For each subject I read the episode in `private/book/text/` and wrote a paraphrase in our own words (under 25 words, in `tools/meta.py` and on the contact sheets). The 8-word echo check on `tools/` gives 0 shared runs, and a 5-word check on `meta.py` also gives 0.
2. **References.** 27 images were downloaded into `private/overnight/vignettes/refs/` from Wikimedia Commons, Flickr (US Fish and Wildlife Service, NPS, California Historical Society, Gary Lee Todd's CC0 set) and the National Gallery of Art via Openverse. Each one has its URL, author, date, licence, a traceable flag and what it was used for in `refs.csv`. Three look-only sources are listed without a file. Only public-domain or CC0 images were traced.
3. **Tracing** (`tools/trace.py`): rembg removes the background (or a plain threshold for the Trinity cloud against its dark sky), potrace turns the mask into an outline, and svgelements scales it onto the 96 grid. Darker tones inside the subject can be traced as separate regions for hatching. `tools/trace_all.sh` has the two traces the set uses.
4. **Drawing** (`tools/ink.py`, `tools/make_set.py`): one pen-and-ink style for all 13. Drawings without a usable trace are drawn in SVG by hand, with proportions taken from the references.

### The style

- Ink `#2b2118` on paper `#e4ddcc`, as `art/build_sprite.py` expects. The only fill is paper, used to knock the map out behind the drawing. A 3.2-unit paper halo round every stroke lets the drawing read over the relief tint and the hachures.
- Line weights on the 96 grid: outline 2.0, detail 1.2, hatching 0.8 at a 2.8 pitch, cross-hatching for the darkest parts (doorways, the blood-black boards of the pit). At the zoom 9 size (0.55) the outline is about 1.1 px.
- Light from the north-west, as on the mountain glyphs. Shade is a hatched band on each shape's south-east side (`edge_shade`: the shape minus itself moved towards the light, done with an SVG mask), so the whole set has one light.
- From the Trail of Blood Meridian map: small, dark, monochrome drawings that sit beside their place, each with a short italic caption under it. Its colour work is sepia on parchment with red kept for the route. Our map already has a near-identical scheme, and Billy's route is already a dark red (`routeBilly #6e1f1c`). For that reason the main set stays two-ink.
- **Accent proposal (optional):** a faded brick red, `#9c4a2f`, with a pale wash `#c98b6f` / `#d7b9a3`, used only where the book names red: the "big red Waco" and the opera wagons' weathered red paint. It is a lighter, browner red than Billy's route, so the two should not be confused, and two drawings out of 13 keep it rare. See `shots/las-varas-babicora-accent.png`. If you would rather not add a colour, nothing else depends on it.
- **Labels** render in the map's own italic (IM Fell English italic, `IMFeENit28P`), ink with a paper halo, under the drawing, through the existing `vignette` layer (`text-field`, `text-optional: true`, so a drawing still shows when its label collides).

## Per subject

"How" is: traced (the outline comes from a public-domain photograph), mixed (built from a traced outline), or drawn (by hand, after the references).

| Vignette | Label | How | What it looked like around 1940, and what changed from the placeholder |
| --- | --- | --- | --- |
| she-wolf | She-wolf, out of Sonora | traced | Mexican grey wolf (USFWS photograph of a trotting wolf, public domain). The tone trace gives the dark saddle along the back. Reads at 53 px |
| steel-trap | Newhouse No. 4½ wolf trap | drawn | The book names the trap: a Newhouse No. 4½, a double long-spring wolf trap with a forked chain and a drag. Drawn from above with both springs, the open jaws and the pan, the chain and the two-pronged drag. The 1919 Newhouse advertisement (public domain) was too small to trace |
| obelisk | Boundary monument, 1890s line | drawn | The 1892-94 resurvey set up the obelisks along 31°20′ N, mostly of cast iron, some of masonry. The book calls them concrete and white. Drawn as a pale obelisk on a stepped base, after D. H. Payne's photograph of Monument 40 (NARA 519682, public domain). The book's red hills are behind and an ocotillo stands beside it for scale |
| hacienda-pit | Cockpit at the hacienda fair | mixed | The book's pit is a round cockpit about twenty feet across, inside the hacienda's granary: a low board palisade dark with old blood, an iron pipe driven into the middle, and stands on poles. **The placeholder's gate is gone**: the book does not make the gate the scene. The wolf is the traced she-wolf, small, chained to the stake |
| ruined-church | Ruined adobe church, upper Bavispe | drawn | A huge adobe church with its roof timbers fallen in. Drawn after the roofless walls of Quarai (CC BY 2.0) and the broken front of San Juan Capistrano about 1900 (public domain): a tall west front with an arched door, a breached nave and fallen beams |
| paquime | Paquimé, adobe ruins, 1940s | drawn | Worn mud walls in ranks, a T-shaped doorway, the rising moon and a squatter's fire, all from the book. After Gary Lee Todd's and DiSchamelrider's CC0 photographs. **Caveat:** Paquimé was excavated and consolidated by Di Peso's expedition in 1958-61, so in the 1940s it was more mound and broken wall than the crisp walls in today's photographs. The drawing keeps the tops rounded and broken, but it is closer to today than to 1940 |
| san-diego-gate | Hacienda de San Diego, Terrazas house | drawn | **The book describes the house front, not a gate:** plaster walls quoined with sandstone, a terracotta parapet, tall shuttered windows, and three stone arches with the hacienda's name carved in an arch over the initials L. T. The drawing follows that. No reusable photograph was found (Commons and Openverse have none, and the web pages that do are all rights reserved), so this is the drawing least checked against the real building |
| opera-caravan | Travelling opera wagons, 1940s | drawn | Two gaudy box wagons with curved roofs, a band of faded gilt lettering, painted panels, and wash hung between them. The seed note has them halted in a field, so the shafts are down and there is no mule (no clean public-domain mule photograph was found, and a hand-drawn mule looked like a goat) |
| blind-man | Blind man of the revolution | drawn | Barefoot, walking the rutted road with his stick, wildflowers by the road (the book has rain and flowers on that walk). Hat and coat after a Fortepan photograph of a peasant with a cane (CC BY-SA 3.0). Tracing the seated figure failed, see below |
| red-plane | Red Waco cabin biplane, 1930s | drawn | The book says a big red Waco. Waco's cabin biplanes (YKS, UKC, UEC) were the 1930s ranch and charter type. Side view with staggered wings, a radial cowling, a dotted circling path and the trees it comes down among. After RuthAS's YKS-6 (CC BY 3.0) and Armchair Aviator's UEC (CC BY 2.0) |
| gypsy-plane | Gypsies' airplane, lost in 1915 | drawn | The gypsy dates the wreck to 1915, so it is a Curtiss JN-type biplane (the US Army's 1st Aero Squadron flew JN-3s over Chihuahua in 1916). Drawn as a bare frame of longerons and diagonals, with one shred of fabric, wings roped along the side and the rudder, on a plank float with truck wheels, pulled by a yoke of oxen. Fuselage after Kaboldy's JN-4B 3-view (CC BY-SA 3.0), oxen after Giovanni Fattori's etching (CC0) |
| crippled-dog | Old dog at the roadside ruin | mixed | The book's dog is old, yellow, grey in the muzzle, crippled behind, with its head askew. It is the traced wolf outline, smaller and bent: the hindquarters sink and the head hangs low and turned. Behind it is the ruin's roofless wall and the door open on the rain |
| trinity-cloud | Trinity test, 16 July 1945 | traced | The cap is traced from the Trinity photograph (US government, public domain; Flickr copy by CTBTO), with the column, the dust skirt and short rays of light drawn on. **The book has only a light, no cloud.** The rays nod to that. See question 4 |

Credits as they would appear on the site are in `tools/meta.py` (`credit`), and on the contact sheets.

## Numbers

- 13 drawings: 2 traced, 2 mixed (built from the traced wolf), 9 drawn by hand after references.
- SVGs: 341 KB in total, 13-66 KB each. Most of that is the hatching, because each hatch draws the full set of strokes and clips them. Trimming the strokes to each region's box would cut it a lot (not done).
- Sprite: `glyphs.png` 142 to 172 KB (+30 KB), `glyphs@2x.png` 252 to 311 KB (+59 KB). The JSON is unchanged in size.
- Screenshots, with every vignette in view placed in both runs:
  - Part I border, zoom 9: obelisk, hacienda pit, she-wolf
  - Casas Grandes, zoom 9: gypsy plane, she-wolf, San Diego, Paquimé, blind man
  - Las Varas, zoom 9: blind man, red plane, opera
  - Black Range and Trinity, zoom 7.6: crippled dog, Trinity
  - Paquimé, zoom 11: Paquimé
  - At 1.3x, the Part I view loses the obelisk to a collision. The other views keep the same drawings.

## What works and what does not

- **Works:** rembg + potrace for an animal in profile against a plain background (the wolf), and a threshold trace for a bright cloud on a dark sky. Hand-drawn SVG for buildings and machines, with shade from `edge_shade`, reads clearly at 53 px. One light direction and one set of line weights make the 13 look like a set. The labels read well in IM Fell italic and do not crowd the map at zoom 9.
- **Failed and dropped:**
  - Tracing the Waco from a three-quarter photo gave a blob. So did the seated man in the Fortepan photo: dark clothes against a pale wall merge into one shape, even with rembg combined with a darkness threshold.
  - The oxen in Fattori's etching merged with the cart, and the yellow dog lying down read as a pig at 53 px.
  - Tone hatching traced from photographs gives ragged patches unless it is heavily blurred, so it is kept only for the wolf.
  - The first Trinity trace read as a tree. Tracing at 160 px for a smoother cap, a flared column and no inner curls fixed it.
- **Research gaps:** Wikimedia Commons' API returned 429 several times with the generic User-Agent, and loc.gov returned 403, so no HABS drawings were used. There is no reusable photograph of the Hacienda de San Diego. The 1898 Boundary Commission report plates were not reached. vtracer is available (`uv tool run --from vtracer`) but was not needed, because every trace was a two-tone mask, which is what potrace does well.
- **At zoom 7 to 7.6** the smaller drawings (the dog, the Trinity cloud) are about 45 px across and hard to read. The 1.3x shots help, at the cost of more collisions.

## Licences

- **Traced** (the derived outline is in our SVGs): USFWS wolf photograph and the Trinity photograph, both US government works, public domain. Credit is not required, but it is given.
- **Drawn after** CC BY and CC BY-SA photographs (Waco, Quarai, JN-4B 3-view, Fortepan): proportions and details were read off them, but nothing was traced. Whether that makes a derivative is a judgement. I have credited them all, and if you want to be strict, the gypsy plane and the blind man would carry CC BY-SA 3.0. The present seed data gives every vignette `source_licence: CC BY 4.0`.
- **Look only:** the watermarked Waco HKS-7 (its Commons licence is doubtful) and the hacienda pages.
- The Trail of Blood Meridian map was used only as a style reference. Nothing was traced from it.

## What rolling out would change

1. **Art.** Move `tools/ink.py` and `tools/make_set.py` into `art/vignettes/`. Either replace `make_vignettes.py`, or keep its name and its `build_sprite()` call at the end. Move the two traced JSON files from `private/overnight/vignettes/traced/` into `art/vignettes/traced/`: they hold only our traced geometry, from public-domain photographs, so they can be public. `trace.py` is only needed to re-trace. The build needs `svgelements`, the trace also needs `pillow`, `numpy` and `rembg`: add them to a dev group, or keep `uv run --with`. Command: `uv run --no-project --with svgelements python art/vignettes/make_set.py`.
2. **Sprite.** `art/build_sprite.py` needs no change: it reads `art/vignettes/svg/`. The sprite grows by about 30 KB at 1x and 59 KB at 2x.
3. **Seed and data.**
   - Add `label` and `credit` columns to `pipeline/seeds/vignettes.csv` (values in `tools/meta.py`). `pipeline/src/crossing/build_vignettes.py` passes them into `data/vignettes.geojson`, and `data/schema/story-layer.schema.json` gets the two properties.
   - Reword the `name` and `note` of `san-diego-gate` ("gate" becomes the house front) and of `hacienda-pit` (no gate).
   - The ids can stay. Renaming `san-diego-gate` would also rename the sprite image and the feature id.
   - Then run `uv run --project pipeline python -m crossing.build_vignettes`.
4. **Site.**
   - In `site/src/map/relief.ts`, function `vignettes()`, add to the `vignette` layer's layout: `text-field ['get','label']`, `text-font [fonts.italic]`, `text-size` 10 to 12 by zoom, `text-anchor 'top'`, `text-offset` 1.9 to 2.8 em by zoom, `text-max-width 9`, `text-optional true`. Add `text-color p.ink`, `text-halo-color p.paper` and `text-halo-width 1.2` to its paint. The exact values are in `tools/shots.mjs`.
   - Remove "(placeholders for now)" from its comment.
   - The Credits page needs a vignettes section built from the `credit` property.
   - If you take the accent, add the colour to `tokens.ts` for the lamplight theme check. It lives inside the sprite, so only `art/` needs it.
5. **Checks:**
   - `uv run --project pipeline python -m crossing.echo_check` (the new text gives 0 shared runs)
   - `node tools/spoiler-leak.mjs` (labels are on the same features, so the `first_seen` filter covers them)
   - `node tools/vignette-sheet.mjs` for the stage-6 views
   - Update `review/stage-6/vignettes/README.md`, which still says "placeholders"

To rebuild this packet: `tools/trace_all.sh`, then `uv run --no-project --with svgelements python -I review/experiments/vignettes/tools/make_set.py` (add `--accent` for `svg-accent/`). Then build the two test sprites with spreet: the glyph SVGs and the set in one scratch folder, as `art/build_sprite.py` does, writing to `sprite-svg/glyphs`. Then run `tools/contact_sheet.py`, and `node review/experiments/vignettes/tools/shots.mjs` with the site on port 5185.

## Questions for the owner

1. **Accent ink.** Keep the set two-ink, or use the faded red (`#9c4a2f`) for the Waco and the opera wagons only?
2. **Size.** The drawings now carry more detail than the placeholders. Go to 1.3 times the present icon size (see the `-large` shots), and accept a few more lost collisions?
3. **Labels.** Are the wording and the dates right? In particular, "Paquimé, adobe ruins, 1940s" (your example), "Travelling opera wagons, 1940s", "Blind man of the revolution", and "Gypsies' airplane, lost in 1915" (the date is the gypsy's own story).
4. **Trinity.** The book has a light, not a cloud. Keep the traced cloud with rays, or draw a burst of light over the Jornada horizon instead (closer to the text, harder to read at 45 px)?
5. **Paquimé in 1940.** Draw it more ruined and mound-like, true to its state before the 1958-61 excavation, or keep today's recognisable walls and T doorway?
6. **San Diego and the pit.** The book gives a house front with three arches and a cockpit inside a granary, not gates. Rename the two vignettes in the seed (ids could stay)?
7. **The dog.** A bent wolf outline stands in for the old yellow dog. Good enough, or should it be a fresh drawing from a public-domain dog photograph in profile?
8. **CC BY-SA "drawn after".** Treat the hand drawings made after CC BY-SA photographs as derivatives (credit and CC BY-SA 3.0 on two drawings), or as new drawings that are only credited?
