"""Vignettes of the sixth round (group c): two scenes that carry the book's cruelty and its fading wolves, in place
of two weaker drawings. The old woman and the girl rolling cigarettes on the pilgrims' trail, her memory of the
priest shot against his own church rising in her smoke (1-09), and the field at Torreón as the girl tells it, the
riderless horse among the dead and the small wolves coming in (3-12). Loaded by art/vignettes/make_vignettes.py.

Each is checked against the passage that gives it. The horse is the traced Muybridge plate (rider-annie-g, public
domain) with the rider cut away, the wolves the traced US Fish and Wildlife Service she-wolf outline, made small.
Everything else is drawn by hand from the book. Light from the north-west, as everywhere: shade on each shape's
south-east side.
"""

import random

from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, grass, poly
from art.vignettes.subjects_parts_1_2 import wolf
from art.vignettes.subjects_parts_3_4 import blob, place
from art.vignettes.subjects_round3 import chevrons, horse
from art.vignettes.subjects_round5_e import palmilla, person


def seated_woman(d: Drawing, x: float, y: float, k: float, flip: bool = False, shawl: bool = True):
    """A woman sitting on the ground facing east, knees drawn up under her skirt, seat at (x, y), about 30 units
    tall before k: a dark rebozo over her head and shoulders, or (shawl False) long dark hair down her back."""
    def p(path: str) -> str:
        return place(path, x, y, k, flip)
    lap = p("M-9,0 C-9,-5 -5,-8 0,-9 L9,-13 C11.4,-13.6 13,-12 12.6,-9.6 L11.6,0 Z")
    d.shape(lap, w=1.3)
    d.edge_shade(lap, dx=-1.4 * k, dy=-1.4 * k)
    torso = p("M-6,-6 C-6.4,-14 -5,-20 -1,-23 L3,-23 C5,-19 5.4,-13 4.6,-7 Z")
    d.shape(torso, w=1.3)
    d.shape(p(circle(0.6, -26.4, 3.4)), w=1.1)
    if shawl:
        rebozo = p("M-3.4,-27 C-3.6,-31.6 4,-32 4.4,-27.6 L5.6,-20 L-1,-15 L-7.6,-9 C-7.6,-15 -6.4,-22 -3.4,-27 Z")
        d.shape(rebozo, w=1.1)
        d.hatch(rebozo, angle=45, pitch=1.1, cross=True)
    else:
        hair = p("M-3,-27 C-3.4,-31 3.6,-31.4 3.6,-28 L1,-27 L-1,-19 L-4.6,-19 C-4.6,-22 -4,-25 -3,-27 Z")
        d.shape(hair, w=0.9)
        d.hatch(hair, angle=80, pitch=0.8)
    return p


# 1. The old woman and the girl by the trail, rolling cigarettes, and the priest she saw shot (1-09) ----------
def old_woman_and_girl() -> Drawing:
    d = Drawing("old-woman-and-girl")
    # What she tells, rising in her smoke: as a child she saw a priest stood against the wall of his own church
    # at Ascensión and shot, and the women came and knelt over him.
    cloud = blob(56, 24, 36, 19, 11, seed=940, depth=0.14)
    d.line(cloud, w=0.8)
    church = "M38,38 L38,20 L48,20 L48,13 L53,8 L58,13 L58,20 L74,20 L74,38 Z"
    d.shape(church, w=1.2)
    d.edge_shade(church, dx=-1.6, dy=-1.6)
    door = "M51,38 L51,29 C51,26 55,26 55,29 L55,38 Z"
    d.shape(door, w=0.9)
    d.hatch(door, angle=45, pitch=1.1, cross=True)
    d.shape(poly((52, 16.4), (54, 16.4), (54, 19), (52, 19)), w=0.7)
    d.dots([(42, 26), (44, 30), (46, 24), (62, 27), (66, 31), (68, 25)], r=0.5)
    # The priest lying at the foot of the wall, and two women kneeling to lift him.
    d.shape(poly((40, 38.6), (40.6, 36.4), (50, 36), (50, 38.6)), w=1.0)
    d.hatch(poly((40, 38.6), (40.6, 36.4), (50, 36), (50, 38.6)), angle=45, pitch=0.9)
    d.shape(circle(38.4, 37, 1.5), w=0.8)
    for kx in (60, 67):
        kneel = f"M{kx - 2},38.6 L{kx - 2},34 C{kx - 2},31.4 {kx + 2},31.4 {kx + 2},34 L{kx + 4},38.6 Z"
        d.shape(kneel, w=0.9)
        d.hatch(kneel, angle=45, pitch=1.0)
        d.shape(circle(kx, 30.2, 1.4), w=0.8)
    # The mountainside, the trail along it, and the country falling away to the west far below.
    d.line("M84,64 C88,66 92,68 96,72 M2,62 L8,61.6", w=0.8)
    grass(d, [(6, 92), (52, 92), (70, 91), (90, 92)], h=4.4)
    # The old woman in her black rebozo, cigarette at her mouth, her smoke going up.
    seated_woman(d, 22, 90, 1.1)
    d.line("M24,72 L29,68 L29.6,64.6", w=1.2)
    d.line("M29.8,62.6 C27,58 32,55 29,51 C27,48 31,46 31,42", w=0.8, halo=False)
    # The tobacco and the cut cornhusks in the grass between them.
    for hx in (42, 46.4):
        d.shape(f"M{hx - 2},90 L{hx},84 L{hx + 2},90 Z", w=0.8)
    d.dots([(50, 89.4), (51.6, 88.6), (52.6, 89.8)], r=0.6)
    # The girl beyond, her back to them, smoking and looking out over the empty country.
    seated_woman(d, 66, 90, 1.0, shawl=False)
    d.line("M68,72 L73,68.6 L73.4,66", w=1.1)
    d.line("M73.6,64.6 C76,61 72,58 75,55", w=0.7, halo=False)
    d.ground(2, 94, 92, ticks=6, seed=941)
    return d


# 2. The field at Torreón as the girl tells it: the riderless horse among the dead, the small wolves coming in
# (3-12) ------------------------------------------------------------------------------------------------------
def torreon_field() -> Drawing:
    d = Drawing("torreon-field")
    # The dark drawing down, and the moon rising blind and white in the east.
    sky = "M-2,-2 L98,-2 L98,52 L-2,52 Z"
    d.hatch(sky, angle=0, pitch=2.2, w=0.6)
    d.shape(circle(78, 16, 7), w=1.2)
    # The low horizon of that plain, and the palmettos.
    d.line("M2,52 C30,51 60,51 94,52", w=1.0)
    for x, b, h in ((10, 56, 12), (90, 58, 14), (58, 54, 8)):
        palmilla(d, x, b, h)
    # Small birds come back to the thorns, flitting.
    chevrons(d, [(30, 30, 0.7), (40, 24, 0.6), (22, 22, 0.5)])
    # The riderless horse wandering in silhouette among the bodies, the stirrups hanging loose.
    f = horse(d, 54, 76, 0.36, graze=0.6)
    d.hatch(poly(f(30, 40), f(64, 40), f(64, 64), f(30, 64)), angle=45, pitch=1.4)
    d.line(f"M{f(46, 44)[0]:.1f},{f(46, 44)[1]:.1f} L{f(44, 58)[0]:.1f},{f(44, 58)[1]:.1f} "
           f"l2.4,0", w=1.0, halo=False)
    # The dead, fallen where they lay, and the sword dropped in the sand.
    rnd = random.Random(942)
    for hx, hy, flip in ((14, 82, False), (78, 86, True), (34, 90, False), (88, 72, True)):
        s = -1 if flip else 1
        person(d, (hx, hy), (hx + 3.4 * s, hy + 0.4), (hx + 12 * s, hy + 0.6),
               back=[[(hx + 12 * s, hy + 0.6), (hx + 19 * s, hy + rnd.uniform(-0.6, 1.0))]],
               front=[[(hx + 12 * s, hy + 0.6), (hx + 18 * s, hy - 2.4), (hx + 20 * s, hy + 0.4)],
                      [(hx + 4 * s, hy + 0.4), (hx + 8 * s, hy - 3)]], r=2.2, width=4.6, w=1.4)
    d.line("M44,92 L60,89.4", w=1.3)
    d.line("M46.4,94 L45.6,89.6", w=1.1)
    # The little wolves trotting in out of the dusk.
    for ox, oy, k in ((-2, 56, 0.16), (14, 60, 0.18), (2, 66, 0.17)):
        wolf(d, k, ox, oy, w=1.1)
    d.ground(2, 94, 95, ticks=5, seed=943)
    return d


SUBJECTS = {
    "old-woman-and-girl": old_woman_and_girl,
    "torreon-field": torreon_field,
}
