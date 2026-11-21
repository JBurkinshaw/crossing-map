"""Vignettes of the fifth round: Billy's ride with "the girl" across the Babícora country (J5, 3-12), his
return to the doctor's gate at Casas Grandes (3-14), Boyd among the workers' offerings at San Diego (3-09), and the
corrido of the güerito as the girl cracking pecans sings and tells it (4-05). Loaded by
art/vignettes/make_vignettes.py.

Each is checked against the episode that first shows it. The riders and horses are the traced Muybridge plate
(rider-annie-g, public domain) through the Parts III and IV helpers, and the dog is the traced she-wolf outline,
made small and curled. Everything else is drawn by hand from the book's description, or after the reference its
seed `credit` names. The two corrido scenes sit inside a printed broadside's border, to say that they are a song's
telling and not the book's own scene. Light from the north-west, as everywhere: shade on each shape's south-east
side.
"""

from art import PAPER
from art.vignettes.ink import Drawing
from art.vignettes.shapes import circle, ellipse, grass, poly, traced, warp
from art.vignettes.subjects_parts_1_2 import fit, juniper
from art.vignettes.subjects_parts_3_4 import blob, rider
from art.vignettes.subjects_round3 import chevrons, figure, horse
from art.vignettes.subjects_round4 import round_


def broadside(d: Drawing):
    """The double rule round a printed corrido sheet, with a small fleuron at each corner."""
    d.shape(poly((3, 3), (93, 3), (93, 93), (3, 93)), w=1.6, fill=False)
    d.line(poly((6, 6), (90, 6), (90, 90), (6, 90)), w=0.7, halo=False)
    d.dots([(3, 3), (93, 3), (3, 93), (93, 93)], r=1.4)


def person(d: Drawing, x: float, y: float, h: float, flip: bool = False, hat: bool = True):
    """Round 3's standing `figure`, with its head drawn as a plain circle (warp drops the arcs of the helper's
    own head), then the hat over it."""
    p = figure(d, x, y, h, flip=flip, hat=False)
    k = h / 24
    d.shape(circle(x, y - 21 * k, 2.2 * k), w=1.0)
    if hat:
        hat_d = p("M-4.6,-22 L4.6,-22 L2.4,-23 C2.4,-26.4 -2.4,-26.4 -2.4,-23 Z")
        d.shape(hat_d, w=0.9)
        d.hatch(hat_d, angle=0, pitch=0.9)
    return p


# 1. A worker standing on the truck bed, fist raised, as the truck pulls away (3-12) ---------------------
def hay_justicia() -> Drawing:
    d = Drawing("hay-justicia")
    # The road running off south into the evening, and the long shadows across the country.
    d.line("M2,70 C20,69 40,68 94,66", w=0.8)
    d.line("M8,76 l10,0 M30,74 l8,0", w=0.6, halo=False)
    # The dust the truck raises as it goes.
    d.line(blob(82, 58, 13, 9, 9, seed=750, depth=0.22), w=0.7, halo=False)
    d.dots([(92, 46), (70, 48), (94, 56), (88, 44)], r=0.6)
    # The flatbed seen from behind, going away: stake sides, the tailgate, twin rear tyres.
    bed = poly((50, 62), (50, 42), (86, 42), (86, 62))
    d.shape(bed, w=1.6)
    d.line("M50,48 L86,48 M50,54 L86,54", w=0.6, halo=False)
    d.line("M56,42 L56,62 M68,42 L68,62 M80,42 L80,62", w=0.9, halo=False)
    d.edge_shade(bed, dx=-2.5, dy=-1.5)
    d.shape(poly((48, 62), (88, 62), (88, 65), (48, 65)), w=1.2)
    for x in (51, 79):
        tyre = poly((x, 64), (x + 6, 64), (x + 6, 72), (x, 72))
        d.shape(tyre, w=1.3)
        d.hatch(tyre, angle=0, pitch=1.0)
    cab = "M58,42 L58,33 C58,31.6 59,31 60.4,31 L75.6,31 C77,31 78,31.6 78,33 L78,42 Z"
    d.shape(cab, w=1.3)
    # The workers seated along the bed, hats over the stake rail.
    for x in (55, 62, 76, 83):
        d.shape(circle(x, 38.6, 2.3), w=1.0)
        hat = f"M{x - 4},37 L{x + 4},37 L{x + 2},36 C{x + 2},33 {x - 2},33 {x - 2},36 Z"
        d.shape(hat, w=0.9)
        d.hatch(hat, angle=0, pitch=0.9)
    # The one who stands, a hand on his companion's shoulder and his fist up.
    man = "M66,42 L66.6,26 C67,23.6 73,23.6 73.4,26 L74,42 Z"
    d.shape(man, w=1.3)
    d.edge_shade(man, dx=-1.6, dy=0)
    d.shape(circle(70, 20.6, 2.8), w=1.1)
    d.line("M72.6,25.6 L76,16 L77,9.4", w=1.6)
    d.shape(circle(77.2, 8.2, 1.8), w=1.1)
    d.line("M67,26 L63,30 L62,35", w=1.4)
    # Billy on the roadside, watching him go.
    rider(d, 22, 88, 0.46, hat="cowboy")
    d.ground(2, 44, 89, ticks=4, seed=751)
    return d


# 2. Billy riding across La Pinta among the junipers, the moon risen (3-12) -----------------------------
def la_pinta_moon() -> Drawing:
    d = Drawing("la-pinta-moon")
    moon = circle(76, 15, 7)
    d.shape(moon, w=1.3)
    d.dots([(12, 8), (26, 16), (40, 6), (54, 14), (92, 30), (8, 26)], r=0.6)
    # The high plain and its scattered junipers.
    d.line("M2,58 C30,56 60,57 94,55", w=0.8)
    juniper(d, 12, 70, 26, seed=1)
    juniper(d, 84, 74, 30, seed=2)
    juniper(d, 34, 58, 10, seed=3)
    juniper(d, 66, 57, 9, seed=4)
    # Billy riding south across it, the shotgun held upright.

    def gun(t):
        d.line(t("M55,40 L60,8"), w=1.3)
    rider(d, 52, 88, 0.48, hat="cowboy", extra=gun)
    d.ground(2, 94, 89, ticks=6, seed=752)
    return d


# 4. Billy crouching at the black lake's edge, the dead she-wolf faint among the drowned stars (3-12) --
def stars_in_the_lake() -> Drawing:
    d = Drawing("stars-in-the-lake")
    # The night sky with its stars, and the far shore.
    for x, y, r in ((14, 10, 2.4), (40, 6, 1.8), (66, 12, 2.6), (86, 6, 1.8), (28, 24, 1.6), (78, 26, 1.6)):
        d.line(f"M{x - r},{y} L{x + r},{y} M{x},{y - r} L{x},{y + r}", w=0.8)
    d.dots([(52, 20), (8, 30), (92, 18), (58, 30)], r=0.6)
    d.line("M2,40 C20,38 40,39 60,38 C76,37.6 86,39 94,38", w=1.0)
    # The lake: black and still, and the same stars down in it.
    lake = "M2,42 C30,41 60,41 94,41 L94,74 C70,75 40,76 2,75 Z"
    d.hatch(lake, angle=0, pitch=1.0, w=0.9)
    d.hatch(lake, angle=90, pitch=1.4, w=0.6)
    # Among them, faint, the she-wolf dead in the mountains, drawn upside down in pale lines like the stars.
    k, ox, oy = 0.4, 50, 75
    for p in traced("she-wolf")["outline"]:
        d.line(warp(p, lambda x, y: (ox + x * k, oy - y * k)), w=1.0, color=PAPER, halo=False)
    for x, y, r in ((14, 70, 2.4), (40, 74, 1.8), (28, 56, 1.6), (8, 50, 1.2), (92, 70, 1.2), (60, 46, 1.2),
                    (84, 46, 1.4)):
        d.line(f"M{x - r - 0.6},{y} L{x + r + 0.6},{y} M{x},{y - r - 0.6} L{x},{y + r + 0.6}", w=1.3, color=PAPER,
               halo=False)
    # Billy crouched at the edge with the serape round his shoulders, hatless.
    cloak = "M28,88 C28,80 30,74 33,71 C36,69.6 44,69.6 47,71 C50,74 52,80 52,88 Z"
    d.shape(cloak, w=1.6)
    d.line("M33,78 L50,78 M32,82 L51,82", w=0.7, halo=False)
    d.edge_shade(cloak, dx=-2.4, dy=-1.6)
    d.shape(circle(40, 65, 4.2), w=1.4)
    d.hatch("M35.8,64.4 C35.8,59.6 44.2,59.6 44.2,64.4 C42,62.6 38,62.6 35.8,64.4 Z", angle=0, pitch=0.8)
    # The sedge he crouches in.
    d.line("M2,88 C30,87 60,87 94,86", w=0.9)
    d.line(" ".join(f"M{x},{88 - (x % 3)} l{-1 + x % 3},-{7 + x % 5} M{x + 2},{88 - (x % 2)} l{1 - x % 2},-{9 + x % 4}"
                    for x in (4, 10, 16, 22, 58, 64, 70, 76, 82, 88)), w=0.9)
    return d


# 5. The old woman's tamale cart at Las Varas (3-12) ----------------------------------------------------
def tamale_cart() -> Drawing:
    d = Drawing("tamale-cart")
    # The street, and the plank wall of a store behind.
    d.line("M2,42 L94,42", w=0.8)
    d.line(" ".join(f"M{x0},{y} L{x0 + 12},{y}" for y, x0 in ((30, 4), (36, 12), (30, 74), (36, 80), (24, 82))), w=0.5,
           halo=False)
    # Charcoal smoke going up from the lid.
    d.line("M44,22 C40,18 46,14 42,8 M50,22 C54,16 48,12 52,6", w=0.7, halo=False)
    # A steel oil drum set upright in a frame of wooden slats, its lid and the hoops round it.
    drum = "M32,70 L32,30 C32,26 60,26 60,30 L60,70 C60,74 32,74 32,70 Z"
    d.shape(drum, w=1.6)
    d.shape(ellipse(46, 30, 14, 3.4), w=1.1)
    d.line("M32,44 C32,47 60,47 60,44 M32,58 C32,61 60,61 60,58", w=1.0, halo=False)
    d.edge_shade(drum, dx=-3, dy=0)
    d.shape(poly((26, 76), (26, 24), (29, 24), (29, 76)), w=1.2)
    d.shape(poly((63, 76), (63, 24), (66, 24), (66, 76)), w=1.2)
    d.shape(poly((24, 76), (68, 76), (68, 80), (24, 80)), w=1.2)
    d.line("M66,30 L76,26", w=1.6)
    # Two cast-iron wheels off an ore cart: small, flanged, spoked.
    for cx in (32, 60):
        d.shape(circle(cx, 84, 6.4), w=1.8)
        d.shape(circle(cx, 84, 4.4), w=0.8, fill=False)
        d.line(f"M{cx - 4},84 L{cx + 4},84 M{cx},80 L{cx},88", w=1.0, halo=False)
        d.dots([(cx, 84)], r=1.1)
    # The old woman selling, her rebozo over her head.
    p = person(d, 82, 90, 34, flip=True, hat=False)
    shawl = p("M-3.6,-20 C-4,-25 4,-25 3.6,-20 L5,-12 L-5,-12 Z")
    d.shape(shawl, w=1.1)
    d.hatch(shawl, angle=60, pitch=1.2)
    d.shape(circle(82, 90 - 21 * 34 / 24, 1.8 * 34 / 24), w=0.9)
    d.ground(2, 94, 91, ticks=6, seed=753)
    return d


# 6. Billy at the doctor's gate in the rain, past midnight, holding the horse (3-14) --------------------
def doctors_gate_in_rain() -> Drawing:
    d = Drawing("doctors-gate-in-rain")
    # The adobe wall of the house and its zaguán: tall double doors under a lintel, one leaf open on lamplight.
    wall = poly((2, 84), (2, 20), (70, 20), (70, 84))
    d.shape(wall)
    d.line("M2,20 L70,20 M2,24 L70,24", w=1.0)
    d.edge_shade(wall, dx=-3, dy=-2)
    gate = poly((16, 84), (16, 36), (52, 36), (52, 84))
    d.shape(gate, w=1.6)
    d.line("M14,34 L54,34", w=1.8)
    leaf = poly((16, 84), (16, 36), (34, 36), (34, 84))
    d.hatch(leaf, angle=45, pitch=1.4, cross=True)
    d.line("M20,44 l10,0 M20,60 l10,0 M20,76 l10,0", w=0.6, halo=False)
    d.hatch(poly((34, 84), (34, 36), (38, 38), (38, 84)), angle=90, pitch=1.0)
    d.shape(poly((38, 84), (38, 38), (48, 36), (48, 84)), w=1.2, fill=False)
    d.hatch(poly((48, 84), (48, 36), (52, 36), (52, 84)), angle=45, pitch=1.4, cross=True)
    # The lamp lit and held out in the open leaf, its glow.
    d.shape(poly((41, 56), (45, 56), (45.6, 62), (40.4, 62)), w=1.1)
    d.line("M43,56 L43,52", w=0.9)
    d.line("M35,59 l-3,0 M51,59 l3,0 M43,66 l0,3 M37.6,53.6 l-2,-2 M48.4,53.6 l2,-2", w=0.7, halo=False)
    # Billy waiting with the wet horse, its head hung low.
    horse(d, 76, 90, 0.44, flip=True, graze=0.6)
    p = person(d, 54, 90, 34)
    d.line(p("M2.6,-15 L6,-12 L8,-12"), w=1.0)
    d.line("M59,78 C62,81 64,82 61,80", w=0.7, halo=False)
    d.line("M2,90 L94,90", w=1.0)
    d.line("M10,93 l8,0 M40,93.4 l10,0 M72,93 l8,0", w=0.6, halo=False)
    # The cold rain, slanting down over all of it.
    d.line(" ".join(f"M{x},{y} l-2,6" for x, y in ((6, 4), (18, 8), (30, 2), (42, 6), (56, 4), (68, 8), (80, 2), (90, 8),
                                                   (76, 18), (86, 26), (92, 40), (60, 12), (12, 12), (36, 12),
                                                   (80, 48), (90, 56), (74, 34), (88, 66), (62, 54), (8, 30),
                                                   (60, 28), (26, 26))),
           w=0.6, halo=False)
    return d


# 7. Boyd on his pallet among the workers' gifts, under the candle in the niche (3-09) -----------------
def boyd_among_offerings() -> Drawing:
    d = Drawing("boyd-among-offerings")
    # The dark room: one candle's light round the niche, the rest in shadow.
    room = "M0,0 L96,0 L96,64 L0,64 Z " + round_(48, 26, 26, 22)
    d.hatch(room, angle=45, pitch=2.2)
    # The wall niche, the wooden Madonna in it and the candle in its glass at her feet.
    niche = "M38,40 L38,20 C38,12 58,12 58,20 L58,40 Z"
    d.shape(niche, w=1.5)
    d.edge_shade(niche, dx=3, dy=2.4)
    d.shape("M44,38 C44,30 46,24 48,22 C50,24 52,30 52,38 Z", w=1.1)
    d.shape(circle(48, 20, 2.0), w=1.0)
    d.shape(poly((45.6, 40), (45.6, 34), (50.4, 34), (50.4, 40)), w=0.9)
    d.line("M48,34 L48,31.4", w=0.8)
    d.line("M38,40 L58,40", w=1.4)
    # Boyd lying on the pallet under a blanket, the dog curled at his feet.
    d.line("M0,64 L96,64", w=1.0)
    pallet = poly((6, 72), (6, 66), (90, 66), (90, 72))
    d.shape(pallet, w=1.4)
    blanket = "M18,66 C20,58 30,56 44,57 C60,56 72,58 80,62 L82,66 Z"
    d.shape(blanket, w=1.3)
    d.hatch(blanket, angle=60, pitch=1.6)
    d.shape(ellipse(13, 62.6, 5.4, 3.2), w=1.1)
    d.shape(circle(15, 58.6, 3.4), w=1.2)
    t = traced("she-wolf")
    lie = fit(0.26, 64, 42)

    def curl(x, y):
        return lie(x, 50 + (y - 50) * 0.4 if y > 50 else y + 6)
    for p in t["outline"]:
        dog = warp(p, curl)
        d.shape(dog, w=1.1)
    # The gifts on the floor before him: ollas, a basket, bottles, flowers in a jar, a little box.
    d.shape("M8,90 C4,86 4,80 8,78 L8,76 L14,76 L14,78 C18,80 18,86 14,90 Z", w=1.3)
    d.edge_shade("M8,90 C4,86 4,80 8,78 L8,76 L14,76 L14,78 C18,80 18,86 14,90 Z", dx=-2, dy=-1)
    basket = "M22,90 L20,80 L36,80 L34,90 Z"
    d.shape(basket, w=1.2)
    d.hatch(basket, angle=45, pitch=1.4, cross=True)
    d.line("M22,80 C22,72 34,72 34,80", w=1.0)
    for x in (42, 47):
        d.shape(f"M{x - 2},90 L{x - 2},82 L{x - 0.8},79 L{x - 0.8},76 L{x + 0.8},76 L{x + 0.8},79 L{x + 2},82 "
                f"L{x + 2},90 Z", w=1.0)
    d.shape("M54,90 L54,82 L62,82 L62,90 Z", w=1.2)
    d.line("M56,82 L53,74 M58,82 L58,72 M60,82 L64,74", w=0.8)
    d.dots([(53, 73.4), (58, 71.4), (64, 73.4)], r=1.2)
    box = poly((68, 90), (68, 83), (80, 83), (80, 90))
    d.shape(box, w=1.2)
    d.hatch(box, angle=0, pitch=1.2)
    d.shape("M84,90 C82,86 82,82 86,80 C90,80 92,84 90,90 Z", w=1.2)
    d.line("M2,91 L94,91", w=1.0)
    return d


# 8. The corrido: six armed riders come to Bachíniva (4-05) ----------------------------------------------
def six_riders_bachiniva() -> Drawing:
    d = Drawing("six-riders-bachiniva")
    broadside(d)
    # The sheet's heading, set as ruled lines: a song, not the book's own scene.
    d.line("M12,11 L48,11 M12,15 L40,15", w=1.4, halo=False)
    # The town's church and low houses on the skyline they ride towards.
    d.shape(poly((66, 40), (66, 22), (70, 18), (74, 22), (74, 40)), w=1.2)
    d.line("M70,18 L70,12 M68,14.6 L72,14.6", w=0.9)
    d.shape(poly((74, 40), (74, 30), (86, 30), (86, 40)), w=1.1)
    d.shape(poly((54, 40), (54, 32), (66, 32), (66, 40)), w=1.1)
    d.line("M8,40 L88,40", w=0.8)

    def rifle(t):
        d.line(t("M57,36 L68,10"), w=1.1)
    # Six riders in two ranks, rifles up.
    for x, y, k in ((22, 62, 0.22), (44, 60, 0.22), (66, 62, 0.22), (16, 86, 0.27), (42, 84, 0.27), (70, 86, 0.27)):
        rider(d, x, y, k, hat="cowboy", extra=rifle)
    return d


# 9. The corrido's ending: the people carry the lovers to a secret grave (4-05) -------------------------
def lovers_secret_grave() -> Drawing:
    d = Drawing("lovers-secret-grave")
    broadside(d)
    d.line("M12,11 L48,11 M12,15 L40,15", w=1.4, halo=False)
    # The little birds flying up and away.
    chevrons(d, [(60, 14, 0.9), (70, 20, 0.8), (78, 12, 0.8), (50, 22, 0.7), (84, 24, 0.7), (66, 28, 0.6)])
    # The hills, and the fresh-dug grave waiting under a lone tree.
    d.line("M8,50 C24,44 36,44 48,48 C60,44 76,42 88,46", w=0.9)
    d.line("M80,62 C80,54 79,50 80,44 M80,52 L86,46", w=1.2)
    crown = blob(82, 40, 8, 6, 9, seed=754, depth=0.25)
    d.shape(crown, w=1.2)
    d.edge_shade(crown, dx=-2, dy=-2)
    mound = "M70,66 C74,61 84,61 88,66 Z"
    d.shape(mound, w=1.2)
    d.hatch(mound, angle=45, pitch=1.2)
    # The bier carried on the shoulders of two bearers, the two lovers wrapped together in one shroud on it.
    for x in (12, 66):
        person(d, x, 89, 36)
    d.line("M2,64.6 L72,64.6", w=1.8)
    body = "M22,62 C20,58 22,54 26,53 L52,52 C56,52 58,55 57,59 L56,62 Z"
    d.shape(body, w=1.5)
    d.shape(circle(25.6, 52.6, 3.2), w=1.2)
    d.shape(circle(26.6, 58, 3.0), w=1.2)
    d.line("M34,52.4 L34,62 M44,52 L44,62 M52,52.4 L52,62", w=0.8, halo=False)
    d.edge_shade(body, dx=-1.8, dy=-1.8)
    for x in (12, 66):
        d.line(f"M{x + 2.6},72 L{x + 5.4},65", w=1.1)
    d.ground(8, 88, 89, ticks=5, seed=755)
    grass(d, [(36, 88), (80, 87)], h=3)
    return d


SUBJECTS = {
    "hay-justicia": hay_justicia,
    "la-pinta-moon": la_pinta_moon,
    "stars-in-the-lake": stars_in_the_lake,
    "tamale-cart": tamale_cart,
    "doctors-gate-in-rain": doctors_gate_in_rain,
    "boyd-among-offerings": boyd_among_offerings,
    "six-riders-bachiniva": six_riders_bachiniva,
    "lovers-secret-grave": lovers_secret_grave,
}
