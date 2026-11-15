"""Which way each named pass runs, for setting its name across the saddle as the Wheeler sheets do.

Run from the repo root:
    uv run --project pipeline python -m crossing.pass_lines

Wheeler letters a pass in small capitals along the road through it (RATON PASS; review/stage-8/wheeler/README.md).
For every named pass in the story box (the named pass glyphs in data/mountain_glyphs.geojson, and the passes the
book names in data/places.geojson), this finds a short line through the pass:

- along the base map's road (Natural Earth roads, as the map draws them) where one passes within ROAD_M of the
  saddle: the road's own course, PASS_HALF_M each way from the point nearest the saddle;
- else across the saddle, the way a path goes over: at a pass the ground curves up along the ridge and down along
  the way over, so the way over is the direction of most negative curvature (the Hessian's smaller eigenvalue) of
  the Copernicus DEM, smoothed to about 150 m.

The map sets each name as a point label rotated to its line (a 5 km line is shorter than the name below zoom 11,
and MapLibre drops a line label longer than its line), so the site's copy, site/public/labels/passes.geojson,
holds one point per pass, at the middle of its line, with `rotate`: the line's angle on a north-up Web Mercator
map, in degrees clockwise from east, turned to read left to right. The lab's type card (review/stage-9/wheeler-type/
type_lab_data.py) uses lines() for the lines themselves.

A pass the book names takes the place's name, first_seen and place_ref, so its name shows only once the reader
has reached it; a gazetteer pass takes its glyph's first_seen (1-01, the land itself).
"""

import json
import math
import tempfile
from pathlib import Path

import numpy as np
import rasterio
import shapely
import shapely.ops
from pyproj import Geod
from rasterio.windows import from_bounds
from scipy import ndimage

from crossing import basemap
from crossing.dem import COPERNICUS, COPERNICUS_REGION, build_vrt, tiles
from crossing.paths import DATA, SITE_PUBLIC, STORY_BOX
from crossing.vector import read

OUT = SITE_PUBLIC / "labels" / "passes.geojson"
GEOD = Geod(ellps="WGS84")
ROAD_M = 1000  # a road this close to the saddle is taken to cross the pass
PASS_HALF_M = 2500  # pass lines run this far each way from the saddle
SAME_PASS_KM = 5  # a book pass and a glyph of the same name this close are one pass
M_PER_DEG_LAT = 110850


def named_passes(bbox=STORY_BOX) -> list[dict]:
    """Every named pass in the box: name, lon, lat, first_seen and place_ref (None for a gazetteer pass)."""
    glyphs = [f for f in json.loads((DATA / "mountain_glyphs.geojson").read_text(encoding="utf-8"))["features"]
              if f["properties"]["kind"] == "pass" and f["properties"]["name"] != "Unnamed pass"]
    places = [f for f in json.loads((DATA / "places.geojson").read_text(encoding="utf-8"))["features"]
              if f["properties"]["kind"] == "pass"]
    out = {}
    for f in glyphs:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        out[p["id"]] = {"name": p["name"], "lon": lon, "lat": lat, "first_seen": p["first_seen"], "place_ref": None}
    for f in places:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        twin = next((k for k, g in out.items() if g["name"] == p["name"]
                     and GEOD.inv(lon, lat, g["lon"], g["lat"])[2] <= SAME_PASS_KM * 1000), None)
        # The glyph's point is the DEM's saddle; the book's name and reading position win.
        at = out.pop(twin) if twin else {"lon": lon, "lat": lat}
        out[p["id"]] = at | {"name": p["name"], "first_seen": p["first_seen"], "place_ref": p["id"]}
    w, s, e, n = bbox
    return sorted((v for v in out.values() if w <= v["lon"] <= e and s <= v["lat"] <= n),
                  key=lambda v: (v["name"], v["lon"]))


def roads(bbox, tmp: Path) -> list[shapely.LineString]:
    name, sql, _ = basemap.LAYERS["road"]
    features = read(basemap.shapefile(name), sql, bbox, tmp / "roads.geojson")
    merged = shapely.line_merge(shapely.unary_union([shapely.geometry.shape(f["geometry"]) for f in features]))
    return [g for g in getattr(merged, "geoms", [merged]) if g.geom_type == "LineString"]


def saddle_line(dem, lon: float, lat: float) -> shapely.LineString:
    """A line across the saddle, along the direction of most negative curvature of the smoothed DEM."""
    kx = 111320 * math.cos(math.radians(lat))
    r = 1500
    win = from_bounds(lon - r / kx, lat - r / M_PER_DEG_LAT, lon + r / kx, lat + r / M_PER_DEG_LAT, dem.transform)
    z = ndimage.gaussian_filter(dem.read(1, window=win, boundless=True).astype(float), 5)
    cell_x, cell_y = abs(dem.transform.a) * kx, abs(dem.transform.e) * M_PER_DEG_LAT
    zy, zx = np.gradient(z, cell_y, cell_x)
    zyy, zyx = np.gradient(zy, cell_y, cell_x)
    _, zxx = np.gradient(zx, cell_y, cell_x)
    cy, cx = z.shape[0] // 2, z.shape[1] // 2
    # Rows run south, so the north component is minus the row component.
    hessian = np.array([[zxx[cy, cx], -zyx[cy, cx]], [-zyx[cy, cx], zyy[cy, cx]]])
    _, vec = np.linalg.eigh(hessian)
    ux, uy = vec[:, 0]
    return shapely.LineString([(lon - ux * PASS_HALF_M / kx, lat - uy * PASS_HALF_M / M_PER_DEG_LAT),
                               (lon + ux * PASS_HALF_M / kx, lat + uy * PASS_HALF_M / M_PER_DEG_LAT)])


def lines(bbox=STORY_BOX) -> list[tuple[dict, shapely.LineString, str]]:
    """Each named pass in the box with its line and how the line was found ('road' or 'saddle')."""
    passes = named_passes(bbox)
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        w, s, e, n = bbox
        near_roads = roads((w - 0.1, s - 0.1, e + 0.1, n + 0.1), Path(tmp))
        vrt = build_vrt(Path(tmp) / "dem.vrt", tiles(COPERNICUS, COPERNICUS_REGION))
        with rasterio.open(vrt) as dem:
            for p in passes:
                point = shapely.Point(p["lon"], p["lat"])
                road = min(near_roads, key=lambda g: g.distance(point)) if near_roads else None
                near = shapely.ops.nearest_points(road, point)[0] if road else None
                if near and GEOD.inv(p["lon"], p["lat"], near.x, near.y)[2] <= ROAD_M:
                    # The road's own course, PASS_HALF_M each way along it from the point nearest the saddle.
                    at = road.project(near)
                    step = PASS_HALF_M / 111320 / math.cos(math.radians(p["lat"]))
                    out.append((p, shapely.ops.substring(road, at - step, at + step), "road"))
                else:
                    out.append((p, saddle_line(dem, p["lon"], p["lat"]), "saddle"))
    return out


def merc_y(lat: float) -> float:
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def rotate(line: shapely.LineString) -> float:
    """The line's end-to-end angle on a north-up Web Mercator map, degrees clockwise from east, in [-90, 90)."""
    (x0, y0), (x1, y1) = line.coords[0], line.coords[-1]
    angle = math.degrees(math.atan2(-(merc_y(y1) - merc_y(y0)), math.radians(x1 - x0)))
    return round((angle + 90) % 180 - 90, 1)


def main() -> None:
    features = []
    for p, line, via in lines():
        mid = line.interpolate(0.5, normalized=True)
        props = {"name": p["name"], "rotate": rotate(line), "via": via, "first_seen": p["first_seen"],
                 "place_ref": p["place_ref"]}
        point = {"type": "Point", "coordinates": [round(mid.x, 5), round(mid.y, 5)]}
        features.append({"type": "Feature", "geometry": point, "properties": props})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False,
                              separators=(",", ":")) + "\n", encoding="utf-8")
    via = {v: sum(f["properties"]["via"] == v for f in features) for v in ("road", "saddle")}
    print(f"{len(features)} passes ({via['road']} along a road, {via['saddle']} across the saddle) -> {OUT}")


if __name__ == "__main__":
    main()
