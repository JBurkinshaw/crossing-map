"""Vignettes of the fifth round: Billy's last journey south (J7), from the border gate at Columbus to the
old man laid out at Namiquipa (Part IV, episodes 4-01 to 4-04). Loaded by art/vignettes/make_vignettes.py.

Each is checked against the episode that first shows it. The riders and horses are the traced Muybridge plate
(rider-annie-g, public domain) through the Parts III and IV helpers. No public-domain reference was found for the
rest, so it is drawn by hand from the book's description, as each seed `credit` says. Light from the north-west,
as everywhere: shade on each shape's south-east side.
"""

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly
from art.vignettes.subjects_parts_3_4 import rider
from art.vignettes.subjects_round3 import figure, horse
from art.vignettes.subjects_round4 import water

# A blanket worn over the shoulders like a poncho, in the traced rider's units (his head is about (51, 21)).
BLANKET = "M48,23 C45,24 42,30 40,40 C46,42 54,42 60,40 C58,30 56,24 53,23 Z"


def blanket(d: Drawing, w: float = 1.1):
    """An `extra` for `rider`: the dark wool blanket over his shoulders, two pale stripes across it."""
    def draw(t):
        d.shape(t(BLANKET), w=w)
        d.hatch(t(BLANKET), angle=80, pitch=1.2)
        d.line(t("M42,33 C48,34.4 54,34.4 58.6,33 M41.4,36.4 C48,38 54,38 59.2,36.4"), w=1.0, color=PAPER, halo=False)
    return draw


# 1. The ragged rider waved through the gate at Columbus (4-01) -----------------------------------------
def ragged_rider_at_gate() -> Drawing:
    d = Drawing("ragged-rider-at-gate")
    # The border fence running off behind the crossing.
    d.line("M2,58 L94,56", w=0.6, halo=False)
    d.line(" ".join(f"M{x},{49 - x * 0.02:.1f} L{x},{58 - x * 0.02:.1f}" for x in (40, 54, 68, 82)), w=1.0)
    d.line("M36,51.6 L94,50.4 M36,54.4 L94,53.2", w=0.5, halo=False)
    # The gateshack: a board hut under a shed roof, its window, and the guard out at the door waving him on.
    hut = poly((4, 86), (4, 36), (30, 32), (30, 86))
    d.shape(hut)
    d.shape(poly((1, 37), (33, 31.6), (33, 28), (1, 33.6)), w=1.3)
    win = poly((9, 44), (25, 42), (25, 54), (9, 56))
    d.shape(win, w=1.1)
    d.hatch(win, angle=45, pitch=1.4)
    d.line(" ".join(f"M{x},{36 - (x - 4) * 0.15:.1f} L{x},86" for x in range(8, 30, 5)), w=0.4, halo=False)
    d.edge_shade(hut, dx=-3, dy=0)
    p = figure(d, 38, 88, 30, flip=True)
    d.line(p("M-2.6,-16.6 L-6,-20 L-7,-27"), w=1.2)
    d.line(p("M-9,-28 l-1.4,-1 M-7.6,-29.6 l0,-1.6 M-5.6,-29 l1.2,-1.2"), w=0.6, halo=False)
    # Billy halted at the gate, the blanket over his shoulders.
    rider(d, 72, 88, 0.56, flip=True, hat="low", extra=blanket(d))
    d.ground(2, 94, 89, ticks=6, seed=800)
    return d


# 2. The flooded salt flats red with the sunset, and the horse that will not go (4-01) ------------------
def lake_of_blood() -> Drawing:
    d = Drawing("lake-of-blood")
    # Gillespie Mountain and the Animas Peaks under snow, the snow left white on their tops.
    peaks = "M48,44 L58,30 L64,34 L72,22 L80,30 L86,26 L94,34"
    d.line(peaks + " L94,44", w=1.1)
    d.hatch("M48,44 L54,36 L60,36 L64,38 L72,32 L80,36 L86,34 L94,38 L94,44 Z", angle=70, pitch=2.0, w=0.6)
    # The sun going down in the west, half under the far shore.
    d.shape("M10,44 C10,36 26,36 26,44 Z", w=1.2)
    d.line("M18,32 l0,-6 M9,36 l-4,-3 M27,36 l4,-3 M4,42 l-3,0 M32,42 l3,0", w=0.8, halo=False)
    d.line("M2,44 L94,44", w=1.0)
    # Water standing on the flats as far as can be seen, dark with the red light, the sun's path across it.
    lake = "M2,44.6 L94,44.6 L94,64 C70,65 40,65 2,64 Z"
    d.hatch(lake, angle=0, pitch=1.2, w=0.9)
    for y, w in ((47, 7), (49.6, 6), (52.4, 5), (55.4, 4), (58.6, 3), (61.6, 2.4)):
        d.line(f"M{18 - w},{y} L{18 + w},{y}", w=1.6, color=PAPER, halo=False)
    d.line("M2,64 C40,65 70,65 94,64", w=1.0)
    # Billy at the near edge, on the bare salt ground, the horse balked at the water.
    rider(d, 64, 90, 0.4, flip=True, hat="cowboy", extra=blanket(d))
    d.line("M6,72 l10,0 M26,78 l8,0 M10,84 l12,0 M84,74 l8,0", w=0.6, halo=False)
    d.ground(2, 94, 91, ticks=6, seed=801)
    return d


# 3. Asleep by the dead fire on the Animas Plain, lightning far off over Mexico (4-02) -----------------
def lightning_over_mexico() -> Drawing:
    d = Drawing("lightning-over-mexico")
    d.dots([(8, 8), (20, 16), (34, 6), (46, 18), (30, 26), (12, 30), (88, 8), (56, 10)], r=0.6)
    # The Hatchet Mountains low on the southern skyline, and the lightning beyond them.
    hills = "M2,52 C8,48 14,46 20,48 L30,42 L38,46 L46,40 L56,46 C66,44 80,46 94,50"
    d.line(hills, w=1.0)
    d.hatch(hills + " L94,54 L2,54 Z", angle=70, pitch=2.4, w=0.6)
    d.line("M74,8 L68,20 L74,19 L64,34 L70,33 L62,44", w=1.5)
    d.line("M68,20 L60,26 M70,33 L76,40", w=0.8)
    # The grass running in the wind.
    d.line("M2,60 C30,58 60,58 94,57", w=0.7, halo=False)
    d.line("M10,64 l6,-2 M30,62 l6,-2 M54,63 l7,-2 M80,62 l6,-2 M20,70 l7,-2.4 M44,68 l7,-2.4", w=0.6, halo=False)
    # The hobbled horse cropping the grass.
    f = horse(d, 76, 84, 0.36, saddle=False, graze=0.8)
    d.line(f"M{f(66, 89)[0]:.1f},{f(66, 89)[1] - 1:.1f} L{f(74, 89)[0]:.1f},{f(74, 89)[1] - 1:.1f}", w=0.9)
    # Billy asleep on the ground rolled in the serape and blanket, and the dead fire: a few sticks, no flame.
    roll = "M8,86 C6,80 10,76 16,76 L44,76 C50,76 54,80 52,86 Z"
    d.shape(roll, w=1.5)
    d.hatch(roll, angle=0, pitch=1.8)
    d.shape(circle(10, 74, 3), w=1.1)
    d.shape("M4,75 C6,70 14,70 16,73 C12,74 8,74 4,75 Z", w=1.0)
    d.line("M54,88 L64,85 M55,85 L64,88", w=1.3)
    d.dots([(58, 86.6), (61, 86.4)], r=0.5)
    d.ground(2, 94, 88, ticks=6, seed=802)
    return d


# 4. The Hashknife linecamp on the Little Colorado (4-02) ----------------------------------------------
def hashknife_linecamp() -> Drawing:
    d = Drawing("hashknife-linecamp")
    # The bare plain beyond the river, flat to the skyline.
    d.line("M2,40 C30,39 60,39 94,38", w=0.8)
    d.line("M60,36 C66,32 76,32 82,36", w=0.7, halo=False)
    # The camp: a board shack under a gable, its stovepipe smoking, and a pole corral beside it.
    shack = poly((14, 66), (14, 44), (30, 34), (46, 44), (46, 66))
    d.shape(shack)
    d.line("M10,46 L30,32 L50,46", w=1.6)
    d.line(" ".join(f"M{x},{44 - min(x - 14, 46 - x) * 10 / 16:.1f} L{x},66" for x in range(18, 46, 4)), w=0.4,
           halo=False)
    door = poly((26, 66), (26, 52), (33, 52), (33, 66))
    d.shape(door, w=1.1)
    d.hatch(door, angle=45, pitch=1.3, cross=True)
    d.edge_shade(shack, dx=-3, dy=0)
    d.line("M40,40 L40,32", w=1.4)
    d.line("M40,30 C38,26 42,24 40,20 C38,16 44,14 46,10", w=0.7, halo=False)
    d.line("M52,64 L92,64 M52,58 L92,58 M52,52 L92,52", w=0.8)
    d.line(" ".join(f"M{x},50 L{x},66" for x in (52, 66, 80, 92)), w=1.3)
    horse(d, 72, 66, 0.26, saddle=False, graze=0.3)
    # The river running past below the camp.
    water(d, 76, seed=3)
    d.line("M2,90 C30,89 60,89 94,88", w=0.8)
    d.line("M6,84 l14,0 M44,86 l18,0 M74,83 l12,0", w=0.6, halo=False)
    return d


# 5. Riding south across the Plains of San Agustín with the packhorse (4-02) ---------------------------
def plains_of_saint_augustine() -> Drawing:
    d = Drawing("plains-of-saint-augustine")
    # The ranges low and far on every side of the plain.
    far = "M2,50 L10,46 L16,48 L24,44 L30,48 C40,49 52,49 60,48 L68,44 L74,46 L82,42 L94,46"
    d.line(far, w=0.9)
    d.hatch(far + " L94,50 L2,50 Z", angle=70, pitch=2.2, w=0.5)
    d.line("M2,52 C30,51 60,51 94,52", w=0.7, halo=False)
    # Billy small on the open grass, leading the packhorse.
    horse(d, 28, 76, 0.3, saddle=False, pack=True)
    d.line("M40,64 C46,66 54,64 62.6,58.8", w=0.6, halo=False)
    rider(d, 60, 76, 0.32, hat="cowboy")
    # The grass running out flat to the skyline.
    grass(d, [(8, 88), (24, 90), (46, 89), (70, 90), (88, 88)], h=4)
    d.line("M6,60 l6,0 M76,58 l8,0 M14,68 l8,0 M80,66 l7,0 M40,80 l8,0 M60,82 l10,0", w=0.6, halo=False)
    d.ground(2, 94, 78, ticks=5, seed=804)
    return d


# 6. Christmas Day in Silver City: snow, and the horses fed on breakfast cereal behind the hotel (4-02) ----
def christmas_cereal() -> Drawing:
    d = Drawing("christmas-cereal")
    # The back wall of the hotel, its windows, and the yard's board fence.
    wall = poly((2, 50), (2, 6), (94, 6), (94, 50))
    d.shape(wall, w=1.4)
    d.line(" ".join(f"M2,{y} L94,{y}" for y in range(10, 50, 4)), w=0.4, halo=False)
    for x in (10, 40, 70):
        win = poly((x, 14), (x + 14, 14), (x + 14, 34), (x, 34))
        d.shape(win, w=1.2)
        d.hatch(win, angle=45, pitch=1.4)
        d.line(f"M{x + 7},14 L{x + 7},34 M{x},24 L{x + 14},24", w=0.8, color=PAPER, halo=False)
    # The two horses, heads down to the boxes of cereal spilled on the snow.
    horse(d, 23, 86, 0.46, saddle=False, graze=0.8)
    horse(d, 73, 88, 0.46, flip=True, saddle=False, graze=0.8)
    for x, y in ((35, 88), (54, 89)):
        box = poly((x, y), (x + 6, y - 1), (x + 7.4, y - 10), (x + 1.4, y - 9))
        d.shape(box, w=1.1)
        d.line(f"M{x + 1.4},{y - 9} l-1,-3 M{x + 7.4},{y - 10} l2,-2.4", w=0.8)
        d.line(f"M{x + 2},{y - 5} l3.6,-0.6", w=0.6, halo=False)
    d.dots([(44, 88), (46, 87), (49, 88.6), (51, 87.4)], r=0.5)
    # The snow falling.
    d.dots([(6, 56), (18, 60), (30, 54), (46, 58), (58, 62), (66, 54), (84, 58), (92, 62), (12, 70), (36, 66),
            (52, 70), (88, 70), (26, 46), (60, 44), (82, 42), (8, 40), (50, 30), (32, 20), (88, 22)], r=0.7)
    d.ground(2, 94, 88, ticks=5, seed=805)
    return d


# 7. Tacos from the woman at her brazier, at the Berrendo crossing (4-03) -----------------------------
def tacos_at_berrendo() -> Drawing:
    d = Drawing("tacos-at-berrendo")
    # The little mud street: a low adobe house behind.
    house = poly((4, 64), (4, 40), (50, 40), (50, 64))
    d.shape(house, w=1.4)
    d.line("M2,40 L52,40", w=1.6)
    d.line("M10,40 l-3,-1 M22,40 l-3,-1 M34,40 l-3,-1 M46,40 l-3,-1", w=0.9)
    door = poly((20, 64), (20, 48), (28, 48), (28, 64))
    d.shape(door, w=1.1)
    d.hatch(door, angle=45, pitch=1.3, cross=True)
    d.edge_shade(house, dx=-3, dy=0)
    # The woman sitting in the dust of the roadside under her rebozo, and the charcoal brazier beside her.
    shawl = "M6,88 C6,78 10,70 16,66 C18,64 22,64 24,66 C30,72 32,80 32,88 Z"
    d.shape(shawl, w=1.4)
    d.hatch(shawl, angle=60, pitch=1.6)
    d.shape(circle(19.6, 66, 3.4), w=1.1)
    d.shape("M14.6,67 C14,61 25,60 24.6,67 C22,64 17,64 14.6,67 Z", w=1.0)
    d.line("M28,78 L36,80", w=1.2)
    brazier = "M34,78 L52,78 C51,84 46,86 43,86 C40,86 35,84 34,78 Z"
    d.shape(brazier, w=1.4)
    d.edge_shade(brazier, dx=-1.6, dy=-1.6)
    d.line("M38,85 L36,90 M48,85 L50,90", w=1.1)
    d.dots([(38, 77), (41, 76.4), (44, 76.8), (47, 76.2), (50, 77)], r=0.8)
    d.line("M42,72 C40,66 46,62 43,56 M46,72 C45,68 50,64 48,58", w=0.6, halo=False)
    # Billy riding on south with a taco in his hand.
    def taco(t):
        d.shape(t("M57,36 C58,31 63,30 64,34 Z"), w=0.9)
    rider(d, 74, 88, 0.48, flip=True, hat="cowboy", extra=taco)
    d.ground(2, 94, 90, ticks=6, seed=806)
    return d


# 8. The tall mud church at Janos and its old Spanish bells on a trestlepole (4-03) --------------------
def janos_bells() -> Drawing:
    d = Drawing("janos-bells")
    d.dots([(70, 8), (84, 14), (92, 6), (60, 18), (76, 24), (88, 30), (8, 6)], r=0.6)
    # The church: a tall plain front of mud with a stepped top, its door, and one small window above.
    church = "M8,88 L8,24 L14,24 L14,18 L22,18 L22,10 L34,10 L34,18 L42,18 L42,24 L48,24 L48,88 Z"
    d.shape(church)
    d.edge_shade(church, dx=-3.5, dy=0)
    door = "M22,88 L22,66 C22,60 34,60 34,66 L34,88 Z"
    d.shape(door, w=1.3)
    d.hatch(door, angle=45, pitch=1.3, cross=True)
    d.shape(circle(28, 34, 3), w=1.1)
    d.hatch(circle(28, 34, 3), angle=45, pitch=1.0)
    d.line("M12,46 l4,0.6 M38,56 l4,-0.4 M14,76 l3,0.4 M40,30 l3,0.4", w=0.6, halo=False)
    # The trestlepole in the churchyard: two posts and a beam, the green bells hung from it, one large and two
    # small.
    d.line("M58,88 L60,40 M90,88 L88,40", w=1.8)
    d.line("M54,42 L94,40", w=2.0)
    for x, r in ((68, 6), (80, 4.4)):
        top = 41.4
        bell = (f"M{x - r * 0.5},{top + 2} C{x - r * 0.5},{top - 1} {x + r * 0.5},{top - 1} {x + r * 0.5},{top + 2} "
                f"C{x + r * 0.6},{top + r * 1.2} {x + r},{top + r * 1.6} {x + r * 1.2},{top + r * 2} "
                f"L{x - r * 1.2},{top + r * 2} C{x - r},{top + r * 1.6} {x - r * 0.6},{top + r * 1.2} {x - r * 0.5},"
                f"{top + 2} Z")
        d.shape(bell, w=1.3)
        d.hatch(bell, angle=45, pitch=1.2)
        d.dots([(x, top + r * 2 + 1.4)], r=0.9)
    d.ground(2, 94, 89, ticks=6, seed=807)
    return d


# 9. Alfonso with his shirt torn open on his three scars, in the cantina at Janos (4-03) ----------------
def alfonsos_scars() -> Drawing:
    d = Drawing("alfonsos-scars")
    # The single shaded bulb over the table.
    d.line("M48,0 L48,6", w=0.9)
    d.shape("M41,13 L45,6 L51,6 L55,13 Z", w=1.2)
    d.line("M38,18 l-4,3 M58,18 l4,3 M48,18 l0,3", w=0.6, halo=False)
    # Alfonso slouched in his chair, his shirt pulled wide open in his fists on the bare chest.
    body = "M14,74 C14,56 22,46 36,44 L60,44 C74,46 82,56 82,74 Z"
    d.shape(body)
    d.hatch(body, angle=60, pitch=1.6)
    chest = "M40,44 C36,52 33,60 34,74 L62,74 C63,60 60,52 56,44 Z"
    d.shape(chest, w=1.4)
    d.line("M40,44 C36,46 32,52 28,58 M56,44 C60,46 64,52 68,58", w=1.0)
    for x in (31, 65):
        fist = circle(x, 60, 4.4)
        d.shape(fist, w=1.3)
        d.line(f"M{x - 2.6},58.4 l5.2,0 M{x - 2.6},61 l5.2,0", w=0.6, halo=False)
    # The three bullet scars set in a triangle over his heart, each a puckered pit.
    for x, y in ((51, 52), (57, 52), (54, 58)):
        d.dots([(x, y)], r=1.3)
        d.line(f"M{x - 2.4},{y} l-1,0 M{x + 2.4},{y} l1,0 M{x},{y - 2.4} l0,-1 M{x},{y + 2.4} l0,1", w=0.6,
               halo=False)
    # His head sunk on his chest: black hair, heavy-lidded eyes.
    head = ellipse(48, 34, 8, 9.4)
    d.shape(head, w=1.4)
    d.shape("M39.6,32 C39,24 43,23 48,23 C53,23 57,24 56.4,32 C54,27 44,27 39.6,32 Z", w=1.0)
    d.hatch("M39.6,32 C39,24 43,23 48,23 C53,23 57,24 56.4,32 C54,27 44,27 39.6,32 Z", angle=80, pitch=0.9)
    d.line("M42.6,35 l3.6,0.4 M49.8,35.4 l3.6,-0.4 M45.6,40.6 l5,0", w=1.1, halo=False)
    d.line("M48,36 l-1,3", w=0.6, halo=False)
    # The table edge, the stopperless bottle of mescal and the glasses.
    d.shape(poly((0, 96), (0, 74), (96, 74), (96, 96)), w=1.6)
    d.hatch(poly((0, 96), (0, 80), (96, 80), (96, 96)), angle=0, pitch=2.0)
    bottle = "M76,74 L76,62 C76,58 79,57 80,54 L80,48 L83,48 L83,54 C84,57 87,58 87,62 L87,74 Z"
    d.shape(bottle, w=1.3)
    d.hatch("M76,74 L76,68 L87,68 L87,74 Z", angle=0, pitch=1.0)
    for x in (8, 18):
        d.shape(poly((x, 74), (x - 1, 64), (x + 7, 64), (x + 6, 74)), w=1.1)
    return d


# 10. The old man laid out on his coolingboard at Namiquipa (4-04) -------------------------------------
def old_man_on_coolingboard() -> Drawing:
    d = Drawing("old-man-on-coolingboard")
    # The bare room: the far wall, one small window high in it, and the candle burning in a dish.
    d.line("M2,60 L94,60", w=0.9)
    win = poly((62, 14), (74, 14), (74, 24), (62, 24))
    d.shape(win, w=1.2)
    d.hatch(win, angle=45, pitch=1.3)
    d.shape("M80,58 C80,55 92,55 92,58 Z", w=1.0)
    d.shape(poly((84.4, 56), (84.4, 46), (87.6, 46), (87.6, 56)), w=1.0)
    d.shape("M86,45 C84,42 86,39 86,36 C88,39 88,42 86,45 Z", w=0.9)
    d.line("M86,32 l0,-3 M80,40 l-3,-1.4 M92,40 l3,-1.4", w=0.6, halo=False)
    # The trestle, and the old man on it in his small dark suit, hands crossed on his chest, his bare feet tied.
    d.shape(poly((6, 64), (6, 60), (78, 60), (78, 64)), w=1.4)
    d.line("M12,64 L8,84 M12,64 L18,84 M70,64 L66,84 M70,64 L76,84", w=1.4)
    # His head in profile on the board, face up: silver hair, the nose, the moustache.
    head = ("M6,60 C4,56 5,52 8,50.4 L12,49.6 L14,46 L15.6,49.6 L17.4,50.2 C19,50.6 20,52 20.4,54 L20,60 Z")
    d.shape(head, w=1.3)
    d.line("M5.6,55 C6.4,53 7.4,52 9,51.4 M5.4,58 C6,56.4 7,55.4 8.4,54.8", w=0.6, halo=False)
    d.line("M15.2,50.2 L18.4,51.4", w=1.4)
    # The small old suit, the broad hands crossed on his chest, and the bare feet tied at the toes.
    suit = "M18,60 L19,53 C22,50 28,49 32,50 L58,53 L60,60 Z"
    d.shape(suit, w=1.4)
    d.hatch(suit, angle=45, pitch=1.4)
    hands = "M28,50.6 C29,46 35,45 37,48 C38,50 36,52 34,52 Z"
    d.shape(hands, w=1.2)
    d.line("M31,48.4 l3,2", w=0.6, halo=False)
    feet = "M58,60 L58.4,52 C58.6,49 62,48 63.6,50 L64,60 Z"
    d.shape(feet, w=1.2)
    d.line("M58.4,51.4 L63.6,51.4", w=0.9, halo=False)
    # The wildflowers about him on the board and the floor.
    for x, y in ((24, 59), (52, 59), (60, 59), (30, 88), (44, 90), (58, 88), (84, 90)):
        d.line(f"M{x},{y} l-1.6,-1 M{x},{y} l1.6,-1 M{x},{y} l0,-1.8 M{x},{y} l-1.4,1.2 M{x},{y} l1.4,1.2", w=0.6,
               halo=False)
        d.dots([(x, y)], r=0.6)
    d.ground(2, 94, 92, ticks=5, seed=809)
    return d


SUBJECTS = {
    "ragged-rider-at-gate": ragged_rider_at_gate,
    "lake-of-blood": lake_of_blood,
    "lightning-over-mexico": lightning_over_mexico,
    "hashknife-linecamp": hashknife_linecamp,
    "plains-of-saint-augustine": plains_of_saint_augustine,
    "christmas-cereal": christmas_cereal,
    "tacos-at-berrendo": tacos_at_berrendo,
    "janos-bells": janos_bells,
    "alfonsos-scars": alfonsos_scars,
    "old-man-on-coolingboard": old_man_on_coolingboard,
}
