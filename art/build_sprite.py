"""Build the map's MapLibre sprite from every set of drawings: the mountain glyphs and the vignettes.

Run from the repo root: uv run --project pipeline python art/build_sprite.py
Needs spreet (cargo install spreet). make_glyphs.py and make_vignettes.py call this after they draw.

spreet reads one directory, so the SVGs of each set are copied into a scratch directory first. A drawing's
name in the sprite is its file name without .svg.
"""

import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SETS = [REPO / "art" / "glyphs" / "svg", REPO / "art" / "vignettes" / "svg"]
SPRITES = REPO / "site" / "public" / "sprites"
NAME = "glyphs"


def build_sprite() -> None:
    SPRITES.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        count = 0
        for folder in SETS:
            for svg in folder.glob("*.svg"):
                (Path(scratch) / svg.name).write_bytes(svg.read_bytes())
                count += 1
        for extra in ([], ["--retina"]):
            out = SPRITES / (f"{NAME}@2x" if extra else NAME)
            subprocess.run([str(Path.home() / ".cargo" / "bin" / "spreet"), *extra, scratch, str(out)], check=True)
    print(f"{count} drawings; sprite at {(SPRITES / NAME).relative_to(REPO)}")


if __name__ == "__main__":
    build_sprite()
