"""Run the vendored hachure generator (pipeline/relief/hachures/) outside the QGIS desktop.

Run with QGIS's Python (QGIS 4), not the uv pipeline:
  PYTHONPATH=$QGIS/share/qgis/python QT_QPA_PLATFORM=offscreen \\
    $QGIS/bin/python3.14 pipeline/relief/run_hachures.py DEM.tif OUT_PREFIX \\
    [--min-spacing 3] [--max-spacing 8] [--min-slope 10] [--max-slope 40] \\
    [--contour-interval 10] [--seed 1994] [--split]

The generator (GPL-3.0) is written for the QGIS Python console: it reads the
selected layer from `iface` and relies on the console's pre-imported modules.
This harness (MIT) supplies both, passes the settings in a SETTINGS dict, and
writes the "Main Hachures" layer to OUT_PREFIX-main.geojson in WGS 84, plus
"Split Hachures" to OUT_PREFIX-split.geojson with --split. The two meet only at
exec() inside one process run (decision 0015).
"""

import argparse
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
SCRIPT = Path(__file__).resolve().parent / "hachures" / "hachure_generator.py"


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
    ap.add_argument("--min-spacing", type=float, default=3, help="DEM pixels")
    ap.add_argument("--max-spacing", type=float, default=8, help="DEM pixels")
    ap.add_argument("--min-slope", type=float, default=10, help="degrees")
    ap.add_argument("--max-slope", type=float, default=40, help="degrees")
    ap.add_argument("--contour-interval", type=float, default=10, help="DEM units (metres)")
    ap.add_argument("--seed", type=int, default=1994)
    ap.add_argument("--split", action="store_true", help="also write the split, slope-weighted pieces")
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
    settings = {
        "min_hachure_spacing": a.min_spacing,
        "max_hachure_spacing": a.max_spacing,
        "min_slope": a.min_slope,
        "max_slope": a.max_slope,
        "contour_interval": a.contour_interval,
        "thickness_layer": a.split,
        "seed": a.seed,
    }

    started = time.monotonic()
    try:
        # The generator is written for the QGIS Python console, which pre-imports qgis.core, Qt and
        # processing and predefines `iface`; it relies on all of these before its own imports.
        console = {"__name__": "__main__", "SETTINGS": settings}
        exec("from qgis.core import *\nfrom qgis.PyQt.QtCore import *\nfrom qgis.PyQt.QtGui import *\nfrom qgis import processing", console)
        console["iface"] = qgis.utils.iface
        exec(compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec"), console)
        print(f"Script ran in {time.monotonic() - started:.0f} s")

        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        outputs = [("Main Hachures", "main")] + ([("Split Hachures", "split")] if a.split else [])
        for layer_name, suffix in outputs:
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
