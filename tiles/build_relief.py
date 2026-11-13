"""Build the relief archives in tiles/out/ (decision 0016; zoom 12 density, plan 5.2).

Run from the repo root, after crossing.hachures:
    uv run --project pipeline python tiles/build_relief.py

From private/cache/relief/production/, three archives so each stays under 100 MB (plan 5.2), and a reader who
stays zoomed out never fetches the dense strokes:
  relief.pmtiles        coarse  hachures from the 90 m DEM, outside the journeys corridor, zoom 10-12
                        fine    short hachure strokes from the 30 m DEM, inside the corridor, zoom 10-12
  relief-dense.pmtiles  dense   the fine strokes closer together, for zoom 12 and up
  contours.pmtiles      contour 50 m contours (`Ele`, metres), zoom 10-12
The map over-zooms each to 13. Hachures carry `Slope`, `Aspect` and `Rand`; crossing.hachures describes them.
"""

import shutil
import subprocess
from pathlib import Path

from crossing.hachures import COPERNICUS

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "private" / "cache" / "relief" / "production"
OUT = REPO / "tiles" / "out"
# archive: (name, minzoom, maxzoom, layers)
ARCHIVES = {
    "relief": ("The Crossing: hachures", 10, 12, ["coarse", "fine"]),
    "relief-dense": ("The Crossing: dense hachures", 12, 12, ["dense"]),
    "contours": ("The Crossing: contours", 10, 12, ["contour"]),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for archive, (title, minzoom, maxzoom, layers) in ARCHIVES.items():
        # No simplification: hachures are short, and simplifying bends them off the fall line.
        # Run from the sources' folder with relative names: tippecanoe records its command line in the
        # archive's metadata, and the archive is published.
        subprocess.run(["tippecanoe", "-q", "-f", "-o", f"{archive}.pmtiles", f"-Z{minzoom}", f"-z{maxzoom}",
                        "--no-line-simplification", "--no-tile-size-limit", "--no-feature-limit",
                        "-n", title, "-N", "From Copernicus GLO-30 (decision 0016)",
                        # MapLibre shows this in the map's attribution; decision 0011 also wants it on the Credits page.
                        "-A", COPERNICUS, *[a for layer in layers for a in ("-L", f"{layer}:{layer}.geojson")]],
                       check=True, cwd=SRC)
        out = OUT / f"{archive}.pmtiles"
        shutil.move(SRC / f"{archive}.pmtiles", out)
        print(f"Wrote {out.relative_to(REPO)} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
