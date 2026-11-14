# tiles-v8: creeks, lakes and river names

What changes in `base.pmtiles` (the only archive that changes in `tiles-v8`), 14 November 2026.

## What changed

- **Creeks by one rule** (from the streams packet, `../streams/`): INEGI's and NHD's smaller streams on both sides of the border, each shown from a zoom set by its Strahler order, widening with order, intermittent ones lighter. `tiles/creeks.py`.
- **River names show again.** The traced rivers (`tiles/rivers.py`) meander too tightly for MapLibre to fit a name along them, so the Bavispe had no name at zoom 9. Names now follow a `river_label` layer: each named river simplified to about 400 m and rounded (Chaikin's corner cutting). Major rivers keep their italic names; minor rivers (Natural Earth's `river_minor`, such as the Río Batepito) are named from zoom 9, smaller. Capitals for the major rivers, as on the Wheeler sheets, is a toggle in the lab, not applied.
- **Stream orders fixed.** NHD's Strahler orders climbed into the hundreds along braided channels, ditches and lines repeated in two watersheds, which made those channels nearly free to the river trace. `rivers.strahler` now raises an order only where two equal orders meet from different sources; `tiles/creeks.py` uses the same function.
- **Lakes from INEGI in Mexico** (`tiles/lakes.py`): every perennial water body of at least 0.1 km², intermittent ones of at least 1 km² (drawn lighter), islets under 0.5 km² filled. Natural Earth's lakes stay outside Mexico. The Laguna de Babícora is now its real shape, and the J5 lake camp (moved in commit c7c596d) sits on its shore.
- **A measure of network breaks.** The build now prints how many km of each traced river run along Natural Earth's line because INEGI's or NHD's network breaks there: 816 km in all, most of it far from the story (the Fuerte 143, the Rio Grande 90, the Colorado 83). A join of broken channel ends was tried and measured: it joined 726 ends but cut the fallback by only 13 km (1.6%), so it was dropped. The Río Batepito's straight 7.8 km above Colonia Morelos remains.

## Checked

- The rendered river labels at six places (screenshots here): the Bavispe at zoom 9 and 12, the Santa María, the Río Batepito and the Bavispe at Colonia Morelos, the Rio Grande. The Babícora lake at zoom 11.
- `crossing.validate`, `crossing.echo_check`, and the spoiler-leak test against the dev server.

## Open questions

1. Streams cross the Babícora lake (its arroyos run through INEGI's water body). Clip creeks by the lakes, or leave them as the lake's channels?
2. Capitalised, letter-spaced names for the major rivers, as on the Wheeler sheets? It is a toggle in the lab (`site/lab.html`, Wheeler section).
