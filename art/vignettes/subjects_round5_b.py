"""Vignettes of the fifth round: ten scenes of Billy's ride south with the she-wolf (J2), from the sleet camp
below the boundary to the sheet he hangs to dry under the Pilares Teras. Loaded by art/vignettes/make_vignettes.py.

Each is checked against the episode that first shows it and drawn after the period reference its seed `credit`
names: the riders and horses are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and
IV helpers, the burros the same horse with a mule's ears, and the wolf and the dogs the traced US Fish and Wildlife
Service outline, bent. Everything else is drawn by hand from the book. Light from the north-west, as everywhere:
shade on each shape's south-east side.
"""

import math

import svgelements as se

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly, warp
from art.vignettes.subjects_parts_1_2 import wolf
from art.vignettes.subjects_parts_3_4 import cottonwood, pine, place, rider
from art.vignettes.subjects_round3 import figure, fire, horse
from art.vignettes.subjects_round4 import MULE_EARS, water

# The traced wolf lying down, legs folded under her and her head lowered (as in subjects_round4).
LIE = lambda x, y: (x, 50 + (y - 50) * 0.35 if y > 50 else y + (6 if x > 70 else 3))  # noqa: E731
# Sitting on her haunches (as in wolf-by-the-fire).
SIT = lambda x, y: (x, y + (0.32 * (40 - x) if x < 40 else 0) - (6 if x > 66 else 0))  # noqa: E731


def hound(x: float, y: float) -> tuple[float, float]:
    """The wolf's pricked ears laid flat, for a hound with drop ears drawn on by hand."""
    if x > 72 and y < 34:
        y = 34 + (y - 34) * 0.3
    return x, y


def turn(d: Drawing, since: int, cx: float, cy: float, deg: float):
    """Rotate everything drawn since item `since` about (cx, cy), clockwise for a positive angle."""
    m = se.Matrix(f"rotate({deg},{cx},{cy})")
    r = math.radians(deg)
    for i in range(since, len(d.items)):
        kind, path, opts = d.items[i]
        if kind == "dots":
            moved = [(cx + (x - cx) * math.cos(r) - (y - cy) * math.sin(r),
                      cy + (x - cx) * math.sin(r) + (y - cy) * math.cos(r)) for x, y in path]
        else:
            moved = (se.Path(path) * m).d()
        d.items[i] = (kind, moved, opts)


def sleet(d: Drawing, x0: float, x1: float, y0: float, y1: float, n: int, seed: int):
    """Fine sleet falling slant on the wind, short strokes scattered over a box."""
    rnd = __import__("random").Random(seed)
    d.line(" ".join(f"M{rnd.uniform(x0, x1):.1f},{rnd.uniform(y0, y1):.1f} l-2.4,5" for _ in range(n)), w=0.6,
           halo=False)


def blanketed(d: Drawing, x: float, y: float, k: float = 1.0):
    """Billy seated, wrapped in a blanket, hat on, his foot at (x, y) (as in wolf-by-the-fire)."""
    body = place("M-10,0 C-12,-10 -10,-24 -4,-30 C0,-34 6,-34 9,-29 C13,-22 14,-10 13,0 Z", x, y, k)
    d.shape(body)
    d.edge_shade(body, dx=-3 * k, dy=-2 * k)
    d.line(place("M0,-30 C2,-20 2,-10 1,0", x, y, k), w=0.8, halo=False)
    d.shape(place(circle(2, -37, 4.2), x, y, k), w=1.3)
    d.shape(place("M-6,-40.5 C-2,-42.2 6,-42.2 10,-40.5 C6,-38.8 -2,-38.8 -6,-40.5 Z", x, y, k), w=1.3)
    d.shape(place("M-1.8,-41 C-1.8,-47 5.8,-47 5.8,-41 Z", x, y, k), w=1.3)


# 1. The camp in the lee of the arroyo, sleet falling slant on the fire (1-09) --------------------------
def sleet_camp() -> Drawing:
    d = Drawing("sleet-camp")
    # Lightning far off over the plains to the south.
    d.line("M54,42 C66,41 80,42 94,41", w=0.8)
    d.line("M80,14 L76,24 L80,23.4 L74,38", w=1.1)
    # The cut bank of the arroyo, and on top of it the cottonwood whose roots the floods have bared.
    bank = "M-2,50 L14,50 C18,54 20,62 21,70 C22,76 23,82 24,88 L-2,88 Z"
    d.shape(bank, w=1.4)
    d.hatch(bank, angle=80, pitch=2.6, w=0.6)
    cottonwood(d, 6, 50, 34, 22, seed=551)
    # The washed-out elbow of root standing out of the bank, the wolf's rope tied to it.
    d.line("M16,58 C22,58 28,60 30,66 C31,70 28,74 22,76", w=2.0)
    d.line("M30,68 C40,70 50,70 60,71", w=0.9)
    # She lies on the arroyo floor facing the fire, her tail curled over her nose.
    wolf(d, 0.44, 30, 50, bend=LIE, w=1.4)
    d.line("M70.6,74 C74,72 76,74 76,77", w=1.2)
    fire(d, 84, 86, 1.0)
    # The fine sleet slanting out of the dark and hissing in the coals.
    sleet(d, 40, 96, 2, 64, 34, seed=552)
    sleet(d, 4, 40, 2, 20, 6, seed=553)
    d.ground(2, 94, 88, ticks=6, seed=550)
    return d


# 2. The wolf drinking from the paper-lined hole he scoops for her (1-09) -------------------------------
def false_waterhole() -> Drawing:
    d = Drawing("false-waterhole")
    # The small pine and the high limb he passed the rope over.
    pine(d, 30, 86, 62, seed=554)
    d.line("M30,38 C42,35 54,34 64,36", w=1.4)
    # The wolf under the limb, head down to the water, her eyes on him.
    def drink(x, y):
        if x > 60 and y < 62:
            s = min(1.0, (62 - y) / 22)
            y += (x - 60) * 1.25 * s
            x -= (x - 60) * 0.2 * s
        return x, y
    wolf(d, 0.5, 26, 42, bend=drink, w=1.5)
    # The rope from her collar up over the limb and back to where he squats holding it.
    d.line("M60,58 C61,50 62,42 63,36.6 M63,36 C50,46 30,62 18,72", w=0.8, halo=False)
    # The hole lined with the sandwich paper, a rock on the paper, the canteen stood beside it.
    paper = poly((60, 82), (80, 81), (82, 87.6), (58, 88.4))
    d.shape(paper, w=1.0)
    hole = ellipse(70, 85, 8, 2.4)
    d.shape(hole, w=1.1)
    d.hatch(hole, angle=0, pitch=0.9)
    d.dots([(67.6, 84.6), (70.4, 84.8)], r=0.6)
    d.shape(ellipse(80, 82, 1.6, 1.0), w=0.9)
    flask = "M86,88 C84,88 83,86 83,82 C83,78 85,76 88,76 C91,76 93,78 93,82 C93,86 92,88 90,88 Z"
    d.shape(flask, w=1.3)
    d.edge_shade(flask, dx=-1.6, dy=-1.6)
    d.shape(poly((87, 76), (87, 73), (89, 73), (89, 76)), w=0.9)
    # Billy squatting back from her, the rope in both hands.
    d.line("M5,82 L15,75 L16,88 M6,84 L13,80 L12.6,88", w=1.6)
    boy = "M3,84 C2,76 4,70 9,66 L14,68 C13,72 11,78 9,84 Z"
    d.shape(boy, w=1.3)
    d.edge_shade(boy, dx=-1.6, dy=-1.6)
    d.line("M12,69 L18,72", w=1.3)
    d.shape(circle(12, 62, 2.8), w=1.1)
    d.shape("M7,59.6 L17,59.6 L14.6,58.4 C14.6,55 9.4,55 9.4,58.4 Z", w=1.0)
    d.ground(2, 94, 90, ticks=7, seed=555)
    return d


# 3. The pilgrims' burros bolting down the mountain at the wolf's scent (1-09) --------------------------
def burro(d: Drawing, ox: float, oy: float, k: float, flip: bool = False, tilt: float = 0.0):
    """A packed burro: the traced horse, unsaddled, with a load and a mule's ears, tipped by `tilt` degrees."""
    since = len(d.items)
    f = horse(d, ox, oy, k, flip=flip, saddle=False, pack=True)
    d.line(warp(MULE_EARS, f), w=1.0)
    turn(d, since, ox, oy, tilt)


def burro_stampede() -> Drawing:
    d = Drawing("burro-stampede")
    # The mountainside falling away to the right, pines on it.
    d.line("M2,26 C30,36 60,58 94,84", w=1.0)
    pine(d, 10, 28, 26, seed=556)
    pine(d, 90, 80, 30, seed=557)
    # The burros careering down it.
    burro(d, 34, 52, 0.42, tilt=22)
    burro(d, 66, 84, 0.5, tilt=26)
    # Behind them the panniers broken open: baled hides tumbling, a blanket, the frame of a kiack.
    for x, y, a in ((14, 40, -20), (22, 30, 30), (48, 62, 10)):
        bale = len(d.items)
        b = poly((x - 4, y - 2.6), (x + 4, y - 2.6), (x + 4, y + 2.6), (x - 4, y + 2.6))
        d.shape(b, w=1.1)
        d.line(f"M{x - 1.4},{y - 2.6} l0,5.2 M{x + 1.6},{y - 2.6} l0,5.2", w=0.6, halo=False)
        turn(d, bale, x, y, a)
    d.line("M6,50 L14,54 M8,56 L12,48", w=1.1)
    d.dots([(18, 22), (30, 44), (54, 70)], r=0.7)
    return d


# 4. Huarache and barefoot prints in the snow of the pass, the wolf's among them (1-09) -----------------
def huarache(cx: float, cy: float, k: float, flip: bool = False) -> str:
    """A flat, heelless sandal print, cut from a tyre."""
    return place("M0,-7 C2.6,-7 3.4,-4 3,0 C2.8,3 2.6,6 0,7 C-2.6,6 -2.8,3 -3,0 C-3.4,-4 -2.6,-7 0,-7 Z", cx, cy, k,
                 flip)


def huarache_prints() -> Drawing:
    d = Drawing("huarache-prints")
    # The snowy ridge of the Cabellera, and pines along it.
    ridge = "M2,30 L14,22 L22,26 L34,16 L44,24 L58,14 L70,22 L80,18 L94,26"
    d.line(ridge, w=1.0)
    d.hatch(ridge + " L94,30 L80,26 L70,30 L58,22 L44,30 L34,24 L22,32 L14,30 L2,36 Z", angle=70, pitch=2.2, w=0.6)
    # The trail running up through the snow, banked either side.
    d.line("M2,90 C18,72 34,58 44,44 M94,90 C78,72 62,58 52,44", w=1.0)
    d.hatch("M2,90 C18,72 34,58 44,44 L40,44 C30,58 14,72 -2,84 Z", angle=60, pitch=2.0, w=0.6)
    d.hatch("M94,90 C78,72 62,58 52,44 L56,44 C66,58 82,72 98,84 Z", angle=60, pitch=2.0, w=0.6)
    # Billy riding on up it, and the wolf trotting behind the horse.
    rider(d, 54, 44, 0.2, hat="cowboy")
    wolf(d, 0.11, 30, 36, w=1.0)
    # In the near snow: the tread-marked huarache prints, a bare foot, and the wolf's big tracks.
    for x, y, k, fl in ((30, 76, 1.2, False), (40, 66, 1.0, True), (62, 82, 1.3, True)):
        h = huarache(x, y, k, fl)
        d.shape(h, w=1.1)
        d.line(" ".join(f"M{x - 2.6 * k:.1f},{y + t * k:.1f} l{5.2 * k:.1f},0" for t in (-4.4, -2.2, 0, 2.2, 4.4)),
               w=0.6, halo=False)
    foot = place("M0,-5 C2.6,-5 3,-2 2.6,1 C2.2,4 2.4,6 0,7 C-2.4,7 -2.6,4 -2.4,1 C-2.2,-2 -2.4,-5 0,-5 Z", 52, 64,
                 1.0)
    d.shape(foot, w=1.0)
    d.dots([(49.6, 57.6), (51.4, 57), (53, 57.2), (54.4, 57.8), (55.4, 59)], r=0.55)
    for x, y in ((72, 70), (80, 60), (66, 56)):
        d.shape(ellipse(x, y + 1.4, 2.2, 1.8), w=0.9)
        d.dots([(x - 2.4, y - 1.4), (x - 0.8, y - 2.4), (x + 0.8, y - 2.4), (x + 2.4, y - 1.4)], r=0.7)
    return d


# 5. Boy and wolf side by side on the moonlit meadow, no fire, the colonia's lights far below (1-09) ----
def meadow_no_fire() -> Drawing:
    d = Drawing("meadow-no-fire")
    # The moon rising over the mountains behind them.
    ridge = "M2,36 L12,26 L20,30 L30,20 L40,30 L48,34"
    d.line(ridge, w=1.0)
    d.hatch(ridge + " L48,40 L2,40 Z", angle=70, pitch=2.4, w=0.6)
    d.shape("M17,26.4 C15,20 18,12 26,11 C33,10.4 38,16 37,23 L30,20 L24,26 Z", w=1.1)
    d.dots([(60, 8), (74, 14), (88, 6), (52, 20), (82, 26)], r=0.6)
    # The Bavispe's valley far below to the west, the yellow window lights of the colonia in it.
    d.line("M50,48 C64,52 80,52 94,50", w=0.8)
    d.dots([(70, 55), (73, 54.4), (76, 55.4), (79, 54.6), (84, 55.2), (88, 54.4)], r=0.8)
    # Billy wrapped in his blanket, and the wolf sitting beside him, ears forward.
    blanketed(d, 22, 86, 0.9)
    wolf(d, 0.4, 36, 50, bend=SIT, w=1.4)
    # Flowers in the meadow grass.
    grass(d, [(54, 90), (76, 90), (88, 91)], h=4)
    d.dots([(60, 88), (66, 90), (72, 87), (82, 89), (92, 88)], r=0.9)
    d.ground(2, 94, 91, ticks=6, seed=558)
    return d


# 6. The muzzled wolf backed under a wagon, the town's dogs and children in the road (1-09) -------------
def wolf_under_the_wagon() -> Drawing:
    d = Drawing("wolf-under-the-wagon")
    # The mud wall of the house behind, a dark doorway in it.
    wall = "M-2,66 L-2,14 C8,12 14,16 22,13 L30,18 C40,16 46,20 56,15 C66,12 72,18 80,14 L88,17 L98,13 L98,66 Z"
    d.shape(wall, w=1.4)
    d.line("M10,24 l4,0.4 M26,28 l3,0 M70,26 l4,0 M86,22 l3,0.4 M64,30 l3,0", w=0.7, halo=False)
    # The wagon: a plank bed on two spoked wheels.
    bed = poly((2, 44), (2, 34), (92, 34), (92, 44))
    d.shape(bed, w=1.6)
    d.line("M2,39 L92,39", w=0.6, halo=False)
    d.edge_shade(bed, dx=0, dy=-2.4)
    for cx in (14, 80):
        d.shape(circle(cx, 56, 10), w=1.6)
        d.line(" ".join(f"M{cx},56 L{cx + 9.4 * math.cos(a):.1f},{56 + 9.4 * math.sin(a):.1f}"
                        for a in (i * math.pi / 5 for i in range(10))), w=0.6, halo=False)
        d.shape(circle(cx, 56, 1.8), w=0.9)
    # The shadow under the wagon, and in it the wolf backed against the wall, facing out, the homemade muzzle over her jaws.
    d.hatch(poly((24, 44), (70, 44), (70, 66), (24, 66)), angle=45, pitch=1.6, cross=True)
    wolf(d, 0.46, 26, 30, flip=True, bend=LIE, w=1.5)
    d.line("M27,50 L34,49.4 M27,52.6 L33.4,52 M29,48.6 L29.4,54 M32,48.4 L32.4,53.6", w=0.7, halo=False)
    d.line("M2,66 L98,66", w=1.0)
    # The dogs and children in the road.
    wolf(d, 0.24, 2, 72, bend=hound, w=1.2)
    wolf(d, 0.24, 66, 72, flip=True, bend=hound, w=1.2)
    for x, h in ((38, 22), (48, 18), (58, 20)):
        figure(d, x, 92, h, hat=False, coat=False)
    d.ground(2, 94, 92, ticks=6, seed=559)
    return d


# 7. The pilgrims' camp on the meadow at dusk, carretas tilted on their tongues (1-09) ------------------
def carreta(d: Drawing, x: float, y: float, k: float):
    """A little two-wheeled cart standing tilted forward on its tongue, in silhouette; wheel hub at (x, y)."""
    d.line(place("M10,-2 L30,9", x, y, k), w=1.6)
    box = place("M-18,-14 L14,-4 L12,2 L-20,-8 Z", x, y, k)
    d.shape(box, w=1.4)
    d.line(place("M-16,-14 L-17,-22 M-6,-11 L-7,-19 M4,-8 L3,-16 M13,-4 L12,-12 M-17,-22 L12,-12", x, y, k), w=1.0)
    wheel = place(circle(0, 0, 9), x, y, k)
    d.shape(wheel, w=1.6)
    d.hatch(wheel, angle=-45, pitch=1.3, cross=True)
    d.shape(place(circle(0, 0, 2), x, y, k), w=0.9)


def pilgrims_camp() -> Drawing:
    d = Drawing("pilgrims-camp")
    # The meadow slope banking away against the dusk sky to the west, burros grazing on it.
    slope = "M2,46 C30,40 60,34 94,30"
    d.line(slope, w=1.0)
    d.hatch("M2,46 C30,40 60,34 94,30 L94,20 C60,24 30,30 2,36 Z", angle=10, pitch=2.6, w=0.5)
    for x, y, k in ((30, 46, 0.16), (52, 42, 0.14)):
        f = horse(d, x, y, k, saddle=False, graze=1.0)
        d.line(warp(MULE_EARS, f), w=0.8)
    # The carretas one behind the next, like ore carts.
    carreta(d, 70, 52, 0.7)
    carreta(d, 46, 60, 0.85)
    carreta(d, 18, 70, 1.0)
    # The fires on the meadow and figures moving between them.
    fire(d, 76, 84, 0.7)
    fire(d, 54, 86, 0.6)
    figure(d, 88, 86, 20, flip=True)
    d.ground(2, 94, 87, ticks=6, seed=560)
    return d


# 8. The alguacil's hunting party along the alameda, charros and bluetick hounds (1-09) ----------------
def sombrero(d: Drawing, t):
    """A charro's broad sombrero, peaked, on a traced rider."""
    d.shape(t("M35,19.6 C42,17 60,17 67,19.6 C60,22.2 42,22.2 35,19.6 Z"), w=1.2)
    crown = t("M46,19 C46.4,13 48,8 51,7.4 C54,8 55.6,13 56,19 Z")
    d.shape(crown, w=1.2)
    d.line(t("M46.4,17 L55.6,17"), w=0.7, halo=False)


def hunting_party() -> Drawing:
    d = Drawing("hunting-party")
    # Two of the riders abreast, in charro dress, spangled sombreros.
    rider(d, 60, 70, 0.44, hat="none", extra=lambda t: sombrero(d, t))
    rider(d, 38, 76, 0.5, hat="none", extra=lambda t: sombrero(d, t))
    # The hounds trotting neat-footed beneath them.
    for x, y in ((4, 74), (34, 76), (62, 74)):
        wolf(d, 0.22, x, y, bend=hound, w=1.1)
        d.line(f"M{x + 76 * 0.22:.1f},{y + 33 * 0.22:.1f} l0.6,{6 * 0.22 + 1.6:.1f}", w=1.4)
        d.dots([(x + px * 0.22, y + py * 0.22) for px, py in ((24, 46), (34, 42), (44, 46), (54, 42), (62, 48),
                                                                (30, 54), (48, 54))], r=0.7)
    d.ground(2, 94, 93, ticks=6, seed=561)
    return d


# 9. Billy midriver in the ford, lit by the last rocket, the three-legged dog on the beach (1-10) -------
def ford_by_rocket_light() -> Drawing:
    d = Drawing("ford-by-rocket-light")
    # The last rocket over the town: its trail and its burst.
    d.line("M92,50 C90,34 86,22 80,14", w=0.8)
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.line(f"M{80 + 3 * math.cos(r):.1f},{12 + 3 * math.sin(r):.1f} L{80 + 8 * math.cos(r):.1f},"
               f"{12 + 8 * math.sin(r):.1f}", w=0.9)
    d.dots([(80 + 10.4 * math.cos(math.radians(a)), 12 + 10.4 * math.sin(math.radians(a))) for a in range(15, 360, 30)],
           r=0.6)
    # The shore trees on the far bank, kept low so they stay behind the rider.
    d.line("M2,46 C20,44 40,45 70,44", w=0.9)
    d.line(" ".join(f"M{x},{46 - (x % 3)} l{(x % 5) - 2},{-4 - (x * 7) % 5}" for x in range(4, 68, 5)), w=0.8)

    # Billy on the horse in the river, the wolf in her pale sheet tied across the saddle bow.
    def bundle(t):
        b = t("M52,35 C60,31 72,31 81,35 C84,39 84,47 81,50 L55,51 C52,48 51,41 52,35 Z")
        d.shape(b, w=1.7)
        d.line(t("M61,32.6 L61.6,50.6 M71,32 L71.6,50.4"), w=0.9, halo=False)
        d.line(t("M81,47 C84,52 84,56 82,60"), w=1.3)
    rider(d, 46, 86, 0.8, flip=True, hat="cowboy", extra=bundle)
    # The river up under the horse's belly, hiding its legs.
    for y in range(61, 94, 2):
        d.line(f"M2,{y} L72,{y}", w=1.6, color=PAPER, halo=False)
    water(d, 61, x0=2, x1=70, seed=3)
    # The town dog on the gravel beach, frozen on three legs.
    d.line("M70,62 C68,72 68,80 70,86 C78,85 86,85 94,86", w=1.0)
    lift = lambda x, y: (x + (4 if x > 60 and y > 60 else 0), y - ((y - 60) * 0.7 if x > 60 and y > 60 else 0))  # noqa: E731
    wolf(d, 0.24, 72, 66, flip=True, bend=lift, w=1.1)
    d.dots([(80, 89), (88, 90), (92, 88)], r=0.9)
    return d


# 10. The washed sheet steaming on its trestle by the fire, under the cliffs of the Pilares (1-10) -----
def sheet_on_the_trestle() -> Drawing:
    d = Drawing("sheet-on-the-trestle")
    # The tall escarpments of the Pilares, and the talus under them.
    cliff = "M-2,20 L-2,4 L14,2 L20,8 L30,4 L40,10 L52,6 L64,10 L74,2 L86,8 L98,4 L98,22 C80,18 60,22 40,20 Z"
    d.shape(cliff, w=1.2)
    d.hatch(cliff, angle=85, pitch=3.0, w=0.6)
    # Two forked hackberry sticks and the trestle pole, the wet sheet hung over it steaming.
    d.line("M28,84 L29,38 M29,38 L25,32 M29,38 L33,32 M70,84 L69,38 M69,38 L65,32 M69,38 L73,32", w=1.5)
    sheet = ("M26,42 C26,40 27,39 30,39 L68,39 C71,39 72,40 72,42 C73,50 74,56 77,64 C70,61 64,68 56,64 "
             "C50,68 42,62 36,67 C30,63 26,66 21,64 C24,56 25,50 26,42 Z")
    d.shape(sheet, w=1.5)
    d.line("M34,41 C33,50 32,58 31,64 M46,41 C46,50 45,58 45,65 M58,41 C59,50 60,58 61,65", w=0.7, halo=False)
    d.edge_shade(sheet, dx=-2.6, dy=0)
    d.line("M24,39 L74,39", w=1.6)
    d.line("M34,34 C31,31 36,29 33,26 M44,34 C41,30 46,28 43,25 "
           "M54,34 C51,31 56,29 53,26 M64,34 C61,31 66,29 63,26", w=0.9)
    # The fire before it, and the wolf lying stiff in the leaves beside it.
    fire(d, 66, 86, 0.8)
    wolf(d, 0.34, 2, 58, bend=LIE, w=1.3)
    d.ground(2, 94, 89, ticks=6, seed=562)
    return d


SUBJECTS = {
    "sleet-camp": sleet_camp,
    "false-waterhole": false_waterhole,
    "burro-stampede": burro_stampede,
    "huarache-prints": huarache_prints,
    "meadow-no-fire": meadow_no_fire,
    "wolf-under-the-wagon": wolf_under_the_wagon,
    "pilgrims-camp": pilgrims_camp,
    "hunting-party": hunting_party,
    "ford-by-rocket-light": ford_by_rocket_light,
    "sheet-on-the-trestle": sheet_on_the_trestle,
}
