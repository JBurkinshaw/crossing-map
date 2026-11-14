# The Crossing: a reading map

A free, self-hosted reading guide to Cormac McCarthy's *The Crossing*. The site maps every journey in the book on real geodata and marks honestly where the book leaves us guessing.

The whole book is mapped: all four Parts, seven journeys, the Spanish lines and their translations, and the open questions where the placing is a judgement call. The site is live at <https://jburkinshaw.github.io/crossing-map/>, with the newest work under [`/preview/`](https://jburkinshaw.github.io/crossing-map/preview/). It is in soft launch: corrections are welcome as [issues](https://github.com/JBurkinshaw/crossing-map/issues).

The build plan is in [`docs/plan.md`](docs/plan.md), and what is still to do is in [`review/outstanding.md`](review/outstanding.md). Changes readers can see are in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

## Layout

| Folder | Contents |
| --- | --- |
| `site/` | Vite, React, and TypeScript app |
| `data/` | Published GeoJSON and JSON, with schemas |
| `pipeline/` | Python (uv) scripts that build the data |
| `tiles/` | Tile build scripts. Built PMTiles are release assets, not committed |
| `tools/` | Build and review-packet scripts |
| `review/` | Review packets and CSVs for sign-off |
| `docs/` | The plan, decision records, and link indexes |
| `private/` | Git-ignored. The book copy and reference images stay on the author's machine |

## Licences

- Code: MIT (`LICENSE`).
- Data and notes in `data/`: CC BY 4.0 (`data/LICENSE`), with per-layer exceptions listed in `data/README.md`.
- `pipeline/relief/hachures/`: GPL-3.0, an adapted copy of Daniel Huffman's Hachures script (decision 0015). The hachure lines it generates are map data, under the data licence.

The site republishes no text from the novel.
