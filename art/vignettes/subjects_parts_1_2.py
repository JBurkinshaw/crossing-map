"""Vignettes for Parts I and II of the book: the she-wolf's journey north (J1), Billy taking her south (J2), and
Billy's wandering in the Sierra Madre and his ride home (J3). Loaded by art/vignettes/make_vignettes.py.

Billy and his horse Bird come from one traced outline (art/vignettes/traced/billy-on-bird.json, traced from a
Muybridge plate of 1887, public domain), with a hand-drawn hat over the jockey's cap. The wolf, and the dog, are the
traced she-wolf outline of the first set, scaled, mirrored or bent. Everything else is drawn by hand after the references
named in each drawing's `credit` in pipeline/seeds/vignettes.csv.
"""

import math

from art import PAPER
from art.vignettes.ink import OUTLINE, Drawing
from art.vignettes.shapes import circle, grass, poly, traced, warp


def fit(k: float, ox: float, oy: float, flip: bool = False):
    """Scale a traced 96-grid outline by k, mirror it if asked, and move its origin to (ox, oy)."""
    return lambda x, y: (ox + ((96 - x) if flip else x) * k, oy + y * k)


def rider(d: Drawing, k: float, ox: float, oy: float) -> None:
    """Billy on Bird, walking east, scaled by k from (ox, oy). The traced plate's jockey gets a broad hat."""
    t, f = traced("billy-on-bird"), fit(k, ox, oy)
    for p in t["outline"]:
        q = warp(p, f)
        d.shape(q, w=OUTLINE * min(1.0, 0.45 + k * 0.6))
        d.edge_shade(q, dx=-2.2 * k, dy=-2.6 * k)
    for p in t["tones"]["0.3"]:
        d.hatch(warp(p, f), pitch=max(1.5, 2.4 * k))
    # The hat, a brim and a low crown over the rider's head, which the trace has at (51, 17) on its grid.
    cx, cy = ox + 51 * k, oy + 17.2 * k
    d.shape(f"M{cx - 7.5 * k:.1f},{cy:.1f} C{cx - 3 * k:.1f},{cy - 1.6 * k:.1f} {cx + 3 * k:.1f},{cy - 1.6 * k:.1f} "
            f"{cx + 7.5 * k:.1f},{cy:.1f} C{cx + 3 * k:.1f},{cy + 1.4 * k:.1f} {cx - 3 * k:.1f},{cy + 1.4 * k:.1f} "
            f"{cx - 7.5 * k:.1f},{cy:.1f} Z", w=1.2)
    d.shape(f"M{cx - 3.4 * k:.1f},{cy - 0.4 * k:.1f} C{cx - 3.4 * k:.1f},{cy - 5 * k:.1f} {cx + 3.4 * k:.1f},"
            f"{cy - 5 * k:.1f} {cx + 3.4 * k:.1f},{cy - 0.4 * k:.1f} Z", w=1.2)


def wolf(d: Drawing, k: float, ox: float, oy: float, flip: bool = False, bend=None, w: float = 1.4) -> None:
    """The traced she-wolf, scaled; `bend` moves her points first (on the 96 grid) to change her pose."""
    f = fit(k, ox, oy, flip)
    g = (lambda x, y: f(*bend(x, y))) if bend else f
    for p in traced("she-wolf")["outline"]:
        q = warp(p, g)
        d.shape(q, w=w)
        d.edge_shade(q, dx=-4 * k, dy=-4.8 * k)


def juniper(d: Drawing, x: float, y: float, h: float, seed: int = 0) -> None:
    """A small juniper: a short crooked trunk and a lobed, wind-leaning crown, hatched dark."""
    r = h * 0.45
    lean = 1.5 + seed % 3
    d.line(f"M{x:.1f},{y:.1f} C{x - 1:.1f},{y - h * 0.15:.1f} {x + 1:.1f},{y - h * 0.25:.1f} {x + lean * 0.4:.1f},"
           f"{y - h * 0.38:.1f}", w=1.4)
    top = y - h
    crown = (f"M{x - r:.1f},{y - h * 0.42:.1f} C{x - r * 1.2:.1f},{top + h * 0.3:.1f} {x - r * 0.5:.1f},{top + h * 0.12:.1f} "
             f"{x - r * 0.1 + lean:.1f},{top + h * 0.16:.1f} C{x + r * 0.2 + lean:.1f},{top - h * 0.02:.1f} "
             f"{x + r * 0.9 + lean:.1f},{top + h * 0.05:.1f} {x + r * 0.8 + lean:.1f},{top + h * 0.28:.1f} "
             f"C{x + r * 1.3 + lean:.1f},{top + h * 0.38:.1f} {x + r * 1.1 + lean:.1f},{y - h * 0.4:.1f} "
             f"{x + r * 0.6:.1f},{y - h * 0.36:.1f} C{x + r * 0.2:.1f},{y - h * 0.3:.1f} {x - r * 0.6:.1f},{y - h * 0.3:.1f} "
             f"{x - r:.1f},{y - h * 0.42:.1f} Z")
    d.shape(crown, w=1.2)
    d.hatch(crown, angle=50 + seed * 6, pitch=1.6)


def lechuguilla(d: Drawing, x: float, y: float, s: float, stalk: float = 0.0) -> None:
    """An agave rosette of stiff leaves, with a tall flower stalk if `stalk` is given."""
    leaves = []
    for a in (-80, -60, -38, -16, 8, 30, 52, 74, 90):
        r = s * (0.7 + 0.3 * math.cos(math.radians(a)))
        ang = math.radians(a - 90)
        leaves.append(f"M{x:.1f},{y:.1f} L{x + r * math.cos(ang) * 0.75:.1f},{y + r * math.sin(ang):.1f}")
    d.line(" ".join(leaves), w=1.0)
    if stalk:
        d.line(f"M{x:.1f},{y - s * 0.6:.1f} C{x + 0.5:.1f},{y - stalk * 0.5:.1f} {x + 1.2:.1f},{y - stalk * 0.8:.1f} "
               f"{x + 1.6:.1f},{y - stalk:.1f}", w=1.0)
        d.dots([(x + 1.0 + (i % 2 - 0.5) * 1.6, y - stalk * (0.62 + i * 0.075)) for i in range(5)], r=0.8)


def pronghorn(d: Drawing, x: float, y: float, s: float) -> None:
    """A pronghorn at full stretch, facing east: dark back and flank, the white rump and belly left bare."""
    def pt(u, v):
        return f"{x + u * s:.1f},{y + v * s:.1f}"
    body = (f"M{pt(0, 0)} C{pt(2, -2)} {pt(10, -2)} {pt(14, -1)} L{pt(17, -7)} L{pt(19, -8)} L{pt(22.5, -5.5)} "
            f"L{pt(21.5, -4.4)} L{pt(18, -4.2)} L{pt(16.5, 1)} C{pt(16, 3.5)} {pt(12, 4)} {pt(8, 4)} "
            f"C{pt(4, 4.4)} {pt(1, 4)} {pt(0, 3)} C{pt(-1, 2)} {pt(-1, 1)} {pt(0, 0)} Z")
    d.line(f"M{pt(15, 3)} L{pt(21, 7.5)} M{pt(14, 3.5)} L{pt(19.5, 9)} M{pt(2, 3.5)} L{pt(-4.5, 7)} "
           f"M{pt(3, 4)} L{pt(-2.5, 9)}", w=0.9)
    d.shape(body, w=1.0)
    d.hatch(f"M{pt(3, -1.4)} C{pt(8, -2)} {pt(12, -1.8)} {pt(14, -1)} L{pt(16.4, 1)} L{pt(3, 1.6)} Z", angle=60,
            pitch=1.2)
    d.line(f"M{pt(18.4, -7.8)} l{-0.2 * s:.1f},{-3.4 * s:.1f} M{pt(19.4, -7.8)} l{0.9 * s:.1f},{-3 * s:.1f}", w=0.8,
           halo=False)


# 1. Wolves running the antelope on the snow, by moonlight (1-01) ---------------------------------------
def wolves_antelope() -> Drawing:
    d = Drawing("wolves-antelope")
    d.shape(circle(82, 13, 6), w=1.2)
    hills = "M4,38 C14,32 22,31 30,35 C38,29 50,29 58,34 C66,31 78,30 92,36"
    d.line(hills, w=1.0)
    d.hatch(hills + " L92,41 L4,41 Z", angle=20, pitch=2.6, w=0.6)
    # Three antelope wheeling away to the east, two wolves loping after them, the near one larger.
    for ax, ay, s in ((54, 60, 1.25), (70, 52, 1.0), (72, 70, 1.15)):
        pronghorn(d, ax, ay, s)
    run = lambda x, y: (x, y + (0.10 * (x - 50) if x > 60 else 0))  # noqa: E731
    wolf(d, 0.34, 10, 40, bend=run, w=1.2)
    wolf(d, 0.42, 20, 52, bend=run, w=1.3)
    # The powder kicked up, the snow plain and the juniper where Billy lay.
    d.dots([(48, 76), (52, 73), (56, 78), (88, 80), (66, 84), (40, 84)], r=0.6)
    juniper(d, 10, 90, 18, seed=1)
    d.ground(20, 94, 89, ticks=5, seed=21)
    return d


# 2. The dog at the gate, watching Billy and Bird ride out (1-04) ---------------------------------------
def billy_and_the_dog() -> Drawing:
    d = Drawing("billy-and-the-dog")
    # The stockgate: two posts and the wire, behind the dog.
    d.line("M8,56 L8,86 M30,58 L30,86", w=1.6)
    d.line("M8,62 L30,64 M8,70 L30,71 M8,78 L30,78", w=0.7, halo=False)
    rider(d, k=0.74, ox=26, oy=18)
    # The dog standing at the gate looking after him.
    wolf(d, 0.26, 4, 64, w=1.1)
    d.ground(4, 94, 88, ticks=7, seed=14)
    return d


# 3. Billy riding south with the wolf on the rope, through the lechuguilla (1-09) -----------------------
def wolf_on_the_rope() -> Drawing:
    d = Drawing("wolf-on-the-rope")
    for x, y, s, st in ((10, 70, 6, 26), (88, 66, 5, 0), (62, 86, 4, 0)):
        lechuguilla(d, x, y, s, st)
    rider(d, k=0.66, ox=34, oy=24)
    # The rope from the saddlehorn back to her collar; she hobbles behind, head low.
    wolf(d, 0.36, 4, 62, bend=lambda x, y: (x, y + (0.12 * (x - 70) if x > 70 else 0)), w=1.2)
    d.line("M64,50 C54,60 46,70 36,74", w=1.0)
    grass(d, [(24, 88), (46, 89), (80, 88)], h=3.4)
    d.ground(4, 94, 90, ticks=6, seed=17)
    return d


# 4. Billy and the wolf by the night fire, side by side (1-09) ------------------------------------------
def wolf_by_the_fire() -> Drawing:
    d = Drawing("wolf-by-the-fire")
    d.dots([(10, 12), (26, 8), (58, 10), (84, 16), (72, 6), (40, 18)], r=0.7)
    # Billy sitting wrapped in his blanket, hat on, the saddle at his back.
    d.shape("M6,80 C6,74 10,70 16,70 C20,70 22,74 22,80 Z", w=1.4)
    d.hatch("M6,80 C6,74 10,70 16,70 C20,70 22,74 22,80 Z", angle=0, pitch=2.0)
    blanket = "M14,82 C12,72 14,58 20,52 C24,48 30,48 33,53 C37,60 38,72 37,82 Z"
    d.shape(blanket)
    d.edge_shade(blanket, dx=-3, dy=-2)
    d.line("M24,52 C26,62 26,72 25,82", w=0.8, halo=False)
    d.shape(circle(26, 45, 4.2), w=1.3)
    d.shape("M18,41.5 C22,39.8 30,39.8 34,41.5 C30,43.2 22,43.2 18,41.5 Z", w=1.3)
    d.shape("M22.2,41 C22.2,35 29.8,35 29.8,41 Z", w=1.3)
    # The fire: a few sticks crossed, flames and sparks.
    d.line("M38,84 L54,78 M40,78 L54,84", w=1.6)
    flame = "M40,79 C38,72 44,70 43,62 C48,66 48,70 47,72 C50,66 52,64 51,58 C56,66 56,74 52,79 Z"
    d.shape(flame, w=1.2)
    d.line("M45,77 C44,73 47,71 46,68 M50,76 C51,72 52,70 52,67", w=0.7, halo=False)
    d.dots([(48, 52), (45, 46), (51, 42)], r=0.6)
    # The wolf beside him on the rope, sitting and watching the fire, her eye lit.
    sit = lambda x, y: (x, y + (0.32 * (40 - x) if x < 40 else 0) - (6 if x > 66 else 0))  # noqa: E731
    wolf(d, 0.4, 60, 52, flip=True, bend=sit, w=1.3)
    d.dots([(66.2, 64.6)], r=0.7)
    d.line("M37,70 C46,64 56,70 64,74", w=0.7, halo=False)
    d.ground(4, 94, 87, ticks=6, seed=19)
    return d


# 5. Billy holding the wolf up in the ford of the Bavispe (1-09) ----------------------------------------
def wolf_ford() -> Drawing:
    d = Drawing("wolf-ford")
    # The far bank: cane and willow.
    d.line("M4,40 C20,38 40,39 60,37 C72,36 84,37 92,38", w=0.9)
    d.line(" ".join(f"M{x},{40 - (x % 3)} l{(x % 5) - 2},{-14 - (x * 7) % 9}" for x in range(8, 90, 6)), w=0.8)
    # Billy thigh-deep, his hips and belt above the water, his arm under the wolf's chest holding her up.
    body = "M24,66 L24.6,52 C24,46 27,40 33,38 C39,38 43,42 43,48 L43.4,52 L44,66 Z"
    d.shape(body)
    d.edge_shade(body, dx=-3, dy=-2)
    d.line("M24.4,54 L43.6,54", w=1.4)
    d.line("M34,56 L34,66", w=0.9, halo=False)
    d.shape(circle(34, 32, 4.6), w=1.4)
    d.shape("M25,27.5 C29,25.8 39,25.8 43,27.5 C39,29.2 29,29.2 25,27.5 Z", w=1.4)
    d.shape("M29.6,27 C29.6,21 38.4,21 38.4,27 Z", w=1.4)
    # The wolf: head and neck up out of the water, ears pricked, the long muzzle strapped shut.
    head = ("M50,66 C50,60 52,55 56,52 L56.5,45.5 L59.6,50.4 L61,45 L63.2,50.6 C67,51.6 72,53.6 78,55.8 "
            "C79.6,56.4 79.4,58 78,58.4 C73,59 68,59.4 64,60 C61,62 59,64 58,66 Z")
    d.shape(head, w=1.4)
    d.hatch("M50,66 C50,60 52,55 56,52 L60,51 C59,56 58,61 57,66 Z", angle=60, pitch=1.5)
    d.line("M70,54 L69.6,59.4 M72.6,54.8 L72.2,59", w=0.8, halo=False)
    d.dots([(64.6, 54.2), (78.4, 56.6)], r=0.7)
    d.line("M41,44 C46,50 50,58 56,62", w=1.8)
    # The river running round them.
    d.line("M4,66 C10,64 18,67 24,66 M44,66 C47,65 49,66 50,66 M58,66 C68,64 78,67 92,65", w=1.1)
    d.line("M8,72 l12,0 M28,71 l14,0.4 M52,72 l10,0 M70,71 l16,0 M14,78 l16,0 M40,78 l10,0 M60,79 l18,0 "
           "M6,85 l10,0 M26,85 l18,0 M54,85 l12,0 M76,86 l12,0", w=0.8)
    return d


# 6. The wolf shown in a sheeted cart at the fair (1-09) ------------------------------------------------
def wolf_cart() -> Drawing:
    d = Drawing("wolf-cart")
    # A tent of sheeting over the little cart, open at the end, her shape in the straw.
    tent = "M14,60 L22,30 L66,30 L80,60 Z"
    d.shape(tent)
    d.line("M22,30 L20,60 M44,30 L44,60 M66,30 L68,60", w=0.8, halo=False)
    d.line("M14,60 C24,56 34,58 44,56 C54,58 66,56 80,60", w=0.8, halo=False)
    d.edge_shade(tent, dx=-3, dy=-2)
    door = "M48,60 L50,40 L62,40 L66,60 Z"
    d.shape(door, w=1.2)
    d.hatch(door, angle=45, pitch=1.6, cross=True)
    d.shape("M52,60 C52,56 56,54 60,55 C62,56 63,58 63,60 Z", w=0.9)
    # The cart bed, its big wheel and the shaft let down.
    bed = poly((10, 60), (84, 60), (84, 66), (10, 66))
    d.shape(bed, w=1.5)
    d.edge_shade(bed, dx=0, dy=-2.4)
    d.shape(circle(30, 72, 11), w=1.6)
    d.line(" ".join(f"M30,72 L{30 + 11 * math.cos(a):.1f},{72 + 11 * math.sin(a):.1f}" for a in
                    [i * math.pi / 4 for i in range(8)]), w=0.8, halo=False)
    d.shape(circle(30, 72, 2), w=1.0)
    d.line("M84,63 L94,84", w=1.4)
    # The sign on its stake, lettered, and the stakes and cords of the tent.
    d.line("M88,58 L88,82", w=1.3)
    d.shape(poly((80, 42), (94, 42), (94, 56), (80, 56)), w=1.2)
    d.line("M82.5,46 l9,0 M82.5,49.5 l7,0 M82.5,53 l8,0", w=0.7, halo=False)
    d.line("M14,60 L6,74 M22,30 L4,48", w=0.6, halo=False)
    d.ground(2, 94, 86, ticks=7, seed=23)
    return d


# 7. Billy carrying the dead wolf to the mountains across his saddle (1-10) -----------------------------
def carrying_the_wolf() -> Drawing:
    d = Drawing("carrying-the-wolf")
    # The tall escarpments of the Pilares ahead, grey before the dawn.
    ridge = "M4,46 L14,30 L22,36 L30,20 L40,30 L50,22 L60,34 L70,26 L80,36 L92,30"
    d.line(ridge, w=1.1)
    d.hatch(ridge + " L92,50 L4,50 Z", angle=70, pitch=2.6, w=0.6)
    rider(d, k=0.74, ox=12, oy=20)
    # Across the bow of the saddle, the wolf wrapped in the sheet, the ends hanging down either side.
    bundle = ("M40,47 C48,43 60,43 67,46 C70,48 71,55 68,59 C66,60 64,59 64,56 C58,53 49,53 45,56 C44,60 41,61 39,59 "
              "C37,55 37,49 40,47 Z")
    d.shape(bundle, w=1.4)
    d.line("M48,45 L48.5,53.8 M57,44.6 L57,53.4", w=0.7, halo=False)
    d.edge_shade(bundle, dx=-2, dy=-2.4)
    d.line("M40,59 C39,63 39,66 40.5,69", w=1.5)
    d.ground(4, 94, 88, ticks=6, seed=27)
    return d


# 8. The wolf's cairn on the high pass (2-01) -----------------------------------------------------------
def wolf_cairn() -> Drawing:
    d = Drawing("wolf-cairn")
    # The saddle of the pass between two shoulders of mountain.
    left = "M4,70 L4,30 C12,26 20,30 28,40 C34,48 40,54 48,58 L48,70 Z"
    right = "M48,58 C56,52 62,40 70,28 C76,22 86,24 92,30 L92,70 Z"
    d.shape(left, w=1.3)
    d.shape(right, w=1.3)
    d.hatch(right, angle=60, pitch=2.0)
    d.edge_shade(left, dx=-4, dy=-3)
    # The cairn: scree stones heaped long and low, the size of a lying wolf.
    stones = [(30, 78, 6, 4), (40, 77, 6, 4.5), (51, 77, 6.5, 4.5), (62, 78, 6, 4), (35, 71, 5.5, 4), (46, 70, 6, 4.2),
              (57, 71, 5.5, 4), (41, 64.5, 5, 3.6), (51, 64, 5, 3.6), (46, 59, 4.4, 3.2)]
    for x, y, rx, ry in stones:
        st = (f"M{x - rx:.1f},{y:.1f} C{x - rx:.1f},{y - ry:.1f} {x - rx * 0.2:.1f},{y - ry * 1.1:.1f} {x + rx * 0.4:.1f},"
              f"{y - ry:.1f} C{x + rx:.1f},{y - ry * 0.8:.1f} {x + rx * 1.05:.1f},{y:.1f} {x + rx * 0.6:.1f},{y + ry * 0.7:.1f} "
              f"C{x:.1f},{y + ry:.1f} {x - rx * 0.8:.1f},{y + ry * 0.7:.1f} {x - rx:.1f},{y:.1f} Z")
        d.shape(st, w=1.2)
        d.edge_shade(st, dx=-1.8, dy=-1.8)
    # Loose scree at its foot, and a juniper leaning in the wind.
    d.dots([(20, 84), (24, 82), (70, 83), (76, 85), (66, 86), (28, 86)], r=0.8)
    juniper(d, 84, 86, 18, seed=2)
    d.ground(4, 94, 88, ticks=6, seed=29)
    return d


# 9. Billy with his holly bow, the hawk overhead (2-01) ------------------------------------------------
def billy_bow_hawk() -> Drawing:
    d = Drawing("billy-bow-hawk")
    rider(d, k=0.74, ox=0, oy=24)
    # The bow drawn and raised towards the hawk: a curved stave and the string.
    d.line("M47,14 C58,14 64,26 59,40", w=1.4)
    d.line("M47,14 L59,40", w=0.6, halo=False)
    d.line("M37,44 L58,27", w=1.8)
    # The hawk wheeling high up, the arrow locked in its breast.
    hawk = ("M68,22 C72,18 76,16 80,17 C82,14 86,12 92,12 C88,15 86,18 84,20 C86,21 87,23 86,24 C83,23 81,22 79,22 "
            "C76,24 72,24 68,22 Z")
    d.shape(hawk, w=1.2)
    d.hatch(hawk, angle=-30, pitch=1.4)
    d.line("M70,30 L79,21", w=0.9)
    d.line("M70,30 l-1.6,0.2 M70,30 l0.2,1.6", w=0.7, halo=False)
    # Mountain shoulder and grass of the high saddle.
    d.line("M60,90 C66,80 74,72 92,66", w=1.0)
    grass(d, [(10, 90), (60, 90), (84, 90)], h=3.6)
    d.ground(4, 94, 91, ticks=6, seed=31)
    return d


# 10. El Tigre: mud and stick jacales on a slope below the mine (2-01) ----------------------------------
def el_tigre() -> Drawing:
    d = Drawing("el-tigre")
    # The mountainside, the mine's dump of tailings and a small headframe above the town.
    d.line("M4,50 C20,40 34,30 52,22 C64,16 78,12 92,12", w=1.1)
    d.line("M63,27 C68,31 76,34 86,36", w=0.9)
    d.dots([(68, 30.5), (72, 32.5), (77, 34), (82, 35.5), (74, 35.6), (80, 37.4)], r=0.7)
    d.line("M60,27 L62,12 L64,26 M60.8,20 L63.2,20 M62,12 l-2.6,0.6", w=1.0)
    # Three jacales stepping down the slope: walls of upright sticks, flat mud roofs, cowhide doors.
    for x, y, wd, ht in ((10, 82, 26, 16), (38, 70, 24, 14), (62, 60, 22, 13)):
        roof = poly((x - 2, y - ht), (x + wd + 2, y - ht - 2), (x + wd + 2, y - ht + 1), (x - 2, y - ht + 3))
        wall = poly((x, y), (x, y - ht + 2), (x + wd, y - ht), (x + wd, y))
        d.shape(wall, w=1.3)
        d.line(" ".join(f"M{xx:.1f},{y:.1f} L{xx:.1f},{y - ht + 2 - (xx - x) * 2 / wd:.1f}"
                        for xx in [x + 2.2 * i for i in range(1, int(wd / 2.2))]), w=0.6, halo=False)
        door = poly((x + wd * 0.55, y), (x + wd * 0.55, y - ht * 0.6), (x + wd * 0.8, y - ht * 0.62), (x + wd * 0.8, y))
        d.shape(door, w=1.1)
        d.hatch(door, angle=80, pitch=1.4)
        d.shape(roof, w=1.3)
        d.edge_shade(wall, dx=-2.5, dy=0)
    d.line("M4,84 C20,82 34,74 50,70 C62,66 76,62 92,52", w=0.9, halo=False)
    d.ground(4, 94, 88, ticks=6, seed=33)
    return d


# 11. The wagon road down the eastern escarpment, switchback on switchback (2-01) -----------------------
def escarpment_road() -> Drawing:
    d = Drawing("escarpment-road")
    # The rim, and the granite face falling away from it into the barranca, the shade on its east flank.
    d.line("M4,24 C20,20 40,18 60,20 C72,21 84,22 92,26", w=1.4)
    d.line("M60,20 C66,40 70,64 66,92", w=1.1)
    d.hatch("M60,20 C72,21 84,22 92,26 L92,92 L66,92 C70,64 66,40 60,20 Z", angle=65, pitch=1.9)
    d.line("M24,30 l4,8 M34,52 l3,7 M12,64 l3,6 M44,84 l3,5", w=0.7, halo=False)
    # The road, a hairspring of switchbacks down the face.
    road = ("M10,24 L54,30 C58,31 58,34 54,35 L18,40 C14,41 14,44 18,45 L52,50 C56,51 56,54 52,55 L20,60 "
            "C16,61 16,64 20,65 L50,70 C54,71 54,74 50,75 L22,80 C18,81 18,84 22,85 L58,90")
    d.line(road, w=3.0)
    d.line(road, w=1.3, color=PAPER, halo=False)
    # Scrub juniper on the rim, leaning in an old wind.
    juniper(d, 70, 22, 13, seed=3)
    juniper(d, 84, 24, 10, seed=4)
    juniper(d, 8, 23, 9, seed=5)
    return d


# 12. The church of San Miguel at Bavispe, on its plaza (2-03) ------------------------------------------
def bavispe_church() -> Drawing:
    d = Drawing("bavispe-church")
    # The nave running back to the west, its long pitched roof.
    nave = "M10,84 L10,52 L44,52 L44,84 Z"
    roof = "M8,52 L16,40 L44,40 L46,52 Z"
    d.shape(nave)
    d.shape(roof, w=1.4)
    d.hatch(roof, angle=0, pitch=1.8)
    for x in (16, 26, 36):
        win = f"M{x},70 L{x},62 C{x},58 {x + 4},58 {x + 4},62 L{x + 4},70 Z"
        d.shape(win, w=0.9)
        d.hatch(win, angle=45, pitch=1.3)
    # The tower front: a tall gable, pointed openings and the spire with its cross.
    tower = "M44,84 L44,44 L50,38 L50,28 L54,24 L58,28 L58,38 L64,44 L64,84 Z"
    d.shape(tower)
    d.edge_shade(tower, dx=-3, dy=0)
    spire = "M50,28 L54,8 L58,28 Z"
    d.shape(spire, w=1.3)
    d.hatch("M54,8 L58,28 L54,28 Z", angle=60, pitch=1.4)
    d.line("M54,8 L54,2 M52,4 L56,4", w=1.0)
    for x, y in ((49.5, 58), (55.5, 58)):
        d.shape(f"M{x},{y + 8} L{x},{y + 2} L{x + 1.5},{y - 1} L{x + 3},{y + 2} L{x + 3},{y + 8} Z", w=0.9)
        d.hatch(f"M{x},{y + 8} L{x},{y + 2} L{x + 1.5},{y - 1} L{x + 3},{y + 2} L{x + 3},{y + 8} Z", angle=45, pitch=1.2)
    d.shape("M52,36 L52,32 L54,29.5 L56,32 L56,36 Z", w=0.9)
    door = "M49,84 L49,74 C49,68 59,68 59,74 L59,84 Z"
    d.shape(door, w=1.3)
    d.hatch(door, angle=45, pitch=1.6, cross=True)
    d.line("M44,64 L64,64 M44,44 L64,44", w=0.8, halo=False)
    # A cypress beside it, and the meat-vendor's cart standing in the plaza.
    cyp = "M74,84 C70,70 72,52 76,38 C80,52 82,70 78,84 Z"
    d.shape(cyp, w=1.2)
    d.hatch(cyp, angle=60, pitch=1.6)
    d.shape(poly((80, 74), (94, 74), (94, 80), (80, 80)), w=1.1)
    d.shape(circle(84, 83, 3), w=1.0)
    d.line("M80,76 L74,80", w=0.9)
    d.ground(2, 94, 87, ticks=8, seed=37)
    return d


SUBJECTS = {
    "wolves-antelope": wolves_antelope, "billy-and-the-dog": billy_and_the_dog, "wolf-on-the-rope": wolf_on_the_rope, "wolf-by-the-fire": wolf_by_the_fire, "wolf-ford": wolf_ford,
    "wolf-cart": wolf_cart, "carrying-the-wolf": carrying_the_wolf, "wolf-cairn": wolf_cairn,
    "billy-bow-hawk": billy_bow_hawk, "el-tigre": el_tigre, "escarpment-road": escarpment_road,
    "bavispe-church": bavispe_church,
}
