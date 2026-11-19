"""Where the she-wolf crosses the Animas Mountains on J1, between San Luis Pass (stop 5) and the Animas Valley (stop 7).

Run from the repo root: uv run --project pipeline python pipeline/measure/animas_crossing.py

The owner's reading of the book: from San Luis Pass she goes north along the east side of the range, then crosses
it about halfway to the Animas Valley stop by the easiest way through. GNIS has no gap on that stretch of the range,
so the crossing is measured on the DEM:

1. The approach is the lowest point of the valley east of the range's western ridge, on the parallel halfway between
   the stops, sampled every 0.0005 degrees between longitudes -108.765 and -108.69.
2. The wolf's least-cost path from the approach to stop 7 is crossing.least_cost's (Copernicus GLO-30, Tobler's
   hiking function unscaled, on its local transverse Mercator grid, WGS 84). Its highest vertex is where it crosses
   the ridge.
3. The stop is the saddle cell nearest that vertex: geomorphons on a 30 m grid with a 250 m lookout, and the saddle
   test, both from crossing.landform_points. A simplified path's vertex can sit a little off the col.

The script then prints the legs the map draws, stop 5 to the crossing and the crossing to stop 7, and the terrain
check on the crossing. Heights are from private/cache/least-cost/dem.vrt. Distances are geodesics on the WGS 84
ellipsoid. Stop points are from pipeline/seeds/stops.csv (WGS 84).
"""

import numpy as np
import rasterio

from crossing import landform_points as lf
from crossing import least_cost as lc

STOP_5 = (-108.74505, 31.39455)   # San Luis Pass (lon, lat)
# The valley point the crossing was measured towards, kept so this script gives the published crossing. The
# published valley stop is the floor between the crossing and Foster Draw (animas_valley_floor.py, decision 0069).
STOP_7 = (-108.88, 31.6)
VALLEY = (-108.765, -108.69)      # the longitudes of the valley east of the western ridge
WOLF = {"mode": "wolf"}


def main() -> None:
    with rasterio.open(lf.DEM) as dem:
        def height(p) -> float:
            return float(next(dem.sample([tuple(p)]))[0])

        half = round((STOP_5[1] + STOP_7[1]) / 2, 5)
        lons = np.arange(VALLEY[0], VALLEY[1], 0.0005)
        approach = (round(float(min(lons, key=lambda x: height((x, half)))), 5), half)
        print(f"Approach, halfway up the east side: {approach[1]}, {approach[0]}, {height(approach):.0f} m")

        through = lc.route(approach, STOP_7, WOLF)["coords"]
        top = max(through, key=height)
        print(f"Highest point of the way through to stop 7: {top[1]}, {top[0]}, {height(top):.0f} m")

        g = lf.grid(top, 1500, 30)
        _, saddle = lf.forms_grid(g, 250)
        cells = [g.lonlat(tuple(c)) for c in np.argwhere(saddle)]
        stop = min(cells, key=lambda p: lf.km(top, p))
        print(f"Crossing (nearest saddle cell): {stop[1]}, {stop[0]}, {height(stop):.0f} m, "
              f"{lf.km(top, stop) * 1000:.0f} m from that point")
        print(f"  {lf.km(STOP_5, stop):.1f} km from stop 5 and {lf.km(stop, STOP_7):.1f} km from stop 7 in a straight "
              f"line, {(stop[1] - half) * 111.0:+.1f} km north of halfway")

        legs = [("Leg 5, stop 5 to the crossing", STOP_5, stop), ("Leg 6, the crossing to stop 7", stop, STOP_7)]
        for name, a, b in legs:
            r = lc.route(a, b, WOLF)
            west = min(p[0] for p in r["coords"])
            print(f"{name}: {r['km']} km, {r['hours']} h, highest {max(map(height, r['coords'])):.0f} m, "
                  f"farthest west {west}")

        ground = lf.ground(stop)
        print(f"Terrain check: {ground}, {lf.verdict('pass', ground)}")


if __name__ == "__main__":
    main()
