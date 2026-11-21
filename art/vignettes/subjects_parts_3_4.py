"""Vignettes for Parts III and IV: the brothers' ride into Chihuahua (J4), Billy alone (J5), Boyd and "the girl"
(J6, as reported), and Billy's last journey north with the bones (J7). Loaded by make_vignettes.

The riders all come from one traced outline: a horse walking with a rider, from Eadweard Muybridge's Animal
Locomotion plate 580 (1887, public domain), traced as art/vignettes/traced/rider-annie-g.json (the horse's name
in the plate). The same horse is reused at other sizes and facings, with a cowboy hat, a slicker, a shotgun, a
second rider or a travois drawn on by hand. Everything else is drawn by hand after the references named in the
seed's `credit` column.

Local helpers draw in their own small coordinates and are placed with `place`, a scale-and-shift that keeps the
pen's stroke widths the same at every size.
"""

import math
import random

from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, poly, traced, warp

Pt = tuple[float, float]


def place(d: str, ox: float, oy: float, k: float, flip: bool = False) -> str:
    """Scale a path drawn in local units by k about its origin, mirror it if asked, and move it to (ox, oy)."""
    s = -1 if flip else 1
    return warp(d, lambda x, y: (ox + s * x * k, oy + y * k))


def blob(cx: float, cy: float, rx: float, ry: float, lumps: int, seed: int, depth: float = 0.18) -> str:
    """A lumpy closed outline (a tree crown, a cloud of dust) as cubic curves through jittered points."""
    rnd = random.Random(seed)
    pts = []
    for i in range(lumps):
        a = 2 * math.pi * i / lumps
        r = 1 + (rnd.random() - 0.5) * depth * 2
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    out = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(lumps):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % lumps]
        # Bulge each lump outwards from the centre.
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        bx, by = cx + (mx - cx) * 1.25, cy + (my - cy) * 1.25
        out.append(f"C{(x0 + bx) / 2:.1f},{(y0 + by) / 2:.1f} {(x1 + bx) / 2:.1f},{(y1 + by) / 2:.1f} {x1:.1f},{y1:.1f}")
    return " ".join(out) + " Z"


# The rider ---------------------------------------------------------------------------------------------
# Traced coordinates (horse facing right, hooves on y = 90, centred on x = 48): the rider's head is about
# (51, 21), his hands about (57, 36), the horse's mouth about (88, 50), the withers about (60, 41).
def rider(d: Drawing, ox: float, oy: float, k: float, flip: bool = False, hat: str = "cowboy",
          reins: bool = True, leg: bool = True, extra=None):
    """The traced horse and rider, its hooves centred on (ox, oy), scaled by k. `extra(t)` draws more on top,
    given the same transform for a path in traced units."""
    s = -1 if flip else 1

    def t(path: str) -> str:
        return warp(path, lambda x, y: (ox + s * (x - 48) * k, oy + (y - 90) * k))

    w = 1.5 if k < 0.6 else 1.8
    tr = traced("rider-annie-g")
    for p in tr["outline"]:
        d.shape(t(p), w=w)
        d.edge_shade(t(p), dx=-2 * s, dy=-2.4)
    for p in tr["tones"]["0.3"]:
        d.hatch(t(p), angle=45 if not flip else 135, pitch=2.0)
    if leg:
        d.line(t("M47,39 C52,41 56,43 56.5,47 L53,58 L57,59"), w=1.0, halo=False)
    if reins:
        d.line(t("M57,36 C66,40 78,46 87,49"), w=0.7, halo=False)
    if hat == "cowboy":
        d.shape(t("M42.5,19.6 C46,18.2 56,18.2 59.5,19.6 C56,21 46,21 42.5,19.6 Z"), w=1.2)
        d.shape(t("M46.5,19.2 C46.5,15 47.5,12.6 51,12.6 C54.5,12.6 55.5,15 55.5,19.2 Z"), w=1.2)
        d.hatch(t("M46.5,19.2 L46.5,17.6 L55.5,17.6 L55.5,19.2 Z"), angle=0, pitch=0.9)
    elif hat == "straw":
        d.shape(t("M40.5,20 C45,18.2 57,18.2 61.5,20 C57,21.6 45,21.6 40.5,20 Z"), w=1.1)
        d.shape(t("M47,19.6 C47,16 48,14 51,14 C54,14 55,16 55,19.6 Z"), w=1.1)
    elif hat == "low":  # pulled low against the rain
        d.shape(t("M42,21.4 C46,19.6 56,19.6 60,21.4 C56,23 46,23 42,21.4 Z"), w=1.2)
        d.shape(t("M46.5,21 C46.5,16.5 47.5,14.2 51,14.2 C54.5,14.2 55.5,16.5 55.5,21 Z"), w=1.2)
        d.hatch(t("M46.5,21 L46.5,14.2 L55.5,14.2 L55.5,21 Z"), angle=45, pitch=1.0)
    if extra:
        extra(t)
    return t


def the_girl(d: Drawing, t, x: float = 0):
    """'The girl' as a second, smaller figure seated behind the rider (traced units), dark hair down her back."""
    hair = f"M{37 + x},22 C{35 + x},26 {35 + x},32 {36 + x},37 L{40 + x},37 C{40 + x},31 {41 + x},26 {40 + x},22 Z"
    body = f"M{36 + x},28 C{37 + x},26 {42 + x},25.5 {44 + x},27 L{46 + x},38 L{47 + x},44 L{35 + x},45 L{36 + x},38 Z"
    d.shape(t(body), w=1.2)
    d.shape(t(f"M{37 + x},22.5 C{37 + x},19.6 {39.5 + x},18.4 {41.5 + x},19.6 C{43 + x},20.6 {43 + x},24 {41 + x},25 "
              f"C{39 + x},25.6 {37 + x},24.6 {37 + x},22.5 Z"), w=1.1)
    d.shape(t(hair), w=1.0)
    d.hatch(t(hair), angle=80, pitch=0.9)
    # Her skirt falling over the horse's flank, and her arm round the rider.
    d.line(t(f"M{35 + x},45 C{33 + x},50 {33 + x},54 {34 + x},57 M{47 + x},44 C{48 + x},49 {48 + x},53 {47 + x},56"), w=0.9,
           halo=False)
    d.line(t(f"M{42 + x},30 C{45 + x},32 {47 + x},33 {49 + x},33"), w=1.0, halo=False)


# 1. The brothers and "the girl" riding south (J4, 3-01) ----------------------------------------------
def brothers_and_the_girl() -> Drawing:
    d = Drawing("brothers-and-the-girl")
    d.line("M4,72 C16,70 26,71 36,73 M62,70 C74,68 84,69 92,71", w=0.9)
    # Boyd behind, with "the girl" riding double; Billy ahead and a little nearer.
    rider(d, 32, 74, 0.44, hat="cowboy", extra=lambda t: the_girl(d, t, x=-4))
    rider(d, 62, 86, 0.5, hat="cowboy")
    d.ground(4, 92, 87, ticks=6, seed=31)
    return d


# 2. Boyd and "the girl", riding away together (J6, reported, 3-14) ------------------------------------
def boyd_and_the_girl() -> Drawing:
    d = Drawing("boyd-and-the-girl")
    # A far line of hills, then the two riders side by side: "the girl" beyond, on the horse she rode at
    # San Diego; Boyd nearer, in the straw hat he wore after the river.
    d.line("M4,58 C14,52 22,52 30,56 C38,50 50,50 58,55 C68,50 80,51 92,56", w=1.0)
    d.hatch("M4,58 C14,52 22,52 30,56 C38,50 50,50 58,55 C68,50 80,51 92,56 L92,62 L4,62 Z", angle=20, pitch=3.2, w=0.6)

    def girl(t):
        # Hide the traced rider's hat-less head under her hair and add a skirt.
        d.shape(t("M46,22 C44,26 43,32 44,37 L49,36 C48,31 49,27 50,23 Z"), w=1.0)
        d.hatch(t("M46,22 C44,26 43,32 44,37 L49,36 C48,31 49,27 50,23 Z"), angle=80, pitch=0.9)
        d.line(t("M41,44 C38,50 38,55 40,59"), w=0.9, halo=False)
    rider(d, 64, 74, 0.46, flip=True, hat="none", extra=girl)
    rider(d, 36, 88, 0.52, flip=True, hat="straw")
    d.ground(4, 92, 89, ticks=6, seed=32)
    return d


# 3. Billy alone, searching, the shotgun across the saddle (J5, 3-14) ----------------------------------
def billy_searching() -> Drawing:
    d = Drawing("billy-searching")
    # Grey weather: a low, even sky drawn as a few long level strokes, and the empty road.
    d.line("M10,20 L40,20 M50,17 L86,17 M18,26 L58,26 M66,24 L90,24", w=0.6, halo=False)
    d.line("M4,82 C30,80 60,80 92,78", w=0.9)

    def gun(t):
        d.line(t("M36,38.5 L70,33.5"), w=1.4)
        d.line(t("M36,38.5 L42,37.6"), w=2.4)
    rider(d, 50, 86, 0.78, hat="cowboy", extra=gun)
    d.ground(4, 92, 87, ticks=6, seed=33)
    return d


# 5. North with the bones on a travois (J7, 4-08) ------------------------------------------------------
def bones_travois() -> Drawing:
    d = Drawing("bones-travois")
    # The two sapling poles, lashed at the saddle and dragging behind, with crossbars and the canvas bundle.
    near, far = "M58,62 L6,88", "M60,59 L12,84"
    d.line(far, w=1.6)
    d.line("M20,80 L16,85 M30,75 L27,81 M42,69 L39,75", w=1.0)
    bundle = "M15,79 C15,76 18,74.5 22,73 L44,63 C47,62 49,64 49,66.5 C49,68.5 48,69.6 46,70.4 L23,81 C19,82.6 15,82 15,79 Z"
    d.shape(bundle, w=1.6)
    d.edge_shade(bundle, dx=1.5, dy=-2.4)
    d.line("M21,73.6 C22,76 23,79 22.6,81 M37,66.4 C38,68.6 38.6,71 38,73.4 M45.6,62.8 C46.4,65 46.6,67.6 46,70", w=0.9,
           halo=False)
    d.line(near, w=1.8)
    rider(d, 68, 86, 0.52, hat="cowboy")
    d.ground(2, 94, 89, ticks=6, seed=35)
    return d


# 6. The windmill and the stone tank on the high prairie (J4, 3-05) ------------------------------------
def windmill_tank() -> Drawing:
    d = Drawing("windmill-tank")
    # The long skewed shadow of the vanes turning out on the prairie.
    shadow = ellipse(20, 88, 16, 2.8)
    d.hatch(shadow, angle=10, pitch=1.6)
    # The tower: four wooden legs drawn as two, tapering to a platform, with braces.
    d.line("M34,88 L43,36 M58,88 L49,36", w=1.6)
    d.line("M37,72 L55,72 M40,55 L52,55 M42,44 L50,44", w=1.0)
    d.line("M37,72 L52,55 M55,72 L40,55 M40,55 L50,44 M52,55 L42,44", w=0.7, halo=False)
    d.line("M45,36 L45,88", w=0.7, halo=False)
    d.shape(poly((40, 36), (52, 36), (52, 38.4), (40, 38.4)), w=1.2)
    # The tail vane out behind, then the wheel seen a little edgewise, its blades as short strokes.
    d.line("M46,26 L74,20", w=1.3)
    vane = poly((66, 16.5), (84, 12), (85, 26), (67, 25))
    d.shape(vane, w=1.3)
    d.edge_shade(vane, dx=-2, dy=-2)
    d.shape(ellipse(46, 26, 11, 14), w=1.3, fill=True)
    blades = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        x0, y0 = 46 + 4.4 * math.cos(a), 26 + 5.6 * math.sin(a)
        x1, y1 = 46 + 10.6 * math.cos(a + 0.12), 26 + 13.6 * math.sin(a + 0.12)
        blades.append(f"M{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f}")
    d.line(" ".join(blades), w=0.8, halo=False)
    d.shape(circle(46, 26, 2.4), w=1.1)
    # The trough of hewn limestone, the pipe running into it, and the water.
    d.line("M51,66 L64,66 L64,72", w=1.2)
    front = poly((58, 76), (92, 76), (92, 87), (58, 87))
    top = poly((60, 72.6), (90, 72.6), (92, 76), (58, 76))
    d.shape(top, w=1.3)
    d.hatch(top, angle=0, pitch=1.2)
    d.shape(front, w=1.6)
    d.line("M58,81.5 L92,81.5 M66,76 L66,81.5 M76,76 L76,81.5 M85,76 L85,81.5 M62,81.5 L62,87 M71,81.5 L71,87 "
           "M81,81.5 L81,87 M89,81.5 L89,87", w=0.7, halo=False)
    d.edge_shade(front, dx=-3, dy=-2)
    d.line("M64,72 l0,2.4", w=0.6, halo=False)
    # Doves flaring away.
    d.line("M8,18 l2,-1.6 l2,1.6 M14,12 l2.2,-1.8 l2.2,1.8 M20,20 l1.8,-1.4 l1.8,1.4", w=0.8)
    d.ground(4, 94, 88, ticks=7, seed=36)
    return d


# 7. The corriente steers trailing north to the Naco pens (J4, 3-04) -----------------------------------
STEER = ("M8,8 C6,10 3,13 1.6,16 C1.4,17.6 2.6,18.8 4,18.6 C6,18.2 8,17.4 9.6,17.6 C11,18.6 12,21 13.6,22 "
         "L34,22.6 C37,22.6 39.4,21 40.4,18 C41.4,14.6 41.2,11 40,8.6 C37.6,6.6 32,6.8 26,7.2 C20,7.2 16,6 13,6 "
         "C11,6 9.4,6.8 8,8 Z")
STEER_LEGS = "M15,21.6 L14,30 M18.6,22 L19.6,30 M32,22.4 L31,30 M37.6,20.4 C38.6,24 37.4,27 38.4,30"
STEER_HORNS = "M8.4,8 C5,6 1,5.6 -3,2.4 M9.6,7.4 C13,5.4 16,3.4 18,-0.8"


def steer(d: Drawing, ox: float, oy: float, k: float, flip: bool = False):
    """A lean steer walking, head low, origin at the top left of its local 42 x 30 box."""
    body = place(STEER, ox, oy, k, flip)
    d.shape(body, w=1.4)
    d.edge_shade(body, dx=-1.8 if not flip else 1.8, dy=-2.2)
    d.line(place(STEER_LEGS, ox, oy, k, flip), w=1.4)
    d.line(place(STEER_HORNS, ox, oy, k, flip), w=1.4)
    d.line(place("M40.6,9 C42.6,13 42.8,19 42,25", ox, oy, k, flip), w=0.9)
    d.line(place("M9,9.4 l3,2", ox, oy, k, flip), w=0.8, halo=False)


def corriente_steers() -> Drawing:
    d = Drawing("corriente-steers")
    # Dust raised by the herd, then three steers, the nearest last.
    d.dots([(46, 40), (52, 36), (60, 34), (72, 33), (82, 36), (88, 42), (90, 50), (84, 30), (66, 30)], r=0.6)
    d.line("M70,36 C76,32 84,34 88,38 M78,44 C84,42 90,44 92,48", w=0.6, halo=False)
    steer(d, 40, 36, 0.86)
    steer(d, 52, 48, 0.92)
    steer(d, 10, 50, 1.02)
    d.ground(2, 94, 82, ticks=7, seed=38)
    return d


# 8. Sandhill cranes going south over the river camp (J5, 3-12) ----------------------------------------
def crane(d: Drawing, x: float, y: float, k: float, up: bool):
    """A crane flying left: neck and bill stretched out ahead, legs trailing, one wing up or down."""
    s = -1 if up else 1
    d.line(place("M0,0 L3,0.4 L10,1.2 L16,1.8", x, y, k), w=1.4)
    d.shape(place("M9,1 C11,-0.4 16,-0.2 18,1.4 C16,3 11,3.2 9,1.8 Z", x, y, k), w=1.0)
    d.line(place("M17.6,1.8 L27,2.8", x, y, k), w=0.8)
    wing = f"M11,1.2 C11,{1 + 5 * s} 14,{1 + 9 * s} 19,{1 + 12 * s} C17,{1 + 7 * s} 16,{1 + 3 * s} 15.6,1.6 Z"
    d.shape(place(wing, x, y, k), w=1.0)
    d.hatch(place(wing, x, y, k), angle=60, pitch=1.0)


def sandhill_cranes() -> Drawing:
    d = Drawing("sandhill-cranes")
    moon = circle(80, 15, 6)
    d.shape(moon, w=1.2)
    # A thin echelon, high, going south (left), wings at different points of the beat.
    for x, y, k, up in [(8, 22, 1.0, True), (22, 30, 0.95, False), (36, 38, 0.9, True), (50, 46, 0.85, False),
                        (63, 54, 0.8, True)]:
        crane(d, x, y, k, up)
    # The river below, with its gravel bar, the driftwood fire, and cottonwoods on the far bank.
    for x, h, w, seed in ((70, 20, 16, 1), (84, 17, 13, 2)):
        crown = blob(x, 86 - h, w / 2, h / 2.4, 8, seed=380 + seed)
        d.line(f"M{x - 1},86 L{x - 1},{86 - h / 2:.0f} M{x + 1.4},86 L{x + 2},{86 - h / 2:.0f}", w=1.2)
        d.shape(crown, w=1.3)
        d.edge_shade(crown, dx=-3, dy=-3)
    d.line("M4,82 C20,80 36,81 54,80 M4,88 C24,87 40,88 60,86", w=0.9)
    d.line("M10,85 l7,0 M28,84.6 l9,0 M44,85.4 l6,0", w=0.6, halo=False)
    d.line("M24,92 l2.2,-4 l1.4,2.6 l1.4,-4.4 l1.6,5.8", w=1.1)
    d.ground(4, 92, 92, ticks=5, seed=39)
    return d


# 9. The cottonwood camp on the river near San José (J4, 3-08) -----------------------------------------
def cottonwood(d: Drawing, x: float, base: float, h: float, w: float, seed: int):
    """A river cottonwood: a pale bole forking low into two or three limbs, under a broad, lumpy crown."""
    top = base - h * .62
    d.shape(f"M{x - 2.6},{base} C{x - 2},{base - h * .2} {x - 2},{base - h * .3} {x - 1.2},{base - h * .36} "
            f"L{x + 1.4},{base - h * .36} C{x + 2},{base - h * .3} {x + 2},{base - h * .2} {x + 3},{base} Z", w=1.3)
    d.line(f"M{x - .6},{base - h * .34} C{x - 2},{base - h * .44} {x - w * .2},{top + 4} {x - w * .26},{top} "
           f"M{x + .8},{base - h * .34} C{x + 2},{base - h * .46} {x + w * .18},{top + 3} {x + w * .22},{top - 2} "
           f"M{x},{base - h * .36} L{x + .4},{top - 4}", w=1.3)
    crown = blob(x, base - h * .7, w / 2, h * .3, 13, seed=seed, depth=0.28)
    d.shape(crown, w=1.5)
    d.edge_shade(crown, dx=-3.5, dy=-3.5)
    rnd = random.Random(seed)
    leaves = []
    for _ in range(9):
        lx = x + (rnd.random() - .6) * w * .6
        ly = base - h * .7 + (rnd.random() - .6) * h * .36
        leaves.append(f"M{lx:.1f},{ly:.1f} c1.2,-1.4 2.6,-1.4 3.6,0")
    d.line(" ".join(leaves), w=0.6, halo=False)


def cottonwood_camp() -> Drawing:
    d = Drawing("cottonwood-camp")
    cottonwood(d, 22, 70, 62, 34, seed=391)
    cottonwood(d, 72, 66, 54, 30, seed=392)
    cottonwood(d, 48, 72, 46, 26, seed=393)
    # The camp under the trees: bedrolls by a small fire, its smoke going up through the branches.
    d.shape("M28,76 C28,74 38,73.6 40,75 C40,77 30,77.6 28,76 Z", w=1.1)
    d.shape("M58,76.4 C58,74.6 67,74.2 69,75.6 C69,77.4 60,78 58,76.4 Z", w=1.1)
    d.line("M47,77 l2,-3.6 l1.2,2.2 l1.2,-3.6 l1.4,5", w=1.0)
    d.line("M50,70 C48,66 52,63 50,59", w=0.6, halo=False)
    # The river, and the far bank where the riders came.
    d.line("M2,82 C20,80 40,81 60,80 C72,79.6 84,80 94,79 M2,89 C24,88 46,89 70,87 C80,86.6 88,87 94,86.6", w=1.0)
    d.line("M10,85.4 l8,0 M34,85 l10,0 M60,84.2 l7,0 M80,83.4 l8,0", w=0.6, halo=False)
    return d


# 10. The farmworkers' truck that took Boyd north (J4 and J6, 3-08) ------------------------------------
def workers_truck() -> Drawing:
    d = Drawing("workers-truck")
    # Dust behind it and the raw dirt road.
    d.line(blob(88, 52, 8, 7, 7, seed=40, depth=0.2), w=0.6, halo=False)
    d.dots([(92, 44), (94, 52), (86, 42)], r=0.6)
    d.line("M2,72 C30,71 60,71 94,70", w=0.9)
    # Workers standing in the bed: heads and hats over the stake sides; one holds the cab roof as lookout.
    for x, y in ((46, 33), (54, 34), (62, 33), (70, 34), (78, 33.4)):
        d.shape(f"M{x - 3.6},50 L{x - 3},{y + 4} C{x - 2},{y + 2.4} {x + 2},{y + 2.4} {x + 3},{y + 4} L{x + 3.6},50 Z", w=1.0)
        d.shape(circle(x, y, 2.2), w=1.0)
        d.line(f"M{x - 3.8},{y - 1.6} L{x + 3.8},{y - 1.6}", w=1.0)
        d.hatch(f"M{x - 2},{y - 1.6} L{x - 1.6},{y - 4} L{x + 1.6},{y - 4} L{x + 2},{y - 1.6} Z", angle=0, pitch=0.9)
    d.line("M43,38 L38,31", w=1.2)
    # Stake sides.
    d.line("M40,40 L86,40 M40,46 L86,46", w=1.2)
    d.line(" ".join(f"M{x},38 L{x},54" for x in (41, 50, 59, 68, 77, 86)), w=1.2)
    # Bed and chassis.
    d.shape(poly((36, 54), (88, 54), (88, 58), (36, 58)), w=1.4)
    # Cab: a square cab with its window, then the long hood and the radiator.
    cab = poly((24, 62), (24, 32), (27, 29.4), (39, 29.4), (40, 32), (40, 62))
    d.shape(cab)
    win = poly((27, 34), (37, 34), (37, 43), (27, 43))
    d.shape(win, w=1.0)
    d.hatch(win, angle=45, pitch=1.4)
    d.line("M27,47 L37,47 M38,50 l-2.4,0", w=0.8, halo=False)
    hood = "M6,58 L6,44 C6,42 7,41 9,41 L24,39 L24,58 Z"
    d.shape(hood)
    d.line("M14,44 L14,52 M16.4,44 L16.4,52 M18.8,44 L18.8,52", w=0.6, halo=False)
    d.shape(poly((3.4, 58), (3.4, 42), (6.4, 41.6), (6.4, 58)), w=1.2)
    d.hatch(poly((3.4, 58), (3.4, 42), (6.4, 41.6), (6.4, 58)), angle=0, pitch=1.0)
    d.edge_shade(cab, dx=-3, dy=-2.5)
    # Fenders, running board and wheels.
    d.shape("M4,62 C5,52 23,52 27,62 L24,62 C21,56 9,56 7,62 Z", w=1.3)
    d.line("M26,61 L60,61", w=1.2)
    d.shape("M60,62 C61,52 79,52 83,62 L80,62 C77,56 65,56 63,62 Z", w=1.3)
    for cx in (15.6, 71.6):
        d.shape(circle(cx, 64, 7), w=1.7)
        d.shape(circle(cx, 64, 2.6), w=1.0)
        d.hatch(circle(cx, 64, 7), angle=60, pitch=1.8)
        d.shape(circle(cx, 64, 2.6), w=1.0)
    return d


# 11. Boyd's grave on the Gallego road: the nameless board cross, the wire wreath, unmarked cairns (4-06)
def boyds_grave() -> Drawing:
    d = Drawing("boyds-grave")
    # The blue mountains on the skyline, and a black smoke going up from the trash burning off to the south.
    hills = "M4,30 C12,22 20,20 28,26 C36,16 46,14 54,22 C62,18 70,20 76,24 C82,20 88,22 92,26"
    d.line(hills, w=1.0)
    d.hatch(hills + " L92,34 L4,34 Z", angle=20, pitch=3.0, w=0.6)
    d.line("M84,36 C80,30 86,26 82,20 C79,15 84,11 80,6", w=1.6)
    d.line("M86,36 C84,31 89,27 86,21", w=0.8, halo=False)
    # The low mud wall, in ruins.
    wall = "M2,44 L2,38 C10,37 18,38 26,37 L30,40 L34,44 Z M44,44 L46,39 C56,38 66,38.6 74,38 L76,44 Z"
    d.shape(wall, w=1.3)
    d.edge_shade(wall, dx=-1.6, dy=-1.6)
    # Unmarked cairns of loose rock over the field, one with two slats wired into a cross, and a raven flying up.
    for x, y, k in ((10, 60, 0.9), (30, 52, 0.7), (76, 56, 0.8), (60, 48, 0.6), (88, 70, 0.9)):
        cairn = f"M{x - 8 * k},{y} C{x - 6 * k},{y - 5 * k} {x + 6 * k},{y - 5 * k} {x + 8 * k},{y} Z"
        d.shape(cairn, w=1.2)
        d.edge_shade(cairn, dx=-1.4, dy=-1.4)
    d.line("M76,54 L76,44 M72.6,47 L79.4,47", w=1.2)
    d.line("M56,8 C58,5 60,5 62,8 C64,5 66,5 68,8", w=1.2)
    # Boyd's grave against the wall: the board cross with the date and dedication burned into it and no name,
    # and the ring of rusted wire that was a wreath leaning on it.
    cairn = "M22,90 C24,82 30,77 40,76 C50,75 60,77 66,82 C70,85 72,88 72,90 Z"
    d.shape(cairn, w=1.6)
    d.edge_shade(cairn, dx=-3, dy=-3)
    for x, y, rx, ry in ((32, 85, 3.2, 2.0), (42, 81, 3.4, 2.0), (54, 82, 3.4, 2.0), (62, 86, 3.0, 1.8),
                         (46, 87, 3.4, 2.0)):
        d.line(ellipse(x, y, rx, ry), w=0.7, halo=False)
    cross_v = poly((42, 82), (42.4, 40), (50, 40.2), (49.6, 82))
    cross_h = poly((30, 50), (62, 49), (62.2, 57.4), (30.2, 58.4))
    d.shape(cross_v, w=1.7)
    d.shape(cross_h, w=1.7)
    d.edge_shade(cross_v, dx=-2, dy=0)
    d.line("M33,52.6 l4,0 M38.6,52.4 l2,0 M51,52 l5,0 M57.4,51.8 l2.6,0 M33,55.4 l6,-0.2 M51.4,55 l3,0 "
           "M44,61 l4,0 M44,64.4 l3.4,0 M44,67.8 l4,0", w=0.7, halo=False)
    d.shape(ellipse(60, 74, 7.4, 8.4), w=1.3, fill=False)
    d.line(ellipse(60, 74, 5.6, 6.6), w=0.7, halo=False)
    d.line(" ".join(f"M{60 + 6.5 * math.cos(a):.1f},{74 + 7.5 * math.sin(a):.1f} l1.4,-1.6" for a in
                    (i * math.pi / 7 for i in range(14))), w=0.6, halo=False)
    d.ground(4, 94, 92, ticks=7, seed=41)
    return d


# 12. The fair at Madera: the opera caravan repainted as a show, its lotería wheel, sawmill smoke (J7, 4-05)
def pine(d: Drawing, x: float, base: float, h: float, seed: int):
    """A ponderosa: a straight bole and a crown of loose, flat clumps set off to either side, flat at the top."""
    d.line(f"M{x},{base} L{x},{base - h}", w=1.2)
    rnd = random.Random(seed)
    n = 5
    for i in range(n):
        cy = base - h * (0.4 + 0.6 * i / n)
        cw = h * (0.34 - 0.04 * i) * (0.8 + rnd.random() * 0.4)
        cx = x + (1 if i % 2 else -1) * h * 0.07 + (rnd.random() - 0.5) * 1.6
        clump = blob(cx, cy, cw / 2, h * 0.06, 9, seed=seed * 10 + i, depth=0.3)
        d.shape(clump, w=1.0)
        d.edge_shade(clump, dx=-1.6, dy=-1.6, pitch=1.6)


def madera_fair() -> Drawing:
    d = Drawing("madera-fair")
    # The pine ridge behind the town, and the sawmill's stack with its smoke drifting over the fair.
    ridge = "M2,30 C14,24 26,22 38,26 C50,20 64,18 76,24 C84,22 90,24 94,26"
    d.line(ridge, w=1.0)
    for x, base, h, seed in ((22, 30, 16, 1), (34, 28, 14, 2), (88, 28, 16, 4)):
        pine(d, x, base, h, seed=420 + seed)
    d.shape(poly((6, 40), (6, 12), (9.4, 12), (9.4, 40)), w=1.2)
    d.line("M8,10 C14,4 24,8 32,4 C40,1 50,6 60,3 C68,1 76,5 84,3", w=1.0, halo=False)
    d.line("M9,7 C16,2 22,4 28,1", w=0.6, halo=False)
    # The old opera caravan, repainted: the curved roof, the gaudy new panels with the old gilt lettering showing
    # through above them, and the lotería wheel fastened to its side.
    body = "M40,70 L40,36 C50,29 82,29 94,36 L94,70 Z"
    d.shape(body)
    d.edge_shade(body, dx=-3, dy=-3)
    d.line("M40,38 C50,31.4 82,31.4 94,38", w=1.0, halo=False)
    d.line(" ".join(f"M{x},40.6 l0.6,2.4 M{x + 1.6},40.6 l1,2.4" for x in range(44, 92, 4)), w=0.5, halo=False)
    d.line("M42,46 L92,46", w=0.8, halo=False)
    for cx, cy in ((48, 60), (86, 60)):
        d.line(f"M{cx - 4},{cy} L{cx},{cy - 6} L{cx + 4},{cy} L{cx},{cy + 6} Z", w=0.9, halo=False)
    wheel = circle(67, 58, 11)
    d.shape(wheel, w=1.6)
    d.shape(circle(67, 58, 7), w=0.8)
    d.line(" ".join(f"M{67 + 7 * math.cos(a):.1f},{58 + 7 * math.sin(a):.1f} L{67 + 11 * math.cos(a):.1f},"
                    f"{58 + 11 * math.sin(a):.1f}" for a in (i * math.pi / 5 for i in range(10))), w=0.7, halo=False)
    d.shape(circle(67, 58, 1.8), w=0.9)
    # La calavera stopped at the top of the wheel.
    d.dots([(65.8, 49.6), (68.2, 49.6)], r=0.6)
    d.line("M66,51.6 L68,51.6", w=0.6, halo=False)
    for cx in (50, 84):
        d.shape(circle(cx, 74, 5), w=1.4)
        d.line(" ".join(f"M{cx},74 L{cx + 5 * math.cos(a):.1f},{74 + 5 * math.sin(a):.1f}"
                        for a in (i * math.pi / 3 for i in range(6))), w=0.6, halo=False)
    # The pitchman in his pulpit, holding out his cane over the crowd.
    pulpit = poly((18, 72), (16, 52), (36, 52), (34, 72))
    d.shape(pulpit, w=1.5)
    d.line("M15,52 L37,52 M17.4,57 L34.6,57", w=0.8, halo=False)
    d.hatch(poly((17.4, 57), (34.6, 57), (34, 72), (18, 72)), angle=45, pitch=1.6)
    man = "M21.6,52 L22,44 C22.4,42 24,41.4 26,41.4 C28,41.4 29.6,42 30,44 L30.4,52 Z"
    d.shape(man, w=1.3)
    d.hatch(man, angle=45, pitch=1.4)
    d.shape(circle(26, 36.4, 2.8), w=1.1)
    d.line("M29,44 L35,41", w=1.3)
    d.line("M35,41 L52,47", w=1.4)
    d.dots([(52.4, 47.2)], r=1.2)
    # The crowd of men in hats inside the rope, looking up at the wheel.
    d.line("M2,78 C30,79 60,79 94,78", w=0.8)
    for i, x in enumerate(range(6, 94, 10)):
        y = 90 + (i % 2) * 1.6
        d.shape(f"M{x - 5},96 C{x - 5},{y - 2} {x - 3},{y - 4} {x},{y - 4} C{x + 3},{y - 4} {x + 5},{y - 2} {x + 5},96 Z",
                w=1.2)
        d.shape(circle(x, y - 7, 2.6), w=1.0)
        d.shape(f"M{x - 5.4},{y - 9} C{x - 2},{y - 10.2} {x + 2},{y - 10.2} {x + 5.4},{y - 9} "
                f"C{x + 2},{y - 8.2} {x - 2},{y - 8.2} {x - 5.4},{y - 9} Z", w=1.0)
        d.shape(f"M{x - 2.4},{y - 9.4} C{x - 2.4},{y - 13} {x + 2.4},{y - 13} {x + 2.4},{y - 9.4} Z", w=1.0)
    return d

SUBJECTS = {
    "brothers-and-the-girl": brothers_and_the_girl,
    "boyd-and-the-girl": boyd_and_the_girl,
    "billy-searching": billy_searching,
    "bones-travois": bones_travois,
    "windmill-tank": windmill_tank,
    "corriente-steers": corriente_steers,
    "sandhill-cranes": sandhill_cranes,
    "cottonwood-camp": cottonwood_camp,
    "workers-truck": workers_truck,
    "boyds-grave": boyds_grave,
    "madera-fair": madera_fair,
}
