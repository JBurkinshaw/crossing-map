"""Download Copernicus GLO-30 DEM tiles for the journeys corridor.

Run from the repo root: uv run --project pipeline python -m crossing.fetch_dem
Tiles are 1° x 1° Cloud-Optimized GeoTIFFs on AWS open data (no login),
named by their south-west corner. A tile is fetched when it lies within
CORRIDOR_KM of any route segment in data/journeys.geojson. Existing files are
skipped. Writes to private/cache/dem/copernicus/. Exits 1 if any tile failed,
after trying the rest; a rerun fetches only what is missing.

With --story-box, fetches instead every tile of the story box (design section 7) that the corridor run does not
already have, into private/cache/dem/copernicus-region/, for the full-region hachure run (design 5.2). That folder
is kept apart so the production relief, which covers whatever is in copernicus/, does not grow by accident.
"""

import argparse
import json
import math
import sys
import time
import urllib.error

from crossing.dem import COPERNICUS, COPERNICUS_REGION, download
from crossing.paths import DATA, STORY_BOX

URL = "https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif"
CORRIDOR_KM = 40


def name(lat: int, lon: int) -> str:
    ns, ew = ("N" if lat >= 0 else "S"), ("E" if lon >= 0 else "W")
    return f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"


def corridor_tiles() -> set[tuple[int, int]]:
    """South-west corners of tiles within CORRIDOR_KM of any journey vertex."""
    pad_lat = CORRIDOR_KM / 111.0
    tiles = set()
    for f in json.loads((DATA / "journeys.geojson").read_text(encoding="utf-8"))["features"]:
        for lon, lat in f["geometry"]["coordinates"]:
            pad_lon = CORRIDOR_KM / (111.0 * math.cos(math.radians(lat)))
            for y in range(math.floor(lat - pad_lat), math.floor(lat + pad_lat) + 1):
                for x in range(math.floor(lon - pad_lon), math.floor(lon + pad_lon) + 1):
                    tiles.add((y, x))
    return tiles


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--story-box", action="store_true", help="the whole story box, into copernicus-region/")
    a = ap.parse_args()
    if a.story_box:
        w, s, e, n = map(int, STORY_BOX)
        tiles, out = sorted((y, x) for y in range(s, n) for x in range(w, e)), COPERNICUS_REGION
    else:
        tiles, out = sorted(corridor_tiles()), COPERNICUS
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(tiles)} tiles")
    failed = []
    for lat, lon in tiles:
        n = name(lat, lon)
        path = out / f"{n}.tif"
        if path.exists() or (COPERNICUS / f"{n}.tif").exists():
            continue
        try:
            download(URL.format(name=n), path)
            print(f"  {n}: {path.stat().st_size / 1e6:.1f} MB")
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {n}: {getattr(e, 'code', None) or e}")
            failed.append(n)
        time.sleep(0.5)
    if failed:
        sys.exit(f"{len(failed)} tiles failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
