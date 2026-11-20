"""Pen-and-ink drawing for the vignettes, on the 96 x 96 sprite grid (design section 10).

Every ink line is drawn with the mountain glyphs' pen (art/pen.py), so the glyphs and the vignettes read as one
hand: a tapered stroke whose width follows the pen's pressure and whose centre line wanders a little, outlines
drawn as two strokes that meet with a small gap or overshoot, and hatching that is loose, jittered and sometimes
broken. A drawing gives its lines as SVG path data; svgelements samples each into polylines, and the pen redraws
them as filled ribbons. Hatching is clipped to its region with shapely, so each hatch has its own ends.

Two inks only, as the sprite expects: ink lines, and paper fills that knock the map out behind the drawing. A
paper halo round every stroke lets the drawing read over the relief tint and the hachures. Light comes from the
north-west, as on the mountain glyphs, so shade falls on each shape's south-east side.
"""

import math
import random

import numpy as np
import svgelements as se
from shapely import affinity
from shapely.geometry import LineString, Polygon

from art import INK, PAPER
from art.pen import PEN, break_lines, extend, ribbon, wobble

Point = tuple[float, float]

# Stroke widths on the 96 grid, as drawn by a plain round pen: the pen draws them heavier by PEN_WEIGHT, the
# ratio of the pen's outline to the plain glyph outline it replaced (1.9 to 1.5).
OUTLINE, DETAIL, HATCH, PITCH = 2.0, 1.2, 0.8, 2.8
PEN_WEIGHT = PEN.outline_w / 1.5
# The vignette grid is drawn at about two-thirds the scale of a glyph canvas, so the pen's wander grows to match.
SCALE = 1.5
HALO = 3.2  # extra paper width under every stroke


def subpaths(d: str, step: float = 0.5) -> list[tuple[list[Point], bool]]:
    """Each subpath of SVG path data as points every `step` units, and whether it is closed."""
    out = []
    for sub in se.Path(d).as_subpaths():
        sub = se.Path(sub)
        length = sub.length(error=1e-3)
        if length < 1e-6:
            continue
        n = max(2, math.ceil(length / step) + 1)
        pts = [(float(x), float(y)) for x, y in sub.npoint(np.linspace(0, 1, n))]
        closed = any(isinstance(seg, se.Close) for seg in sub) or math.dist(pts[0], pts[-1]) < 0.05
        out.append((pts, closed))
    return out


def region(d: str):
    """The area a closed path encloses, with holes by the even-odd rule."""
    area = Polygon()
    for pts, _ in subpaths(d, 0.8):
        if len(pts) >= 3:
            area = area.symmetric_difference(Polygon(pts).buffer(0))
    return area


class Drawing:
    def __init__(self, name: str, width: int = 96, height: int = 96):
        """A drawing on a width x height grid in the 96 grid's units: the sprite's vignettes use 96 x 96, and a
        larger grid draws a larger picture with the same pen, so its lines are finer relative to its size."""
        self.name = name
        self.width, self.height = width, height
        self.items: list[tuple] = []  # (kind, d, opts)

    # Shapes ------------------------------------------------------------------------------------------
    def shape(self, d: str, w: float = OUTLINE, fill: bool = True):
        """A closed outline: paper inside, ink edge."""
        self.items.append(("shape", d, {"w": w, "fill": fill}))
        return self

    def line(self, d: str, w: float = DETAIL, halo: bool = True, color: str | None = None):
        """An open line; `color` PAPER draws a highlight across ink."""
        self.items.append(("line", d, {"w": w, "halo": halo, "color": color}))
        return self

    def hatch(self, area: str, angle: float = 45, pitch: float = PITCH, w: float = HATCH, cross: bool = False):
        """Parallel strokes within a region (angle in degrees from horizontal, 45 = rising to the right)."""
        self.items.append(("hatch", area, {"angle": angle, "pitch": pitch, "w": w}))
        if cross:
            self.items.append(("hatch", area, {"angle": angle - 90, "pitch": pitch * 1.15, "w": w}))
        return self

    def edge_shade(self, d: str, dx: float = -3.5, dy: float = -3.5, pitch: float = PITCH, cross: bool = False):
        """Hatch the south-east band of a shape: the shape minus itself moved towards the light."""
        self.items.append(("edge", d, {"dx": dx, "dy": dy, "pitch": pitch, "angle": 45}))
        if cross:
            self.items.append(("edge", d, {"dx": dx * .55, "dy": dy * .55, "pitch": pitch * 1.15, "angle": -45}))
        return self

    def dots(self, pts: list[Point], r: float = 0.7):
        self.items.append(("dots", pts, {"r": r}))
        return self

    def ground(self, x0: float, x1: float, y: float, ticks: int = 6, seed: int = 1):
        """A broken ground line with a few short hatch strokes under it."""
        segs, x, rnd = [], x0, _rng(seed)
        while x < x1:
            span = 6 + rnd() * 10
            segs.append(f"M{x:.1f},{y + (rnd() - .5) * .8:.1f} L{min(x + span, x1):.1f},{y + (rnd() - .5) * .8:.1f}")
            x += span + 2 + rnd() * 3
        self.line(" ".join(segs), w=1.1)
        t = []
        for i in range(ticks):
            tx = x0 + (x1 - x0) * (i + .5) / ticks + (rnd() - .5) * 4
            t.append(f"M{tx:.1f},{y + 2.2:.1f} l{3 + rnd() * 3:.1f},0")
        self.line(" ".join(t), w=0.8)
        return self

    # Output ------------------------------------------------------------------------------------------
    def svg(self, size: int | None = None) -> str:
        """The paper halo under everything first (the knock-out), then each item in order, so a later shape's
        paper fill hides what lies behind it. Seeded by the drawing's name, so a rebuild draws the same strokes."""
        rng = random.Random(f"vignette-{self.name}")
        under, body = [], []
        for kind, d, o in self.items:
            if kind == "shape":
                under.append(f'<path d="{d}" fill="{PAPER}" stroke="{PAPER}" stroke-width="{o["w"] + HALO}"/>')
                if o["fill"]:
                    body.append(f'<path d="{d}" fill="{PAPER}" stroke="none"/>')
                body.append(_ink(_outline(d, o["w"], rng)))
            elif kind == "line":
                if o["halo"]:
                    under.append(f'<path d="{d}" fill="none" stroke="{PAPER}" stroke-width="{o["w"] + HALO}"/>')
                body.append(_ink(_lines(d, o["w"], rng), o["color"] or INK))
            elif kind == "hatch":
                body.append(_ink(_hatches(region(d), o["angle"], o["pitch"], o["w"], rng)))
            elif kind == "edge":
                area = region(d)
                band = area.difference(affinity.translate(area, o["dx"], o["dy"]))
                body.append(_ink(_hatches(band, o["angle"], o["pitch"], HATCH, rng)))
            elif kind == "dots":
                body.append("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{o["r"]}" fill="{INK}"/>' for x, y in d))
        w = size or self.width
        h = round(w * self.height / self.width)
        box = f"0 0 {self.width} {self.height}"
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{box}">'
                f'<g stroke-linecap="round" stroke-linejoin="round">{"".join(under)}</g>'
                f'{"".join(body)}</svg>')


def _ink(path_data: str, colour: str = INK) -> str:
    return f'<path d="{path_data}" fill="{colour}" stroke="none"/>' if path_data else ""


def _outline(d: str, w: float, rng: random.Random) -> str:
    """A closed outline as two pen strokes that start at its top and meet near its foot, with a small gap or
    overshoot where they meet; an open subpath is one stroke."""
    width = w * PEN_WEIGHT
    out = []
    for pts, closed in subpaths(d):
        wander = random.Random(rng.random())
        if not closed or len(pts) < 8:
            out.append(ribbon(wobble(pts, wander, PEN.wobble * SCALE, 20.0 * SCALE), width, PEN.end_w, PEN.taper, rng))
            continue
        # Start the ring at its top before the pen wanders, so the only join is where the strokes meet.
        top = min(range(len(pts)), key=lambda i: pts[i][1])
        ring = wobble(pts[top:] + pts[1:top + 1], wander, PEN.wobble * SCALE, 20.0 * SCALE)
        cut = len(ring) // 2 + rng.randint(-len(ring) // 8, len(ring) // 8)
        run_on = rng.uniform(0.3, 1.0) if rng.random() < 0.5 else -rng.uniform(0.15, 0.4)
        out.append(ribbon(extend(ring[:cut + 1], 0.0, run_on), width, PEN.end_w, PEN.taper, rng))
        out.append(ribbon(extend(ring[cut:], rng.uniform(-0.1, 0.3), 0.0), width, PEN.end_w, PEN.taper, rng,
                          start_w=0.75))
    return "".join(out)


def _lines(d: str, w: float, rng: random.Random) -> str:
    width = w * PEN_WEIGHT
    return "".join(ribbon(wobble(pts, random.Random(rng.random()), PEN.wobble * SCALE * 0.7, 20.0 * SCALE), width,
                          PEN.end_w, PEN.taper, rng) for pts, _ in subpaths(d))


def _hatches(area, angle: float, pitch: float, w: float, rng: random.Random) -> str:
    """Hatches across a region at an angle, as the pen draws them: spacing and angle jittered, some rows left out,
    each hatch a little short of the region's edge at a random end, some broken in two."""
    if area.is_empty:
        return ""
    j = PEN.hatch_jitter
    cx, cy = area.centroid.x, area.centroid.y
    reach = math.dist(area.bounds[:2], area.bounds[2:]) / 2 + pitch
    lines: list[list[Point]] = []
    offset = -reach + rng.uniform(0, pitch)
    while offset < reach:
        a = math.radians(angle + rng.uniform(-6, 6) * j)
        dx, dy = math.cos(a), -math.sin(a)  # along the stroke (SVG y runs down)
        nx, ny = -dy, dx
        px, py = cx + nx * offset, cy + ny * offset
        cut = LineString([(px - dx * reach, py - dy * reach), (px + dx * reach, py + dy * reach)]).intersection(area)
        # A line that only grazes the region can come back as a collection with points in it.
        pieces = [g for g in getattr(cut, "geoms", [cut]) if isinstance(g, LineString)]
        for piece in pieces:
            if piece.length < 0.8 or rng.random() > PEN.hatch_share:
                continue
            (x0, y0), (x1, y1) = piece.coords[0], piece.coords[-1]
            trim = min(0.6, piece.length * 0.15)
            t0, t1 = rng.uniform(0, trim) / piece.length, 1 - rng.uniform(0, trim) / piece.length
            lines.append([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)])
        offset += pitch * (1 + rng.uniform(-0.3, 0.3) * j)
    width = w * PEN.hatch_w / 0.8
    return "".join(ribbon(wobble(line, rng, PEN.wobble * 0.4, 6.0), width, 0.25, 0.45, rng, start_w=0.8)
                   for line in break_lines(lines, rng, PEN.broken))


def _rng(seed: int):
    """A small repeatable sequence for the ground lines, independent of the pen's seed."""
    s = [seed * 9301 + 49297]

    def r() -> float:
        s[0] = (s[0] * 9301 + 49297) % 233280
        return s[0] / 233280
    return r

