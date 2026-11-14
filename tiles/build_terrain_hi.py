"""Build tiles/out/terrain-hi.pmtiles: zoom 11-12 elevation for the hillshade, from Copernicus GLO-30.

Not part of a release yet; review/stage-8/lab-hillshade/README.md has the sizes and the trade-offs. Run from the
repo root:
    uv run --project pipeline python tiles/build_terrain_hi.py --estimate 25      # every 25th tile, projected size
    uv run --project pipeline python tiles/build_terrain_hi.py --zooms 11 11      # the whole story box at zoom 11
    uv run --project pipeline python tiles/build_terrain_hi.py --bbox -109.4 31.3 -108.6 31.9 --out site/public/tiles/terrain-hi.pmtiles

terrain.pmtiles stops at zoom 10, where a pixel is about 130 m on the ground at 31° N; from zoom 11 the map
stretches those pixels and the hillshade turns soft. Copernicus GLO-30 (1 arc-second, about 26 m by 31 m here)
holds about four times the detail, which zoom 12 (about 33 m a pixel) shows. Zoom 13 would only interpolate.

Reads the story box's Copernicus tiles already cached for the hachures (private/cache/dem/copernicus*/), warps
each web tile bilinearly into Web Mercator, rounds heights to --quantum metres, encodes them as Terrarium and
saves lossless WebP, as build_terrain.py does. Rounding is what keeps the size down: the fraction of a metre is
noise that lossless WebP cannot compress. Steps of 1 m halve the size of 0.25 m steps, but can show as faint
terraces on the gentlest basin floors. MapLibre reads the archive as a second raster-dem source that the hillshade
switches to at map zoom 10, where 256 px tiles of zoom 11 are sharp; terrain.pmtiles keeps zoom 5-10.
"""

import argparse
import io
import sqlite3
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_terrain  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DEM_FOLDERS = [REPO / "private" / "cache" / "dem" / "copernicus", REPO / "private" / "cache" / "dem" / "copernicus-region"]
OUT = REPO / "tiles" / "out" / "terrain-hi.pmtiles"
SIZE = 256
HALF = 20037508.342789244  # half the width of the Web Mercator world, metres
COPERNICUS = ("Copernicus DEM GLO-30, © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, "
              "provided under COPERNICUS by the European Union and ESA")

# One open dataset per worker thread; GDAL handles are not safe to share between threads.
_local = threading.local()


def mercator_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    step = 2 * HALF / 2**z
    return -HALF + x * step, HALF - (y + 1) * step, -HALF + (x + 1) * step, HALF - y * step


def encode(vrt: str, t: tuple[int, int, int], quantum: float) -> bytes:
    """One web tile of heights as Terrarium (height + 32768 = R * 256 + G + B / 256) in lossless WebP."""
    if not hasattr(_local, "dem"):
        _local.dem = rasterio.open(vrt)
    heights = np.zeros((SIZE, SIZE), np.float32)
    reproject(rasterio.band(_local.dem, 1), heights, dst_transform=from_bounds(*mercator_bounds(*t), SIZE, SIZE),
              dst_crs="EPSG:3857", resampling=Resampling.bilinear, dst_nodata=0)
    v = np.round(heights / quantum) * quantum + 32768
    rgb = np.stack([v // 256, np.floor(v) % 256, np.floor((v % 1) * 256)], axis=-1).astype(np.uint8)
    out = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(out, "WEBP", lossless=True, method=6, exact=True)
    return out.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zooms", type=int, nargs=2, default=[11, 12], metavar=("MIN", "MAX"))
    ap.add_argument("--quantum", type=float, default=1.0, help="height step in metres (default 1)")
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("W", "S", "E", "N"), help="a smaller area than the story box")
    ap.add_argument("--estimate", type=int, metavar="N", help="encode every Nth tile and print the projected size")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if a.bbox:
        build_terrain.WEST, build_terrain.SOUTH, build_terrain.EAST, build_terrain.NORTH = a.bbox
    zooms = range(a.zooms[0], a.zooms[1] + 1)
    by_name = {p.name: p for folder in DEM_FOLDERS for p in sorted(folder.glob("*.tif"))}
    tiles = [t for z in zooms for t in build_terrain.tile_range(z)]
    chosen = tiles[:: a.estimate] if a.estimate else tiles
    print(f"{len(tiles)} tiles at zoom {zooms.start}-{zooms.stop - 1} from {len(by_name)} DEM tiles; encoding {len(chosen)}")
    with tempfile.TemporaryDirectory() as tmp:
        vrt = str(Path(tmp) / "dem.vrt")
        subprocess.run(["gdalbuildvrt", "-q", vrt, *map(str, by_name.values())], check=True)
        with ThreadPoolExecutor(max_workers=8) as pool:
            blobs = list(pool.map(lambda t: encode(vrt, t, a.quantum), chosen))

    if a.estimate:
        for z in zooms:
            sizes = [len(b) for t, b in zip(chosen, blobs) if t[0] == z]
            count = sum(1 for t in tiles if t[0] == z)
            print(f"zoom {z}: {count} tiles, mean {np.mean(sizes) / 1e3:.1f} kB, about {np.mean(sizes) * count / 1e6:.0f} MB")
        return

    a.out.parent.mkdir(parents=True, exist_ok=True)
    mbtiles = a.out.with_suffix(".mbtiles")
    mbtiles.unlink(missing_ok=True)
    db = sqlite3.connect(mbtiles)
    db.executescript("CREATE TABLE metadata (name TEXT, value TEXT);"
                     "CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);")
    bounds = ",".join(str(v) for v in (build_terrain.WEST, build_terrain.SOUTH, build_terrain.EAST, build_terrain.NORTH))
    meta = {"name": "terrain-hi", "format": "webp", "type": "baselayer", "minzoom": str(zooms.start),
            "maxzoom": str(zooms.stop - 1), "bounds": bounds, "attribution": COPERNICUS,
            "description": f"Copernicus GLO-30 heights (Terrarium encoding, {a.quantum} m steps)"}
    db.executemany("INSERT INTO metadata VALUES (?, ?)", meta.items())
    # MBTiles rows count from the south (TMS); XYZ rows count from the north.
    db.executemany("INSERT INTO tiles VALUES (?, ?, ?, ?)", [(z, x, 2**z - 1 - y, b) for (z, x, y), b in zip(tiles, blobs)])
    db.commit()
    db.close()
    subprocess.run(["pmtiles", "convert", str(mbtiles), str(a.out)], check=True)
    mbtiles.unlink()
    print(f"Wrote {a.out} ({a.out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
