# 0020. Landform names along computed axes

Status: proposed (2026-11-14)
Phase: P1

## Context

The Wheeler Survey sheets letter a range, valley, plain or mesa in spaced roman capitals laid along the landform's long axis, spread over most of its length (`review/stage-8/wheeler/README.md`). Our map sets these names as horizontal point labels. To letter them along the landform we need a line for each one, and no open source gives such lines for our area. The gazetteers give points (GNIS, GeoNames, INEGI). GNIS valleys also give a head point beside the mouth. GMBA Mountain Inventory v2 gives range outlines, but only for some US ranges and a few in Sonora: the bootheel's Animas, San Luis and Hatchet ranges, and most Mexican sierras, are not in it.

## Decision

`crossing.landform_axes` writes `data/landforms.geojson`, one label line per landform in the box 112° to 104° W, 28° to 34° N, and records how each line was made in its `axis` property:

- **gmba:** a range with a GMBA outline of the same name within 10 km gets the principal axis of that outline (CC BY 4.0).
- **gnis:** a GNIS valley gets the line from its mouth (primary point) to its head (source point) (public domain).
- **dem:** every other landform gets the principal axis of the region of the Copernicus DEM around its gazetteer point: ground standing above the local valley floor for a range, flat ground near the top for a mesa or plateau, flat low ground for a plain. Where a range's region runs on past a 30 km window, as most sierras of the Sierra Madre do, the line takes the grain of the ground within 12 km of the point and has certainty `inferred`.
- A hand-edit table, `pipeline/seeds/landform_axes.toml`, applied last, moves, turns, lengthens, bends, drops or keeps lines, each with a reason that is published in `reasoning`.

The book's ranges, valleys and plains (in `places.geojson`) always get a line, under the book's name and from the place's `first_seen`. Landforms the book never names get `first_seen` 1-01. They are kept by size, each kind to a cap, with a minimum spacing between lines of one kind. The rule is in the module's docstring.

## Alternatives

- **Hand-drawn lines for every name.** Best result, but there are about 300 names, and the method would not be repeatable.
- **GNIS multipoints.** The full GNIS model stores one point per 7.5′ quad a feature crosses. This is coarse, US only, and needs a separate large download.
- **OpenStreetMap ridge and valley lines.** Sparse here (32 named ridges in the box) and ODbL.
- **Point labels, as now.** They do not read as part of the land, and in the tilted view they lie at odd angles to the ridges.

## Consequences

- Every line is an estimate. Lines from the DEM in the Sierra Madre show the local grain, not a whole range. The book's landforms in the Wheeler test area were checked by eye on a hillshade (`review/stage-9/wheeler-type/`), and the others were not.
- The Credits page must add GMBA (CC BY 4.0). GeoNames, GNIS and the Copernicus DEM are already credited.
- The layer has a GeoParquet copy like the other story layers (decision 0009). The site does not draw it yet. The lab's Wheeler section shows it for the test area.
