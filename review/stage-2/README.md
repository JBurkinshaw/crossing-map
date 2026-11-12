# Stage 2 review packet: the literary base, first look

## What was built

- **Base tiles.** `tiles/build_base.py` clips Natural Earth 10m and the US Census 2023 county lines to the story box and builds `base.pmtiles` with tippecanoe, at zoom 4–11. The archive is 1.1 MB.
- **Literary style** (`site/src/map/style.ts`):
  - caliche paper, with the Mexico side a shade darker
  - rivers in blue-grey ink
  - a dash-dot international line
  - dashed state lines and dotted county lines
  - railroads with cross-ties
  - dashed roads
- **Self-hosted IM Fell glyphs.** `tiles/build_glyphs.sh` builds them from the OFL fonts, and they are committed with the licence. Towns are labelled in roman type, rivers in italic along the line, and ranges and valleys in spaced italic.
- **Map furniture.** A scale bar in miles (the book's unit), a title cartouche, and a north arrow.
- **Guild references.** 24 threads are indexed in `docs/inspiration/guild.md`, with screenshots in `private/inspiration/guild/`.

## What to look at

1. Look at `screenshots/`, especially `bootheel-desktop.png` and `casas-grandes-desktop.png`.
2. Compare them with the Wheeler and Ehrenberg sheets, and with the Guild screenshots. Judge type, colour, and line weights.

## Checks the base already gives stage 1

- Natural Earth's Bavispe line runs through the wolf's crossing circle and past the J2 stops at Colonia Oaxaca and Morelos, which were placed from gazetteer points alone.
- The border stop at 108°30′ W sits on the 31°20′ line, west of the bootheel's corner.
- The Mexico Northwestern railroad runs through Casas Grandes, as the book describes.

## Decided (11 November 2026)

- **Paper: option B, caliche** (`#e4ddcc`, Mexico `#d9cfbb`). The three options are in `paper/` for comparison.
- **Towns: option 1.** The Natural Earth towns are gone from the style and the tiles. Every town label now comes from `data/places.geojson`, so it carries a source and obeys the spoiler filter. Fifteen real towns the book never names (Bisbee, Willcox, Fronteras, Nacozari, Huásabas, Nuevo Casas Grandes and others; `pipeline/seeds/context.csv`) are a `context` set, shown at every reading position as small faint dots. The resolver now prefers a municipal seat to a minor place of the same name. That fixed Moctezuma and Cumpas, and no Part I pick changed.

## Added since the first look

- **Creeks.** USGS NHD natural streams for six bootheel watersheds, from zoom 9. Named creeks show from zoom 9; the dense unnamed network from zoom 10, fainter. NHD maps these cross-border watersheds into Sonora as well.
- **First narrated route.** The wolf's leg from Whitewater Creek to the San Luis Mountains now follows the creek's NHD course, drawn solid; legs the book names no road or river for stay dashed. `pipeline/seeds/part1-snaps.csv` lists snapped legs. See `screenshots/whitewater-z10-desktop.png`.

- **Satellite and compare.** A Literary / Satellite / Compare switch, top right. Satellite draws the journeys, stops, labels and border over MapTiler imagery; Compare splits the view at a draggable divider (arrow keys move it too). The MapTiler SDK and its session start only when a reader first leaves the literary map, and the satellite map is then kept, so switching back and forth costs one session (checked: one style load over six switches). The SDK carries a MapLibre advisory, accepted in decision 0012. See `screenshots/satellite-desktop.png` and `compare-desktop.png`. On the live site satellite waits on the MapTiler key accepting the Pages origin.

## Not done yet in stage 2

- **60 fps on a mid-range phone.** Not measured yet.
- **Mexican creeks beyond the border watersheds.** INEGI's 1:50,000 river network has no direct download; it comes through INEGI's interactive downloads portal (see `TODO-prerequisites.md`). The Cajon Bonita leg stays schematic until then.
- **More snapped legs.** The Cloverdale Creek road is a road, not the creek; no road line for it exists yet.
- **State names in small capitals.** The glyphs are built; the label points are not.
- **Spoiler hiding.** Every label shows regardless of reading progress. That is stage 5.

## Data sources

Downloaded on 11 November 2026 into `private/cache/basemap/`:

- Natural Earth 10m, public domain, from https://naciscdn.org/naturalearth/10m/: admin 0 boundary lines, admin 1 states and lines, rivers and lake centrelines (plus the North America supplement), lakes (plus the North America supplement), railroads (North America), roads, and populated places.
- US Census cartographic boundary counties, 2023, 1:500k, public domain: https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip
- USGS NHD Best Resolution, HU8 units 13030201, 13030202, 15040006, 15080301, 15080302 and 15080303 (shapefiles, published December 2023), public domain: https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU8/Shape/
- IM Fell English, IM Fell English Italic, and IM Fell English SC, by Igino Marini, under the SIL Open Font License, from https://github.com/google/fonts

## Before this stage can deploy

`tiles/release.txt` now names `tiles-v2`: the rebuilt base (no towns, with creeks, 5.5 MB) and the stage 3 terrain archive (69.4 MB), published together so stage 3 needs no further release. From anywhere:

```bash
gh release create tiles-v2 /Users/jb/repos/crossing-map/tiles/out/base.pmtiles /Users/jb/repos/crossing-map/tiles/out/terrain.pmtiles --repo JBurkinshaw/crossing-map --target main --title 'Tiles v2: base with creeks, and terrain' --notes 'base.pmtiles: Natural Earth 10m, 2023 Census counties and USGS NHD streams, zoom 4-11 (tiles/build_base.py). terrain.pmtiles: AWS Terrain Tiles, Terrarium encoding, zoom 5-10 (tiles/build_terrain.py); 3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey; Source: INEGI, Continental relief, 2016.'
```
