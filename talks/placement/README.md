# Placing a novel on the ground

Notes for writing or a talk on one theme: **LLMs are poor geographers from memory, but strong ones when they use the geodata and tools that already exist.** Most of this map was placed by an LLM working through a pipeline, with the owner reviewing. The examples below come from one review session, on 17 November 2026, of the she-wolf's journey (J1) through the New Mexico bootheel.

## The argument in three lines

1. Asked where a landform is, a model gives a point: the first coordinate it finds. A landform is not a point, and the book rarely means the whole of it.
2. The data to do better usually exists already, and often sits in the same record the model read (GNIS stores a draw's head beside its mouth). The model has to know to ask for it.
3. Given the tools (a gazetteer, a DEM, flow routing, a terrain classifier), the model can build, calibrate and run a reproducible method in an afternoon, citing the literature as it goes. Where it still falls short is judgement about what the words mean, and a habit of checking its answer against the ground.

## Example 1: "the head of the draw"

The book puts the calf kill "at the head of Foster Draw, in the Peloncillo Mountains". The map put the stop on GNIS's point for Foster Draw, on the flat floor of the Animas Valley.

- GNIS records a linear feature with two points: a **primary point at its mouth** and a **source point at its head**. The pipeline read the first and ignored the second.
- The head is 12.4 km west and 216 m higher, in the Peloncillos, exactly as the book says.
- The model had already sensed a problem. The site carried an open question, "How high between Clanton and Foster draws?", whose own text said the calf was killed at the head of the draw. It still left the stop at the mouth.
- The owner caught it from one word, "head", and asked what it means.

Images: `shots/j1-foster-draw-before.png`, `shots/j1-foster-draw-after.png`, `figures/j1-foster-draw.png` (the red cross is the mouth, the blue square GNIS's head).

Talking point: the error was not missing data. It was reading a name as a point.

## Example 2: Starvation Canyon, flagged and not fixed

"She works west to the head of the canyon." Same fault, same fix: GNIS's head is 6.4 km up-canyon from the mouth where the stop sat. Here the site had an open question titled **"Starvation Canyon: mouth or head?"**, with the right answer offered as the "other reading". The model identified the ambiguity, wrote it down for the reader, and chose the wrong side.

Images: `shots/j1-starvation-canyon-before.png` (the open question in the panel), `shots/j1-starvation-canyon-after.png`, `figures/j1-starvation-canyon.png`.

Talking point: an LLM can be good at noticing doubt and still default to the data's first answer. Flagging is not resolving.

## Example 3: "the high country between" (the fix that was still wrong)

The book sends her back east to the high country between Clanton and Foster draws. The original stop sat between the two draws' mouths, on the valley floor at the 9th height percentile of its surroundings.

The first fix, approved in conversation, moved it to the midpoint of the two draws' heads. That sounds right. A terrain check run afterwards flagged it: the midpoint falls in a valley, at the 42nd percentile. "High country" is a property of the ground, not of the geometry between two points.

A hybrid method found better ground: the drainage divide between the two draws' catchments, computed from the DEM, at the point nearest the two GNIS heads. It lands on a ridge at the 87th percentile, 1.6 km from the midpoint.

Images: `shots/j1-clanton-foster-before.png`, `shots/j1-clanton-foster-after.png`, `figures/j1-clanton-foster.png` (green dots: the divide, green diamond: the hybrid point, black circle and blue square: the midpoint).

Talking point: the most useful tool in the session was one that checked the answers, including the human-approved one.

## Example 4: "through its gap"

"She crosses the range and goes north through its gap." The stop was on the San Luis Mountains' GNIS point, a peak at 2,052 m. The owner guessed San Luis Pass. GNIS has San Luis Pass as a feature of class Gap, 5.9 km north. Asked for "the GNIS gap near this range on her way north", the data gives the owner's answer.

A DEM-only search for a saddle on the way found a col 5.4 km away, on a slope. Named features beat derived ones whenever they exist.

Images: `shots/j1-san-luis-before.png`, `shots/j1-san-luis-after.png`, `figures/j1-san-luis-mountains.png`.

Side note for the honest version of the talk: moving the stop exposed a drawing flaw. The Whitewater Creek leg is traced along the creek, then joined straight to the stop, and that straight stretch is drawn solid like the traced part. Fixing one point can surface the next problem.

## Example 4b: the reader's route over the quickest one

"She passes through the Animas range on her way north." The stop sat on the range's point, beside Animas Peak, 20 km north of San Luis Pass, on a peak. The owner read the line differently: up the valley on the east side of the range, then over it about halfway to the Animas Valley.

GNIS has no gap on that stretch, so this one came from the DEM, but steered by the reading. Start at the low point of the east-side valley on the halfway parallel, take the wolf's least-cost path from there to the next stop, and put the stop on the saddle nearest where the path tops the ridge. The terrain check calls it a saddle. A plain least-cost path from the pass to the valley would cross sooner, over a low ridge just north of the pass, about 40 minutes quicker for her.

Talking point: the model is good at "the easiest way". The book is not always about the easiest way, and the reader's interpretation is a legitimate input to the method. Recording it as an open question ("Where does she cross the Animas Mountains?") keeps both readings visible.

Script: `pipeline/measure/animas_crossing.py`.

## Example 5: what the DEM alone gets wrong

To test a DEM-only method, the model traced each stream up from its mouth to its head, using standard flow routing, for 159 GNIS valleys, streams and arroyos around J1, and compared each head with GNIS's.

- Median error: 3.5 km. Within 1 km: 22 %.
- But where the trace climbed the same valley as GNIS (39 of 159), 82 % were within 1 km, with a median of 0.4 km.
- So the method is right about channels and wrong about **which** channel. On a flat valley floor the mouth snaps to the biggest channel nearby, and at each fork it follows the largest catchment, which is not necessarily the named valley.

Image: `figures/calibration.png`.

Talking point: a calibration against ground truth took one script and 15 minutes. It turned "the DEM method looks plausible on two examples" into "it is right a quarter of the time, and here is why".

## Example 6: a check that knows its limits

The terrain check flagged the Animas Valley stop as "spur, 48th percentile, not a valley floor". The figure shows it is on the valley floor, 1 km from the axis. The check used a 3 km window on a valley 15 km wide. The fix is to scale the window to the landform. This is a good example of a checker raising a false alarm that a person dismisses in seconds with the image in front of them.

Image: `figures/j1-animas-valley.png`.

## Example 7: a view the ground does not allow

"From the eastern escarpment he looks east over the Bavispe's barranca to the Carretas Plain." The stop was placed from the order of events: he goes down to the river and rides north to a ford, so the escarpment went south of that ford. Nobody had asked whether the view works from there.

A viewshed asks it. Of 617 lookouts along the escarpment, every 1.5 km, 4 can see the Carretas Plain at all. The ranges east of the river stand higher than the escarpment. The stop's own stretch sees no plain of any kind. Only the high ground west of Bavispe town, 75 km north, sees the plain well, its nearest edge 56 km off. That is close to the book's "forty miles" (64 km) for a locomotive's smoke on the plain.

Talking point: two clues in the same paragraph point 75 km apart. The model can now say so with numbers and a map, instead of quietly following one clue. What to do about it is a reading of the novel, and stays with a person. A novelist's "Carretas Plain" may name the country beyond, not ground in sight.

Images: `figures/escarpment-view.png`. Method: `review/experiments/escarpment-view/README.md`.

## The method as a diagram

`docs/placement-method.md` sets out the whole placement method as a decision tree (Mermaid, rendered in `figures/placement-method-flow.png`), with each step in words and the code behind it. It is the version to show in a talk.

## From experiment to process

The next day the method became part of the pipeline (decision 0059). Each stop whose text names part of a landform has a position (23 of 171). A command produces candidates by tier and checks each one. A local review screen shows the owner every candidate on the map, with the DEM-only ones marked as review aids, and records a verdict. The build lists flagged stops that have no verdict, but never fails on one. Of the 23, 7 were flagged. None moved without a person deciding.

Talking point: the useful shape is not "the model places things". It is "the model proposes, checks and shows its working, and a person decides". The review screen took one delegated sub-task to build.

## Interface fixes from the same review

The same review pass fixed three display problems. They are not about geography, but they show the loop of looking at screenshots, naming what is wrong, and fixing it:

- The key's grouped-stops marker overlapped its label: `shots/key-before.png`, `shots/key-after.png`.
- The map credits ran under the title cartouche when opened: `shots/attribution-1400-key-open-before.png`, `shots/attribution-1400-key-open-after.png` (and the 900 px pair).
- All map text was 20 % too small: `shots/type-bootheel-before.png`, `shots/type-bootheel-after.png`.

## Ideas to develop

- **Gazetteer literacy.** Most of the wins came from knowing what fields a gazetteer has (GNIS source points, feature classes like Gap). A model that knows the schema of the standard datasets is worth more than one that remembers coordinates.
- **Words that name parts of landforms.** Head, mouth, foot, crest, gap, saddle, floor, rim, "between", "the high country". A list of these, each tied to a data rule and a terrain test, is a small, publishable piece of method.
- **Tiers, then a check.** Named point, then named line, then DEM, then a geomorphon check on whatever was chosen. Reproducible, citable, and honest about which tier answered.
- **Calibrate before you trust.** The 159-feature test cost minutes and changed the recommendation.
- **The human's role moved, not vanished.** The owner did not compute anything. They noticed that a word was being misread and asked what it meant. The model did the rest, including finding a flaw in the owner's own approved fix.
- **Methods the model wrote from the literature in one sitting:** priority-flood depression filling (Barnes et al. 2014), D8 flow directions (O'Callaghan and Mark 1984), channel-head support areas (Montgomery and Dietrich 1988), geomorphons (Jasiewicz and Stepinski 2013), plus least-cost paths with Tobler's hiking function from earlier work on this map.
- **Where it is still weak:** choosing the first coordinate, not checking the ground, and resolving a flagged doubt the easy way. All three are habits, which suggests they can be taught or built into the pipeline.

## Files

- `shots/`: site screenshots, each view `-before` and `-after` the fixes (2x, 1400 x 900 desktop). Made by `tools/placement-shots.mjs`.
- `figures/`: hillshade maps of each stop with every candidate point, and the calibration histogram, from `crossing.landform_points_images`. Method and numbers: `review/experiments/landform-points/README.md`.
- Decisions: `docs/decisions/0056-heads-and-gaps-in-j1.md` (the placements), `0055-map-text-a-fifth-larger.md` (the text and credits).
