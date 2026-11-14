"""Build the QGIS project for finishing the inferred areas by hand: pipeline/qgis/areas.qgs (decision 0020).

The editable layer is the seed itself, pipeline/seeds/areas.geojson. Set an area's draft_confidence to "checked" when
it is finished, so `crossing.area_drafts --force` keeps it.

Run from the repo root with the QGIS 4 environment (decision 0015), after `crossing.area_drafts --qgis`:
    PYTHONPATH=$QGIS_ENV/share/qgis/python QT_QPA_PLATFORM=offscreen \
        $QGIS_ENV/bin/python3.14 pipeline/src/crossing/area_drafts_qgis.py

Every path in the project is relative. The hillshade (layers/dem.vrt, over private/cache/dem), the streams and the
stops' circles (private/overnight/areas/) live under private/, so they show only on a machine with those caches.
"""

import sys
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsAttributeEditorContainer,
    QgsAttributeEditorField,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsEditorWidgetSetup,
    QgsFillSymbol,
    QgsHillshadeRenderer,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsProject,
    QgsProperty,
    QgsRasterLayer,
    QgsRectangle,
    QgsReferencedRectangle,
    QgsRendererCategory,
    QgsSymbolLayer,
    QgsTextFormat,
    QgsTolerance,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtGui import QColor

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "pipeline" / "qgis"
PROJECT = OUT / "areas.qgs"
SEED = REPO / "pipeline" / "seeds" / "areas.geojson"
STREAMS = REPO / "private" / "overnight" / "areas" / "streams.gpkg"
CIRCLES = REPO / "private" / "overnight" / "areas" / "circles.geojson"
CONFIDENCE = {"high": "#1a9850", "medium": "#f39c12", "low": "#d73027", "kept": "#7f7f7f", "checked": "#2166ac"}


def vector(path: Path, name: str, subset: str | None = None) -> QgsVectorLayer:
    layer = QgsVectorLayer(str(path), name, "ogr")
    if not layer.isValid():
        sys.exit(f"Could not open {path}")
    if subset:
        layer.setSubsetString(subset)
    return layer


def drafts_layer() -> QgsVectorLayer:
    layer = vector(SEED, "Draft areas (edit these; pipeline/seeds)")
    cats = []
    for value, colour in CONFIDENCE.items():
        sym = QgsFillSymbol.createSimple({"color": colour, "outline_color": colour, "outline_width": "0.6"})
        sym.setOpacity(1)
        fill = QColor(colour)
        fill.setAlpha(90)  # about 35%
        sym.symbolLayer(0).setFillColor(fill)
        cats.append(QgsRendererCategory(value, sym, value))
    layer.setRenderer(QgsCategorizedSymbolRenderer("draft_confidence", cats))

    # Labels: the area id, so each area can be found in the report and the contact sheets.
    pal = QgsPalLayerSettings()
    pal.fieldName = "id"
    fmt = QgsTextFormat()
    fmt.setSize(8)
    fmt.buffer().setEnabled(True)
    pal.setFormat(fmt)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)

    # The form: what the draft is and why. The book's reasoning is on the stop (Identify on the stops layer).
    fields = layer.fields()
    multiline = QgsEditorWidgetSetup("TextEdit", {"IsMultiline": True, "UseHtml": False})
    layer.setEditorWidgetSetup(fields.indexOf("draft_rule"), multiline)
    layer.setEditorWidgetSetup(
        fields.indexOf("draft_confidence"), QgsEditorWidgetSetup("ValueMap", {"map": [{k: k} for k in CONFIDENCE]})
    )
    form = layer.editFormConfig()
    form.setLayout(Qgis.AttributeFormLayout.DragAndDrop)
    root = form.invisibleRootContainer()
    root.clear()

    def tab(title: str, names: list[str]) -> None:
        box = QgsAttributeEditorContainer(title, root)
        for n in names:
            box.addChildElement(QgsAttributeEditorField(n, fields.indexOf(n), box))
        root.addChildElement(box)

    tab("Draft", ["id", "stop", "draft_confidence", "draft_rule", "straight_road"])
    for n in ("id", "stop"):
        form.setReadOnly(fields.indexOf(n), True)
    layer.setEditFormConfig(form)
    return layer


def main() -> None:
    app = QgsApplication([], False)
    app.initQgis()
    project = QgsProject.instance()
    project.clear()
    project.setFileName(str(PROJECT))
    project.setFilePathStorage(Qgis.FilePathType.Relative)
    crs = QgsCoordinateReferenceSystem("EPSG:32612")  # UTM 12N, as the relief runs use
    project.setCrs(crs)
    project.setTitle("The Crossing: inferred areas to finish by hand (decision 0008)")

    # Hillshade from the cached Copernicus tiles. The VRT is in degrees, so the z factor turns metres into degrees
    # (1 / 111,320) with an exaggeration of two.
    dem = QgsRasterLayer(str(OUT / "layers" / "dem.vrt"), "Hillshade (needs private/cache/dem)")
    if dem.isValid():
        shade = QgsHillshadeRenderer(dem.dataProvider(), 1, 315, 45)
        shade.setZFactor(2 / 111_320)
        shade.setMultiDirectional(True)
        dem.setRenderer(shade)
        dem.renderer().setOpacity(0.85)
    else:
        print("warning: the hillshade VRT did not open (are the DEM tiles in private/cache/dem?)")

    streams = QgsVectorLayer(f"{STREAMS}|layername=streams", "Streams (INEGI, NHD; needs private/)", "ogr")
    line = QgsLineSymbol.createSimple({"color": "#2b6cb0", "width": "0.25"})
    line.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.Property.StrokeWidth, QgsProperty.fromExpression('0.1 + 0.12 * ("ord" - 2)')
    )
    streams.renderer().setSymbol(line)

    data = REPO / "data"
    journeys = vector(data / "journeys.geojson", "Journeys (data/, read only)")
    journeys.renderer().setSymbol(
        QgsLineSymbol.createSimple({"color": "#7f2704", "width": "0.5", "line_style": "dash"})
    )
    stops = vector(data / "stops.geojson", "Stops (data/, read only)")
    stops.renderer().setSymbol(
        QgsMarkerSymbol.createSimple(
            {"name": "circle", "color": "black", "size": "1.6", "outline_color": "white", "outline_width": "0.3"}
        )
    )
    circles = vector(CIRCLES, "Stops' circles (upper bound; needs private/)")
    circles.renderer().setSymbol(
        QgsFillSymbol.createSimple(
            {"style": "no", "outline_color": "#55555599", "outline_width": "0.3", "outline_style": "dash"}
        )
    )
    regions = vector(data / "areas.geojson", "Regions (data/, read only)", "\"kind\" = 'region'")
    regions.renderer().setSymbol(
        QgsFillSymbol.createSimple({"style": "no", "outline_color": "#1a9850", "outline_width": "0.6"})
    )
    babicora = vector(
        OUT / "babicora-compare.geojson",
        "La Babícora, four municipios (alternative)",
        "\"kind\" IN ('region-alternative', 'municipio')",
    )
    babicora.renderer().setSymbol(
        QgsFillSymbol.createSimple(
            {"style": "no", "outline_color": "#7b3294", "outline_width": "0.5", "outline_style": "dot"}
        )
    )
    drafts = drafts_layer()

    for read_only in (journeys, stops, circles, regions, babicora, streams):
        read_only.setReadOnly(True)
    for layer in (dem, streams, babicora, regions, journeys, circles, drafts, stops):
        if layer.isValid():
            project.addMapLayer(layer)

    # Snapping on, to vertices and segments of every layer, so edits can follow streams, roads and old outlines.
    snap = project.snappingConfig()
    snap.setEnabled(True)
    snap.setMode(Qgis.SnappingMode.AllLayers)
    snap.setTypeFlag(Qgis.SnappingTypes(Qgis.SnappingType.Vertex | Qgis.SnappingType.Segment))
    snap.setTolerance(12)
    snap.setUnits(QgsTolerance.UnitType.Pixels)
    snap.setIntersectionSnapping(True)
    project.setSnappingConfig(snap)
    project.setTopologicalEditing(False)

    ext = QgsCoordinateTransform(drafts.crs(), crs, project).transformBoundingBox(drafts.extent())
    project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(QgsRectangle(ext), crs))
    if not project.write():
        sys.exit(f"Could not write {PROJECT}")
    print(f"Wrote {PROJECT.relative_to(REPO)}: {len(project.mapLayers())} layers")
    app.exitQgis()


if __name__ == "__main__":
    main()
