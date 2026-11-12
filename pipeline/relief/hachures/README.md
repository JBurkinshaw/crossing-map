# Hachure generator (vendored, GPL-3.0)

`hachure_generator.py` is Daniel Huffman's [Hachures](https://github.com/pinakographos/Hachures) QGIS script, `Hachure Generator.py` at upstream commit `3170a3f0007154b26493039e5e531ab5ed7609da`, lightly adapted. It stays under the GNU General Public License v3 (`LICENSE`, from the same commit). The rest of this repository is MIT; the two meet only when `pipeline/relief/run_hachures.py` runs this file inside one QGIS process (decision 0015).

## Changes from upstream

- The user parameters come from a `SETTINGS` dict passed in by the harness, not from edits to the file.
- The slope limits are absolute, in degrees (`min_slope`, `max_slope`). Upstream takes them as percentages of the lowest and highest slope in each DEM, so the same settings meant different slopes on different extents.
- The contour interval is absolute, in DEM units (`contour_interval`). Upstream sets it to the DEM's elevation range divided by `spacing_checks`.
- The input checks follow: `min_slope` and `max_slope` must lie between 0 and 90, and `contour_interval` must be positive. The `spacing_checks` warnings are gone with the setting.
- `random` is seeded from `SETTINGS["seed"]`, so the one shuffle in the script repeats between runs.
- The slope and aspect algorithms are called by their QGIS 4 names, `native:slope` and `native:aspect` (upstream: `qgis:slope`, `qgis:aspect`).

Everything else, including how hachures are seeded, grown, spaced and split, is upstream's code.
