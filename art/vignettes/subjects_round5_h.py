"""Vignettes of the fifth round: Billy's last ride in Mexico and his return north with Boyd's remains, from
the ciénega at Babícora (4-05) to the road by the waystation (4-09). Loaded by art/vignettes/make_vignettes.py.

Each is checked against the episode that first shows it and drawn after the reference its seed `credit` names: the
riders and horses are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and IV
helpers, the obelisk as in the boundary vignette. Everything else is drawn by hand from the book. Light from the
north-west, as everywhere: shade on each shape's south-east side.
"""

import math

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly, traced, warp
from art.vignettes.subjects_parts_3_4 import blob, cottonwood, place, rider
from art.vignettes.subjects_round3 import horse
from art.vignettes.subjects_round4 import water


def rider_head_down(d: Drawing, ox: float, oy: float, k: float, graze: float = 0.8):
    """The traced horse and rider with the horse's head and neck lowered, as horse(graze=) does for a horse alone,
    the rider sitting upright with his hat pulled low."""
    def f(x: float, y: float) -> tuple[float, float]:
        if x > 64:
            y += (x - 64) * graze
            x -= (x - 64) * graze * 0.3
        return ox + (x - 48) * k, oy + (y - 90) * k

    def t(path: str) -> str:
        return warp(path, f)
    tr = traced("rider-annie-g")
    for p in tr["outline"]:
        d.shape(t(p), w=1.5)
        d.edge_shade(t(p), dx=-2, dy=-2.4)
    for p in tr["tones"]["0.3"]:
        d.hatch(t(p), angle=45, pitch=2.0)
    d.line(t("M47,39 C52,41 56,43 56.5,47 L53,58 L57,59"), w=1.0, halo=False)
    d.line(t("M57,36 C66,40 78,46 87,49"), w=0.7, halo=False)
    d.shape(t("M42,21.4 C46,19.6 56,19.6 60,21.4 C56,23 46,23 42,21.4 Z"), w=1.2)
    d.shape(t("M46.5,21 C46.5,16.5 47.5,14.2 51,14.2 C54.5,14.2 55.5,16.5 55.5,21 Z"), w=1.2)
    d.hatch(t("M46.5,21 L46.5,14.2 L55.5,14.2 L55.5,21 Z"), angle=45, pitch=1.0)
    return t


def creosote(d: Drawing, x: float, base: float, s: float):
    """A creosote bush: a fan of thin stems from one root, a few leafy tufts at their tips."""
    stems = " ".join(f"M{x:.1f},{base:.1f} L{x + s * dx:.1f},{base - s * dy:.1f}"
                     for dx, dy in ((-7, 6), (-4, 10), (0, 12), (4, 10), (7, 6)))
    d.line(stems, w=0.9)
    d.dots([(x + s * dx, base - s * dy) for dx, dy in ((-7, 6), (-4, 10), (0, 12), (4, 10), (7, 6), (-2, 8),
                                                       (2, 8))], r=0.9)


# 1. The ring of old cottonwoods at the ciénega, and the man on horseback watching Billy wake (4-05) ---------
def cienega_cottonwoods() -> Drawing:
    d = Drawing("cienega-cottonwoods")
    # The ring of old trees round the wet meadow, the far ones smaller.
    cottonwood(d, 36, 54, 26, 16, seed=851)
    cottonwood(d, 60, 52, 24, 15, seed=852)
    cottonwood(d, 12, 76, 62, 26, seed=853)
    cottonwood(d, 86, 74, 56, 22, seed=854)
    # The ciénega's open water and reeds.
    d.line("M24,62 C34,60 54,60 70,62", w=0.9)
    d.line("M30,64.6 l10,0 M48,64.2 l12,0", w=0.6, halo=False)
    grass(d, [(26, 63), (68, 63)], h=4)
    # Billy sitting up in his soogan.
    roll = "M22,86 C22,82 30,81 44,81.4 C49,81.6 52,83 52,85.4 C52,88 46,89 36,89 C28,89 22,88.4 22,86 Z"
    d.shape(roll, w=1.4)
    d.edge_shade(roll, dx=-1.6, dy=-1.8)
    body = "M24,84 C23,78 24,74 27,73 L31,73 C33,75 33,80 32,84 Z"
    d.shape(body, w=1.2)
    d.shape(circle(29, 69.6, 2.6), w=1.0)
    # The man sitting his horse, watching.
    rider(d, 66, 88, 0.36, flip=True, hat="cowboy")
    d.ground(2, 94, 91, ticks=6, seed=855)
    return d


# 2. The girl breaking pecans on a white canvas in the hotel garden at Casas Grandes (4-05) -----------------
def girl_cracking_pecans() -> Drawing:
    d = Drawing("girl-cracking-pecans")
    # A garden shrub and the wall behind.
    d.line("M2,44 L94,44 M2,48 L94,48", w=0.8)
    bush = blob(80, 34, 12, 12, 10, seed=856, depth=0.25)
    d.shape(bush, w=1.3)
    d.edge_shade(bush, dx=-3, dy=-3)
    d.line("M80,46 L80,40", w=1.2)
    # The white canvas spread on the ground: left bare, the ground round it hatched.
    cloth = poly((4, 90), (16, 62), (86, 62), (92, 90))
    d.hatch("M0,96 L0,56 L96,56 L96,96 Z " + poly((4, 90), (16, 62), (86, 62), (92, 90)), angle=10, pitch=2.6)
    d.shape(cloth, w=1.4)
    # The pile of pecans heaped on it.
    heap = "M60,80 C62,70 70,66 76,66 C82,66 88,72 90,80 Z"
    d.shape(heap, w=1.3)
    d.edge_shade(heap, dx=-2, dy=-2)
    nuts = [(66, 76), (71, 77), (76, 76.4), (81, 77), (86, 77.6), (69, 72), (74, 71.4), (79, 72), (84, 73),
            (72, 67.6), (77, 68)]
    for x, y in nuts:
        d.shape(ellipse(x, y, 1.8, 1.1), w=0.7)
    d.shape(ellipse(58, 84.6, 1.6, 1.0), w=0.7)
    d.shape(ellipse(54, 86, 1.6, 1.0), w=0.7)
    # The girl sitting, bent forward over the flat stone in her lap, the mano in her hands, her dark hair
    # hanging about them.
    skirt = "M18,86 C16,80 20,74 28,73 L46,76 C52,77 54,82 52,86 Z"
    d.shape(skirt, w=1.5)
    d.edge_shade(skirt, dx=-2, dy=-2)
    torso = "M20,76 C18,68 22,60 30,56 L37,58 C36,64 32,70 30,76 Z"
    d.shape(torso, w=1.4)
    d.shape(ellipse(46, 79, 6, 2), w=1.2)
    d.line("M33,58 C38,62 40,68 42,73 M30,62 C34,66 37,71 40,74", w=1.2)
    d.shape(ellipse(43, 74.6, 3.2, 1.8), w=1.1)
    d.hatch(ellipse(43, 74.6, 3.2, 1.8), angle=0, pitch=0.9)
    hair = "M30,52 C33,48 40,48 42,53 C43,58 42,64 40,70 C38,70 37,66 36,62 C34,60 31,58 30,55 Z"
    d.shape(hair, w=1.2)
    d.hatch(hair, angle=75, pitch=0.9)
    # Her song.
    d.line("M48,48 c1,-3 3,-3 4,-1 M54,42 c1,-3 3,-3 4,-1", w=0.7, halo=False)
    return d


# 3. The weatherboard cabin with its one lit window on the dark plain (4-05) -------------------------------
def quijada_cabin_light() -> Drawing:
    d = Drawing("quijada-cabin-light")
    # The mountains with the broad gap where the sun went down, the afterglow in it.
    d.line("M2,40 L10,30 L18,34 L26,26 L34,36 L40,44 M60,44 L66,34 L74,28 L82,32 L94,24", w=1.1)
    d.hatch("M2,40 L10,30 L18,34 L26,26 L34,36 L40,44 L2,44 Z", angle=70, pitch=2.0)
    d.hatch("M60,44 L66,34 L74,28 L82,32 L94,24 L94,44 Z", angle=70, pitch=2.0)
    d.line("M40,38 l20,0 M42,34 l16,0 M45,30 l10,0", w=0.6, halo=False)
    d.line("M2,44 C30,43 60,43 94,44", w=0.8)
    d.dots([(12, 10), (30, 6), (52, 14), (70, 8), (88, 12), (60, 22)], r=0.6)
    # The cabin: weatherboarded gable end and side, hatched dark for the night, the one window lit.
    end = poly((40, 84), (40, 58), (54, 48), (68, 58), (68, 84))
    d.shape(end)
    d.hatch(end, angle=45, pitch=1.6, cross=True)
    side = poly((68, 84), (68, 58), (90, 56), (90, 82))
    d.shape(side, w=1.6)
    d.hatch(side, angle=45, pitch=1.6)
    d.line("M54,48 L76,46 L92,54 L90,56 M68,58 L54,46.6", w=1.4)
    d.line("M37,60 L54,46 L71,60", w=1.8)
    win = poly((47, 72), (47, 62), (57, 62), (57, 72))
    d.shape(win, w=1.4)
    d.line("M52,62 L52,72 M47,67 L57,67", w=0.8)
    d.line("M45,60 l-4,-4 M52,60 l0,-5 M59,60 l4,-4 M45,74 l-4,4 M59,74 l4,4 M45,67 l-4,0 M59,67 l4,0", w=0.8)
    door = poly((75, 82.6), (75, 64), (83, 63.4), (83, 82))
    d.shape(door, w=1.0)
    # Billy sitting his horse before it, calling out.
    rider(d, 18, 88, 0.34, hat="cowboy")
    d.ground(2, 94, 88, ticks=6, seed=857)
    return d


# 5. Billy in the river at dawn, plastering clay over the knife wound in Niño's chest (4-06) ---------------
def clay_on_the_wound() -> Drawing:
    d = Drawing("clay-on-the-wound")
    # The far mountains to the west in the first light, and the willows on the bank.
    d.line("M2,30 L10,22 L16,26 L24,18 L32,26 L40,24 L48,30", w=1.0)
    d.line("M2,44 C30,42 60,43 94,42", w=0.9)
    for x in (66, 76, 88):
        d.line(f"M{x},44 C{x - 1},36 {x - 4},30 {x - 7},26 M{x},44 C{x + 1},36 {x + 3},30 {x + 6},25 "
               f"M{x},44 L{x},24", w=0.9)
        d.line(f"M{x - 5},30 l-2,5 M{x - 3},34 l-1.4,5 M{x + 4},29 l2,5 M{x + 2},33 l1.4,5 M{x},28 l0,5", w=0.6,
               halo=False)
    # Steam rising off the river.
    d.line("M62,54 C60,50 64,48 62,44 M90,58 C88,54 92,52 90,48", w=0.6, halo=False)
    # Billy standing in the water, and Niño with the clay plastered on his chest, his long face laid on Billy's
    # shoulder.
    body = "M6,96 L6,76 C6,72 10,69 14,69 L18,69 C22,69 24,72 24,76 L24,96 Z"
    d.shape(body, w=1.5)
    d.edge_shade(body, dx=-2, dy=-2)
    d.shape(circle(15, 63, 4.2), w=1.3)
    hat = "M7.4,61 L22.6,61 L19.4,59.6 C19.4,54.2 10.6,54.2 10.6,59.6 Z"
    d.shape(hat, w=1.2)
    d.hatch(hat, angle=0, pitch=0.9)
    f = horse(d, 64, 90, 0.74, flip=True, saddle=True)
    clay = warp("M75,55 C78,53 82,55 82,59 C82,63 78,65 75,63 C73,61 73,57 75,55 Z", f)
    d.shape(clay, w=1.1)
    d.hatch(clay, angle=45, pitch=0.9, cross=True)
    d.line("M22,74 C28,74 33,72 38.4,70", w=1.6)
    # The river over their legs.
    for y in range(80, 94, 2):
        d.line(f"M0,{y} L96,{y}", w=1.5, color=PAPER, halo=False)
    water(d, 80, x0=2, x1=94, seed=3)
    d.line("M4,86 l14,0 M30,88 l18,0 M62,86 l20,0 M10,92 l20,0 M56,92 l24,0", w=0.7, halo=False)
    return d


# 6. Across the dry reservoir by Dog Springs: the travois over cracked clay printed with crane tracks (4-08) -
def reservoir_crane_tracks() -> Drawing:
    d = Drawing("reservoir-crane-tracks")
    # The broken earthwork of the old dam behind, and a boundary obelisk on the line.
    d.line("M2,38 C14,34 24,34 34,37 M44,37 C56,34 70,34 82,37 M88,37 L94,36", w=1.1)
    d.hatch("M2,38 C14,34 24,34 34,37 L34,40 L2,40 Z M44,37 C56,34 70,34 82,37 L82,40 L44,40 Z", angle=60, pitch=2.0)
    ob = poly((10.4, 36), (11.6, 22), (12.4, 19), (13.2, 22), (14.4, 36))
    d.shape(ob, w=1.1)
    d.shape(poly((8.6, 39), (8.6, 36), (16.2, 36), (16.2, 39)), w=1.1)
    d.line("M2,41 C30,40 60,40 94,41", w=0.8)
    # Billy riding over the floor with the travois rasping behind.
    d.line("M62,54 L28,62 M64,52 L32,59", w=1.2)
    bundle = ("M32,59 C32,57 34,56 38,55 L52,51.6 C54,51.2 56,52.2 55.6,53.6 C55.2,55 54,55.6 52,56 L38,59.6 "
              "C35,60.6 32,60.6 32,59 Z")
    d.shape(bundle, w=1.2)
    rider(d, 72, 62, 0.32, hat="cowboy")
    # The cracked clay in the foreground.
    cracks = ("M2,66 L14,68 L22,64 L34,67 L46,64 L58,68 L70,65 L82,68 L94,66 "
              "M14,68 L12,80 L2,82 M12,80 L26,84 L34,78 L34,67 M34,78 L48,80 L46,64 M48,80 L52,94 "
              "M48,80 L62,78 L58,68 M62,78 L74,82 L70,65 M74,82 L86,78 L82,68 M86,78 L94,82 "
              "M26,84 L22,94 M74,82 L78,94")
    d.line(cracks, w=0.9)
    # Crane tracks: three long toes splayed forward and a short hind toe, a bird's walk across the mud.
    for x, y, a in ((10, 74, 10), (24, 78, -6), (40, 72, 8), (54, 88, -4), (66, 74, 12), (80, 86, -8), (88, 72, 4),
                    (30, 90, 0)):
        r = math.radians(a)

        def p(u, v, r=r, x=x, y=y):
            return (x + u * math.cos(r) - v * math.sin(r), y + u * math.sin(r) + v * math.cos(r))
        toes = [p(6.4, 0), p(4.4, -4.4), p(4.4, 4.4), p(-2.4, 0)]
        o = p(0, 0)
        d.line(" ".join(f"M{o[0]:.1f},{o[1]:.1f} L{tx:.1f},{ty:.1f}" for tx, ty in toes), w=1.0, halo=False)
    return d


def walker(d: Drawing, x: float, y: float, h: float, skirt: bool):
    """A person walking west in a long skirt or shirt and trousers, feet at (x, y), h tall, a soot mark on the
    brow (local units 24 tall, facing left)."""
    k = h / 24

    def p(path: str) -> str:
        return place(path, x, y, k)
    if skirt:
        d.line(p("M-1,-4 L-3,0 M1.4,-4 L2.6,0"), w=1.2)
        body = p("M-2.6,-18 C-1.6,-19.4 1.8,-19.4 2.8,-18 L5,-4 L-5,-4 Z")
    else:
        d.line(p("M-1.2,-10 L-3.6,0 M1.4,-10 L3,0"), w=1.3)
        body = p("M-2.6,-18 C-1.6,-19.4 1.8,-19.4 2.6,-18 L3,-9.6 L-3,-9.6 Z")
    d.shape(body, w=1.2)
    d.edge_shade(body, dx=-1.2, dy=-1.2)
    d.line(p("M-1.4,-16.6 L-3.6,-10.6 M1.6,-16.6 L3.4,-11"), w=1.0)
    d.shape(circle(x - 0.4 * k, y - 21.6 * k, 2.6 * k), w=1.1)
    d.line(f"M{x - 1.6 * k:.1f},{y - 22.6 * k:.1f} L{x + 0.2 * k:.1f},{y - 22.8 * k:.1f}", w=max(1.0, 0.7 * k), halo=False)


# 7. The woman and five children with ash on their brows, walking out of Animas (4-08) ----------------------
def ash_wednesday() -> Drawing:
    d = Drawing("ash-wednesday")
    # The edge of the town behind them, low and flat-roofed.
    d.shape(poly((60, 50), (60, 38), (82, 38), (82, 50)), w=1.1)
    d.shape(poly((82, 50), (82, 34), (94, 34), (94, 50)), w=1.1)
    d.hatch(poly((82, 50), (82, 34), (94, 34), (94, 50)), angle=45, pitch=2.0)
    d.line("M66,50 l0,-6 l4,0 l0,6", w=0.8)
    d.line("M2,52 C30,51 60,51 94,50", w=0.8)
    # The woman leading and the five children in file behind her, the smallest last, walking west, each with
    # the soot mark on the brow.
    for x, h, skirt in ((14, 48, True), (32, 34, True), (46, 30, False), (59, 26, True), (71, 22, False),
                        (82, 18, False)):
        walker(d, x, 88, h, skirt)
    d.ground(2, 94, 90, ticks=7, seed=859)
    return d


# 8. Waist-deep in the caliche, digging the grave, as the sheriff's car pulls up at the gate (4-08) ---------
def waist_deep_caliche() -> Drawing:
    d = Drawing("waist-deep-caliche")
    # The cemetery's wire fence and gateposts, and the sheriff's car pulled up outside.
    d.line("M2,46 L36,46 M2,42 L36,42 M50,46 L94,46 M50,42 L94,42", w=0.6, halo=False)
    d.line("M8,40 L8,48 M20,40 L20,48 M60,40 L60,48 M76,40 L76,48 M90,40 L90,48", w=0.9)
    d.line("M36,34 L36,48 M50,34 L50,48 M35,34 L51,34", w=1.6)
    car = ("M56,48 L56,43 C56,41.6 57.4,41 60,41 L63,36.6 C63.6,36 64.4,36 65.4,36 L74,36 C75.4,36 76,36.6 77,37.8 "
           "L79.6,41 C82.6,41 84,41.6 84,43 L84,48 Z")
    d.shape(car, w=1.3)
    d.shape(poly((64.4, 40.6), (65.6, 37.6), (69.6, 37.6), (69.6, 40.6)), w=0.7)
    d.shape(poly((71, 40.6), (71, 37.6), (75.4, 37.6), (77.6, 40.6)), w=0.7)
    d.edge_shade(car, dx=0, dy=-1.6)
    for cx in (61.6, 78.6):
        d.shape(circle(cx, 48, 2.4), w=1.1)
        d.hatch(circle(cx, 48, 2.4), angle=45, pitch=0.9)
    d.line("M2,52 C30,51 60,51 94,52", w=0.8)
    # Old wooden crosses in the dry ground.
    d.line("M14,66 L14,54 M10.6,57.4 L17.4,57.4 M84,64 L84,54 M81,56.6 L87,56.6", w=1.4)
    d.shape("M8,66 C10,63 18,63 20,66 Z", w=1.0)
    d.shape("M79,64 C81,61.4 87,61.4 89,64 Z", w=1.0)
    # The heap of dug dirt and caliche, the open grave, Billy in it to the waist, the spade in his hands.
    heap = "M56,80 C60,68 70,64 78,64 C86,66 92,72 94,80 Z"
    d.shape(heap, w=1.4)
    d.edge_shade(heap, dx=-2.4, dy=-2.4)
    d.dots([(66, 74), (72, 70), (78, 75), (84, 71), (88, 77), (70, 78)], r=0.8)
    pit = poly((14, 92), (22, 74), (60, 74), (56, 92))
    d.shape(pit, w=1.6)
    d.hatch(pit, angle=45, pitch=1.4, cross=True)
    body = "M31,86 L31,72 C31,66 33,62 36,61 L42,61 C45,62 46,66 46,72 L46,86 Z"
    d.shape(body, w=1.5)
    d.edge_shade(body, dx=-2, dy=-2)
    d.shape(circle(38.6, 56.4, 3.6), w=1.2)
    hat = "M32.2,54.6 L45,54.6 L42.2,53.2 C42.2,48.6 35,48.6 35,53.2 Z"
    d.shape(hat, w=1.1)
    d.hatch(hat, angle=0, pitch=0.9)
    d.line("M58,50 L42,86", w=1.6)
    d.line("M33,64 C35,70 40,73 46.6,72.6 M44.6,63 C48,62 50,62 51.6,62", w=1.4)
    d.shape(poly((14, 92), (18, 84), (58, 84), (56, 92)), w=1.4)
    d.dots([(24, 88), (34, 89), (46, 87.6), (52, 89)], r=0.6)
    return d


# 9.    return d


# 10. Horse head down, rider upright with his hat pulled low, on the blacktop among the cast tire casings (4-08)
def tire_casing(d: Drawing, cx: float, cy: float, rx: float, ry: float, turn: float = 0.0):
    """A cast-off truck tire casing lying coiled on the verge: a flattened ring, black, its tread ridged."""
    outer, inner = ellipse(cx, cy, rx, ry), ellipse(cx + turn, cy - ry * 0.12, rx * 0.56, ry * 0.42)
    d.shape(outer, w=1.3)
    d.hatch(outer, angle=45, pitch=1.0, cross=True)
    d.shape(inner, w=1.0)
    d.line(" ".join(f"M{cx + rx * 0.62 * math.cos(math.radians(a)):.1f},{cy + ry * 0.62 * math.sin(math.radians(a)):.1f} "
                    f"L{cx + rx * 0.98 * math.cos(math.radians(a)):.1f},{cy + ry * 0.98 * math.sin(math.radians(a)):.1f}"
                    for a in range(0, 360, 30)), w=0.9, color=PAPER, halo=False)


def head_down_hat_low() -> Drawing:
    d = Drawing("head-down-hat-low")
    # The wind-driven clouds, the rain blowing down in sheets, the far raw ranges under them.
    cloud = "M2,18 C10,8 24,8 30,14 C38,6 54,6 60,12 C68,6 84,6 94,14 L94,22 C70,20 30,20 2,24 Z"
    d.shape(cloud, w=1.0)
    d.hatch(cloud, angle=0, pitch=1.8)
    d.line(" ".join(f"M{x},{y} l-5,12" for x, y in ((10, 24), (18, 24), (26, 24), (34, 24), (42, 24),
                                                     (14, 38), (22, 38), (30, 38), (38, 38))),
           w=0.6, halo=False)
    d.line("M54,44 L62,38 L68,40 L76,33 L84,39 L90,36 L94,40", w=0.9)
    d.line("M2,46 C30,45 60,45 94,44", w=0.7, halo=False)
    # The blacktop crossing the plain, its centre line.
    road = poly((0, 84), (96, 70), (96, 61), (0, 70))
    d.shape(road, w=1.3)
    d.hatch(road, angle=0, pitch=1.6)
    d.line("M4,76.4 L12,75.1 M22,73.6 L30,72.3 M40,70.8 L48,69.5 M58,68 L66,66.7 M76,65.2 L84,63.9",
           w=1.4, color=PAPER, halo=False)
    grass(d, [(6, 85), (40, 80), (70, 75), (90, 72)], h=4)
    # The castoff casings coiled along the verge, near and far.
    tire_casing(d, 18, 89, 13, 5.6, turn=1.4)
    tire_casing(d, 82, 85, 10, 4.2, turn=-1)
    # Billy on the shoulder, the horse's head down, his hat pulled low.
    rider_head_down(d, 52, 75, 0.46, graze=0.65)
    d.dots([(44, 92), (58, 90), (70, 93)], r=0.5)
    d.ground(36, 94, 95, ticks=4, seed=960)
    return d


# 11. Sitting in the road at dawn, the hat on the tarmac before him (4-09) ----------------------------------
def hat_on_the_tarmac() -> Drawing:
    d = Drawing("hat-on-the-tarmac")
    # The sun coming up at the end of the road.
    sun = "M38,44 C38,36 58,36 58,44 Z"
    d.shape(sun, w=1.2)
    d.line(" ".join(f"M{48 + 13 * math.cos(math.radians(a)):.1f},{44 - 13 * math.sin(math.radians(a)):.1f} "
                    f"l{5 * math.cos(math.radians(a)):.1f},{-5 * math.sin(math.radians(a)):.1f}"
                    for a in (15, 40, 65, 90, 115, 140, 165)), w=0.9)
    d.line("M2,44 L94,44", w=1.0)
    # The blacktop running away east, its edges and centre line.
    road = poly((0, 96), (44, 44), (52, 44), (96, 96))
    d.shape(road, w=1.4)
    d.hatch(road, angle=0, pitch=2.2)
    d.line("M47.6,50 L47.4,54 M47.2,60 L46.8,66 M46.6,74 L46,84", w=2.0, color=PAPER, halo=False)
    grass(d, [(8, 60), (18, 54), (82, 58), (90, 66)], h=4)
    # Billy sitting on the road, head bowed in his hands, the hat set down before him.
    back = "M24,92 C20,84 22,74 30,70 L36,70 C38,74 38,82 36,92 Z"
    d.shape(back, w=1.6)
    d.edge_shade(back, dx=-2, dy=-2)
    d.line("M34,90 L46,78 L54,92 M30,92 L42,82 L50,92", w=1.8)
    d.shape(circle(40, 72, 4.2), w=1.3)
    d.hatch("M36.4,70.4 C37,67.6 41,67 43,68.6 C41,69 38,70 36.4,70.4 Z", angle=0, pitch=0.8)
    d.line("M34,74 L42,80 L44,74", w=1.3)
    brim = ellipse(66, 89, 9, 2.4)
    d.shape(brim, w=1.3)
    crown = "M60,89 C60,82 62,80 66,80 C70,80 72,82 72,89 Z"
    d.shape(crown, w=1.3)
    d.hatch("M60,89 L60,86 L72,86 L72,89 Z", angle=0, pitch=0.9)
    return d


SUBJECTS = {
    "cienega-cottonwoods": cienega_cottonwoods,
    "girl-cracking-pecans": girl_cracking_pecans,
    "quijada-cabin-light": quijada_cabin_light,
    "clay-on-the-wound": clay_on_the_wound,
    "reservoir-crane-tracks": reservoir_crane_tracks,
    "ash-wednesday": ash_wednesday,
    "waist-deep-caliche": waist_deep_caliche,
    "head-down-hat-low": head_down_hat_low,
    "hat-on-the-tarmac": hat_on_the_tarmac,
}
