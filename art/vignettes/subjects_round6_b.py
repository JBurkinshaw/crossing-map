"""Vignettes of the sixth round, group b: three drawings that replace weak ones with scenes that carry the book's
themes, Mexico and the fading Apaches at the fair in Colonia Morelos (1-09), the cairns of the slain on the dead
pass over the sierra (2-01), and the great sawed stump by the river bed below the Parham house (1-01). Loaded by
art/vignettes/make_vignettes.py.

Each is checked against the passage it shows and drawn from the book, after the period references its seed
`credit` names: the riders are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and
IV helpers, the travois after the Little Bighorn photograph of a mule travois (public domain), the pronghorn after
the public-domain park photographs used for the wolves and antelope. Light from the north-west, as everywhere:
shade on each shape's south-east side.
"""

from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly
from art.vignettes.subjects_parts_1_2 import pronghorn
from art.vignettes.subjects_parts_3_4 import blob, rider, steer
from art.vignettes.subjects_round3 import figure
from art.vignettes.subjects_round5_d import sitter


def bare_tree(d: Drawing, x: float, base: float, h: float, seed: int, w: float = 1.0):
    """A winter cottonwood with no leaves: a pale bole and bony limbs forking up and out."""
    s = h / 50
    trunk = f"M{x - 2.6 * s},{base} L{x - 1.2 * s},{base - 22 * s} L{x + 1.4 * s},{base - 22 * s} L{x + 3 * s},{base} Z"
    d.shape(trunk, w=1.3 * w)
    lean = (seed % 3 - 1) * 2
    limbs = [
        f"M{x - 1 * s},{base - 22 * s} C{x - 6 * s},{base - 30 * s} {x - 12 * s},{base - 36 * s} {x - 16 * s},{base - 48 * s}",
        f"M{x + 1 * s},{base - 22 * s} C{x + 4 * s},{base - 32 * s} {x + 10 * s},{base - 38 * s} {x + 12 * s + lean},{base - 50 * s}",
        f"M{x},{base - 22 * s} L{x + 1 * s + lean},{base - 44 * s}",
    ]
    d.line(" ".join(limbs), w=1.4 * w)
    twigs = [
        f"M{x - 8 * s},{base - 33 * s} l{-7 * s},{-4 * s} M{x - 12 * s},{base - 40 * s} l{3 * s},{-8 * s}",
        f"M{x + 6 * s},{base - 34 * s} l{7 * s},{-3 * s} M{x + 9 * s},{base - 42 * s} l{-4 * s},{-6 * s}",
        f"M{x + 0.6 * s},{base - 36 * s} l{-5 * s},{-5 * s}",
    ]
    d.line(" ".join(twigs), w=0.9 * w)


def cairn(d: Drawing, x: float, base: float, s: float = 1.0):
    """A heap of fieldstones, base centred on (x, base), its south-east side shaded."""
    stones = [(-5, -1.6, 3.2, 1.8), (0.4, -1.8, 3.4, 2.0), (5.4, -1.4, 2.6, 1.6), (-2.6, -4.8, 3.0, 1.8),
              (2.8, -5.0, 2.8, 1.8), (0, -8.2, 2.6, 1.7), (0.4, -11, 1.8, 1.3)]
    for cx, cy, rx, ry in stones:
        q = ellipse(x + cx * s, base + cy * s, rx * s, ry * s)
        d.shape(q, w=1.0)
        d.hatch(ellipse(x + (cx + rx * 0.35) * s, base + (cy + ry * 0.3) * s, rx * 0.6 * s, ry * 0.6 * s), angle=45,
                pitch=0.9)


# 1. The fair in the alameda at Colonia Morelos: the band in the kiosk, Yaquis with bows, two Apache boys (1-09)
def fair_in_the_alameda() -> Drawing:
    d = Drawing("fair-in-the-alameda")
    # The brick store's false front across the road, behind.
    front = poly((2, 70), (2, 22), (26, 22), (26, 70))
    d.shape(front, w=1.4)
    d.shape(poly((1, 22), (1, 18), (27, 18), (27, 22)), w=1.1)
    d.line(" ".join(f"M2,{y} L26,{y}" for y in range(26, 44, 3)), w=0.4, halo=False)
    door = poly((4, 70), (4, 54), (10, 54), (10, 70))
    d.shape(door, w=1.0)
    d.hatch(door, angle=45, pitch=1.3, cross=True)
    d.edge_shade(front, dx=-2.4, dy=0)
    # Two starveling trees of the alameda, the bunting strung from one to the other.
    for x, cy, seed in ((40, 20, 920), (90, 20, 921)):
        d.line(f"M{x},72 C{x - 1},56 {x + 1},44 {x},{cy + 8}", w=1.4)
        crown = blob(x, cy, 7, 9, 9, seed=seed, depth=0.3)
        d.shape(crown, w=1.2)
        d.edge_shade(crown, dx=-2.4, dy=-2.4)
    d.line("M42,22 C56,32 74,32 88,22", w=0.7)
    d.shape(" ".join(f"M{x:.1f},{22 + (x - 42) * (88 - x) * 0.0052:.1f} l3,0 l-1.5,3.6 Z" for x in range(46, 86, 6)),
            w=0.7)
    # The little kiosk: a roof on posts over a raised floor, and the brass band sitting in it.
    roof = "M42,42 L50,34 L74,34 L82,42 Z"
    d.shape(roof, w=1.3)
    d.hatch(roof, angle=0, pitch=1.5)
    d.line("M62,34 L62,30", w=0.9)
    for x in (51, 62, 73):
        body = f"M{x - 3.4},60 L{x - 3},51.6 C{x - 2},50 {x + 2},50 {x + 3},51.6 L{x + 3.4},60 Z"
        d.shape(body, w=1.0)
        d.shape(circle(x, 47.4, 2.4), w=1.0)
        d.hatch(f"M{x - 2.4},46.8 C{x - 2.4},44 {x + 2.4},44 {x + 2.4},46.8 Z", angle=0, pitch=0.8)
    d.line("M53,53 L59,50", w=1.0)
    d.line("M73,53 C76,51 77,47 76,44", w=1.4)
    bell = circle(76, 42.6, 3.0)
    d.shape(bell, w=1.0)
    d.shape(circle(76, 42.6, 1.3), w=0.6)
    d.line("M45,42 L45,60 M79,42 L79,60", w=1.2)
    plinth = poly((40, 60), (84, 60), (84, 67), (40, 67))
    d.shape(plinth, w=1.3)
    d.edge_shade(plinth, dx=-2, dy=-1.6)
    d.line("M40,63 L84,63", w=0.5, halo=False)
    # In front, a Yaqui with his bow and quiver, and the two Apache boys in deerskin boots.
    quiver = "M18,60 L28,74 L31,72 L21,58 Z"
    d.shape(quiver, w=1.0)
    d.hatch(quiver, angle=45, pitch=1.0)
    d.line("M19,59 l-2,-4 M20.4,58 l-0.6,-4.6 M21.6,57.4 l1,-4", w=0.9)
    p = figure(d, 27, 90, 30, hat=False)
    d.hatch(p("M-2.2,-21.6 C-2.4,-24 2.4,-24 2.2,-21.6 L2.6,-19 L-2.6,-19 Z"), angle=80, pitch=0.8)
    d.line(p("M3,-16 L6.6,-13"), w=1.0)
    d.line(p("M6,-29 C11,-21 11,-6 6,1"), w=1.7)
    d.line(p("M6,-29 L6,1"), w=0.5, halo=False)
    for x, h in ((54, 22), (66, 21)):
        q = figure(d, x, 90, h, hat=False)
        boots = q("M-3,-8 L-3.4,0 L-0.6,0 L-0.6,-8 Z M0.6,-8 L0.6,0 L3.6,0 L3,-8 Z")
        d.shape(boots, w=0.9)
        d.hatch(boots, angle=60, pitch=0.9)
        d.hatch(q("M-2.2,-21.6 C-2.4,-24 2.4,-24 2.2,-21.6 L2.6,-18.4 L-2.6,-18.4 Z"), angle=80, pitch=0.8)
    d.ground(2, 94, 91, ticks=7, seed=922)
    return d


# 2. The cairns of the slain below the dead pass on the wagon road over the sierra (2-01) -------------------
def mojoneras_de_muerte() -> Drawing:
    d = Drawing("mojoneras-de-muerte")
    # The narrow pass between two rock walls, the road coming down out of it.
    left = "M-2,64 L-2,10 L8,6 L18,14 L26,10 L34,22 L40,36 L42,48 L36,60 Z"
    right = "M98,60 L98,8 L86,4 L76,12 L66,8 L58,22 L54,36 L54,48 L60,58 Z"
    for m in (left, right):
        d.shape(m, w=1.6)
    d.hatch(left, angle=70, pitch=2.2, w=0.6)
    d.edge_shade(right, dx=-3.5, dy=-3.5, cross=True)
    d.line("M20,24 L28,34 M10,30 L22,44 M70,20 L64,32 M84,24 L76,40", w=0.8, halo=False)
    # The old wagon-hub scars along the rock at the narrows.
    d.line("M38,44 l3,0 M37,47 l4,-0.4 M56,43 l-3,0 M57,46 l-4,0.4", w=0.9, halo=False)
    road = "M44,40 C46,48 52,52 48,58 C44,64 30,66 36,74 C42,82 66,82 70,94"
    d.line(road, w=1.0)
    d.line("M52,40 C54,48 58,52 54,58 C50,64 38,67 44,74 C50,80 76,82 82,94", w=1.0)
    # The cairns scattered below the pass, where travellers were killed.
    for x, base, s in ((14, 80, 1.3), (26, 90, 1.0), (62, 70, 0.8), (84, 84, 1.4), (76, 66, 0.7), (8, 66, 0.8)):
        cairn(d, x, base, s)
    # Billy, gaunt, with the bow across his back, coming down out of the pass alone.

    def bow(t):
        d.line(t("M38,16 C30,24 30,40 40,48"), w=1.3)
    rider(d, 48, 52, 0.22, hat="straw", extra=bow)
    grass(d, [(40, 92), (92, 92), (4, 90)], h=3.0)
    return d


# 3. Dragging dead wood past the great sawed stump in the river bed below the house (1-01) ----------------
def wood_and_the_sawed_stump() -> Drawing:
    d = Drawing("wood-and-the-sawed-stump")
    # The sun low in the west under the barren mountains, and the antelope among the cattle on the plain.
    hills = "M2,46 L10,38 L18,42 L28,32 L36,40 L44,36 L52,44 L60,40 L72,46"
    d.line(hills, w=1.0)
    d.shape("M10,46 C10,40 20,40 20,46 Z", w=1.0, fill=True)
    d.line("M2,48 L94,48", w=0.8)
    steer(d, 26, 47, 0.16)
    steer(d, 46, 48, 0.15, flip=True)
    pronghorn(d, 36, 50, 0.32)
    pronghorn(d, 56, 50, 0.3)
    # The bare cottonwoods with their limbs like bones.
    bare_tree(d, 78, 78, 62, seed=923)
    bare_tree(d, 92, 70, 44, seed=924, w=0.8)
    # Billy on the horse dragging the travois of dead wood, Boyd riding on it with the axe.
    d.line("M54,64 L26,84 M56,62 L30,80", w=1.3)
    load = "M28,80 C28,77 32,75 36,73 L48,66 C50,65 52,66 51.6,68 L38,77 C34,80 30,82 28,80 Z"
    d.shape(load, w=1.2)
    d.line("M32,76 L52,70 M30,79 L48,71 M36,73 l-4,-3 M46,68 l-2,-4", w=0.8, halo=False)
    boyd = sitter(d, 42, 72, 0.5, flip=True)
    d.line(boyd("M2,-10 L10,-24"), w=1.2)
    d.shape(boyd("M8,-26 L13,-23 L11.6,-21 L8.4,-22.6 Z"), w=0.9)
    rider(d, 66, 84, 0.4, hat="cowboy")
    # The great sawed stump in front.
    top = ellipse(16, 70, 14, 4)
    side = "M2,70 L3,88 C10,91 22,91 29,88 L30,70 Z"
    d.shape(side, w=1.8)
    d.line("M7,72 L7.4,88 M13,74 L13,90 M20,74 L20.4,90 M26,72 L26,88", w=0.6, halo=False)
    d.edge_shade(side, dx=-3, dy=0)
    d.shape(top, w=1.6)
    d.line(ellipse(16, 70, 9, 2.6) + " " + ellipse(16, 70, 4.4, 1.2), w=0.6, halo=False)
    d.ground(2, 94, 91, ticks=7, seed=925)
    return d


SUBJECTS = {
    "fair-in-the-alameda": fair_in_the_alameda,
    "mojoneras-de-muerte": mojoneras_de_muerte,
    "wood-and-the-sawed-stump": wood_and_the_sawed_stump,
}
