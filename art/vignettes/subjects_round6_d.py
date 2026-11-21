"""Vignettes of the sixth round, group d: five scenes that replace lone riders and repeats with the book's people
and its ruins, from the rancho on the Cajón Bonito (1-09) to the old woman at prayer in San Buenaventura (4-06).
Loaded by art/vignettes/make_vignettes.py.

Each is checked against the passage that shows it and drawn only from what the text gives. The riders and horses
are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and IV helpers, the mud houses
after Russell Lee's FSA photograph of an adobe at Peñasco (public domain) as in round 5. Everything else, the
people posed by hand among them, is drawn from the book. Light from the north-west, as everywhere: shade on each
shape's south-east side.
"""

import math

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly
from art.vignettes.subjects_parts_3_4 import blob, place, rider
from art.vignettes.subjects_round3 import fire, horse
from art.vignettes.subjects_round5_d import sitter
from art.vignettes.subjects_round5_e import hat, mud_house, person


def ruin(d: Drawing, x0: float, x1: float, base: float, top: float, door: float, seed: int):
    """An adobe fallen into ruin: the wall's top broken down in steps and gaps, a viga end or two, the bricks
    showing where the plaster has gone, and a dark doorway."""
    n = 7
    pts = [(x0, base), (x0, top + 3)]
    for i in range(1, n):
        x = x0 + (x1 - x0) * i / n
        drop = ((seed * 7 + i * 5) % 9) * 0.9
        pts += [(x - 1.2, top + drop), (x + 1.2, top + drop + (2.4 if i % 2 else -1.0))]
    pts += [(x1, top + 6 + seed % 3), (x1, base)]
    wall = poly(*pts)
    d.shape(wall)
    d.edge_shade(wall, dx=-3, dy=-1)
    # Bare adobe bricks where the plaster has fallen.
    bx, by = x0 + 3 + seed % 4, top + 8
    d.line(f"M{bx},{by} l6,0 M{bx + 2},{by + 2.6} l6,0 M{bx},{by + 5.2} l6,0 M{bx + 3},{by} l0,2.6 "
           f"M{bx + 5},{by + 2.6} l0,2.6", w=0.6, halo=False)
    d.line(f"M{x0 + 2},{top + 5} l-3.4,0.4", w=1.3)
    dh = (base - top) * 0.62
    dr = poly((door, base), (door, base - dh), (door + dh * 0.5, base - dh), (door + dh * 0.5, base))
    d.shape(dr, w=1.2)
    d.hatch(dr, angle=45, pitch=1.2, cross=True)
    return dr


def ocotillo(d: Drawing, x: float, base: float, h: float):
    """An ocotillo: a fan of long thin wands from one root, spined."""
    wands = [(-0.34, 0.9), (-0.16, 1.0), (0.02, 1.05), (0.18, 0.96), (0.34, 0.86)]
    d.line(" ".join(f"M{x},{base} Q{x + h * a * 0.4:.1f},{base - h * n * 0.5:.1f} {x + h * a:.1f},{base - h * n:.1f}"
                    for a, n in wands), w=0.9)
    d.dots([(x + h * a * f, base - h * n * f) for a, n in wands for f in (0.45, 0.7)], r=0.5)


def standing(d: Drawing, x: float, y: float, h: float, flip: bool = False, ragged: bool = False,
             skirt: bool = False):
    """A person standing facing out, feet at (x, y), h tall (24 local units), bare-headed: a man in shirt and
    trousers, torn at the hem and sleeves if `ragged`, or a woman in a long skirt and shawl."""
    k = h / 24

    def p(path: str) -> str:
        return place(path, x, y, k, flip)
    if skirt:
        body = p("M-2.8,-18 C-2,-19.4 2,-19.4 2.8,-18 L5,-0.4 L-5,-0.4 Z")
        d.shape(body, w=1.1)
        d.hatch(p("M-2.8,-18 C-2,-19.4 2,-19.4 2.8,-18 L3.8,-11 L-3.8,-11 Z"), angle=60, pitch=0.9)
    else:
        d.line(p("M-1.6,-9 L-2.2,0 M1.6,-9 L2.2,0"), w=1.3)
        hem = "L3.4,-8 L2.2,-9.6 L1,-7.8 L-0.4,-9.4 L-1.6,-7.6 L-2.8,-9.2 L-3.4,-8" if ragged else "L3,-9 L-3,-9"
        body = p(f"M-2.8,-17.6 C-2,-19 2,-19 2.8,-17.6 {hem} Z")
        d.shape(body, w=1.1)
        d.line(p("M-2.8,-16.6 L-3.8,-9.6 M2.8,-16.6 L3.8,-9.6"), w=1.0)
        if ragged:
            d.line(p("M-0.6,-17 L0.6,-12.6 L-0.4,-11"), w=0.6, halo=False)
    d.shape(circle(x, y - 21.2 * k, 2.3 * k), w=1.0)


# 1. The ruined rancho on the Cajón Bonito: three crumbling adobes, the man in rags at a door, no smoke (1-09) --
def ruined_rancho() -> Drawing:
    d = Drawing("ruined-rancho")
    # The mountains he is bound for, and the low hills.
    ridge = "M2,30 L12,22 L20,26 L32,16 L42,24 L52,20 L62,26 L74,18 L86,24 L94,22"
    d.line(ridge, w=1.0)
    d.hatch(ridge + " L94,32 L2,36 Z", angle=70, pitch=2.6, w=0.6)
    d.line("M2,46 C20,42 40,44 60,42 C76,41 86,43 94,42", w=0.8)
    # Three crumbling adobe houses along the trail, the middle one nearest, its roof gone.
    ruin(d, 4, 30, 66, 46, door=18, seed=1)
    ruin(d, 66, 92, 64, 46, door=72, seed=2)
    ruin(d, 26, 70, 80, 50, door=36, seed=3)
    # The man in rags standing at the doorway, half naked on a cold day.
    standing(d, 54, 84, 30, ragged=True)
    # Sparse grass and ocotillo.
    ocotillo(d, 84, 90, 26)
    grass(d, [(24, 88), (58, 90), (70, 86)], h=3.4)
    d.ground(2, 94, 91, ticks=6, seed=961)
    return d


# 2. Boyd staring into the fire in the stone arroyo below the Dos Cabezas (2-07) --------------------------------
def boyd_by_the_fire() -> Drawing:
    d = Drawing("boyd-by-the-fire")
    # The night ridge to the north, and the stony banks of the shallow arroyo.
    ridge = "M2,34 L14,26 L24,30 L36,22 L50,28 L62,24 L76,30 L94,26"
    d.line(ridge, w=1.0)
    d.hatch("M2,2 L94,2 L94,26 L76,30 L62,24 L50,28 L36,22 L24,30 L14,26 L2,34 Z", angle=0, pitch=2.2, w=0.6)
    d.dots([(10, 8), (30, 14), (46, 6), (70, 12), (88, 8)], r=0.7)
    for i, (cx, cy, rx, ry) in enumerate(((8, 56, 8, 5), (22, 52, 7, 4.4), (78, 54, 8, 5), (90, 60, 6, 4),
                                           (64, 50, 5, 3.4), (4, 66, 5, 3.6))):
        rock = blob(cx, cy, rx, ry, 7, seed=962 + i, depth=0.2)
        d.shape(rock, w=1.2)
        d.edge_shade(rock, dx=-1.6, dy=-1.6)
    d.line("M2,62 C20,60 34,58 50,58 C66,58 80,62 94,66", w=0.8)
    # The fire.
    fire(d, 60, 84, 1.0)
    p = place
    # Boyd sitting with his knees drawn up, arms round them, hatless, his pale hair white in the firelight.
    k = 1.25

    def b(path: str) -> str:
        return p(path, 34, 86, k)
    torso = b("M-6,-1 C-7,-6 -6,-12 -3.6,-15 L0.6,-15 C1.4,-11 1,-6 0,-1 Z")
    d.shape(torso, w=1.3)
    d.edge_shade(torso, dx=-1.2, dy=-1.2)
    d.line(b("M-1,-2 L7,-10 L9,0 L12,0"), w=2.2)
    d.line(b("M-1,-13 L4,-9.6 L7,-9.4"), w=1.4)
    d.shape(circle(34 + 0.6 * k, 86 - 18.6 * k, 2.9 * k), w=1.1)
    d.line(b("M-2,-20.4 C-1,-22.4 2.6,-22.4 3.4,-20 M-2.2,-19 C-3,-17 -2.6,-15.6 -1.6,-15.2"), w=1.0, halo=False)
    d.dots([(34 + 3.6 * k, 86 - 18.4 * k)], r=0.5)
    # Billy across the fire, hatted, watching him.
    sitter(d, 82, 88, 1.0, flip=True)
    d.ground(2, 94, 90, ticks=6, seed=968)
    return d


# 3. The thin rider passing back north through the mud hamlets of the mesa, watched from the doorways (3-14) ---
def mesa_hamlets() -> Drawing:
    d = Drawing("mesa-hamlets")
    # The cold high plain, a far line of mountains.
    d.line("M2,34 L12,30 L22,32 L34,27 L46,31 L58,28 L70,32 L82,28 L94,31", w=0.9)
    d.line("M2,38 C30,37 60,37 94,36", w=0.7, halo=False)
    # The row of mud houses along the road, the poblanos in their doorways.
    mud_house(d, 2, 44, 72, 42, door=8, seed=0)
    mud_house(d, 52, 94, 70, 44, door=76, seed=1)
    standing(d, 12.4, 72, 20, skirt=True)
    standing(d, 30, 74, 19)
    standing(d, 81, 70, 19)
    # Billy riding back north past them, alone, thin and pale with dust.
    rider(d, 52, 92, 0.48, flip=True)
    d.dots([(14, 90), (26, 92), (64, 92), (80, 90), (90, 93)], r=0.5)
    d.ground(2, 94, 92, ticks=6, seed=969)
    return d


# 4. The bandolero's work at dawn: the bedroll cut open on the track, Billy holding his hat to Niño's chest, the
#    riders sitting their horses before the grove (4-06) ---------------------------------------------------------
def the_bandolero() -> Drawing:
    d = Drawing("the-bandolero")
    # The grey dawn coming up behind the grove of trees, the river flat beyond.
    d.line(" ".join(f"M{48 + 10 * math.cos(math.radians(a)):.1f},{30 - 10 * math.sin(math.radians(a)):.1f} "
                    f"l{4 * math.cos(math.radians(a)):.1f},{-4 * math.sin(math.radians(a)):.1f}"
                    for a in (20, 50, 80, 110, 140, 160)), w=0.8)
    d.line("M40,30 C40,22 56,22 56,30", w=1.0)
    for i, (cx, cy, rx, ry) in enumerate(((14, 30, 12, 8), (82, 28, 13, 9))):
        crown = blob(cx, cy, rx, ry, 9, seed=970 + i, depth=0.25)
        d.shape(crown, w=1.3)
        d.hatch(crown, angle=60, pitch=1.6)
    d.line("M2,38 C30,36 64,36 94,37", w=0.9)
    # The riders sitting their horses on the track, dark against the light.
    for x, y in ((62, 50), (76, 51), (90, 50)):
        rider(d, x, y, 0.18, flip=True, hat="low")
    # Niño, the knife wound in his chest, and Billy pressing his hat to it.
    horse(d, 66, 82, 0.56, flip=True)
    d.line("M45,68 L44.6,77 M47,69 L47.4,79 M46,74 C45.6,80 46.4,82 46,84", w=1.0)
    person(d, (26, 50), (26.4, 54.6), (25, 72), back=[[(25, 72), (22, 80), (21, 90)], [(27, 56), (34, 62), (42, 62)]],
           front=[[(25, 72), (27, 81), (28, 90)], [(27, 57), (33, 65), (42, 66)]], r=3.0, width=7, w=1.9, dark=True)
    hat(d, 44, 64, s=1.2, tilt=-80)
    # The soogan cut open from end to end on the ground, Boyd's bones kicked about it.
    roll = "M2,92 C6,86 22,84 38,86 C40,88 38,92 34,94 C22,95 10,95 2,94 Z"
    d.shape(roll, w=1.2)
    d.edge_shade(roll, dx=-1.4, dy=-1.4)
    d.line("M6,90 C14,88 24,88 34,89", w=0.8, halo=False)
    d.shape(ellipse(12, 89, 3, 2.4), w=1.1)
    d.dots([(11, 88.6), (13.2, 88.6)], r=0.5)
    d.line("M18,90 L28,88.6 M22,91.6 L32,90.6 M44,93 L52,92", w=1.2)
    d.ground(40, 94, 92, ticks=4, seed=972)
    return d


# 5. The old woman of Mexico kneeling at prayer before the altar candles in the dark church (4-06) --------------
def old_woman_at_prayer() -> Drawing:
    d = Drawing("old-woman-at-prayer")
    # The dark church: the far wall in shadow, a little light round the candles on the altar.
    glow = [(56, 44, 9), (72, 44, 8)]
    wall = poly((2, 4), (94, 4), (94, 74), (2, 74))
    holes = " ".join(circle(x, y, r) for x, y, r in glow)
    d.hatch(f"{wall} {holes}", angle=10, pitch=2.2, cross=True)
    # The cross on the wall above the altar.
    cross = "M62.6,8 L65.4,8 L65.4,14 L70,14 L70,16.6 L65.4,16.6 L65.4,30 L62.6,30 L62.6,16.6 L58,16.6 L58,14 L62.6,14 Z"
    d.shape(cross, w=1.1)
    # The altar and its cloth, a few small candles burning.
    altar = poly((44, 50), (86, 50), (86, 74), (44, 74))
    d.shape(altar, w=1.4)
    d.edge_shade(altar, dx=-2.4, dy=-1.6)
    d.line("M44,56 L86,56 M48,56 L48,62 M82,56 L82,62", w=0.8, halo=False)
    for x in (52, 57, 62, 70, 75):
        stick = poly((x - 0.8, 50), (x - 0.8, 44), (x + 0.8, 44), (x + 0.8, 50))
        d.shape(stick, w=0.8)
        d.shape(f"M{x},{43.2} C{x - 1.4},{41.6} {x - 0.4},{39.6} {x},{38} C{x + 0.4},{39.6} {x + 1.4},{41.6} {x},{43.2} Z",
                w=0.7)
    # The loose tiles of the floor.
    d.line("M2,74 L94,74", w=1.1)
    d.line("M2,80 L94,80 M2,87 L94,87 M14,74 L6,94 M34,74 L30,94 M54,74 L54,94 M74,74 L78,94 M90,74 L94,84",
           w=0.6, halo=False)
    # The old woman kneeling, bent, her rebozo over her head and down her back, her hands at her beads.
    shawl = ("M30,46 C24,46 20,52 18,60 C16,70 12,80 10,90 L40,90 C40,84 38,80 36,76 C40,74 42,68 40,62 "
             "C40,54 36,46 30,46 Z")
    d.shape(shawl, w=1.6)
    d.hatch(shawl, angle=60, pitch=1.0, cross=True)
    d.line("M24,56 C22,66 20,78 18,88 M30,60 C28,70 28,80 28,88", w=1.0, color=PAPER, halo=False)
    face = "M35.4,52 C38.2,53 39.4,56 38.6,59.4 C37,59.6 35.6,58 35,55 Z"
    d.shape(face, w=0.9)
    d.hatch(face, angle=45, pitch=1.2)
    hands = "M40,66 C42,64.6 44.6,65 45,67 C44.4,69 42,69.4 40.4,68.6 Z"
    d.shape(hands, w=1.0)
    d.dots([(43.4, 70.6), (43, 72.6), (42.2, 74.4), (41, 75.8)], r=0.55)
    d.line("M40,90 L46,90", w=1.4)
    return d


SUBJECTS = {
    "ruined-rancho": ruined_rancho,
    "boyd-by-the-fire": boyd_by_the_fire,
    "mesa-hamlets": mesa_hamlets,
    "the-bandolero": the_bandolero,
    "old-woman-at-prayer": old_woman_at_prayer,
}
