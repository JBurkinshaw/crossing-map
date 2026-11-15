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
import sys
from pathlib import Path

from art import PAPER
from art.build_sprite import build_sprite
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly, traced, warp

SVG_DIR = Path(__file__).parent / "svg"


def she_wolf() -> Drawing:
    d, t = Drawing("she-wolf"), traced("she-wolf")
    for p in t["outline"]:
        d.shape(p)
        d.edge_shade(p, dx=-3, dy=-3.5)
    for p in t["tones"]["0.3"]:
        d.hatch(p, pitch=2.4)
    d.ground(8, 88, 84, ticks=5, seed=3)
    grass(d, [(14, 84), (60, 84), (84, 84)])
    return d


# 2. The Newhouse trap, chain and drag ------------------------------------------------------------------
def steel_trap() -> Drawing:
    d = Drawing("steel-trap")
    # Two long springs, each a narrow loop running out from the jaw posts (seen from above, a little oblique).
    d.shape("M38,36 C30,33 14,33 6,36 C4,37 4,41 6,42 C14,44 30,43 38,40 Z")
    d.line("M34,37.2 C26,36 15,36.2 9,38 C15,40 26,40 34,39", w=0.9, halo=False)
    d.shape("M58,36 C66,33 82,33 90,36 C92,37 92,41 90,42 C82,44 66,43 58,40 Z")
    d.line("M62,37.2 C70,36 81,36.2 87,38 C81,40 70,40 62,39", w=0.9, halo=False)
    # The base plate (cross) under the jaws.
    d.shape(poly((43, 26), (53, 26), (53, 33), (60, 33), (60, 45), (53, 45), (53, 52), (43, 52), (43, 45), (36, 45), (36, 33), (43, 33)))
    # Open jaws: a ring seen at an angle, and the pan with its lettering.
    d.shape(ellipse(48, 39, 15, 10.5), w=2.2, fill=False)
    d.shape(ellipse(48, 39, 12, 8), w=1.2, fill=False)
    d.shape(ellipse(48, 40, 6, 4), w=1.2)
    d.line("M45,40 l1.2,0 M47.4,40 l1.2,0 M49.8,40 l1.2,0", w=0.7, halo=False)
    d.hatch(poly((53, 33), (60, 33), (60, 45), (53, 45), (53, 52), (48, 52), (48, 47)), pitch=2.4)
    # The chain: links alternately seen flat and edge-on, curving down to the drag.
    pts = [(48, 54), (50, 60), (53, 65.5), (57, 70.5), (61.5, 74.5), (66.5, 78)]
    for i, (x, y) in enumerate(pts):
        if i % 2 == 0:
            d.shape(ellipse(x, y, 2.6, 3.4), w=1.3, fill=False)
        else:
            d.line(f"M{x - 1.4:.1f},{y - 2.6:.1f} L{x + 1.4:.1f},{y + 2.6:.1f}", w=1.6)
    # The two-pronged drag: a shank with two hooked prongs.
    d.line("M68,80 L80,86", w=2.2)
    d.line("M80,86 C86,88 88,82 85,78", w=2.0)
    d.line("M80,86 C83,92 89,92 91,87", w=2.0)
    d.line("M84.6,77.6 l1.8,-1.2 M91,87 l1.6,-1", w=1.3)
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


# 4. The cockpit at the hacienda: low palisade, the stake, the wolf on her chain ------------------------
def hacienda_pit() -> Drawing:
    d = Drawing("hacienda-pit")
    # Bleachers on poles behind, under the bodega's lights.
    d.line("M8,26 L88,26 M6,34 L90,34 M4,42 L92,42", w=1.3)
    d.line("M10,26 L10,50 M30,26 L30,46 M48,26 L48,44 M66,26 L66,46 M86,26 L86,50", w=1.0)
    d.line("M10,34 L30,26 M48,34 L66,26 M30,42 L48,34 M66,42 L86,34", w=0.7, halo=False)
    d.line("M24,14 L24,20 M72,14 L72,20", w=0.7, halo=False)
    d.shape(circle(24, 21.5, 1.6), w=0.9)
    d.shape(circle(72, 21.5, 1.6), w=0.9)
    # The pit: a low board palisade round a dirt floor, seen from the stands.
    rim = ellipse(48, 58, 40, 16)
    d.shape(rim, w=1.6)
    inner = "M8,58 C8,48 26,42 48,42 C70,42 88,48 88,58 C88,52 70,49 48,49 C26,49 8,52 8,58 Z"
    d.hatch(inner, angle=80, pitch=1.8)
    d.line("M8,58 C8,52 26,49 48,49 C70,49 88,52 88,58", w=0.9, halo=False)
    wall = "M8,58 C8,67 26,74 48,74 C70,74 88,67 88,58 L88,66 C88,75 70,82 48,82 C26,82 8,75 8,66 Z"
    d.shape(wall, w=1.6)
    d.hatch(wall, angle=60, pitch=1.9, cross=True)
    for x in (14, 22, 30, 39, 48, 57, 66, 74, 82):
        yt = 58 + 16 * math.sqrt(max(0, 1 - ((x - 48) / 40) ** 2))
        d.line(f"M{x},{yt:.1f} L{x},{yt + 8:.1f}", w=1.0, halo=False)
    # The iron stake and the wolf crouched by it on her chain.
    d.line("M56,50 L56,62", w=2.0)
    t = traced("she-wolf")
    k, ox, oy = 0.36, 20, 41
    for p in t["outline"]:
        d.shape(warp(p, lambda x, y: (ox + x * k, oy + y * k)), w=1.4)
    d.line("M56,60 C52,63 48,63 46,59", w=0.8, halo=False)
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


# 7. The Hacienda de San Diego: the house front with its three arches and the initials ------------------
def san_diego() -> Drawing:
    d = Drawing("san-diego-gate")
    body = poly((6, 84), (6, 44), (90, 44), (90, 84))
    d.shape(body)
    # Parapet with the pierced terracotta band; a raised centre panel over the arches.
    d.shape(poly((6, 44), (6, 38), (28, 38), (28, 34), (68, 34), (68, 38), (90, 38), (90, 44)))
    d.line(" ".join(f"M{x},40.8 l1.6,0" for x in range(9, 88, 3)), w=0.9, halo=False)
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
    # Tall shuttered windows in the wings; quoins at the corners.
    for x in (11, 19, 75, 83):
        w = poly((x - 2.5, 74), (x - 2.5, 52), (x + 2.5, 52), (x + 2.5, 74))
        d.shape(w, w=1.1)
        d.hatch(w, angle=0, pitch=1.6)
    for y in range(46, 84, 6):
        d.line(f"M6,{y} l3,0 l0,3 l-3,0 M90,{y} l-3,0 l0,3 l3,0", w=0.8, halo=False)
    d.edge_shade(body, dx=-3, dy=-2.5)
    d.ground(2, 94, 86, ticks=8, seed=4)
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


# 10. The red Waco ---------------------------------------------------------------------------------------
def red_plane() -> Drawing:
    d = Drawing("red-plane")
    # The circling flight path, dotted.
    d.line("M84,70 C96,52 80,34 56,32 C40,31 22,36 12,46", w=0.8, halo=False)
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
    # The trees it drops among.
    for x, h in ((70, 10), (78, 13), (86, 9)):
        d.shape(f"M{x - 4},{88} C{x - 6},{88 - h} {x - 2},{88 - h - 4} {x},{88 - h - 3} C{x + 3},{88 - h - 4} {x + 6},{88 - h} {x + 4},{88} Z", w=1.2)
        d.hatch(f"M{x},{88 - h - 3} C{x + 3},{88 - h - 4} {x + 6},{88 - h} {x + 4},{88} L{x},{88} Z", pitch=1.8)
    d.ground(6, 94, 89, ticks=5, seed=2)
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


# 12. The crippled dog in the doorway of the ruin -------------------------------------------------------
def crippled_dog() -> Drawing:
    d = Drawing("crippled-dog")
    # The back wall of the ruined adobe, roofless, with its open door onto the rain and the road.
    wall = "M4,70 L4,26 C10,22 16,28 24,24 C32,20 38,26 46,23 C56,20 62,27 72,24 C80,22 86,27 92,25 L92,70 Z"
    d.shape(wall)
    door = poly((52, 70), (52, 36), (68, 36), (68, 70))
    d.shape(door, w=1.4)
    d.hatch(door, angle=-70, pitch=2.2, w=0.6)
    d.line("M50,36 L70,36", w=1.6)
    d.line("M12,38 l3,0.5 M26,52 l3,0 M80,44 l3,0.4 M36,34 l2.6,0 M84,60 l2.6,0", w=0.7, halo=False)
    d.edge_shade(wall, dx=-3, dy=-2)
    # Floor line, and the old dog lying in the corner, its head turned and askew (traced).
    d.line("M4,70 L92,70", w=1.2)
    # The old dog: the traced wolf outline, made smaller and bent so that the hindquarters sink and the
    # head hangs low and askew, as the book describes him (the dog photographs found were all lying down).
    t = traced("she-wolf")
    k = 0.62
    def bend(x, y):
        x2, y2 = 12 + x * k, 34 + y * k
        if x < 40:   # hindquarters: drop and shorten
            y2 += (40 - x) * 0.20
        if x > 70:   # head: down and turned
            y2 += (x - 70) * 0.30
        return x2, y2
    for p in t["outline"]:
        dog = warp(p, bend)
        d.shape(dog)
        d.edge_shade(dog, dx=-2.5, dy=-3)
    d.line("M44,72 l2,-1 M48,73 l2,-1", w=0.7, halo=False)
    d.line("M10,86 L30,86 M74,86 L90,86", w=1.0)
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
    "she-wolf": she_wolf, "steel-trap": steel_trap, "obelisk": obelisk, "hacienda-pit": hacienda_pit,
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
