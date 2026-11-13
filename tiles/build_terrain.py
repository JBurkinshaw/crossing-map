"""Repack AWS Terrain Tiles (Terrarium PNG) into tiles/out/terrain.pmtiles.

Run from the repo root: uv run --project pipeline python tiles/build_terrain.py
Downloads the story box at zoom 5-10 once (1,171 tiles) into
private/cache/terrain/, four requests at a time, skipping tiles already
cached. Re-encodes each tile as lossless WebP (about a third smaller, and
bit-exact, so the decoded heights do not change), writes an MBTiles file and
converts it with the `pmtiles` CLI. MapLibre reads the result as a raster-dem
source with encoding "terrarium".
See decision 0011 for why the tiles are repacked, not linked.
Attribution: 3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S.
Geological Survey; Source: INEGI, Continental relief, 2016.
"""

import io
import math
import sqlite3
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "private" / "cache" / "terrain"
OUT = REPO / "tiles" / "out" / "terrain.pmtiles"
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
WEST, SOUTH, EAST, NORTH = -113, 27, -104, 36  # the story box, plan section 7
ZOOMS = range(5, 11)


def tile_range(z: int) -> list[tuple[int, int, int]]:
    n = 2**z

    def row(lat: float) -> int:
        r = math.radians(lat)
        return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)

    xs = range(int((WEST + 180) / 360 * n), int((EAST + 180) / 360 * n) + 1)
    ys = range(row(NORTH), row(SOUTH) + 1)
    return [(z, x, y) for x in xs for y in ys]


def fetch(t: tuple[int, int, int]) -> Path:
    z, x, y = t
    path = CACHE / f"{z}/{x}/{y}.png"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": "crossing-map-pipeline/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
    return path


def webp(path: Path) -> bytes:
    """The tile as lossless WebP; `exact` keeps the RGB values, which carry the heights, untouched."""
    out = io.BytesIO()
    Image.open(path).convert("RGB").save(out, "WEBP", lossless=True, method=6, exact=True)
    return out.getvalue()


def main() -> None:
    tiles = [t for z in ZOOMS for t in tile_range(z)]
    print(f"{len(tiles)} tiles at zoom {ZOOMS.start}-{ZOOMS.stop - 1}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(fetch, tiles))

    OUT.parent.mkdir(exist_ok=True)
    mbtiles = OUT.with_suffix(".mbtiles")
    mbtiles.unlink(missing_ok=True)
    db = sqlite3.connect(mbtiles)
    db.executescript("CREATE TABLE metadata (name TEXT, value TEXT);"
                     "CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);")
    meta = {"name": "terrain", "format": "webp", "type": "baselayer", "minzoom": str(ZOOMS.start),
            "maxzoom": str(ZOOMS.stop - 1), "bounds": f"{WEST},{SOUTH},{EAST},{NORTH}",
            "attribution": "3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey; Source: INEGI, Continental relief, 2016",
            "description": "AWS Terrain Tiles (Terrarium encoding), repacked"}
    db.executemany("INSERT INTO metadata VALUES (?, ?)", meta.items())
    # MBTiles rows count from the south (TMS); XYZ rows count from the north.
    db.executemany("INSERT INTO tiles VALUES (?, ?, ?, ?)",
                   [(z, x, 2**z - 1 - y, webp(p)) for (z, x, y), p in zip(tiles, paths)])
    db.commit()
    db.close()
    subprocess.run(["pmtiles", "convert", str(mbtiles), str(OUT)], check=True)
    mbtiles.unlink()
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
