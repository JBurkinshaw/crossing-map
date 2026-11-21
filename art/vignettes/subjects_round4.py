"""Vignettes of the fourth round: three of design section 10's first candidates at their stops, and fourteen scenes
along the journeys, each set at a point along its leg (decision 0066). Loaded by art/vignettes/make_vignettes.py.

Each is checked against the episode that first shows it and drawn after the period reference its seed `credit`
names: the riders and horses are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and
IV helpers, the wolves the traced US Fish and Wildlife Service outline. Everything else is drawn by hand. Light from
the north-west, as everywhere: shade on each shape's south-east side.
"""

import math

import svgelements as se

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly, traced, warp
from art.vignettes.subjects_parts_1_2 import wolf
from art.vignettes.subjects_parts_3_4 import blob, cottonwood, pine, place, rider, steer
from art.vignettes.subjects_round3 import chevrons, figure, horse

# A mule's long ears, in the traced horse's units (the poll is about (86, 31)).
MULE_EARS = "M84.4,32 L81.6,24 M86.8,31.4 L86.4,23.6"


def chain(d: Drawing, x0: float, y0: float, x1: float, y1: float, links: int):
    """A chain pulled taut between two points, its links alternately flat and edge-on."""
    for i in range(links):
        t = (i + 0.5) / links
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if i % 2 == 0:
            a = math.degrees(math.atan2(y1 - y0, x1 - x0))
            r = math.radians(a)
            dx, dy = 1.8 * math.cos(r), 1.8 * math.sin(r)
            d.line(f"M{x - dx:.1f},{y - dy:.1f} L{x + dx:.1f},{y + dy:.1f}", w=1.4)
        else:
            d.shape(ellipse(x, y, 1.9, 1.3), w=0.9, fill=False)


def shift(d: Drawing, since: int, dx: float, dy: float, k: float = 1.0):
    """Move and scale (about the origin) everything drawn since item `since`, to lay out a group drawn in place."""
    m = se.Matrix(k, 0, 0, k, dx, dy)
    for i in range(since, len(d.items)):
        kind, path, opts = d.items[i]
        moved = [(x * k + dx, y * k + dy) for x, y in path] if kind == "dots" else (se.Path(path) * m).d()
        d.items[i] = (kind, moved, opts)


def round_(cx: float, cy: float, rx: float, ry: float | None = None) -> str:
    """An ellipse as four cubic curves, so that warp can bend it (warp drops arcs)."""
    ry = rx if ry is None else ry
    c = 0.5523
    return (f"M{cx - rx},{cy} C{cx - rx},{cy - ry * c} {cx - rx * c},{cy - ry} {cx},{cy - ry} "
            f"C{cx + rx * c},{cy - ry} {cx + rx},{cy - ry * c} {cx + rx},{cy} "
            f"C{cx + rx},{cy + ry * c} {cx + rx * c},{cy + ry} {cx},{cy + ry} "
            f"C{cx - rx * c},{cy + ry} {cx - rx},{cy + ry * c} {cx - rx},{cy} Z")


def star(cx: float, cy: float, r: float, inner: float = 0.4) -> str:
    """A five-pointed star, one point up."""
    pts = []
    for k in range(10):
        a = math.radians(-90 + 36 * k)
        rr = r if k % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return poly(*pts)


def water(d: Drawing, y: float, x0: float = 2, x1: float = 94, seed: int = 0):
    """Ripple lines on still or slow water, a few short ones under the long."""
    d.line(f"M{x0},{y} C{x0 + 20},{y - 1} {x1 - 40},{y + 1} {x1},{y - 0.4}", w=0.9)
    rows = [(y + 3.4, 10, 12), (y + 3, 40, 10), (y + 6, 22, 14), (y + 6.4, 66, 10), (y + 3.6, 76, 8)]
    d.line(" ".join(f"M{x0 + (x + seed * 7) % (x1 - x0 - w):.1f},{yy:.1f} l{w},0" for yy, x, w in rows), w=0.6,
           halo=False)


# 1. The male wolf in the trap, snarling at the she-wolf (1-04) ----------------------------------------
def wolf_mate() -> Drawing:
    d = Drawing("wolf-mate")
    # A low ridge of the Sonoran mountains behind.
    ridge = "M2,30 C12,24 20,22 30,26 C40,20 52,20 60,24 C70,20 82,20 94,24"
    d.line(ridge, w=1.0)
    d.hatch(ridge + " L94,28 L2,32 Z", angle=20, pitch=3.6, w=0.5)
    # The she-wolf lying flat just beyond the chain's reach, ears back, facing him.
    lie = lambda x, y: (x, 50 + (y - 50) * 0.35 if y > 50 else y + (6 if x > 70 else 3))  # noqa: E731
    wolf(d, 0.42, 56, 64, flip=True, bend=lie, w=1.2)
    # The male braced back on the chain, head low and lips drawn off his teeth at her.
    stand = lambda x, y: (x, y + (8 if x > 74 else 0))  # noqa: E731
    wolf(d, 0.74, -2, 30, bend=stand, w=1.6)
    d.line("M57,66.4 L62.4,64.6 M57.4,69 L62.6,68.4", w=0.9, halo=False)
    d.line("M58,65.6 l0.6,1.6 M59.8,65 l0.6,1.6 M61.4,64.6 l0.4,1.4", w=0.6, halo=False)
    # The steel trap shut on his near forefoot, the chain drawn taut back to the drag in the brush.
    d.shape(ellipse(49, 86.4, 4.4, 1.8), w=1.3, fill=False)
    d.line("M44.6,86.6 L53.4,86.2", w=0.9, halo=False)
    chain(d, 44, 87.4, 12, 89, 8)
    d.line("M12,89 L6,86.4 M12,89 L6.6,92.4", w=1.6)
    d.line("M3,84 l3,-6 M6,85 l1,-7 M9,84 l3,-5", w=0.9)
    d.ground(14, 94, 90, ticks=6, seed=401)
    return d


# 2. The rancher's Model A on the road, the wolf held in the bar ditch (1-08) ---------------------------
def model_a_wolf() -> Drawing:
    d = Drawing("model-a-wolf")
    truck = len(d.items)
    # The road and the running fence beyond it.
    d.line("M2,62 C30,61 60,61 94,60", w=0.9)
    d.line("M60,48 L94,46 M60,54 L94,52.4", w=0.6, halo=False)
    for x in (64, 78, 92):
        d.line(f"M{x},{44 + (x - 64) * -0.05:.1f} L{x},{60 - (x - 64) * 0.04:.1f}", w=1.4)
    # The Model A pickup, facing west: closed cab, tall radiator shell, the short bed with its tailgate.
    bed = poly((36, 54), (36, 42), (56, 42), (56, 54))
    d.shape(bed, w=1.5)
    d.line("M36,46 L56,46", w=0.6, halo=False)
    cab = "M22,54 L22,34 C22,31 24,30 26,30 L35,30 C36,30 37,31 37,33 L37,54 Z"
    d.shape(cab)
    win = poly((25, 33), (34, 33), (34, 40), (25, 40))
    d.shape(win, w=0.9)
    d.hatch(win, angle=45, pitch=1.3)
    d.line("M24,44 L35,44", w=0.6, halo=False)
    hood = "M6,54 L6,41 C6,39.6 7,39 8.6,39 L22,37.6 L22,54 Z"
    d.shape(hood)
    d.line("M12,42 L12,50 M14.4,42 L14.4,50 M16.8,42 L16.8,50", w=0.6, halo=False)
    shell = "M3.6,54 L3.6,40 C3.6,38.4 6.6,38.4 6.6,40 L6.6,54 Z"
    d.shape(shell, w=1.1)
    d.hatch(shell, angle=0, pitch=0.9)
    d.shape(circle(6.6, 44.6, 1.8), w=0.9)
    d.edge_shade(cab, dx=-2.5, dy=-2)
    # Sweeping fenders over spoked wheels, and the running board.
    d.shape("M2,58 C3,50 17,49 20,57 L18,57 C16,52 7,52 5,58 Z", w=1.2)
    d.shape("M40,57 C41,49 55,49 58,57 L56,57 C54,52 45,52 43,58 Z", w=1.2)
    d.line("M19,57 L41,57", w=1.1)
    for cx in (11.6, 49.6):
        d.shape(circle(cx, 59, 5.6), w=1.5)
        d.line(" ".join(f"M{cx},59 L{cx + 5 * math.cos(a):.1f},{59 + 5 * math.sin(a):.1f}"
                        for a in (i * math.pi / 6 for i in range(12))), w=0.4, halo=False)
        d.shape(circle(cx, 59, 1.4), w=0.8)
    d.dots([(62, 40), (66, 37), (60, 34), (70, 41)], r=0.5)
    shift(d, truck, 0, -12)
    # The bar ditch below the road: the wolf crouched in it, her jaws gagged with a stick, and the boy kneeling
    # over her with his arms round her neck.
    ditch = len(d.items)
    d.line("M2,64 C20,68 40,69 60,68 C74,67.6 86,66 94,64", w=0.9)
    lie = lambda x, y: (x, 50 + (y - 50) * 0.35 if y > 50 else y + (6 if x > 70 else 3))  # noqa: E731
    wolf(d, 0.5, 40, 64, bend=lie, w=1.3)
    d.line("M80,77.4 L87.6,75", w=1.3)
    # The boy on his knees behind her, bent over with his arms round her neck.
    d.line("M34,89 L44,89 L43,80", w=1.5)
    torso = "M40,81 C40,76 44,70 50,67 L55,69 C52,74 49,79 47,82 Z"
    d.shape(torso, w=1.3)
    d.edge_shade(torso, dx=-1.6, dy=-1.6)
    d.shape(circle(55, 64, 2.6), w=1.0)
    d.shape("M50.6,62.6 L59.6,62.6 L57.2,61.6 C57.2,58.6 53,58.6 53,61.6 Z", w=0.9)
    d.line("M51,69 L62,73 L76,74 M49,72 L60,77 L74,77.6", w=1.2)
    shift(d, ditch, 0, -4)
    d.ground(2, 94, 88, ticks=6, seed=417)
    return d


# 3. The miners carrying their dead companion home on a bier (1-09) -------------------------------------
def tumpline_bearers() -> Drawing:
    d = Drawing("tumpline-bearers")
    # Scrub oak on the slope of the draw where they nooned, and the smoke of their fire.
    for x, base, h, seed in ((8, 50, 34, 1), (20, 48, 26, 2), (86, 48, 30, 3)):
        pine(d, x, base, h, seed=420 + seed)
    d.line("M2,52 C24,50 50,50 94,48", w=0.8)
    d.line("M62,56 C58,50 64,46 60,40 C57,36 62,32 60,28", w=0.6, halo=False)
    d.line("M58,60 l2,-3 l1.2,2 l1.2,-3 l1.4,4", w=1.0)
    # The bier lying apart in the leaves: two poles, a cowhide sling, the body in its tied canvas under green
    # branches.
    d.line("M4,82 L60,76 M6,86 L62,80", w=1.6)
    sling = "M10,84.4 C18,87 46,84 56,79 L56,75.6 C46,80 20,82 10,81 Z"
    d.shape(sling, w=1.1)
    d.hatch(sling, angle=60, pitch=1.6)
    body = "M10,80 C10,74 16,72 24,72 L48,69 C54,68.6 58,70 58,73 C58,76 54,77 48,77.4 L24,80 C16,81 10,82 10,80 Z"
    d.shape(body, w=1.6)
    d.line("M20,72.6 L21,80.4 M30,71.6 L31,79.4 M40,70.6 L41,78.6 M50,69.2 L50.6,77.4", w=0.8, halo=False)
    d.line("M24,71 C26,68 29,68 30,70 M36,70 C38,66 42,66 43,69 M46,68 c2,-3 5,-3 6,0", w=0.8)
    d.line("M27,69.4 l1,-1.6 M40,68 l1.4,-1.2 M49.6,67.6 l1.2,-1.6", w=0.6, halo=False)
    # One man sitting by it with his knees drawn up, and one standing, his load slung on the tumpline across
    # his brow.
    sit = "M64,88 L64,78 C64,74.6 66,73 68,73 C70.4,73 72,74.6 72,78 L76,76 L78,82 L78,88 Z"
    d.shape(sit, w=1.2)
    d.edge_shade(sit, dx=-1.6, dy=-1.6)
    d.shape(circle(68, 69.4, 2.6), w=1.0)
    d.shape("M63.4,67.6 L72.6,67.6 L70.2,66.6 C70.2,63.6 65.8,63.6 65.8,66.6 Z", w=0.9)
    p = figure(d, 88, 88, 36, flip=True)
    pack = p("M-2.6,-19 L-8.6,-19 L-9.4,-6.6 L-3,-6.6 Z")
    d.shape(pack, w=1.1)
    d.hatch(pack, angle=0, pitch=1.4)
    d.line(p("M-8,-18.6 C-6,-22 -3,-23 1.8,-22.4"), w=0.9)
    d.ground(2, 94, 90, ticks=7, seed=404)
    return d


# 4. The horse in the storm by the ruined compound (2-03) -----------------------------------------------
def hail_shelter() -> Drawing:
    d = Drawing("hail-shelter")
    # The storm moving off west: cloud base and a fork of lightning.
    d.line(blob(22, 10, 22, 7, 9, seed=405, depth=0.25), w=0.9)
    d.hatch("M2,12 C14,18 30,18 46,12 L46,16 C30,22 14,22 2,16 Z", angle=-30, pitch=1.8)
    d.line("M18,18 L13,28 L18,27 L10,42", w=1.4)
    # The rain.
    d.line(" ".join(f"M{x},{y} l-2,6" for x, y in ((56, 6), (64, 10), (72, 4), (80, 8), (88, 4), (60, 22), (70, 18),
                                                   (82, 20), (90, 16), (52, 32), (92, 30))), w=0.6, halo=False)
    # The roofless walls of the old compound, a doorway, and the sagging roof in the corner room.
    walls = ("M4,82 L4,48 C8,46 10,50 14,47 L20,44 L22,50 C26,48 28,52 32,50 L36,52 L36,58 C40,56 44,60 48,58 "
             "L50,64 L50,82 Z")
    d.shape(walls)
    d.edge_shade(walls, dx=-3.5, dy=-2.5)
    door = poly((18, 82), (18, 64), (26, 64), (26, 82))
    d.shape(door, w=1.2)
    d.hatch(door, angle=45, pitch=1.4, cross=True)
    d.line("M4,50 L22,46 M6,54 L20,50", w=1.0)
    d.line("M40,70 l3,0.4 M8,70 l2.6,0 M30,58 l2,0.4", w=0.7, halo=False)
    d.shape("M36,84 C40,79 46,79 50,82 C54,80 58,82 60,85 Z", w=1.2)
    # The horse standing out by the road in the rain, unsaddled.
    horse(d, 74, 86, 0.4, saddle=False, graze=0.3)
    d.line("M52,90 C66,89 80,89 94,88", w=0.9)
    d.ground(2, 50, 88, ticks=4, seed=406)
    return d


# 5. Old names and dates cut in the rock of the pass (2-04) ---------------------------------------------
def names_in_rock() -> Drawing:
    d = Drawing("names-in-rock")
    # The far wall of the pass and the gap through it, the evening sky beyond.
    far = "M60,58 L62,40 L68,34 L72,36 L78,28 L86,30 L94,26 L94,58 Z"
    d.shape(far, w=1.2)
    d.hatch(far, angle=70, pitch=2.2, w=0.6)
    # The near rock face, bedded and cracked like the sandstone at El Morro, cut with names and dates.
    # The face runs up out of the drawing: a cliff, not a stone.
    face = ("M-2,90 L-2,-2 L40,-2 L42,4 L48,6 L50,14 L54,18 L55,30 L58,36 L58,46 L62,52 L63,62 L67,70 L68,80 "
            "L72,90 Z")
    d.shape(face)
    d.line("M0,20 C16,18 34,21 52,19 M0,48 C20,46 40,48 59,47 M0,70 C22,68 44,70 66,70", w=0.7, halo=False)
    d.line("M30,0 L31,18 M48,48 L50,68 M12,70 L14,88 M22,20 L20,30", w=0.7, halo=False)
    d.hatch("M50,14 L54,18 L55,30 L58,36 L58,46 L62,52 L63,62 L67,70 L68,80 L72,90 L62,90 L58,70 L54,50 L50,30 Z",
            angle=75, pitch=1.8)
    d.shape("M60,90 C62,86 66,85 68,88 C70,85 74,86 76,90 Z", w=1.1)
    rows = [(8, 26, 24), (8, 32, 16), (30, 32, 18), (8, 54, 30), (8, 60, 20), (34, 60, 18), (8, 76, 26)]
    for x, y, w in rows:
        marks, cx, k = [], x, 0
        while cx < x + w:
            h = 3.2 if k % 3 else 4
            marks.append(f"M{cx:.1f},{y:.1f} l{0.4 if k % 2 else -0.4:.1f},{h:.1f}")
            if k % 4 == 1:
                marks.append(f"M{cx - 0.8:.1f},{y + h / 2:.1f} l2.4,0")
            cx += 2.6 if k % 5 != 4 else 4.4
            k += 1
        d.line(" ".join(marks), w=0.7, halo=False)
    # A date large enough to read on the map, 1881, and a cross.
    d.line("M10,38 l0,7 M13,38.6 C13,37 17,37 17,39 C17,40.6 13,40.6 13,42.4 C13,44.6 17,44.8 17,42.6 "
           "C17,41 13,41 13,39 M20,38.6 C20,37 24,37 24,39 C24,40.6 20,40.6 20,42.4 C20,44.6 24,44.8 24,42.6 "
           "C24,41 20,41 20,39 M27,38 l0,7", w=0.9, halo=False)
    d.line("M44,30 L44,42 M40,34 L48,34", w=1.0, halo=False)
    # Billy riding down out of the pass below it, slouched against the cold.
    rider(d, 80, 88, 0.36, flip=True, hat="low")
    d.line("M62,90 C72,89 84,89 94,88", w=0.9)
    d.line("M66,20 l8,-1 M70,24 l6,-0.6 M84,16 l8,-1", w=0.6, halo=False)
    return d


# 6. A rider coming across the playa at sunrise, broken in his reflection (2-07) ------------------------
def playa_rider() -> Drawing:
    d = Drawing("playa-rider")
    # Far hills on the edge of the dry lake.
    hills = "M2,40 C10,36 18,36 26,38 C34,34 42,34 48,37 M66,38 C74,35 84,35 94,38"
    d.line(hills, w=0.9)
    d.line("M2,44 C30,43 64,43 94,44", w=0.8)
    # The rider small on the shallow sheet of water, and his reflection broken by the ripples.
    rider(d, 48, 66, 0.4, hat="cowboy")
    t = lambda x, y: (48 + (x - 48) * 0.4, 66 + (90 - y) * 0.4)  # noqa: E731
    for p in traced("rider-annie-g")["outline"]:
        d.shape(warp(p, t), w=0.7, fill=False)
    for k, y in enumerate((68, 70.4, 72.6, 75, 77.6, 80, 82.4)):
        d.line(f"M{28 + k % 2 * 2},{y} L{68 - k % 3 * 2},{y}", w=1.2, color=PAPER, halo=False)
    d.line("M4,66 L24,66 M72,66 L92,66 M10,72 L22,72 M76,71 L90,71 M6,80 L18,80 M78,79 L92,79 M14,87 L40,87 "
           "M56,86 L84,86", w=0.6, halo=False)
    # Cracked clay at the near edge.
    d.line("M2,92 L94,92", w=0.9)
    d.line("M12,92 l3,-2 l4,1 M40,92 l2,-2.4 l5,0.8 M70,92 l4,-2 l3,1.2", w=0.6, halo=False)
    return d


# 7. The meadow of stumps and the fallen sawmill, and across the valley the miners' family at the old silver mine
# watching the riders pass (2-08) ----------------------------------------------------------------------------
def silver_mine_family() -> Drawing:
    d = Drawing("silver-mine-family")
    # Across the valley: the far slope, the pale tailings, the headframe over the shaft.
    d.line("M2,40 C18,24 32,16 48,14 C62,13 78,18 94,26", w=1.0)
    tail = "M28,42 C30,32 34,26 38,24 C42,27 46,34 50,42 Z"
    d.shape(tail, w=1.0)
    d.dots([(34, 36), (38, 30), (42, 38), (36, 40), (44, 41)], r=0.5)
    d.line("M10,42 L15,22 L20,42 M12,34 L18,34 M15,22 L24,32", w=1.1)
    d.shape(circle(15, 22, 2.2), w=0.9, fill=False)
    # Their withy huts and the family drawn up in a row, all sizes, shading their eyes.
    hut = place("M-6,0 C-6,-6 -3,-8 0,-8 C3,-8 6,-6 6,0 Z", 86, 40, 1.0)
    d.shape(hut, w=1.0)
    d.hatch(hut, angle=70, pitch=1.4)
    for x, h in ((56, 15), (60.6, 13.4), (64.8, 11.6), (68.4, 9.6), (71.6, 7.8), (74.4, 6.4)):
        p = figure(d, x, 46, h, hat=False, coat=h > 12)
        d.line(p("M2.6,-16.6 L5,-19.6 L1.4,-22.6"), w=0.8)
    d.line("M2,50 C30,48 60,49 94,47", w=0.7, halo=False)
    # This side: a meadow scattered with the stumps of cut pines.
    for x, y, s in ((10, 60, 0.8), (30, 58, 0.7), (64, 60, 0.75), (86, 58, 0.7), (20, 72, 1.0), (78, 74, 1.1),
                    (50, 66, 0.8), (6, 86, 1.3), (90, 88, 1.2)):
        stump = f"M{x - 4 * s},{y} L{x - 3.4 * s},{y - 6 * s} L{x + 3.4 * s},{y - 6 * s} L{x + 4 * s},{y} Z"
        d.shape(stump, w=1.1)
        d.hatch(stump, angle=60, pitch=0.9, cross=True)
        d.shape(ellipse(x, y - 6 * s, 3.4 * s, 1.1 * s), w=0.8)
    # The ruin of an old sawmill: the rusted saw, and the frame of heavy timbers fallen askew across it.
    blade = ellipse(50, 82, 8, 7)
    d.shape(blade, w=1.4)
    teeth = " ".join(f"M{50 + 8 * math.cos(a):.1f},{82 + 7 * math.sin(a):.1f} l{2 * math.cos(a + 1.2):.1f},"
                     f"{2 * math.sin(a + 1.2):.1f}" for a in [i * math.pi / 9 for i in range(18)])
    d.line(teeth, w=0.8)
    d.hatch("M44,86 C46,80 52,78 56,80 C56,84 52,88 46,88 Z", angle=45, pitch=1.0)
    d.dots([(50, 82)], r=1.2)
    d.line("M24,92 L30,68 M30,68 L44,62 L62,74 L66,92", w=2.0)
    d.line("M20,82 L68,78 M36,92 L70,72", w=1.7)
    d.ground(2, 94, 92, ticks=7, seed=408)
    return d


# 8. The horned moon on its back, Venus over it, and the horses driven through the night (3-08) ---------
def horned_moon() -> Drawing:
    d = Drawing("horned-moon")
    # The thin crescent lying on its back in the west, Venus straight above it.
    moon = "M26,26 C28,38 46,38 48,26 C44,33 30,33 26,26 Z"
    d.shape(moon, w=1.1)
    d.hatch(moon, angle=0, pitch=1.0)
    d.shape(circle(37, 13, 1.6), w=1.0)
    d.line("M37,8.4 l0,-3 M37,17.6 l0,3 M32.4,13 l-3,0 M41.6,13 l3,0", w=0.8, halo=False)
    d.dots([(70, 8), (84, 16), (62, 20), (90, 6), (8, 12), (76, 28), (14, 40)], r=0.6)
    # The blue plain, and the brothers driving their horses north across it.
    d.line("M2,56 C30,54 60,55 94,54", w=0.9)
    d.hatch("M2,56 C30,54 60,55 94,54 L94,60 L2,61 Z", angle=10, pitch=2.2, w=0.6)
    horse(d, 30, 82, 0.26, saddle=False)
    horse(d, 46, 80, 0.24, saddle=False, graze=-0.2)
    horse(d, 60, 83, 0.26, saddle=False)
    rider(d, 16, 86, 0.3, hat="cowboy")
    rider(d, 78, 86, 0.3, hat="cowboy")
    d.ground(2, 94, 88, ticks=6, seed=409)
    return d


# 9. A boy dressed for the Saturday dance, riding a little mine mule (3-12) -----------------------------
def dance_riders() -> Drawing:
    d = Drawing("dance-riders")
    # The road north at dusk, a burro and its rider behind.
    d.line("M2,62 C30,60 60,60 94,58", w=0.8)
    d.line("M60,22 C60,16 64,12 70,12 C76,12 80,16 80,22", w=1.0)
    d.line("M56,22 L84,22", w=0.8)

    def ears_small(t):
        d.line(t(MULE_EARS), w=0.9)
    rider(d, 22, 66, 0.3, hat="cowboy", extra=ears_small)

    # The boy on the mule: no hat, his hair slicked down, a pressed white shirt and polished boots.
    def dressed(t):
        d.line(t(MULE_EARS), w=1.2)
        d.hatch(t("M47.6,18.6 C48,14.6 54.6,14.2 55,18.6 L54.6,20 L48,20 Z"), angle=0, pitch=0.8)
        d.line(t("M49,27 L53,27 M51,27 L51,30"), w=0.7, halo=False)
        d.hatch(t("M53,58 L57,59 L57.6,62 L53,62 Z"), angle=45, pitch=0.8)
    rider(d, 52, 90, 0.62, hat="none", extra=dressed)
    d.ground(2, 94, 91, ticks=6, seed=410)
    return d


# 10. "The girl" riding by in her new blue dress (3-12) -------------------------------------------------
def girl_in_blue() -> Drawing:
    d = Drawing("girl-in-blue")
    # Grass by the little stream, and the road.
    d.line("M2,86 C30,84 60,84 94,83", w=0.9)
    grass(d, [(8, 92), (20, 93), (74, 92), (88, 93)], h=4)

    def dress(t):
        # A full skirt over the horse's flank, her dark hair, the straw hat and its long ribbon down her back.
        skirt = t("M44,28 C42,36 38,46 36,56 C42,58 52,58 58,55 C56,46 55,36 54,28 Z")
        d.shape(skirt, w=1.2)
        d.edge_shade(skirt, dx=-2.4, dy=-2)
        d.line(t("M40,48 C44,52 50,52 56,50"), w=0.6, halo=False)
        d.hatch(t("M47.6,18.4 C46,22 46,26 47,28 L49.6,27 C48.6,24 48.6,21 49.6,19 Z"), angle=80, pitch=0.8)
        d.shape(t("M41,19.6 C45,17.8 57,17.8 61,19.6 C57,21.4 45,21.4 41,19.6 Z"), w=1.0)
        d.shape(t("M47,19.2 C47,15.6 48.4,14.2 51,14.2 C53.6,14.2 55,15.6 55,19.2 Z"), w=1.0)
        d.line(t("M47,18.6 L55,18.6"), w=0.9, halo=False)
        d.line(t("M46.6,19 C42,24 40,30 38,36 M46.6,19.4 C43,25 42,31 41,36"), w=0.8)
    rider(d, 48, 90, 0.66, hat="none", leg=False, extra=dress)
    return d


# 11. The night bus up the Rio Grande, waterfowl dropping to the marshes (4-01) -------------------------
def night_bus() -> Drawing:
    d = Drawing("night-bus")
    # Skeins of ducks and geese circling down to the river marsh east of the highway, in the dusk.
    chevrons(d, [(40, 8, 0.9), (46, 12, 0.8), (52, 16, 0.8), (58, 20, 0.7), (70, 8, 0.8), (76, 12, 0.7),
                 (82, 16, 0.7), (88, 24, 0.6), (64, 28, 0.6), (74, 32, 0.6)])
    d.dots([(8, 8), (20, 14), (14, 26), (30, 6)], r=0.6)
    d.line("M2,42 C30,40 60,41 94,40", w=0.8)
    d.line("M60,40 l-1,-6 M64,40 l1,-7 M70,40 l-0.6,-5 M84,40 l1,-6 M88,40 l-1,-5 M92,40 l0.6,-4", w=0.7)
    # A 1940 Yellow Coach Silversides, long and low: the rounded nose, the passengers' deck raised behind the
    # driver, the lit windows, and the fluted sides it was named for.
    body = "M4,76 L4,64 C4,58 8,55 14,54.4 L22,54 L26,50 L90,50 C92,50 93,51 93,53 L93,76 Z"
    d.shape(body)
    d.shape(poly((8, 61), (8, 57.6), (22, 56.4), (22, 61)), w=0.9)
    d.hatch(poly((8, 61), (8, 57.6), (22, 56.4), (22, 61)), angle=45, pitch=1.3)
    for x in range(28, 90, 6):
        d.shape(poly((x, 53), (x + 4.4, 53), (x + 4.4, 58.6), (x, 58.6)), w=0.8)
    d.line("M24,60.6 L92,60.6", w=0.9, halo=False)
    d.line(" ".join(f"M5,{y} L92,{y}" for y in (64, 66.2, 68.4, 70.6)), w=0.5, halo=False)
    d.edge_shade(body, dx=0, dy=-2.6)
    d.shape(circle(6.4, 68, 1.5), w=0.9)
    d.line("M4,67.4 L-2,65 M4,68.6 L-2,71", w=0.6, halo=False)
    for cx in (18, 78):
        d.shape(f"M{cx - 7.6},77 C{cx - 7.6},69.6 {cx + 7.6},69.6 {cx + 7.6},77 Z", w=1.2)
        d.shape(circle(cx, 77.4, 4.8), w=1.6)
        d.hatch(circle(cx, 77.4, 4.8), angle=60, pitch=1.4)
        d.shape(circle(cx, 77.4, 1.6), w=0.9)
    d.line("M2,83 L94,83", w=1.0)
    d.line("M10,87 l8,0 M34,87 l8,0 M58,87 l8,0 M82,87 l8,0", w=0.8, halo=False)
    return d


# 12. A gold star in the window of a ranch house (4-02) ------------------------------------------------
def gold_star() -> Drawing:
    d = Drawing("gold-star")
    # The end of a board and batten ranch house under its gable, and the porch post.
    house = poly((10, 90), (10, 34), (48, 12), (86, 34), (86, 90))
    d.shape(house)
    d.line(" ".join(f"M{x},{34 - (x - 10) * 22 / 38 if x < 48 else 12 + (x - 48) * 22 / 38:.1f} L{x},90"
                    for x in range(16, 86, 7)), w=0.5, halo=False)
    d.line("M6,36 L48,10 L90,36", w=1.6)
    d.edge_shade(house, dx=-3, dy=0)
    # The window, its sash and curtains, and the gold star hung in it on a cord. The book gives the star alone.
    frame = poly((26, 82), (26, 36), (70, 36), (70, 82))
    d.shape(frame, w=1.6)
    d.hatch(frame, angle=45, pitch=2.6)
    d.line("M24,82 L72,82 M24,85 L72,85", w=1.2)
    d.shape("M28,38 C34,46 32,64 28,80 Z", w=0.9)
    d.shape("M68,38 C62,46 64,64 68,80 Z", w=0.9)
    d.line("M36,40 L60,40 M48,40 L48,50", w=0.8)
    d.shape(star(48, 60.4, 12), w=1.8)
    d.ground(2, 94, 91, ticks=6, seed=418)
    return d


# 13. Three children astride Niño, led down to the stream (4-04) ----------------------------------------
def children_on_nino() -> Drawing:
    d = Drawing("children-on-nino")
    # The low mud houses of the town behind, and the stream crossing the road in the grassy field.
    d.shape(poly((4, 50), (4, 40), (30, 40), (30, 50)), w=1.1)
    d.shape(poly((60, 48), (60, 40), (92, 40), (92, 48)), w=1.1)
    d.line("M12,50 l0,-6 l4,0 l0,6 M74,48 l0,-5 l4,0 l0,5", w=0.8)
    d.line("M2,52 C30,51 60,51 94,50", w=0.8)
    water(d, 86, seed=1)
    grass(d, [(8, 84), (18, 83), (90, 82)], h=4)
    f = horse(d, 46, 86, 0.66, saddle=False, graze=0.2)
    # The children on his bare back: the youngest at the withers, the girl, and the eldest behind holding them.
    for x, h in ((60, 13), (50, 15), (40, 18)):
        kid = f"M{x - 4},38 C{x - 4.6},{38 - h * 0.7} {x + 4.6},{38 - h * 0.7} {x + 4},38 Z"
        d.shape(warp(kid, f), w=1.2)
        d.shape(warp(round_(x, 38 - h * 0.7 - 3.6, 3.6), f), w=1.1)
        d.line(warp(f"M{x + 1},37 L{x + 2},{49}", f), w=1.2)
    d.hatch(warp("M46.6,22 C46.6,18 53.4,18 53.4,22 L53,25 L47,25 Z", f), angle=80, pitch=0.9)
    d.line(warp("M43,28 L50,30 M53,30 L60,31", f), w=0.9, halo=False)
    # Billy at the horse's head, holding the reins.
    figure(d, 90, 90, 30, flip=True)
    d.line("M86.6,76 C84,72 82,66 80,62", w=0.7, halo=False)
    return d


# 14. The wedding carreta on the road into Namiquipa (4-04) ---------------------------------------------
def wedding_carreta() -> Drawing:
    d = Drawing("wedding-carreta")
    d.line("M2,88 C30,87 60,87 94,86", w=0.9)
    # The canopy: cotton sheeting tied over a rickety hoop frame of willow, bunting hung along its edge.
    canopy = "M38,46 C38,32 46,24 58,24 C70,24 80,32 80,46 Z"
    d.shape(canopy, w=1.4)
    d.line("M45,46 C45,36 50,29 56,27 M73,46 C73,36 68,29 62,27", w=0.6, halo=False)
    d.line("M38,46 L80,46", w=1.0)
    d.shape(" ".join(f"M{x},46 L{x + 4},46 L{x + 2},51 Z" for x in range(38, 80, 6)), w=0.8)
    # The bride under her open parasol, sitting alone in the box.
    d.shape("M50,52 C50,46 64,46 64,52 C60,51 54,51 50,52 Z", w=1.1)
    d.hatch("M50,52 C50,46 64,46 64,52 C60,51 54,51 50,52 Z", angle=80, pitch=1.4)
    d.line("M57,50 L57,58", w=0.8)
    d.shape("M53,64 C53,58 54,55 57,55 C60,55 61,58 61,64 Z", w=1.0)
    d.shape(circle(57, 55, 2), w=0.9)
    # The plank box on its two solid wooden wheels.
    box = poly((38, 70), (38, 60), (80, 60), (80, 70))
    d.shape(box, w=1.5)
    d.line("M38,63.4 L80,63.4 M38,66.8 L80,66.8", w=0.6, halo=False)
    d.line("M38,46 L38,60 M80,46 L80,60", w=1.0)
    d.shape(circle(62, 74, 12), w=1.8)
    d.line("M51,70 L73,70 M50.4,74 L73.6,74 M51,78 L73,78", w=0.6, halo=False)
    d.shape(circle(62, 74, 2.8), w=1.0)
    d.hatch(circle(62, 74, 2.8), angle=45, pitch=0.9)
    # The shafts down to the one small grey mule.
    f = horse(d, 20, 86, 0.34, flip=True, saddle=False)
    d.hatch(warp("M22,46 C34,40 56,40 70,44 L72,58 L24,60 Z", f), angle=30, pitch=2.4)
    d.line(warp(MULE_EARS, f), w=1.0)
    d.line("M38,66 L24,73 M38,68 L26,75", w=1.3)
    # One of the men in a dark suit walking beside.
    p = figure(d, 90, 90, 28, flip=True)
    d.hatch(p("M-3,-17.6 C-2,-19 2,-19 3,-17.6 L4,-8.4 L-4,-8.4 Z"), angle=45, pitch=1.0)
    return d


# 16. The old man's oxen wading into the river to drink (3-03) ------------------------------------------
def oxen_at_the_river() -> Drawing:
    d = Drawing("oxen-at-the-river")
    # The woods on the far bank they came down through.
    d.line("M2,46 C30,44 60,45 94,44", w=0.8)
    for x, base, h, w, seed in ((70, 44, 30, 16, 413), (86, 46, 34, 18, 414), (10, 44, 24, 14, 415)):
        cottonwood(d, x, base, h, w, seed=seed)
    # The pair wading in, heads down to drink, under a yoke of poplar bleached white by the sun: the criollo
    # draught cattle of the steers drawing, heavier, the near one a little lower.
    steer(d, 18, 40, 0.95)
    steer(d, 2, 54, 1.05)
    yoke = poly((10, 58), (27, 42), (29.6, 44), (12.6, 60.4))
    d.shape(yoke, w=1.4)
    d.line("M12.4,60 C11,64 14,66 16,62 M26,45 C25,49 28,50 29,47", w=0.9)
    # The river over their legs.
    for y in range(76, 88, 2):
        d.line(f"M0,{y} L62,{y}", w=1.5, color=PAPER, halo=False)
    water(d, 76, x0=2, x1=94, seed=2)
    d.line("M4,80 l14,0 M30,82 l18,0 M10,86 l20,0", w=0.7, halo=False)
    # The old man in his white field clothes at the water's edge, the stick tilted towards them.
    p = figure(d, 84, 80, 30, flip=True, coat=True)
    d.line(p("M3,-15 L8,-11 L20,-28"), w=0.9)
    d.line("M70,81 C78,80 88,80 94,81", w=0.8)
    return d


# 17. Whiteface Herefords of the Babícora on the high grassland (4-05) ----------------------------------
HEREFORD = ("M10,8 C14,4 24,4 30,5 C36,4 42,5 44,8 C46,12 46,18 44,21 L44,30 L40.6,30 L40,22 L34,23 L20,23 "
            "L18.6,30 L15,30 L15,22 C12,21 10,19 9,16 L4,17 C1,17.4 0,15 1,12 L4,7 C6,6 8,6 10,8 Z")


def hereford(d: Drawing, x: float, y: float, k: float, flip: bool = False):
    """A blocky Hereford, its body dark and its face, chest and belly line white; origin top left of a 46 x 30
    box, head to the west."""
    body = place(HEREFORD, x, y, k, flip)
    d.shape(body, w=1.4)
    dark = place("M14,7 C20,5 30,6 36,5 C42,5 44,9 44,14 L44,20 L36,20 L22,21 L15,19 C13,15 12,10 14,7 Z", x, y, k,
                 flip)
    d.hatch(dark, angle=45, pitch=1.3, cross=True)
    d.line(place("M4,7 C2,4 1,3 -2,3 M8,6.6 C9,4 11,3 13,3.4", x, y, k, flip), w=1.0)
    d.line(place("M44,9 C47,13 47,18 46,24", x, y, k, flip), w=0.8)


def babicora_hereford() -> Drawing:
    d = Drawing("babicora-hereford")
    # The high grassland and the sierra on its rim.
    ridge = "M2,40 L12,32 L20,36 L30,26 L40,34 L52,28 L62,36 L72,30 L82,36 L94,32"
    d.line(ridge, w=1.0)
    d.hatch(ridge + " L94,44 L2,44 Z", angle=70, pitch=2.6, w=0.6)
    d.line("M2,52 C30,51 60,51 94,50", w=0.7, halo=False)
    hereford(d, 52, 50, 0.7)
    hereford(d, 8, 54, 1.25)
    grass(d, [(12, 92), (40, 93), (66, 92), (86, 92)], h=4)
    d.ground(2, 94, 92, ticks=6, seed=416)
    return d


SUBJECTS = {
    "wolf-mate": wolf_mate,
    "model-a-wolf": model_a_wolf,
    "tumpline-bearers": tumpline_bearers,
    "hail-shelter": hail_shelter,
    "names-in-rock": names_in_rock,
    "playa-rider": playa_rider,
    "silver-mine-family": silver_mine_family,
    "horned-moon": horned_moon,
    "dance-riders": dance_riders,
    "girl-in-blue": girl_in_blue,
    "night-bus": night_bus,
    "gold-star": gold_star,
    "children-on-nino": children_on_nino,
    "wedding-carreta": wedding_carreta,
    "oxen-at-the-river": oxen_at_the_river,
    "babicora-hereford": babicora_hereford,
}
