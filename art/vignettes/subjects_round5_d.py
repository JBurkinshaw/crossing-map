"""Vignettes of the fifth round: the brothers' second ride into Mexico (J4), from Apache Pass and the
border road through Bacerac and the escarpment to the loss of the horses on the Boquilla road. Each is set at its
stop or at a point along its leg (decision 0066). Loaded by art/vignettes/make_vignettes.py.

Each is checked against the episode that first shows it. The riders and horses are the traced Muybridge plate
(rider-annie-g, public domain) through the Parts III and IV helpers, with Boyd drawn on behind his brother by hand.
The dog is the traced US Fish and Wildlife Service wolf outline made small, as at the gate in Part I. Everything
else, the seated and squatting people included, is drawn by hand from the book. Light from the north-west, as
everywhere: shade on each shape's south-east side.
"""

import math

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, warp
from art.vignettes.subjects_parts_1_2 import wolf
from art.vignettes.subjects_parts_3_4 import cottonwood, place, rider
from art.vignettes.subjects_round3 import chevrons, figure, fire, horse
from art.vignettes.subjects_round4 import water


def boy_behind(d: Drawing, t):
    """Boyd riding double behind the rider (traced units): a thin boy in a hat, his legs dangling on the flank."""
    body = "M37.6,29 C38.6,26.6 43,26 45,27.6 L46,38 L46.6,44 L36.6,45 L37.4,38 Z"
    d.shape(t(body), w=1.2)
    d.shape(t("M38.4,23 C38.4,20 40.6,18.8 42.6,19.8 C44.2,20.8 44.2,24.2 42.2,25.2 C40.2,26 38.4,25.2 38.4,23 Z"),
            w=1.0)
    d.shape(t("M35,20.4 C38,19 45,19 48,20.4 C45,21.8 38,21.8 35,20.4 Z"), w=1.0)
    d.shape(t("M38.4,20.2 C38.4,16.6 39.6,15 41.6,15 C43.6,15 44.8,16.6 44.8,20.2 Z"), w=1.0)
    d.line(t("M39,44 C38.4,50 38,55 39.4,60 M44,44 C44,49 43.4,53 44.6,57"), w=1.0)


def doubled(d: Drawing, ox: float, oy: float, k: float, flip: bool = False):
    """The brothers riding double on one horse."""
    return rider(d, ox, oy, k, flip=flip, extra=lambda t: boy_behind(d, t))


def dog(d: Drawing, x: float, y: float, k: float = 0.22, flip: bool = False):
    """The brothers' dog: the traced wolf outline made small, as at the gate in Part I. Origin top left."""
    wolf(d, k, x, y, flip=flip, w=1.1)


def sitter(d: Drawing, x: float, y: float, k: float, flip: bool = False, squat: bool = False, straw: bool = False,
           arm: str | None = None):
    """A person sitting on the ground with knees drawn up (or squatting on his heels), facing east, seat at
    (x, y), about 24 units tall before k. `arm` replaces the near arm. Returns the place transform for more detail."""
    def p(path: str) -> str:
        return place(path, x, y, k, flip)
    if squat:
        torso = "M-5,-4 C-5,-10 -3,-15 0,-18 L3.6,-16.6 C3,-12 1.4,-7 0,-3 Z"
        legs, arm_, (hx, hy) = "M-2,-4 L6,-12 L5,0 L8.4,0", "M2,-15 L6,-10 L10,-6", (2.8, -20.8)
    else:
        torso = "M-5,-1 C-6,-6 -5,-12 -3,-15 L1,-15 C1.6,-11 1,-6 0,-1 Z"
        legs, arm_, (hx, hy) = "M-1,-2 L7,-10 L9,0 L12,0", "M-1,-13 L3,-9 L6.6,-9", (-1.4, -18)
    d.shape(p(torso), w=1.3)
    d.edge_shade(p(torso), dx=-1.2, dy=-1.2)
    d.line(p(legs), w=2.0)
    d.line(p(arm_ if arm is None else arm), w=1.3)
    d.shape(p(circle(hx, hy, 2.6)), w=1.1)
    brim = 6.4 if straw else 4.8
    hat = (f"M{hx - brim},{hy - 1.6} L{hx + brim},{hy - 1.6} L{hx + 2.4},{hy - 2.6} C{hx + 2.4},{hy - 6} "
           f"{hx - 2.4},{hy - 6} {hx - 2.4},{hy - 2.6} Z")
    d.shape(p(hat), w=1.0)
    if not straw:
        d.hatch(p(hat), angle=0, pitch=0.9)
    return p


# 1. The brothers riding double through Apache Pass, ravens on the updrafts (2-07) -----------------------
def apache_pass_ravens() -> Drawing:
    d = Drawing("apache-pass-ravens")
    # The high gap: mountain shoulders either side, the country falling away south to a far line where the
    # colour changes.
    left = "M-2,70 L-2,30 L8,24 L16,30 L24,22 L34,34 L40,48 L46,62 L48,70 Z"
    right = "M98,66 L98,22 L88,16 L78,24 L70,30 L64,44 L60,58 L58,66 Z"
    for m in (left, right):
        d.shape(m, w=1.5)
    d.hatch(left, angle=70, pitch=2.4, w=0.6)
    d.edge_shade(right, dx=3, dy=-3, cross=False)
    d.line("M40,58 C46,57 54,57 62,58", w=0.8)
    d.hatch("M40,58 C46,57 54,57 62,58 L62,61 L40,61 Z", angle=0, pitch=1.4, w=0.6)
    # Ravens riding the updrafts over the south-facing slopes.
    d.line(" ".join(f"M{x - 4},{y - 1} Q{x - 2},{y - 3} {x},{y} Q{x + 2},{y - 3} {x + 4},{y - 1}"
                    for x, y in ((50, 14), (60, 22), (38, 8), (72, 10))), w=1.4)
    # Billy with Boyd up behind him, looking over the country to the south.
    doubled(d, 42, 92, 0.52)
    d.ground(2, 94, 92, ticks=6, seed=650)
    return d


# 3. The storm driving the doves, the brothers sheltering in roadside trees (2-07) -----------------------
def storm_and_doves() -> Drawing:
    d = Drawing("storm-and-doves")
    # Blue mountains far off under the cloud, thin wires of lightning standing over them.
    d.line("M2,40 L10,34 L18,38 L28,30 L38,38 L46,34 L56,40", w=1.0)
    d.line("M20,12 L17,22 L21,22 L16,32 M40,14 L42,22 L38,24 L41,34", w=0.8)
    d.hatch("M2,2 L62,2 L62,10 C44,14 22,14 2,10 Z", angle=0, pitch=1.6, w=0.6)
    # The rain coming across the desert in a wall, flights of doves driven before it.
    d.hatch("M2,42 L30,42 L18,90 L2,90 Z", angle=-70, pitch=2.0, w=0.7)
    chevrons(d, [(38, 52, 1.0), (46, 48, 0.9), (44, 58, 0.9), (54, 54, 0.8), (36, 64, 0.8), (52, 62, 0.8)])
    # The grove of roadside trees, and the boys standing under them holding the horse.
    cottonwood(d, 86, 70, 46, 24, seed=651)
    cottonwood(d, 66, 66, 36, 20, seed=652)
    horse(d, 76, 90, 0.34, saddle=True, graze=0.6)
    figure(d, 58, 91, 24, flip=True)
    figure(d, 50, 91, 20, flip=True)
    d.line("M58.6,76 C64,74 70,72 76,70", w=0.7, halo=False)
    d.ground(2, 94, 91, ticks=7, seed=653)
    return d


# 4. The old man drawing the country in the dust of the square at Bacerac (2-08) -------------------------
def dust_map() -> Drawing:
    d = Drawing("dust-map")
    # Their horse standing in the street, which the old man squints at to reckon the hours.
    horse(d, 74, 44, 0.3)
    d.line("M2,46 C30,45 60,45 94,44", w=0.8)
    # The map scratched in the dirt, about the size of a blanket: ranges, a stream, pueblos, a tree, a cloud,
    # a bird, and the two horsemen doubled on their mount.
    d.line("M24,64 L28,60 L31,63 L35,58 L39,63 M52,60 L55,57 L58,60 L61,56 L65,61", w=0.9, halo=False)
    d.line("M22,76 C30,70 38,78 46,72 C54,66 60,74 70,68", w=0.9, halo=False)
    d.line("M44,64 l3,0 l0,-2.4 l-3,0 Z M58,78 l3,0 l0,-2.4 l-3,0 Z M30,80 l3,0 l0,-2.4 l-3,0 Z", w=0.7,
           halo=False)
    d.line("M70,78 l0,-4 M68,74 C68,70 72,70 72,74 Z", w=0.7, halo=False)
    d.line("M40,54 C40,52 44,52 44,54 C45,52 48,53 47,55 L40,55 Z M60,52 q1.4,-1.4 2.6,0 q1.4,-1.4 2.6,0", w=0.7,
           halo=False)
    d.line("M48,82 l2,-3 l3,0 l1,3 M50,79 l0,-2 l1.4,0", w=0.7, halo=False)
    d.line("M18,86 C30,90 64,90 80,86", w=0.6, halo=False)
    # The thin old man squatting with his whittled stick, and the two brothers sitting opposite.
    p = sitter(d, 10, 88, 1.3, squat=True)
    d.line(p("M10,-6 L15,1"), w=1.0)
    sitter(d, 90, 88, 1.15, flip=True)
    sitter(d, 72, 91, 1.05, flip=True)
    d.ground(2, 94, 91, ticks=6, seed=654)
    return d


# 5. The brothers on the eastern rim of the escarpment as the sun comes up out of the plains (2-08) -----
def sunrise_on_the_rim() -> Drawing:
    d = Drawing("sunrise-on-the-rim")
    # The sun swelling up out of the plains of Chihuahua, far below to the east.
    d.line("M40,52 C60,51 80,51 96,52", w=0.9)
    sun = "M58,52 C58,40 84,40 84,52 Z"
    d.shape(sun, w=1.4)
    d.line(" ".join(f"M{71 + 16 * math.cos(a):.1f},{52 - 16 * math.sin(a):.1f} "
                    f"L{71 + 24 * math.cos(a):.1f},{52 - 24 * math.sin(a):.1f}"
                    for a in (math.radians(v) for v in (10, 35, 60, 90, 120, 145, 170))), w=0.9)
    d.line("M46,58 L94,58 M54,63 L94,63 M60,68 L94,68", w=0.5, halo=False)
    # The rim: a cliff edge dropping away on the right, the two riders sitting their horses on it.
    rim = "M-2,96 L-2,62 C10,60 30,60 42,62 L46,70 L50,74 L52,84 L56,96 Z"
    d.shape(rim, w=1.5)
    d.hatch("M42,62 L46,70 L50,74 L52,84 L56,96 L44,96 L42,80 L38,66 Z", angle=75, pitch=1.6)
    rider(d, 18, 62, 0.34)
    rider(d, 34, 64, 0.38)
    return d


# 6. The Tarahumara camp, the old man fiddling and the boy with his violin lowered (2-08) ----------------
def violin(d: Drawing, x: float, y: float, k: float, angle: float):
    """A homemade violin: a waisted body and its neck, centred on (x, y), rotated by angle degrees."""
    r = math.radians(angle)
    c, s = math.cos(r), math.sin(r)
    body = "M0,-4 C2.6,-4 2.6,-1.6 1.6,-0.6 C2.8,0.4 3,4 0,4 C-3,4 -2.8,0.4 -1.6,-0.6 C-2.6,-1.6 -2.6,-4 0,-4 Z"
    rot = lambda u, v: (x + (u * c - v * s) * k, y + (u * s + v * c) * k)  # noqa: E731
    d.shape(warp(body, rot), w=1.0)
    d.line(warp("M0,-4 L0,-10", rot), w=1.2)


def tarahumara_violins() -> Drawing:
    d = Drawing("tarahumara-violins")
    # The tree in the glade, their bundles and bows stood under it.
    cottonwood(d, 14, 66, 50, 26, seed=655)
    d.line("M24,66 L28,42 M27,66 L32,44", w=0.9)
    d.line("M28,42 C25,50 25,58 24,66 M32,44 C29,52 29,58 27,66", w=0.6, halo=False)
    d.line("M2,66 C10,66 20,66 40,66", w=0.7)
    # The cookfire.
    fire(d, 32, 88, 0.8)
    # The old man seated playing on, in breechclout and straw hat, the fiddle at his chin and the bow across it.
    p = sitter(d, 58, 90, 1.7, straw=True, arm="M-1,-13 L4,-11 L8.4,-15.4")
    violin(d, 60.4, 65.5, 1.5, angle=80)
    d.line(p("M-5,-10 L9,-21"), w=1.0)
    # The boy standing by him, his fiddle lowered.
    q = figure(d, 88, 90, 34, flip=True, hat=False, coat=False)
    d.shape(q("M-6,-22.4 L6,-22.4 L2.4,-23.4 C2.4,-26.6 -2.4,-26.6 -2.4,-23.4 Z"), w=0.9)
    d.line(q("M-1.6,-17 L1.6,-12.4 L5,-12"), w=1.0)
    violin(d, 84, 73, 1.3, angle=-100)
    d.line(q("M2,-16 L4,-9 M4,-9 L4.6,-2"), w=0.8)
    d.ground(2, 94, 89, ticks=6, seed=656)
    return d


# 7. The girl riding off alone down the narrow road east, Boyd left standing (3-03) ----------------------
def girl_rides_east() -> Drawing:
    d = Drawing("girl-rides-east")
    # Weather clouds over the south.
    cloud = ("M2,26 C2,18 10,14 16,18 C18,8 30,6 36,14 C42,6 56,8 58,16 C64,10 76,12 78,20 C84,16 94,20 94,26 Z")
    d.shape(cloud, w=1.1)
    d.hatch("M2,26 C2,22 30,20 50,22 C70,20 94,22 94,26 Z", angle=-30, pitch=1.6)
    # The narrow dirt road running off east.
    d.line("M2,88 C30,80 60,70 94,62 M2,96 C34,88 66,76 94,66", w=0.9)
    # The girl bareback, her dark hair down her back, riding away east.

    def girl(t):
        d.shape(t("M46,22 C44,26 43,32 44,37 L49,36 C48,31 49,27 50,23 Z"), w=1.0)
        d.hatch(t("M46,22 C44,26 43,32 44,37 L49,36 C48,31 49,27 50,23 Z"), angle=80, pitch=0.9)
        d.line(t("M41,44 C38,50 38,55 40,59"), w=0.9, halo=False)
    rider(d, 62, 74, 0.42, hat="none", extra=girl)
    # Boyd standing in the road watching her go.
    figure(d, 18, 92, 26)
    return d


# 8. Their own horses coming up wet from the laguna onto the road (3-04) --------------------------------
def horses_from_the_laguna() -> Drawing:
    d = Drawing("horses-from-the-laguna")
    # The high-country laguna below the road.
    # The road along the top of the bank, and the two young riders hazing the horses up onto it.
    d.line("M2,52 C30,51 60,51 94,50", w=0.9)
    rider(d, 80, 52, 0.22, flip=True)
    # Niño, Bailey and Tom clambering up out of the laguna still dripping, heads up.
    d.line("M-2,80 C20,78 34,70 50,62 C60,58 80,56 98,56", w=1.0)
    horse(d, 66, 58, 0.3, saddle=False, graze=-0.2)
    horse(d, 44, 74, 0.34, saddle=False, graze=-0.3)
    horse(d, 20, 92, 0.38, saddle=False, graze=-0.2)
    # The laguna round the last one's legs.
    for y in range(84, 96, 2):
        d.line(f"M-2,{y} L50,{y}", w=1.5, color=PAPER, halo=False)
    water(d, 84, x0=2, x1=50, seed=3)
    d.line(" ".join(f"M{x},{y} l0,2.4" for x, y in ((14, 72), (22, 74), (30, 73), (38, 58), (46, 60), (52, 57),
                                                     (60, 46), (68, 47))), w=0.6, halo=False)
    return d


# 9. The one-armed man at the head of the riders in the road (3-04) --------------------------------------
def one_armed_man() -> Drawing:
    d = Drawing("one-armed-man")
    d.line("M2,50 C30,49 60,49 94,48", w=0.8)
    # The other riders strung across the road behind him, rifles across their saddle bows.

    def rifle(t):
        d.line(t("M38,42 L72,30"), w=1.2)
    for x in (12, 32, 74, 92):
        rider(d, x, 52, 0.2, flip=True, extra=rifle)
    # The older man: right sleeve pinned to his shoulder, reins tied, a pistol at his belt, a plain flat-crowned
    # hat, tooled boots to the knee.
    f = horse(d, 50, 92, 0.5, flip=True)

    def t(path):
        return warp(path, f)
    torso = "M45,24 C46,22 54,22 56,24 L57,38 L45,39 Z"
    d.shape(t(torso), w=1.3)
    d.edge_shade(t(torso), dx=1.6, dy=-1.6)
    d.shape(t("M49,25 C51,24 54,25 54,28 C53,30 50,30 49,29 Z"), w=0.9)
    d.line(t("M50,26 l3,2 M50,28 l2,-1"), w=0.6, halo=False)
    d.shape(t(circle(51, 18.6, 3.6)), w=1.1)
    d.shape(t("M42.4,15.2 L59.6,15.2 L59.6,16.4 L42.4,16.4 Z"), w=1.1)
    d.shape(t("M46.4,15.2 L46.4,10.4 L55.6,10.4 L55.6,15.2 Z"), w=1.1)
    d.hatch(t("M46.4,15.2 L46.4,10.4 L55.6,10.4 L55.6,15.2 Z"), angle=0, pitch=0.9)
    d.shape(t("M53,36 L58,36 L58.6,41 L55.6,41 Z"), w=0.9)
    d.line(t("M48,38 C52,41 56,43 56.5,47 L53,58 L57,59"), w=1.3)
    d.hatch(t("M54,47 L57,47.6 L54.6,58.6 L52,58 Z"), angle=45, pitch=0.9)
    d.ground(2, 94, 93, ticks=6, seed=659)
    return d


# 10. Back west along the road, doubled on the one horse, the dog in its shadow (3-04) -------------------
def back_west_with_the_dog() -> Drawing:
    d = Drawing("back-west-with-the-dog")
    d.line("M2,62 C30,61 60,61 94,60", w=0.8)
    # The horse's shadow thrown on the road, and the dog trotting in it at the offside.
    shadow = "M20,88 C34,84 70,84 92,88 C72,94 36,94 20,88 Z"
    d.hatch(shadow, angle=0, pitch=1.4)
    # Boyd in front now, Billy up behind him, riding back west.
    doubled(d, 44, 86, 0.48, flip=True)
    dog(d, 56, 72, k=0.2, flip=True)
    d.ground(2, 94, 94, ticks=6, seed=660)
    return d


SUBJECTS = {
    "apache-pass-ravens": apache_pass_ravens,
    "storm-and-doves": storm_and_doves,
    "dust-map": dust_map,
    "sunrise-on-the-rim": sunrise_on_the_rim,
    "tarahumara-violins": tarahumara_violins,
    "girl-rides-east": girl_rides_east,
    "horses-from-the-laguna": horses_from_the_laguna,
    "one-armed-man": one_armed_man,
    "back-west-with-the-dog": back_west_with_the_dog,
}
