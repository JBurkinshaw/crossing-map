# 0073. Vignettes to 150, by the book's big scenes

Status: accepted (2026-11-19); placement superseded by 0075, which also corrects its note on overlapping drawings
Phase: P1

## Context

The map had 71 drawings, spread unevenly. Some journeys had long stretches with nothing on them: J4 had a handful of drawings over 41 stops, and much of J7's ride through New Mexico and Arizona had none. The owner asked for more drawings at stops and along legs, the big scenes first, with something general on long empty stretches, up to 150 in all. Accuracy is welcome but matters less than coverage.

Five readers each read one block of the book in full, checked the 71 drawings against the text and proposed 223 new ones with chapter and line references. The check found no invented scene, but 31 drawings had a detail the text does not give, or stood in the wrong place.

## Decision

- **79 new drawings.** The picks are the proposals marked as key scenes, spread across every journey, plus simple travel scenes on the longest empty stretches: the she-wolf's legs through the San Luis Pass, J4 on route 666 past Elfrida and McNeal, and J7 at Winslow, on the Plains of San Agustín, towards Glenwood and over the Black Range. J4 gains its scenes of Billy, Boyd and the dog travelling together, the owner's example.
- **Each drawing is checked against its passage** and drawn in the glyphs' pen, after the references already in use: the traced Muybridge rider and horse, the traced US Fish and Wildlife Service wolf, and the public-domain photographs in the reference set. Where none fits, the drawing is from the book's description and its credit says so. No new images were fetched.
- **The scenes from the corrido at Bachíniva** (six riders, and the lovers carried to a secret grave) are drawn in a broadside's border and captioned as the song's telling, so they do not read as events the book shows.
- **Corrections to the existing drawings.** The notes, names and labels that went beyond the text now follow it. Billy wades thigh-deep at the ford, not chest-deep. At the blind man's house the wife tells their story. Quijada is superintendent of the Nahuerichic. The Babícora's cattle are whitefaced, not Herefords. The gold star hangs alone in the window, without a service flag. The boundary obelisks are concrete. The red Waco comes down among the trees, and the Trinity drawing is "the Trinity light". Two drawings are redrawn to match: the ford and the gold star.
- **Placement fixes.** Billy's hawk moves to the leg before the promontory (`j3-seg-01`), where the book has it. The hailstorm moves to the end of the leg from Morelos towards Ojito (`j3-seg-11`). The two drawings on the Cajón Bonito leg take the book's order: the wolf on the rope early on it, the night by the fire late.
- **The opera camp stays south of Las Varas,** as the text has it. Its stop was already there.

## Alternatives

- **Every proposal (223 more, about 300 drawings).** The map is already crowded at 150 (see below).
- **Only the key scenes, with no general travel scenes.** It leaves the longest stretches of J7 and the she-wolf's route as empty as before, which is what the owner asked to fix.
- **New reference photographs for each subject.** Better likenesses for a few subjects (the Dodge, the tamale cart, the goat), but a network batch for little gain at 53 px.

## Consequences

`pipeline/measure/vignette_clashes.py`, at each drawing's own first zoom:

| | 71 drawings (decision 0066) | 150 drawings |
| --- | --- | --- |
| Drawings that clash (a stop, or more than their width of route line) | 32 | 82 |
| Stop markers covered | 27 | 95 |
| Route line covered | 6,260 px | 16,824 px |
| Pairs of drawings on each other | 0 | 110 |

At zoom 10, 143 drawings show and 68 pairs overlap. The map's symbol collision draws the higher-priority drawing and hides the other, so fewer show at once than the count suggests, and more appear on zooming in. Many drawings, old and new, now wait one zoom step (from 8 to 9 or 9 to 10) under decision 0026's cap. The bootheel, Casas Grandes and the Babícora are the most crowded.

A shared drawing helper dropped arc segments when it bent a path, so every person drawn with it had no head. With that fixed, seven published drawings gain the heads they were drawn with: the children on Niño, the oxen at the river, the recruiting office, the silver mine family, the taking of the girl, the bearers and the wedding cart.

Some drawings read only roughly at map size: the surgery by candlelight, Alfonso's scars, the violins at the Tarahumara camp, the one-armed man's empty sleeve and the burro stampede. They can be redrawn without moving.
