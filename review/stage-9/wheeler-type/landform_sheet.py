"""A review sheet of the landform label lines over a hillshade, to check each axis by eye.

Run from the repo root:
    uv run --project pipeline python review/stage-9/wheeler-type/landform_sheet.py [W S E N] [OUT]
Defaults to the Wheeler test area (109.6 to 108.4° W, 30.5 to 31.6° N) and writes
private/review/stage-9/wheeler-type/landform-sheet.png (git-ignored). Lines from the book are drawn dark red,
GMBA lines blue, GNIS valleys green, DEM lines black; hand-edited lines are dashed in the colour of their source.
"""

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

from crossing.dem import COPERNICUS, COPERNICUS_REGION, build_vrt, tiles
from crossing.paths import DATA, PRIVATE

BOX = tuple(map(float, sys.argv[1:5])) if len(sys.argv) >= 5 else (-109.6, 30.5, -108.4, 31.6)
OUT = Path(sys.argv[5]) if len(sys.argv) >= 6 else PRIVATE / "review/stage-9/wheeler-type/landform-sheet.png"
PAD = 0.15
WIDTH = 1800
COLOUR = {"gmba": (40, 70, 170), "gnis": (30, 120, 60), "dem": (20, 20, 20)}


def main() -> None:
    w, s, e, n = BOX[0] - PAD, BOX[1] - PAD, BOX[2] + PAD, BOX[3] + PAD
    kx = math.cos(math.radians((s + n) / 2))
    height = int(WIDTH * (n - s) / ((e - w) * kx))
    with tempfile.TemporaryDirectory() as tmp, \
            rasterio.open(build_vrt(Path(tmp) / "dem.vrt", tiles(COPERNICUS, COPERNICUS_REGION))) as dem:
        z = dem.read(1, window=from_bounds(w, s, e, n, dem.transform), out_shape=(height, WIDTH),
                     resampling=Resampling.average).astype(float)
    cell = (e - w) * 111320 * kx / WIDTH
    gy, gx = np.gradient(z, cell)
    # Light from the north-west at 45°.
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    shade = np.cos(math.radians(45)) * np.cos(slope) + np.sin(math.radians(45)) * np.sin(slope) * np.cos(
        math.radians(315) - aspect)
    img = Image.fromarray((np.clip(shade, 0, 1) * 120 + 125).astype(np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(img)

    def px(lon, lat):
        return (lon - w) / (e - w) * WIDTH, (n - lat) / (n - s) * height

    # The test area's frame.
    draw.rectangle([px(BOX[0], BOX[3]), px(BOX[2], BOX[1])], outline=(200, 120, 0), width=2)
    for f in json.loads((DATA / "landforms.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        pts = [px(*c) for c in f["geometry"]["coordinates"]]
        if not any(0 <= x <= WIDTH and 0 <= y <= height for x, y in pts):
            continue
        colour = (150, 20, 20) if p["place_ref"] else COLOUR[p["axis"]]
        if p["reasoning"]:
            for a, b in zip(pts, pts[1:], strict=False):
                for t in np.arange(0, 1, 0.1):
                    draw.line([(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                               (a[0] + (b[0] - a[0]) * (t + 0.05), a[1] + (b[1] - a[1]) * (t + 0.05))],
                              fill=colour, width=4)
        else:
            draw.line(pts, fill=colour, width=3)
        mx, my = pts[len(pts) // 2] if len(pts) > 2 else ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
        label = f"{p['name']} ({p['kind']}, {p['axis']}, {p['len_m'] / 1000:.0f} km)"
        draw.text((mx + 4, my + 4), label, fill=colour, font_size=18)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
