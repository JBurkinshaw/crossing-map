"""The base map's lake layer: INEGI's water bodies in Mexico, Natural Earth's lakes elsewhere.

Called by tiles.build_base. Natural Earth's 1:10 million lakes are coarse outlines: the Laguna de Babícora's
spills over the plain where the book's riders camp on its shore. In Mexico the lakes come from the water-body
polygons of INEGI's Red Hidrográfica 1:50,000 (the `_ha` layers): every perennial body of at least MIN_PERENNIAL_KM2,
and intermittent ones of at least MIN_INTERMITTENT_KM2 (smaller ones are mostly stock tanks), marked `i` so the
style can draw them lighter. Natural Earth's lakes are kept outside Mexico.

In the US the closed valleys of the bootheel and southern Arizona (the Animas, the Playas, Willcox) drain to dry
lakes, which Natural Earth leaves out, so their washes would end on bare ground. NHD's playas (ftype 361) and
intermittent lakes (fcode 39004) of at least MIN_INTERMITTENT_KM2 are added outside Mexico, marked `i` like
INEGI's. NHD's reservoirs are left out: nearly all are stock tanks and dams built since the 1940s.

Reservoirs built after the book's years are left out on both sides of the border: the water bodies listed in
LATER_RESERVOIRS with action "drop" (decision 0031). tiles.later_reservoirs drafts that list from the Global Dam
Watch database; the list is then curated by hand.
"""

import csv
import json
import zipfile
from collections.abc import Sequence
from pathlib import Path

import shapely
from shapely.geometry import mapping, shape

from crossing.basemap import shapefile
from crossing.hydro import INEGI, NHD
from crossing.paths import SEEDS
from crossing.vector import read

MIN_PERENNIAL_KM2 = 0.1
MIN_INTERMITTENT_KM2 = 1.0
# Islets and marsh patches smaller than this (km²) are filled: INEGI draws hundreds in the Laguna de Babícora,
# which would speckle the lake at every zoom.
MAX_HOLE_KM2 = 0.5
# NHD water bodies taken: playas, and lakes whose water comes and goes.
NHD_DRY_LAKES = "ftype = 361 OR fcode = 39004"
# Reservoirs built after the book, each by a point inside the lake polygon it floods.
LATER_RESERVOIRS = SEEDS / "later_reservoirs.csv"
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


def dropped_points() -> list[shapely.Point]:
    """The points of the reservoirs LATER_RESERVOIRS drops."""
    with LATER_RESERVOIRS.open(newline="") as f:
        return [shapely.Point(float(r["lon"]), float(r["lat"])) for r in csv.DictReader(f) if r["action"] == "drop"]


def write_layer(bbox: Sequence, mexico: shapely.Geometry, tmp: Path) -> Path:
    """lake.geojson in tmp, for tippecanoe, without the reservoirs built after the book."""
    drop = dropped_points()
    features = [f for f in lake_features(bbox, mexico, tmp)
                if not any(shape(f["geometry"]).intersects(p) for p in drop)]
    out = tmp / "lake.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"lakes: {len(features)} drawn, reservoirs built after the book left out where {len(drop)} points fall")
    return out


def lake_features(bbox: Sequence, mexico: shapely.Geometry, tmp: Path) -> list[dict]:
    """Every lake the base map could draw: INEGI's, NHD's dry lakes and Natural Earth's."""
    features = []
    ne = read(shapefile("ne_10m_lakes_north_america"), "SELECT name FROM ne_10m_lakes_north_america", bbox,
              tmp / "ne-lakes.geojson")
    for g in (shape(f["geometry"]) for f in ne):
        rest = g.difference(mexico)
        if not rest.is_empty:
            features.append({"type": "Feature", "geometry": mapping(rest), "properties": {}})
    kept = {"perennial": 0, "intermittent": 0}
    for i, zip_path in enumerate(sorted(INEGI.glob("*.zip"))):
        for j, name in enumerate(n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith("_ha.shp")):
            sql = f"SELECT CONDICION FROM {Path(name).stem}"
            for f in read(f"/vsizip/{zip_path}/{name}", sql, bbox, tmp / f"ha{i}-{j}.geojson", latin1=True):
                g = fill_holes(shape(f["geometry"]).buffer(0))
                intermittent = "INTERMITENTE" in (f["properties"]["CONDICION"] or "")
                if g.area * KM2 < (MIN_INTERMITTENT_KM2 if intermittent else MIN_PERENNIAL_KM2):
                    continue
                kept["intermittent" if intermittent else "perennial"] += 1
                features.append({"type": "Feature", "geometry": mapping(shapely.simplify(g, 0.0002)),
                                 "properties": {"i": 1} if intermittent else {}})
    dry = 0
    for i, shp_dir in enumerate(sorted(NHD.glob("*/Shape"))):
        sql = f"SELECT ftype FROM NHDWaterbody WHERE {NHD_DRY_LAKES}"
        for f in read(shp_dir / "NHDWaterbody.shp", sql, bbox, tmp / f"nhd-dry-{i}.geojson"):
            g = fill_holes(shape(f["geometry"]).buffer(0)).difference(mexico)
            if g.is_empty or g.area * KM2 < MIN_INTERMITTENT_KM2:
                continue
            dry += 1
            features.append({"type": "Feature", "geometry": mapping(shapely.simplify(g, 0.0002)),
                             "properties": {"i": 1}})
    print(f"lakes: {kept['perennial']} perennial and {kept['intermittent']} intermittent from INEGI, "
          f"{dry} dry lakes from NHD, {len(features) - sum(kept.values()) - dry} from Natural Earth outside Mexico")
    return features

