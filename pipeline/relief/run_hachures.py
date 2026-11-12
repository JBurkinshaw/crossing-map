"""Run Daniel Huffman's Hachures script, unmodified, outside the QGIS desktop.

Run with QGIS's Python (QGIS 4), not the uv pipeline:
  PYTHONPATH=$QGIS/share/qgis/python QT_QPA_PLATFORM=offscreen \\
    $QGIS/bin/python3.14 pipeline/relief/run_hachures.py DEM.tif OUT_PREFIX \\
    [--min-spacing 2] [--max-spacing 6] [--checks 125] [--min-slope 20] [--max-slope 75]

The script (GPL-3.0, private/cache/hachures/, pinned in COMMIT there) expects
the QGIS desktop: a selected layer from `iface`, and QGIS 3 algorithm names.
This harness supplies both from outside the script, sets the script's own
user-parameter lines (its documented way of being configured), runs it, and
writes its two output layers to OUT_PREFIX-main.geojson and
OUT_PREFIX-split.geojson in WGS 84. The script file itself is not changed;
the GPL code and this MIT harness meet only at exec() inside one process run.
"""

import argparse
import re
import sys
import time
from pathlib import Path

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsProject,
    QgsRasterLayer,
    QgsVectorFileWriter,
)

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "private" / "cache" / "hachures" / "Hachure Generator.py"
# QGIS 4 renamed these Processing algorithms; the script uses the QGIS 3 names.
RENAMED = {"qgis:slope": "native:slope", "qgis:aspect": "native:aspect"}


class _MessageBar:
    def pushMessage(self, title, text, *args, **kwargs):
        print(f"[{title}] {text}", file=sys.stderr)


class _Iface:
    """The two parts of the desktop interface the script uses."""

    def __init__(self, layer):
        self._layer = layer

    def activeLayer(self):
        return self._layer

    def messageBar(self):
        return _MessageBar()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dem")
    ap.add_argument("out_prefix")
    ap.add_argument("--min-spacing", type=float, default=2)
    ap.add_argument("--max-spacing", type=float, default=6)
    ap.add_argument("--checks", type=int, default=125)
    ap.add_argument("--min-slope", type=float, default=20)
    ap.add_argument("--max-slope", type=float, default=75)
    a = ap.parse_args()

    app = QgsApplication([], False)
    app.initQgis()
    sys.path.append(str(Path(QgsApplication.prefixPath()).parent / "share" / "qgis" / "python" / "plugins"))
    from processing.core.Processing import Processing

    Processing.initialize()
    import qgis.utils
    from qgis import processing

    dem = QgsRasterLayer(a.dem, "DEM")
    if not dem.isValid():
        sys.exit(f"Cannot read {a.dem}")
    qgis.utils.iface = _Iface(dem)
    run = processing.run
    processing.run = lambda alg, params, *rest, **kw: run(RENAMED.get(alg, alg), params, *rest, **kw)

    source = SCRIPT.read_text(encoding="utf-8")
    settings = {
        "min_hachure_spacing": a.min_spacing,
        "max_hachure_spacing": a.max_spacing,
        "spacing_checks": a.checks,
        "min_slope_val": a.min_slope,
        "max_slope_val": a.max_slope,
        "thickness_layer": True,
    }
    for name, value in settings.items():
        source, n = re.subn(rf"^{name} = .*$", f"{name} = {value!r}", source, count=1, flags=re.M)
        if n != 1:
            sys.exit(f"Setting {name} not found in the script")

    started = time.monotonic()
    try:
        # The script is written for the QGIS Python console, which pre-imports qgis.core, Qt and
        # processing and predefines `iface`; the script relies on all of these before its own imports.
        console = {"__name__": "__main__"}
        exec("from qgis.core import *\nfrom qgis.PyQt.QtCore import *\nfrom qgis.PyQt.QtGui import *\nfrom qgis import processing", console)
        console["iface"] = qgis.utils.iface
        exec(compile(source, str(SCRIPT), "exec"), console)
        print(f"Script ran in {time.monotonic() - started:.0f} s")

        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        for layer_name, suffix in (("Main Hachures", "main"), ("Split Hachures", "split")):
            layers = QgsProject.instance().mapLayersByName(layer_name)
            if not layers:
                sys.exit(f"The script made no '{layer_name}' layer")
            opts = QgsVectorFileWriter.SaveVectorOptions()
            opts.driverName = "GeoJSON"
            out = f"{a.out_prefix}-{suffix}.geojson"
            opts.ct = QgsCoordinateTransform(layers[0].crs(), wgs84, QgsProject.instance())
            err = QgsVectorFileWriter.writeAsVectorFormatV3(layers[0], out, QgsCoordinateTransformContext(), opts)
            print(f"{out}: {layers[0].featureCount()} features ({err[0]})")
    finally:
        app.exitQgis()


if __name__ == "__main__":
    main()
