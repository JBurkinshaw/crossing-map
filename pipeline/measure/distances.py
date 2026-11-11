"""Distances quoted in docs/plan.md, computed so anyone can rerun them.

Run from the repo root: uv run --project pipeline python pipeline/measure/distances.py

Method: geodesic (shortest path on the WGS 84 ellipsoid) with pyproj.Geod,
which wraps PROJ's implementation of Karney's algorithm. Results are straight
lines, not travel distances. Coordinates are Wikidata P625 values, read
11 November 2026; their precision is noted where it limits the answer.
"""

from pyproj import Geod, __version__ as pyproj_version, proj_version_str

GEOD = Geod(ellps="WGS84")

# name: (lat, lon, source, note)
POINTS = {
    "trinity": (33.676669444444, -106.47556111111, "Wikidata Q19842077, Trinity Site", ""),
    "emory_pass": (32.91, -107.76666666667, "Wikidata Q49487009, Emory Pass Historical Marker",
                   "given to 0.01 deg, so about 1 km; a stand-in for the Black Range crest"),
    "casas_grandes": (30.3822, -107.9569, "Wikidata Q3867357, Casas Grandes (town)", ""),
    "mata_ortiz": (30.181111111111, -108.02277777778, "Wikidata Q4284456, Mata Ortiz", ""),
}

PAIRS = [
    ("emory_pass", "trinity", "Plan 2.4: the false dawn, Black Range to Trinity"),
    ("casas_grandes", "mata_ortiz", "Plan 2.4: Mata Ortiz from Casas Grandes"),
]

# The story box from plan section 7, step 3: 104-113 W, 27-36 N.
BOX = {"west": -113.0, "east": -104.0, "south": 27.0, "north": 36.0}


def geodesic(a: str, b: str) -> tuple[float, float]:
    """Return (distance in km, initial azimuth in degrees clockwise from north) from a to b."""
    lat1, lon1 = POINTS[a][:2]
    lat2, lon2 = POINTS[b][:2]
    azimuth, _, metres = GEOD.inv(lon1, lat1, lon2, lat2)
    return metres / 1000, azimuth % 360


def main() -> None:
    print(f"pyproj {pyproj_version}, PROJ {proj_version_str}, ellipsoid WGS 84\n")
    for a, b, label in PAIRS:
        km, az = geodesic(a, b)
        print(f"{label}\n  {km:.1f} km, initial bearing {az:.0f} deg")
        for p in (a, b):
            note = f" ({POINTS[p][3]})" if POINTS[p][3] else ""
            print(f"  {p}: {POINTS[p][2]}{note}")
        print()

    print("Story box size (geodesic along each edge)")
    # Geod.line_length follows the given vertices as geodesics; dense
    # vertices along a parallel make the result the length along that parallel.
    for lat in (BOX["south"], BOX["north"]):
        lons = [BOX["west"] + i * 0.1 for i in range(int((BOX["east"] - BOX["west"]) / 0.1) + 1)]
        km = GEOD.line_length(lons, [lat] * len(lons)) / 1000
        print(f"  width along {lat:.0f} N: {km:.0f} km")
    _, _, metres = GEOD.inv(BOX["west"], BOX["south"], BOX["west"], BOX["north"])
    print(f"  height along a meridian: {metres / 1000:.0f} km")


if __name__ == "__main__":
    main()
