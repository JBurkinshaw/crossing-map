# Decision records

One file per decision, in the order made. The site's "How it's built" page renders these files, so they are the project's real decision log.

Each record has four parts: **Context** (the problem), **Decision** (what we do), **Alternatives** (what we rejected and why), and **Consequences** (what follows, good and bad).

## Rules

- After a record is accepted, only its `Status:` line may change. Everything below it stays as it was decided.
- A later decision gets a new record that says what it supersedes. The old record's status line then names the new one: `superseded by NNNN`, or, when only part of it changes, which part.
- Facts learned after acceptance, such as which tile release built a decision, go in the status line or in [`../CHANGELOG.md`](../CHANGELOG.md), not in the body.
- Records cite "plan section N". Those sections are the same numbers in [`../design.md`](../design.md). The build stages a record mentions are listed in [`../roadmap.md`](../roadmap.md) where work remains.

## Index

| Record | Status |
| --- | --- |
| 0001 Story data as plain GeoJSON | accepted |
| 0002 Literary basemap as PMTiles | accepted |
| 0003 Host on GitHub Pages | accepted |
| 0004 Tiles ship as GitHub Release assets | accepted |
| 0005 Satellite through MapTiler SDK JS | accepted |
| 0006 React, TypeScript, Vite, and MapLibre | accepted |
| 0007 Python pipeline with uv | accepted |
| 0008 Inferred areas drawn by hand | accepted; amended by 0020 |
| 0009 Downloads as GeoJSON and GeoParquet | accepted |
| 0010 Dating features by episode | accepted |
| 0011 Elevation: Terrain Tiles for display, Copernicus for analysis | accepted; hillshade method superseded by 0016 |
| 0012 Ship the MapTiler SDK despite its MapLibre advisory | accepted; revisit when MapTiler ships an SDK on a fixed MapLibre |
| 0013 Running the hachure script unmodified | superseded by 0015 |
| 0014 The relief treatment | superseded by 0016 |
| 0015 A vendored hachure generator | accepted |
| 0016 The relief style (S5) | accepted; paper and hachure ink amended by 0022, hillshade by 0025 |
| 0017 Views of the literary map | accepted; Raised area superseded by 0018 and 0019; the Raised view renamed Oblique and redrawn by 0040 |
| 0018 Raised over the first two journeys | accepted; area and archive size superseded by 0019; line work superseded by 0040 |
| 0019 Raised over every journey | accepted |
| 0020 Inferred areas drafted by rule from the stop's circle | accepted |
| 0021 Least-cost routes for the sierra and valley legs | accepted; J7 leg 41 traced instead by 0032 |
| 0022 Paper, ink and lettering after the Wheeler Survey sheets | accepted |
| 0023 Landform names along computed axes | proposed |
| 0024 Wheeler hachures in the journeys corridor | accepted |
| 0025 A MapTiler-like hillshade | accepted |
| 0026 Vignettes beside their pins | accepted; extended by 0039 |
| 0027 Wheeler frame, water places and type scale on the map | accepted |
| 0028 Context places of the period on the map | proposed |
| 0029 Place pins apart from their stops | proposed |
| 0030 Lakes drawn over the rivers | proposed |
| 0031 Reservoirs built after the book left off the base map | proposed |
| 0032 Traced legs, and how each line was drawn | accepted |
| 0033 One ink per journey, and a line's dash for how sure it is | accepted |
| 0034 Ask on the first visit, then where the reader is up to | accepted |
| 0035 Plain names for certainty, and common Spanish lines left out of the panel | accepted |
| 0036 Stop names and drawing captions that give nothing away | accepted; extended by 0038 |
| 0037 One voice, one spelling, and plain words in the site's text | accepted |
| 0038 Drawings' subjects that give nothing away, and the Parham house dated 2-05 | accepted |
| 0039 Drawings in the Oblique view | accepted |
| 0040 The Oblique view: oblique-map strokes, and land cover from the CEC read with Brown's bands | accepted |
| 0041 The classic map is called the Vintage map | accepted |
| 0042 Land cover drawn in ink over its colour | accepted |
| 0043 MapTiler's logo and credits in the map's own controls | accepted |
| 0044 Reader feedback through a Tally form, discussion on Reddit | accepted |
| 0045 The data and notes stay under CC BY 4.0 | accepted |
| 0046 Compare with satellite or Topo | accepted |
| 0047 Spanish word lists for search, and the translations outside CC BY | accepted |
| 0048 Regions held by their crests | accepted |
| 0049 Which area a click opens | accepted |
| 0050 A stop's area on its card and map | accepted |
| 0051 A synopsis for each stop, folded while its episode is read | accepted |
| 0052 Episodes named by their quoted opening words, and the stop card's two blocks | accepted |
| 0053 The reader's place in the address and on the device, and "Read on" | accepted |
| 0054 The spoiler-leak test in two halves: the data at every position, the site in one walk through the book | accepted |
| 0055 The vintage map's text a fifth larger, and the credits kept clear of the cartouche | accepted |
| 0056 The head of a draw, and the gap through a range, for the she-wolf's journey | accepted |
| 0057 Stop rows checked against the book while writing the synopses | accepted |
| 0058 Back and Next go on across journeys | accepted |
| 0059 Where a stop sits on its landform: named points first, a terrain check, and the owner's review | accepted |
| 0060 On phones the story comes first, and the map carries less | accepted |
| 0061 Each route is lettered with its journey's number | accepted |
| 0062 An Itinerary page is the map's text alternative, and Compare moves without a drag | accepted |
| 0063 An open question can show its other reading on the map, and say more on request | accepted |
| 0064 A size budget for the Pages site, checked in CI | accepted |

## Template

```markdown
# NNNN. Title

Status: accepted (YYYY-MM-DD) | proposed | superseded by NNNN
Phase: P1 | P2

## Context
## Decision
## Alternatives
## Consequences
```
