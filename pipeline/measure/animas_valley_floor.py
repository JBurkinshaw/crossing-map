"""Where the she-wolf crosses the Animas Valley floor on J1, between the Animas Mountains (stop 6) and Foster Draw
(stop 8).

Run from the repo root: uv run --project pipeline python pipeline/measure/animas_valley_floor.py

The book has her cross the valley from the Animas Mountains to the hills on its west side, and names no place on the
floor. The stop is the lowest ground on the geodesic between stops 6 and 8, sampled every 100 m: the valley's axis
where her way crosses it. Heights are from the Copernicus GLO-30 mosaic (private/cache/least-cost/dem.vrt).
Distances are geodesics on the WGS 84 ellipsoid. Stop points are from pipeline/seeds/stops.csv (WGS 84).
"""

import rasterio
from pyproj import Geod

GEOD = Geod(ellps="WGS84")
DEM = "private/cache/least-cost/dem.vrt"
STOP_6 = (-108.81146, 31.52114)  # the Animas Mountains stop, at the head of Taylor Draw (lon, lat)
STOP_8 = (-108.99639, 31.4825)   # the head of Foster Draw
STEP_M = 100


def main() -> None:
    length = GEOD.inv(*STOP_6, *STOP_8)[2]
    n = int(length // STEP_M)
    points = [STOP_6, *GEOD.npts(*STOP_6, *STOP_8, n - 1), STOP_8]
    with rasterio.open(DEM) as dem:
        heights = [float(v[0]) for v in dem.sample(points)]
    i = min(range(len(points)), key=heights.__getitem__)
    lon, lat = points[i]
    print(f"stop 6 to stop 8: {length / 1000:.1f} km, {len(points)} samples")
    print(f"lowest ground: {lon:.5f}, {lat:.5f}, {heights[i]:.0f} m, {i * length / (len(points) - 1) / 1000:.1f} km "
          f"from stop 6 (stop 6 at {heights[0]:.0f} m, stop 8 at {heights[-1]:.0f} m)")


if __name__ == "__main__":
    main()
