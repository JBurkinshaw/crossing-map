"""Shared drawing helpers for the vignette subjects (art/vignettes/make_vignettes.py and subjects_*.py): paths for
polygons, ellipses and circles on the 96 x 96 grid, the traced outlines in traced/, a warp for bending a traced
shape, and grass tufts.
"""

import json
from pathlib import Path

import svgelements as se

from art.vignettes.ink import Drawing

TRACED = Path(__file__).parent / "traced"


def poly(*pts, close=True) -> str:
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + (" Z" if close else "")


def ellipse(cx, cy, rx, ry) -> str:
    return f"M{cx - rx},{cy} a{rx},{ry} 0 1,0 {2 * rx},0 a{rx},{ry} 0 1,0 {-2 * rx},0 Z"


def circle(cx, cy, r) -> str:
    return ellipse(cx, cy, r, r)


def traced(name: str) -> dict:
    return json.loads((TRACED / f"{name}.json").read_text())


def warp(d: str, fn) -> str:
    """Move every point of a path through fn(x, y) -> (x, y) (used to bend a traced animal)."""
    p = se.Path(d)
    out = []
    for seg in p:
        if isinstance(seg, se.Move):
            out.append("M{:.1f},{:.1f}".format(*fn(*seg.end)))
        elif isinstance(seg, se.Close):
            out.append("Z")
        elif isinstance(seg, se.CubicBezier):
            a, b, c = fn(*seg.control1), fn(*seg.control2), fn(*seg.end)
            out.append("C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}".format(*a, *b, *c))
        elif isinstance(seg, se.Line):
            out.append("L{:.1f},{:.1f}".format(*fn(*seg.end)))
        elif isinstance(seg, se.Arc):  # circle() and ellipse() are arcs: bend them as cubics, or they vanish
            for c in seg.as_cubic_curves():
                a, b, e = fn(*c.control1), fn(*c.control2), fn(*c.end)
                out.append("C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}".format(*a, *b, *e))
    return " ".join(out)


def grass(d: Drawing, pts, h=4.0):
    s = []
    for x, y in pts:
        s.append(f"M{x - 1.6:.1f},{y:.1f} l-1,{-h * .7:.1f} M{x:.1f},{y:.1f} l0,{-h:.1f} M{x + 1.6:.1f},{y:.1f} l1.2,{-h * .75:.1f}")
    d.line(" ".join(s), w=0.9)


# 1. The she-wolf ---------------------------------------------------------------------------------------
