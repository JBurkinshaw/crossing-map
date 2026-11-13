"""Build the map's MapLibre sprite from every set of drawings: the mountain glyphs and the vignettes.

Run from the repo root: uv run --project pipeline python art/build_sprite.py
Needs spreet (cargo install spreet). make_glyphs.py and make_vignettes.py call this after they draw.

spreet reads one directory, so the SVGs of each set are copied into a scratch directory first. A drawing's
name in the sprite is its file name without .svg.

Two sheets are built, one per theme of the map (site/src/map/tokens.ts): glyphs, as drawn, and
glyphs-lamplight, in which the drawings' ink and paper colours are swapped for the lamplight theme's, so
each drawing's paper fill knocks out the hachures on the dark paper (plan 5.2, layer 2, step 4). Both
sheets hold the same drawings at the same sizes, so their indexes match.
"""

import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SETS = [REPO / "art" / "glyphs" / "svg", REPO / "art" / "vignettes" / "svg"]
SPRITES = REPO / "site" / "public" / "sprites"
# The drawings' ink and paper (art/glyphs/make_glyphs.py, art/vignettes/make_vignettes.py), and their colours
# in each theme's sheet: the palettes' ink and paper in site/src/map/tokens.ts.
INK, PAPER = "#2b2118", "#e4ddcc"
THEMES = {
    "glyphs": {},
    "glyphs-lamplight": {INK: "#e6d9c0", PAPER: "#1d1915"},
}


def build_sprite() -> None:
    SPRITES.mkdir(parents=True, exist_ok=True)
    for name, colours in THEMES.items():
        with tempfile.TemporaryDirectory() as scratch:
            count = 0
            for folder in SETS:
                for svg in folder.glob("*.svg"):
                    text = svg.read_text()
                    for old, new in colours.items():
                        if old not in text:
                            raise SystemExit(f"{svg.name}: no {old} to recolour for {name}")
                        text = text.replace(old, new)
                    (Path(scratch) / svg.name).write_text(text)
                    count += 1
            for extra in ([], ["--retina"]):
                out = SPRITES / (f"{name}@2x" if extra else name)
                subprocess.run([str(Path.home() / ".cargo" / "bin" / "spreet"), *extra, scratch, str(out)], check=True)
        print(f"{count} drawings; sprite at {(SPRITES / name).relative_to(REPO)}")


if __name__ == "__main__":
    build_sprite()
