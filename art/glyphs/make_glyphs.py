"""Generate the mountain glyph SVGs and build the MapLibre sprite (plan section 5.2, layer 2).

Run from the repo root: uv run --project pipeline python art/glyphs/make_glyphs.py
Needs spreet (cargo install spreet).

One family of COUNT shapes per landform (crossing.landforms), named
<landform>-<nn>.svg: peak, dome, mesa, butte, cone and ridge. Each glyph is a
profile in one ink weight, filled with paper so it knocks out the hachures
behind it, and lit from the north-west. Peaks and cones have a spur line down
from the summit with hatching between it and the south-east flank. The other
families hatch every flank that faces right, and mesas and buttes get a caprock line
under the rim. Shapes are random but seeded, so a rebuild draws the same set.
Each has a mirrored twin ("-flip") whose silhouette is reversed but whose
hatching is redrawn on the right, so the light stays in the north-west.
"""

import math
import random
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SVG_DIR = Path(__file__).parent / "svg"
SPRITE = REPO / "site" / "public" / "sprites" / "glyphs"
INK, PAPER = "#2b2118", "#e4ddcc"
COUNT = 12  # shapes per family
Point = tuple[float, float]


# Silhouettes. Each returns the outline from the left foot to the right foot, and
# any extra lines (the caprock), in a canvas of the family's width and height.

def peak(rng: random.Random, W: float, H: float) -> tuple[list[Point], list[list[Point]]]:
    """One or two summits."""
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
    return pts, []


def dome(rng: random.Random, W: float, H: float) -> tuple[list[Point], list[list[Point]]]:
    """A rounded hill: a bell curve with a round crown and flaring feet, sometimes with a lower second hump."""
    base = H - 3
    width, height = rng.uniform(46, 58), rng.uniform(15, 24)
    left = (W - width) / 2
    k = rng.uniform(1.3, 2.4)  # higher is narrower in the crown and longer in the feet
    skew = rng.uniform(-0.12, 0.12)  # moves the crown off centre
    pts = []
    for i in range(25):
        t = -1 + 2 * i / 24
        tt = t - skew * (1 - t * t)
        y = base - height * (math.exp(-k * tt * tt) - math.exp(-k)) / (1 - math.exp(-k))
        pts.append((left + width * (t + 1) / 2, y))
    if rng.random() < 0.35:  # a lower hump on the right
        hx, hw, hh = left + width * rng.uniform(0.72, 0.82), width * 0.22, height * rng.uniform(0.4, 0.55)
        pts = [(x, min(y, base - hh * max(0.0, 1 - ((x - hx) / hw) ** 2))) for x, y in pts]
    return pts, []


def tableland(rng: random.Random, W: float, H: float, width: float, top: float, height: float,
              cliff: float) -> tuple[list[Point], list[list[Point]]]:
    """A flat top on cliffs over talus slopes: `top` is the rim width, `cliff` the cliff's share of `height`."""
    base = H - 3
    left = (W - width) / 2
    rim_y = base - height
    cliff_y = rim_y + height * cliff
    rim_l = W / 2 - top / 2 + rng.uniform(-2, 2)
    rim_r = rim_l + top
    foot_l, foot_r = rim_l - rng.uniform(0.5, 2), rim_r + rng.uniform(0.5, 2)  # cliffs lean out a little
    pts = [(left, base)]
    # Concave talus up to the cliff foot.
    for f in (0.35, 0.65, 0.88):
        pts.append((left + (foot_l - left) * f, base - (base - cliff_y) * f ** 2 + rng.uniform(-0.6, 0.6)))
    pts += [(foot_l, cliff_y), (rim_l, rim_y + rng.uniform(0, 1))]
    # The top: nearly level, with a few small steps.
    for f in (0.25, 0.5, 0.75):
        pts.append((rim_l + top * f, rim_y + rng.uniform(-0.8, 0.8)))
    pts += [(rim_r, rim_y + rng.uniform(0, 1)), (foot_r, cliff_y)]
    right = left + width
    for f in (0.12, 0.35, 0.65):
        pts.append((foot_r + (right - foot_r) * f, cliff_y + (base - cliff_y) * (1 - (1 - f) ** 2) + rng.uniform(-0.6, 0.6)))
    pts.append((right, base))
    caprock = [(rim_l + 1.2, rim_y + 2.6), (rim_r - 1.2, rim_y + 2.6 + rng.uniform(-0.4, 0.4))]
    return pts, [caprock]


def mesa(rng: random.Random, W: float, H: float) -> tuple[list[Point], list[list[Point]]]:
    width = rng.uniform(62, 74)
    return tableland(rng, W, H, width, width * rng.uniform(0.45, 0.6), rng.uniform(13, 20), rng.uniform(0.35, 0.5))


def butte(rng: random.Random, W: float, H: float) -> tuple[list[Point], list[list[Point]]]:
    return tableland(rng, W, H, rng.uniform(30, 40), rng.uniform(8, 13), rng.uniform(22, 30), rng.uniform(0.5, 0.65))


def cone(rng: random.Random, W: float, H: float) -> tuple[list[Point], list[list[Point]]]:
    """A symmetric cone with straight, slightly concave sides and a crater notch."""
    base = H - 3
    width, height, crater = rng.uniform(40, 52), rng.uniform(16, 24), rng.uniform(4, 8)
    left, top_y = (W - width) / 2, base - height
    cl, cr = W / 2 - crater / 2, W / 2 + crater / 2
    pts = [(left, base)]
    for f in (0.3, 0.6, 0.85):
        pts.append((left + (cl - left) * f, base - height * f ** 1.15))
    pts += [(cl, top_y), (W / 2, top_y + rng.uniform(0.8, 1.6)), (cr, top_y + rng.uniform(-0.3, 0.3))]
    right = left + width
    for f in (0.15, 0.4, 0.7):
        pts.append((cr + (right - cr) * f, top_y + height * (1 - (1 - f) ** 1.15)))
    pts.append((right, base))
    return pts, []


def ridge(rng: random.Random, W: float, H: float) -> tuple[list[Point], list[list[Point]]]:
    """A long crest of several summits, highest near the middle."""
    base = H - 3
    width, height = rng.uniform(72, 84), rng.uniform(13, 20)
    left = (W - width) / 2
    teeth = rng.randint(4, 7)
    pts = [(left, base)]
    for i in range(teeth):
        # Each tooth: a summit and the saddle after it, under an arched envelope.
        f = (i + 0.5) / teeth
        crest = base - height * (0.55 + 0.45 * math.sin(math.pi * f)) * rng.uniform(0.85, 1.0)
        x = left + width * (0.08 + 0.84 * f) + rng.uniform(-1.5, 1.5)
        pts.append((x, crest))
        if i < teeth - 1:
            pts.append((x + width * 0.84 / teeth * rng.uniform(0.35, 0.65), crest + rng.uniform(2, 7)))
    pts.append((left + width, base))
    return pts, []


FAMILIES = {  # landform: (silhouette, canvas width, canvas height)
    "peak": (peak, 64, 44),
    "dome": (dome, 64, 40),
    "mesa": (mesa, 80, 40),
    "butte": (butte, 52, 44),
    "cone": (cone, 60, 40),
    "ridge": (ridge, 90, 36),
}


def edge_x(pts: list[Point], y: float, right: bool) -> float | None:
    """x where the outline crosses height y, on the right or left flank."""
    xs = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if min(y1, y2) <= y <= max(y1, y2) and y1 != y2:
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    if not xs:
        return None
    return max(xs) if right else min(xs)


def peak_marks(pts: list[Point], rng: random.Random, H: float) -> tuple[list[str], list[str]]:
    """A peak's hatching, between a spur from the summit and the south-east flank, and the spur."""
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
    spur = f"M{top[0]:.1f},{top[1]:.1f} Q{spur_mid[0]:.1f},{spur_mid[1]:.1f} {spur_end[0]:.1f},{spur_end[1]:.1f}"
    return hatches, [f'<path d="{spur}" stroke-width="1"/>']


def face_hatches(pts: list[Point], rng: random.Random, hang: bool) -> list[str]:
    """Strokes running inward from every stretch of outline that falls to the right (faces south-east).

    Strokes run up and to the left, the same lie as the peaks' strokes, or hang
    down from the crest (`hang`), for shapes too thin to hold the first kind.
    """
    hatches = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = math.hypot(x2 - x1, y2 - y1)
        # Only stretches that fall to the right; level ground and left-facing flanks are lit.
        if x2 < x1 or y2 - y1 < 0.25 * (x2 - x1) or seg < 1:
            continue
        n = max(1, round(seg / 2.2))
        for k in range(n):
            t = (k + rng.uniform(0.3, 0.7)) / n
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            if hang:
                length = rng.uniform(3, 7)
                end = (x - length * 0.35, y + length)
            else:
                length = rng.uniform(5, 11)
                end = (x + 0.6 - length, y - length * 0.3)
            hatches.append(f'<line x1="{x + 0.6:.1f}" y1="{y:.1f}" x2="{end[0]:.1f}" y2="{end[1]:.1f}"/>')
    return hatches


def svg(family: str, pts: list[Point], extras: list[list[Point]], rng: random.Random, W: float, H: float) -> str:
    # Cones take the peaks' spur and hatching; the rest hatch their south-east faces.
    if family in ("peak", "cone"):
        hatches, marks = peak_marks(pts, rng, H)
    else:
        hatches, marks = face_hatches(pts, rng, hang=family == "ridge"), []
    marks += [f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in line)}" stroke-width="0.8"/>' for line in extras]
    outline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<defs><clipPath id="m"><polygon points="{outline}"/></clipPath></defs>'
        f'<polygon points="{outline}" fill="{PAPER}" stroke="none"/>'
        f'<g fill="none" stroke="{INK}" stroke-linecap="round" stroke-linejoin="round">'
        f'<polyline points="{outline}" stroke-width="1.5"/>'
        f'{"".join(marks)}'
        f'<g stroke-width="0.8" clip-path="url(#m)">{"".join(hatches)}</g>'
        f"</g></svg>"
    )


def mirror(line: list[Point], W: float) -> list[Point]:
    return [(W - x, y) for x, y in reversed(line)]


def main() -> None:
    SVG_DIR.mkdir(exist_ok=True)
    for old in SVG_DIR.glob("*.svg"):
        old.unlink()
    for family, (shape, W, H) in FAMILIES.items():
        for i in range(1, COUNT + 1):
            # Peaks keep the seeds they were first drawn with, so they do not change.
            seed = f"mountain-{i}" if family == "peak" else f"{family}-{i}"
            hatch_seed = f"hatch-{i}" if family == "peak" else f"{family}-hatch-{i}"
            pts, extras = shape(random.Random(seed), W, H)
            (SVG_DIR / f"{family}-{i:02d}.svg").write_text(svg(family, pts, extras, random.Random(hatch_seed), W, H))
            (SVG_DIR / f"{family}-{i:02d}-flip.svg").write_text(
                svg(family, mirror(pts, W), [mirror(e, W) for e in extras], random.Random(hatch_seed), W, H))
    SPRITE.parent.mkdir(parents=True, exist_ok=True)
    for extra in ([], ["--retina"]):
        out = f"{SPRITE}@2x" if extra else str(SPRITE)
        subprocess.run([str(Path.home() / ".cargo" / "bin" / "spreet"), *extra, str(SVG_DIR), out], check=True)
    print(f"{len(FAMILIES) * COUNT * 2} glyphs in {len(FAMILIES)} families; sprite at {SPRITE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
