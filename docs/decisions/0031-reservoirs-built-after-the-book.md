# 0031. Reservoirs built after the book left off the base map

Status: proposed (2026-11-15). Owner's request after the Bavispe review.
Phase: P1

## Context

The base map's lakes come from INEGI's water bodies in Mexico, NHD's dry lakes in the US, and Natural Earth's lakes elsewhere (`tiles/lakes.py`). Many are reservoirs. NHD's reservoirs were already left out, but INEGI and Natural Earth hold reservoirs whose dams were built after the book's years (1939 to 1945, decision 0028), such as El Novillo on the Yaqui (1964). A reader would take them for water the riders saw. Neither source dates its water bodies.

## Decision

- **The dates come from the Global Dam Watch database v1.0** (Lehner et al. 2024, CC BY 4.0), which carries GRanD v1.3 and gives each dam's year (`YEAR_DAM`) and a reservoir polygon. It was chosen over CONAGUA's SISPRESAS inventory, which had no public download the project could reach.
- **`tiles.later_reservoirs` drafts a list, `pipeline/seeds/later_reservoirs.csv`.** A lake is a reservoir's when at least half its area lies in the reservoir's GDW polygon (areas in an Albers equal-area projection on WGS 84, standard parallels 27° and 35° N). Each such lake gets a row with the dam's name, river, year and year source, and a point inside the lake.
- **The drafted action is "drop" for a dam finished after 1945, and "keep" otherwise.** A dam finished from 1939 to 1945, such as La Angostura on the Bavispe (1942), is kept: it stood during part of the book. A dam with no year in GDW, or one that only regulates a natural lake, is kept and its note asks for review.
- **The list is curated by hand.** A rerun keeps each row's `action` and `note`, so a hand edit survives. `tiles.lakes` reads only the list, not GDW, and leaves out every lake polygon that holds a "drop" point.
- On 2026-11-15 the draft has 53 rows: 24 lakes dropped (18 dams), 29 kept. 21 of the kept rows are small dams in Mexico with no year.

## Alternatives

- **CONAGUA's SISPRESAS.** Mexico's own inventory, with construction years, but its site redirected to CONAGUA's home page and datos.gob.mx refused the request. GDW covers both countries in one file.
- **Remove every reservoir GDW knows.** Simpler, but it would also remove the reservoirs that stood in 1939, such as Elephant Butte (1921 in GDW) and Roosevelt Lake (1911).
- **Draw later reservoirs as a dashed outline with the year.** Honest, but it is a new map feature; possible later.
- **Clip the lakes by the GDW polygons.** The two sources' outlines differ, so a clip would leave slivers. Whole lakes are kept or left out.

## Consequences

- Where a reservoir is left out, the river under it shows: INEGI's and NHD's flow lines run through water bodies. That line approximates the drowned channel; it is not a survey of the old riverbed.
- A reservoir not in GDW, or matched to a lake by less than half its area, is still drawn. So is a dam GDW does not date.
- The list's names and years come from GDW, so GDW is credited on the Credits page and in `data/README.md`.
