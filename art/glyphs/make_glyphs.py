"""Generate the mountain glyph SVGs and build the MapLibre sprite (plan section 5.2, layer 2).

Run from the repo root: uv run --project pipeline python art/glyphs/make_glyphs.py
Needs spreet (cargo install spreet).

Each glyph is a profile mountain in one ink weight, filled with paper so it
knocks out the hachures behind it, lit from the north-west: a spur line runs
down from the summit and short hatch strokes shade the south-east flank.
Shapes are random but seeded, so a rebuild draws the same 12. Each has a
mirrored twin ("-flip") whose silhouette is reversed but whose hatching is
redrawn on the right, so the light stays in the north-west.
"""

import random
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SVG_DIR = Path(__file__).parent / "svg"
SPRITE = REPO / "site" / "public" / "sprites" / "glyphs"
INK, PAPER = "#2b2118", "#e4ddcc"
W, H = 64, 44  # canvas in px at 1x
COUNT = 12


def silhouette(rng: random.Random) -> list[tuple[float, float]]:
    """Points from the left foot over one or two summits to the right foot."""
    base = H - 3
    width = rng.uniform(44, 58)
    left = (W - width) / 2
    peak_x = left + width * rng.uniform(0.38, 0.55)
    peak_y = rng.uniform(5, 13)
    pts = [(left, base)]
    # Rise in a few jittered steps, with an optional shoulder.
    for f in (0.3, 0.6, 0.85):
        x = left + (peak_x - left) * f
        y = base - (base - peak_y) * (f ** 1.3) + rng.uniform(-2, 2)
        pts.append((x, y))
    pts.append((peak_x, peak_y))
    right = left + width
    if rng.random() < 0.45:  # a lower second summit on the right
        sx = peak_x + (right - peak_x) * rng.uniform(0.35, 0.5)
        pts += [(peak_x + (sx - peak_x) * 0.5, peak_y + rng.uniform(6, 10)), (sx, peak_y + rng.uniform(2, 6))]
    for f in (0.35, 0.65, 0.9):
        x = pts[-1][0] + (right - pts[-1][0]) * f
        y = pts[-1][1] + (base - pts[-1][1]) * (f ** 0.9) + rng.uniform(-1.5, 1.5)
        pts.append((x, y))
    pts.append((right, base))
    return pts


def edge_x(pts: list[tuple[float, float]], y: float, right: bool) -> float | None:
    """x where the outline crosses height y, on the right or left flank."""
    xs = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if min(y1, y2) <= y <= max(y1, y2) and y1 != y2:
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    if not xs:
        return None
    return max(xs) if right else min(xs)


def svg(pts: list[tuple[float, float]], rng: random.Random) -> str:
    top = min(pts, key=lambda p: p[1])
    base = H - 3
    # The spur: from the summit down and a little right, dividing lit and shaded flanks.
    spur_end = (top[0] + rng.uniform(4, 9), base - rng.uniform(0, 3))
    spur_mid = ((top[0] + spur_end[0]) / 2 + rng.uniform(-1.5, 1.5), (top[1] + spur_end[1]) / 2)

    def spur_x(y: float) -> float:
        (x1, y1), (x2, y2) = ((top, spur_mid) if y <= spur_mid[1] else (spur_mid, spur_end))
        return x1 + (y - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else x1

    hatches = []
    y = top[1] + 4
    while y < base - 1.5:
        x1, x2 = spur_x(y) + 1, edge_x(pts, y, right=True)
        if x2 is not None and x2 - x1 > 2.5:
            length = (x2 - x1) * rng.uniform(0.55, 0.85)
            # Strokes slope down to the right, roughly with the flank, as on the survey sheets.
            hatches.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x1 + length:.1f}" y2="{y + length * 0.45:.1f}"/>')
        y += 2.8
    outline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    spur = f"M{top[0]:.1f},{top[1]:.1f} Q{spur_mid[0]:.1f},{spur_mid[1]:.1f} {spur_end[0]:.1f},{spur_end[1]:.1f}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<defs><clipPath id="m"><polygon points="{outline}"/></clipPath></defs>'
        f'<polygon points="{outline}" fill="{PAPER}" stroke="none"/>'
        f'<g fill="none" stroke="{INK}" stroke-linecap="round" stroke-linejoin="round">'
        f'<polyline points="{outline}" stroke-width="1.5"/>'
        f'<path d="{spur}" stroke-width="1"/>'
        f'<g stroke-width="0.8" clip-path="url(#m)">{"".join(hatches)}</g>'
        f"</g></svg>"
    )


def main() -> None:
    SVG_DIR.mkdir(exist_ok=True)
    for i in range(1, COUNT + 1):
        rng = random.Random(f"mountain-{i}")
        pts = silhouette(rng)
        (SVG_DIR / f"mountain-{i:02d}.svg").write_text(svg(pts, random.Random(f"hatch-{i}")))
        mirrored = [(W - x, y) for x, y in reversed(pts)]
        (SVG_DIR / f"mountain-{i:02d}-flip.svg").write_text(svg(mirrored, random.Random(f"hatch-{i}")))
    SPRITE.parent.mkdir(parents=True, exist_ok=True)
    for extra in ([], ["--retina"]):
        out = f"{SPRITE}@2x" if extra else str(SPRITE)
        subprocess.run([str(Path.home() / ".cargo" / "bin" / "spreet"), *extra, str(SVG_DIR), out], check=True)
    print(f"{COUNT * 2} glyphs; sprite at {SPRITE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
