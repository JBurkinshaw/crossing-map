"""Download Copernicus GLO-30 DEM tiles for the journeys corridor.

Run from the repo root: uv run --project pipeline python -m crossing.fetch_dem
Tiles are 1° x 1° Cloud-Optimized GeoTIFFs on AWS open data (no login),
named by their south-west corner. A tile is fetched when it lies within
CORRIDOR_KM of any route segment in data/journeys.geojson, or inside one of
the EXTRA regions that later Parts cover. Existing files are skipped.
Writes to private/cache/dem/copernicus/.
"""

import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "private" / "cache" / "dem" / "copernicus"
URL = "https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif"
CORRIDOR_KM = 40
# (west, south, east, north): the Casas Grandes - Babícora - Namiquipa country of Parts II-IV; the bootheel to
# Deming, Lordsburg and Apache Pass (J4, J7); the Black Range (J7). Only legs on horseback or on foot (plan 5.2).
EXTRA = [(-109, 28, -106, 31), (-108, 31, -107, 32), (-110, 32, -107, 33), (-108, 33, -107, 34)]


def name(lat: int, lon: int) -> str:
    ns, ew = ("N" if lat >= 0 else "S"), ("E" if lon >= 0 else "W")
    return f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"


def corridor_tiles() -> set[tuple[int, int]]:
    """South-west corners of tiles within CORRIDOR_KM of any journey vertex."""
    pad_lat = CORRIDOR_KM / 111.0
    tiles = set()
    for f in json.loads((REPO / "data" / "journeys.geojson").read_text(encoding="utf-8"))["features"]:
        for lon, lat in f["geometry"]["coordinates"]:
            pad_lon = CORRIDOR_KM / (111.0 * math.cos(math.radians(lat)))
            for y in range(math.floor(lat - pad_lat), math.floor(lat + pad_lat) + 1):
                for x in range(math.floor(lon - pad_lon), math.floor(lon + pad_lon) + 1):
                    tiles.add((y, x))
    for w, s, e, n in EXTRA:
        tiles |= {(y, x) for y in range(s, n) for x in range(w, e)}
    return tiles


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = sorted(corridor_tiles())
    print(f"{len(tiles)} tiles in the corridor")
    for lat, lon in tiles:
        n = name(lat, lon)
        path = OUT / f"{n}.tif"
        if path.exists():
            continue
        req = urllib.request.Request(URL.format(name=n), headers={"User-Agent": "crossing-map-pipeline/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                path.write_bytes(r.read())
            print(f"  {n}: {path.stat().st_size / 1e6:.1f} MB")
        except urllib.error.HTTPError as e:
            print(f"  {n}: HTTP {e.code}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
