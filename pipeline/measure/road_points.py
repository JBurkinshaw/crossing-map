"""Points on today's roads used to place three stops (decision 0032), computed so anyone can rerun them.

Run from the repo root: uv run --project pipeline python pipeline/measure/road_points.py

Sources: Census TIGER/Line 2023 roads (Cochise and Hidalgo counties, in private/cache/roads/tiger/) and the
Copernicus GLO-30 DEM mosaic (private/cache/least-cost/dem.vrt). Lengths along a road are geodesic, on the WGS 84
ellipsoid (pyproj.Geod). Coordinates are NAD83 as TIGER gives them, taken as WGS 84 (they differ by about 1 m here).

- The J3 pass: the highest point of Geronimo Trail between 109.1 and 108.95 W, where the old Douglas to
  Cloverdale road crosses the Guadalupe Mountains.
- The SK Bar: the point nine road miles (14.48 km) north from the Parham house (the Cloverdale stop) along the
  Animas Valley road, Cloverdale Rd C001 then Co Rd C001.
- The J4 camp: the point on Apache Pass Road, south of the Bowie stop, where the road enters the Dos Cabezas
  foothills (the first point 100 m above the Bowie stop).
"""

import json
import subprocess

import rasterio
from pyproj import Geod
from shapely.geometry import LineString, Point, shape
from shapely.ops import linemerge, substring

GEOD = Geod(ellps="WGS84")
TIGER = "private/cache/roads/tiger/tl_2023_{}_roads.zip"
DEM = "private/cache/least-cost/dem.vrt"


def road(county: str, names: list[str]) -> list[LineString]:
    layer = f"tl_2023_{county}_roads"
    sql = f"SELECT * FROM {layer} WHERE FULLNAME IN ({', '.join(repr(n) for n in names)})"
    out = subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-dim", "XY", "-sql", sql, "/vsistdout/",
                          f"/vsizip/{TIGER.format(county)}"], check=True, capture_output=True, text=True).stdout
    return [g for f in json.loads(out)["features"] for g in getattr(shape(f["geometry"]), "geoms",
                                                                     [shape(f["geometry"])]) if g.length > 0]


def elevation(points: list[tuple[float, float]]) -> list[float]:
    with rasterio.open(DEM) as dem:
        return [v[0] for v in dem.sample(points)]


def km_along(coords: list[tuple[float, float]]) -> list[float]:
    out, total = [0.0], 0.0
    for (x0, y0), (x1, y1) in zip(coords, coords[1:], strict=False):
        total += GEOD.inv(x0, y0, x1, y1)[2] / 1000
        out.append(total)
    return out


def densify(line: LineString, step_deg: float = 0.0005) -> list[tuple[float, float]]:
    n = max(2, int(line.length / step_deg))
    return [line.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)]


def main() -> None:
    # The J3 pass.
    trail = [p for g in road("04003", ["E Geronimo Trl", "Geronimo Trl"]) + road("35023", ["Geronimo Trl"])
             for p in densify(g) if -109.1 <= p[0] <= -108.95]
    z = elevation(trail)
    top = max(range(len(trail)), key=z.__getitem__)
    print(f"J3 pass: Geronimo Trail's highest point {trail[top][1]:.5f} N, {-trail[top][0]:.5f} W, {z[top]:.0f} m")

    # The SK Bar: nine road miles north from the Cloverdale stop.
    cloverdale = Point(-108.92977, 31.41705)  # the j3-parham-house stop
    valley = linemerge(road("35023", ["Cloverdale Rd C001", "Co Rd C001"]))
    valley = max(getattr(valley, "geoms", [valley]), key=lambda g: g.length)
    start = valley.project(cloverdale)
    part = substring(valley, start, valley.length) if valley.coords[-1][1] > valley.coords[0][1] \
        else substring(valley, 0, start).reverse()
    coords = densify(part, 0.0002)
    along = km_along(coords)
    i = next(k for k, d in enumerate(along) if d >= 9 * 1.609344)
    print(f"SK Bar: {coords[i][1]:.5f} N, {-coords[i][0]:.5f} W, {along[i]:.2f} km by road from the Cloverdale stop")

    # The J4 camp on Apache Pass Road.
    bowie = Point(-109.46, 32.32)
    pass_road = linemerge(road("04003", ["Apache Pass Rd", "S Apache Pass Rd", "N Apache Pass Rd"]))
    pass_road = min(getattr(pass_road, "geoms", [pass_road]), key=lambda g: g.distance(bowie))
    start = pass_road.project(bowie)
    tail = substring(pass_road, start, pass_road.length)
    head = substring(pass_road, 0, start).reverse()
    south = tail if tail.coords[-1][1] < head.coords[-1][1] else head
    coords = densify(south, 0.0002)
    z = elevation(coords)
    i = next(k for k, v in enumerate(z) if v >= z[0] + 100)
    print(f"J4 camp: {coords[i][1]:.5f} N, {-coords[i][0]:.5f} W, {z[i]:.0f} m, "
          f"{km_along(coords[: i + 1])[-1]:.1f} km by road south of the Bowie stop")


if __name__ == "__main__":
    main()
