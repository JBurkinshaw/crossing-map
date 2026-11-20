"""Large vignettes for the low-zoom map: six uncaptioned drawings of the novel's broad themes that fill the empty
quarters of the map when it first loads and fade out as the reader zooms in.

They are drawn on a 288 x 216 grid (in the 96 grid's units) with the same pen as the 96 x 96 sprite vignettes, so
the lines read finer and carry more detail, after the engraved cartouche art on old survey maps. They are not in
the sprite: art/vignettes/make_vignettes.py loads only subjects_*.py modules, and this module writes its own SVGs
to art/vignettes/large/ and PNGs to site/public/art/. Run it with

    uv run --project pipeline --extra art python -m art.vignettes.large [id ...]

The horses and riders are traced afresh, at the larger size, from the same Muybridge plate as the sprite's riders
(Animal Locomotion plate 580, "Annie G." walking, 1887, public domain): the horse alone, its darkest tones, and the
horse with its rider, kept below as point rings. The she-wolf's outline was set by hand over the US Fish and Wildlife
Service photograph the sprite's wolf comes from (Flickr 14883247361, public domain), with her head carried level
and her legs a little longer. The ruined church is drawn after the Quarai mission photograph (suemruth, CC BY 2.0,
drawn after, not traced). Everything else is drawn by hand. The paper knock-out is kept light, with open skies and
edges that trail off into hatching, so each reads as drawn on the map. Light from the north-west: shade on each
shape's south-east side.
"""

import math
import random
import subprocess
import sys
from itertools import pairwise
from pathlib import Path

import svgelements as se
from shapely.geometry import LineString
from shapely.ops import unary_union

from art import PAPER
from art.vignettes.ink import Drawing, region
from art.vignettes.shapes import grass, poly, warp
from art.vignettes.subjects_parts_1_2 import lechuguilla
from art.vignettes.subjects_parts_3_4 import blob
from art.vignettes.subjects_round3 import chevrons

W, H = 288, 216
ROOT = Path(__file__).resolve().parents[2]
SVG_DIR = Path(__file__).parent / "large"
PNG_DIR = ROOT / "site" / "public" / "art"
PNG_WIDTH, FALLBACK_WIDTH = 1152, 960
MAX_BYTES = 350 * 1024

Pt = tuple[float, float]


# Helpers ----------------------------------------------------------------------------------------------
def _pl(pts: list[Pt]) -> str:
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def _rings(data: str | tuple[str, ...]) -> list[list[Pt]]:
    """Traced point rings ("x,y x,y ...", one string per ring)."""
    return [[tuple(map(float, p.split(","))) for p in r.split()] for r in ((data,) if isinstance(data, str) else data)]


def _path(geom) -> str:
    """A shapely polygon or multipolygon as path data."""
    return " ".join(poly(*p.exterior.coords[:-1]) for p in getattr(geom, "geoms", [geom]))


def smooth(pts: list[Pt], closed: bool = True) -> str:
    """A curve through the points (Catmull-Rom as cubic Béziers), so a traced polygon is drawn round."""
    n = len(pts)
    out = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(n if closed else n - 1):
        p0 = pts[(i - 1) % n] if closed or i else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else pts[-1]
        out.append(f"C{p1[0] + (p2[0] - p0[0]) / 6:.1f},{p1[1] + (p2[1] - p0[1]) / 6:.1f} "
                   f"{p2[0] - (p3[0] - p1[0]) / 6:.1f},{p2[1] - (p3[1] - p1[1]) / 6:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(out) + (" Z" if closed else "")


def _mover(ox: float, oy: float, k: float, flip: bool, head: float = 0.0):
    """The transform from an animal's own units to the drawing: scale by k, mirror if asked, move to (ox, oy).
    `head` turns the head and neck (everything west of x = -26) up by that many degrees, or down if negative."""
    s = -1 if flip else 1

    def f(x: float, y: float) -> Pt:
        if head and x < -26:
            a = math.radians(head) * min(1.0, (-26 - x) / 8)
            dx, dy = x + 26, y + 46
            x, y = -26 + dx * math.cos(a) - dy * math.sin(a), -46 + dx * math.sin(a) + dy * math.cos(a)
        return ox + s * x * k, oy + y * k

    def t(path: str) -> str:
        return warp(path, f)
    return f, t


def fur(pts: list[Pt], zones: list[tuple[float, float, float, float]], seed: int, step: float = 1.3,
        depth: float = 0.8) -> list[Pt]:
    """A traced ring roughened into tufts of fur wherever it passes through one of the boxes (x0, y0, x1, y1):
    points every `step` units, pushed alternately out and in along the outline's normal."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))
    out_sign = 1 if area > 0 else -1
    rnd = random.Random(seed)
    res: list[Pt] = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1], strict=True):
        ln = math.dist((ax, ay), (bx, by))
        n = max(1, round(ln / step))
        nx, ny = (by - ay) / (ln or 1) * out_sign, -(bx - ax) / (ln or 1) * out_sign
        for j in range(n):
            x, y = ax + (bx - ax) * j / n, ay + (by - ay) * j / n
            if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in zones):
                o = depth * rnd.uniform(.5, 1.1) * (1 if len(res) % 2 else -.4)
                x, y = x + nx * o, y + ny * o
            res.append((x, y))
    return res


def conifer(d: Drawing, x: float, base: float, h: float, seed: int, w: float = 1.0):
    """A pine in the engraved manner: a straight bole under tiers of drooping, ragged boughs that narrow to a
    point, each tier shaded on its south-east side."""
    rnd = random.Random(seed)
    d.line(f"M{x:.1f},{base:.1f} L{x:.1f},{base - h * .9:.1f}", w=1.3 * w)
    tiers = 6 if h > 50 else 4
    for i in range(tiers):
        f = i / tiers
        ty = base - h * (.22 + .78 * f)
        th = h * (.3 - .1 * f)
        half = h * (.26 - .2 * f) * rnd.uniform(.85, 1.15)
        top = (x + rnd.uniform(-.8, .8), ty - th)
        teeth = 5 if half > 10 else 3
        pts = [top]
        for j in range(teeth * 2 + 1):
            u = -1 + 2 * j / (teeth * 2)
            dip = th * (.12 if j % 2 else -.04) * rnd.uniform(.6, 1.2)
            pts.append((x + u * half, ty + dip - th * .15 * (1 - abs(u))))
        tier = ("M{:.1f},{:.1f} C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} ".format(
            *top, top[0] - half * .3, top[1] + th * .4, x - half * .9, ty - th * .3, *pts[1])
            + " ".join(f"L{px:.1f},{py:.1f}" for px, py in pts[2:])
            + " C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} Z".format(
            x + half * .9, ty - th * .3, top[0] + half * .3, top[1] + th * .4, *top))
        d.shape(tier, w=w)
        d.edge_shade(tier, dx=-half * .3, dy=-th * .2, pitch=2.1)
    d.line(f"M{x:.1f},{base - h * .98:.1f} L{x:.1f},{base - h * 1.06:.1f}", w=0.8 * w)


def treeline(d: Drawing, x0: float, x1: float, y: float, seed: int, h: float = 9.0, gap: float = 7.0, rows: int = 2):
    """Small pines along the foot of a range, drawn as the survey maps drew forest: a stem and two strokes for
    the boughs, set in staggered rows and thinning out towards the ends."""
    rnd = random.Random(seed)
    marks = []
    for r in range(rows):
        x = x0 + rnd.uniform(0, gap) + r * gap / 2
        while x < x1:
            if rnd.random() > _edge(x, x0, x1) ** 2:
                yy, hh = y + r * h * .55 + rnd.uniform(-1, 1), h * rnd.uniform(.8, 1.15) * (1 + r * .12)
                marks.append(f"M{x:.1f},{yy:.1f} l0,{-hh:.1f} M{x - hh * .3:.1f},{yy - hh * .25:.1f} l{hh * .3:.1f},"
                             f"{-hh * .55:.1f} l{hh * .3:.1f},{hh * .55:.1f}")
            x += gap * rnd.uniform(.8, 1.25)
    d.line(" ".join(marks), w=0.6, halo=False)


def broadleaf(d: Drawing, x: float, base: float, h: float, wide: float, seed: int, dark: bool = False,
              spots: list[tuple[float, float, float]] | None = None):
    """A cottonwood or juniper: a trunk forking into limbs that each carry a scalloped clump of leaves, the clumps
    shaded on their south-east sides with leaf marks on the lit ones. `dark` hatches the clumps all over, for the
    juniper's dark foliage. `spots` places the clumps (across as a fraction of the width, up and size as fractions
    of the height)."""
    rnd = random.Random(seed)
    fork = base - h * .42
    spots = spots or [(-.36, .52, .2), (-.2, .78, .2), (.06, .92, .21), (.3, .72, .2), (.4, .48, .17), (.02, .6, .24),
             (-.42, .3, .14), (.24, .38, .16)]
    clumps = []
    for u, v, r in spots:
        cx = x + wide * (u + rnd.uniform(-.04, .04))
        cy = base - h * (v + rnd.uniform(-.03, .03))
        clumps.append((cx, cy, wide * r * rnd.uniform(.9, 1.1), h * r * .62 * rnd.uniform(.9, 1.1)))
    tw = max(1.6, wide * .065)
    d.shape(f"M{x - tw:.1f},{base:.1f} C{x - tw * .7:.1f},{base - h * .2:.1f} {x - tw * .6:.1f},{fork + 4:.1f} "
            f"{x - tw * .4:.1f},{fork:.1f} L{x + tw * .5:.1f},{fork:.1f} C{x + tw * .7:.1f},{fork + 4:.1f} "
            f"{x + tw * .8:.1f},{base - h * .2:.1f} {x + tw * 1.2:.1f},{base:.1f} Z", w=1.3)
    d.hatch(f"M{x + tw * .2:.1f},{base:.1f} L{x + tw * .2:.1f},{fork:.1f} L{x + tw:.1f},{fork:.1f} "
            f"L{x + tw * 1.2:.1f},{base:.1f} Z", angle=80, pitch=1.1, w=0.5)
    limbs = []
    for cx, cy, _, ry in clumps:
        mx = (x + cx) / 2 + rnd.uniform(-3, 3)
        limbs.append(f"M{x:.1f},{fork + 1:.1f} Q{mx:.1f},{(fork + cy) / 2 + 4:.1f} {cx:.1f},{cy + ry * .3:.1f}")
    d.line(" ".join(limbs), w=1.1)
    # One outline round the whole crown, with the lower edge of each clump drawn inside it.
    paths = [blob(cx, cy, rx, ry, 13, seed=seed * 20 + i, depth=.2) for i, (cx, cy, rx, ry) in enumerate(clumps)]
    crown = unary_union([region(p) for p in paths]).buffer(0)
    for part in getattr(crown, "geoms", [crown]):
        d.shape(poly(*part.exterior.coords[:-1]), w=1.1)
    if dark:
        d.hatch(_path(crown), angle=55, pitch=1.3, w=0.5)
    arcs, marks = [], []
    for (cx, cy, rx, ry), p in sorted(zip(clumps, paths, strict=True), key=lambda c: c[0][1]):
        d.edge_shade(p, dx=-rx * .4, dy=-ry * .45, pitch=1.2, cross=True)
        a0 = rnd.uniform(-.3, .2)
        arc = [(cx + rx * .95 * math.cos(a), cy + ry * .95 * math.sin(a)) for a in
               (a0 + j * .35 for j in range(9))]
        arcs.append(_pl(arc))
        for _ in range(3):
            mx, my = cx - rx * rnd.uniform(0, .55), cy - ry * rnd.uniform(-.1, .5)
            marks.append(f"M{mx:.1f},{my:.1f} l1.4,0.9 M{mx + 2.4:.1f},{my - .6:.1f} l1.2,1")
    d.line(" ".join(arcs), w=0.6, halo=False)
    if not dark:
        d.line(" ".join(marks), w=0.5, halo=False)


# The horse of Muybridge's plate 580 (facing west, hooves on y = 0, about 85 units long), its tail drawn by hand.
TAIL = ("M17.6,-47 C22,-46.6 25.4,-41 25.6,-34 C25.8,-29 25,-24.6 23.6,-20.4 C22.6,-21.6 21.6,-23.4 21,-24.6 "
        "C20.6,-22.6 20,-21.4 19.4,-20.8 C18.8,-26 18.4,-32 17.8,-36 C17.4,-40 17,-43 17.6,-47 Z")
MANE = [(-48.6, -58.4), (-43, -57.6), (-38.3, -56.3), (-34, -54.4), (-29.9, -52.5), (-24.5, -51.6)]


def mustang(d: Drawing, ox: float, oy: float, k: float, flip: bool = False, coat: str = "bay", body: str = "",
            tones: str | tuple[str, ...] = (), tail: bool = True, head: float = 0.0):
    """A horse traced from the plate, hooves centred about (ox, oy), scaled by k (1 is about 85 units long),
    facing west unless flipped. `coat` is "bay" (hatched dark all over), "dun" (shaded only) or "paint" (dark
    patches); `head` raises or lowers the head (degrees). Returns the transform for a path in the horse's units."""
    f, t = _mover(ox, oy, k, flip, head)
    w = 1.3 if k < 0.8 else 1.6
    if tail:
        tl = t(TAIL)
        d.shape(tl, w=w * .8)
        d.line(t("M18.6,-44 C20.6,-38 21.4,-31 21.6,-25 M20.4,-45 C23,-39 24,-32 23.8,-24 M19,-38 C19.6,-32 "
                 "20,-27 20,-22.6"), w=0.5, halo=False)
    outline = smooth([f(x, y) for x, y in _rings(body or HORSE)[0]])
    d.shape(outline, w=w)
    a = 135 if flip else 45
    if coat == "bay":
        d.hatch(outline, angle=a, pitch=1.5, w=0.55)
    elif coat == "paint":
        for p in ("M-12,-46 C-6,-48 2,-48 6,-44 C8,-38 2,-33 -4,-34 C-10,-34 -14,-40 -12,-46 Z",
                  "M8,-46 C12,-48 16,-46 17.6,-42 L18,-30 C14,-28 10,-32 8,-38 Z",
                  "M-50,-56 C-46,-58 -42,-56 -42,-52 C-44,-50 -48,-50 -50,-56 Z"):
            d.hatch(t(p), angle=a, pitch=1.2, w=0.55, cross=True)
    for r in _rings(tones or HORSE_TONES):
        d.hatch(smooth([f(x, y) for x, y in r]), angle=a - 90, pitch=1.3, w=0.5)
    d.edge_shade(outline, dx=-2.6, dy=-2.6, pitch=1.4)
    # Head: eye, nostril, mouth, the round of the cheek, the ear; the mane along the crest.
    d.dots([f(-50.2, -51.6)], r=0.55 * min(1.6, k + .4))
    d.line(t("M-54.2,-41.6 c0.6,-0.6 1.2,-0.6 1.6,0 M-54.6,-39.4 L-52,-39.2 M-50.4,-49.4 C-46.4,-48.8 -45.2,-45.6 "
             "-47.4,-43 M-52.6,-56 L-51.4,-53.6"), w=0.6, halo=False)
    mane = []
    for (x0, y0), (x1, y1) in pairwise(MANE):
        for j in range(3):
            x, y = x0 + (x1 - x0) * j / 3, y0 + (y1 - y0) * j / 3
            mane.append(f"M{x:.1f},{y + .4:.1f} l{1.6 + j * .4:.1f},{3.2 + (j % 2) * 1.2:.1f}")
    d.line(t(" ".join(mane)), w=0.55, halo=False)
    # The legs: the far foreleg behind the lifted near one, the stifle, hocks and hoof bands.
    d.line(t("M-27.6,-26 C-28,-21 -28.4,-17 -28.6,-13 M-26.4,-9 L-27.4,-3 M2.6,-34 C4.6,-30 6,-27 6.6,-23 "
             "M14.6,-40 C13,-35 13.4,-30 15.6,-25.6 M-29.6,-2.6 l3,0.4 M-2.6,-1.6 l2.6,0.2 M27,-2.6 l2.4,0.2"),
           w=0.6, halo=False)
    return t


# The rider, traced from the same plate with the horse, wearing a broad hat for the jockey's cap.
def vaquero(d: Drawing, ox: float, oy: float, k: float, flip: bool = False, coat: str = "bay", arm: str = ""):
    """A horse and rider facing west unless flipped; `arm` is extra path data in the horse's units (a raised arm,
    a lead rope). Returns the transform."""
    t = mustang(d, ox, oy, k, flip, coat=coat, body=RIDER, tones=RIDER_TONES)
    leg = ("M-6,-52 C-12,-51.8 -18,-50.8 -22.4,-48.6 C-24.6,-45 -25.6,-41 -26.6,-37.4 L-30.6,-35 L-30.2,-33.4 "
           "L-24.6,-34 C-23.4,-37.6 -22,-41.4 -20.6,-43.8 C-16,-45.6 -12,-46.6 -8,-47.4 Z")
    d.shape(t(leg), w=1.1)
    d.hatch(t("M-26.6,-37.4 L-30.6,-35 L-30.2,-33.4 L-24.6,-34 Z"), angle=0, pitch=0.8, w=0.5)
    d.line(t("M-17,-55 C-28,-50 -40,-46 -49.6,-43.4 M-24,-34 l0,2.4 l-4,0"), w=0.6, halo=False)
    hat = t("M-20,-71 C-17,-72.6 -14,-72.4 -10,-72.4 C-6,-72.4 -3,-72.6 0,-71 C-3,-70.6 -6,-70 -10,-70 "
            "C-14,-70 -17,-70.6 -20,-71 Z")
    crown = t("M-13.8,-71.8 C-14,-74.6 -13.4,-76.8 -12,-77 C-11,-76.2 -9,-76.2 -8,-77 C-6.6,-76.8 -6,-74.6 "
              "-6.2,-71.8 Z")
    d.shape(crown, w=1.1)
    d.shape(hat, w=1.1)
    d.hatch(t("M-13.8,-71.8 L-13.8,-73.4 L-6.2,-73.4 L-6.2,-71.8 Z"), angle=0, pitch=0.8, w=0.5)
    if arm:
        d.line(t(arm), w=1.3)
    return t


# The she-wolf, drawn by hand over the US Fish and Wildlife Service photograph (facing east, feet on y = 0, about
# 70 units long): the dark saddle and shoulder, the black tail tip, long hair at the tail, ruff and belly.
def lobo(d: Drawing, ox: float, oy: float, k: float, flip: bool = False, head: float = 0.0):
    """The she-wolf, feet centred about (ox, oy), scaled by k, facing east unless flipped; `head` lifts her head
    and neck by that many degrees (or lowers them, if negative)."""
    g, _ = _mover(ox, oy, k, flip)

    def f(x: float, y: float) -> Pt:
        if head and x > 14 and y < -24:
            a = -math.radians(head) * min(1.0, (x - 14) / 8, (-24 - y) / 6)
            dx, dy = x - 14, y + 34
            x, y = 14 + dx * math.cos(a) - dy * math.sin(a), -34 + dx * math.sin(a) + dy * math.cos(a)
        # Her legs drawn a fifth longer than the photograph's, for a wolf's rangy build.
        return g(x, (-22 + (y + 22) * 1.2 if y > -22 else y) - 4.4)

    def t(path: str) -> str:
        return warp(path, f)
    # Tufts on the tail, the ruff at her throat and chest, her belly and the backs of her thighs.
    ring = fur(_rings(WOLF)[0], [(-36, -30, -22, -8), (16, -30, 26, -18), (-16, -22, 16, -16),
                                 (-24, -24, -15, -10), (17, -41, 22, -36)], seed=5, step=2.6, depth=0.5)
    body = smooth([f(x, y) for x, y in ring])
    d.shape(body, w=1.6)
    d.edge_shade(body, dx=-3.2, dy=-3.2, pitch=1.4)
    a = 135 if flip else 45
    saddle = ("M-23.4,-32.6 C-22,-35 -20,-36.4 -16,-37.4 C-11,-38.4 -4,-38.6 1.4,-37.8 C2,-36 1,-34.4 -1,-34 "
              "C-6,-33.6 -12,-33.4 -16,-32.2 C-19,-31.2 -21.6,-30 -22.6,-28.6 Z")
    d.hatch(t(saddle), angle=a, pitch=1.1, w=0.55, cross=True)
    d.hatch(t("M3,-37.6 C6,-38 8.4,-37.4 9,-35 C9.4,-32 8,-29 7,-27.6 C5.6,-30 4,-33 3,-37.6 Z"), angle=a - 90,
            pitch=1.1, w=0.5)
    d.hatch(t("M-35.3,-10.3 C-34.6,-12 -33.6,-13.6 -32.6,-14.4 L-30.8,-12.6 C-32.2,-11.6 -33.8,-10.8 -35.3,-10.3 Z"),
            angle=a, pitch=0.8, w=0.6, cross=True)
    # Face: eye, nose, mouth, the bridge of the muzzle, the ears and the ruff.
    d.shape(t("M26.6,-38.6 C27.4,-39.4 28.4,-39.4 29,-38.8 C28.2,-38.2 27.4,-38 26.6,-38.6 Z"), w=0.7)
    d.dots([f(27.9, -38.7)], r=0.45 * k)
    nose = t("M35.6,-34.2 C35.8,-33.2 35.4,-32.8 34.4,-32.8 C34,-33.6 34.4,-34.4 35.6,-34.2 Z")
    d.shape(nose, w=0.8)
    d.hatch(nose, angle=45, pitch=0.5, w=0.5, cross=True)
    d.line(t("M34.4,-32.6 C32.6,-32.4 30.8,-32.2 29.4,-32.4 M29,-38.6 C30.8,-37.4 32.8,-35.8 34.4,-34.6 "
             "M20.6,-42.2 L21,-44.2 M23.6,-42.6 L24.4,-44.8 "
             "M23.4,-40 C22.2,-36 22.8,-32.6 24.6,-30.6 C25.6,-29.8 26.6,-29.6 27.6,-29.8 "
             "M8,-34.4 C10.6,-30 11.6,-25 11.8,-19.6 M-21,-31 C-18.6,-28 -16.6,-24 -15.4,-19.8 "
             "M-3.6,-18.2 C-3.4,-14 -3,-10 -2,-7"), w=0.6, halo=False)
    d.hatch(t("M20.2,-42 L20.6,-44.8 L22,-42.4 Z M23.4,-42.8 L24.6,-45.4 L25.4,-42.4 Z"), angle=80, pitch=0.8, w=0.45)
    d.hatch(t("M23.6,-42.6 C25.6,-42 27.2,-40.6 28.8,-38.8 C26.8,-37.4 25,-37.6 23.6,-38.6 Z"), angle=a, pitch=1.1,
            w=0.45)
    d.hatch(t("M29.4,-38.2 L34.4,-34.4 L34.4,-33.6 C32.6,-34.4 30.8,-35.8 29.4,-37 Z"), angle=a - 90, pitch=0.9,
            w=0.45)
    # Her grizzled coat: a light broken tone over the back and neck, darker under the crest.
    d.hatch(t("M-24,-30 C-20,-35 -12,-37.6 0,-37.6 C8,-37.6 14,-37 19,-38.6 C20,-34 18,-30 14,-27 C8,-29 0,-30 "
              "-8,-29.6 C-14,-29 -20,-27 -24,-24 Z"), angle=a - 90, pitch=1.9, w=0.45)
    d.hatch(t("M14,-37.6 C17,-38.4 19,-39.6 20.4,-40.6 C20,-36 20.6,-31 22.6,-27.4 C20,-25 17,-23 14,-22 "
              "C15,-27 15.6,-32 14,-37.6 Z"), angle=a, pitch=1.5, w=0.45)
    strokes = []
    rnd = random.Random(7)
    # Long hair breaking the outline: down the tail, under the belly, at the ruff and the backs of the thighs.
    hair = (((-34.6, -12), (-25, -27), 9, (-1.2, 1.4)), ((-31, -11), (-24, -19), 5, (-1, 1.6)),
            ((-12, -18.6), (10, -16.4), 8, (-.6, 1.6)), ((22, -26), (19, -17), 5, (-.4, 1.8)),
            ((-22, -21), (-17, -13), 4, (-1.4, .8)))
    for (x0, y0), (x1, y1), n, (hx, hy) in hair:
        for j in range(n):
            u = (j + rnd.uniform(.2, .8)) / n
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            strokes.append(f"M{x - hx * .6:.1f},{y - hy * .6:.1f} l{hx * 1.4:.1f},{hy * 1.4:.1f}")
    for x, y in ((-18, -35), (-12, -36.6), (-6, -36.8), (0, -36.4), (6, -36), (12, -35.4), (16, -34.4),
                 (-26, -24), (-28, -20), (-30, -16), (14, -26), (16, -22), (-8, -30), (-2, -29), (4, -30)):
        strokes.append(f"M{x + rnd.uniform(-1, 1):.1f},{y:.1f} "
                       f"l{1.6 + rnd.uniform(0, .8):.1f},{.9 + rnd.uniform(0, .6):.1f}")
    d.line(t(" ".join(strokes)), w=0.5, halo=False)
    return t


def tilt(d: Drawing, since: int, cx: float, cy: float, deg: float):
    """Turn everything drawn since item `since` by deg degrees about (cx, cy) (negative is anticlockwise)."""
    m = se.Matrix(f"rotate({deg} {cx} {cy})")
    for i in range(since, len(d.items)):
        kind, path, opts = d.items[i]
        if kind == "dots":
            moved = [tuple(m.point_in_matrix_space((x, y))) for x, y in path]
        else:
            moved = (se.Path(path) * m).d()
        d.items[i] = (kind, moved, opts)


def _edge(x: float, x0: float, x1: float) -> float:
    """0 at the middle of [x0, x1], 1 at its ends: how far into the feathered edge x lies."""
    return min(1.0, abs(x - (x0 + x1) / 2) / ((x1 - x0) / 2))


def mountains(d: Drawing, x0: float, x1: float, base: float, peaks: list[Pt], seed: int, w: float = 1.1,
              pitch: float = 2.0, angle: float = 62, rough: float = 0.9, spurs: bool = True):
    """A range of peaks (x, height above base) in the engraved manner: a ridge line that thins and breaks up
    towards both ends, the south-east flank of each peak hatched (closer under the crest), a few fall lines on
    the lit side, and no foot line, so the range fades into the ground."""
    rnd = random.Random(seed)
    keys: list[Pt] = [(x0, base - peaks[0][1] * 0.15)]
    for i, (px, h) in enumerate(peaks):
        keys.append((px, base - h))
        if i + 1 < len(peaks):
            nx, nh = peaks[i + 1]
            keys.append(((px + nx) / 2 + rnd.uniform(-.12, .12) * (nx - px), base - min(h, nh) * rnd.uniform(.35, .6)))
    keys.append((x1, base - peaks[-1][1] * 0.15))
    # Roughen each run between key points, keeping the keys themselves.
    runs: list[list[Pt]] = []
    for (ax, ay), (bx, by) in pairwise(keys):
        n = max(2, int(math.dist((ax, ay), (bx, by)) / 4))
        run = [(ax, ay)]
        for j in range(1, n):
            t = j / n
            run.append((ax + (bx - ax) * t + rnd.uniform(-.4, .4), ay + (by - ay) * t + rnd.uniform(-rough, rough)))
        run.append((bx, by))
        runs.append(run)
    # The ridge: heavier in the middle, broken into dashes over the outer runs.
    for k, run in enumerate(runs):
        e = _edge((run[0][0] + run[-1][0]) / 2, x0, x1)
        if k in (0, len(runs) - 1):
            dashes, i = [], 0
            while i < len(run) - 1:
                j = min(len(run) - 1, i + rnd.randint(1, 3))
                dashes.append(_pl(run[i:j + 1]))
                i = j + rnd.randint(1, 2)
            d.line(" ".join(dashes), w=w * 0.55)
        else:
            d.line(_pl(run), w=w * (1 - 0.45 * e * e))
    # Shade the south-east flank of each peak, fading out at the foot and towards the ends of the range.
    for i, (px, h) in enumerate(peaks):
        flank = runs[2 * i + 1]
        sx, sy = flank[-1]
        e = _edge(px, x0, x1)
        p = pitch * (1 + 1.6 * e * e)
        foot = [(sx + rnd.uniform(-2, 2), base + rnd.uniform(-h * .15, h * .05)),
                ((sx + px) / 2 + rnd.uniform(-3, 3), base + rnd.uniform(-h * .2, 0)),
                (px + (sx - px) * .08, base - h * rnd.uniform(.1, .3))]
        d.hatch(poly(*flank, *foot), angle=angle, pitch=p, w=0.55)
        crest = [(x, y + h * .28) for x, y in reversed(flank)]
        d.hatch(poly(*flank, *crest), angle=angle - 75, pitch=p * 1.25, w=0.5)
    # Fall lines on the lit (north-west) slopes.
    if spurs:
        falls = []
        for i, (px, _) in enumerate(peaks):
            up = runs[2 * i]
            e = _edge(px, x0, x1)
            for x, y in up[1:-1:2]:
                if rnd.random() < 0.55 - 0.3 * e:
                    ln = rnd.uniform(.15, .4) * (base - y)
                    falls.append(f"M{x:.1f},{y + 1.2:.1f} l{-ln * .25:.1f},{ln:.1f}")
        if falls:
            d.line(" ".join(falls), w=0.5, halo=False)


def plain(d: Drawing, x0: float, x1: float, y: float, seed: int, w: float = 1.1, rows: int = 2, sag: float = 0.0):
    """A ground line that thins and breaks up towards both ends, with rows of short strokes below it that thin
    out the same way. `sag` bows the line down in the middle (negative bows it up)."""
    rnd = random.Random(seed)

    def gy(x: float) -> float:
        t = (x - x0) / (x1 - x0)
        return y + sag * 4 * t * (1 - t)
    x = x0 + rnd.uniform(0, 4)
    while x < x1:
        e = _edge(x, x0, x1)
        span = (24 + rnd.random() * 40) * (1 - .8 * e)
        xe = min(x + span, x1)
        mid = (x + xe) / 2
        d.line(f"M{x:.1f},{gy(x) + rnd.uniform(-.5, .5):.1f} Q{mid:.1f},{gy(mid) + rnd.uniform(-.9, .9):.1f} "
               f"{xe:.1f},{gy(xe) + rnd.uniform(-.5, .5):.1f}", w=w * (1 - .5 * e))
        x = xe + .6 + rnd.random() * 2 + 20 * e ** 3
    for r in range(rows):
        strokes = []
        x = x0 + rnd.uniform(4, 16)
        while x < x1 - 4:
            e = _edge(x, x0, x1)
            if rnd.random() > e * 1.1:
                ln = rnd.uniform(3, 9) * (1 - .4 * r)
                yy = gy(x) + 3.4 + r * 3.6 + rnd.uniform(-.6, .6)
                strokes.append(f"M{x:.1f},{yy:.1f} l{ln:.1f},{rnd.uniform(-.3, .3):.1f}")
            x += rnd.uniform(8, 20) * (1 + r * .6)
        if strokes:
            d.line(" ".join(strokes), w=0.6, halo=False)


def tufts(d: Drawing, x0: float, x1: float, y: float, n: int, seed: int, h: float = 4.0, spread: float = 6.0):
    """Grass tufts scattered along a ground line, fewer towards its ends."""
    rnd = random.Random(seed)
    pts = []
    while len(pts) < n:
        x = rnd.uniform(x0, x1)
        if rnd.random() > _edge(x, x0, x1) ** 2:
            pts.append((x, y + rnd.uniform(-spread / 2, spread / 2)))
    grass(d, pts, h=h)


def stones(d: Drawing, pts: list[tuple[float, float, float]], seed: int):
    """Small rocks lying on the ground, each shaded on its south-east side."""
    for i, (x, y, r) in enumerate(pts):
        s = blob(x, y - r * .45, r, r * .5, 6, seed=seed + i, depth=.22)
        d.shape(s, w=0.8)
        d.hatch(f"M{x:.1f},{y - r * .45:.1f} L{x + r * 1.2:.1f},{y - r * .9:.1f} L{x + r * 1.2:.1f},{y + 1:.1f} "
                f"L{x - r * .2:.1f},{y + 1:.1f} Z", angle=45, pitch=1.1, w=0.5)


def soaptree(d: Drawing, x: float, base: float, h: float, seed: int):
    """A soaptree yucca: a shaggy trunk under a round head of stiff, thin leaves."""
    rnd = random.Random(seed)
    top = base - h * .62
    d.line(f"M{x:.1f},{base:.1f} C{x - .6:.1f},{base - h * .3:.1f} {x + .8:.1f},{base - h * .45:.1f} {x:.1f},{top:.1f}",
           w=1.4)
    d.line(" ".join(f"M{x - .8:.1f},{base - h * t:.1f} l1.8,1.2" for t in (.12, .24, .36, .48)), w=0.5, halo=False)
    leaves = []
    for k in range(17):
        a = math.radians(-180 + k * (180 / 16) + rnd.uniform(-5, 5))
        r = h * rnd.uniform(.3, .4)
        leaves.append(f"M{x:.1f},{top:.1f} L{x + r * math.cos(a):.1f},{top + r * math.sin(a) * 1.05:.1f}")
    for a in (20, 160):
        r = h * .26
        leaves.append(f"M{x:.1f},{top:.1f} L{x + r * math.cos(math.radians(a)):.1f},{top + r * .5:.1f}")
    d.line(" ".join(leaves), w=0.6)
    if seed % 2:
        d.line(f"M{x:.1f},{top - h * .3:.1f} L{x + .6:.1f},{top - h * .62:.1f}", w=0.9)
        d.dots([(x + .3 + (i % 2 - .5) * 2.4, top - h * (.46 + i * .04)) for i in range(5)], r=0.7)


def saguaro(d: Drawing, x: float, base: float, h: float, arms: list[tuple[float, float, float]]):
    """A saguaro: a ribbed column with arms that turn up from it, each arm (side -1 or 1, height up the trunk as
    a fraction, length as a fraction of h). One outline round the whole plant, ribs, spines, shade on the east."""
    r = h * .07
    lines = [LineString([(x, base), (x, base - h + r)])]
    for side, at, ln in arms:
        y0 = base - h * at
        out = x + side * (r + h * .1)
        bend = [(x, y0)] + [(x + side * h * .1 * (1 - math.cos(a)) + side * r * .3, y0 - h * .1 * math.sin(a))
                            for a in (.5, 1, 1.4)]
        bend += [(out, y0 - h * .12), (out, y0 - h * ln)]
        lines.append(LineString(bend))
    plant = unary_union([ln.buffer(r if i == 0 else r * .78, quad_segs=6) for i, ln in enumerate(lines)])
    outline = poly(*plant.exterior.coords[:-1])
    d.shape(outline, w=1.1)
    d.edge_shade(outline, dx=-r * .9, dy=0, pitch=1.1)
    ribs, spines = [], []
    for i, ln in enumerate(lines):
        rr = r if i == 0 else r * .78
        for off in (-.45, 0, .45):
            rib = ln.offset_curve(rr * off)
            if not rib.is_empty and rib.length > 2:
                ribs.append(_pl(list(rib.coords)[1:-1] if len(rib.coords) > 3 else list(rib.coords)))
    for px, py in list(plant.exterior.coords)[::3]:
        spines.append(f"M{px:.1f},{py:.1f} l{(px - x) * .04:.1f},-0.8")
    d.line(" ".join(ribs), w=0.45, halo=False)
    d.line(" ".join(spines), w=0.4, halo=False)


UP_WING = ("M19,0.4 C17.6,-3 17,-7 18.2,-11 C20.6,-16 24,-21 28,-25.4 L29.4,-22.6 L31,-24.6 L31.2,-21.2 "
           "L33,-22.6 L32.8,-18.8 L34.4,-19.4 L33,-15.4 C31.6,-10.6 29,-4.6 25.6,0.6 Z")
UP_FEATHERS = "M29.8,-6.4 L20.4,-5.6 M31.6,-11 L19.4,-10 M32.6,-15.4 L21.6,-14.6 M30.4,-20.6 L25.4,-18.6"


def sandhill(d: Drawing, x: float, y: float, k: float, beat: str = "up"):
    """A sandhill crane flying west, its bill at (x, y), about 44 units long at k = 1: neck stretched out, legs
    trailing, both long wings raised ("up") or the near one swept down ("down"), the primaries splayed."""
    _, t = _mover(x, y, k, False)

    def wing(path: str, far: bool):
        q = t(path)
        d.shape(q, w=0.9 if far else 1.0)
        if far:
            d.hatch(q, angle=70, pitch=1.1, w=0.45)
        else:
            d.edge_shade(q, dx=-1.6 * k, dy=0, pitch=1.0)
            d.line(t(UP_FEATHERS if path == UP_WING else _flip_y(UP_FEATHERS)), w=0.45, halo=False)
    if beat == "up":
        wing(_shift(UP_WING, 2.6, 1.2, .82), far=True)
    else:
        wing(_shift(UP_WING, 1.4, 1.6, .38), far=True)
    d.line(t("M0,0 L4.8,0.3"), w=0.9)
    d.shape(t("M4.2,-0.6 C5,-1.8 7,-1.8 7.8,-0.4 C10,0 13,0.4 16,0.4 L16.4,2.6 C13,2.2 10,1.6 7.6,1 "
              "C6.4,1.2 5,0.8 4.2,-0.6 Z"), w=0.9)
    d.hatch(t("M4.8,-0.9 C5.4,-1.6 6.6,-1.6 7.2,-0.8 L6.6,-0.2 Z"), angle=0, pitch=0.6, w=0.45)
    body = "M15,0.6 C18,-0.6 24,-0.8 28,0.2 C30.6,0.8 32.4,1.6 33.4,2.6 C31,3.6 27,4.2 22,4 C19,3.8 16.6,3.2 15,2.4 Z"
    d.shape(t(body), w=1.0)
    d.edge_shade(t(body), dx=0, dy=-1.4 * k, pitch=0.9)
    d.line(t("M31,3 L44,4.6 M31.4,3.6 L43.6,6"), w=0.8)
    wing(UP_WING if beat == "up" else _flip_y(UP_WING, 3.2), far=False)


def _shift(path: str, dx: float, dy: float, ky: float = 1.0) -> str:
    """A wing path moved back and squashed towards the body, for the far wing."""
    return warp(path, lambda x, y: (x + dx, y * ky + dy))


def _flip_y(path: str, about: float = 0.0) -> str:
    return warp(path, lambda x, y: (x, about - y))


# 1. The she-wolf trotting north out of Sonora ---------------------------------------------------------
JUNIPER = [(-.4, .42, .24), (-.14, .62, .28), (.16, .66, .26), (.4, .46, .22), (.04, .4, .28), (-.3, .24, .17),
           (.3, .26, .17)]


def she_wolf() -> Drawing:
    d = Drawing("large-she-wolf", W, H)
    # Low hills far off, junipers dotted on the near slope, and the swell of the open ground before them.
    mountains(d, 22, 284, 118, [(52, 14), (90, 24), (132, 17), (176, 30), (222, 20), (262, 12)], seed=11, w=0.9,
              pitch=1.5, rough=0.5)
    for x, y, h in ((254, 128, 10), (266, 131, 7), (60, 132, 7), (72, 130, 5)):
        broadleaf(d, x, y, h, h * 1.1, seed=x, dark=True, spots=JUNIPER[:4])
    plain(d, 30, 286, 142, seed=14, w=0.8, rows=1, sag=-3)
    # A juniper in the foreground to the west, and a lechuguilla or two.
    broadleaf(d, 38, 194, 50, 58, seed=15, dark=True, spots=JUNIPER)
    lechuguilla(d, 256, 197, 9)
    lechuguilla(d, 272, 194, 6)
    # Her, big and alone, trotting with her head low; her shadow falls to the south-east.
    d.hatch("M104,193 C130,188 200,188 236,192 C220,198 140,199 104,193 Z", angle=0, pitch=1.3, w=0.5)
    lobo(d, 150, 191, 2.1)
    plain(d, 10, 280, 195, seed=16, rows=2)
    tufts(d, 70, 250, 195, 9, seed=17, h=5)
    stones(d, [(92, 199, 2.6), (228, 200, 3.2), (240, 201, 2)], seed=18)
    return d


# 2. The brothers riding up through the pines ---------------------------------------------------------
def riders_in_the_sierra() -> Drawing:
    d = Drawing("large-riders-in-the-sierra", W, H)
    # Ridges behind, the far one higher and lighter, the near one wooded along its foot.
    mountains(d, 6, 284, 96, [(36, 30), (80, 54), (128, 40), (178, 66), (226, 48), (262, 30)], seed=21, w=0.8,
              pitch=2.8, spurs=False)
    mountains(d, 46, 254, 130, [(84, 26), (130, 38), (178, 24), (222, 30)], seed=22, w=1.0, pitch=1.8)
    treeline(d, 52, 248, 132, seed=23, gap=8)
    # The trail climbing east through the pines.
    conifer(d, 238, 158, 62, seed=24, w=0.9)
    conifer(d, 72, 160, 42, seed=25, w=0.9)
    d.line("M30,214 C76,204 112,194 150,180 C182,168 214,160 250,152", w=1.0)
    d.line("M70,215 C110,208 146,198 180,186 C208,177 236,170 264,164", w=0.7, halo=False)
    # Billy ahead and Boyd behind, leaning into the climb.
    n = len(d.items)
    vaquero(d, 190, 176, 0.8, flip=True, coat="dun")
    tilt(d, n, 190, 176, -9)
    n = len(d.items)
    vaquero(d, 120, 203, 0.9, flip=True, coat="bay")
    tilt(d, n, 120, 203, -10)
    conifer(d, 26, 214, 120, seed=26, w=1.1)
    conifer(d, 266, 212, 100, seed=27, w=1.1)
    stones(d, [(160, 199, 4), (172, 200, 2.6), (88, 211, 3.4)], seed=28)
    tufts(d, 80, 240, 205, 6, seed=29, h=4.5, spread=12)
    return d


# 3. Sandhill cranes over a desert range at dusk ------------------------------------------------------
def cranes() -> Drawing:
    d = Drawing("large-cranes", W, H)
    # The sun going down behind the range, its rays fanned up into the evening sky.
    sx, sy, sr = 200, 168, 18
    rays = []
    for k in range(17):
        a = math.radians(-174 + k * 10.5)
        r0, r1 = sr + 5, sr + 14 + 12 * (k % 2)
        rays.append(f"M{sx + r0 * math.cos(a):.1f},{sy + r0 * math.sin(a):.1f} "
                    f"L{sx + r1 * math.cos(a):.1f},{sy + r1 * math.sin(a):.1f}")
    d.line(" ".join(rays), w=0.45, halo=False)
    d.shape(f"M{sx - sr},{sy} A{sr},{sr} 0 0,1 {sx + sr},{sy} Z", w=1.0)
    d.line(f"M{sx - 13},{sy - 8} l26,0 M{sx - 16},{sy - 3.6} l32,0 M132,150 l30,0 M236,148 l30,0 M142,145 l14,0",
           w=0.45, halo=False)
    mountains(d, 4, 284, 194, [(34, 24), (84, 44), (138, 30), (172, 22), (238, 34), (268, 20)], seed=31, w=1.0,
              pitch=1.5)
    # The skein in a long V, high and going south, wings at different points of the beat.
    skein = [(30, 90, 1.05, "up"), (68, 75, 1.0, "up"), (106, 60, .95, "down"), (144, 46, .9, "up"),
             (182, 34, .85, "down"), (220, 24, .8, "up"), (74, 104, 1.0, "down"), (114, 114, .95, "up"),
             (154, 122, .9, "up")]
    for x, y, k, beat in skein:
        sandhill(d, x, y, k, beat=beat)
    chevrons(d, [(250, 40, 1.1), (262, 35, 0.9), (272, 42, 0.8)])
    saguaro(d, 44, 210, 80, [(-1, .5, .32), (1, .62, .28)])
    saguaro(d, 254, 207, 50, [(1, .5, .3)])
    plain(d, 8, 282, 210, seed=33, rows=1)
    tufts(d, 70, 230, 209, 6, seed=34, h=4)
    return d


# 4. A band of horses driven across the Chihuahua grass -----------------------------------------------
def horse_herd() -> Drawing:
    d = Drawing("large-horse-herd", W, H)
    mountains(d, 30, 270, 112, [(70, 8), (110, 12), (150, 7), (200, 14), (240, 9)], seed=41, w=0.6, pitch=1.6,
              rough=0.4, spurs=False)
    plain(d, 14, 284, 114, seed=42, w=0.7, rows=0)
    # The dust they raise, thickest at their heels and drifting up behind them.
    rnd = random.Random(43)
    dust = []
    while len(dust) < 190:
        px, py = rnd.uniform(60, 286), rnd.uniform(84, 200)
        if rnd.random() < ((px - 60) / 226) ** 1.4 * ((py - 84) / 116) ** .8:
            dust.append((px, py))
    d.dots(dust, r=0.5)
    # The loose band going west, from the far ones to the near.
    mustang(d, 146, 146, 0.6, coat="dun", head=6)
    mustang(d, 206, 142, 0.56, coat="bay", head=-4)
    mustang(d, 100, 160, 0.68, coat="bay", head=10)
    mustang(d, 176, 168, 0.74, coat="paint")
    mustang(d, 56, 180, 0.72, coat="dun", head=-8)
    mustang(d, 120, 194, 0.84, coat="bay", head=4)
    # The vaquero behind them, his loop swinging over his head.
    t = vaquero(d, 244, 202, 0.8, coat="dun", arm="M-5,-63 C0,-66 3,-72 1,-83")
    d.line(t("M1,-83 C0,-87 -3,-90 -6,-91"), w=0.6)
    d.shape(t("M-8,-92 C-8,-97 24,-98 27,-93 C28,-88 -8,-88 -8,-92 Z"), w=0.9, fill=False)
    plain(d, 12, 284, 204, seed=44, rows=2)
    tufts(d, 30, 270, 204, 10, seed=45, h=5, spread=8)
    return d


# 5. A lone rider leading a packhorse across the high plain -------------------------------------------
def lone_rider() -> Drawing:
    d = Drawing("large-lone-rider", W, H)
    # A big sky: one tall cloud, its billows drawn in line and only its flat base shaded, and high streaks.
    cloud = ("M60,88 C52,80 58,68 70,70 C70,56 86,48 98,56 C102,40 124,34 136,46 C144,34 164,36 168,50 C178,46 192,54 "
             "188,66 C198,68 202,80 192,88")
    d.line(cloud, w=0.8)
    d.line("M98,56 C104,60 106,66 104,72 M136,46 C134,54 138,60 144,62 M168,50 C166,58 170,62 176,64 "
           "M70,70 C76,72 78,76 78,80", w=0.55, halo=False)
    d.line("M58,89 C90,90 140,89 194,88", w=0.6, halo=False)
    d.hatch("M60,88 C80,80 100,82 120,78 C140,82 160,78 180,80 C186,82 190,85 192,88 Z", angle=0, pitch=1.3, w=0.45)
    d.line("M198,42 l44,0 M216,48 l48,0 M18,108 l34,0 M30,113 l46,0 M210,104 l32,0", w=0.5, halo=False)
    # The far range on the rim of the plain.
    mountains(d, 118, 286, 154, [(146, 10), (176, 20), (206, 15), (240, 27), (268, 12)], seed=51, w=0.7,
              pitch=1.5, rough=0.6)
    plain(d, 4, 286, 155, seed=52, w=0.6, rows=0)
    # The rider going west, the packhorse on a lead behind.
    t = mustang(d, 200, 190, 0.7, coat="dun")
    load = t("M-21,-49 C-21,-58 4,-58 4,-49 L5,-38 C-2,-36 -14,-36 -22,-38 Z")
    d.shape(load, w=1.1)
    d.edge_shade(load, dx=-2, dy=-2, pitch=1.2)
    d.line(t("M-14,-56 L-16,-37 M-3,-56 L-1,-37 M-22,-44 L5,-44"), w=0.6, halo=False)
    vaquero(d, 112, 194, 0.82, coat="bay")
    d.line("M114,150 C126,162 142,166 164,158", w=0.6, halo=False)
    d.hatch("M70,195 C100,191 230,191 262,195 C236,200 100,200 70,195 Z", angle=0, pitch=1.5, w=0.45)
    plain(d, 6, 284, 197, seed=53, rows=2)
    soaptree(d, 30, 208, 42, seed=1)
    soaptree(d, 268, 204, 30, seed=2)
    tufts(d, 40, 260, 203, 9, seed=54, h=4.5, spread=10)
    chevrons(d, [(236, 72, 1.2), (248, 78, 1.0)])
    return d


# 6. A ruined adobe mission in the south-east of Chihuahua --------------------------------------------
def ruined_church() -> Drawing:
    d = Drawing("large-ruined-church", W, H)
    mountains(d, 4, 286, 122, [(28, 22), (70, 42), (118, 30), (178, 60), (230, 40), (266, 24)], seed=61,
              w=0.9, pitch=1.5)
    broadleaf(d, 56, 196, 112, 84, seed=62, spots=[(-.36, .56, .2), (-.2, .78, .2), (.08, .88, .2), (.32, .72, .19),
                                                     (.02, .64, .23), (.36, .52, .15), (-.14, .5, .16)])
    # The nave running back to the east, roofless, its wall tops worn ragged and stepped, a breach in its side.
    nave = ("M150,90 C156,88 160,94 166,93 L170,98 C174,98 176,102 178,106 L182,118 L186,128 L190,134 L195,136 "
            "L199,131 L203,122 L207,114 L211,111 C216,110 222,116 230,115 L236,118 L240,190 L150,192 Z")
    d.shape(nave, w=1.6)
    d.hatch("M150,100 L238,126 L240,190 L150,192 Z", angle=12, pitch=2.2, w=0.45)
    d.edge_shade(nave, dx=-6, dy=-4, pitch=1.4)
    # Through the breach, the inside face of the far wall in shadow.
    inside = ("M178,106 L182,118 L186,128 L190,134 L195,136 L199,131 L203,122 L207,114 L211,111 L212,132 "
              "C206,138 202,148 196,154 C190,148 182,140 177,130 Z")
    d.shape(inside, w=0.9)
    d.hatch(inside, angle=45, pitch=1.1, cross=True)
    # The fallen vigas, one still lodged across the breach, and the beam ends standing out of the wall top.
    for p in ("M184,150 L224,100", "M184,190 L254,174", "M200,192 L246,186", "M170,192 L196,160"):
        d.line(p, w=2.8)
        d.line(p, w=0.9, color=PAPER, halo=False)
    d.line("M158,96 l-6,-3 M176,102 l-5,-3 M198,110 l-4,-3 M222,116 l-4,-3", w=1.6)
    # The west front: a tall gable broken away on its north side, the belfry cracked, the arched door dark.
    front = ("M102,192 L102,86 C106,80 114,74 122,66 L124,52 L140,52 L141,62 L146,64 L144,70 L150,74 L148,80 L152,84 "
             "L152,192 Z")
    d.shape(front, w=1.8)
    d.hatch("M146,84 L152,84 L152,192 L146,192 Z", angle=80, pitch=1.2, w=0.45)
    door = "M116,192 L116,152 C116,139 138,139 138,152 L138,192 Z"
    d.shape(door, w=1.3)
    d.hatch(door, angle=45, pitch=1.1, cross=True)
    d.line("M112.6,192 L112.6,151 C112.6,135 141.4,135 141.4,151 L141.4,192", w=0.7, halo=False)
    for win in ("M128,60 C128,55 135,55 135,60 L135,70 L128,70 Z", "M122,108 C122,102 130,102 130,108 L130,120 "
                "L122,120 Z"):
        d.shape(win, w=1.0)
        d.hatch(win, angle=45, pitch=1.0, cross=True)
    d.line("M130,52 L131.6,38 M126.6,42.6 L135.6,43.6", w=1.3)
    d.line("M138,56 L134,74 L137,86 M108,120 L112,132 L109,140", w=0.6, halo=False)
    # Where the plaster has fallen from the front, the adobe courses show.
    for x0, y0, n in ((106, 156, 4), (134, 92, 3), (140, 168, 3)):
        d.line(" ".join(f"M{x0 + (j % 2) * 3},{y0 + j * 3.2} l5,0 m1.6,0 l5,0" for j in range(n)), w=0.5, halo=False)
        d.line(f"M{x0 - 2},{y0 - 1.6} C{x0 + 4},{y0 - 3.4} {x0 + 10},{y0 - 2.6} {x0 + 14},{y0 - .6} "
               f"C{x0 + 15},{y0 + n * 2} {x0 + 12},{y0 + n * 3.4} {x0 + 6},{y0 + n * 3.4}", w=0.5, halo=False)
    # Rubble at the foot of the walls, and fallen adobes.
    rubble = ("M140,196 C146,188 156,186 162,192 C168,184 182,184 188,192 C196,186 208,184 218,190 C226,184 240,186 "
              "254,196 Z")
    d.shape(rubble, w=1.2)
    d.edge_shade(rubble, dx=-2, dy=-2.4, pitch=1.2)
    for x, y in ((92, 196), (258, 197), (266, 195), (148, 199)):
        b = poly((x, y), (x + 5, y - 1), (x + 5.6, y + 1.6), (x + .6, y + 2.6))
        d.shape(b, w=0.8)
        d.hatch(b, angle=45, pitch=1.0, w=0.45)
    plain(d, 8, 282, 200, seed=64, rows=2)
    tufts(d, 20, 276, 200, 10, seed=65, h=5, spread=8)
    return d


LARGE = {
    "large-she-wolf": she_wolf,
    "large-riders-in-the-sierra": riders_in_the_sierra,
    "large-cranes": cranes,
    "large-horse-herd": horse_herd,
    "large-lone-rider": lone_rider,
    "large-ruined-church": ruined_church,
}


# Traced outlines ---------------------------------------------------------------------------------------
# Thresholded from the plates and traced with potrace, then simplified to points every few tenths of a unit: the
# horse alone (the rider cut away above the back and the plate's docked tail left off), its darkest tones, and the
# horse with its rider. The she-wolf's points were set by hand over the photograph.
HORSE = (
    "-48.2,-58.1 -53.1,-57.7 -54.1,-57.0 -54.1,-56.4 -53.2,-55.1 -54.6,-50.9 -54.6,-41.1 -55.3,-39.9 -53.6,-38.1 "
    "-52.8,-38.4 -51.7,-37.8 -50.5,-38.3 -50.0,-38.7 -50.0,-39.9 -48.5,-42.1 -46.7,-42.3 -47.5,-43.5 -44.4,-47.4 "
    "-42.1,-44.7 -42.3,-43.6 -41.2,-43.0 -39.5,-40.3 -37.5,-38.3 -37.3,-37.6 -38.2,-36.2 -37.8,-36.0 -37.1,-36.8 "
    "-36.6,-36.6 -36.7,-33.7 -35.8,-31.7 -32.7,-28.3 -30.6,-26.9 -34.5,-15.0 -33.9,-12.9 -31.6,-10.8 -28.8,-6.0 "
    "-26.9,-4.6 -27.1,-3.3 -28.7,-1.3 -28.5,-0.9 -26.9,-0.5 -25.1,-2.5 -23.2,-3.0 -21.7,-1.6 -21.3,-1.9 "
    "-21.7,-4.1 -22.4,-5.3 -23.1,-5.1 -23.0,-4.2 -24.0,-4.7 -23.6,-6.0 -24.1,-6.7 -24.5,-10.8 -23.9,-14.7 "
    "-23.9,-24.7 -22.9,-26.8 -8.9,-28.8 1.2,-32.3 1.9,-31.3 3.3,-25.0 4.1,-18.7 4.0,-13.2 1.4,-7.4 -1.0,-3.4 "
    "-3.3,-0.7 -0.9,-0.5 1.4,-2.0 4.5,-8.6 8.7,-15.2 8.8,-23.2 9.7,-25.7 10.9,-26.8 15.3,-23.0 23.4,-13.9 "
    "27.4,-4.9 27.3,-2.2 29.2,-0.6 29.8,-0.8 29.4,-2.8 30.1,-5.1 29.6,-7.2 24.2,-19.6 20.1,-24.7 18.9,-27.0 "
    "18.4,-41.0 16.9,-43.6 18.4,-44.4 18.2,-46.2 10.6,-48.8 6.9,-49.6 -7.9,-47.4 -15.1,-47.6 -20.7,-48.9 "
    "-20.9,-50.6 -22.4,-51.4 -29.9,-52.2 -38.3,-56.0 -42.9,-57.3"
)

HORSE_TONES = (
    "-47.3,-54.2 -48.4,-53.7 -45.8,-51.0 -47.5,-49.2 -47.2,-48.1 -49.0,-46.8 -49.6,-46.8 -50.1,-47.4 -50.9,-46.2 "
    "-51.9,-46.8 -52.5,-46.1 -52.0,-45.5 -51.0,-45.7 -50.0,-43.5 -48.3,-44.2 -44.5,-48.3 -45.2,-49.6 -43.4,-48.3 "
    "-43.0,-48.7 -43.1,-50.7 -45.5,-53.5",
    "-2.6,-47.3 -10.6,-46.3 -16.3,-43.2 -15.5,-42.5 -11.6,-45.2 -10.2,-45.6 -5.6,-45.8 -4.1,-44.8 -3.4,-46.0 "
    "-2.2,-46.9",
    "2.0,-45.2 0.7,-43.8 1.5,-42.5 1.4,-41.6 -1.1,-37.2 -4.1,-39.2 -7.6,-40.2 -8.5,-39.7 -9.1,-38.4 -9.9,-38.2 "
    "-10.7,-37.3 -13.9,-36.5 -14.2,-35.4 -15.0,-35.0 -16.5,-36.2 -17.9,-35.7 -18.7,-36.1 -18.6,-39.3 -19.1,-39.9 "
    "-21.5,-37.4 -23.0,-36.7 -23.9,-34.8 -25.8,-34.2 -26.4,-32.4 -25.6,-30.0 -29.9,-30.0 -30.7,-29.6 -29.6,-28.2 "
    "-30.6,-22.3 -29.7,-20.2 -27.7,-20.6 -26.2,-18.6 -25.6,-18.9 -24.6,-25.5 -22.9,-27.5 -10.5,-29.3 -7.0,-30.8 "
    "-5.2,-30.8 -1.7,-31.8 1.4,-33.3 3.3,-35.1 3.4,-36.8 2.5,-38.2 2.9,-39.3 3.8,-39.6 4.8,-39.0 5.2,-39.4 "
    "4.8,-40.7 6.3,-41.4 5.4,-42.3 3.5,-43.0",
    "10.4,-41.3 8.6,-39.0 9.0,-36.6 7.6,-34.5 7.3,-33.3 3.8,-31.8 3.3,-30.9 3.5,-30.2 5.4,-31.3 6.8,-30.6 "
    "3.8,-27.2 5.2,-26.5 5.1,-25.1 5.9,-20.6 5.0,-19.9 5.9,-17.8 6.3,-17.4 7.0,-18.4 6.4,-20.0 7.7,-21.8 "
    "8.8,-25.5 9.8,-27.0 10.7,-27.5 13.0,-26.2 19.2,-20.5 20.9,-18.3 22.6,-16.9 23.5,-16.8 23.9,-17.5 23.3,-18.9 "
    "19.1,-24.8 18.3,-26.7 18.0,-37.9 17.6,-40.2",
    "-28.7,-40.2 -32.9,-37.3 -34.1,-33.9 -32.8,-32.5 -30.8,-32.7 -29.8,-33.8 -28.7,-33.7 -26.7,-35.1 -26.7,-36.4 "
    "-25.6,-38.3 -25.7,-39.6 -27.6,-39.6",
)

RIDER = (
    "-13.2,-74.2 -15.6,-73.3 -16.3,-73.6 -17.5,-72.7 -17.0,-71.7 -17.8,-70.6 -16.8,-69.8 -17.0,-68.3 -16.4,-66.9 "
    "-15.6,-66.1 -13.9,-66.1 -13.5,-65.7 -14.2,-64.8 -13.8,-64.0 -14.6,-60.2 -14.7,-54.8 -15.3,-53.7 -18.8,-52.7 "
    "-20.1,-51.3 -21.1,-50.9 -23.8,-51.7 -30.2,-52.3 -38.0,-55.9 -43.0,-57.3 -48.1,-58.1 -53.7,-57.6 -54.2,-56.5 "
    "-53.2,-55.0 -54.6,-50.8 -54.6,-41.2 -55.2,-39.8 -53.7,-38.2 -52.7,-38.3 -51.8,-37.8 -50.6,-38.2 -48.6,-42.1 "
    "-46.7,-42.2 -47.4,-43.6 -44.5,-47.4 -42.1,-44.8 -42.4,-43.7 -41.3,-43.1 -37.4,-38.2 -37.3,-37.5 -38.3,-36.3 "
    "-37.9,-35.9 -37.0,-36.8 -36.5,-36.5 -36.7,-33.8 -35.7,-31.7 -32.6,-28.2 -30.6,-27.0 -34.5,-15.1 -34.0,-13.0 "
    "-31.7,-10.9 -28.9,-6.1 -26.9,-4.5 -27.0,-3.4 -28.7,-1.2 -28.0,-0.7 -26.8,-0.6 -25.5,-2.1 -24.2,-2.8 "
    "-23.1,-2.9 -21.6,-1.6 -21.3,-2.0 -22.3,-5.1 -23.0,-5.3 -22.7,-4.6 -23.1,-4.2 -24.0,-4.8 -23.6,-5.9 "
    "-24.1,-6.8 -24.5,-10.9 -23.9,-14.8 -24.0,-24.5 -23.0,-26.7 -8.8,-28.8 1.3,-32.4 3.4,-24.9 4.1,-18.7 "
    "4.0,-13.1 1.3,-7.3 -1.1,-3.3 -3.4,-0.7 -0.9,-0.6 1.4,-2.1 4.6,-8.7 8.7,-15.1 9.0,-16.0 8.8,-23.1 9.6,-25.5 "
    "10.8,-26.8 15.1,-23.2 23.4,-13.9 27.5,-4.8 27.3,-2.1 29.7,-0.6 29.4,-2.9 30.1,-5.2 29.6,-7.2 24.3,-19.5 "
    "20.1,-24.8 18.9,-27.0 18.4,-40.9 17.0,-43.6 18.4,-44.4 18.4,-46.1 10.6,-48.8 7.2,-49.5 -4.6,-47.9 -6.2,-48.4 "
    "-6.7,-50.3 -8.2,-51.2 -7.5,-52.1 -6.3,-52.0 -5.8,-52.8 -5.1,-52.7 -4.0,-53.7 -5.7,-61.0 -6.9,-63.5 "
    "-10.9,-68.4 -10.5,-70.8 -11.0,-73.1"
)

RIDER_TONES = (
    "-8.0,-62.2 -10.4,-58.8 -11.3,-59.4 -12.0,-58.9 -12.7,-56.0 -13.9,-54.4 -14.3,-52.8 -13.9,-51.4 -11.6,-51.6 "
    "-7.9,-53.9 -5.3,-54.1 -5.7,-57.7 -6.6,-60.5 -7.3,-62.0",
    "-47.3,-54.2 -48.4,-53.7 -45.8,-51.0 -47.5,-49.2 -47.2,-48.1 -49.0,-46.8 -49.6,-46.8 -50.1,-47.4 -50.9,-46.2 "
    "-51.9,-46.8 -52.5,-46.1 -52.0,-45.5 -51.0,-45.7 -50.0,-43.5 -48.3,-44.2 -44.5,-48.3 -45.2,-49.6 -43.4,-48.3 "
    "-43.0,-48.7 -43.1,-50.7 -45.5,-53.5",
    "-6.7,-47.5 -11.4,-46.0 -16.3,-43.2 -15.3,-42.5 -11.6,-45.2 -10.2,-45.6 -5.6,-45.8 -4.1,-44.7 -3.4,-46.0 "
    "-2.2,-46.9",
    "2.0,-45.2 0.7,-43.8 1.5,-42.5 1.4,-41.6 -1.1,-37.2 -4.1,-39.2 -7.6,-40.2 -8.5,-39.7 -9.1,-38.4 -9.9,-38.2 "
    "-10.7,-37.3 -13.9,-36.5 -14.2,-35.4 -15.0,-35.0 -16.5,-36.2 -17.9,-35.7 -18.7,-36.1 -18.6,-39.3 -19.1,-39.9 "
    "-21.5,-37.4 -23.0,-36.7 -23.9,-34.8 -25.8,-34.2 -26.4,-32.4 -25.6,-30.0 -29.9,-30.0 -30.7,-29.6 -29.6,-28.2 "
    "-30.6,-22.3 -29.7,-20.2 -27.7,-20.6 -26.2,-18.6 -25.6,-18.9 -24.6,-25.5 -22.9,-27.5 -10.5,-29.3 -7.0,-30.8 "
    "-5.2,-30.8 -1.7,-31.8 1.4,-33.3 3.3,-35.1 3.4,-36.8 2.5,-38.2 2.9,-39.3 3.8,-39.6 4.8,-39.0 5.2,-39.4 "
    "4.8,-40.7 6.3,-41.4 5.4,-42.3 3.5,-43.0",
    "10.4,-41.3 8.6,-39.0 9.0,-36.6 7.6,-34.5 7.3,-33.3 3.8,-31.8 3.3,-30.9 3.5,-30.2 5.4,-31.3 6.8,-30.6 "
    "3.8,-27.2 5.2,-26.5 5.1,-25.1 5.9,-20.6 5.0,-19.9 5.9,-17.8 6.3,-17.4 7.0,-18.4 6.4,-20.0 7.7,-21.8 "
    "8.8,-25.5 9.8,-27.0 10.7,-27.5 13.0,-26.2 19.2,-20.5 20.9,-18.3 22.6,-16.9 23.5,-16.8 23.9,-17.5 23.3,-18.9 "
    "19.1,-24.8 18.3,-26.7 18.0,-37.9 17.6,-40.2",
    "-28.7,-40.2 -32.9,-37.3 -34.1,-33.9 -32.8,-32.5 -30.8,-32.7 -29.8,-33.8 -28.7,-33.7 -26.7,-35.1 -26.7,-36.4 "
    "-25.6,-38.3 -25.7,-39.6 -27.6,-39.6",
)

WOLF = (
    "-35.3,-10.3 -33.0,-14.2 -29.7,-19.0 -26.8,-23.5 -24.8,-28.5 -22.8,-32.8 -19.7,-35.8 -15.0,-37.6 -7.0,-38.0 "
    "-1.0,-37.9 6.3,-38.0 13.7,-38.7 18.3,-39.8 19.7,-41.2 20.6,-45.4 22.4,-42.4 23.0,-42.8 24.8,-46.0 25.8,-42.2 "
    "27.2,-40.8 29.0,-38.6 31.4,-37.0 33.4,-35.6 34.6,-34.8 35.4,-33.6 34.8,-32.6 32.8,-31.8 30.4,-31.2 "
    "28.0,-30.2 25.4,-28.6 23.0,-24.6 21.6,-20.6 20.0,-18.0 20.6,-15.0 21.3,-11.5 20.8,-8.0 20.0,-6.0 18.6,-4.2 "
    "16.8,-5.4 17.6,-8.0 18.0,-11.5 16.8,-13.5 14.0,-15.0 10.0,-16.5 6.0,-17.0 1.7,-18.0 1.0,-14.0 0.5,-9.0 "
    "0.0,-6.7 -1.2,-6.0 -5.0,-6.0 -8.0,-6.4 -8.2,-7.4 -6.0,-8.0 -3.0,-8.5 -2.6,-14.0 -3.0,-17.8 -5.5,-18.6 "
    "-9.0,-19.0 -11.5,-18.2 -13.5,-16.5 -14.5,-13.0 -13.5,-9.8 -10.2,-5.5 -6.8,-1.5 -6.0,0.0 -7.5,0.4 -9.2,0.0 "
    "-11.5,-3.0 -14.8,-7.0 -17.2,-11.2 -19.0,-15.8 -21.5,-20.2 -23.8,-17.4 -26.8,-14.4 -30.2,-11.4 -33.4,-10.0"
)


def main() -> None:
    """Write each drawing's SVG and render its PNG at PNG_WIDTH, or at FALLBACK_WIDTH if that is over MAX_BYTES."""
    only = sys.argv[1:]
    SVG_DIR.mkdir(exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in LARGE.items():
        if only and name not in only:
            continue
        svg = SVG_DIR / f"{name}.svg"
        png = PNG_DIR / f"{name}.png"
        svg.write_text(fn().svg())
        for width in (PNG_WIDTH, FALLBACK_WIDTH):
            subprocess.run(["inkscape", str(svg), "--export-type=png", f"--export-filename={png}", "-w", str(width)],
                           check=True, capture_output=True)
            if png.stat().st_size <= MAX_BYTES:
                break
        print(f"{png.relative_to(ROOT)}: {width} px, {png.stat().st_size // 1024} KB")

if __name__ == "__main__":
    main()
