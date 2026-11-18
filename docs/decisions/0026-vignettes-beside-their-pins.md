# 0026. Vignettes beside their pins

Status: accepted (2026-11-14); the upper zoom bound (`max_zoom`) dropped on 2026-11-16, since a drawing beside its pin needs none; amended 2026-11-16: each side and first zoom chosen by script, clear of the stops and route lines, and the drawings of other journeys lighter (below); the wait for a closer zoom capped at one step the same day (below), and on 2026-11-17 every drawing at full strength and none before its pin (below). Amends design section 10's placement rules. Drawn in the Raised view too, from raised copies, by 0039.
Phase: P1

## Context

Design section 10 placed each vignette in empty country near what it stands for, offset 11 to 20 km (the she-wolf 101 km), with a hairline leader for real located sites. Readers took the drawings as far from their places. The owner asked for them as close to their places as possible, with no leader lines, and a note in the key that their positions are approximate.

## Decision

- Each vignette's point is the stop or place it stands for (the seed's `ref`); only the Trinity cloud keeps its own position, the Trinity Site, which is not one of the book's places.
- The drawing is set beside the point on a `side` (one of eight, taken from where each drawing sat before) with a 16 px gap at the drawing's scale, by `icon-anchor` and `icon-offset`. It stays next to its pin at every zoom and never covers it. Its label sits under it.
- The drawing may sit under other labels, which draw over it, so every drawing shows in its zoom range and hides no name. Its caption is its own layer at the top of the label stack: it is placed first, and other labels make room for it.
- No leader lines. The key says a drawing is beside where its scene happens and its position is approximate.

## Amendment, 2026-11-16: sides and zooms chosen clear of the story

The sides taken from the old positions put many drawings on the stops and route lines they stand beside, worst where journeys meet: Casas Grandes, San Diego, Colonia Morelos, Cloverdale and the Peloncillos. Every drawing stays on the map; three rules keep it off the story.

- **The side is chosen by script.** `crossing.build_vignettes` tries all eight sides of each drawing, in `priority` order, and measures what the drawing and its caption cover on screen at its `min_zoom`: the stop markers (22 px) and route lines of all seven journeys, the pins of other places, and the drawings already placed. The sizes, anchor and gap are those of `site/src/map/relief.ts`, in Web Mercator pixels; caption widths are estimates. Clashes are ranked: covering another drawing is worst, as the two then read as neither; then a stop marker; then more route line than the drawing's own width (one line passing across it is accepted, since every drawing on a journey has its line near). Within a rank the score is the route line covered in pixels plus 40 for each stop or drawing and 20 for each place pin. A tie keeps the side nearest the seed's `side`.
- **The busiest drawings wait for a closer zoom.** If every side still clashes at the seed's `min_zoom`, the script tries each closer zoom up to 12 and shows the drawing from the first where some side is clear, or failing that off every stop. A drawing as crowded at every zoom keeps its zoom: waiting would not help. Each published `reasoning` says which side it took, why, and from which zoom.
- **Drawings of other journeys are lighter.** Each vignette has a `journey`: its stop's, or for a place its first stop's in reading order (the Trinity cloud's is J7, from the waystation). The drawings of the journey in focus show at full strength, the others at 60%, drawing and caption, as the route lines of other journeys are lighter.

`pipeline/measure/vignette_clashes.py` counts what the drawings cover. At each drawing's own first zoom, before and after:

| | Before | After |
| --- | --- | --- |
| Drawings that clash (a stop, or more than their width of route line) | 36 of 54 | 7 of 54 |
| Drawings on a stop marker | 26 | 1 (the fair at Colonia Morelos) |
| Stop markers covered | 85 | 3 |
| Route line covered | 7,780 px | 2,709 px |
| Pairs of drawings on each other | 7 | 0 |

At zoom 10, the 54 drawings before covered 17 stop markers and 6,822 px of route line, with 31 clashing; the 42 shown at zoom 10 after cover 6 stop markers and 2,300 px, with 9 clashing. These are the numbers before the one-step cap below, which the site now publishes. 36 drawings changed side and 28 wait for a closer zoom: most by one step, the steel trap, the wolves running antelope, the cottonwood camp, Boyd's grave, Quijada, the remuda, the rider in the rain and others to 11, and the red plane, the corriente steers and Keno at Bacerac to 12. The she-wolf, which was the one drawing at zoom 6, now shows from 7.

The seven drawings still clashing stand where many stops and lines meet (Paquimé, the San Diego house front, the opera caravan, the wolf's cart at Colonia Morelos, the calf at Foster Draw, the night train at Las Varas and the waterfowl at Buenaventura): every side and every zoom up to 12 is crowded, and each takes the side that covers least.

## Amendment, 2026-11-16: wait at most one zoom step

Waiting up to zoom 12 kept twelve drawings off the map until zoom 11 or 12, and 28 in all past their seed's zoom: readers who did not zoom in never saw them. The owner chose to keep the drawings in view for context, at the cost of more of them touching a route line.

- **A drawing waits at most one zoom step** past its seed's `min_zoom` (`MAX_RISE` in `crossing.build_vignettes`). If it would be clear only at a closer zoom, it shows from that one step and takes its clearest side there, and its `reasoning` says it is still crowded.
- The seed's `side_fixed` column, which no row used, is gone: every side is chosen by the script.

The same measure at each drawing's own first zoom, for the seed's sides, the uncapped script above and the one-step cap:

| | Seed sides | Uncapped | One-step cap (published) |
| --- | --- | --- | --- |
| Drawings that clash | 36 of 54 | 7 of 54 | 19 of 54 |
| Drawings on a stop marker | 26 | 1 | 5 |
| Stop markers covered | 85 | 3 | 7 |
| Route line covered | 7,780 px | 2,709 px | 3,967 px |
| Pairs of drawings on each other | 7 | 0 | 0 |

At zoom 10, 53 drawings show with the cap (42 uncapped): they cover 10 stop markers and 3,441 px of route line, and 20 clash. Against the seed, 34 drawings change side and 27 wait one zoom step; none waits longer. The she-wolf still shows from 7, and Boyd riding in for the girl (seeded at 10) from 11. Most of the twelve extra clashes are one route line run along the drawing's edge (the steel trap, Boyd's grave, the cottonwood camp, the rider in the rain); the drawings that now touch a stop marker are the red plane, the wolves running antelope, Billy and the dog, Quijada and the wolf's cart.

## Amendment, 2026-11-17: full strength, and never before the pin

The owner found the drawings of other journeys, at 60%, read as greyed out, and asked for every drawing at full strength, shown only once the reader has come far enough that it gives nothing away.

- **Every drawing is at full strength**, drawing and caption, whichever journey is in focus. The route lines of other journeys stay lighter.
- **A drawing shows from the later of its scene's episode and its pin's** (`shown_from` in `crossing.build_vignettes`). Its `first_seen` is that episode, and its `episode` stays the scene's. A drawing beside a pin the reader has not reached would say where the story goes: Echols' cabin, from 1-02, stood beside the SK Bar pin, which the reader meets in 2-05. Four drawings wait: Echols' cabin to 2-05, the wolves running antelope (1-01) and the steel trap (1-03) to 1-04, and Billy and the dog to 1-05. Each one's `reasoning` says so. `crossing.validate` fails if a drawing shows before its pin.

## Alternatives

- **Geographic offsets a few kilometres out.** Close at one zoom, far at another.
- **Keeping empty-country anchors with more leaders.** Readers still read the drawing's place as the scene's place.

## Consequences

Drawings now crowd the busiest towns (Casas Grandes, San Diego) and can hide a place name under a drawing's paper; the place labels stay on top. The seed's `lon` and `lat` hold a position only for a subject that is not a stop or place.

Since the amendment, the side and first zoom of a drawing can change when a stop or a route line near it moves; the build prints each drawing whose side or zoom differs from its seed. A drawing that waits a zoom step is seen only by readers who zoom in that far. Labels are not in the measure: a caption can still give way to another label drawn before it (the San Diego house front's does at zoom 10).
