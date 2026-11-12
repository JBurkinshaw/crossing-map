"""Prepare DEMs for the relief experiment (plan section 5.2, stage 3).

Run from the repo root: uv run --project pipeline python -m crossing.relief
For each test area: mosaic the Copernicus GLO-30 tiles, reproject to UTM 12N
at 30 m, smooth with a Gaussian of SMOOTH_SIGMA cells so hachures follow
landforms rather than noise, and write a GeoTIFF to private/cache/relief/.
"""

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

REPO = Path(__file__).resolve().parents[3]
DEM_TILES = REPO / "private" / "cache" / "dem" / "copernicus"
OUT = REPO / "private" / "cache" / "relief"
CRS = "EPSG:32612"  # UTM 12N: the bootheel and eastern Sonora; Chihuahua lies just east of the zone
CELL_M = 30
SMOOTH_SIGMA = 1.5  # cells; the plan asks for a light Gaussian of 2-3 cells in width

# Test areas (west, south, east, north), about 45 km square each.
AREAS = {
    "peloncillos": (-109.15, 31.35, -108.65, 31.75),  # Peloncillos and the Animas Valley
    "pilares": (-109.35, 30.55, -108.90, 30.95),  # the Pilares Teras and the Bavispe barranca
    "babicora": (-108.00, 29.10, -107.50, 29.50),  # the Babícora plains
}


def prepare(name: str, bounds: tuple[float, float, float, float]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}.tif"
    with tempfile.TemporaryDirectory() as tmp:
        vrt = Path(tmp) / "mosaic.vrt"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *map(str, sorted(DEM_TILES.glob("*.tif")))], check=True)
        warped = Path(tmp) / "warped.tif"
        subprocess.run(
            ["gdalwarp", "-q", "-overwrite", "-te_srs", "EPSG:4326", "-te", *map(str, bounds), "-t_srs", CRS,
             "-tr", str(CELL_M), str(CELL_M), "-r", "bilinear", "-ot", "Float32", str(vrt), str(warped)],
            check=True,
        )
        with rasterio.open(warped) as src:
            profile = src.profile
            dem = src.read(1).astype(np.float32)
        smooth = gaussian_filter(dem, sigma=SMOOTH_SIGMA)
        profile.update(driver="GTiff", compress="deflate", tiled=True, blockxsize=256, blockysize=256)
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(smooth, 1)
    # A 90 m copy for the coarse hachures: the script spaces lines in cells, so a coarser grid spaces them wider.
    coarse = OUT / f"{name}-90m.tif"
    subprocess.run(["gdalwarp", "-q", "-overwrite", "-tr", "90", "90", "-r", "average", "-co", "COMPRESS=DEFLATE",
                    str(out), str(coarse)], check=True)
    print(f"{out.name}: {dem.shape[1]} x {dem.shape[0]} cells, {float(dem.min()):.0f}-{float(dem.max()):.0f} m; plus {coarse.name}")
    return out


def main() -> None:
    for name, bounds in AREAS.items():
        prepare(name, bounds)


if __name__ == "__main__":
    main()
