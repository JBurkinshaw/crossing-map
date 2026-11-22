# 0076. Large drawings in the empty quarters at low zoom

Status: accepted (2026-11-19). Amended by 0079 (moved closer in). Amended by 0082.
Phase: P1

## Context

The map opens far out, on the whole story box (zoom about 5.5). There the small drawings (decision 0026) are 50 px or smaller and most do not show yet, and the country east and west of the story is empty paper and relief. The owner asked for much larger drawings in that empty space when the map first loads: no caption, broad themes such as a wolf or riders in the mountains, the same hand-drawn look, gone as the reader zooms in. Large art in the margins of old maps is part of the look the site follows. Design section 10 left further drawings to Phase 2 and an illustrator; the owner asked for these now.

## Decision

- **Six drawings of the book's broad themes**: the she-wolf, two riders in the sierra, sandhill cranes over a desert range, a horse herd driven across the plain, a lone rider and his packhorse, and a ruined adobe church. None shows an event of the book, so none is dated by reading progress.
- **The same pen on a larger grid.** `art/vignettes/large.py` draws each on a 288 by 216 grid with the small drawings' pen (`art/vignettes/ink.py`, whose `Drawing` now takes a grid size), so the lines are finer for the size. The horses and riders are traced afresh from Muybridge's plate 580, with tails, manes and hats drawn by hand. The wolf's outline is set by hand over a US Fish and Wildlife Service photograph, her head raised and legs lengthened so she reads as a wolf at this size. The church is drawn after suemruth's photograph of the Quarai mission ruin (CC BY 2.0), not traced. The Credits page lists all six.
- **Georeferenced images, not sprite icons.** Each is a transparent PNG (`site/public/art/`, 960 or 1152 px wide, 230 to 350 KB) on a MapLibre image source with its four corners, so it grows with the map like the land under it. The corners are in `site/src/map/largeArt.ts`: each box is 3 degrees wide and 4:3 on screen in Web Mercator, at least half a degree clear of every stop and route line. Three stand down the west side, in Sonora and Arizona, and three down the east, in Chihuahua and New Mexico. Those are the quarters a search over the story's stops and legs found empty.
- **Under the story, gone by zoom 7.** The layers lie on the relief, under every line, name and pin. They are at full strength out to zoom 6 and fade to nothing by 7, where a drawing would be about 550 px across and reach the story. Like the rest of the vintage map's base, they hide over satellite imagery and in the Oblique view.

## Alternatives

- **Sprite icons at a large size.** A 300 px icon at 2x would add about 0.6 MB per drawing to the sprite every page loads, and an icon stays the same size on screen while the land under it grows.
- **One drawing per journey.** Seven drawings would crowd the opening view, and some journeys share their themes.
- **Image generation.** Plan section 10 allows it only as a sketch, and the pen look comes from the drawing code.

## Consequences

The opening view gains about 1.7 MB of images, loaded once. On a narrow window the church in the south-east sits partly under the title cartouche. The images are fixed to the ground, so a reader who opens the map closer in, or whose first journey frames it at zoom 7 or more, does not see them until zooming out.
