"""Build the map's MapLibre sprite from every set of drawings: the mountain glyphs and the vignettes.

Run from the repo root: uv run --project pipeline python -m art.build_sprite
Needs spreet (cargo install spreet). art.glyphs.make_glyphs and art.vignettes.make_vignettes call this after they draw.

spreet reads one directory, so the SVGs of each set are copied into a scratch directory first. A drawing's
name in the sprite is its file name without .svg. The sprite is written straight into site/public/sprites and
committed: the site build reads it from there, and CI has no Rust to run spreet.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from crossing.paths import REPO, SITE_PUBLIC

SETS = [REPO / "art" / "glyphs" / "svg", REPO / "art" / "vignettes" / "svg"]
SPRITES = SITE_PUBLIC / "sprites"
NAME = "glyphs"


def spreet() -> str:
    """spreet from PATH, or from cargo's bin folder, where `cargo install` puts it."""
    search = os.pathsep.join([os.environ.get("PATH", ""), str(Path.home() / ".cargo" / "bin")])
    found = shutil.which("spreet", path=search)
    if not found:
        sys.exit("spreet not found: cargo install spreet")
    return found


def build_sprite() -> None:
    SPRITES.mkdir(parents=True, exist_ok=True)
    tool = spreet()
    with tempfile.TemporaryDirectory() as scratch:
        count = 0
        for folder in SETS:
            for svg in folder.glob("*.svg"):
                (Path(scratch) / svg.name).write_bytes(svg.read_bytes())
                count += 1
        for extra in ([], ["--retina"]):
            out = SPRITES / (f"{NAME}@2x" if extra else NAME)
            subprocess.run([tool, *extra, scratch, str(out)], check=True)
    print(f"{count} drawings; sprite at {(SPRITES / NAME).relative_to(REPO)}")


if __name__ == "__main__":
    build_sprite()
