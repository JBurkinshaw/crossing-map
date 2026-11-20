"""Vignettes of the fifth round: the end of the brothers' ride in Part III (J4), from the siesta in the
alameda at La Boquilla to the doctor's surgery at San Diego. Loaded by art/vignettes/make_vignettes.py.

Each is checked against the episode that first shows it and drawn after the period reference its seed `credit`
names: the riders and horses are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and
IV helpers, and the dog is the traced US Fish and Wildlife Service she-wolf outline, made smaller and bent, as for
the crippled dog. The mud houses follow Russell Lee's FSA photograph of an adobe at Peñasco (public domain).
Everything else, the people posed by hand, the Dodge coupe and the goat among them, is drawn from the book. Light
from the north-west, as everywhere: shade on each shape's south-east side.
"""

import math

from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, grass, poly, traced, warp
from art.vignettes.subjects_parts_1_2 import wolf
from art.vignettes.subjects_parts_3_4 import blob, place, rider
from art.vignettes.subjects_round3 import _horse, figure, horse

# The traced she-wolf (facing east) lying down flat, as in the wolf-mate drawing.
LIE = lambda x, y: (x, 50 + (y - 50) * 0.35 if y > 50 else y + (6 if x > 70 else 3))  # noqa: E731


def limb(pts) -> str:
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def person(d: Drawing, head, neck, hip, back=(), front=(), r: float = 2.4, width: float = 4.4, w: float = 1.6,
           dark: bool = False) -> str:
    """A person posed by its joints, for the poses `figure` cannot take (lying, sitting, bending): the far limbs,
    a tapered torso from neck to hip, the head, then the near limbs. Each limb is a list of points."""
    for pts in back:
        d.line(limb(pts), w=w)
    (nx, ny), (hx, hy) = neck, hip
    a = math.atan2(hy - ny, hx - nx)
    px, py = -math.sin(a), math.cos(a)
    s, h = width / 2, width * 0.42
    torso = poly((nx + px * s, ny + py * s), (hx + px * h, hy + py * h), (hx - px * h, hy - py * h),
                 (nx - px * s, ny - py * s))
    d.shape(torso, w=1.1)
    if dark:
        d.hatch(torso, angle=45, pitch=1.0)
    d.shape(circle(*head, r), w=1.0)
    for pts in front:
        d.line(limb(pts), w=w)
    return torso


def hat(d: Drawing, x: float, y: float, s: float = 1.0, tilt: float = 0.0):
    """A cowboy hat, its brim centred on (x, y), tilted by `tilt` degrees."""
    c, n = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))

    def f(u, v):
        return x + (u * c - v * n) * s, y + (u * n + v * c) * s
    d.shape(warp("M-6,0 C-3,-1.6 3,-1.6 6,0 C3,1.4 -3,1.4 -6,0 Z", f), w=1.0)
    crown = warp("M-3.2,-0.4 C-3.4,-3.2 -2.6,-4.6 0,-4.6 C2.6,-4.6 3.4,-3.2 3.2,-0.4 Z", f)
    d.shape(crown, w=1.0)
    d.hatch(warp("M-3.2,-0.4 L-3.3,-1.6 L3.3,-1.6 L3.2,-0.4 Z", f), angle=0, pitch=0.8)


def dog(d: Drawing, k: float, ox: float, oy: float, flip: bool = False, bend=None, w: float = 1.3):
    """The brothers' dog: the traced she-wolf made smaller, as for the crippled dog."""
    wolf(d, k, ox, oy, flip=flip, bend=bend, w=w)


def mud_house(d: Drawing, x0: float, x1: float, base: float, top: float, door: float, seed: int = 0):
    """A low flat-roofed adobe after Russell Lee's Peñasco photograph: rounded parapet, a viga or two through the
    wall, and a dark doorway."""
    wall = (f"M{x0},{base} L{x0},{top + 1.6} C{x0},{top} {x0 + 2},{top - 0.6} {x0 + 6},{top - 0.4} "
            f"L{x1 - 6},{top - 0.8} C{x1 - 2},{top - 0.8} {x1},{top} {x1},{top + 2} L{x1},{base} Z")
    d.shape(wall)
    d.edge_shade(wall, dx=-3, dy=-1)
    d.line(f"M{x0 + 6},{top + 3} l-3,0.4 M{x1 - 14},{top + 2.6} l-3,0.2", w=1.2)
    dw = (base - top) * 0.36
    dr = poly((door, base), (door, base - (base - top) * 0.66), (door + dw, base - (base - top) * 0.66),
              (door + dw, base))
    d.shape(dr, w=1.2)
    d.hatch(dr, angle=45, pitch=1.3, cross=True)
    d.line(f"M{x0 + 4},{top + 9 + seed} l3,0.4 M{x1 - 8},{base - 6} l2.6,0", w=0.6, halo=False)
    return dr


# 1. Boyd asleep in the alameda with the dog for a pillow (3-07) ----------------------------------------
def alameda_siesta() -> Drawing:
    d = Drawing("alameda-siesta")
    # The painted trees of the alameda: trunks whitewashed to a line, bare bark above, under round crowns.
    for i, (x, base, h) in enumerate(((14, 66, 58), (80, 64, 56))):
        paint = base - h * 0.22
        trunk = f"M{x - 2.8},{base} L{x - 2},{base - h * 0.5} L{x + 2},{base - h * 0.5} L{x + 2.8},{base} Z"
        d.shape(trunk, w=1.3)
        d.hatch(f"M{x - 3},{paint} L{x - 3},{base - h * 0.5} L{x + 3},{base - h * 0.5} L{x + 3},{paint} Z",
                angle=80, pitch=1.1)
        d.line(f"M{x - 2.6},{paint} L{x + 2.6},{paint}", w=1.0, halo=False)
        crown = blob(x, base - h * 0.72, 15, h * 0.26, 11, seed=720 + i, depth=0.25)
        d.shape(crown, w=1.5)
        d.edge_shade(crown, dx=-3, dy=-3)
    # The horses tied in the shade, the hackamore ropes trailing.
    horse(d, 48, 62, 0.3, saddle=False, graze=0.6)
    d.line("M60,52 C61,56 60,60 63,62", w=0.7)
    d.line("M4,64 C30,63 60,63 94,62", w=0.8)
    # The dog lying flat, and Boyd stretched in the dry grass with his head on it, his hat over his eyes.
    dog(d, 0.5, 2, 56, flip=True, bend=LIE)
    person(d, (40, 78.6), (45, 80.6), (66, 82),
           back=[[(66, 82), (78, 82.6), (90, 85)]],
           front=[[(66, 82), (76, 74), (84, 85)], [(46, 81), (54, 78), (60, 80)]], r=3.2, width=7, w=1.9)
    hat(d, 40, 76.4, s=1.45)
    grass(d, [(8, 89), (30, 90), (56, 89), (92, 89)], h=3.4)
    d.ground(2, 94, 90, ticks=6, seed=701)
    return d


# 2. The dry camp in the burned trees, Billy keeping watch with the shotgun (3-08) ----------------------
def snag(d: Drawing, x: float, base: float, h: float, seed: int):
    """A burned tree, dead, black and ragged: a charred trunk and a few broken limbs."""
    lean = (seed % 3 - 1) * 2
    trunk = f"M{x - 2.4},{base} L{x - 1 + lean},{base - h} L{x + 0.6 + lean},{base - h} L{x + 2.6},{base} Z"
    d.shape(trunk, w=1.2)
    d.hatch(trunk, angle=60, pitch=0.9, cross=True)
    arms = []
    for i, (t, side, ln) in enumerate(((0.45, -1, 0.42), (0.6, 1, 0.38), (0.78, -1, 0.3), (0.7, 1, 0.22))):
        if (seed + i) % 5 == 4:
            continue
        y = base - h * t
        xx = x + lean * t
        arms.append(f"M{xx:.1f},{y:.1f} L{xx + side * h * ln:.1f},{y - h * ln * 0.7:.1f} "
                    f"l{side * 1.6:.1f},{-2 - i:.1f}")
    d.line(" ".join(arms), w=1.6)


def quemada_dry_camp() -> Drawing:
    d = Drawing("quemada-dry-camp")
    # No moon, no wind: stars over the slight rise and its ruin of dead trees.
    d.dots([(6, 8), (22, 4), (38, 10), (54, 4), (66, 12), (80, 5), (92, 12), (46, 20), (10, 24), (90, 28)], r=0.6)
    d.line("M2,72 C24,62 54,58 94,64", w=1.0)
    for x, base, h, seed in ((10, 68, 40, 1), (28, 64, 54, 2), (60, 61, 46, 3), (84, 62, 40, 4)):
        snag(d, x, base, h, seed)
    # The horses staked on the slope.
    horse(d, 78, 82, 0.26, saddle=False, graze=0.6)
    d.line("M88,77 C90,79 92,81 93,82 M93,79 L93,84", w=0.8)
    # Billy sitting in the dark with the shotgun across his knees.
    person(d, (42, 56), (43, 61), (44, 77),
           back=[[(44, 77), (54, 69), (57, 84)]],
           front=[[(44, 77), (52, 68), (55, 84)], [(43.4, 62), (48, 71), (54, 68)]], r=3.4, width=7.2, w=2.0,
           dark=True)
    hat(d, 42, 52.6, s=1.4)
    d.line("M30,80 L66,62", w=1.8)
    d.line("M30,80 l-4,2.6", w=2.8)
    d.ground(2, 94, 89, ticks=6, seed=702)
    return d


# 3. A goat watching from a mud roof at San José as the brothers pass (3-08) ---------------------------
def goat(d: Drawing, x: float, y: float, k: float, flip: bool = False):
    """A goat standing, head up and turned to look: hooves on y, origin at its rump, facing west unless flipped."""
    def p(path):
        return place(path, x, y, k, flip)
    d.line(p("M-3,-8 L-3.4,0 M-6,-8 L-6.6,0 M-15,-9 L-15,0 M-18,-9 L-18.6,0"), w=1.3)
    body = p("M0,-12 C0,-16 -4,-17 -10,-17 C-14,-17 -16,-17.6 -18,-19 L-21,-26 C-22,-28 -25,-28 -26,-26 L-27,-23.6 "
             "C-26,-22.6 -24.6,-22.4 -23.4,-22.6 L-21.6,-16 C-21,-12 -20,-9 -17,-8.6 L-3,-8.4 C-1,-8.6 0,-10 0,-12 Z")
    d.shape(body, w=1.3)
    d.edge_shade(body, dx=1.6 if not flip else -1.6, dy=-1.8)
    d.line(p("M-20.4,-26.6 C-19,-30 -16,-31 -14,-29.6 M-22,-26 L-19,-24.4"), w=1.1)
    d.line(p("M-25.6,-23 L-25.4,-20 M0,-14 L1.6,-17"), w=1.0)
    d.dots([(x - (23.2 if not flip else -23.2) * k, y - 25 * k)], r=0.6)


def goat_on_the_roof() -> Drawing:
    d = Drawing("goat-on-the-roof")
    # The low grey mud hovels of San José along the rutted track, a woman peering from a doorway.
    mud_house(d, 4, 40, 64, 44, 10, seed=0)
    mud_house(d, 34, 92, 64, 38, 50, seed=2)
    d.shape(circle(53.6, 50.6, 2.2), w=0.9)
    d.line("M51.6,53 L51.6,58 M55.6,53 L55.6,58", w=0.8, halo=False)
    # The goat on the roof, looking down at them.
    goat(d, 80, 37.6, 0.9)
    # The brothers going by with their string of horses.
    rider(d, 34, 90, 0.3, flip=True, hat="cowboy")
    horse(d, 62, 90, 0.26, flip=True, saddle=False)
    d.line("M2,80 C30,78 60,78 94,79 M10,88 l10,0 M60,92 l12,0", w=0.8)
    d.ground(2, 94, 92, ticks=6, seed=703)
    return d


# 4. Niño carrying the brothers double, the five horsemen behind (3-08) ---------------------------------
def palmilla(d: Drawing, x: float, base: float, h: float):
    """A palmilla: a short shaggy trunk and a burst of stiff leaves."""
    d.line(f"M{x},{base} L{x + 0.4},{base - h * 0.55}", w=1.4)
    top = base - h * 0.55
    d.line(" ".join(f"M{x + 0.4},{top} l{h * 0.45 * math.cos(math.radians(a)):.1f},{-h * 0.45 * math.sin(math.radians(a)):.1f}"
                    for a in (10, 35, 60, 80, 100, 125, 150, 170)), w=0.8)


def the_chase() -> Drawing:
    d = Drawing("the-chase")
    # The blue sierras far off, and the open grass plain dotted with palmilla.
    ridge = "M2,30 L10,24 L18,28 L28,20 L38,26 L48,22 L58,28 L68,22 L80,27 L94,22"
    d.line(ridge, w=0.9)
    d.hatch(ridge + " L94,34 L2,34 Z", angle=70, pitch=2.8, w=0.6)
    d.line("M2,42 C30,41 60,41 94,40", w=0.7, halo=False)
    for x, b, h in ((8, 54, 12), (40, 46, 8)):
        palmilla(d, x, b, h)
    # The horsemen strung out behind in a thin line of dust, rifles held out at their sides.
    d.line("M60,48 C70,44 82,46 94,44 M64,50 C74,48 84,49 94,48", w=0.6, halo=False)
    for x in (66, 78, 90):
        rider(d, x, 50, 0.15, flip=True, hat="cowboy", reins=False, leg=False)
        d.line(f"M{x - 1},43.4 l-3.6,1", w=0.9, halo=False)

    # Niño at a run, legs flung out, Boyd slumped in the saddle and Billy up behind holding him on.
    k, ox, oy = 0.62, 44, 90

    def f(x, y):
        if y > 60:
            x += (y - 60) * (0.5 if x > 52 else -0.5)
        return ox - (x - 48) * k, oy + (y - 90) * k
    t = lambda p: warp(p, f)  # noqa: E731
    tr = traced("rider-annie-g")
    for p in tr["outline"]:
        d.shape(t(p), w=1.8)
        d.edge_shade(t(p), dx=2, dy=-2.4)
    for p in tr["tones"]["0.3"]:
        d.hatch(t(p), angle=135, pitch=2.0)
    d.line(t("M57,36 C66,40 78,46 87,49"), w=0.7, halo=False)
    person(d, f(40, 22), f(41, 27), f(41, 42), back=[[f(41, 42), f(45, 50), f(44, 60)]],
           front=[[f(42, 29), f(47, 33), f(52, 34)]], r=3.0 * k, width=8 * k, w=1.4)
    hat(d, *f(40, 19.6), s=1.1)
    # Dust kicked up behind.
    d.line("M74,86 c3,-3 6,-2 8,-5 M76,90 c4,-2 7,0 10,-3", w=0.8, halo=False)
    d.ground(2, 94, 91, ticks=6, seed=705)
    return d


# 5. Billy leading his father's horse afoot at dusk, white with salt, towards a far light (3-08) ---------
def salt_rimed_horse() -> Drawing:
    d = Drawing("salt-rimed-horse")
    # The darkening plain, the one light low in the north, and the paring of the old moon over the western
    # mountains.
    d.line("M2,50 C30,49 60,49 94,48", w=0.9)
    d.hatch("M2,50 C30,49 60,49 94,48 L94,92 L2,92 Z", angle=10, pitch=2.4, w=0.6)
    d.dots([(10, 47)], r=1.4)
    d.line("M10,42.4 l0,-3 M4.8,47 l-2.6,0 M15.2,47 l2.6,0", w=0.7, halo=False)
    d.line("M64,48 L72,40 L78,44 L86,36 L94,42", w=0.9)
    d.shape("M76,14 C80,22 88,20 90,12 C86,17 80,18 76,14 Z", w=1.0)
    d.dots([(30, 10), (46, 18), (58, 8), (8, 22), (66, 26)], r=0.5)
    # Niño, left unhatched so the salt rime shows him pale against the dusk, his head low with weariness.
    body, _ = _horse()
    k, ox, oy = 0.7, 60, 90

    def f(x, y):
        if x > 64:
            y += (x - 64) * 0.6
            x -= (x - 64) * 0.18
        return ox - (x - 48) * k, oy + (y - 90) * k
    d.shape(warp(body, f), w=1.8)
    d.shape(warp("M41,38.6 C42,34.6 44,35 45.4,37.6 C49,38.2 53,37.4 56.4,35.4 C57.6,36.6 57.8,38 57,39.6 "
                 "L55,45 L43,45 Z", f), w=1.0)
    d.dots([f(x, y) for x, y in ((30, 46), (24, 52), (36, 54), (20, 44), (44, 52), (62, 48), (70, 46), (30, 60),
                                  (14, 50), (50, 56), (66, 54), (40, 60), (56, 52), (76, 60))], r=0.55)
    # Billy walking at the horse's head, a hand on the cheekstrap.
    person(d, (18, 52), (18.6, 56.6), (20, 72),
           back=[[(20, 72), (16, 81), (13, 90)], [(19, 58), (23, 66), (28, 64)]],
           front=[[(20, 72), (23, 81), (25, 90)]], r=3.0, width=6.6, w=1.9, dark=True)
    hat(d, 18, 49, s=1.25)
    return d


# 6. The dog coming out of the chaparral, cut up and holding up a paw (3-09) ---------------------------
def dog_returns() -> Drawing:
    d = Drawing("dog-returns")
    # The chaparral at the roadside.
    for cx, cy, rx, ry, seed in ((10, 58, 10, 9, 1), (26, 62, 9, 7, 2)):
        bush = blob(cx, cy, rx, ry, 10, seed=710 + seed, depth=0.35)
        d.shape(bush, w=1.2)
        d.hatch(bush, angle=60, pitch=1.6)
    d.line("M2,88 C30,87 60,87 94,86", w=0.9)

    # The dog limping out of it, cut and bloody, a forepaw held up to his chest.
    def lame(x, y):
        if x > 60 and y > 60:
            y -= (y - 60) * 0.55
        return x, y
    dog(d, 0.52, 4, 46, bend=lame, w=1.5)
    d.line("M24,68 l3,3 M30,64 l2,4 M38,67 l3,2.4", w=0.9, halo=False)
    d.dots([(27.6, 72), (32.4, 69), (41.4, 70.4), (36, 80)], r=0.8)
    # Billy halted on the road, looking down at him.
    rider(d, 76, 88, 0.48, flip=True, hat="cowboy")
    d.ground(2, 94, 90, ticks=6, seed=706)
    return d


# 7. The girl at Billy's stirrup at Mata Ortiz, giving him a silver heart (3-09) ------------------------
def silver_heart_milagro() -> Drawing:
    d = Drawing("silver-heart-milagro")
    # The old woman standing in her door.
    mud_house(d, 2, 34, 88, 44, 8)
    p = figure(d, 15, 86, 28, hat=False)
    d.shape(p("M-3,-17.6 C-2,-19 2,-19 3,-17.6 L5,0 L-5,0 Z"), w=1.1)
    d.hatch(p("M-2.8,-22.6 C-2.8,-25.6 2.8,-25.6 2.8,-22.6 L3.2,-17 L-3.2,-17 Z"), angle=0, pitch=0.9)
    # Billy on the horse, reaching down.
    rider(d, 70, 90, 0.62, flip=True, hat="cowboy")
    d.line("M64,55 C66,56 67,58 66.6,60", w=1.4)
    # The girl at the stirrup, holding up the little silver heart to him.
    g = figure(d, 56, 90, 30, hat=False)
    d.shape(g("M-2.6,-17.6 C-2,-19 2,-19 2.6,-17.6 L5.4,-1 L-5.4,-1 Z"), w=1.2)
    d.hatch(g("M-2.4,-23 C-3.4,-21 -3.4,-18 -3.2,-15 L-1,-15 C-1.6,-18 -1.4,-21 -0.6,-23 Z"), angle=80, pitch=0.8)
    d.line(g("M1.8,-16.6 L4.4,-21 L5.4,-25.6"), w=1.3)
    heart = place("M0,-1.8 C-1.2,-4.2 -4.6,-4 -4.6,-1.2 C-4.6,1.4 -1.2,3.4 0,5.2 C1.2,3.4 4.6,1.4 4.6,-1.2 "
                  "C4.6,-4 1.2,-4.2 0,-1.8 Z", 63, 54, 1.0)
    d.shape(heart, w=1.2)
    d.line("M61.4,52.8 C61,52 61.4,51.2 62.2,51", w=0.6, halo=False)
    d.line("M67.6,49 l2,-2 M58.4,49.4 l-2,-2 M69,54 l2.4,-0.2", w=0.7, halo=False)
    d.ground(34, 94, 91, ticks=5, seed=707)
    return d


# 8. The doctor's old Dodge on the dark road, cattle eyes in the lights (3-10) --------------------------
def doctors_dodge() -> Drawing:
    d = Drawing("doctors-dodge")
    # The night everywhere but in the headlights' beam, where the road shows.
    beam = "M42,62 L-2,48 L-2,84 Z"
    d.hatch("M-2,-2 L98,-2 L98,98 L-2,98 Z " + beam, angle=30, pitch=2.0, w=0.7)
    d.line("M2,76 C14,74 28,70 42,68 M2,84 L40,72", w=0.8, halo=False)
    # The hot eyes of cattle in the bar ditches, floating up at the edge of the light.
    for x, y in ((6, 42), (20, 47), (8, 90), (24, 84)):
        for dx in (0, 3.6):
            d.shape(circle(x + dx, y, 1.3), w=0.7)
    # The opera coupe, facing west: long hood, the small closed cab, the rounded deck behind, the spare on its
    # tail, and the big lamps on the fenders.
    car = ("M42,72 L42,62 C42,60 44,59 46,59 L64,57.6 L68,49 C69,47.4 70,47 72,47 L80,47 C84,47 86,50 88,55 "
           "C91,57 93,61 93,66 L93,72 Z")
    d.shape(car)
    d.edge_shade(car, dx=0, dy=-3)
    win = "M69.4,56 L71.4,50 L79,50 L79,56 Z"
    d.shape(win, w=0.9)
    d.hatch(win, angle=45, pitch=1.1, cross=True)
    d.line("M68,58 L68,70 M48,62 L64,61 M50,64 l12,-0.6", w=0.7, halo=False)
    for x0, cx in ((44, 54), (76, 84)):
        d.shape(f"M{x0},74 C{x0},64 {x0 + 4},61 {cx},61 C{cx + 6},61 {cx + 10},66 {cx + 11},74 Z", w=1.3)
        d.shape(circle(cx, 76, 6), w=1.7)
        d.hatch(circle(cx, 76, 6), angle=60, pitch=1.3)
        d.shape(circle(cx, 76, 2), w=0.9)
    d.line("M64,74 L77,74", w=1.2)
    d.shape("M40,72 C39,66 40,62 42,60 L44,60 L44,72 Z", w=1.0)
    d.line("M41,64 l2.6,0 M40.6,67 l3,0 M40.6,70 l3,0", w=0.5, halo=False)
    d.shape(circle(45, 59.4, 2.6), w=1.2)
    d.ground(40, 96, 83, ticks=4, seed=708)
    return d


# 9. The doctor at work by the votive light, the flashlight in his teeth (3-10) -------------------------
def surgery_by_candle() -> Drawing:
    d = Drawing("surgery-by-candle")
    # The dark room; the flashlight's beam and the votive light's glow left clear.
    beam = "M46,36 L36,72 L56,72 Z"
    glow = circle(7, 58, 8)
    d.hatch("M-2,-2 L98,-2 L98,80 L-2,80 Z " + beam + " " + glow, angle=45, pitch=2.6, w=0.6)
    # The doctor bent over the wound in his dark suit and spectacles, the little flashlight gripped in his teeth.
    doctor = ("M58,18 C53,16 48,18 47,23 L46.4,28 C46.8,30.4 49,31.6 51.4,31.4 L56,34 C62,40 68,46 72,50 L72,88 "
              "L77,88 L78,62 L81,88 L86,88 L85.4,54 C85,46 83,40 79,36 C73,28 66,22 60,22 Z")
    d.shape(doctor, w=1.6)
    d.hatch("M56,34 C62,40 68,46 72,50 L72,88 L77,88 L78,62 L81,88 L86,88 L85.4,54 C85,46 83,40 79,36 "
            "C73,28 66,24 60,24 Z", angle=45, pitch=1.2)
    d.shape(circle(53, 22.6, 5.4), w=1.3)
    arm = "M58,28 L64,33 L54,62 L49,61 Z"
    d.shape(arm, w=1.3)
    d.hatch(arm, angle=-45, pitch=1.2)
    d.shape(circle(49.6, 22.4, 1.6), w=0.8, fill=False)
    d.line("M47.6,29 L45.4,35", w=2.6)
    d.line("M45.6,36 L38,70 M45.6,36 L54,70", w=0.5, halo=False)
    # The pallet on the floor and Boyd on it, Billy sitting at his head holding his hand.
    pallet = poly((12, 88), (12, 79), (96, 79), (96, 88))
    d.shape(pallet, w=1.5)
    d.line("M12,83.6 L96,83.6", w=0.6, halo=False)
    boyd = "M32,70 C42,67 54,68 62,70 C72,71 84,71 94,72 L94,79 L31,79 C29,77 29,72 32,70 Z"
    d.shape(boyd, w=1.6)
    d.edge_shade(boyd, dx=0, dy=-2.4)
    d.shape(circle(28, 73.4, 4), w=1.4)
    d.line("M36,70 L33,64 L28,61", w=2.0)
    person(d, (16, 44), (16.6, 49), (17.6, 67),
           back=[[(17.6, 67), (26, 67), (25, 86)]],
           front=[[(17.6, 67), (24, 70), (23, 88)], [(17, 51), (21, 58), (27, 61)]], r=3.6, width=7.4, w=2.2)
    hat(d, 16, 40.6, s=1.4)
    # The votive glass on the floor and its thin upright flame.
    d.shape(poly((3.6, 72), (3.6, 62), (9.6, 62), (9.6, 72)), w=1.2)
    d.shape("M6.6,60 C5,58 5.8,54 6.6,51 C7.4,54 8.2,58 6.6,60 Z", w=1.0)
    return d


SUBJECTS = {
    "alameda-siesta": alameda_siesta,
    "quemada-dry-camp": quemada_dry_camp,
    "goat-on-the-roof": goat_on_the_roof,
    "the-chase": the_chase,
    "salt-rimed-horse": salt_rimed_horse,
    "dog-returns": dog_returns,
    "silver-heart-milagro": silver_heart_milagro,
    "doctors-dodge": doctors_dodge,
    "surgery-by-candle": surgery_by_candle,
}
