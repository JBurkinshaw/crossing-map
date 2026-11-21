"""Draw the vignettes and rebuild the map sprite (design section 10).

Run from the repo root: uv run --project pipeline --extra art python -m art.vignettes.make_vignettes [ID ...]
Needs spreet (cargo install spreet).

Thirteen drawings of what the book describes, each looking roughly as its subject did around 1940, on the
96 x 96 sprite grid, named vignette-<id> as in pipeline/seeds/vignettes.csv. Each subject is a function that
returns a Drawing (art/vignettes/ink.py), drawn with the mountain glyphs' pen in two inks. Outlines marked
traced come from public-domain photographs: art/vignettes/traced/<id>.json holds only our traced geometry (the
photographs and the tracing script stay in private/; the credits are in the seed's `credit` column). The rest
are drawn by hand in SVG, with proportions taken from the references listed in the seed.
"""

import importlib
import math
import random
import sys
from pathlib import Path

from shapely.ops import unary_union

from art import PAPER
from art.build_sprite import build_sprite
from art.vignettes.ink import Drawing, region
from art.vignettes.shapes import circle, ellipse, grass, poly, traced, warp
from art.vignettes.subjects_parts_3_4 import blob
from art.vignettes.subjects_round3 import _path
from art.vignettes.subjects_round4 import shift, water
from art.vignettes.subjects_round5_a import hound
from art.vignettes.subjects_round5_e import LIE, hat, person
from art.vignettes.subjects_round6_a import handler, onlooker, stump

SVG_DIR = Path(__file__).parent / "svg"


def she_wolf() -> Drawing:
    d, t = Drawing("she-wolf"), traced("she-wolf")
    # Behind her the cut-over slope of the sierra: rows of sawn stumps and a felled trunk where the forest stood.
    d.line("M2,8 C22,9 52,15 94,22", w=1.0)
    for x, base, w, felled in ((14, 18, 4.2, False), (36, 20, 4, False), (60, 24, 4.4, False), (84, 27, 4, False),
                               (22, 32, 6, True), (50, 33, 5.6, False), (62, 35, 5.6, False), (9, 46, 7.6, False),
                               (33, 41, 6, False)):
        stump(d, x, base, w, w * 0.9, felled)
    k, ox, oy = 0.86, 6, 18
    for p in t["outline"]:
        q = warp(p, lambda x, y: (ox + x * k, oy + y * k))
        d.shape(q)
        d.edge_shade(q, dx=-3, dy=-3.5)
    for p in t["tones"]["0.3"]:
        d.hatch(warp(p, lambda x, y: (ox + x * k, oy + y * k)), pitch=2.4)
    d.ground(6, 90, 88, ticks=5, seed=3)
    grass(d, [(10, 88), (56, 88), (84, 88)])
    return d


# 3. The boundary obelisk -------------------------------------------------------------------------------
def obelisk() -> Drawing:
    d = Drawing("obelisk")
    # Red hills behind (the book), then the monument on its stepped base.
    hills = "M4,70 C14,62 22,60 30,64 C36,58 44,56 50,62 C58,58 70,57 78,63 C84,61 89,63 92,66"
    d.line(hills, w=1.1)
    d.hatch(hills + " L92,72 L4,72 Z", angle=20, pitch=3.2, w=0.6)
    # Shaft: lit west face and shaded east face.
    d.shape(poly((40.5, 77), (43, 22), (46, 14), (49, 22), (53.5, 77)))
    d.line("M46,14 L47.2,22.4 L48.6,77", w=1.0, halo=False)
    d.hatch(poly((46, 14), (49, 22), (53.5, 77), (48.6, 77), (47.2, 22.4)), angle=60, pitch=2.2)
    d.line("M43,22 L49,22", w=0.9, halo=False)
    # Base in two steps.
    d.shape(poly((36, 77), (58, 77), (58, 81), (36, 81)))
    d.hatch(poly((48.6, 77), (58, 77), (58, 81), (48.6, 81)), angle=60, pitch=2.2)
    d.shape(poly((32, 81), (62, 81), (62, 85), (32, 85)))
    d.hatch(poly((48.6, 81), (62, 81), (62, 85), (48.6, 85)), angle=60, pitch=2.2)
    # An inscription panel, and an ocotillo to the west for scale.
    d.line("M43.5,58 l3.5,0 M43.6,60.5 l3.4,0", w=0.6, halo=False)
    d.line("M18,86 C17,76 13,66 11,58 M19,86 C19,74 19,64 20,54 M20,86 C22,78 25,70 28,63 M18.5,86 C16,80 10,76 7,72", w=1.0)
    d.ground(4, 92, 86, ticks=7, seed=5)
    return d


# 4. The cockpit at the hacienda: the crowd on the bleachers, the blood-black palisade, the wolf at the stake --
def hacienda_pit() -> Drawing:
    d = Drawing("hacienda-pit")
    # The tin reflectors hung over the pit.
    for x in (26, 70):
        d.line(f"M{x},0 L{x},4", w=0.7, halo=False)
        d.shape(f"M{x - 5},9 L{x - 1.6},4 L{x + 1.6},4 L{x + 5},9 Z", w=1.0)
    # The bleachers on poles along the far side, packed with men in hats.
    for y in (19, 27, 35):
        d.line(f"M4,{y} L92,{y}", w=1.2)
    d.line("M8,19 L8,44 M30,19 L30,44 M66,19 L66,44 M88,19 L88,44", w=0.9)
    rows = ((18, 0.78, [8 + 7 * i for i in range(12)]), (26, 0.84, [11 + 7.5 * i for i in range(11)]),
            (34, 0.9, [6 + 8 * i for i in range(12)]))
    for row, (y, s, xs) in enumerate(rows):
        for i, x in enumerate(xs):
            onlooker(d, x, y, s, dark=(i + row) % 3 == 0)
    # The estacada: a low palisade of boards black with old blood round a dirt floor, seen across from the crowd.
    d.shape(ellipse(48, 59, 44, 14), w=1.6)
    far = "M4,59 C4,50 24,45 48,45 C72,45 92,50 92,59 C92,54 72,50 48,50 C24,50 4,54 4,59 Z"
    d.hatch(far, angle=80, pitch=1.4, cross=True)
    d.line("M4,59 C4,54 24,50 48,50 C72,50 92,54 92,59", w=0.9, halo=False)
    near = "M4,59 C4,67 24,73 48,73 C72,73 92,67 92,59 L92,66 C92,75 72,81 48,81 C24,81 4,75 4,66 Z"
    d.shape(near, w=1.6)
    d.hatch(near, angle=60, pitch=1.5, cross=True)
    for x in (10, 18, 27, 37, 48, 59, 69, 78, 86):
        yt = 59 + 14 * math.sqrt(max(0, 1 - ((x - 48) / 44) ** 2))
        d.line(f"M{x},{yt:.1f} L{x},{yt + 7:.1f}", w=1.0, color=PAPER, halo=False)
    # The iron pipe and the wolf down by it on her chain, her head in the dirt.
    d.line("M47,50 L47,62", w=2.2)
    bend = lambda x, y: LIE(x, y + (0.25 * (x - 66) if x > 66 else 0))  # noqa: E731
    for p in traced("she-wolf")["outline"]:
        q = warp(p, lambda x, y: (14 + bend(x, y)[0] * 0.37, 41 + bend(x, y)[1] * 0.37))
        d.shape(q, w=1.6)
        d.edge_shade(q, dx=-1.4, dy=-1.6)
    d.line("M47,60.4 C45,62.6 43,63 41,62", w=0.9, halo=False)
    # Across the pit the two airedales straining at their leashes, the handlers braced back.
    for ox, hx in ((50, 69), (68, 87)):
        g = hound(d, 0.16, ox, 49, flip=True, collar=True)
        hand = handler(d, hx, 63, 16)
        cx, cy = g(70, 42)
        d.line(f"M{cx:.1f},{cy:.1f} L{hand[0]:.1f},{hand[1]:.1f}", w=0.8, halo=False)
    # Those standing nearest, seen from behind at the front of the crowd.
    for x in (6, 17, 79, 90):
        onlooker(d, x, 97, 1.5, dark=True, behind=True)
    return d


# 5. The ruined adobe church ----------------------------------------------------------------------------
def ruined_church() -> Drawing:
    d = Drawing("ruined-church")
    # Nave wall running back to the east, its top worn ragged, no roof.
    nave = "M44,40 C50,38 54,44 60,42 C66,40 70,46 76,45 C80,44 84,48 88,49 L88,82 L44,84 Z"
    d.shape(nave)
    d.edge_shade(nave, dx=-4, dy=-3)
    # A breach in the nave wall shows the dark inside and the roof beams fallen across it.
    breach = "M54,44 C58,50 60,56 62,62 C66,58 70,58 74,62 C76,56 78,50 80,47 L80,70 L54,70 Z"
    d.shape(breach, w=1.3)
    d.hatch(breach, angle=45, pitch=1.6, cross=True)
    d.line("M50,58 L84,40", w=2.6)
    d.line("M56,70 L82,52", w=2.6)
    d.line("M50,58 L84,40 M56,70 L82,52", w=0.9, color=PAPER, halo=False)
    # West front: a tall gable, eroded at the top, with a broken belfry stub and an arched door.
    front = "M14,84 L14,36 C16,32 20,30 24,26 L26,18 L32,18 L33,24 C38,28 42,32 44,36 L44,84 Z"
    d.shape(front)
    d.shape("M23,84 L23,62 C23,55 35,55 35,62 L35,84 Z")
    d.hatch("M23,84 L23,62 C23,55 35,55 35,62 L35,84 Z", angle=45, pitch=1.8, cross=True)
    d.line("M27,26 C27,23 31,23 31,26 L31,30 L27,30 Z", w=1.0)
    d.line("M18,48 l3,0 M38,44 l3,1 M16,70 l2.5,0.6 M40,70 l2,0", w=0.7, halo=False)
    # Rubble mounds at the foot.
    d.shape("M40,86 C44,79 50,79 54,83 C58,78 66,78 70,84 C74,80 82,80 90,86 Z", w=1.4)
    d.dots([(47, 84), (51, 83), (61, 82), (64, 84), (76, 83), (80, 84.5)], r=0.8)
    d.ground(6, 92, 87, ticks=6, seed=8)
    return d


# 6. Paquimé ---------------------------------------------------------------------------------------------
def paquime() -> Drawing:
    d = Drawing("paquime")
    moon = circle(76, 17, 7)
    d.shape(moon, w=1.3)
    d.hatch("M76,10 C82,11 84,22 76,24 C80,20 80,14 76,10 Z", angle=45, pitch=1.8)
    # Three ranks of worn mud walls, rounded at the tops, stepping down towards the viewer.
    back = "M30,58 L30,36 C30,32 34,31 36,33 C40,30 46,30 50,32 C56,30 64,31 70,34 C74,33 78,35 78,39 L78,58 Z"
    d.shape(back)
    d.edge_shade(back, dx=-4, dy=-3)
    d.line("M50,32 L50,58 M64,32 L64,58", w=0.9, halo=False)
    mid = "M54,72 L54,48 C54,45 58,44 60,45 C66,43 74,44 80,46 C84,46 88,48 88,52 L88,72 Z"
    d.shape(mid)
    d.edge_shade(mid, dx=-4, dy=-3)
    # The front wall with a T-shaped doorway.
    front = "M8,84 L8,54 C8,50 12,49 15,50 C22,47 32,48 38,50 C44,48 52,49 56,52 C60,52 62,55 62,58 L62,84 Z"
    d.shape(front)
    d.edge_shade(front, dx=-4, dy=-3)
    tdoor = poly((26, 84), (26, 70), (21, 70), (21, 61), (37, 61), (37, 70), (32, 70), (32, 84))
    d.shape(tdoor, w=1.3)
    d.hatch(tdoor, angle=45, pitch=1.6, cross=True)
    d.line("M44,66 l4,0.4 M14,76 l3,0 M50,58 l3,-0.4", w=0.7, halo=False)
    # A squatter's fire and its smoke against the walls.
    d.line("M70,82 l2.5,-4.5 l1.5,3 l1.5,-5 l1.8,6.5", w=1.2)
    d.line("M73.5,72 C70,68 76,64 72,59 C69,55 74,52 72,48", w=0.8, halo=False)
    d.ground(4, 92, 85, ticks=7, seed=11)
    return d


# 7. The Hacienda de San Diego going to ruin: the house front, its arches and initials, plaster flaking, shutters
# broken (3-01, 4-04) -------------------------------------------------------------------------------------
def san_diego() -> Drawing:
    d = Drawing("san-diego-gate")
    body = poly((6, 84), (6, 44), (90, 44), (90, 84))
    d.shape(body)
    # Parapet with the pierced terracotta band, broken away at the east corner; a raised panel over the arches.
    d.shape(poly((6, 44), (6, 38), (28, 38), (28, 34), (68, 34), (68, 38), (80, 38), (82, 41), (86, 39), (90, 42),
                 (90, 44)))
    d.line(" ".join(f"M{x},40.8 l1.6,0" for x in range(9, 79, 3) if x not in (18, 21, 54)), w=0.9, halo=False)
    d.shape(poly((30, 34), (34, 24), (62, 24), (66, 34)))
    # The carved name, arched, over the initials: drawn as a curved line of tick marks and a real L T.
    d.line(" ".join(f"M{48 + 13 * math.cos(math.radians(a)):.1f},{35 - 7 * math.sin(math.radians(a)):.1f} l0,1.6"
                    for a in range(160, 15, -9)), w=0.7, halo=False)
    d.line("M43,28.5 L43,32.5 L46,32.5 M50,28.5 L54,28.5 M52,28.5 L52,32.5", w=1.1, halo=False)
    # Three stone arches with the dark portico behind.
    for x in (30, 44, 58):
        arch = f"M{x},84 L{x},62 C{x},54 {x + 10},54 {x + 10},62 L{x + 10},84 Z"
        d.shape(arch, w=1.4)
        d.hatch(arch, angle=45, pitch=1.8, cross=True)
    d.line("M28,84 L28,48 L70,48 L70,84", w=1.0, halo=False)
    # Plaster flaked away in patches, the adobe courses showing; cracks running down from the parapet.
    for patch in ("M34,46 C38,44.6 44,45 46,47 C46,50 43,53 39,53 C36,52.6 33,50 34,46 Z",
                  "M60,47 C63,45.4 68,46 68,49 C67,52 63,53 61,51.6 Z",
                  "M7,77 C10,75 15,75.4 16,78.6 C16,82 11,83 8,82 Z", "M78,76 C82,74.4 88,75 88,78.6 C87,82 81,82.6 79,81 Z"):
        d.shape(patch, w=1.0)
        d.hatch(patch, angle=0, pitch=1.5, w=0.6)
    d.line("M24,44 l-1.4,3 l1.6,2.4 l-1.2,3.4 M82,44 l1.2,2.6 l-1.6,2 l1,3", w=0.7, halo=False)
    # The tall windows in the wings, their shutters weathered and broken: one hanging askew off its hinge, one gone
    # to the dark of the room, two with louvres missing.
    for x in (11, 19, 75, 83):
        w = poly((x - 2.5, 74), (x - 2.5, 52), (x + 2.5, 52), (x + 2.5, 74))
        d.shape(w, w=1.1)
        if x in (19, 75):
            d.hatch(w, angle=45, pitch=1.3, cross=True)
        else:
            d.line(" ".join(f"M{x - 2.5},{y} l5,0" for y in range(54, 73, 2) if not 58 < y < 66), w=0.7, halo=False)
    hung = poly((21.4, 52.6), (26.4, 54.6), (22.6, 75.4), (17.8, 73.4))
    d.shape(hung, w=1.1)
    d.hatch(hung, angle=-12, pitch=1.6)
    for y in range(46, 84, 6):
        d.line(f"M6,{y} l3,0 l0,3 l-3,0 M90,{y} l-3,0 l0,3 l3,0", w=0.8, halo=False)
    d.edge_shade(body, dx=-3, dy=-2.5)
    # Fallen plaster and a broken board at the foot of the wall.
    d.dots([(12, 85.6), (15, 86.4), (78, 85.8), (82, 86.4), (86, 85.4)], r=0.9)
    d.ground(2, 94, 87, ticks=8, seed=4)
    return d


# 8. The opera company's caravan wagon and its mule -----------------------------------------------------
def opera_caravan() -> Drawing:
    d = Drawing("opera-caravan")
    # The second wagon behind, and the wash hung between them.
    d.shape("M6,62 L6,34 C14,27 30,27 38,34 L38,62 Z", w=1.6)
    d.line("M6,40 L38,40 M6,46 L38,46", w=0.8, halo=False)
    d.edge_shade("M6,62 L6,34 C14,27 30,27 38,34 L38,62 Z", dx=-3, dy=-3)
    for cx in (13, 29):
        d.shape(circle(cx, 66, 5), w=1.3)
    d.line("M12,36 C20,40 28,40 36,36", w=0.7, halo=False)
    d.line("M16,38 l0,5 l3,0 l0,-4 M24,39.5 l0,6 l3,0 l0,-6", w=0.8, halo=False)
    # The wagon body with a curved roof, a band of faded gilt lettering and a painted panel.
    body = "M36,68 L36,36 C46,28 78,28 90,36 L90,68 Z"
    d.shape(body)
    d.line("M36,38 C46,31 78,31 90,38", w=1.0, halo=False)
    d.line("M38,42 L88,42 M38,49 L88,49", w=0.9, halo=False)
    d.line(" ".join(f"M{x},44 l0,3 M{x + 1.5},44 l1.2,3" for x in range(41, 86, 4)), w=0.6, halo=False)
    for x in (42, 60, 76):
        panel = poly((x, 53), (x + 10, 53), (x + 10, 64), (x, 64))
        d.shape(panel, w=0.9)
    d.line("M44,58 C46,55 50,55 52,58 C50,61 46,61 44,58 Z M62,62 L66,55 L70,62 M80,55 L84,62 M84,55 L80,62", w=0.7, halo=False)
    d.edge_shade(body, dx=-3, dy=-3)
    # Wheels: small at the front, big at the back.
    for cx, cy, r in ((46, 74, 8), (80, 72, 11)):
        d.shape(circle(cx, cy, r), w=1.6)
        d.line(" ".join(f"M{cx},{cy} L{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}" for a in
                        [i * math.pi / 5 for i in range(10)]), w=0.7, halo=False)
        d.shape(circle(cx, cy, 1.8), w=0.9)
    # The shafts let down on the ground: the company halted in a field.
    d.line("M36,62 L27,82 M36,66 L31,83", w=1.3)
    d.ground(4, 94, 84, ticks=7, seed=6)
    return d


# 9. The blind man --------------------------------------------------------------------------------------
def blind_man() -> Drawing:
    d = Drawing("blind-man")
    # The rutted road and wildflowers by it (the book has rain and flowers on his walk).
    d.line("M4,86 C30,85 60,84 92,84 M10,91 C36,90 62,89 92,89", w=0.9)
    for x, y in ((12, 82), (18, 80), (80, 79), (86, 81)):
        d.line(f"M{x},{y + 4} L{x},{y}", w=0.7)
        d.dots([(x, y)], r=1.2)
    # A walking figure facing east: broad hat, coat, bare feet, the green stick probing ahead.
    back_leg = "M38,58 L44,58 L39,82 L34,82 Z"
    d.shape(back_leg, w=1.5)
    d.hatch(back_leg, pitch=1.8)
    d.line("M34,82.5 L40,83", w=1.4)
    coat = "M36,34 C40,31 46,31 50,33 L53,47 L51,61 L35,61 L34,47 Z"
    front_leg = "M44,59 L50,59 L58,82 L53,83 Z"
    d.shape(front_leg, w=1.5)
    d.line("M53,83.5 L59.5,83.5", w=1.4)
    d.shape(coat)
    d.edge_shade(coat, dx=-3, dy=-1.5)
    d.line("M42,33 L43,60 M38,48 L48,48", w=0.7, halo=False)
    # Arm and stick.
    d.line("M48,36 L56,46 L60,47", w=2.6)
    d.line("M58,44 L76,85", w=1.4)
    # Head, closed eyes, moustache, and the hat.
    d.shape(circle(43, 27.5, 4.6), w=1.5)
    d.line("M45,26.6 l2.4,0.4 M45.6,30 l2.6,0.6", w=0.8, halo=False)
    d.shape("M31,22.5 C36,20.4 50,20.4 55,22.5 C50,24.6 36,24.6 31,22.5 Z", w=1.5)
    crown = "M37,22 C37,16 39,13.6 43,13.6 C47,13.6 49,16 49,22 Z"
    d.shape(crown, w=1.5)
    d.hatch("M37,22 L37,19.5 L49,19.5 L49,22 Z", angle=0, pitch=1.0)
    return d


# 10. The red Waco circling over the plain, the dust smoking off Babícora beyond the lake (4-04) ----------
def red_plane() -> Drawing:
    d = Drawing("red-plane")
    # The dust blowing out of Babícora on the dry north wind, smoking up off the far plain as if it were afire:
    # loose plumes of hatched tone, rising from the ground and streaming away downwind.
    plumes = ((90, 36, 9, 8), (78, 40, 12, 9), (86, 50, 10, 7), (64, 46, 12, 8), (50, 51, 11, 7), (72, 55, 10, 6),
              (36, 56, 10, 5.4), (56, 58, 9, 4.6), (22, 59, 9, 4), (10, 61, 6, 2.6))
    puffs = [blob(cx, cy, rx, ry, 9, seed=903 + i, depth=0.26) for i, (cx, cy, rx, ry) in enumerate(plumes)]
    d.shape(_path(unary_union([region(p) for p in puffs]).simplify(0.2)), w=0.7)
    for puff in puffs:
        d.line(puff, w=0.5, halo=False)
        d.hatch(puff, angle=-25, pitch=2.2, w=0.5)
    d.line("M4,63 C30,62.4 60,62.4 94,62", w=1.0)
    d.dots([(30, 50), (52, 42), (70, 34), (88, 28), (40, 47), (62, 38)], r=0.5)
    # The lake in front of it, and the trees the plane comes down among.
    water(d, 72, 6, 62, seed=1)
    for x, h in ((70, 10), (78, 13), (86, 9)):
        d.shape(f"M{x - 4},{88} C{x - 6},{88 - h} {x - 2},{88 - h - 4} {x},{88 - h - 3} C{x + 3},{88 - h - 4} {x + 6},{88 - h} {x + 4},{88} Z", w=1.2)
        d.hatch(f"M{x},{88 - h - 3} C{x + 3},{88 - h - 4} {x + 6},{88 - h} {x + 4},{88} L{x},{88} Z", pitch=1.8)
    d.ground(6, 94, 89, ticks=5, seed=2)
    # The big cabin biplane overhead, coming round on its circle (drawn full size, then made smaller).
    since = len(d.items)
    # A cabin biplane in side view, banking a little: lower wing, fuselage, upper wing (staggered forward).
    lower = "M30,54 L64,52 C66,52 67,54 65,55 L31,57 C29,57 28,55 30,54 Z"
    d.shape(lower, w=1.4)
    fus = ("M18,48 C22,44 30,42 34,42 L38,36 C42,34 50,34 54,36 L62,40 C66,41 70,43 71,46 L71,52 "
           "C66,54 58,54 54,53 L24,52 C20,51 17,50 18,48 Z")
    d.shape(fus)
    d.line("M40,37 L40,43 L52,43 L52,37", w=0.9, halo=False)
    d.line("M46,36 L46,43", w=0.7, halo=False)
    # Tail: rounded fin and the tailplane.
    d.shape("M18,48 C14,46 11,40 12,34 C14,32 17,33 19,36 L24,45 Z", w=1.4)
    d.line("M12,48 L26,48", w=1.6)
    # Engine cowling and propeller.
    d.shape(ellipse(72, 47, 3.2, 6.2), w=1.4)
    d.line("M75.5,38 C76.5,44 76.5,50 75.5,57", w=1.0)
    upper = "M38,28 L74,26 C76,26 77,28 75,29 L39,31 C37,31 36,29 38,28 Z"
    d.shape(upper, w=1.6)
    d.edge_shade(upper, dx=0, dy=-1.6)
    # Interplane struts and the landing gear.
    d.line("M44,31 L42,53 M66,29 L62,52 M44,31 L50,52", w=1.0, halo=False)
    d.line("M54,53 L57,58 M60,53 L57,58", w=1.2)
    d.shape(circle(57, 59.5, 3), w=1.4)
    d.hatch(circle(57, 59.5, 3), pitch=1.4)
    d.edge_shade(fus, dx=-2.5, dy=-3)
    shift(d, since, 2, -12, 0.66)
    return d


# 11. The gypsies' airplane on its float ----------------------------------------------------------------
def gypsy_plane() -> Drawing:
    d = Drawing("gypsy-plane")
    # The wings, folded and roped down along the far side of the fuselage.
    wing = "M38,44 L92,40 L92,48 L38,52 Z"
    d.shape(wing, w=1.3)
    d.line(" ".join(f"M{x},{44 - (x - 38) * 4 / 54:.1f} L{x},{52 - (x - 38) * 4 / 54:.1f}" for x in range(43, 92, 5)), w=0.6, halo=False)
    # The fuselage: a bare frame of longerons and diagonals, a shred of fabric, the rudder.
    fus = "M36,58 L36,46 C40,42 46,42 50,44 L88,50 L88,56 L50,60 Z"
    d.shape(fus, w=1.5)
    d.line("M40,52 L86,53 " + " ".join(f"M{x},{44 + (x - 50) * 6 / 38:.1f} L{x + 5},{59.4 - (x - 50) * 3.6 / 38:.1f}" for x in range(50, 85, 6)), w=0.7, halo=False)
    d.line(" ".join(f"M{x},{44 + (x - 50) * 6 / 38:.1f} L{x},{60 - (x - 50) * 4 / 38:.1f}" for x in range(50, 88, 6)), w=0.8, halo=False)
    d.hatch("M60,46 L68,47.2 L67,52 C64,54 62,51 60,53 Z", angle=30, pitch=1.4)
    d.shape("M86,50 L88,38 L94,38 L94,56 L88,56 Z", w=1.3)
    d.line("M90,40 L90,55 M92,40 L92,55", w=0.6, halo=False)
    # Engine stub at the front.
    d.shape(poly((30, 46), (36, 46), (36, 58), (30, 58)), w=1.3)
    d.hatch(poly((30, 46), (36, 46), (36, 58), (30, 58)), pitch=1.8)
    # Ropes.
    d.line("M44,42 L44,62 M70,40 L70,62", w=0.7, halo=False)
    # The float of green lumber on old truck axles.
    bed = poly((24, 62), (92, 62), (92, 67), (24, 67))
    d.shape(bed, w=1.5)
    d.line("M24,64.5 L92,64.5", w=0.6, halo=False)
    d.edge_shade(bed, dx=0, dy=-2.5)
    for cx in (36, 80):
        d.shape(circle(cx, 72, 6), w=1.6)
        d.shape(circle(cx, 72, 2.2), w=1.0)
    # The yoke of oxen out in front, small, heads down (drawn after Fattori's etching of yoked oxen).
    def ox(dx, dy, front=True):
        body = (f"M{9 + dx},{56 + dy} C{13 + dx},{51 + dy} {22 + dx},{52 + dy} {26 + dx},{55 + dy} L{27 + dx},{65 + dy} "
                f"L{25.5 + dx},{76 + dy} L{23.5 + dx},{76 + dy} L{22.5 + dx},{67 + dy} L{13 + dx},{67 + dy} L{12 + dx},{76 + dy} "
                f"L{10 + dx},{76 + dy} L{9 + dx},{65 + dy} L{6 + dx},{63 + dy} L{3 + dx},{64 + dy} L{1.5 + dx},{61 + dy} "
                f"L{3.5 + dx},{57 + dy} Z")
        d.shape(body, w=1.4)
        d.edge_shade(body, dx=-2, dy=-2.5)
        d.line(f"M{5 + dx},{56.5 + dy} l-2.5,-3.5 M{7.5 + dx},{55.5 + dy} l1,-4", w=1.1)
    ox(5, -3)
    ox(0, 0)
    d.line("M2,54.5 L12,51.5", w=1.6)
    d.line("M24,64 L10,56", w=1.2)
    d.ground(2, 94, 79, ticks=7, seed=9)
    return d


# 12. Billy in the rain with the pipe, the crippled dog hobbling off up the wet road (4-08) -------------
def crippled_dog() -> Drawing:
    d = Drawing("crippled-dog")
    rnd = random.Random(912)
    d.line(" ".join(f"M{rnd.uniform(2, 98):.1f},{rnd.uniform(2, 70):.1f} l-2.4,{5 + rnd.random() * 4:.1f}"
                    for _ in range(34)), w=0.5, halo=False)
    # The corner of the ruined waystation, its doorway dark.
    wall = "M-2,86 L-2,30 C4,28 8,32 14,29 L18,31 L18,86 Z"
    d.shape(wall, w=1.6)
    door = poly((4, 86), (4, 52), (13, 52), (13, 86))
    d.shape(door, w=1.2)
    d.hatch(door, angle=45, pitch=1.5, cross=True)
    d.edge_shade(wall, dx=-2.4, dy=0)
    # The wet road running off up the country into the dusk: dark with rain, puddles shining on it.
    d.line("M18,36 C40,35 70,35 96,36", w=0.8)
    d.line("M22,35.6 C30,31 40,31 48,35 M80,35.4 C86,30.4 92,31 96,32", w=0.8, halo=False)
    road = "M40,96 C52,72 64,52 72,36 L76,36 C80,52 88,72 98,96 Z"
    d.line("M40,96 C52,72 64,52 72,36 M76,36 C80,52 88,72 98,96", w=1.1)
    d.hatch(road, angle=0, pitch=1.6, w=0.7)
    for x, y, w in ((58, 86, 10), (74, 76, 8), (70, 44, 3), (76, 40, 2)):
        d.line(f"M{x},{y} l{w},0", w=1.4, color=PAPER, halo=False)
    # The dog going away up the road on its twisted legs, its head thrown up sideways to howl.
    def bend(x, y):
        if x < 40:
            y += (40 - x) * 0.22
        if x > 66:
            y -= (x - 66) * 0.5
            x -= (x - 66) * 0.3
        return x, y
    t = traced("she-wolf")
    for p in t["outline"]:
        q = warp(p, lambda x, y: (58 + bend(x, y)[0] * 0.28, 42 + bend(x, y)[1] * 0.28))
        d.shape(q, w=1.4)
        d.edge_shade(q, dx=-1.2, dy=-1.4)
    # Billy on the gravel apron, the length of pipe in his fist.
    person(d, (33, 44), (32.4, 48), (31, 66), back=[[(31, 66), (28, 77), (25, 88)], [(31.4, 50), (28, 58), (28, 65)]],
           front=[[(31, 66), (35, 77), (37, 88)], [(33, 50), (38.6, 45), (41, 39.4)]], r=3.2, width=7.6, w=2.2,
           dark=True)
    d.line("M38,45 L47.6,30.4", w=2.4)
    hat(d, 33.4, 41, s=1.05)
    d.line("M23,88.6 L27,88.6 M36,88.6 L40.6,88.6", w=1.4)
    d.ground(20, 94, 90, ticks=5, seed=901)
    return d


# 13. The Trinity cloud ---------------------------------------------------------------------------------
def trinity_cloud() -> Drawing:
    d = Drawing("trinity-cloud")
    # A few rays of the light the book describes, behind the cloud.
    d.line(" ".join(f"M{48 + 34 * math.cos(math.radians(a)):.1f},{56 - 34 * math.sin(math.radians(a)):.1f} "
                    f"L{48 + 44 * math.cos(math.radians(a)):.1f},{56 - 44 * math.sin(math.radians(a)):.1f}"
                    for a in range(15, 170, 15)), w=0.7, halo=False)
    t = traced("trinity-cloud")
    # The darker column under the cap and the skirt of dust it raises (drawn after the same photograph).
    stem = "M41,54 C42,64 38,72 30,80 L66,80 C58,72 54,64 55,54 Z"
    d.shape(stem, w=1.6)
    d.line("M45,58 C46,66 43,72 39,78 M49,58 L49,78 M52,60 C53,68 56,73 60,78", w=0.8, halo=False)
    d.edge_shade(stem, dx=-4, dy=0)
    skirt = "M14,84 C16,78 24,77 30,79 C34,75 40,75 44,78 C50,74 58,75 62,79 C68,76 78,77 82,84 Z"
    d.shape(skirt, w=1.5)
    d.edge_shade(skirt, dx=-2, dy=-3)
    d.shape("M80,84 C81,80 86,79 88,84 Z", w=1.2)
    for p in t["outline"]:
        d.shape(p)
        d.edge_shade(p, dx=-3.5, dy=-3.5)
    for p in t["tones"].get("0.3", []):
        d.hatch(p, angle=45, pitch=2.2)
    # The Oscura Mountains on the horizon and the desert floor.
    d.line("M4,82 C10,78 16,79 20,80 M76,80 C82,77 88,78 92,81", w=1.0)
    d.ground(4, 92, 86, ticks=7, seed=12)
    return d


SUBJECTS = {
    "she-wolf": she_wolf, "obelisk": obelisk, "hacienda-pit": hacienda_pit,
    "ruined-church": ruined_church, "paquime": paquime, "san-diego-gate": san_diego, "opera-caravan": opera_caravan,
    "blind-man": blind_man, "red-plane": red_plane, "gypsy-plane": gypsy_plane, "crippled-dog": crippled_dog,
    "trinity-cloud": trinity_cloud,
}


def all_subjects() -> dict:
    """These subjects and those of every art/vignettes/subjects_*.py module (each exports its own SUBJECTS)."""
    out = dict(SUBJECTS)
    for path in sorted(Path(__file__).parent.glob("subjects_*.py")):
        more = importlib.import_module(f"art.vignettes.{path.stem}").SUBJECTS
        if clash := out.keys() & more.keys():
            raise SystemExit(f"{path.name}: subjects already defined: {', '.join(sorted(clash))}")
        out.update(more)
    return out


def main() -> None:
    only = sys.argv[1:]
    subjects = all_subjects()
    for name, fn in subjects.items():
        if only and name not in only:
            continue
        (SVG_DIR / f"vignette-{name}.svg").write_text(fn().svg())
    print(f"{len(only) or len(subjects)} vignettes in {SVG_DIR}")
    build_sprite()


if __name__ == "__main__":
    main()
