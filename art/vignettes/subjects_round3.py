"""Vignettes of the third round: scenes, buildings, plants and riders across all four Parts, each checked against
the episode that first shows it. Loaded by art/vignettes/make_vignettes.py.

The riders are the traced Muybridge horse and rider of the Parts III and IV set (rider-annie-g, public domain),
drawn through that module's `rider`. A horse without a rider is the same outline with the rider cut away above
the saddle, so the loose horses, Keno, the packhorse and the remuda all come from the one plate. The she-wolf is
the traced US Fish and Wildlife Service outline. Everything else is drawn by hand after the references named in
the seed's `credit` column, or from the book's description where none was found.
"""

from functools import cache

from shapely.geometry import box

from art.vignettes.ink import Drawing, region
from art.vignettes.shapes import circle, ellipse, grass, poly, traced, warp
from art.vignettes.subjects_parts_1_2 import juniper, wolf
from art.vignettes.subjects_parts_3_4 import blob, cottonwood, pine, place, rider

# The rider of the traced plate sits inside this box (traced units); cutting it away leaves a saddled horse.
RIDER_BOX = box(39.5, 0, 58.6, 38.4)


def _path(geom) -> str:
    """A shapely polygon or multipolygon as path data, small slivers dropped."""
    parts = []
    for p in getattr(geom, "geoms", [geom]):
        if p.geom_type != "Polygon" or p.area < 1:
            continue
        parts.append(poly(*p.exterior.coords[:-1]))
        parts.extend(poly(*i.coords[:-1]) for i in p.interiors)
    return " ".join(parts)


@cache
def _horse() -> tuple[str, tuple[str, ...]]:
    t = traced("rider-annie-g")
    body = _path(region(t["outline"][0]).difference(RIDER_BOX))
    tones = tuple(_path(region(p).difference(RIDER_BOX)) for p in t["tones"]["0.3"])
    return body, tuple(p for p in tones if p)


def horse(d: Drawing, ox: float, oy: float, k: float, flip: bool = False, graze: float = 0.0, saddle: bool = True,
          pack: bool = False):
    """A horse walking with no rider, hooves centred on (ox, oy), scaled by k. `graze` lowers the head and neck
    (0.8 head down, 1.2 grazing). Returns the transform for drawing more in traced units."""
    s = -1 if flip else 1

    def f(x: float, y: float) -> tuple[float, float]:
        if graze and x > 64:
            y += (x - 64) * graze
            x -= (x - 64) * graze * 0.3
        return ox + s * (x - 48) * k, oy + (y - 90) * k

    body, tones = _horse()
    q = warp(body, f)
    d.shape(q, w=1.4 if k < 0.6 else 1.7)
    d.edge_shade(q, dx=-2 * s, dy=-2.4)
    for p in tones:
        d.hatch(warp(p, f), angle=45 if not flip else 135, pitch=2.0)
    if saddle:
        d.shape(warp("M41,38.6 C42,34.6 44,35 45.4,37.6 C49,38.2 53,37.4 56.4,35.4 C57.6,36.6 57.8,38 57,39.6 "
                     "L55,45 L43,45 Z", f), w=1.0)
    if pack:
        load = warp("M38,38.8 C38,30 58,30 58,38.8 L59,48 C54,50 42,50 37,48 Z", f)
        d.shape(load, w=1.2)
        d.line(warp("M44,32 L42,48 M52,32 L54,48 M37.6,42 L58.6,42", f), w=0.6, halo=False)
        d.edge_shade(load, dx=-1.5 * s, dy=-1.5)
    return f


def figure(d: Drawing, x: float, y: float, h: float, flip: bool = False, hat: bool = True, coat: bool = True):
    """A person standing, feet at (x, y), h tall, drawn in a local 24-unit figure."""
    k = h / 24

    def p(path: str) -> str:
        return place(path, x, y, k, flip)
    d.line(p("M-1.8,-9 L-2.6,0 M1.8,-9 L2.6,0"), w=1.2)
    body = "M-3,-17.6 C-2,-19 2,-19 3,-17.6 L4,-8.4 L-4,-8.4 Z" if coat else "M-2.6,-17.6 C-2,-19 2,-19 2.6,-17.6 L3,-9 L-3,-9 Z"
    d.shape(p(body), w=1.1)
    d.shape(p(circle(0, -21, 2.2)), w=1.0)
    if hat:
        hat_d = p("M-4.6,-22 L4.6,-22 L2.4,-23 C2.4,-26.4 -2.4,-26.4 -2.4,-23 Z")
        d.shape(hat_d, w=0.9)
        d.hatch(hat_d, angle=0, pitch=0.9)
    return p


def fire(d: Drawing, x: float, y: float, s: float = 1.0):
    """A small campfire: crossed sticks, a flame and a few sparks, its base at (x, y)."""
    d.line(place("M-8,0 L8,-3 M-7,-3 L8,0", x, y, s), w=1.4)
    flame = "M-6,-1 C-8,-6 -2,-8 -3,-14 C1,-11 2,-8 1,-6 C3,-10 5,-12 4,-16 C8,-10 8,-4 5,-1 Z"
    d.shape(place(flame, x, y, s), w=1.1)
    d.dots([(x + 1 * s, y - 20 * s), (x - 2 * s, y - 24 * s), (x + 3 * s, y - 27 * s)], r=0.6)


def cholla(d: Drawing, x: float, base: float, k: float):
    """A cane cholla after the White Sands photograph: a short trunk forking into crooked arms of jointed stems,
    each joint knobbed and spined. Drawn in a local box about 40 wide and 60 tall, base at (x, base), scaled by k."""
    arms = ["M0,0 L0.6,-14 L-1,-22", "M-1,-22 L-8,-30 L-10,-40 L-16,-46", "M-10,-40 L-6,-50",
            "M-8,-30 L-16,-32 L-22,-40", "M-1,-22 L4,-32 L2,-44 L6,-54", "M4,-32 L12,-38 L14,-48",
            "M12,-38 L20,-40 L24,-48", "M0.6,-14 L10,-20 L18,-24"]
    d.line(place(" ".join(arms), x, base, k), w=2.4)
    knots = [(-1, -22), (-8, -30), (-10, -40), (-16, -46), (-6, -50), (-16, -32), (-22, -40), (4, -32), (2, -44),
             (6, -54), (12, -38), (14, -48), (20, -40), (24, -48), (10, -20), (18, -24)]
    d.dots([(x + a * k, base + b * k) for a, b in knots], r=1.3)
    spines = " ".join(f"M{x + a * k:.1f},{base + b * k:.1f} l-1.4,-1 M{x + a * k:.1f},{base + b * k:.1f} l1.4,-1"
                      for a, b in knots)
    d.line(spines, w=0.6, halo=False)


def chevrons(d: Drawing, birds: list[tuple[float, float, float]]):
    """Birds in flight seen far off, each a shallow M of two wingbeats."""
    d.line(" ".join(f"M{x - 3 * s:.1f},{y - 1 * s:.1f} Q{x - 1.4 * s:.1f},{y - 2 * s:.1f} {x:.1f},{y:.1f} "
                    f"Q{x + 1.4 * s:.1f},{y - 2 * s:.1f} {x + 3 * s:.1f},{y - 1 * s:.1f}" for x, y, s in birds), w=0.8)


# 1. Echols' cabin, and the old traps on the smokehouse wall (1-02) -------------------------------------
def echols_cabin() -> Drawing:
    d = Drawing("echols-cabin")
    # The cabin: a low gabled house with a porch, its door padlocked, one small window at the back.
    house = poly((6, 80), (6, 52), (44, 52), (44, 80))
    roof = poly((2, 53), (14, 36), (48, 36), (48, 53))
    d.shape(house)
    d.shape(roof, w=1.4)
    d.hatch(roof, angle=0, pitch=1.9)
    d.line("M2,53 L14,36 L26,53", w=1.2)
    door = poly((30, 80), (30, 62), (38, 62), (38, 80))
    d.shape(door, w=1.1)
    d.hatch(door, angle=80, pitch=1.4)
    d.shape(circle(36.4, 70, 1.0), w=0.7)
    win = poly((12, 60), (20, 60), (20, 68), (12, 68))
    d.shape(win, w=1.0)
    d.hatch(win, angle=45, pitch=1.3)
    d.line("M27,56 L46,56 M28,56 L28,80 M45,56 L45,80", w=1.0)
    d.edge_shade(house, dx=-3, dy=0)
    # The smokehouse beside it, and on its wall the old longspring coyote traps hung by their chains.
    shed = poly((56, 82), (56, 46), (90, 46), (90, 82))
    d.shape(shed)
    d.shape(poly((53, 47), (60, 38), (86, 38), (93, 47)), w=1.3)
    d.hatch(poly((53, 47), (60, 38), (86, 38), (93, 47)), angle=0, pitch=1.8)
    d.line(" ".join(f"M{x},46 L{x},82" for x in (62, 68, 74, 80, 86)), w=0.5, halo=False)
    for x in (62, 73, 84):
        d.line(f"M{x},50 L{x},55", w=0.8)
        d.dots([(x, 50)], r=0.8)
        d.shape(ellipse(x, 59, 3.6, 2.6), w=1.1, fill=False)
        d.line(f"M{x - 3},61 C{x - 4},65 {x - 3},68 {x - 1},70 M{x + 3},61 C{x + 4},65 {x + 3},68 {x + 1},70", w=1.0)
    d.edge_shade(shed, dx=-3, dy=0)
    d.ground(2, 94, 86, ticks=7, seed=301)
    return d


# 2. The calf killed at the head of Foster Draw (1-03) --------------------------------------------------
def dead_calf() -> Drawing:
    d = Drawing("dead-calf")
    # The edge of the trees on the upland meadow, old snow in their shade.
    for x, base, h, seed in ((10, 50, 32, 1), (22, 46, 26, 2), (84, 48, 28, 3)):
        juniper(d, x, base, h, seed=seed)
    d.line("M4,54 C20,52 40,53 60,52 C74,51 86,53 94,53", w=0.9)
    # What is left of the calf: the open ribcage on its spine, the head apart, a leg bone flung out.
    d.line("M30,68 C40,64 54,64 66,68", w=1.6)
    d.line(" ".join(f"M{x},{66 - abs(x - 48) * 0.1:.1f} C{x - 3},{72:.1f} {x - 2},{77:.1f} {x + 1},{80:.1f}"
                    for x in range(34, 64, 5)), w=1.1)
    skull = "M70,72 C72,67 78,66 82,68 C85,70 85,74 82,76 L76,79 C73,79 70,76 70,72 Z"
    d.shape(skull, w=1.3)
    d.dots([(76, 71)], r=0.9)
    d.line("M74,67 l-1,-3 M80,67 l2,-3", w=0.9)
    d.line("M14,76 L26,74 M13,75 l-1,2 M27,73 l1,2", w=1.3)
    # Blood on the snow, and the coyotes' tracks crossing and recrossing it.
    d.hatch("M22,84 C26,80 34,81 40,84 C34,88 26,88 22,84 Z", angle=20, pitch=1.3)
    d.hatch("M64,86 C68,83 76,83 80,86 C74,89 68,89 64,86 Z", angle=20, pitch=1.3)
    d.dots([(8, 64), (12, 62), (16, 65), (14, 70), (86, 62), (90, 66), (88, 72), (92, 78), (10, 80), (6, 86)], r=0.7)
    d.ground(2, 94, 90, ticks=6, seed=302)
    return d


# 3. Don Arnulfo's mud house on the plain below Animas (1-07) -------------------------------------------
def arnulfo_house() -> Drawing:
    d = Drawing("arnulfo-house")
    # The mountains to the west and the long rise of the plain.
    hills = "M2,40 C10,32 18,30 26,34 C34,28 42,28 48,34 C54,32 60,34 64,38"
    d.line(hills, w=1.0)
    d.hatch(hills + " L64,42 L2,42 Z", angle=20, pitch=3.0, w=0.6)
    d.line("M60,46 C70,42 82,42 94,44", w=0.8)
    # The low mud house: flat roof on vigas, a door and one small west window.
    house = poly((14, 80), (14, 56), (70, 56), (70, 80))
    d.shape(house)
    d.line("M12,56 L72,56", w=1.6)
    d.line(" ".join(f"M{x},58 l-3,0" for x in (18, 30, 42, 54, 66)), w=1.0)
    door = poly((46, 80), (46, 64), (54, 64), (54, 80))
    d.shape(door, w=1.1)
    d.hatch(door, angle=45, pitch=1.4, cross=True)
    win = poly((22, 63), (28, 63), (28, 69), (22, 69))
    d.shape(win, w=1.0)
    d.hatch(win, angle=45, pitch=1.2)
    d.edge_shade(house, dx=-3, dy=0)
    # The fence's cornerpost, with Billy's horse tied to it.
    d.line("M82,86 L82,62 M82,66 L94,68 M82,74 L94,75", w=1.2)
    horse(d, 86, 88, 0.26, flip=True, graze=0.6)
    d.ground(2, 94, 88, ticks=7, seed=303)
    return d


# 4. The she-wolf caught, the trap's drag fast in a cholla (1-08) --------------------------------------
def wolf_in_the_cholla() -> Drawing:
    d = Drawing("wolf-in-the-cholla")
    cholla(d, 72, 86, 1.25)
    # She stands braced, the trap on her right forefoot and the chain running back to the drag in the cholla.
    wolf(d, 0.5, 6, 42, w=1.3)
    d.line("M42,85 C50,86 58,86 66,84", w=1.0)
    d.shape(ellipse(41, 84, 3.4, 1.8), w=1.1, fill=False)
    d.line("M66,84 l3,-3 M66,84 l3,2", w=1.2)
    d.ground(2, 94, 90, ticks=7, seed=305)
    grass(d, [(10, 90), (30, 90), (88, 90)], h=3.4)
    return d


# 5. The Parham house found empty at night (2-04) -------------------------------------------------------
def parham_house() -> Drawing:
    d = Drawing("parham-house")
    d.shape(circle(84, 12, 5.5), w=1.2)
    d.dots([(10, 10), (28, 6), (50, 12), (66, 6), (40, 22)], r=0.6)
    # The barn behind, its bay open and dark.
    barn = poly((54, 76), (54, 42), (70, 30), (86, 42), (86, 76))
    d.shape(barn)
    bay = poly((63, 76), (63, 56), (77, 56), (77, 76))
    d.shape(bay, w=1.1)
    d.hatch(bay, angle=45, pitch=1.4, cross=True)
    d.edge_shade(barn, dx=-3, dy=0)
    # The house: a porch along the front and every window dark.
    house = poly((8, 82), (8, 54), (50, 54), (50, 82))
    roof = poly((4, 55), (16, 42), (42, 42), (54, 55))
    d.shape(house)
    d.shape(roof, w=1.4)
    d.hatch(roof, angle=0, pitch=1.8)
    d.line("M6,62 L52,62 M8,62 L8,82 M29,62 L29,82 M50,62 L50,82", w=1.0)
    for x in (13, 37):
        win = poly((x, 66), (x + 8, 66), (x + 8, 76), (x, 76))
        d.shape(win, w=1.0)
        d.hatch(win, angle=45, pitch=1.2, cross=True)
    door = poly((24, 82), (24, 68), (30, 68), (30, 82))
    d.shape(door, w=1.0)
    d.hatch(door, angle=45, pitch=1.2, cross=True)
    d.edge_shade(house, dx=-3, dy=0)
    # The stockgate left standing open.
    d.line("M88,86 L88,66 M88,70 L94,62 M88,78 L94,72", w=1.0)
    d.ground(2, 94, 88, ticks=7, seed=306)
    return d


# 6. Keno under the elder tree at Bacerac (2-07) --------------------------------------------------------
def keno_bacerac() -> Drawing:
    d = Drawing("keno-bacerac")
    # The whitewashed house behind, and the elder over the two horses standing head down.
    house = poly((40, 70), (40, 34), (94, 34), (94, 70))
    d.shape(house)
    d.line("M38,34 L96,34", w=1.6)
    door = poly((74, 70), (74, 50), (82, 50), (82, 70))
    d.shape(door, w=1.1)
    d.hatch(door, angle=45, pitch=1.4, cross=True)
    d.edge_shade(house, dx=-3, dy=0)
    d.line("M20,86 C20,70 18,56 22,42 M22,52 C26,46 30,44 34,40", w=1.6)
    crown = blob(24, 28, 20, 13, 11, seed=307, depth=0.25)
    d.shape(crown, w=1.4)
    d.edge_shade(crown, dx=-3.5, dy=-3.5)
    d.dots([(14, 24), (20, 30), (28, 22), (34, 30), (24, 36)], r=0.9)
    # The roan behind; Keno nearer, still under the stranger's saddle.
    horse(d, 70, 80, 0.36, graze=0.8, saddle=False)
    horse(d, 30, 89, 0.46, graze=0.8)
    d.ground(2, 94, 89, ticks=6, seed=308)
    return d


# 7. Boyd rides through the fire for "the girl" (2-08) ------------------------------------------------
def taking_the_girl() -> Drawing:
    d = Drawing("taking-the-girl")
    # The oaks over the camp at night, and the fire.
    for x, base, h, w, seed in ((12, 50, 36, 22, 309), (82, 46, 34, 22, 310)):
        cottonwood(d, x, base, h, w, seed=seed)
    fire(d, 74, 86, 0.8)
    # Boyd bent low on Keno at a gallop, the shotgun held up, Billy's horse on the reins behind him.
    def gun(t):
        d.line(t("M58,32 L80,12"), w=1.5)
    rider(d, 48, 86, 0.5, hat="cowboy", extra=gun)
    horse(d, 16, 84, 0.36)
    d.line("M25,64 C30,62 34,60 40,60", w=0.8, halo=False)
    # "The girl" on her feet by the fire, her bundle in her arms.
    figure(d, 90, 88, 18, hat=False)
    d.shape("M85,76 C85,73 88,72 90,73 C92,74 92,76 91,77 C89,78 86,78 85,76 Z", w=1.0)
    d.ground(2, 94, 89, ticks=6, seed=311)
    return d


# 8. The Mormon colony at Colonia Juárez: orchards and the plank bridge (2-08) --------------------------
def colonia_juarez() -> Drawing:
    d = Drawing("colonia-juarez")
    # A brick house with a tin roof, among rows of apple trees.
    house = poly((56, 56), (56, 34), (86, 34), (86, 56))
    d.shape(house)
    roof = poly((52, 35), (62, 24), (80, 24), (90, 35))
    d.shape(roof, w=1.3)
    d.line(" ".join(f"M{x},25 L{x - 3},35" for x in range(64, 82, 3)), w=0.5, halo=False)
    for x in (61, 75):
        win = poly((x, 40), (x + 5, 40), (x + 5, 48), (x, 48))
        d.shape(win, w=0.9)
        d.hatch(win, angle=45, pitch=1.2)
    d.edge_shade(house, dx=-3, dy=0)
    for row, (y, xs) in enumerate(((50, (8, 22, 36)), (62, (14, 28, 42, 70, 84)))):
        for x in xs:
            d.line(f"M{x},{y} L{x},{y - 4}", w=1.1)
            c = blob(x, y - 8, 5.5, 4.6, 8, seed=312 + x + row)
            d.shape(c, w=1.0)
            d.dots([(x - 2, y - 9), (x + 2, y - 7)], r=0.7)
    # The river below, and the narrow plank bridge across it.
    d.line("M2,72 C20,70 40,71 60,70 C74,69.6 86,70 94,69 M2,86 C24,85 46,86 70,84 C80,83.6 88,84 94,83.6", w=1.0)
    d.line("M10,79 l8,0 M60,77 l10,0 M80,78 l8,0", w=0.6, halo=False)
    deck = poly((26, 77), (56, 75), (56, 78), (26, 80))
    d.shape(deck, w=1.2)
    d.line("M30,79.6 L30,86 M40,79 L40,86 M50,78.4 L50,85", w=1.1)
    d.line(" ".join(f"M{x},{80 - (x - 26) / 15:.1f} L{x},{77 - (x - 26) / 15:.1f}" for x in range(29, 56, 3)),
           w=0.5, halo=False)
    return d


# 9. Quijada sitting his horse at the crossroads (3-04) -------------------------------------------------
def quijada() -> Drawing:
    d = Drawing("quijada")
    # The pines along the road behind him, and the faint dust of the remuda hanging down the road.
    for x, base, h, seed in ((72, 66, 38, 1), (84, 62, 30, 2), (93, 66, 36, 3)):
        pine(d, x, base, h, seed=330 + seed)
    d.dots([(10, 40), (16, 36), (22, 42), (8, 48), (26, 34)], r=0.5)
    d.line("M4,40 C10,34 20,34 28,38", w=0.5, halo=False)

    def smoke(t):
        d.line(t("M60,34 C64,30 62,26 66,22 C70,18 68,14 72,10"), w=0.6, halo=False)
    rider(d, 44, 84, 0.66, flip=True, hat="cowboy", reins=False, extra=smoke)
    # The crossroads: the rutted track out of the mountains crossing the road.
    d.line("M2,86 C30,85 60,85 94,84 M40,94 L46,86 M52,86 L60,78", w=1.0)
    d.ground(2, 94, 89, ticks=6, seed=331)
    return d


# 10. Boyd ropes their horses out of the Babícora remuda (3-04) -----------------------------------------
def remuda() -> Drawing:
    d = Drawing("remuda")
    for x, base, h, seed in ((6, 58, 36, 1), (90, 56, 34, 2), (80, 54, 26, 3)):
        pine(d, x, base, h, seed=340 + seed)
    # The bunched horses in the golden dust, lifting and ducking their heads.
    d.dots([(30, 38), (40, 34), (52, 36), (62, 40), (46, 42)], r=0.5)
    horse(d, 42, 66, 0.34, saddle=False)
    horse(d, 64, 64, 0.32, flip=True, graze=0.5, saddle=False)
    horse(d, 54, 72, 0.38, saddle=False, graze=-0.4)
    horse(d, 30, 76, 0.4, flip=True, saddle=False)
    # Boyd on the near side, his loop thrown over the backs of the others onto Niño.
    def arm(t):
        d.line(t("M57,36 L68,16"), w=1.2)
    rider(d, 76, 90, 0.44, flip=True, hat="cowboy", extra=arm)
    d.line("M70,57 C66,44 56,36 48,38", w=0.8)
    d.shape(ellipse(42, 40, 7, 3), w=1.1, fill=False)
    d.ground(2, 94, 91, ticks=6, seed=341)
    return d


# 11. The night train going downcountry towards Las Varas (3-12) ----------------------------------------
def night_train() -> Drawing:
    d = Drawing("night-train")
    d.dots([(8, 8), (24, 14), (44, 6), (60, 12), (78, 6), (90, 16)], r=0.6)
    # The headlight's cone boring down the desert ahead (south is to the left).
    d.line("M20,46 L2,40 M20,50 L2,58", w=0.7, halo=False)
    # The engine: smokebox, boiler and stack, the cab and the tender, the drivers under them.
    boiler = "M20,44 C20,40 22,38 26,38 L56,38 L56,54 L26,54 C22,54 20,52 20,48 Z"
    d.shape(boiler)
    d.edge_shade(boiler, dx=0, dy=-3)
    d.shape(poly((28, 38), (28, 28), (33, 28), (33, 38)), w=1.2)
    d.shape(poly((40, 38), (41, 33), (46, 33), (47, 38)), w=1.1)
    d.shape(circle(21.4, 47, 2.2), w=1.0)
    cab = poly((56, 54), (56, 32), (54, 30), (72, 30), (70, 32), (70, 54))
    d.shape(cab)
    d.shape(poly((60, 36), (66, 36), (66, 42), (60, 42)), w=0.9)
    d.shape(poly((72, 54), (72, 42), (90, 42), (90, 54)), w=1.4)
    d.hatch(poly((72, 54), (72, 42), (90, 42), (90, 54)), angle=45, pitch=1.6)
    d.shape(poly((14, 62), (20, 54), (24, 54), (24, 62)), w=1.1)
    for cx in (30, 40, 50):
        d.shape(circle(cx, 58, 4.6), w=1.4)
        d.dots([(cx, 58)], r=0.8)
    d.shape(circle(64, 59, 3.4), w=1.2)
    d.line("M28,58 L52,58", w=1.0)
    d.shape(circle(80, 59, 3), w=1.1)
    d.shape(circle(87, 59, 3), w=1.1)
    # The trail of boilersmoke drifting back over the train.
    d.line(blob(48, 20, 9, 4.4, 8, seed=342), w=0.7, halo=False)
    d.line(blob(66, 16, 9, 4, 8, seed=343), w=0.6, halo=False)
    d.line("M74,14 C82,12 88,14 94,12", w=0.6, halo=False)
    d.line("M2,63 L94,63 M2,65.4 L94,65.4", w=0.9)
    d.line(" ".join(f"M{x},63 l-1,2.4" for x in range(6, 94, 6)), w=0.5, halo=False)
    # Billy's horse in the foreground with its head up, watching it pass.
    horse(d, 70, 92, 0.24, flip=True, graze=-0.3, saddle=False)
    return d


# 12. Turned away at the army recruiting office (4-01) --------------------------------------------------
def recruiting_office() -> Drawing:
    d = Drawing("recruiting-office")
    # A brick armory with a crenellated parapet, the flag on its pole, the steps up to the door.
    front = poly((10, 80), (10, 34), (70, 34), (70, 80))
    d.shape(front)
    d.line("M8,34 L8,28 L14,28 L14,32 L22,32 L22,28 L28,28 L28,32 L36,32 L36,28 L44,28 L44,32 L52,32 L52,28 "
           "L58,28 L58,32 L66,32 L66,28 L72,28 L72,34", w=1.2)
    d.line(" ".join(f"M10,{y} L70,{y}" for y in (42, 50, 58, 66, 74)), w=0.4, halo=False)
    door = "M32,80 L32,62 C32,56 48,56 48,62 L48,80 Z"
    d.shape(door, w=1.2)
    d.hatch(door, angle=45, pitch=1.4, cross=True)
    for x in (16, 54):
        win = poly((x, 44), (x + 10, 44), (x + 10, 56), (x, 56))
        d.shape(win, w=1.0)
        d.hatch(win, angle=45, pitch=1.3)
    d.shape(poly((30, 40), (50, 40), (50, 46), (30, 46)), w=0.9)
    d.line("M33,43 l14,0", w=0.6, halo=False)
    d.line("M28,80 L52,80 M26,83 L54,83 M24,86 L56,86", w=1.0)
    d.edge_shade(front, dx=-3, dy=0)
    d.line("M40,28 L40,6", w=1.0)
    flag = "M40,7 C44,5 48,9 54,7 L54,15 C48,17 44,13 40,15 Z"
    d.shape(flag, w=1.0)
    d.line("M40,9.6 C44,8 48,12 54,10 M40,12.4 C44,10.6 48,14.6 54,12.6", w=0.5, halo=False)
    # Billy walking away down the street.
    figure(d, 84, 88, 28, flip=True)
    d.ground(2, 94, 89, ticks=6, seed=350)
    return d


# 13. The corridero in the bodega at Temósachic (4-05) -------------------------------------------------
def corridero() -> Drawing:
    d = Drawing("corridero")
    # The single shaded bulb over the table.
    d.line("M50,2 L50,12", w=0.8)
    d.shape("M44,18 L47,12 L53,12 L56,18 Z", w=1.0)
    d.line("M40,24 l-3,3 M60,24 l3,3 M50,22 l0,4", w=0.6, halo=False)
    # The singer seated, his hat on, the guitar on his knee, one hand on its neck, the other raising his glass.
    d.shape("M24,90 L26,70 L40,70 L42,90", w=1.2, fill=False)
    coat = "M22,74 C20,62 22,52 29,48.6 C35,47 41,48.6 44,54 C46,60 46,68 44,74 Z"
    d.shape(coat)
    d.edge_shade(coat, dx=-3, dy=-2)
    d.shape(circle(33, 39.6, 4.4), w=1.3)
    d.shape("M22,32.6 C27,30.6 39,30.6 44,32.6 C39,34.6 27,34.6 22,32.6 Z", w=1.3)
    d.shape("M27.6,32 C27.6,24 38.4,24 38.4,32 Z", w=1.3)
    d.hatch("M27.6,32 C27.6,24 38.4,24 38.4,32 Z", angle=45, pitch=1.2)
    guitar = ("M14,74 C10,70 12,64 17,64 C20,64 22,66 24,66 C27,64 32,64 34,68 C36,72 34,78 28,79 "
              "C25,79 23,77 21,77 C18,79 15,78 14,74 Z")
    d.shape(guitar, w=1.3)
    d.shape(circle(25, 71, 2.0), w=0.9)
    d.hatch(circle(25, 71, 2.0), angle=45, pitch=0.8)
    d.line("M32,68 L60,56", w=2.0)
    d.shape(poly((58, 54), (66, 51), (67, 54), (60, 58)), w=1.0)
    d.line("M44,54 C50,52 54,54 58,56", w=1.4)
    d.line("M40,48 C44,42 46,36 48,30", w=1.4)
    d.shape(poly((46, 30), (51, 30), (50.4, 23), (46.6, 23)), w=1.0)
    # The table with a bottle on it.
    d.shape(poly((60, 70), (94, 70), (94, 73), (60, 73)), w=1.3)
    d.line("M64,73 L64,90 M90,73 L90,90", w=1.3)
    bottle = "M76,70 L76,60 C76,58 77,57 78,56 L78,51 L80,51 L80,56 C81,57 82,58 82,60 L82,70 Z"
    d.shape(bottle, w=1.0)
    d.hatch(bottle, angle=60, pitch=1.2)
    d.line("M2,90 L94,90", w=1.0)
    return d


# 14. Billy at dawn at the Buenaventura crossroads, the waterfowl going over (3-14) ---------------------
def waterfowl() -> Drawing:
    d = Drawing("waterfowl")
    # The sun coming up red behind the lagunas, and long trailing skeins of birds against it.
    d.line("M60,52 C60,44 66,40 72,40 C78,40 84,44 84,52", w=1.1)
    d.line("M56,46 l-4,-2 M60,40 l-3,-4 M72,36 l0,-5 M84,40 l3,-4 M88,46 l4,-2", w=0.7, halo=False)
    chevrons(d, [(10, 18, 1.0), (16, 22, 0.9), (22, 26, 0.9), (28, 30, 0.8), (34, 34, 0.8), (40, 20, 1.0),
                 (46, 24, 0.9), (52, 28, 0.8), (62, 14, 0.9), (68, 18, 0.8), (74, 22, 0.8), (80, 26, 0.7)])
    d.line("M40,54 C54,52 70,53 94,52 M48,58 l14,0 M70,57.6 l12,0", w=0.9)
    d.line("M2,62 C14,60 24,61 32,62", w=0.8, halo=False)
    rider(d, 26, 88, 0.44, hat="cowboy")
    d.ground(2, 94, 89, ticks=6, seed=360)
    return d


# 15. Billy in his rags with the bow, riding the high woods (J3, 2-01) ----------------------------------
def billy_in_rags() -> Drawing:
    d = Drawing("billy-in-rags")
    # Madroño and oak of the high country: twisted trunks, low lumpy crowns.
    for x, base, h, w, seed in ((12, 62, 44, 22, 370), (84, 60, 40, 22, 371)):
        cottonwood(d, x, base, h, w, seed=seed)

    def bow(t):
        d.line(t("M38,16 C30,24 30,40 40,48"), w=1.3)
        d.line(t("M38,16 L40,48"), w=0.5, halo=False)
        d.line(t("M45,30 l-2,4 M50,32 l1,4 M47,40 l-3,3"), w=0.7, halo=False)
    rider(d, 50, 86, 0.66, hat="straw", extra=bow)
    d.ground(2, 94, 87, ticks=6, seed=372)
    return d


# 16. Billy riding west towards La Norteña and the watershed (J5, 3-14) --------------------------------
def billy_to_the_watershed() -> Drawing:
    d = Drawing("billy-to-the-watershed")
    ridge = "M2,46 L12,34 L20,40 L30,26 L40,36 L52,28 L62,38 L70,32 L80,40 L94,36"
    d.line(ridge, w=1.1)
    d.hatch(ridge + " L94,50 L2,50 Z", angle=70, pitch=2.6, w=0.6)
    d.line("M4,58 C30,57 60,57 94,56", w=0.8)
    rider(d, 52, 86, 0.64, flip=True, hat="low")
    d.ground(2, 94, 87, ticks=6, seed=380)
    return d


# 17. Billy with his packhorse in the pine country to Temósachic (J7, 4-05) -----------------------------
def billy_and_packhorse() -> Drawing:
    d = Drawing("billy-and-packhorse")
    for x, base, h, seed in ((8, 56, 34, 1), (88, 54, 36, 2), (78, 52, 24, 3)):
        pine(d, x, base, h, seed=390 + seed)
    horse(d, 28, 82, 0.4, flip=True, saddle=False, pack=True)
    d.line("M48,50 C42,56 34,58 26,60", w=0.7, halo=False)
    rider(d, 60, 88, 0.56, flip=True, hat="cowboy")
    d.ground(2, 94, 89, ticks=6, seed=391)
    return d


SUBJECTS = {
    "echols-cabin": echols_cabin,
    "dead-calf": dead_calf,
    "arnulfo-house": arnulfo_house,
    "wolf-in-the-cholla": wolf_in_the_cholla,
    "parham-house": parham_house,
    "keno-bacerac": keno_bacerac,
    "taking-the-girl": taking_the_girl,
    "colonia-juarez": colonia_juarez,
    "quijada": quijada,
    "remuda": remuda,
    "night-train": night_train,
    "recruiting-office": recruiting_office,
    "corridero": corridero,
    "waterfowl": waterfowl,
    "billy-in-rags": billy_in_rags,
    "billy-to-the-watershed": billy_to_the_watershed,
    "billy-and-packhorse": billy_and_packhorse,
}
