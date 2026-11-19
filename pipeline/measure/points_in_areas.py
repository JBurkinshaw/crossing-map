"""Points for the stops whose point lies outside their own area, each moved to the nearest ground inside it.

Run from the repo root: uv run --project pipeline python pipeline/measure/points_in_areas.py

A stop with an area is drawn as its area, and its point is the best single guess inside it, so the point must lie in
the area. For each stop whose point (data/stops.geojson) is outside its area (data/areas.geojson), this prints the
nearest point that is at least INSET metres inside the area. If the stop has a landform position
(pipeline/seeds/stop-positions.csv), the point must also pass the terrain check for it (crossing.landform_points.check):
cells of a 60 m grid are screened by the check's geomorphon at a 500 m lookout and the height percentile over the
area's bounding window, nearest first, and the first that passes the full check is taken.

Grids are local transverse Mercator (WGS 84) from crossing.landform_points, on the Copernicus GLO-30 DEM. Distances
are geodesics on the WGS 84 ellipsoid. Stop and area coordinates are WGS 84.
"""

import csv
import json

import numpy as np
import shapely
from shapely.geometry import Point, shape

from crossing import landform_points as lf
from crossing.paths import DATA, REPO

INSET = 200  # m: how far inside the area's edge the point must be
TRIES = 40   # screened cells to try with the full check, nearest first


def main() -> None:
    stops = {f["properties"]["id"]: f["geometry"]["coordinates"]
             for f in json.loads((DATA / "stops.geojson").read_text(encoding="utf-8"))["features"]}
    with (REPO / "pipeline" / "seeds" / "stop-positions.csv").open(encoding="utf-8") as f:
        positions = {r["stop"]: r["position"] for r in csv.DictReader(f)}
    for area in json.loads((DATA / "areas.geojson").read_text(encoding="utf-8"))["features"]:
        stop = area["properties"]["id"].removeprefix("area-")
        if stop not in stops:
            continue
        here = tuple(stops[stop])
        poly = shape(area["geometry"])
        if poly.contains(Point(here)):
            continue
        minx, miny, maxx, maxy = poly.bounds
        centre = ((minx + maxx) / 2, (miny + maxy) / 2)
        half = max(lf.km((minx, centre[1]), (maxx, centre[1])), lf.km((centre[0], miny), (centre[0], maxy))) * 500 + 500
        g = lf.grid(centre, half, 60)
        rows, cols = np.mgrid[:g.z.shape[0], :g.z.shape[1]]
        xs = -g.half + (cols + 0.5) * g.res
        ys = g.half - (rows + 0.5) * g.res
        # The area in the grid's metres, shrunk by INSET, so a chosen cell is clearly inside.
        fwd = g.fwd
        local = shapely.transform(poly, lambda xy, fwd=fwd: np.column_stack(fwd.transform(xy[:, 0], xy[:, 1])))
        inner = local.buffer(-INSET)
        inside = shapely.contains_xy(inner, xs, ys)
        position = positions.get(stop)
        if position:
            forms_ok, (lo, hi), _ = lf.EXPECT[position]
            forms, _ = lf.forms_grid(g, lf.LOOKOUTS[0])
            order = np.sort(g.z[inside])
            pct = np.searchsorted(order, g.z) / len(order) * 100
            inside &= np.isin(forms, list(forms_ok)) & (pct >= lo) & (pct <= hi)
        hx, hy = g.fwd.transform(*here)
        cells = np.argwhere(inside)
        cells = cells[np.argsort(np.hypot(xs[inside] - hx, ys[inside] - hy))]
        chosen, verdict = None, "no position"
        for rc in cells[:TRIES if position else 1]:
            point = g.lonlat(tuple(rc))
            if not position:
                chosen = point
                break
            _, verdict = lf.check(position, point)
            if verdict.startswith("ok"):
                chosen = point
                break
        outside_km = lf.km(here, local_to_lonlat(g, local.boundary.interpolate(local.boundary.project(
            shapely.Point(hx, hy)))))
        if chosen is None:
            print(f"{stop}: {outside_km:.1f} km outside, and no cell inside passes the check for {position!r}")
            continue
        print(f"{stop}: {outside_km:.1f} km outside its area. New point {chosen[1]}, {chosen[0]}, "
              f"{lf.km(here, chosen):.1f} km from the old one, {position or 'no position'}: {verdict}")


def local_to_lonlat(g, p) -> tuple[float, float]:
    return g.inv.transform(p.x, p.y)


if __name__ == "__main__":
    main()
