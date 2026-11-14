"""Build tiles/out/terrain-hi.pmtiles: zoom 11-12 elevation for the hillshade, from Copernicus GLO-30.

Not part of a release yet; review/stage-8/lab-hillshade/README.md has the sizes and the trade-offs. Run from the
repo root:
    uv run --project pipeline python -m tiles.build_terrain_hi --estimate 25   # every 25th tile, projected size
    uv run --project pipeline python -m tiles.build_terrain_hi --zooms 11 11   # the whole story box at zoom 11
    uv run --project pipeline python -m tiles.build_terrain_hi --bbox -109.4 31.3 -108.6 31.9 \
        --out site/public/tiles/terrain-hi.pmtiles

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
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

from crossing import dem
from crossing.paths import STORY_BOX, TILES_OUT
from tiles.raster import tile_range, write_pmtiles

OUT = TILES_OUT / "terrain-hi.pmtiles"
SIZE = 256
HALF = 20037508.342789244  # half the width of the Web Mercator world, metres

# One open dataset per worker thread; GDAL handles are not safe to share between threads.
_local = threading.local()


def mercator_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    step = 2 * HALF / 2**z
    return -HALF + x * step, HALF - (y + 1) * step, -HALF + (x + 1) * step, HALF - y * step


def encode(vrt: str, t: tuple[int, int, int], quantum: float) -> bytes:
    """One web tile of heights as Terrarium (height + 32768 = R * 256 + G + B / 256) in lossless WebP."""
    if not hasattr(_local, "src"):
        _local.src = rasterio.open(vrt)
    heights = np.zeros((SIZE, SIZE), np.float32)
    reproject(rasterio.band(_local.src, 1), heights, dst_transform=from_bounds(*mercator_bounds(*t), SIZE, SIZE),
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
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("W", "S", "E", "N"), default=list(STORY_BOX),
                    help="a smaller area than the story box")
    ap.add_argument("--estimate", type=int, metavar="N", help="encode every Nth tile and print the projected size")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    zooms = range(a.zooms[0], a.zooms[1] + 1)
    by_name = {p.name: p for p in dem.tiles(dem.COPERNICUS, dem.COPERNICUS_REGION)}
    tiles = [t for z in zooms for t in tile_range(z, a.bbox)]
    chosen = tiles[:: a.estimate] if a.estimate else tiles
    print(f"{len(tiles)} tiles at zoom {zooms.start}-{zooms.stop - 1} from {len(by_name)} DEM tiles; "
          f"encoding {len(chosen)}")
    with tempfile.TemporaryDirectory() as tmp:
        vrt = str(dem.build_vrt(Path(tmp) / "dem.vrt", list(by_name.values())))
        with ThreadPoolExecutor(max_workers=8) as pool:
            blobs = list(pool.map(lambda t: encode(vrt, t, a.quantum), chosen))

    if a.estimate:
        for z in zooms:
            sizes = [len(b) for t, b in zip(chosen, blobs, strict=True) if t[0] == z]
            count = sum(1 for t in tiles if t[0] == z)
            mean = np.mean(sizes)
            print(f"zoom {z}: {count} tiles, mean {mean / 1e3:.1f} kB, about {mean * count / 1e6:.0f} MB")
        return

    meta = {"name": "terrain-hi", "format": "webp", "type": "baselayer", "minzoom": str(zooms.start),
            "maxzoom": str(zooms.stop - 1), "bounds": ",".join(f"{v:g}" for v in a.bbox), "attribution": dem.NOTICE,
            "description": f"Copernicus GLO-30 heights (Terrarium encoding, {a.quantum} m steps)"}
    write_pmtiles(a.out, ((z, x, y, b) for (z, x, y), b in zip(tiles, blobs, strict=True)), meta)
    print(f"Wrote {a.out} ({a.out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
