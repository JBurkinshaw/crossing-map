# The Crossing: a reading map

A free, self-hosted reading guide to Cormac McCarthy's *The Crossing*. The site maps every journey in the book on real geodata and marks honestly where the book leaves us guessing.

The preview at <https://jburkinshaw.github.io/crossing-map/preview/> maps the whole book: all four Parts, seven journeys, the Spanish lines and their translations, and the open questions where placing something is a judgement call. The public root, <https://jburkinshaw.github.io/crossing-map/>, still serves an early build of Part I until the work is merged to `main`. Corrections are welcome as [issues](https://github.com/JBurkinshaw/crossing-map/issues); see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Documentation

| File | What it holds |
| --- | --- |
| [`docs/design.md`](docs/design.md) | How the site should work, the rules it keeps, and a glossary |
| [`docs/roadmap.md`](docs/roadmap.md) | Open work and the owner's pending decisions |
| [`docs/decisions/`](docs/decisions/README.md) | One record per technical or judgement call, published on the site |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Changes readers and data users can see |
| [`docs/pipeline.md`](docs/pipeline.md) | Every build step, in order |
| [`docs/releasing-tiles.md`](docs/releasing-tiles.md) | Building and publishing a tile release |
| [`docs/data-sources.md`](docs/data-sources.md) | Every pipeline input and where it comes from |
| [`data/README.md`](data/README.md) | The published data, its licences, and the copyright check |

## Run it locally

You need Node 22 (`.nvmrc`) and, for the checks, [uv](https://docs.astral.sh/uv/). Run each command from the repo root.

1. Install the site's packages:

   ```bash
   (cd site && npm ci)
   ```

2. Optional: for Satellite, Topo, and Compare, put a MapTiler key in `site/.env.local`. The key must allow your dev server's origin. Without a key, those switches show as unavailable and the classic map works as normal.

   ```ini
   VITE_MAPTILER_KEY=your-key
   ```

3. Get the tiles into `site/public/tiles/`. Either download the release that `tiles/release.txt` names (needs [`gh`](https://cli.github.com/), logged in):

   ```bash
   gh release download "$(cat tiles/release.txt)" --pattern '*.pmtiles' --dir site/public/tiles
   ```

   or, after building tiles yourself, copy them in with `uv run --project pipeline python -m tiles.install`.

4. Start the dev server. It copies `data/` into the app first.

   ```bash
   (cd site && npm run dev)
   ```

The dev server also serves the map lab at `/lab.html` and the route review at `?review=routes`. Two optional variables help scripted checks: `VITE_DEBUG=1` keeps the `window.__map` handle (opened with `?debug`) in a production build, and `VITE_TILES_BASE` points a build at tiles served from another path.

Before a commit, run the checks from the repo root:

```bash
(cd site && npm run lint && npm test)
uv run --project pipeline ruff check
(cd pipeline && uv run pytest)
uv run --project pipeline python -m crossing.validate
```

[`CONTRIBUTING.md`](CONTRIBUTING.md) explains them and the copyright check.

## Rebuild the data

Most steps read the owner's private copy of the novel or downloaded caches in `private/`, so they run only on the owner's machine. [`docs/pipeline.md`](docs/pipeline.md) gives every step in order, with its inputs and outputs; [`docs/data-sources.md`](docs/data-sources.md) lists the downloads; [`docs/releasing-tiles.md`](docs/releasing-tiles.md) covers publishing tiles. `make help` lists the common runs, and `make check` runs the CI checks.

The full toolchain:

- **uv**, which installs Python 3.12 and the pipeline's packages (`uv sync --project pipeline`, plus `--extra translations` for the translation build).
- **GDAL** 3.13 or later, with the Parquet and PMTiles drivers (`ogr2ogr`, `gdalwarp`, `gdalbuildvrt`).
- **tippecanoe** and the **`pmtiles`** CLI, for the tile builds.
- **`gh`**, for downloading and publishing tile releases.
- **spreet** and **build_pbf_glyphs**, for the sprite and the map type: `cargo install spreet build_pbf_glyphs`.
- **QGIS 4** in a micromamba environment, for the hachures, with `QGIS_ENV` set to that environment.

## Layout

| Folder | Contents |
| --- | --- |
| `site/` | Vite, React, and TypeScript app |
| `data/` | Published GeoJSON and JSON, with schemas |
| `pipeline/` | Python (uv) package that builds the data |
| `tiles/` | Tile build scripts. Built PMTiles are release assets, not committed |
| `art/` | Mountain-glyph and vignette sources, and the sprite build |
| `tools/` | Site build, spoiler-leak test, and screenshot scripts |
| `review/` | Review packets and worksheets awaiting the owner |
| `docs/` | Design, roadmap, decision records, changelog, and reference indexes |
| `private/` | Git-ignored. The book copy, caches, and reference images stay on the owner's machine |

## Licences

The licences below are in place, and the owner has yet to confirm them before launch ([`docs/roadmap.md`](docs/roadmap.md#2-decisions-pending)).

- Code: MIT (`LICENSE`).
- Data and notes in `data/`: CC BY 4.0 (`data/LICENSE`), with per-layer source terms listed in `data/README.md`.
- `pipeline/relief/hachures/`: GPL-3.0, an adapted copy of Daniel Huffman's Hachures script (decision 0015). The hachure lines it generates are map data, under the data licence.

The site republishes no text from the novel.
