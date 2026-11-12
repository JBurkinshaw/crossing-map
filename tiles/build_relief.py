"""Build tiles/out/relief.pmtiles: the production hachures (decision 0014).

Run from the repo root, after crossing.hachures:
    uv run --project pipeline python tiles/build_relief.py

Layers, from private/cache/relief/production/:
  coarse  hachures from the 90 m DEM, wherever the DEM covers: zoom 6-9 inside the journeys
          corridor, 6-13 outside it
  fine    hachures from the 30 m DEM, zoom 10-13, inside the journeys corridor
Each line carries its mean slope (`Slope`, degrees) for the style's line width.
Each feature's zoom range comes from its `tippecanoe` member, set by crossing.hachures.
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
    subprocess.run(["tippecanoe", "-q", "-f", "-o", "relief.pmtiles", "-Z6", "-z13", "--no-line-simplification",
                    "--no-tile-size-limit", "--no-feature-limit",
                    "-n", "The Crossing: hachures", "-N", "Hachures from Copernicus GLO-30 (decision 0014)",
                    "-L", "coarse:coarse.geojson", "-L", "fine:fine.geojson"], check=True, cwd=SRC)
    shutil.move(SRC / "relief.pmtiles", OUT)
    print(f"Wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
