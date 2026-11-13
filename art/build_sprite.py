"""Build the map's MapLibre sprite from every set of drawings: the mountain glyphs and the vignettes.

Run from the repo root: uv run --project pipeline python art/build_sprite.py
Needs spreet (cargo install spreet). make_glyphs.py and make_vignettes.py call this after they draw.

spreet reads one directory, so the SVGs of each set are copied into a scratch directory first. A drawing's
name in the sprite is its file name without .svg.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SETS = [REPO / "art" / "glyphs" / "svg", REPO / "art" / "vignettes" / "svg"]
SPRITE = REPO / "site" / "public" / "sprites" / "glyphs"


def build_sprite() -> None:
    with tempfile.TemporaryDirectory() as scratch:
        count = 0
        for folder in SETS:
            for svg in folder.glob("*.svg"):
                shutil.copy(svg, scratch)
                count += 1
        SPRITE.parent.mkdir(parents=True, exist_ok=True)
        for extra in ([], ["--retina"]):
            out = f"{SPRITE}@2x" if extra else str(SPRITE)
            subprocess.run([str(Path.home() / ".cargo" / "bin" / "spreet"), *extra, scratch, out], check=True)
    print(f"{count} drawings; sprite at {SPRITE.relative_to(REPO)}")


if __name__ == "__main__":
    build_sprite()
