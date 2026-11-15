# Pipeline

How to rebuild the published data, the tiles, and the drawings, in order. [`design.md`](design.md), section 7, explains the method; [`data-sources.md`](data-sources.md) lists every input to download first. Publishing tiles is in [`releasing-tiles.md`](releasing-tiles.md).

Run every command from the repo root. Each module's docstring has the detail and any flags not listed here. The `Makefile` groups the common runs (`make help` lists them); `make check` runs the same checks as CI.

**Private** in the tables means the step reads `private/`: the owner's copy of the novel or the downloaded caches. Those steps run only on the owner's machine. CI runs only the lint, the tests, `crossing.validate`, `crossing.downloads --check`, and the spoiler-leak test.

## Seeds

The hand-kept inputs are in `pipeline/seeds/`. The build scripts read them; only the gazetteer, `crossing.regions --force`, and `crossing.translations build` write back to them.

| File | Holds | Written by |
| --- | --- | --- |
| `places.csv` | Every place the book names, plus context towns, with the book's spellings and first episode | Hand |
| `place-picks.csv` | The gazetteer's pick and candidates for each place | `crossing.gazetteer` |
| `place-overrides.csv` | Hand decisions, which win over a pick, each with its reasoning | Hand |
| `stops.csv` | Every journey's stops, in order, with reasoning and `travel` | Hand |
| `snaps.csv` | The road, river, or flowline each narrated segment follows | Hand |
| `modeled-legs.csv` | The legs drawn as least-cost paths (decision 0021), with mode, corridor and a note | Hand |
| `regions.geojson` | The Animas Valley and La Babícora outlines | `crossing.regions`, then hand edits in QGIS |
| `areas.geojson` | Each inferred area's outline: the stop's circle cut by a rule (decision 0020) | `crossing.area_drafts`, then hand edits in `pipeline/qgis/areas.qgs` |
| `vignettes.csv` | The vignette anchors | Hand |
| `landforms.toml` | Every weight and threshold of the landform rules, with comments | Hand |
| `landform_axes.toml` | Hand edits to the landform label lines, each with a reason | Hand |
| `translations.csv` | Our English for each Spanish line; a non-empty cell wins over the draft | `crossing.translations build`, then hand edits |
| `road-refs.csv` | Runs of lines spoken while travelling one route segment | Hand |
| `where-spoken.csv` | Single lines placed by hand, each with a reason | Hand |

## 1. Story data

| Step | Command | Reads | Writes | Private |
| --- | --- | --- | --- | --- |
| Episodes and mentions | `uv run --project pipeline python -m crossing.extract` | `private/book/the-crossing.epub`, `places.csv` | `private/book/episodes.csv`, `mentions.csv`, and `text/<episode>.txt` | Yes |
| Episode list | `uv run --project pipeline python -m crossing.build_episodes` | `private/book/episodes.csv` | `data/episodes.json`, keeping summaries and page ranges | Yes |
| Gazetteer | `uv run --project pipeline python -m crossing.gazetteer [ID ...]` | `places.csv`, GNIS, GeoNames, Wikidata (cached) | `place-picks.csv`. Without IDs it refreshes the seeds already picked and lists seeds with neither a pick nor an override; name a new seed's ID to add it | Yes |
| Area drafts | `uv run --project pipeline python -m crossing.area_drafts [--force]` | `stops.csv`, `data/places.geojson`, the DEM, INEGI, NHD and TIGER | `pipeline/seeds/areas.geojson`, keeping areas marked `checked` with `--force`; a report in `private/review/areas/`. `--qgis` writes the QGIS project's layers | Yes |
| Modelled legs | `uv run --project pipeline python -m crossing.least_cost` (optional: `build_story` calls it) | `modeled-legs.csv`, `data/stops.geojson`, the DEM, INEGI streams and road tracks, Natural Earth | Cached routes in `private/cache/least-cost/routes/`, and a line per leg printed | Yes |
| Story layers | `uv run --project pipeline python -m crossing.build_story` | The seeds; snap shapefiles in `private/cache/` | `data/places.geojson`, `stops.geojson`, `areas.geojson`, `journeys.geojson`, `elsewhere.json`; the stage 4 checklists, keeping ticked rows | Yes |
| Region drafts | `uv run --project pipeline python -m crossing.regions [--force]` | `data/places.geojson`, the DEM | `pipeline/seeds/regions.geojson`; refuses to overwrite without `--force` | Yes |
| Vignette anchors | `uv run --project pipeline python -m crossing.build_vignettes` | `vignettes.csv`, `data/stops.geojson`, `data/places.geojson` | `data/vignettes.geojson` | No |
| State labels | `uv run --project pipeline python -m tiles.state_labels` | Natural Earth admin 1 states, the story layers in `data/` | `site/public/labels/states.geojson`: label points clear of the story | Yes |
| Water places | `uv run --project pipeline python -m crossing.water_places` | GNIS, GeoNames, `data/places.geojson`, `data/journeys.geojson` | `data/water_places.geojson`: springs, wells, tanks, ranches and stations in the journeys corridor | Yes |
| Context places | `uv run --project pipeline python -m crossing.context_places` | GNIS, the GNIS national file of 2021 (`private/cache/gazetteer/Features_20210825/`), GeoNames, Natural Earth railroads, `data/places.geojson`, `data/water_places.geojson` | `data/context_places.geojson`: forts, ghost towns, mines, sawmills, churches, cemeteries, schools, old post offices, corrals, camps, named wells, dry lakes and flats in the journeys corridor | Yes |
| Graticule | `uv run --project pipeline python -m crossing.graticule` | The story box | `site/public/labels/graticule.geojson`: the 15′ graticule | No |

Order matters in four places:

1. A first build runs `crossing.build_story` (it skips a missing regions file), then `crossing.regions`, then `crossing.build_story` again, because the region drafts sit on place pins.
2. `crossing.build_vignettes`, `tiles.state_labels` and `crossing.water_places` follow `crossing.build_story` (the water places drop gazetteer points near the book's places and follow the journeys' corridor), and `crossing.context_places` follows `crossing.water_places`, whose names it does not repeat.
3. After a change to a stop's pin or radius, run `crossing.area_drafts --force` before `crossing.build_story`, which stops if a draft lies outside its stop's circle.
4. `crossing.validate` checks that `data/raised/` holds the same features, first seen at the same episodes, as the flat layers. After a `build_story` change that adds, removes, or redates a feature, rerun `crossing.plan_oblique` (section 5, hours) before committing, or CI fails.

## 2. Summits

| Step | Command | Reads | Writes | Private |
| --- | --- | --- | --- | --- |
| DEM tiles | `uv run --project pipeline python -m crossing.fetch_dem [--story-box]` | `data/journeys.geojson` | `private/cache/dem/copernicus/` (corridor); with `--story-box`, `copernicus-region/` | Yes (network) |
| Peaks | `uv run --project pipeline python -m crossing.peaks` | The DEM, gazetteers, `data/places.geojson`, the previous `data/mountain_glyphs.geojson` | `data/mountain_glyphs.geojson` | Yes |
| Landforms | `uv run --project pipeline python -m crossing.landforms` | `data/mountain_glyphs.geojson`, `landforms.toml`, the DEM | Landforms in `data/mountain_glyphs.geojson`; `review/stage-3/landforms.csv` | Yes |
| Landform label lines | `uv run --project pipeline python -m crossing.landform_axes` | `data/places.geojson`, GNIS, GeoNames, GMBA (`private/cache/gmba/`), the DEM, `landform_axes.toml` | `data/landforms.geojson` | Yes |
| Pass names | `uv run --project pipeline python -m crossing.pass_lines` | `data/mountain_glyphs.geojson`, `data/places.geojson`, Natural Earth roads, the DEM | `site/public/labels/passes.geojson`: each named pass, rotated to the road through it or across its saddle | Yes |

`crossing.landforms` must follow every `crossing.peaks` run: `crossing.validate` fails until it has. `crossing.pass_lines` follows `crossing.peaks` and any change to the book's passes. `crossing.landform_axes` follows a change to the book's ranges, valleys or plains in `places.geojson`; `crossing.validate` fails if a line shows before its place. It downloads nothing: fetch the GMBA standard zip (`https://data.earthenv.org/mountains/standard/GMBA_Inventory_v2.0_standard.zip`) into `private/cache/gmba/` first. `crossing.peaks` keeps the ids of nearby glyphs from the previous file, so the committed file is also an input.

## 3. Translations

The `translations` extra installs pypdf, lingua, and rapidfuzz.

| Step | Command | Reads | Writes | Private |
| --- | --- | --- | --- | --- |
| Find | `uv run --project pipeline --extra translations python -m crossing.translations find` | `private/book/text/`, the cached guide PDF, `/usr/share/dict/words` | `private/translations/spans.json` | Yes |
| Build | `uv run --project pipeline --extra translations python -m crossing.translations build` | Spans, drafts, `translations.csv`, `road-refs.csv`, `where-spoken.csv` | `data/translations.json`, `translations.csv`, `review/stage-5/translation-gaps.csv` | Yes |

Span ids (`tr-<episode>-<nnn>`) number the lines in reading order. Do not rerun `find` with changed detection settings after editing has started, or the ids can shift. On Linux, install the `wamerican` package for the word list.

## 4. Photos

| Step | Command | Reads | Writes | Private |
| --- | --- | --- | --- | --- |
| Candidates | `uv run --project pipeline python -m crossing.photos [--dry-run \| --offline]` | Places and stops, cached Wikidata entities, Commons (cached) | `review/stage-6/photos.csv`, keeping every pick | Yes (network) |

`--dry-run` counts the requests still needed. `--offline` writes the CSV from the cache only.

## 5. Relief and the Raised view

These need QGIS 4. Set `QGIS_ENV` to its micromamba environment.

| Step | Command | Reads | Writes | Private |
| --- | --- | --- | --- | --- |
| Hachures | `QGIS_ENV=/path/to/qgis uv run --project pipeline python -m crossing.hachures [--scale fine\|coarse\|dense\|all] [--jobs 4]` | The DEM, `data/journeys.geojson` | `private/cache/relief/production/` | Yes |
| Wheeler hachures | `QGIS_ENV=/path/to/qgis uv run --project pipeline python -m crossing.hachures --style wheeler --region corridor --out private/cache/relief/wheeler [--jobs 9]` (or `--bbox W S E N` for one box) | The DEM, `data/journeys.geojson`, `data/mountain_glyphs.geojson` | `private/cache/relief/wheeler/` | Yes |
| Full-region run (optional) | `QGIS_ENV=/path/to/qgis uv run --project pipeline python -m crossing.full_region [--jobs 10]` | `copernicus-region/` | The same tile cache; a report in `private/overnight/full-region.md` | Yes |
| Raised view | `uv run --project pipeline python -m crossing.plan_oblique` | The hachure cache, the DEM, INEGI, NHD, Natural Earth, Census | `tiles/out/oblique-<n>.pmtiles`, `data/raised/*.geojson`, `data/raised/archives.json` | Yes |

Hachure tiles are cached one file per tile. Delete a tile's file to run it again. The Wheeler build (decision 0024) keeps its generator tiles in `<out>/tiles/`; they depend only on the tile and the Wheeler settings, so a box's tiles can be copied into the corridor's folder. It cuts, clears and measures the strokes again on every run, which takes a few minutes. `crossing.full_region` sizes a whole-region run and does not change the production build.

## 6. Tiles

| Step | Command | Reads | Writes | Private |
| --- | --- | --- | --- | --- |
| Base map | `uv run --project pipeline python -m tiles.build_base` | Natural Earth, Census, NHD, INEGI | `tiles/out/base.pmtiles` | Yes |
| Relief | `uv run --project pipeline python -m tiles.build_relief` | The hachure cache | `tiles/out/relief.pmtiles`, `relief-dense.pmtiles`, `contours.pmtiles` | Yes |
| Wheeler relief | `uv run --project pipeline python -m tiles.build_relief --style wheeler --region corridor` | The Wheeler cache, the production `coarse.geojson` | `tiles/out/relief-wheeler.pmtiles` (zoom 10-11), `relief-wheeler-12.pmtiles` (zoom 12) | Yes |
| Terrain | `uv run --project pipeline python -m tiles.build_terrain` | AWS Terrain Tiles (cached in `private/cache/terrain/`) | `tiles/out/terrain.pmtiles` | Yes (network once) |
| Sharper terrain (not released) | `uv run --project pipeline python -m tiles.build_terrain_hi [--estimate N] [--zooms MIN MAX] [--bbox W S E N] [--quantum M] [--out PATH]` | The Copernicus tiles | `tiles/out/terrain-hi.pmtiles` | Yes |
| Into the local site | `uv run --project pipeline python -m tiles.install` | `tiles/out/` | `site/public/tiles/`, removing Raised archives that `archives.json` no longer lists | No |

Each archive must stay under 100 MB. `tiles.build_relief` and `crossing.plan_oblique` split their output to keep under it.

## 7. Drawings and type

These write straight into `site/public/` and are committed, because CI has no Rust.

| Step | Command | Writes | Needs |
| --- | --- | --- | --- |
| Mountain glyphs | `uv run --project pipeline python -m art.glyphs.make_glyphs` | `art/glyphs/svg/`, then the sprite | `spreet` |
| Vignettes | `uv run --project pipeline --extra art python -m art.vignettes.make_vignettes [ID ...]` | The 13 drawings in `art/vignettes/svg/`, from the subjects in the script and the traced outlines in `art/vignettes/traced/`, then the sprite | `spreet`, the `art` extra (svgelements) |
| Sprite only | `uv run --project pipeline python -m art.build_sprite` | `site/public/sprites/` | `spreet` |
| Map type | `tiles/build_glyphs.sh` | `site/public/fonts/` | `build_pbf_glyphs`, the IM Fell fonts in `private/cache/basemap/fonts/` |

Install the Rust tools with `cargo install spreet build_pbf_glyphs`.

## 8. Publish and check

| Step | Command | Private |
| --- | --- | --- |
| GeoParquet copies | `uv run --project pipeline python -m crossing.downloads` (`--check` writes nothing and fails on any mismatch) | No |
| Validate | `uv run --project pipeline python -m crossing.validate` | No |
| Echo check | `uv run --project pipeline python -m crossing.echo_check [--words N] [PATH ...]` | Yes; skips without the text |

Run `crossing.downloads` after any change to a story layer, then `crossing.validate`, then `crossing.echo_check`. A full data rebuild is sections 1 to 4 in order, then section 8.
