"""Where J1's draws and canyons head, and the point between the heads of Clanton and Foster draws.

Run from the repo root: uv run --project pipeline python pipeline/measure/draw_heads.py

GNIS records a valley, canyon or stream with two points: the primary point at its mouth and a source point at
its head. Coordinates are from the GNIS national file of 25 August 2021 (private/cache/gazetteer/Features_20210825/,
fields PRIM_LAT_DEC, PRIM_LONG_DEC, SOURCE_LAT_DEC, SOURCE_LONG_DEC), on NAD83, taken as WGS 84 (they differ by
about a metre here). Distances are geodesics on the WGS 84 ellipsoid (pyproj.Geod, Karney's algorithm). The
midpoint is the geodesic midpoint. The divide between the draws is computed on the same DEM by flow routing
(crossing.landform_points: priority-flood filling, D8 directions, 60 m transverse Mercator grid). Heights are
sampled from the Copernicus GLO-30 DEM
(private/cache/least-cost/dem.vrt).
"""

from pathlib import Path

import rasterio
from pyproj import Geod

from crossing import landform_points as lf

GEOD = Geod(ellps="WGS84")
DEM = Path(__file__).resolve().parents[2] / "private/cache/least-cost/dem.vrt"

# name: (GNIS id, mouth (lat, lon), head (lat, lon))
FEATURES = {
    "Foster Draw": (889164, (31.5078801, -108.8692174), (31.4825, -108.9963889)),
    "Clanton Draw": (887634, (31.5350167, -108.8748406), (31.5121262, -109.034553)),
    "Starvation Canyon": (11797, (31.5751897, -109.123225), (31.5224431, -109.0957349)),
    # In Hidalgo County; the other Taylor Draw in GNIS (895531) is in Eddy County, 485 km east.
    "Taylor Draw": (896882, (31.5079666, -108.8690762), (31.5211429, -108.8114597)),
}
# Stops the book places by these features, as the map had them before this measurement.
OLD_STOP_12 = (31.52, -108.87)


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    return GEOD.inv(a[1], a[0], b[1], b[0])[2] / 1000


def main() -> None:
    with rasterio.open(DEM) as dem:
        def height(p: tuple[float, float]) -> int:
            return round(float(next(dem.sample([(p[1], p[0])]))[0]))

        for name, (gnis, mouth, head) in FEATURES.items():
            print(f"{name} (GNIS {gnis}): mouth {mouth} {height(mouth)} m, head {head} {height(head)} m, "
                  f"{km(mouth, head):.1f} km apart")
        foster, clanton = FEATURES["Foster Draw"][2], FEATURES["Clanton Draw"][2]
        lon, lat = GEOD.npts(foster[1], foster[0], clanton[1], clanton[0], 1)[0]
        mid = (round(lat, 5), round(lon, 5))
        print(f"Between the heads: {mid} {height(mid)} m; the heads are {km(foster, clanton):.1f} km apart; "
              f"{km(OLD_STOP_12, mid):.1f} km from the old stop 12 at {OLD_STOP_12} ({height(OLD_STOP_12)} m)")

        # The midpoint lies in a valley, so stop 12 is on the drainage divide between the two draws' catchments,
        # at the divide's high cell nearest the two heads (crossing.landform_points.dem_between).
        mouths = [FEATURES[n][1][::-1] for n in ("Foster Draw", "Clanton Draw")]
        heads = [FEATURES[n][2][::-1] for n in ("Foster Draw", "Clanton Draw")]
        lon, lat = lf.dem_between(*mouths, heads_at=heads)[0]
        ground = lf.ground((lon, lat))
        print(f"On the divide nearest the heads: ({lat}, {lon}) {height((lat, lon))} m, {ground['form_500']} at a "
              f"500 m lookout, height percentile {ground['height_pct']} within 3 km, {km(mid, (lat, lon)):.1f} km "
              f"from the midpoint")


if __name__ == "__main__":
    main()
