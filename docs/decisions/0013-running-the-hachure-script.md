# 0013. Running the hachure script unmodified

Status: accepted (2026-11-11)
Phase: P1

## Context

The plan (section 5.2, "D-relief-hachures") runs Daniel Huffman's Hachures script unmodified for the relief experiment, and vendors an adapted copy only if hachures are chosen. The script is GPL-3.0 and written for the QGIS 3 Python console. It reads the selected layer through `iface.activeLayer()`, and relies on the console's pre-imported `qgis.core`, Qt and `processing`. It also calls the Processing algorithms `qgis:slope` and `qgis:aspect`, which QGIS 4 renamed `native:slope` and `native:aspect`. This machine has QGIS 4.2.3.

## Decision

`pipeline/relief/run_hachures.py` (ours, MIT) runs the script file unchanged in a headless QGIS 4 process:

- It recreates the console namespace: `qgis.core`, Qt, `processing`, and an `iface` whose `activeLayer()` returns the DEM.
- It maps the two renamed algorithm ids when the script calls `processing.run`.
- It sets the script's user-parameter lines (spacing, slope range, number of checks, `thickness_layer`), which is how the script is meant to be configured.
- It saves the script's "Main Hachures" and "Split Hachures" layers as GeoJSON in WGS 84.

The script itself lives in `private/cache/hachures/`, pinned to upstream commit `3170a3f`, and is not committed. The GPL code and the MIT harness meet only inside one process run.

## Alternatives

- Run it by hand in the QGIS desktop: works, but six runs per settings change is slow and unrepeatable.
- Edit the script for QGIS 4 and headless use now: that is the vendoring step, which waits until the experiment picks hachures.

## Consequences

The experiment's hachures are reproducible from the command line. The script's slope limits are percentages of each DEM's own range, so the settings for each test area do not transfer to another extent: the production run needs the adapted copy with absolute limits, as the plan says.
