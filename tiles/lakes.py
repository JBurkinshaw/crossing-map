"""The base map's lake layer: INEGI's water bodies in Mexico, Natural Earth's lakes elsewhere.

Called by tiles/build_base.py. Natural Earth's 1:10 million lakes are coarse outlines: the Laguna de Babícora's
spills over the plain where the book's riders camp on its shore. In Mexico the lakes come from the water-body
polygons of INEGI's Red Hidrográfica 1:50,000 (the `_ha` layers): every perennial body of at least MIN_PERENNIAL_KM2,
and intermittent ones of at least MIN_INTERMITTENT_KM2 (smaller ones are mostly stock tanks), marked `i` so the
style can draw them lighter. Natural Earth's lakes are kept outside Mexico.
"""

import json
import zipfile
from pathlib import Path

import shapely
from shapely.geometry import mapping, shape

from creeks import mexico
from rivers import INEGI, NE, read

MIN_PERENNIAL_KM2 = 0.1
MIN_INTERMITTENT_KM2 = 1.0
# Islets and marsh patches smaller than this (km²) are filled: INEGI draws hundreds in the Laguna de Babícora,
# which would speckle the lake at every zoom.
MAX_HOLE_KM2 = 0.5
# Square degrees to km² at about 30° N.
KM2 = 111.32 * 111.32 * 0.866


def fill_holes(g: shapely.Geometry) -> shapely.Geometry:
    polygons = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon":
            continue
        keep = [r for r in p.interiors if shapely.Polygon(r).area * KM2 >= MAX_HOLE_KM2]
        polygons.append(shapely.Polygon(p.exterior, keep))
    return shapely.MultiPolygon(polygons) if len(polygons) != 1 else polygons[0]


def write_layer(bbox: list[str], tmp: Path) -> Path:
    """lake.geojson in tmp, for tippecanoe."""
    land = mexico(bbox, tmp)
    features = []
    for g in (shape(f["geometry"]) for f in read(str(NE / "ne_10m_lakes_north_america" / "ne_10m_lakes_north_america.shp"),
                                                  "SELECT name FROM ne_10m_lakes_north_america", bbox, tmp, "ne-lakes")):
        rest = g.difference(land)
        if not rest.is_empty:
            features.append({"type": "Feature", "geometry": mapping(rest), "properties": {}})
    kept = {"perennial": 0, "intermittent": 0}
    for i, zip_path in enumerate(sorted(INEGI.glob("*.zip"))):
        for j, name in enumerate(n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith("_ha.shp")):
            for f in read(f"/vsizip/{zip_path}/{name}", f"SELECT CONDICION FROM {Path(name).stem}", bbox, tmp, f"ha{i}-{j}", latin1=True):
                g = fill_holes(shape(f["geometry"]).buffer(0))
                intermittent = "INTERMITENTE" in (f["properties"]["CONDICION"] or "")
                if g.area * KM2 < (MIN_INTERMITTENT_KM2 if intermittent else MIN_PERENNIAL_KM2):
                    continue
                kept["intermittent" if intermittent else "perennial"] += 1
                features.append({"type": "Feature", "geometry": mapping(shapely.simplify(g, 0.0002)),
                                 "properties": {"i": 1} if intermittent else {}})
    out = tmp / "lake.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"lakes: {kept['perennial']} perennial and {kept['intermittent']} intermittent from INEGI, "
          f"{len(features) - sum(kept.values())} from Natural Earth outside Mexico")
    return out

