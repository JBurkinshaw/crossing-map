"""Build tiles/out/relief-test.pmtiles for the relief comparison sheet (stage 3).

Run from the repo root: uv run --project pipeline python tiles/build_relief_test.py
Layers, from the three test areas only:
  hachure_fine    the split hachures from the 30 m runs, with their Slope (degrees)
  hachure_lines   whole hachure lines from the 30 m runs, with their mean Slope
  hachure_coarse  whole hachure lines from the 90 m runs, with their mean Slope
  stipple         dots on steep ground for the "Sierra" treatment, denser where steeper
Hachures come from pipeline/relief/run_hachures.py; DEMs from crossing.relief.
This archive is a review artefact: it is not published.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

REPO = Path(__file__).resolve().parents[1]
RELIEF = REPO / "private" / "cache" / "relief"
OUT = REPO / "tiles" / "out" / "relief-test.pmtiles"
AREAS = ["peloncillos", "pilares", "babicora"]
STIPPLE_FROM_DEG = 15  # no dots on gentler ground
STIPPLE_PER_CELL = 0.12  # chance of a dot in a 90 m cell at 45 degrees and steeper


def stipple(area: str, rng: np.random.Generator) -> list[dict]:
    with rasterio.open(RELIEF / f"{area}-90m.tif") as src:
        dem = src.read(1).astype(float)
        transform, crs = src.transform, src.crs
    gy, gx = np.gradient(dem, transform.e, transform.a)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    chance = np.clip((slope - STIPPLE_FROM_DEG) / (45 - STIPPLE_FROM_DEG), 0, 1) * STIPPLE_PER_CELL
    rows, cols = np.nonzero(rng.random(slope.shape) < chance)
    # Jitter within the cell so the dots do not sit on a grid.
    xs, ys = rasterio.transform.xy(transform, rows + rng.random(rows.size), cols + rng.random(cols.size), offset="ul")
    lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(xs, ys)
    return [{"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [round(a, 5), round(b, 5)]}}
            for a, b in zip(lon, lat)]


def slope_raster(dem_path: Path):
    """Slope in degrees, the raster's transform, and a WGS 84 -> raster CRS transformer."""
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(float)
        transform, crs = src.transform, src.crs
    gy, gx = np.gradient(dem, transform.e, transform.a)
    return np.degrees(np.arctan(np.hypot(gx, gy))), transform, Transformer.from_crs("EPSG:4326", crs, always_xy=True)


def with_mean_slope(lines_path: Path, dem_path: Path, out_path: Path) -> list[float]:
    """Copy a whole-line hachure file, adding each line's mean slope sampled at its vertices (plan 5.2, step 4)."""
    slope, transform, to_dem = slope_raster(dem_path)
    doc = json.loads(lines_path.read_text())
    means = []
    for f in doc["features"]:
        lon, lat = zip(*f["geometry"]["coordinates"])
        x, y = to_dem.transform(lon, lat)
        rows, cols = rasterio.transform.rowcol(transform, x, y)
        rows = np.clip(rows, 0, slope.shape[0] - 1)
        cols = np.clip(cols, 0, slope.shape[1] - 1)
        mean = float(slope[rows, cols].mean())
        f["properties"] = {"Slope": round(mean, 1)}
        means.append(mean)
    out_path.write_text(json.dumps(doc))
    return means


def main() -> None:
    rng = np.random.default_rng(1994)
    with tempfile.TemporaryDirectory() as tmp:
        dots = [f for area in AREAS for f in stipple(area, rng)]
        stipple_path = Path(tmp) / "stipple.geojson"
        stipple_path.write_text(json.dumps({"type": "FeatureCollection", "features": dots}))
        args = ["-L", f"stipple:{stipple_path}"]
        # The script's split pieces carry slope already; whole lines get a mean slope here.
        for area in AREAS:
            args += ["-L", f"hachure_fine:{RELIEF / 'hachures' / f'{area}-fine-split.geojson'}"]
            for layer, scale, dem in (("hachure_lines", "fine", f"{area}.tif"), ("hachure_coarse", "coarse", f"{area}-90m.tif")):
                dst = Path(tmp) / f"{area}-{scale}-lines.geojson"
                means = with_mean_slope(RELIEF / "hachures" / f"{area}-{scale}-main.geojson", RELIEF / dem, dst)
                print(f"{area} {scale}: {len(means)} lines, mean slope median {np.median(means):.1f}, "
                      f">=25: {sum(m >= 25 for m in means)}, >=18: {sum(m >= 18 for m in means)}")
                args += ["-L", f"{layer}:{dst}"]
        subprocess.run(["tippecanoe", "-q", "-f", "-o", str(OUT), "-Z6", "-z13", "--no-tile-size-limit",
                        "--no-feature-limit", "--no-line-simplification", *args], check=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB); {len(dots)} stipple dots")


if __name__ == "__main__":
    main()
