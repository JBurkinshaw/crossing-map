"""Vignettes of the fifth round: Billy's ride home through the Sierra and back to Hidalgo County (J3, Part
II, 2-01 to 2-06), and the brothers' first days riding south together (J4, 2-07). Loaded by
art/vignettes/make_vignettes.py.

Each is checked against the passage that shows it and drawn only from what the text gives. The riders and horses
are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and IV helpers, the dog the
traced US Fish and Wildlife Service she-wolf made smaller, as for the dog at the gate. Everything else is drawn by
hand from the book. Light from the north-west, as everywhere: shade on each shape's south-east side.
"""

import math

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly, warp
from art.vignettes.subjects_parts_1_2 import wolf
from art.vignettes.subjects_parts_3_4 import blob, cottonwood, place, rider
from art.vignettes.subjects_round3 import chevrons, figure, fire, horse
from art.vignettes.subjects_round4 import round_, water


def woman(d: Drawing, x: float, y: float, h: float, flip: bool = False):
    """A woman standing, feet at (x, y), h tall: a long skirt to the ankles and dark hair, in the 24-unit figure."""
    k = h / 24

    def p(path: str) -> str:
        return place(path, x, y, k, flip)
    skirt = p("M-2.8,-17.6 C-2,-19 2,-19 2.8,-17.6 L3.4,-11 L5,-0.6 L-5,-0.6 L-3.4,-11 Z")
    d.shape(skirt, w=1.1)
    d.line(p("M-1.6,-0.6 L-1.8,0.4 M1.6,-0.6 L1.8,0.4"), w=1.0, halo=False)
    d.shape(p(circle(0, -21, 2.2)), w=1.0)
    hair = p("M-2.2,-21.6 C-2.4,-24 2.4,-24 2.2,-21.6 L2.6,-17.4 L1.6,-17.6 L1.4,-20 L-1.4,-20 L-1.6,-17.6 "
             "L-2.6,-17.4 Z")
    d.shape(hair, w=0.8)
    d.hatch(hair, angle=80, pitch=0.8)
    return p


def pillion(d: Drawing, t, x: float = -7):
    """A second rider (a boy, hatted) sitting behind the first on the same horse, in traced units."""
    body = f"M{37 + x},39 L{38 + x},28 C{39 + x},25.6 {44 + x},25.4 {46 + x},27.6 L{47 + x},39 Z"
    d.shape(t(body), w=1.2)
    d.edge_shade(t(body), dx=-1.4, dy=-1.6)
    d.shape(t(round_(41.6 + x, 22, 3)), w=1.1)
    d.shape(t(f"M{36 + x},19.6 C{39 + x},18.4 {45 + x},18.4 {48 + x},19.6 C{45 + x},20.8 {39 + x},20.8 {36 + x},19.6 Z"),
            w=1.0)
    d.shape(t(f"M{39 + x},19.4 C{39 + x},15.6 {40 + x},14.4 {42 + x},14.4 C{44 + x},14.4 {45 + x},15.6 {45 + x},19.4 Z"),
            w=1.0)
    d.line(t(f"M{41 + x},39 C{44 + x},43 {45 + x},47 {44 + x},55 L{47 + x},56"), w=1.0, halo=False)
    d.line(t(f"M{44 + x},30 C{47 + x},32 {50 + x},33 {52 + x},33"), w=1.0, halo=False)


def dog(d: Drawing, k: float, ox: float, oy: float, flip: bool = False, sit: bool = False):
    """The family dog: the traced she-wolf made smaller, trotting, or sitting with its haunches down."""
    if sit:
        def bend(x, y):
            if x < 44:
                y += (44 - x) * 0.55
                x = 44 - (44 - x) * 0.55
            return x, y
        wolf(d, k, ox, oy, flip=flip, bend=bend, w=1.2)
    else:
        wolf(d, k, ox, oy, flip=flip, w=1.2)


def standing_crane(d: Drawing, x: float, y: float, k: float, flip: bool = False, mirror: bool = False):
    """A sandhill crane standing, facing west: long legs, a grey body with a drooping bustle, the neck up, the red
    crown. Feet at (x, y). `mirror` draws its reflection in the water below, thin and unfilled."""
    s = -1 if flip else 1
    f = (lambda u, v: (x + s * u * k, y - v * k * 0.55)) if mirror else (lambda u, v: (x + s * u * k, y + v * k))
    legs = "M0,0 L0.6,-15 M3.6,0 L2.6,-15"
    body = "M-5,-22 C-4,-28 6,-29 11,-24 C14,-21 13,-16 9,-15 C4,-14 -2,-15 -4,-18 C-5,-19.4 -5,-21 -5,-22 Z"
    bustle = "M6,-17 C10,-18 14,-15 13,-11 C11,-13 9,-14 6,-15 Z"
    neck = "M-3,-25 C-5,-29 -3,-33 -4,-37"
    head = "M-6,-37.6 C-6,-40 -3,-40.6 -2.4,-38.6 C-2.2,-37 -3.4,-36.2 -4.6,-36.4 Z"
    bill = "M-5.6,-37.8 L-11,-36.2"
    if mirror:
        d.line(warp(legs + " " + neck + " " + bill, f), w=0.7, halo=False)
        d.shape(warp(body, f), w=0.7, fill=False)
        return
    d.line(warp(legs, f), w=1.1)
    d.shape(warp(body, f), w=1.3)
    d.hatch(warp(body, f), angle=30, pitch=1.4)
    d.shape(warp(bustle, f), w=1.0)
    d.line(warp(neck, f), w=1.6)
    d.shape(warp(head, f), w=1.0)
    d.hatch(warp(head, f), angle=0, pitch=0.7)
    d.line(warp(bill, f), w=1.1)


# 1. The old man holding Billy's saddle among the wickiups (2-01) ---------------------------------------
def old_man_at_the_saddle() -> Drawing:
    d = Drawing("old-man-at-the-saddle")
    # The brush wickiups of the ranchería behind.
    for x, y, s in ((10, 56, 1.1), (28, 52, 0.8), (90, 54, 0.7)):
        hut = place("M-9,0 C-9,-9 -4,-12 0,-12 C4,-12 9,-9 9,0 Z", x, y, s)
        d.shape(hut, w=1.2)
        d.hatch(hut, angle=75, pitch=1.5)
        d.shape(place("M-2,0 L-2,-5 C-2,-6.4 2,-6.4 2,-5 L2,0 Z", x, y, s), w=0.9)
    d.line("M2,57 C30,55 60,55 94,54", w=0.8)
    # The women who fed him, standing to watch.
    woman(d, 74, 70, 18)
    woman(d, 84, 72, 16)
    # Billy on his horse, the old man at its side with a hand on the saddle fore and aft, speaking up to him.
    rider(d, 34, 90, 0.6, hat="cowboy")
    p = figure(d, 41, 93, 30, flip=True, hat=False)
    hair = p("M-2.2,-21.6 C-2.4,-24.2 2.4,-24.2 2.2,-21.6 L2.6,-15.6 L1.4,-15.8 L1.6,-20 L-1.6,-20 Z")
    d.shape(hair, w=0.8)
    d.hatch(hair, angle=80, pitch=0.8)
    # The geometric figures worked on his clothes.
    d.line(p("M-3,-15 l1.5,1.4 l1.5,-1.4 l1.5,1.4 l1.5,-1.4 M-3.4,-11.6 l1.7,1.4 l1.7,-1.4 l1.7,1.4 l1.7,-1.4"),
           w=0.6, halo=False)
    d.line(p("M-2,-17 L-9,-27 M2,-17 L5,-26"), w=1.2)
    d.ground(2, 94, 93, ticks=6, seed=600)
    return d


# 2. Pictographs on the bluffs of the eastern escarpment, and one vulture (2-01) ------------------------
def rim_pictographs() -> Drawing:
    d = Drawing("rim-pictographs")
    # The plain far below to the east, and a range beyond it in the haze.
    d.line("M54,50 L62,44 L68,47 L76,40 L84,45 L94,42", w=0.8)
    d.line("M52,58 C66,57 80,57 94,56", w=0.6, halo=False)
    # A single vulture held high on the wind, wings in a shallow V.
    d.line("M60,22 C65,17 70,17 74,20.4 L77,21 L80,20.4 C84,17 89,17 94,22", w=1.6)
    d.shape("M74.6,20.6 C75.4,19.4 78.6,19.4 79.4,20.6 L78,24 L76,24 Z", w=1.0)
    d.hatch("M74.6,20.6 C75.4,19.4 78.6,19.4 79.4,20.6 L78,24 L76,24 Z", angle=0, pitch=0.7)
    # The bluff of grey rock, the juniper on its rim leaning in a wind long gone.
    face = "M2,92 L2,30 L12,26 L22,28 L34,24 L44,30 L50,40 L54,58 L58,72 L62,92 Z"
    d.shape(face)
    d.line("M2,48 C16,46 34,49 50,47 M2,70 C20,68 40,71 57,70", w=0.6, halo=False)
    d.hatch("M44,30 L50,40 L54,58 L58,72 L62,92 L54,92 L50,72 L46,52 L42,36 Z", angle=75, pitch=1.8)
    d.line("M32,25 C30,20 26,17 20,15 C16,14 12,14 8,12", w=1.6)
    for cx, cy, rx, sd in ((10, 11, 6, 610), (20, 12, 6, 611), (27, 17, 4.4, 612)):
        clump = blob(cx, cy, rx, 3, 9, seed=sd, depth=0.3)
        d.shape(clump, w=1.0)
        d.hatch(clump, angle=50, pitch=1.3)
    # The pictographs: men, a deer, a sun, a moon and a sign with no referent.
    men = []
    for x, y in ((10, 54), (17, 55)):
        men.append(f"M{x},{y} l0,7 M{x - 3},{y + 2} l3,1.6 l3,-1.6 M{x},{y + 7} l-2.4,4 M{x},{y + 7} l2.4,4")
    d.line(" ".join(men), w=1.1, halo=False)
    d.dots([(10, 52.6), (17, 53.6)], r=1.1)
    d.line("M26,60 C28,57.6 34,57.6 36,60 M27,60 l-1,4 M35,60 l1,4 M36,60 l2,-3 l1,-3 M38,57 l2,-1", w=1.1,
           halo=False)
    d.shape(circle(14, 38, 3.4), w=1.0)
    d.line(" ".join(f"M{14 + 4.6 * math.cos(a):.1f},{38 + 4.6 * math.sin(a):.1f} "
                    f"l{2.2 * math.cos(a):.1f},{2.2 * math.sin(a):.1f}"
                    for a in (i * math.pi / 4 for i in range(8))), w=0.8, halo=False)
    moon = "M32,34 C28,36 28,42 32,44 C30,41 30,37 32,34 Z"
    d.shape(moon, w=1.0)
    d.hatch(moon, angle=0, pitch=0.8)
    d.line("M40,44 C40,42 44,42 44,44 C44,47 38,47 38,44 C38,40 46,40 46,44", w=0.9, halo=False)
    d.line("M12,76 l4,-4 l4,4 l4,-4 l4,4 M34,78 l0,-6 M38,78 l0,-6 M42,78 l0,-6", w=0.9, halo=False)
    return d


# 3. Billy midstream in the ford, letting the bow go (2-01) ---------------------------------------------
def bow_in_the_ford() -> Drawing:
    d = Drawing("bow-in-the-ford")
    # The ruined mud town on the red plain beyond the river, its one smoke, and swallows over the water.
    town = "M54,40 L54,32 L60,32 L60,34 L66,34 L66,30 L74,30 L76,33 L82,33 L82,36 L90,36 L90,40 Z"
    d.shape(town, w=1.1)
    d.line("M62,40 l0,-3 l2,0 l0,3 M78,40 l0,-3 l2,0 l0,3", w=0.7, halo=False)
    d.line("M70,30 C68,25 72,22 70,17 C69,14 72,12 71,9", w=0.7, halo=False)
    d.line("M2,42 C30,41 60,41 94,40", w=0.8)
    chevrons(d, [(14, 24, 0.7), (24, 30, 0.6), (34, 22, 0.6), (40, 32, 0.5)])
    # Billy on the horse, halted in the stream, the water over its legs.
    rider(d, 36, 82, 0.52, hat="cowboy")
    for y in range(68, 84, 2):
        d.line(f"M8,{y} L82,{y}", w=1.6, color=PAPER, halo=False)
    water(d, 68, x0=2, x1=94, seed=3)
    # The bow drifting away below him on the current: a crescent of pale wood turning in the riffles.
    bow = "M52,84 C58,74 80,70 92,78 C80,72.4 60,75.6 52,84 Z"
    d.shape(bow, w=1.3)
    d.line("M51,85.4 l2,-2.6 M91,79.4 l2,-1.6", w=1.0)
    d.line("M54,90 c4,-1 8,-1 12,0 M76,86 c4,-1 8,-1 12,0 M64,92 l10,0", w=0.6, halo=False)
    return d


# 4. His father's horse passing in the street, seen from the patio at Bacerac (2-03) --------------------
def fathers_horse() -> Drawing:
    d = Drawing("fathers-horse")
    # Through the gateway, the horse going by in the street, framed by the arch (the wall drawn over it).
    d.line("M40,72 L80,72", w=0.8)
    horse(d, 62, 72, 0.5, flip=True)
    # The patio wall and its zaguán, flowers hanging down over the wall.
    wall = "M2,72 L2,22 L94,22 L94,72 L76,72 L76,40 C76,28 42,28 42,40 L42,72 Z"
    d.shape(wall)
    d.line("M2,22 L94,22", w=1.6)
    d.edge_shade(wall, dx=-2, dy=-2.5)
    for x, n, sd in ((8, 3, 613), (20, 2, 614), (84, 3, 615)):
        hang = blob(x + 3, 22 + n * 2, 4, n * 2, 9, seed=sd, depth=0.3)
        d.shape(hang, w=1.0)
        d.dots([(x + 1, 24 + n), (x + 5, 26 + n), (x + 2, 28 + n * 2)], r=0.7)
    d.line("M2,72 L94,72", w=1.0)
    # Billy in the patio, turned towards the gate with the coffee cup in his hand.
    p = figure(d, 20, 93, 34, hat=False)
    d.line(p("M3,-16 L5.4,-12 L7,-14"), w=1.1)
    d.shape(p("M6.4,-15.6 L9.6,-15.6 L9,-13 L7,-13 Z"), w=0.9)
    d.line(p("M7.4,-17 c0,-1 1,-1 1,-2 M8.8,-17 c0,-1 1,-1 1,-2"), w=0.6, halo=False)
    d.ground(2, 94, 93, ticks=6, seed=601)
    return d


# 5. Gilchrist's spun half dollar at the Douglas crossing (2-03) ----------------------------------------
def gilchrists_half_dollar() -> Drawing:
    d = Drawing("gilchrists-half-dollar")
    # The gatehouse at the line and its barrier pole.
    shack = poly((4, 76), (4, 44), (22, 44), (22, 76))
    d.shape(shack)
    d.shape(poly((1, 44), (13, 36), (25, 44)), w=1.4)
    win = poly((8, 50), (18, 50), (18, 58), (8, 58))
    d.shape(win, w=1.0)
    d.hatch(win, angle=45, pitch=1.3)
    d.edge_shade(shack, dx=-2.5, dy=0)
    d.line("M22,58 L30,58 M30,56 L30,76", w=1.4)
    # The guard, a hand up from tossing the coin.
    p = figure(d, 34, 88, 30)
    d.line(p("M2.6,-17 L5.6,-21 L6.4,-26"), w=1.1)
    # The coin spinning up between them, and the boy's cupped hand reaching for it.
    d.shape(ellipse(46, 40, 1.6, 2.8), w=1.1)
    d.hatch(ellipse(46, 40, 1.6, 2.8), angle=80, pitch=0.7)
    d.line("M42,40 l-2,0 M50,40 l2,0 M46,35 l0,-2 M43,36.6 l-1.4,-1.4 M49,36.6 l1.4,-1.4", w=0.6, halo=False)
    d.line("M40,48 C41,46 42,45 43,44", w=0.5, halo=False)

    def reach(t):
        d.line(t("M57,36 C55,30 53,24 49,20"), w=1.1)
    rider(d, 68, 90, 0.56, flip=True, hat="cowboy", extra=reach)
    d.ground(2, 94, 90, ticks=6, seed=602)
    return d


# 6. Old Sanders on his porch, Leona's hand on his shoulder (2-04) --------------------------------------
def sanders_porch() -> Drawing:
    d = Drawing("sanders-porch")
    # The porch roof, posts and boards.
    d.shape(poly((2, 30), (62, 30), (66, 36), (2, 36)), w=1.5)
    d.hatch(poly((2, 30), (62, 30), (66, 36), (2, 36)), angle=0, pitch=1.4)
    d.line("M4,36 L4,80 M58,36 L58,80", w=1.6)
    d.line("M2,80 L64,80 M2,83.6 L62,83.6", w=1.2)
    door = poly((7, 80), (7, 46), (17, 46), (17, 80))
    d.shape(door, w=1.1)
    d.hatch(door, angle=45, pitch=1.6)
    # The old man in his chair, facing the yard.
    d.line("M30,80 L30,56 M44,80 L44,64 M30,66 L44,66", w=1.1)
    sit = "M32,66 L32,52 C32,48 34,47 37,47 C40,47 41,49 41,52 L42,60 L50,62 L50,66 Z"
    d.shape(sit, w=1.3)
    d.hatch("M32,64 L32,52 C32,48 34,47 37,47 C40,47 41,49 41,52 L41.6,60 L36,64 Z", angle=45, pitch=1.3)
    d.line("M50,66 L50,79 L53,79", w=1.3)
    d.shape(circle(37, 43.4, 3), w=1.1)
    hat = "M31.6,41.4 L42.4,41.4 L40,40.2 C40,36.6 34,36.6 34,40.2 Z"
    d.shape(hat, w=1.0)
    d.hatch(hat, angle=0, pitch=0.9)
    d.line("M39,53 L46,59", w=1.0)
    # Leona standing behind him, one hand on his shoulder and the other shading her eyes.
    p = woman(d, 26, 80, 34)
    d.line(p("M2.6,-17 L7,-14.4 L8.6,-17.4"), w=1.1)
    d.line(p("M-2.6,-17 L-1,-13 L1,-19.4 L3,-22"), w=1.1)
    # The rider in the yard.
    rider(d, 80, 88, 0.34, flip=True, hat="cowboy")
    d.ground(2, 94, 89, ticks=6, seed=603)
    return d


# 7. Billy untying the horse from a parking meter in Lordsburg (2-06) -----------------------------------
def parking_meter() -> Drawing:
    d = Drawing("parking-meter")
    # A shop front along the street.
    d.line("M2,22 L94,22 M2,26 L94,26", w=1.0)
    for x in (4, 58):
        win = poly((x, 32), (x + 32, 32), (x + 32, 56), (x, 56))
        d.shape(win, w=1.1)
        d.hatch(win, angle=45, pitch=3.4)
    door = poly((42, 62), (42, 32), (52, 32), (52, 62))
    d.shape(door, w=1.1)
    d.hatch(door, angle=45, pitch=1.6)
    d.line("M2,62 L94,62", w=0.9)
    # The kerb, the horse standing at it, and the meter it was tied to.
    horse(d, 66, 86, 0.44, flip=True)
    d.line("M2,88 L94,88 M2,91 L94,91", w=1.0)
    post = poly((29, 88), (29, 68), (31, 68), (31, 88))
    d.shape(post, w=1.2)
    head = "M25.6,68 L25.6,58 C25.6,53 34.4,53 34.4,58 L34.4,68 Z"
    d.shape(head, w=1.5)
    d.shape("M27.6,62 L27.6,58.6 C27.6,56 32.4,56 32.4,58.6 L32.4,62 Z", w=0.8)
    d.line("M30,61.6 L31.4,58", w=0.6, halo=False)
    d.line("M31,70 C38,70 42,66 46,62", w=0.9)
    # Billy, ragged, at the meter untying the reins, and a man in the street turned to stare.
    p = figure(d, 16, 88, 28)
    d.line(p("M-4,-8.4 l0.6,1.6 l0.8,-1.2 l0.8,1.4 l0.8,-1.2 l0.8,1.4 l0.8,-1.2 l0.6,1.2"), w=0.6, halo=False)
    d.line(p("M3,-16 L8,-12 L11,-13"), w=1.1)
    q = figure(d, 90, 88, 22, flip=True)
    d.line(q("M-2.8,-17 L-4.6,-10"), w=1.0)
    return d


# 8. The brothers riding out of Lordsburg double, the dog trotting after (2-07) -------------------------
def riding_out_double() -> Drawing:
    d = Drawing("riding-out-double")
    # A yard with a washline, and the woman hanging clothes, her clothespins in her mouth.
    d.line("M8,64 L8,36 M40,64 L40,36 M8,38 C18,42 30,42 40,38", w=1.2)
    d.shape("M13,40 L13,50 L19,50 L19,41.6 Z", w=0.9)
    d.shape("M28,41.6 L28,52 L34,52 L34,40.6 Z", w=0.9)
    p = woman(d, 23, 64, 22)
    d.line(p("M2.6,-17 L5,-21 L6,-24"), w=1.0)
    d.line("M2,64 L46,64", w=0.8)
    # The two boys on the one horse, the bag tied to the horn, and the dog behind.
    def double(t):
        pillion(d, t)
        bag = t("M60,40 C58,42 58,50 61,51 C64,51 66,48 64,40 Z")
        d.shape(bag, w=1.0)
    rider(d, 62, 88, 0.52, hat="cowboy", extra=double)
    dog(d, 0.24, 8, 66)
    d.ground(2, 94, 89, ticks=6, seed=604)
    return d


# 9. Two sandhill cranes on the flooded flats, and the fencepost fire (2-07) ----------------------------
def cranes_on_the_flats() -> Drawing:
    d = Drawing("cranes-on-the-flats")
    # The far edge of the flats and the sheet of water on them.
    d.line("M2,34 C30,33 60,33 94,32", w=0.8)
    d.line("M34,58 C50,57 76,57 94,58", w=1.0)
    standing_crane(d, 52, 58, 0.62)
    standing_crane(d, 72, 57, 0.7, flip=True)
    standing_crane(d, 52, 58, 0.62, mirror=True)
    standing_crane(d, 72, 57, 0.7, flip=True, mirror=True)
    for y in (60.6, 62.8, 65, 67.2):
        d.line(f"M40,{y} L94,{y}", w=1.0, color=PAPER, halo=False)
    d.line("M38,62 l10,0 M60,65 l14,0 M80,61 l10,0 M46,68 l10,0", w=0.6, halo=False)
    d.line("M34,72 C50,71 76,71 94,72", w=0.8)
    # The cracked mud of the flats, and the fire of fenceposts blown ragged in the wind.
    d.line("M2,80 L30,78 M2,88 L40,86 M8,80 l2,8 M20,79 l-1,8 M30,78 l2,8 M44,82 l12,-1 l6,6 M70,82 l14,1 l2,6",
           w=0.6, halo=False)
    fire(d, 16, 72, 1.1)
    d.line("M2,74 L30,68 M4,68 L28,75", w=1.8)
    d.line("M24,52 C28,50 32,52 36,50 M26,46 l3,-1", w=0.6, halo=False)
    d.ground(2, 94, 92, ticks=6, seed=605)
    return d


# 10. The brothers in the gravel pool on the San Simon, the dog in the grass (2-07) ---------------------
def san_simon_pool() -> Drawing:
    d = Drawing("san-simon-pool")
    cottonwood(d, 20, 60, 54, 30, seed=606)
    cottonwood(d, 76, 58, 50, 28, seed=607)
    # The pool: the two boys sitting in it to the chest, bareheaded.
    d.line("M2,62 C30,60 60,61 94,60", w=0.9)
    for x, h in ((40, 1.0), (56, 0.9)):
        torso = f"M{x - 4 * h},74 L{x - 4 * h},{74 - 8 * h} C{x - 4 * h},{70 - 8 * h} {x + 4 * h},{70 - 8 * h} " \
                f"{x + 4 * h},{74 - 8 * h} L{x + 4 * h},74 Z"
        d.shape(torso, w=1.3)
        d.shape(circle(x, 74 - 13 * h, 3 * h), w=1.2)
        d.hatch(f"M{x - 3 * h},{74 - 14 * h} C{x - 3 * h},{74 - 17 * h} {x + 3 * h},{74 - 17 * h} {x + 3 * h},"
                f"{74 - 14 * h} Z", angle=0, pitch=0.8)
    for y in (73, 75.6):
        d.line(f"M26,{y} L70,{y}", w=1.6, color=PAPER, halo=False)
    water(d, 72, x0=24, x1=74, seed=4)
    d.dots([(30, 82), (36, 84), (52, 83), (60, 85), (66, 82), (44, 86)], r=0.6)
    d.line("M22,80 C40,82 60,82 76,79", w=0.8)
    # The dog sitting in the grass, watching them.
    dog(d, 0.3, 68, 56, flip=True, sit=True)
    grass(d, [(78, 82), (86, 83), (92, 81), (6, 82), (14, 84)], h=4)
    d.ground(2, 94, 90, ticks=6, seed=608)
    return d


SUBJECTS = {
    "old-man-at-the-saddle": old_man_at_the_saddle,
    "rim-pictographs": rim_pictographs,
    "bow-in-the-ford": bow_in_the_ford,
    "fathers-horse": fathers_horse,
    "gilchrists-half-dollar": gilchrists_half_dollar,
    "sanders-porch": sanders_porch,
    "parking-meter": parking_meter,
    "riding-out-double": riding_out_double,
    "cranes-on-the-flats": cranes_on_the_flats,
    "san-simon-pool": san_simon_pool,
}
