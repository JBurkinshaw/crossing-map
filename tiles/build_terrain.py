"""Repack AWS Terrain Tiles (Terrarium PNG) into tiles/out/terrain.pmtiles.

Run from the repo root: uv run --project pipeline python -m tiles.build_terrain
Downloads the story box at zoom 5-10 once into private/cache/terrain/, four requests at a time, skipping tiles
already cached. Re-encodes each tile as lossless WebP (about a third smaller, and bit-exact, so the decoded
heights do not change), writes an MBTiles file and converts it with the `pmtiles` CLI. MapLibre reads the result
as a raster-dem source with encoding "terrarium".
See decision 0011 for why the tiles are repacked, not linked.
"""

import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from crossing.dem import download
from crossing.paths import CACHE, STORY_BOX, TILES_OUT
from tiles.raster import tile_range, write_pmtiles

TERRAIN_CACHE = CACHE / "terrain"
OUT = TILES_OUT / "terrain.pmtiles"
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
ZOOMS = range(5, 11)
ATTRIBUTION = ("3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey; "
               "Source: INEGI, Continental relief, 2016")


def fetch(t: tuple[int, int, int]) -> Path:
    z, x, y = t
    path = TERRAIN_CACHE / f"{z}/{x}/{y}.png"
    if not path.exists():
        download(URL.format(z=z, x=x, y=y), path, timeout=60)
    return path


def webp(path: Path) -> bytes:
    """The tile as lossless WebP; `exact` keeps the RGB values, which carry the heights, untouched."""
    out = io.BytesIO()
    Image.open(path).convert("RGB").save(out, "WEBP", lossless=True, method=6, exact=True)
    return out.getvalue()


def main() -> None:
    tiles = [t for z in ZOOMS for t in tile_range(z, STORY_BOX)]
    print(f"{len(tiles)} tiles at zoom {ZOOMS.start}-{ZOOMS.stop - 1}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(fetch, tiles))
    meta = {"name": "terrain", "format": "webp", "type": "baselayer", "minzoom": str(ZOOMS.start),
            "maxzoom": str(ZOOMS.stop - 1), "bounds": ",".join(f"{v:g}" for v in STORY_BOX),
            "attribution": ATTRIBUTION, "description": "AWS Terrain Tiles (Terrarium encoding), repacked"}
    write_pmtiles(OUT, ((z, x, y, webp(p)) for (z, x, y), p in zip(tiles, paths, strict=True)), meta)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
