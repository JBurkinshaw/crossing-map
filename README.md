# The Crossing: a reading map

A free, self-hosted reading guide to Cormac McCarthy's *The Crossing*. The site maps every journey in the book on real geodata and marks honestly where the book leaves us guessing.

This repository is at an early stage. The build plan is in [`docs/plan.md`](docs/plan.md); work runs in stages, one pull request per stage.

## Layout

| Folder | Contents |
| --- | --- |
| `site/` | Vite, React, and TypeScript app |
| `data/` | Published GeoJSON and JSON, with schemas |
| `pipeline/` | Python (uv) scripts that build the data |
| `tiles/` | Tile build scripts. Built PMTiles are release assets, not committed |
| `tools/` | Review-packet and browsing scripts |
| `review/` | Review packets and CSVs for sign-off |
| `docs/` | The plan, decision records, and link indexes |
| `private/` | Git-ignored. The book copy and reference images stay on the author's machine |

## Licences

- Code: MIT (`LICENSE`).
- Data and notes in `data/`: CC BY 4.0 (`data/LICENSE`), with per-layer exceptions listed in `data/README.md`.
- `pipeline/vendor/hachures/`, when added: GPL-3.0, an adapted copy of Daniel Huffman's Hachures script.

The site republishes no text from the novel.
