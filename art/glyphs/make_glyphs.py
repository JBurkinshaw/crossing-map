"""Generate the mountain glyph SVGs and build the MapLibre sprite (design section 5.2, layer 2).

Run from the repo root: uv run --project pipeline python -m art.glyphs.make_glyphs
Needs spreet (cargo install spreet). The sprite also holds the vignettes (art.build_sprite).

One family of SHAPES_PER_FAMILY shapes per landform (crossing.landforms), named
<landform>-<nn>.svg: peak, dome, mesa, butte, cone, ridge and pass. Each glyph is a
profile in one ink weight, filled with paper so it knocks out the hachures
behind it, and lit from the north-west. Peaks and cones have a spur line down
from the summit with hatching between it and the south-east flank. The other
families hatch every flank that faces right, and mesas and buttes get a caprock line
under the rim. Shapes are random but seeded, so a rebuild draws the same set.
Each has a mirrored twin ("-flip") whose silhouette is reversed but whose
hatching is redrawn on the right, so the light stays in the north-west.
"""

import itertools
import math
import random
from pathlib import Path

from art import INK, PAPER
from art.build_sprite import build_sprite
from art.pen import PEN, Pen, break_lines, extend, normals, ribbon, wobble
from crossing.glyphs import SHAPES_PER_FAMILY

SVG_DIR = Path(__file__).parent / "svg"
Point = tuple[float, float]
SPUR_SHARE = 1.0  # share of a peak's spur line drawn, from the summit down


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
        y = cliff_y + (base - cliff_y) * (1 - (1 - f) ** 2) + rng.uniform(-0.6, 0.6)
        pts.append((foot_r + (right - foot_r) * f, y))
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


def saddle(rng: random.Random, W: float, H: float) -> tuple[list[Point], list[list[Point]]]:
    """A pass: two rounded shoulders and the broad dip of the col between them, lower than a twin peak."""
    base = H - 3
    width, height = rng.uniform(42, 50), rng.uniform(11, 14)
    left = (W - width) / 2
    right_share = rng.uniform(0.8, 0.95)  # the right shoulder is a little lower
    cl, cr, s = rng.uniform(0.24, 0.3), rng.uniform(0.7, 0.76), rng.uniform(0.13, 0.16)

    def bumps(t: float) -> float:
        return math.exp(-((t - cl) ** 2) / (2 * s * s)) + right_share * math.exp(-((t - cr) ** 2) / (2 * s * s))

    # Less a straight line between the two ends, so both feet touch the ground.
    ts = [i / 28 for i in range(29)]
    lift = [bumps(t) - (bumps(0) + (bumps(1) - bumps(0)) * t) for t in ts]
    k = height / max(lift)
    pts = [(left + width * t, base - k * v) for t, v in zip(ts, lift, strict=True)]
    return pts, []


FAMILIES = {  # landform: (silhouette, canvas width, canvas height)
    "peak": (peak, 64, 44),
    "dome": (dome, 64, 40),
    "mesa": (mesa, 80, 40),
    "butte": (butte, 52, 44),
    "cone": (cone, 60, 40),
    "ridge": (ridge, 90, 36),
    "pass": (saddle, 52, 26),
}


def edge_x(pts: list[Point], y: float, right: bool) -> float | None:
    """x where the outline crosses height y, on the right or left flank."""
    xs = []
    for (x1, y1), (x2, y2) in itertools.pairwise(pts):
        if min(y1, y2) <= y <= max(y1, y2) and y1 != y2:
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    if not xs:
        return None
    return max(xs) if right else min(xs)


def peak_hatches(pts: list[Point], rng: random.Random, H: float, st: Pen) -> tuple[list[list[Point]], list[Point]]:
    """Hatches between a spur from the summit and the south-east flank, and the spur's own line."""
    top = min(pts, key=lambda p: p[1])
    base = H - 3
    spur_end = (top[0] + rng.uniform(4, 9), base - rng.uniform(0, 3))
    spur_mid = ((top[0] + spur_end[0]) / 2 + rng.uniform(-1.5, 1.5), (top[1] + spur_end[1]) / 2)
    spur = [top, spur_mid, spur_end]

    def spur_x(y: float) -> float:
        (x1, y1), (x2, y2) = (top, spur_mid) if y <= spur_mid[1] else (spur_mid, spur_end)
        return x1 + (y - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else x1

    lines = []
    y = top[1] + 4 + rng.uniform(-0.5, 0.5) * st.hatch_jitter
    stop = top[1] + (base - 1.5 - top[1]) * st.hatch_reach
    j = st.hatch_jitter
    while y < stop:
        x1, x2 = spur_x(y) + 1, edge_x(pts, y, right=True)
        if x2 is not None and x2 - x1 > 2.5 and rng.random() < st.hatch_share:
            length = (x2 - x1) * rng.uniform(0.55, 0.85) * (1 + rng.uniform(-0.25, 0.15) * j)
            slope = 0.45 + rng.uniform(-0.15, 0.15) * j
            sx = x1 + rng.uniform(-0.4, 0.6) * j
            lines.append([(sx, y), (sx + length, y + length * slope)])
        y += st.hatch_gap * (1 + rng.uniform(-0.3, 0.3) * j)
    return lines, spur


def face_hatches(pts: list[Point], rng: random.Random, hang: bool, st: Pen) -> list[list[Point]]:
    """Strokes running inward from every stretch of outline that falls to the right (faces south-east)."""
    j = st.hatch_jitter
    top_y = min(y for _, y in pts)
    base_y = max(y for _, y in pts)
    lines = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:], strict=False):
        seg = math.hypot(x2 - x1, y2 - y1)
        if x2 < x1 or y2 - y1 < 0.25 * (x2 - x1) or seg < 1:
            continue
        n = max(1, round(seg / (st.hatch_gap * 0.8)))
        for k in range(n):
            t = (k + rng.uniform(0.5 - 0.2 - 0.2 * j, 0.5 + 0.2 + 0.2 * j)) / n
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            if (y - top_y) > st.hatch_reach * (base_y - top_y) + 0.5 or rng.random() > st.hatch_share:
                continue
            if hang:
                length = rng.uniform(3, 7) * (1 + rng.uniform(-0.2, 0.2) * j)
                lean = 0.35 + rng.uniform(-0.15, 0.15) * j
                end = (x - length * lean, y + length)
            else:
                length = rng.uniform(5, 11) * (1 + rng.uniform(-0.25, 0.15) * j)
                lift = 0.3 + rng.uniform(-0.12, 0.12) * j
                end = (x + 0.6 - length, y - length * lift)
            lines.append([(x + 0.6, y), end])
    return lines


def split_outline(pts: list[Point], family: str, rng: random.Random) -> list[list[Point]]:
    """Where the pen lifts: at the summit for single-summit shapes, at the rim corners of tablelands,
    at one or two saddles of a ridge."""
    top = min(range(len(pts)), key=lambda i: pts[i][1])
    if family in ("mesa", "butte"):
        cuts = [top]  # pts[top] is a rim point; the pen lifts once on the rim
    elif family == "ridge":
        saddles = [i for i in range(2, len(pts) - 2) if pts[i][1] > pts[i - 1][1] and pts[i][1] > pts[i + 1][1]]
        cuts = sorted(rng.sample(saddles, min(len(saddles), 2))) if saddles else [top]
    elif family == "pass":
        cuts = [min(range(len(pts) // 3, 2 * len(pts) // 3), key=lambda i: -pts[i][1])]  # the col
    else:
        cuts = [top]
    pieces, last = [], 0
    for c in cuts:
        if 0 < c < len(pts) - 1:
            pieces.append(pts[last:c + 1])
            last = c
    pieces.append(pts[last:])
    return [p for p in pieces if len(p) >= 2]


def svg(family: str, pts: list[Point], extras: list[list[Point]], rng: random.Random,
          W: float, H: float, st: Pen) -> str:
    # The paper fill and the hatch clip follow the wobbled outline drawn as one line.
    centre = wobble(pts, random.Random(rng.random()), st.wobble)
    strokes: list[str] = []
    pieces = split_outline(centre, family, rng)
    for i, piece in enumerate(pieces):
        # Each meeting gets either a small overshoot (the pen runs on) or a small gap.
        run_on = rng.uniform(0.3, 1.0) if rng.random() < 0.5 else -rng.uniform(0.15, 0.4)
        start = 0.0 if i == 0 else rng.uniform(-0.1, 0.3)
        end = 0.0 if i == len(pieces) - 1 else run_on
        # Strokes start pressed (full width) at the summit and lift off at the feet.
        strokes.append(ribbon(extend(piece, start, end), st.outline_w, st.end_w, st.taper, rng,
                              start_w=0.75 if i > 0 else None))

    if st.double and rng.random() < st.double:
        # A second, thinner pass along part of the shaded (right) flank, a little inside it.
        top = min(range(len(centre)), key=lambda i: centre[i][1])
        flank = centre[top:]
        if len(flank) > 8:
            a = rng.randint(0, len(flank) // 3)
            b = rng.randint(a + len(flank) // 3, len(flank) - 1)
            part = flank[a:b]
            ns = normals(part)
            off = rng.uniform(0.6, 0.9)
            part = [(x - nx * off, y - ny * off) for (x, y), (nx, ny) in zip(part, ns, strict=False)]
            strokes.append(ribbon(wobble(part, rng, st.wobble * 0.6), st.outline_w * 0.4, 0.1, 0.35, rng))

    marks: list[str] = []
    if family in ("peak", "cone"):
        hatch_lines, spur = peak_hatches(pts, rng, H, st)
        curve = spur_curve(spur)
        spur_line = wobble(curve[:max(2, round(len(curve) * SPUR_SHARE))], rng, st.wobble * 0.7)
        marks.append(ribbon(spur_line, 1.0 * st.outline_w / 1.5, 0.35, 0.4, rng, start_w=0.9))
    else:
        hatch_lines = face_hatches(pts, rng, hang=family in ("ridge", "pass"), st=st)
    for line in extras:  # the caprock under a tableland's rim
        marks.append(ribbon(wobble(line, rng, st.wobble * 0.5), 0.8 * st.outline_w / 1.5, 0.4, 0.3, rng))

    hatch_lines = break_lines(hatch_lines, rng, st.broken)
    hatches = [ribbon(wobble(line, rng, st.wobble * 0.4, 6.0), st.hatch_w, 0.25, 0.45, rng, start_w=0.8)
               for line in hatch_lines]

    outline = " ".join(f"{x:.1f},{y:.1f}" for x, y in centre[::2] + centre[-1:])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<defs><clipPath id="m"><polygon points="{outline}"/></clipPath></defs>'
        f'<polygon points="{outline}" fill="{PAPER}" stroke="none"/>'
        f'<g fill="{INK}" stroke="none">'
        f'<path d="{"".join(strokes)}"/>'
        f'<path d="{"".join(marks)}"/>'
        f'<path clip-path="url(#m)" d="{"".join(hatches)}"/>'
        f"</g></svg>"
    )


def spur_curve(spur: list[Point]) -> list[Point]:
    """The spur: a quadratic curve from the summit through the control point."""
    (x0, y0), (cx, cy), (x1, y1) = spur
    ts = [k / 16 for k in range(17)]
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
             (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1) for t in ts]


def mirror(line: list[Point], W: float) -> list[Point]:
    return [(W - x, y) for x, y in reversed(line)]


def main() -> None:
    SVG_DIR.mkdir(exist_ok=True)
    for old in SVG_DIR.glob("*.svg"):
        old.unlink()
    for family, (shape, W, H) in FAMILIES.items():
        for i in range(1, SHAPES_PER_FAMILY + 1):
            # Peaks use their own seed names, so the peak set stays as published.
            seed = f"mountain-{i}" if family == "peak" else f"{family}-{i}"
            # The pen's seed keeps the name it had in the glyph trial, so the set is the one the owner chose.
            pen_seed = f"hand-B-{family}-{i}"
            pts, extras = shape(random.Random(seed), W, H)
            (SVG_DIR / f"{family}-{i:02d}.svg").write_text(
                svg(family, pts, extras, random.Random(pen_seed), W, H, PEN))
            (SVG_DIR / f"{family}-{i:02d}-flip.svg").write_text(
                svg(family, mirror(pts, W), [mirror(e, W) for e in extras], random.Random(pen_seed + "-flip"), W, H,
                    PEN))
    print(f"{len(FAMILIES) * SHAPES_PER_FAMILY * 2} glyphs in {len(FAMILIES)} families")
    build_sprite()


if __name__ == "__main__":
    main()
