"""Contact sheets for the hillshade lab packet, from the shots of hillshade-lab-shots.mjs.

Run from the repo root:
    uv run --project pipeline python tools/hillshade-sheet.py \
        <shots dir> <out.jpg> <place> <column,column,...> [--scale 0.5]
One row per zoom (8, 10, 12), one column per shot suffix (a preset id, "topo", or "<preset>-sharper"), each
labelled. Writes a JPEG under about 1 MB.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ZOOMS = [8, 10, 12]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("place")
    ap.add_argument("columns")
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--labels", help="column labels, comma-separated (default: the suffixes)")
    a = ap.parse_args()
    columns = a.columns.split(",")
    labels = a.labels.split(",") if a.labels else columns
    first = Image.open(a.shots / f"{a.place}-z{ZOOMS[0]}-{columns[0]}.jpg")
    w, h = int(first.width * a.scale), int(first.height * a.scale)
    head, side, gap = 28, 90, 4
    sheet = Image.new("RGB", (side + len(columns) * (w + gap), head + len(ZOOMS) * (h + gap)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    for c, label in enumerate(labels):
        draw.text((side + c * (w + gap) + 6, 4), label, fill="black", font=font)
    for r, z in enumerate(ZOOMS):
        draw.text((8, head + r * (h + gap) + h // 2 - 10), f"zoom {z}", fill="black", font=font)
        for c, col in enumerate(columns):
            img = Image.open(a.shots / f"{a.place}-z{z}-{col}.jpg").resize((w, h), Image.LANCZOS)
            sheet.paste(img, (side + c * (w + gap), head + r * (h + gap)))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out, "JPEG", quality=80, optimize=True)
    print(f"Wrote {a.out} ({a.out.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
