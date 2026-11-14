"""The pen: strokes drawn as a hand with a dip pen would, shared by the mountain glyphs and the vignettes.

Each stroke is a filled outline whose width follows a pen pressure (thin at the ends, with a slow swell), its
centre line wanders a little (low-frequency noise, seeded per drawing), strokes meet with small gaps or overshoots,
and hatching jitters in spacing, angle and length, with some strokes broken. Only the two inks are used, so the
sprite build treats the result like any other drawing. The settings are variant B of the glyph trial
(review/experiments/glyphs/), which the owner chose on 14 November 2026.
"""

import math
import random
from dataclasses import dataclass

Point = tuple[float, float]


@dataclass(frozen=True)
class Pen:
    wobble: float          # largest sideways drift of a stroke's centre line, in drawing units
    outline_w: float       # outline width at full pressure
    end_w: float           # share of full width left at a stroke's ends
    taper: float           # share of a stroke's length over which it tapers in at each end
    double: float          # chance of a second, thin pass along part of a shaded edge
    hatch_w: float         # hatch width at full pressure
    hatch_gap: float       # mean spacing between hatches
    hatch_jitter: float    # spacing, length and angle jitter (0 to 1)
    broken: float          # chance that a hatch is drawn as two pieces
    hatch_share: float     # share of the hatch rows kept (the rest are left out)
    hatch_reach: float     # how far down a flank hatching runs (1 = to the foot)


# Strong pressure taper, outlines in strokes that meet at the summit, loose and sometimes broken hatching, and a
# second pass on part of the shaded side.
PEN = Pen(wobble=0.6, outline_w=1.9, end_w=0.2, taper=0.3, double=0.6, hatch_w=0.95, hatch_gap=2.6,
          hatch_jitter=0.8, broken=0.18, hatch_share=0.9, hatch_reach=1.0)


def resample(line: list[Point], step: float = 0.5) -> list[Point]:
    """The polyline with points every `step` units, keeping its corners."""
    out = [line[0]]
    for (x1, y1), (x2, y2) in zip(line, line[1:], strict=False):
        n = max(1, math.ceil(math.hypot(x2 - x1, y2 - y1) / step))
        out += [(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n) for k in range(1, n + 1)]
    return out


def lengths(line: list[Point]) -> list[float]:
    s = [0.0]
    for (x1, y1), (x2, y2) in zip(line, line[1:], strict=False):
        s.append(s[-1] + math.hypot(x2 - x1, y2 - y1))
    return s


def normals(line: list[Point], reach: int = 2) -> list[Point]:
    """Unit normals from a chord `reach` points either side, so they turn smoothly at corners."""
    out = []
    for i in range(len(line)):
        a, b = line[max(0, i - reach)], line[min(len(line) - 1, i + reach)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        out.append((-dy / d, dx / d))
    return out


def noise(rng: random.Random, amp: float, scale: float):
    """Smooth 1D noise: a sum of three sines with random phases, wavelengths around `scale` units."""
    waves = [(rng.uniform(0.7, 1.4) * scale * f, rng.uniform(0, 2 * math.pi), w)
             for f, w in ((1.0, 1.0), (0.55, 0.45), (0.35, 0.15))]
    norm = sum(w for _, _, w in waves)
    return lambda s: amp * sum(w * math.sin(2 * math.pi * s / lam + ph) for lam, ph, w in waves) / norm


def wobble(line: list[Point], rng: random.Random, amp: float, scale: float = 20.0) -> list[Point]:
    """The line with its points pushed sideways by smooth noise; the two ends move least."""
    if amp <= 0:
        return resample(line)
    pts = resample(line)
    s = lengths(pts)
    total = s[-1] or 1.0
    f = noise(rng, amp, scale)
    out = []
    for (x, y), (nx, ny), si in zip(pts, normals(pts), s, strict=False):
        hold = min(1.0, 0.4 + 0.6 * min(si, total - si) / min(4.0, total / 2))  # ends drift less
        d = f(si) * hold
        out.append((x + nx * d, y + ny * d))
    return out


def extend(line: list[Point], start: float, end: float) -> list[Point]:
    """Lengthen (positive) or shorten (negative) the line at each end, along its end direction."""
    def push(p: Point, q: Point, by: float) -> Point:
        dx, dy = p[0] - q[0], p[1] - q[1]
        d = math.hypot(dx, dy) or 1.0
        return (p[0] + dx / d * by, p[1] + dy / d * by)

    pts = resample(line, 0.25)
    if start < 0:
        pts = pts[min(len(pts) - 2, round(-start / 0.25)):]
    elif start > 0:
        pts = [push(pts[0], pts[1], start)] + pts
    if end < 0:
        pts = pts[:max(2, len(pts) - round(-end / 0.25))]
    elif end > 0:
        pts = pts + [push(pts[-1], pts[-2], end)]
    return pts


def ribbon(line: list[Point], width: float, end_w: float, taper: float, rng: random.Random,
           start_w: float | None = None) -> str:
    """A pen stroke along `line` as a filled outline (SVG path data): full width in the middle,
    narrowing to `end_w` of it at the ends over `taper` of the length, with a slow pressure swell."""
    pts = resample(line, 0.7)
    if len(pts) < 2:
        return ""
    s = lengths(pts)
    total = s[-1] or 1.0
    swell = noise(rng, 0.12, 16.0)
    t_len = max(0.6, taper * total)
    w0 = end_w if start_w is None else start_w

    def w(si: float) -> float:
        a = min(1.0, si / t_len)
        b = min(1.0, (total - si) / t_len)
        ease = lambda u: u * u * (3 - 2 * u)  # noqa: E731
        p = min(w0 + (1 - w0) * ease(a), end_w + (1 - end_w) * ease(b))
        return width * max(0.15, p * (1 + swell(si))) / 2

    ns = normals(pts)
    left = [(x + nx * w(si), y + ny * w(si)) for (x, y), (nx, ny), si in zip(pts, ns, s, strict=False)]
    right = [(x - nx * w(si), y - ny * w(si)) for (x, y), (nx, ny), si in zip(pts, ns, s, strict=False)]
    ring = left + right[::-1]
    return "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in ring) + "Z"


def break_lines(lines: list[list[Point]], rng: random.Random, chance: float) -> list[list[Point]]:
    """Split some lines in two with a small gap, as a pen skipping."""
    out = []
    for a, b in lines:
        if rng.random() < chance:
            t, gap = rng.uniform(0.35, 0.65), rng.uniform(0.6, 1.2)
            d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            if d < 2 * gap:  # too short to skip: the two pieces would run past the ends
                out.append([a, b])
                continue
            g = gap / d / 2
            out += [[a, (a[0] + (b[0] - a[0]) * (t - g), a[1] + (b[1] - a[1]) * (t - g))],
                    [(a[0] + (b[0] - a[0]) * (t + g), a[1] + (b[1] - a[1]) * (t + g)), b]]
        else:
            out.append([a, b])
    return out
