"""Vignettes of the sixth round, group a: the dead coyote Billy carries home from the double set (Part I, 1-06),
in place of the steel trap, and the small helpers the round's redraws in make_vignettes.py share: the men in hats
on the cockpit's bleachers and the stumps of the cut-over sierra. Loaded by art/vignettes/make_vignettes.py.

Each is checked against the passage that shows it and drawn only from what the text gives. The rider and horse
are the traced Muybridge plate (rider-annie-g, public domain) through the Parts III and IV helpers. The coyote,
the stumps and the onlookers are drawn by hand from the book. Light from the north-west, as everywhere: shade on
each shape's south-east side.
"""

from art.vignettes.ink import Drawing
from art.vignettes.shapes import grass, poly
from art.vignettes.subjects_parts_3_4 import place, rider
from art.vignettes.subjects_round4 import round_
from art.vignettes.subjects_round5_e import hat, person


def onlooker(d: Drawing, x: float, y: float, s: float = 1.0, dark: bool = False, behind: bool = False):
    """A man seen from in front or behind, head and shoulders only, in a broad hat: one of a crowd. (x, y) is the
    middle of his shoulders' foot, s the scale (about 10 units tall at s = 1). `behind` darkens the back of the
    head."""
    body = place("M-4.4,0 L-4,-4.6 C-3.4,-6 3.4,-6 4,-4.6 L4.4,0 Z", x, y, s)
    d.shape(body, w=1.0)
    if dark:
        d.hatch(body, angle=45, pitch=1.1)
    head = place(round_(0, -7.6, 2.0), x, y, s)
    d.shape(head, w=0.9)
    if behind:
        d.hatch(head, angle=80, pitch=0.8)
    brim = place("M-4.6,-8.6 C-2,-9.6 2,-9.6 4.6,-8.6 C2,-7.8 -2,-7.8 -4.6,-8.6 Z", x, y, s)
    crown = place("M-2.2,-9 C-2.2,-11.8 -1.2,-12.4 0,-12.4 C1.2,-12.4 2.2,-11.8 2.2,-9 Z", x, y, s)
    d.shape(brim, w=0.9)
    d.shape(crown, w=0.9)
    d.hatch(crown, angle=0, pitch=0.8)


def stump(d: Drawing, x: float, base: float, w: float, h: float, felled: bool = False):
    """A sawn stump, flat-topped with a ring on its cut face and roots flaring into the ground; `felled` lays its
    trunk on the slope beside it."""
    r = w / 2
    top = base - h
    body = (f"M{x - r - w * 0.35:.1f},{base:.1f} C{x - r:.1f},{base - h * 0.2:.1f} {x - r:.1f},{top + 1:.1f} "
            f"{x - r:.1f},{top:.1f} L{x + r:.1f},{top:.1f} C{x + r:.1f},{top + 1:.1f} {x + r:.1f},{base - h * 0.2:.1f} "
            f"{x + r + w * 0.35:.1f},{base:.1f} Z")
    d.shape(body, w=1.1)
    d.hatch(poly((x + r * 0.2, top + 0.8), (x + r + w * 0.4, top + 0.8), (x + r + w * 0.4, base), (x + r * 0.2, base)),
            angle=80, pitch=1.0)
    face = round_(x, top, r, r * 0.38)
    d.shape(face, w=1.0)
    if w > 4.5:
        d.line(round_(x, top, r * 0.45, r * 0.17), w=0.5, halo=False)
    if felled:
        log = poly((x + r + 1, base - 0.4), (x + r + h * 2.6, base - 1.6), (x + r + h * 2.6, base - 1.6 - w * 0.7),
                   (x + r + 1, base - 0.4 - w * 0.7))
        d.shape(log, w=1.0)
        d.hatch(log, angle=0, pitch=1.1)


def handler(d: Drawing, x: float, y: float, h: float = 20.0):
    """A man facing west, braced back on a leash: feet at (x, y), h tall. Returns his hands' point."""
    k = h / 24

    def q(u: float, v: float) -> tuple[float, float]:
        return x + u * k, y + v * k
    person(d, q(3.4, -20.4), q(2.2, -17), q(0.6, -9), back=[[q(0.6, -9), q(3.6, -4.6), q(4, 0)]],
           front=[[q(0.6, -9), q(-3, -4.4), q(-5.4, 0)], [q(2, -16), q(-2, -13), q(-5, -12.4)]], r=2.2 * k,
           width=5 * k, w=1.3)
    hat(d, *q(3.6, -22.4), s=0.75 * h / 20)
    return q(-5, -12.4)


# 1. Billy riding home with the dead coyote tied on behind the cantle (1-06) ---------------------------
def coyote_in_the_set() -> Drawing:
    d = Drawing("coyote-in-the-set")
    # The pass behind, the snow gone save in the north-facing folds: the shade hatched round pale patches.
    ridge = "M2,30 L10,24 L16,27 L26,12 L34,20 L40,16 L50,26 L58,18 L66,24 L74,14 L84,22 L94,20"
    d.line(ridge, w=1.1)
    for shade in ("M26,12 L34,20 L32,26 L24,24 Z", "M58,18 L66,24 L64,30 L56,28 Z", "M74,14 L84,22 L82,28 L72,26 Z"):
        d.hatch(shade, angle=70, pitch=1.6, w=0.6)
    for snow in ("M27,15 L31,19 L28,21 Z", "M75,17 L80,21 L76,22 Z"):
        d.shape(snow, w=0.6)

    def coyote(t):
        # Tied on lengthwise behind the cantle: the limp body along the horse's croup, its head and forelegs hanging
        # down behind the haunch, the brush hanging by the saddle skirt.
        body = t("M42,41 C40,33 30,29.6 20,30.6 C12,31.4 7,34 5,39 L11,41.6 C20,39.4 32,39.4 42,41 Z")
        d.shape(body, w=1.5)
        d.hatch(body, angle=60, pitch=1.2)
        head = t("M5,37 C2,41 1,46 1.6,51 L0.6,58 L4,58.6 L6,52 C7.6,47 9.4,43 10.6,40 Z")
        d.shape(t("M2.4,46 L-3,42.4 L1.4,50.6 Z"), w=1.1)
        d.shape(head, w=1.4)
        d.hatch(t("M5,37 C2,41 1,46 1.6,51 L3.4,50 C4,46 6,42 8,39.4 Z"), angle=60, pitch=1.0)
        d.line(t("M3.6,57 L1.4,61.4 M3,55.6 L5.6,60.6"), w=1.1)
        d.line(t("M9,41 L8,52 L10,55 M12.4,41 L13.4,51 M36,40.6 L37,50 L35.8,52.6 M39,41 L40.4,49.6"), w=1.2)
        tail = t("M42,39 C45,43 46.4,50 45.4,56 C44.6,58.4 42,58.4 41.6,56 C41,51 41,45 40.4,41 Z")
        d.shape(tail, w=1.2)
        d.hatch(tail, angle=80, pitch=1.0)
        # Where it leaked down the horse's flank.
        d.line(t("M28,42 C27.4,47 27.8,52 27,57"), w=0.7, halo=False)
    rider(d, 52, 90, 0.82, extra=coyote)
    grass(d, [(8, 90), (84, 90)], h=3.4)
    d.ground(2, 94, 91, ticks=7, seed=900)
    return d


SUBJECTS = {"coyote-in-the-set": coyote_in_the_set}
