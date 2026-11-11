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

## Questions for you

1. **The paper and Mexico tints** (`#e6d9bd` and `#dccdaa`): too yellow, or about right?
2. **Duplicate labels.** A town that is both a Natural Earth town and one of our places is labelled twice; Ascensión shows it. Should our places replace the base towns of the same name, or should base towns be dropped once a place exists?

## Not done yet in stage 2

- **Swipe to satellite.** Blocked on the MapTiler key.
- **60 fps on a mid-range phone.** Not measured yet.
- **Small creeks.** Cloverdale Creek, Whitewater Creek, and the Cajon Bonita are not in Natural Earth. They need USGS NHD and INEGI hydrography, a larger download batch, asked for separately.
- **Part I routes in their final ink, snapped to rivers.** This waits on the small-creek data.
- **State names in small capitals.** The glyphs are built; the label points are not.
- **Spoiler hiding.** Every label shows regardless of reading progress. That is stage 5.

## Data sources

Downloaded on 11 November 2026 into `private/cache/basemap/`:

- Natural Earth 10m, public domain, from https://naciscdn.org/naturalearth/10m/: admin 0 boundary lines, admin 1 states and lines, rivers and lake centrelines (plus the North America supplement), lakes (plus the North America supplement), railroads (North America), roads, and populated places.
- US Census cartographic boundary counties, 2023, 1:500k, public domain: https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip
- IM Fell English, IM Fell English Italic, and IM Fell English SC, by Igino Marini, under the SIL Open Font License, from https://github.com/google/fonts

## Before this stage can deploy

`tiles/release.txt` now names `tiles-v1`. Publish the base archive as that release, from the repo root:

```bash
gh release create tiles-v1 tiles/out/base.pmtiles --target main --title 'Tiles v1: literary base, first look' --notes 'Natural Earth 10m and US Census 2023 counties, clipped to the story box, zoom 4-11. Built by tiles/build_base.py.'
```
