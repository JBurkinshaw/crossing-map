"""Build tiles/out/relief.pmtiles: the production hachures and contours (decision 0016).

Run from the repo root, after crossing.hachures:
    uv run --project pipeline python tiles/build_relief.py

Layers, from private/cache/relief/production/, all zoom 10-12 (the map over-zooms to 13):
  coarse   hachures from the 90 m DEM, outside the journeys corridor
  fine     short hachure strokes from the 30 m DEM, inside the corridor
  contour  50 m contours (`Ele`, metres)
Hachures carry `Slope`, `Aspect` and `Rand` for the style; crossing.hachures describes them.
"""

import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "private" / "cache" / "relief" / "production"
OUT = REPO / "tiles" / "out" / "relief.pmtiles"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # No simplification: hachures are short, and simplifying bends them off the fall line.
    # Run from the sources' folder with relative names: tippecanoe records its command line in the
    # archive's metadata, and the archive is published.
    subprocess.run(["tippecanoe", "-q", "-f", "-o", "relief.pmtiles", "-Z10", "-z12", "--no-line-simplification",
                    "--no-tile-size-limit", "--no-feature-limit",
                    "-n", "The Crossing: hachures", "-N", "Hachures and contours from Copernicus GLO-30 (decision 0016)",
                    "-L", "coarse:coarse.geojson", "-L", "fine:fine.geojson", "-L", "contour:contour.geojson"], check=True, cwd=SRC)
    shutil.move(SRC / "relief.pmtiles", OUT)
    print(f"Wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
