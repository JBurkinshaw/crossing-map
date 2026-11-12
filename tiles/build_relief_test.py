"""Build tiles/out/relief-test.pmtiles for the relief comparison sheet (stage 3).

Run from the repo root: uv run --project pipeline python tiles/build_relief_test.py
Layers, from the three test areas only:
  hachure_fine    the split hachures from the 30 m runs, with their Slope (degrees)
  hachure_coarse  whole hachure lines from the 90 m runs
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


def main() -> None:
    rng = np.random.default_rng(1994)
    with tempfile.TemporaryDirectory() as tmp:
        dots = [f for area in AREAS for f in stipple(area, rng)]
        stipple_path = Path(tmp) / "stipple.geojson"
        stipple_path.write_text(json.dumps({"type": "FeatureCollection", "features": dots}))
        args = ["-L", f"stipple:{stipple_path}"]
        # Fine: the split pieces, which carry slope for weighted widths. Coarse: whole hachure lines,
        # which read as relief at small scale where the short pieces read as scattered ticks.
        for scale, part in (("fine", "split"), ("coarse", "main")):
            for area in AREAS:
                args += ["-L", f"hachure_{scale}:{RELIEF / 'hachures' / f'{area}-{scale}-{part}.geojson'}"]
        subprocess.run(["tippecanoe", "-q", "-f", "-o", str(OUT), "-Z6", "-z13", "--no-tile-size-limit",
                        "--no-feature-limit", "--no-line-simplification", *args], check=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB); {len(dots)} stipple dots")


if __name__ == "__main__":
    main()
