"""Vignettes of the sixth round, group e: new drawings for the book's themes where the set had none. The
executions at the granja wall as the girl tells them to the blind man (3-09), the girl taken away at San Lorenzo
as Quijada tells it (4-05), Billy's dream of the wolves in the snow (3-09), the lumber and the maize warehouses at
Las Varas (3-04), the slag heaps of Corralitos before dawn (4-06), and the die-up of 1886 as old Sanders remembers
it (4-01). Loaded by art/vignettes/make_vignettes.py.

Each is checked against the passage that gives it. The two scenes the book only reports sit inside the broadside
border of the corrido drawings (round 5, group f), to say that they are someone's telling and not the book's own
scene. The wolves are the traced US Fish and Wildlife Service she-wolf (public domain). The house at San Lorenzo
follows Russell Lee's FSA photograph of an adobe at Peñasco (public domain). Everything else, the people posed by
hand, the dog and the cattle among them, is drawn from the book. Light from the north-west, as everywhere: shade on each shape's
south-east side.
"""

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly
from art.vignettes.subjects_parts_1_2 import wolf
from art.vignettes.subjects_parts_3_4 import place
from art.vignettes.subjects_round3 import figure
from art.vignettes.subjects_round5_c import woman
from art.vignettes.subjects_round5_e import mud_house, person
from art.vignettes.subjects_round5_f import broadside


def straw_hat(d: Drawing, x: float, y: float, s: float = 1.0):
    """A peaked sombrero of woven straw held brim-on, its brim centred on (x, y)."""
    brim = f"M{x - 7 * s},{y} C{x - 4 * s},{y - 2.2 * s} {x + 4 * s},{y - 2.2 * s} {x + 7 * s},{y} " \
           f"C{x + 4 * s},{y + 2 * s} {x - 4 * s},{y + 2 * s} {x - 7 * s},{y} Z"
    d.shape(brim, w=1.0)
    d.hatch(brim, angle=20, pitch=1.1, w=0.5)
    crown = f"M{x - 3 * s},{y - 0.8 * s} C{x - 2.6 * s},{y - 4 * s} {x - 1 * s},{y - 8.4 * s} {x},{y - 8.8 * s} " \
            f"C{x + 1 * s},{y - 8.4 * s} {x + 2.6 * s},{y - 4 * s} {x + 3 * s},{y - 0.8 * s} Z"
    d.shape(crown, w=1.0)
    d.hatch(crown, angle=-60, pitch=1.2, w=0.5)
    # The band round the crown, and a line or two of the weave on the brim.
    d.hatch(f"M{x - 3 * s},{y - 0.8 * s} L{x - 2.8 * s},{y - 2.2 * s} L{x + 2.8 * s},{y - 2.2 * s} "
            f"L{x + 3 * s},{y - 0.8 * s} Z", angle=0, pitch=0.8)
    d.line(f"M{x - 5 * s},{y + 0.6 * s} C{x - 2 * s},{y + 1.4 * s} {x + 2 * s},{y + 1.4 * s} {x + 5 * s},{y + 0.6 * s}",
           w=0.5, halo=False)


# 1. The granja wall washed clean, and the girl with her father's hat (3-09) -----------------------------
def rodeo_wall() -> Drawing:
    d = Drawing("rodeo-wall")
    broadside(d)
    # The clay wall of the granja, long and blank, the wash marks still running down it.
    wall = "M8,62 L8,24 C12,22 18,23 24,22 C40,21 60,23 76,21 C82,21 86,22 88,23 L88,62 Z"
    d.shape(wall)
    d.edge_shade(wall, dx=-3, dy=-1)
    d.line("M14,27 L14.4,52 M22,27 L21.6,46 M30,26 L30.4,56 M66,26 L65.8,48 M74,25 L74.4,56 M82,26 L81.6,44",
           w=0.5, halo=False)
    d.line("M12,34 l3,0.4 M50,30 l3,0 M78,50 l2.6,0", w=0.7, halo=False)
    # The puddles of the night's rain at its foot.
    for cx, cy, rx in ((12, 74, 6), (80, 72, 8)):
        pool = ellipse(cx, cy, rx, 1.6)
        d.shape(pool, w=0.9)
        d.hatch(pool, angle=0, pitch=1.0, w=0.5)
    # The bucket they washed it with.
    bucket = "M20,68 L28,68 L27,76 L21,76 Z"
    d.shape(bucket, w=1.1)
    d.edge_shade(bucket, dx=-1.6, dy=0)
    d.line("M20.4,70.6 L27.6,70.6 M20.8,73.6 L27.2,73.6", w=0.6, halo=False)
    d.line("M20,68 C20,63 28,63 28,68", w=0.8)
    # The blind man, hat on, and the girl telling him, her father's straw sombrero held before her.
    figure(d, 36, 88, 46)
    d.line("M40,70 L46,89", w=1.2)
    woman(d, 62, 88, 32)
    straw_hat(d, 69, 71, 1.25)
    d.line("M59.6,66 L61.4,71 M64.4,66 L66,70", w=1.2)
    d.ground(8, 88, 89, ticks=5, seed=980)
    return d


# 2. The girl led away at San Lorenzo, bloodied and falling, as Quijada tells it (4-05) --------------------
def girl_taken_away() -> Drawing:
    d = Drawing("girl-taken-away")
    broadside(d)
    # A low adobe of the town behind, and the road.
    mud_house(d, 8, 30, 46, 34, door=20, seed=1)
    d.line("M8,46 L88,46", w=0.8)
    # The two who lead her off, their coats dark and their faces never shown.
    for x in (26, 72):
        p = figure(d, x, 89, 52, flip=x > 50)
        d.hatch(p("M-3,-17.6 C-2,-19 2,-19 3,-17.6 L4,-8.4 L-4,-8.4 Z"), angle=45, pitch=1.0)
        d.hatch(p(circle(0, -21, 2.2)), angle=45, pitch=0.7, cross=True)
    # The girl between them, her knees giving way and her feet dragging, held up by the arms, her clothes dark
    # with blood.
    person(d, head=(45, 52), neck=(47.6, 55.6), hip=(51, 69),
           back=([(47.6, 56.4), (38, 56), (30, 55.4)], [(51, 69), (49, 78), (58, 86)]),
           front=([(47.6, 56.4), (58, 56), (68, 55.4)], [(51, 69), (53, 79), (63, 85)]), r=3.2, width=7,
           dark=True)
    hair = "M42.6,49 C40.6,53 40.4,58 41.4,61 L44.4,60 L45.4,52 Z"
    d.shape(hair, w=0.8)
    d.hatch(hair, angle=80, pitch=0.8)
    skirt = "M46.6,66 L55,66 L58,79 L45,79 Z"
    d.shape(skirt, w=1.1)
    d.hatch(skirt, angle=45, pitch=1.0, cross=True)
    # Blood fallen on the road behind them.
    d.dots([(56, 91), (62, 90.4), (40, 90.6), (66, 91.2), (82, 90.6), (48, 91)], r=0.8)
    d.ground(8, 88, 89, ticks=5, seed=981)
    return d


# 3. Billy's dream: the wolves in a crescent before him in the moonlit snow (3-09) -------------------------
def wolves_dream() -> Drawing:
    d = Drawing("wolves-dream")
    # The winter night, the moon, and the dark shapes of the mountains the wolves look back to.
    d.hatch("M2,2 L94,2 L94,30 L2,30 Z " + circle(16, 12, 7), angle=0, pitch=3.0, w=0.5)
    d.shape(circle(16, 12, 4.6), w=1.2)
    ridge = "M2,36 L12,28 L20,31 L32,22 L44,31 L52,27 L60,32 L68,28 L72,30 L72,38 L2,38 Z"
    d.shape(ridge, w=1.0)
    d.hatch(ridge, angle=45, pitch=1.3)
    # The darkened house and its fence: the wolves come no nearer than the gate.
    house = "M76,52 L76,38 L84,31 L93,38 L93,52 Z"
    d.shape(house, w=1.3)
    d.hatch(house, angle=45, pitch=1.1, cross=True)
    d.line("M62,54 L62,46 M66,54 L66,46 M70,54 L70,46 M74,54 L74,46 M60,48 L76,48 M60,51.6 L76,51.6", w=0.9)
    # Billy kneeling in the snow, his arms out to them.
    person(d, head=(77, 62), neck=(77.4, 65.2), hip=(79, 74),
           back=([(77.4, 66), (71, 62), (66, 58.4)], [(79, 74), (75, 80), (84, 81)]),
           front=([(77.4, 66), (71, 69), (65.4, 70)], [(79, 74), (74, 81), (85, 82.4)]), r=2.6, width=4.6, w=1.4)
    # The wolves in a crescent before him, facing him.
    for k, cx, cy in ((0.2, 58, 56), (0.22, 40, 58), (0.24, 26, 68), (0.25, 30, 82), (0.24, 50, 88)):
        wolf(d, k, cx - 48 * k, cy - 53 * k, w=1.1)
    d.line("M6,72 l6,0 M60,74 l5,0 M10,92 l8,0 M68,90 l10,0", w=0.6, halo=False)
    return d


# 4. Las Varas: raw pine slabs on the sidings, the maize warehouses, the three-legged dog (3-04) ------------
DOG = ("M2,-12 L5,-13.4 C6,-15 7,-16 8,-16 L8.6,-18.4 L10,-15.6 C12,-14 13,-12 15,-11.6 C19,-11.6 23,-11.6 25,-12 "
       "C27,-12.6 29,-14 30,-15.6 C30,-13 28,-11 26,-10 C26,-8 25.5,-7 25,-6 L25.8,0 L24.4,0 L23.4,-5 L21.6,-5.4 "
       "L21.4,0 L20,0 L19.6,-6 C16,-6.6 13,-6.6 11,-6 L10.6,0 L9.2,0 L8.6,-6.6 C7,-8 6,-10 5,-10.6 C4,-10.6 3,-11 "
       "2,-12 Z")

# The letters MAIZ in strokes, 4 units tall, each 3 wide.
MAIZ = ("M0,4 L0,0 L1.5,2 L3,0 L3,4 M4.4,4 L5.9,0 L7.4,4 M5,2.6 L6.8,2.6 M8.8,0 L8.8,4 M10.2,0 L13.2,0 L10.2,4 "
        "L13.2,4")


# And COMPRO, the same.
COMPRO = ("M3,0 L0,0 L0,4 L3,4 M4.4,0 L7.4,0 L7.4,4 L4.4,4 Z M8.8,4 L8.8,0 L10.3,2 L11.8,0 L11.8,4 "
          "M13.2,4 L13.2,0 L16.2,0 L16.2,2 L13.2,2 M17.6,4 L17.6,0 L20.6,0 L20.6,2 L17.6,2 L20.6,4 "
          "M22,0 L25,0 L25,4 L22,4 Z")


def las_varas_lumber() -> Drawing:
    d = Drawing("las-varas-lumber")
    # The big adobe warehouse with its mud buttresses and its painted sign.
    wall = "M4,58 L4,24 L58,22 L58,58 Z"
    d.shape(wall)
    d.edge_shade(wall, dx=-3, dy=-1)
    for x in (4, 22, 40):
        b = f"M{x + 3},58 L{x + 4},38 C{x + 4},36.4 {x + 6.4},36.4 {x + 6.6},38 C{x + 8},44 {x + 11},50 {x + 13},58 Z"
        d.shape(b, w=1.2)
        d.edge_shade(b, dx=-1.6, dy=0)
    d.shape(poly((10, 25.4), (56, 24.2), (56, 32), (10, 33)), w=0.9)
    d.line(place(COMPRO, 13, 27, 1.0), w=0.8, halo=False)
    d.line(place(MAIZ, 41, 26.6, 1.0), w=0.8, halo=False)
    d.line("M49.6,25.6 L50.4,24.4", w=0.6, halo=False)
    # The stacks of raw slab-cut pine along the siding, the boards' ends showing.
    for x0, top in ((62, 40), (78, 46)):
        stack = poly((x0, 62), (x0, top), (x0 + 16, top - 2), (x0 + 16, 62))
        d.shape(stack, w=1.3)
        rows = " ".join(f"M{x0},{y} L{x0 + 16},{y - 1}" for y in range(top + 4, 62, 4))
        d.line(rows, w=0.6, halo=False)
        d.edge_shade(stack, dx=-2.4, dy=0)
    # The railway tracks.
    d.line("M2,66 L94,65 M2,70 L94,69", w=1.1)
    d.line(" ".join(f"M{x},64.2 L{x - 1},71.4" for x in range(6, 94, 6)), w=0.7, halo=False)
    # The boldlooking dog with a foreleg off, turned in the street to stand them off.
    dog = place(DOG, 34, 88, 0.9)
    d.shape(dog, w=1.2)
    d.edge_shade(dog, dx=-1.4, dy=-1.6)
    d.line(place("M12,-6.4 L12.6,-4.4", 34, 88, 0.9), w=1.0)
    d.ground(4, 92, 88.6, ticks=5, seed=982)
    return d


# 5. Corralitos before full light: loopholed adobes and the dark slag heaps (4-06) --------------------------
def corralitos_slagheaps() -> Drawing:
    d = Drawing("corralitos-slagheaps")
    # The sky still dark overhead, paling low in the east.
    d.hatch("M2,2 L94,2 L94,14 L2,30 Z", angle=0, pitch=2.0, w=0.5)
    d.hatch("M2,30 L94,14 L94,24 L2,40 Z", angle=0, pitch=3.6, w=0.4)
    d.line("M2,52 L94,52", w=0.8)
    # The naked slag heaps against the skyline.
    for cx, top, half in ((62, 24, 16), (84, 34, 11), (44, 38, 10)):
        heap = poly((cx - half, 52), (cx - 2.4, top), (cx + 2.4, top - 0.4), (cx + half, 52))
        d.shape(heap, w=1.2)
        d.hatch(heap, angle=60, pitch=1.0, cross=True)
        d.line(f"M{cx - 1},{top + 4} L{cx - half * 0.5},50 M{cx + 1.4},{top + 6} L{cx + half * 0.4},50", w=0.6,
               halo=False, color=PAPER)
    # The half-ruined adobes, their walls loopholed against the Apaches.
    wall = "M4,78 L4,40 L14,38 L18,44 L24,40 L34,41 L34,78 Z"
    d.shape(wall)
    d.edge_shade(wall, dx=-3, dy=-1)
    stub = "M34,78 L34,52 L42,50 L46,56 L52,54 L52,78 Z"
    d.shape(stub)
    d.edge_shade(stub, dx=-3, dy=-1)
    for x, y in ((8, 48), (16, 48), (27, 48), (38, 60), (46, 62)):
        slot = poly((x, y), (x + 1.4, y), (x + 1.4, y + 5), (x, y + 5))
        d.shape(slot, w=0.9)
        d.hatch(slot, angle=45, pitch=0.7)
    door = poly((14, 78), (14, 62), (22, 62), (22, 78))
    d.shape(door, w=1.2)
    d.hatch(door, angle=45, pitch=1.3, cross=True)
    d.line("M6,58 l3,0.4 M28,70 l3,0 M40,70 l2.6,0", w=0.6, halo=False)
    d.ground(2, 94, 80, ticks=6, seed=983)
    grass(d, [(60, 79), (74, 80), (88, 79)], h=3)
    return d


# 6. The die-up of '86: cattle so poor the low sun shows through them (4-01) -------------------------------
# A starved steer walking west in a 46 x 33 local box: spine and hip bones up, the belly drawn in, head low.
GAUNT = ("M16,6 C20,8 26,8 30,7 C33,6 35,4 37,4.6 L42,8 C44,11 44,16 42,20 L40,22 C34,18.6 25,18.6 18,22 L14,22 "
         "C11,21 8,22 6.6,23 C5,25 3,26 1.4,25.6 C0,25 -0.4,23 0.4,21 C2,17 5,13 8,11 C11,9 13,7 16,6 Z")
GAUNT_LEGS = "M14,21 L13,33 M18,21.6 L19,33 M40,21 L38.6,26 L40,33 M42.6,19 L43.4,26 L42.6,33"
GAUNT_HORNS = "M8.6,10.4 C5,5 1,3 -4,3.6 M9.6,10 C12,5 15,3 19,2.6 M42,8 C45,13 45,20 44,28"
GAUNT_BONES = ("M21,10 C20,13 20,17 21,20 M24.5,9.4 C23.5,13 23.5,16 24.5,19 M28,9 C27,12 27,15 28,18.6 "
               "M31.5,8 C30.6,11 30.6,14 31.5,18.4 M37,5 L34,10")


def gaunt(d: Drawing, x: float, base: float, k: float):
    """A starved steer against the light, its hooves on `base`: a dark shape with the ribs and hip bones showing
    pale through it."""
    y = base - 33 * k
    body = place(GAUNT, x, y, k)
    d.line(place(GAUNT_LEGS, x, y, k), w=1.2)
    d.line(place(GAUNT_HORNS, x, y, k), w=1.4)
    d.shape(body, w=1.3)
    d.hatch(body, angle=45, pitch=0.9, cross=True)
    d.line(place(GAUNT_BONES, x, y, k), w=0.9, halo=False, color=PAPER)


def die_up_of_86() -> Drawing:
    d = Drawing("die-up-of-86")
    # The sun low on the western desert's edge, the sky about it hatched, and the parched plain.
    sun = "M22,62 C22,44 35,34 50,34 C65,34 78,44 78,62 Z"
    d.hatch("M2,12 L94,12 L94,62 L2,62 Z " + sun, angle=0, pitch=2.4, w=0.5)
    d.shape(sun, w=1.3)
    d.line("M2,62 L94,62", w=1.0)
    # The poor cattle trailing across the sun in a file.
    gaunt(d, 2, 64, 0.56)
    gaunt(d, 32, 64, 0.8)
    gaunt(d, 68, 64, 0.56)
    # A skull on the plain before them.
    skull = place("M-5,-6 C-5,-9.6 5,-9.6 5,-6 L3,4 C2,7 -2,7 -3,4 Z", 28, 82, 1.0)
    d.shape(skull, w=1.1)
    d.dots([(26, 75.6), (30, 75.6)], r=1.0)
    d.line("M23,76 C18,75 16,72 16,69 M33,76 C38,75 40,72 40,69", w=1.1)
    d.ground(2, 94, 89, ticks=6, seed=984)
    grass(d, [(58, 88), (80, 88)], h=3)
    return d


SUBJECTS = {
    "rodeo-wall": rodeo_wall,
    "girl-taken-away": girl_taken_away,
    "wolves-dream": wolves_dream,
    "las-varas-lumber": las_varas_lumber,
    "corralitos-slagheaps": corralitos_slagheaps,
    "die-up-of-86": die_up_of_86,
}
