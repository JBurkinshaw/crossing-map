"""Data for the lab's type-hierarchy card (site/src/lab/wheeler/subset/type.ts), for the Wheeler test area only.

Run from the repo root: uv run --project pipeline python review/stage-9/wheeler-type/type_lab_data.py
Reads data/landforms.geojson, data/mountain_glyphs.geojson, data/places.geojson, the base tiles in
site/public/tiles/base.pmtiles (rivers and roads, through GDAL's PMTiles driver) and the Copernicus DEM.
Writes three small GeoJSON files to site/public/lab/wheeler/:

  type-landforms.geojson  the landform lines, clipped to the test area, with len_m and mpp0 for the clipped part,
                          so a long valley (the Animas, 136 km) is lettered on the stretch the reader is looking at;
  type-rivers.geojson     the base map's major river-label lines (Natural Earth names), merged and clipped;
  type-passes.geojson     a short line through each named pass: along the base map's road where one passes within
                          ROAD_M of the saddle, else across the saddle, the way a path would cross it.
"""

import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import rasterio
import shapely
import shapely.ops
from pyproj import Geod
from rasterio.windows import from_bounds
from scipy import ndimage

from crossing.dem import COPERNICUS, COPERNICUS_REGION, build_vrt, tiles
from crossing.paths import DATA, REPO
from crossing.vector import chaikin

TEST = (-109.6, 30.5, -108.4, 31.6)
OUT = REPO / "site" / "public" / "lab" / "wheeler"
BASE = REPO / "site" / "public" / "tiles" / "base.pmtiles"
GEOD = Geod(ellps="WGS84")
ROAD_M = 1000  # a road this close to the saddle is taken to cross the pass
PASS_HALF_M = 2500  # pass lines run this far each way from the saddle
MIN_M = 5000  # clipped pieces shorter than this are dropped: no name fits them
# GNIS calls draws, canyons and washes "Valley" too; these are lettered small, like creeks, not in capitals.
MINOR_VALLEY = ("Draw", "Canyon", "Cañón", "Wash", "Arroyo")


def length_m(line: shapely.LineString) -> float:
    return GEOD.geometry_length(line)


def mpp0(line: shapely.LineString) -> int:
    return round(156543.03 * math.cos(math.radians(line.interpolate(0.5, normalized=True).y)))


def rounded(geom: shapely.Geometry) -> dict:
    return shapely.geometry.mapping(shapely.set_precision(geom, 1e-5))


def tile_layer(layer: str, zoom: int) -> list[dict]:
    """The features of one layer of the base tiles around the test area, at one zoom, in lon/lat."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / f"{layer}.geojson"
        w, s, e, n = TEST
        subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-oo", f"ZOOM_LEVEL={zoom}", "-t_srs", "EPSG:4326",
                        "-spat_srs", "EPSG:4326", "-spat", str(w - 0.2), str(s - 0.2), str(e + 0.2), str(n + 0.2),
                        str(out), str(BASE), layer], check=True, capture_output=True)
        return json.loads(out.read_text())["features"]


def longest(geom: shapely.Geometry) -> shapely.LineString | None:
    parts = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "LineString" and not g.is_empty]
    return max(parts, key=length_m) if parts else None


def landforms() -> list[dict]:
    out = []
    for f in json.loads((DATA / "landforms.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        line = longest(shapely.clip_by_rect(shapely.geometry.shape(f["geometry"]), *TEST))
        if line is None or length_m(line) < MIN_M:
            continue
        minor = p["kind"] == "valley" and any(w in p["name"] for w in MINOR_VALLEY)
        props = {"id": p["id"], "name": p["name"], "kind": p["kind"], "tier": "minor" if minor else "major",
                 "len_m": round(length_m(line)), "mpp0": mpp0(line), "first_seen": p["first_seen"]}
        out.append({"type": "Feature", "geometry": rounded(line), "properties": props})
    return out


def rivers() -> list[dict]:
    # Zoom 8: one or two tiles cover the test area, so few cuts to mend, and the label lines are already smoothed.
    by_name: dict[str, list] = {}
    for f in tile_layer("river_label", 8):
        if f["properties"].get("rank") == "major":
            by_name.setdefault(f["properties"]["name"], []).append(shapely.geometry.shape(f["geometry"]))
    out = []
    for name, geoms in sorted(by_name.items()):
        # Simplified and rounded again: the tile's geometry is quantised, and its small kinks stop a name in large
        # spaced capitals from fitting along the river (MapLibre's text-max-angle).
        merged = shapely.line_merge(shapely.unary_union(geoms))
        merged = shapely.MultiLineString([chaikin(np.asarray(g.simplify(0.02).coords), 3)
                                          for g in getattr(merged, "geoms", [merged])])
        for line in getattr(shapely.clip_by_rect(merged, *TEST), "geoms", [shapely.clip_by_rect(merged, *TEST)]):
            if line.geom_type == "LineString" and length_m(line) >= MIN_M:
                props = {"name": name, "len_m": round(length_m(line)), "mpp0": mpp0(line), "first_seen": "1-01"}
                out.append({"type": "Feature", "geometry": rounded(line), "properties": props})
    return out


def saddle_line(dem, lon: float, lat: float) -> shapely.LineString:
    """A line across the saddle: at a pass the ground curves up along the ridge and down along the way over, so
    the way over is the direction of the most negative curvature (the Hessian's smaller eigenvalue) of the DEM,
    smoothed to about 150 m."""
    kx = 111320 * math.cos(math.radians(lat))
    r = 1500
    win = from_bounds(lon - r / kx, lat - r / 110850, lon + r / kx, lat + r / 110850, dem.transform)
    z = ndimage.gaussian_filter(dem.read(1, window=win, boundless=True).astype(float), 5)
    cell_x, cell_y = abs(dem.transform.a) * kx, abs(dem.transform.e) * 110850
    zy, zx = np.gradient(z, cell_y, cell_x)
    zyy, zyx = np.gradient(zy, cell_y, cell_x)
    _, zxx = np.gradient(zx, cell_y, cell_x)
    cy, cx = z.shape[0] // 2, z.shape[1] // 2
    # Rows run south, so the north component is minus the row component.
    hessian = np.array([[zxx[cy, cx], -zyx[cy, cx]], [-zyx[cy, cx], zyy[cy, cx]]])
    ev, vec = np.linalg.eigh(hessian)
    ux, uy = vec[:, 0]
    return shapely.LineString([(lon - ux * PASS_HALF_M / kx, lat - uy * PASS_HALF_M / 110850),
                               (lon + ux * PASS_HALF_M / kx, lat + uy * PASS_HALF_M / 110850)])


def passes() -> list[dict]:
    named = []
    for f in json.loads((DATA / "mountain_glyphs.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        if p["kind"] == "pass" and p["name"] != "Unnamed pass":
            named.append((p["name"], *f["geometry"]["coordinates"], p["first_seen"]))
    for f in json.loads((DATA / "places.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        if p["kind"] == "pass" and p["name"] not in {n[0] for n in named}:
            named.append((p["name"], *f["geometry"]["coordinates"], p["first_seen"]))
    named = [n for n in named if TEST[0] <= n[1] <= TEST[2] and TEST[1] <= n[2] <= TEST[3]]
    roads = shapely.line_merge(shapely.unary_union([shapely.geometry.shape(f["geometry"])
                                                    for f in tile_layer("road", 11)]))
    out = []
    with tempfile.TemporaryDirectory() as tmp, \
            rasterio.open(build_vrt(Path(tmp) / "dem.vrt", tiles(COPERNICUS, COPERNICUS_REGION))) as dem:
        for name, lon, lat, first_seen in named:
            point = shapely.Point(lon, lat)
            road = min(getattr(roads, "geoms", [roads]), key=lambda g: g.distance(point))
            near = shapely.ops.nearest_points(road, point)[0]
            if GEOD.inv(lon, lat, near.x, near.y)[2] <= ROAD_M:
                # The road's own course, PASS_HALF_M each way along it from the point nearest the saddle.
                at = road.project(near)
                step = PASS_HALF_M / 111320 / math.cos(math.radians(lat))
                line, via = shapely.ops.substring(road, at - step, at + step), "road"
            else:
                line, via = saddle_line(dem, lon, lat), "saddle"
            props = {"name": name, "via": via, "first_seen": first_seen}
            out.append({"type": "Feature", "geometry": rounded(line), "properties": props})
            print(f"{name}: {via}")
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, features in (("landforms", landforms()), ("rivers", rivers()), ("passes", passes())):
        path = OUT / f"type-{name}.geojson"
        path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"{path.relative_to(REPO)}: {len(features)} features")


if __name__ == "__main__":
    main()
