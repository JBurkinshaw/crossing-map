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
    # Part I candidates quoted in pipeline/seeds/part1-stops.csv
    "foster_hidalgo": (31.50815, -108.86894, "GNIS 889164, Foster Draw, Hidalgo County NM", ""),
    "foster_grant": (32.92802, -108.77058, "GNIS 889163, Foster Draw, Grant County NM", ""),
    "foster_socorro": (33.81634, -107.55638, "GNIS 906343, Foster Draw, Socorro County NM", ""),
    "clanton": (31.53502, -108.87484, "GNIS 887634, Clanton Draw", ""),
    "skeleton": (31.59055, -109.06124, "GNIS 11397, Skeleton Canyon, Cochise County AZ", ""),
    "starvation": (31.57519, -109.12323, "GNIS 11797, Starvation Canyon, Cochise County AZ", ""),
    "hog_spring": (31.50062, -109.08673, "GNIS 5857, Hog Canyon Spring, Cochise County AZ", ""),
    "cajon_north": (31.12684, -109.29153, "GeoNames 4016262, Cajón Bonito", ""),
    "cajon_east": (30.50576, -108.70780, "GeoNames 8688529, Cajón Bonito", ""),
    "cajon_south": (30.03211, -109.44123, "GeoNames 9024194, Cajón Bonito", ""),
    "oaxaca_son": (30.73016, -109.05822, "GeoNames 4013341, Oaxaca, Sonora", ""),
    "oaxaca_chh": (30.92590, -108.15891, "GeoNames 3996846, Colonia Oaxaca, Chihuahua", ""),
    "morelos": (30.82701, -109.22383, "GeoNames 4013350, Colonia Morelos", ""),
    "animas_valley_gnis": (32.57228, -108.83603, "GNIS 900285, Animas Valley", ""),
    "animas_valley_stop": (31.6, -108.88, "Stop j1-animas-valley, our inference", ""),
    "madera_pick": (29.93737, -109.51313, "GeoNames 9028461, Sierra La Madera", ""),
    "cumpas": (29.9948, -109.7804, "GeoNames 4012143, Cumpas", ""),
    "huasabas": (29.9083, -109.3010, "GeoNames 4004662, Huásabas", ""),
    "granados": (29.8618, -109.3111, "GeoNames 4005715, Granados", ""),
    "villa_hidalgo": (30.1620, -109.3209, "GeoNames 3971332, Villa Hidalgo", ""),
    "bavispe_crossing": (30.0119, -109.316, "Stop j1-bavispe-crossing, midpoint of Granados to Villa Hidalgo", ""),
}

PAIRS = [
    ("emory_pass", "trinity", "Plan 2.4: the false dawn, Black Range to Trinity"),
    ("casas_grandes", "mata_ortiz", "Plan 2.4: Mata Ortiz from Casas Grandes"),
    ("foster_hidalgo", "foster_grant", "Part I: Foster Draw candidates"),
    ("foster_hidalgo", "foster_socorro", "Part I: Foster Draw candidates"),
    ("clanton", "foster_hidalgo", "Part I: Clanton Draw to Foster Draw"),
    ("skeleton", "starvation", "Part I: Skeleton Canyon to Starvation Canyon"),
    ("starvation", "hog_spring", "Part I: Starvation Canyon to Hog Canyon Spring"),
    ("cajon_north", "cajon_east", "Part I: Cajón Bonito candidates"),
    ("cajon_north", "cajon_south", "Part I: Cajón Bonito candidates"),
    ("oaxaca_son", "morelos", "Part I: Colonia Oaxaca to Colonia Morelos"),
    ("oaxaca_son", "oaxaca_chh", "Part I: the two Colonia Oaxacas"),
    ("animas_valley_gnis", "animas_valley_stop", "Part I: Animas Valley pin to the J1 stop"),
    ("madera_pick", "cumpas", "Part I: Sierra La Madera pick to Cumpas (west)"),
    ("madera_pick", "huasabas", "Part I: Sierra La Madera pick to Huásabas (east, on the Bavispe)"),
    ("bavispe_crossing", "granados", "Part I: wolf crossing to Granados"),
    ("bavispe_crossing", "villa_hidalgo", "Part I: wolf crossing to Villa Hidalgo"),
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
