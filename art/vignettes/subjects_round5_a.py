"""Vignettes of the fifth round: the Indian at the tank below the Parham house, the trapping trips into the
Peloncillos with the she-wolf's road north and her howl at dawn, and Billy's first days taking her south (Part I,
1-01 to 1-08). Each stands at its stop or at a point along its leg (decision 0066). Loaded by
art/vignettes/make_vignettes.py.

Each is checked against the episode that shows it. The riders and horses are the traced Muybridge plate
(rider-annie-g, public domain) through the Parts III and IV helpers, the trotting wolf and the hounds the traced US Fish and
Wildlife Service outline. The howling wolf, the crouched figures and the steel trap (after the Newhouse trap of the
first set) are drawn by hand, with everything else, from the book. Light from the north-west, as everywhere: shade on each shape's south-east side.
"""

import math

from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly, traced, warp
from art.vignettes.subjects_parts_1_2 import fit, wolf
from art.vignettes.subjects_parts_3_4 import blob, pine, place, rider
from art.vignettes.subjects_round3 import figure, horse
from art.vignettes.subjects_round4 import chain, round_

# A person squatting on their heels, facing east, in the 24-unit figure of `figure` (feet at the origin): the
# coat leaning forward over the knees, and the legs folded under it.
CROUCH_COAT = "M-1.2,-12.6 C0,-13.6 2.4,-13.4 3.2,-12.2 L2.6,-7.4 C0.6,-6.4 -1.6,-5.4 -3.4,-4.6 Z"
CROUCH_LEGS = ("M-3.2,-4.4 L5,-9.6 C6.4,-9.8 6.8,-8.8 6.4,-7.6 L5.8,-1.2 L7.8,-0.2 L7.6,0.4 L0.4,0.4 "
               "C-1.8,-0.4 -3.4,-2.2 -3.2,-4.4 Z")


def crouch(d: Drawing, x: float, y: float, h: float, flip: bool = False, hat: bool = True):
    """A person squatting on their heels, feet at (x, y), h the height they would stand. Returns the placer for
    drawing arms and what they hold in the same local units."""
    k = h / 24

    def p(path: str) -> str:
        return place(path, x, y, k, flip)
    legs = p(CROUCH_LEGS)
    d.shape(legs, w=1.1)
    d.hatch(legs, angle=45 if not flip else 135, pitch=1.3)
    coat = p(CROUCH_COAT)
    d.shape(coat, w=1.2)
    d.edge_shade(coat, dx=-1.2 * (-1 if flip else 1), dy=-1.2)
    d.shape(p(round_(2.2, -15.4, 2.3)), w=1.0)
    if hat:
        brim = p("M-2.4,-16.6 L6.8,-16.6 L4.6,-17.6 C4.6,-21 -0.2,-21 -0.2,-17.6 Z")
        d.shape(brim, w=0.9)
        d.hatch(brim, angle=0, pitch=0.9)
    return p


# The she-wolf sitting back on her haunches, muzzle thrown up to howl, facing east (feet at the origin). Drawn by
# hand: the traced trotting wolf cannot be bent into this pose (the howling photograph is a head only).
HOWL = ("M12,-47 L13,-45.4 C11,-42 10,-39 8.4,-36 C7.4,-32 7.6,-27 7,-22 C6.6,-17 6.2,-10 6.8,-3 L9.8,-1.4 L9.6,0 "
        "L3.4,0 L3.4,-10 C1,-8 -1.6,-5 -2.6,-1.6 L-0.6,0 L-8,0 C-14,0 -17,-4 -16,-10 C-15,-18 -10,-24 -6,-28 "
        "C-4,-31 -2,-35 -0.4,-38 L-1.6,-44.6 L2.4,-41 C4.4,-42.4 7,-45.4 9,-47.6 Z")
HOWL_TAIL = "M-14.6,-3 C-19,-3.6 -24,-2 -27,1 C-22,2.4 -17,1.6 -13.6,-0.4 Z"
HOWL_SADDLE = "M-14,-14 C-12,-20 -8,-25 -5,-28.6 C-3.4,-31 -2,-34 -0.8,-37 L2,-34 C0,-28 -4,-22 -8,-16 Z"


def howling(d: Drawing, x: float, y: float, k: float):
    """The she-wolf howling, sitting, feet at (x, y), scaled by k (about 50 units tall at k = 1)."""
    tail = place(HOWL_TAIL, x, y, k)
    d.shape(tail, w=1.2)
    d.hatch(tail, angle=30, pitch=1.2)
    body = place(HOWL, x, y, k)
    d.shape(body, w=1.6)
    d.edge_shade(body, dx=-2.6, dy=-2.6)
    d.hatch(place(HOWL_SADDLE, x, y, k), angle=60, pitch=1.3)
    d.line(place("M12.6,-45.6 L9.6,-43.4 M3.4,-10 C2,-14 0,-17 -4,-19", x, y, k), w=0.9, halo=False)
    d.dots([(x + 5.6 * k, y - 42.4 * k)], r=0.7)


def hound(d: Drawing, k: float, ox: float, oy: float, flip: bool = False, collar: bool = True):
    """A ranch hound running low, from the traced wolf outline: left pale, with a dropped ear and a collar.
    Returns the transform from wolf units, for a chain."""
    f = fit(k, ox, oy, flip)
    g = lambda x, y: f(x, y + (0.16 * (x - 56) if x > 56 else 0))  # noqa: E731
    for p in traced("she-wolf")["outline"]:
        d.shape(warp(p, g), w=1.3)
    ear = warp("M75,30 C72,36 73,44 77,46 C80,43 81,36 80,30 Z", g)
    d.shape(ear, w=1.0)
    d.hatch(ear, angle=80, pitch=0.9)
    if collar:
        d.line(warp("M68,34 C69,40 70,46 71,52", g), w=1.8)
    return g


# 1. The Indian squatting in the carrizo by the tank, his rifle across his knees (1-01) -----------------
def indian_at_the_tank() -> Drawing:
    d = Drawing("indian-at-the-tank")
    # The sun going down red behind the barren mountains to the west, across the river bed.
    d.line("M30,46 C40,40 48,38 56,42 C64,37 76,37 84,40 C88,39 92,40 94,42", w=0.9)
    d.shape("M58,40 C58,33 70,33 70,40 Z", w=1.0)
    d.line("M55,32 l-3,-3 M64,30 l0,-4 M73,32 l3,-3", w=0.7, halo=False)
    # The thin stand of carrizo cane, and the Indian squatting under it with the old single-shot rifle.
    canes = [(3, 24), (9, 18), (29, 22), (34, 34)]
    d.line(" ".join(f"M{x},88 C{x - 0.6},70 {x + 0.6},50 {x + 1.6},{top}" for x, top in canes), w=1.0)
    d.line(" ".join(f"M{x + 0.4},{top + 10} l-5,4 M{x + 1},{top + 4} l5,3 M{x + 0.8},{top + 20} l4,4"
                    for x, top in canes), w=0.7, halo=False)
    p = crouch(d, 16, 88, 44, hat=False)
    d.hatch(p("M1.6,-17.6 C-0.4,-17.4 -1,-15 -0.6,-12.6 L0.8,-12.8 C0.6,-14.6 1,-16.2 2.8,-17.4 Z"), angle=80, pitch=0.8)
    d.line(p("M-4,-8.2 L13,-9.4"), w=1.8)
    d.line(p("M1.8,-11.6 L5.6,-9 M0.6,-11 L0.4,-8.4"), w=1.1)
    # The pothole in the dry river bed.
    pool = "M38,93 C38,87 50,85 62,86 C74,87 80,89 79,93 Z"
    d.shape(pool, w=1.1)
    d.line("M44,89 l10,0 M58,88.4 l12,0 M48,91.2 l14,0", w=0.6, halo=False)
    # Boyd turned to face him, near enough to touch, and Billy watering the horse at the tank.
    figure(d, 42, 88, 22, flip=True, hat=False, coat=False)
    horse(d, 76, 89, 0.3, flip=True, graze=1.1)
    figure(d, 91, 89, 24, flip=True)
    return d


# 2. Billy and his father riding south at daybreak, the traps in the willow basket (1-03) ---------------
def to_the_peloncillos() -> Drawing:
    d = Drawing("to-the-peloncillos")
    # Black Point catching the sun above them, new snow on its top, the valley floor still in shadow.
    peak = "M2,58 C14,50 24,40 34,26 L40,18 L46,22 L52,16 C60,26 70,38 82,46 C88,50 92,54 94,56 Z"
    d.shape(peak, w=1.4)
    d.hatch("M2,58 C14,50 22,44 28,40 C34,42 38,36 44,38 C48,34 54,38 60,34 C66,40 74,42 82,46 C88,50 92,54 94,56 "
            "Z", angle=60, pitch=2.0)
    d.line("M36,28 l3,3 M44,25 l2,4 M53,22 l-2,4 M58,28 l-3,3", w=0.6, halo=False)

    # The father ahead with the packbasket on his back, its foot riding on the cantle; the boy behind him.
    def basket(t):
        b = t("M29,17 L43,17 L43.6,39 L32,39 Z")
        d.shape(b, w=1.2)
        d.hatch(b, angle=0, pitch=1.2)
        d.line(t("M33,17 L34,39 M37,17 L37.6,39"), w=0.6, halo=False)
        d.line(t("M43,20 C46,21 48,23 49,27"), w=0.9, halo=False)
    rider(d, 64, 88, 0.52, extra=basket)
    rider(d, 20, 86, 0.36)
    d.ground(2, 94, 90, ticks=7, seed=501)
    return d


# 3. Billy's father on the calfhide, truing the trap against the morning sky (1-03) ---------------------
def making_the_set() -> Drawing:
    d = Drawing("making-the-set")
    # The gap of the mountain the wolf had crossed, and the sun behind him.
    d.line("M2,70 C8,66 14,62 20,64 C26,70 32,74 38,74 M64,72 C70,66 78,60 86,60 C90,60 92,62 94,64", w=1.0)
    d.hatch("M64,72 C70,66 78,60 86,60 C90,60 92,62 94,64 L94,70 C86,68 76,70 66,74 Z", angle=60, pitch=2.0, w=0.6)
    d.shape(circle(86, 16, 4), w=1.0)
    d.line("M86,8 l0,-3 M93,11 l2.4,-2 M94.4,18 l2,0.4 M79,11 l-2.4,-2 M80,22 l-2.4,2", w=0.7, halo=False)
    # The calfhide thrown down hair side down, and the packbasket set by it.
    hide = "M6,92 C8,84 20,80 32,82 C46,80 62,80 72,82 C80,82 86,86 84,92 Z"
    d.shape(hide, w=1.3)
    d.line("M10,90 l-2,1 M6,92 l-2,-1 M84,90 l2,1 M86,86 l2,-1 M72,82 l1,-2 M32,82 l-1,-2", w=0.6, halo=False)
    bk = "M72,86 L71,64 L87,64 L86,86 Z"
    d.shape(bk, w=1.3)
    d.hatch(bk, angle=0, pitch=1.6)
    d.line("M75,64 L75.4,86 M79,64 L79,86 M83,64 L82.6,86", w=0.6, halo=False)
    # The father crouched on the hide with the sun at his back, the trap held up at eye level against the sky,
    # its springs clamped down and the jaws fallen open.
    p = crouch(d, 54, 88, 52, flip=True)
    d.line(p("M1.6,-12 L5.6,-13.2 L8.8,-15 M2.6,-11 L6.4,-12 L9,-13.8"), w=1.2)
    d.shape(ellipse(30, 53, 5, 4), w=1.8, fill=False)
    d.shape(ellipse(30, 53, 2, 1.5), w=0.9)
    d.shape("M25,52 C20,51 12,51.4 6,53 C12,54.6 20,55 25,54 Z", w=1.1)
    d.shape("M35,52 C38,51 40,51 41,51.4 L41,54.6 C40,55 38,55 35,54 Z", w=1.1)
    return d


# 4. The she-wolf coming up through the San Luis Pass, the Animas beyond (1-01) -------------------------
def san_luis_gap() -> Drawing:
    d = Drawing("san-luis-gap")
    # The Animas range far off through the gap.
    far = "M14,46 L22,40 L28,43 L36,34 L44,40 L52,32 L60,38 L68,35 L80,44"
    d.line(far, w=0.9)
    d.hatch(far + " L80,50 L14,50 Z", angle=70, pitch=2.4, w=0.5)
    # The slopes of the pass on either side, falling to the saddle she crosses.
    pass_ = "M-2,96 L-2,22 C10,24 18,40 22,56 C24,64 26,70 30,73 L68,73 C72,70 74,62 76,54 C80,36 88,22 98,20 L98,96 Z"
    d.shape(pass_)
    d.hatch("M8,24 C16,34 20,46 22,56 C24,64 26,70 30,73 L24,73 C20,66 16,56 13,44 C11,36 8,30 4,26 Z", angle=60,
            pitch=2.0)
    d.line("M60,80 l10,-6 M72,86 l12,-10 M10,70 l8,4 M14,84 l12,2", w=0.6, halo=False)
    wolf(d, 0.42, 28, 40, w=1.4)
    return d


# 5. The she-wolf howling from a rock over the snowy valley before sunrise (1-04) -----------------------
def howl_at_dawn() -> Drawing:
    d = Drawing("howl-at-dawn")
    d.dots([(70, 8), (84, 14), (90, 4), (60, 16)], r=0.6)
    # The valley floor white with snow, the far side of the basin, and the light coming behind it.
    d.line("M40,52 C54,48 70,46 94,48", w=0.9)
    d.line("M60,42 l20,0 M66,38 l16,0 M72,34 l12,0", w=0.6, halo=False)
    d.line("M44,64 C60,62 78,62 94,63 M50,76 l14,0 M72,72 l16,0", w=0.6, halo=False)
    # The low promontory, and her on it, muzzle raised.
    rock = "M-2,96 L-2,64 C4,60 14,58 26,58 C38,58 46,62 50,68 C54,74 56,84 58,96 Z"
    d.shape(rock)
    d.edge_shade(rock, dx=-4, dy=-4, cross=True)
    d.line("M10,66 C16,64 22,66 26,70 M34,72 l6,8", w=0.8, halo=False)
    howling(d, 28, 59, 1.0)
    return d


# 6. Billy crouched over the she-wolf's prints in the snow below the pass (1-04) ------------------------
def tracks_in_the_pass() -> Drawing:
    d = Drawing("tracks-in-the-pass")
    # The dark mountain woods.
    for x, base, h, seed in ((8, 52, 40, 503), (20, 46, 30, 504), (88, 50, 42, 505), (76, 44, 28, 506)):
        pine(d, x, base, h, seed=seed)
    d.line("M2,54 C24,50 60,50 94,52", w=0.9)
    # Bird standing where the reins were dropped.
    horse(d, 22, 72, 0.3)
    d.line("M33.4,60 C34,66 34,70 33,72", w=0.6, halo=False)
    # Billy squatting in the snow, the brim of his hat thumbed back.
    p = crouch(d, 48, 88, 42)
    d.line(p("M1.6,-12 L5.2,-9 L8,-4.4"), w=1.1)
    # Her prints going down the trail before him: the broad forefoot and the narrow hind.
    prints = [(66, 87, 1.5), (78, 81, 1.3), (70, 74, 1.1), (82, 68, 0.95), (74, 63, 0.8), (84, 58, 0.65)]
    for i, (x, y, s) in enumerate(prints):
        rx = 1.7 * s if i % 2 == 0 else 1.3 * s
        d.shape(ellipse(x, y, rx, 1.3 * s), w=0.9)
        d.hatch(ellipse(x, y, rx, 1.3 * s), angle=45, pitch=0.8)
        d.dots([(x - 1.6 * s, y - 2.6 * s), (x - 0.6 * s, y - 3.4 * s), (x + 0.6 * s, y - 3.4 * s),
                (x + 1.6 * s, y - 2.6 * s)], r=0.55 * s + 0.15)
    d.line("M4,90 C20,88 40,90 60,89 C72,88 84,90 94,89", w=0.8)
    return d


# 7. The cold fire with the trap buried in it, and Billy's warning scratched in the sand (1-08) ---------
def trap_in_the_fire() -> Drawing:
    d = Drawing("trap-in-the-fire")
    # Billy riding off home across the pasture in the twilight, turned to look back.
    d.dots([(14, 8), (30, 14), (48, 6), (66, 12), (86, 8)], r=0.6)
    d.line("M2,40 C30,38 60,38 94,37", w=0.8)
    rider(d, 76, 40, 0.18, flip=True)
    # The cold fire, ash drifted back over the set: charred sticks, bones and rinds of skin.
    ash = "M14,62 C18,54 34,52 48,52 C62,52 78,54 82,62 C66,66 30,66 14,62 Z"
    d.shape(ash, w=1.1)
    d.dots([(24, 60), (32, 57), (40, 61), (58, 56), (66, 61), (72, 58), (48, 63)], r=0.5)
    for x0, y0, x1, y1 in ((6, 52, 44, 59), (90, 50, 52, 59), (30, 70, 46, 60), (70, 70, 52, 60)):
        n = math.hypot(x1 - x0, y1 - y0)
        ox, oy = -(y1 - y0) / n * 1.8, (x1 - x0) / n * 1.8
        log = poly((x0 + ox, y0 + oy), (x1 + ox, y1 + oy), (x1 - ox, y1 - oy), (x0 - ox, y0 - oy))
        d.shape(log, w=1.1)
        mx, my = x0 + (x1 - x0) * 0.55, y0 + (y1 - y0) * 0.55
        d.hatch(poly((mx + ox, my + oy), (x1 + ox, y1 + oy), (x1 - ox, y1 - oy), (mx - ox, my - oy)), angle=0,
                pitch=0.9, cross=True)
    d.line("M22,68 L30,66.6 M64,66 L72,67.4", w=1.2)
    d.dots([(21.6, 67.4), (22.4, 69), (72.4, 66.6), (72.6, 68.4)], r=0.9)
    # The smoothed sand before it, the letters cut deep but too small to read, and the stick flung aside.
    for y, x0, x1 in ((80, 20, 74), (89, 16, 62)):
        pts, x, k = [], x0, 0
        while x < x1:
            tall = k % 3 == 1
            pts.append(f"M{x:.1f},{y:.1f} c0.6,{-5 if tall else -2.6} 2.2,{-5 if tall else -2.6} 1.6,0 "
                       f"c-0.4,1.2 1.2,1.4 2,0")
            x += 3.8 if k % 5 != 4 else 7
            k += 1
        d.line(" ".join(pts), w=1.0, halo=False)
    d.line("M80,88 L92,80", w=1.4)
    return d


# 8. Billy giving the gagged wolf water from his canteen by the road (1-08) -----------------------------
def water_from_the_canteen() -> Drawing:
    d = Drawing("water-from-the-canteen")
    # The road, the horse standing in it with the reins down.
    d.line("M2,50 C30,48 60,48 94,47", w=0.9)
    horse(d, 74, 52, 0.36, flip=True)
    d.line("M61,39.6 C59,44 59,48 60,52", w=0.6, halo=False)
    # Billy astride the wolf where he has forced her down in the grass at the roadside, leaning over her head,
    # the canteen tipped to the side of her mouth along the stick that gags her.
    d.line("M60,89 L52,89 L50,80", w=1.5)
    torso = "M46,81 C45,75 42,69 40,65 L48,63 C50,69 53,75 54,81 Z"
    d.shape(torso, w=1.4)
    d.edge_shade(torso, dx=1.4, dy=-1.4)
    d.shape(round_(43, 60, 3), w=1.1)
    hat = "M37,58.4 L49,58.4 L46.4,57.4 C46.4,53.4 39.8,53.4 39.8,57.4 Z"
    d.shape(hat, w=1.0)
    d.hatch(hat, angle=0, pitch=0.9)
    lie = lambda x, y: (x, 50 + (y - 50) * 0.35 if y > 50 else y + (6 if x > 70 else 3))  # noqa: E731
    wolf(d, 0.56, 20, 56, flip=True, bend=lie, w=1.5)
    d.line("M19,79 L31,76.6", w=1.4)
    d.line("M50,80 L44,89 L57,90", w=1.6)
    d.line("M42,67 L34,70 L30,72 M45,68 L38,76 L31,77", w=1.2)
    d.shape(circle(28.4, 69.4, 3.4), w=1.2)
    d.line("M26.6,72 l-2.2,2", w=1.4)
    d.line("M23.8,75.6 l-0.2,1.6 M22.4,75.4 l-0.4,1.4", w=0.6, halo=False)
    grass(d, [(8, 92), (62, 92), (78, 92), (90, 92)], h=4)
    return d


# 9. Billy stopped at Robertson's crossfence, the wolf limping behind, cloud shadows on the grass (1-08) ----
def robertsons_crossfence() -> Drawing:
    d = Drawing("robertsons-crossfence")
    # Clouds going over, and their shadows running on the plain below them.
    for cx, cy, rx, ry, seed in ((24, 14, 14, 5, 507), (70, 10, 16, 5, 508)):
        cloud = blob(cx, cy, rx, ry, 9, seed=seed, depth=0.3)
        d.shape(cloud, w=1.0)
        d.edge_shade(cloud, dx=0, dy=-2.4)
    d.line("M2,40 C14,36 22,36 30,38 C40,34 52,34 60,37 L94,36", w=0.8)
    for x, y, rx in ((26, 46, 14), (74, 44, 16)):
        d.hatch(ellipse(x, y, rx, 2.4), angle=0, pitch=1.2)
    # The crossfence corner: one fence coming down towards us, the other running off east.
    posts = [(6, 92, 24), (20, 80, 18), (31, 70, 13), (39, 63, 9), (45, 58, 6)]
    d.line(" ".join(f"M{x},{y} l0,{-h}" for x, y, h in posts), w=1.6)
    d.line("M6,72 L45,54 M6,80 L45,56 M6,86 L45,57.4", w=0.6, halo=False)
    d.line("M45,58 L94,56 M45,52.8 L94,51 M45,55.4 L94,53.4", w=0.6, halo=False)
    d.line(" ".join(f"M{x},{56.6 - (x - 45) * 0.03:.1f} l0,-5" for x in (58, 71, 84)), w=1.2)
    # Billy sitting the horse a long time, and the wolf come up at the rope's end behind.
    rider(d, 52, 88, 0.42, flip=True)
    wolf(d, 0.2, 70, 72, flip=True, w=1.1)
    d.line("M46,66 C60,74 70,82 76,82", w=0.8)
    # The yellow grass leaning in the wind.
    d.line(" ".join(f"M{x},{y} l2.4,-4" for x, y in ((14, 92), (30, 90), (40, 93), (86, 92), (92, 89), (52, 92))),
           w=0.8)
    return d


# 10. The ranch hounds on Billy and the wolf at the last fence (1-08) -----------------------------------
def three_hounds() -> Drawing:
    d = Drawing("three-hounds")
    # The ranch house up the road, where the howl came from.
    d.shape("M72,35 L72,27 L80,21 L88,27 L88,35 Z", w=1.0)
    d.line("M2,36 C30,35 60,34 94,34", w=0.8)
    # The three hounds come on low and fast round them, two with broken chain hanging from the collar.
    hound(d, 0.22, 22, 32, collar=False)
    g = hound(d, 0.36, -6, 50)
    x, y = g(70, 52)
    chain(d, x, y, x - 10, y + 14, 5)
    # Billy in the road, the rifle swung back to strike, and the wolf hard against his leg, her hair on end.
    p = figure(d, 50, 90, 40, flip=True)
    d.line(p("M-2,-17 L-6,-21 M2,-17 L-4,-22"), w=1.2)
    d.line(p("M-13,-29 L4,-17"), w=1.8)
    wolf(d, 0.3, 30, 66, flip=True, w=1.3)
    d.hatch("M38,78 C44,74 54,74 58,76 L58,82 L38,84 Z", angle=45, pitch=1.2)
    d.line("M44,76 l-1,-3 M48,75.4 l0,-3 M52,75.6 l1,-3 M56,76 l1.4,-2.6", w=0.7, halo=False)
    g = hound(d, 0.34, 64, 60, flip=True)
    x, y = g(70, 52)
    chain(d, x, y, x + 10, y + 14, 5)
    d.ground(2, 94, 90, ticks=7, seed=509)
    return d


SUBJECTS = {
    "indian-at-the-tank": indian_at_the_tank,
    "to-the-peloncillos": to_the_peloncillos,
    "making-the-set": making_the_set,
    "san-luis-gap": san_luis_gap,
    "howl-at-dawn": howl_at_dawn,
    "tracks-in-the-pass": tracks_in_the_pass,
    "trap-in-the-fire": trap_in_the_fire,
    "water-from-the-canteen": water_from_the_canteen,
    "robertsons-crossfence": robertsons_crossfence,
    "three-hounds": three_hounds,
}
