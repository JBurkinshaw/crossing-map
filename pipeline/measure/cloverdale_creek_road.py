"""Where the Cloverdale Creek road ends, for the trap site of J1 stop 13 and J2 stop 2 (decision 0078).

Run from the repo root: uv run --project pipeline python pipeline/measure/cloverdale_creek_road.py

In 1-08 Billy rides west up the creek road from Cloverdale, past an old dance platform in the woods, and two hours
after that leaves the road for the vaqueros' fire. The dance platform is taken as Cloverdale Park (GNIS 933623, a
historic site on the same point as Cloverdale, 920578), so the ride is measured from Cloverdale. At a horse's walk,
about 6 km/h, two hours is some 12 km. The road is Census TIGER/Line 2023 (Hidalgo County, in
private/cache/roads/tiger/): Co Rd C001 west along the creek, then Co Rd C106 to its end. Lengths along the road are
geodesic on the WGS 84 ellipsoid (pyproj.Geod). TIGER coordinates are NAD83, taken as WGS 84 (they differ by about
1 m here).
"""

from road_points import km_along, road
from shapely.geometry import Point
from shapely.ops import linemerge

CLOVERDALE = (-108.9297735, 31.4170488)  # GNIS 920578 and 933623 (lon, lat)


def main() -> None:
    lines = road("35023", ["Cloverdale Rd C001", "Co Rd C001", "Co Rd C106"])
    # The creek road: the parts south of 31.46 N (Co Rd C001 also runs 60 km north up the Animas Valley), merged and
    # run east to west, from where it passes nearest the Cloverdale pin to the end of Co Rd C106.
    merged = linemerge([g for g in lines if max(y for _, y in g.coords) < 31.46])
    coords = list(max(getattr(merged, "geoms", [merged]), key=lambda g: g.length).coords)
    if coords[0][0] < coords[-1][0]:
        coords.reverse()
    start = min(range(len(coords)), key=lambda i: Point(coords[i]).distance(Point(CLOVERDALE)))
    coords = coords[start:]
    along = km_along(coords)
    end = coords[-1]
    print(f"creek road from Cloverdale: {along[-1]:.1f} km to its end at ({end[1]:.5f}, {end[0]:.5f})")
    print(f"two hours at 6 km/h: 12.0 km, {12.0 - along[-1]:.1f} km past the road's end")


if __name__ == "__main__":
    main()
