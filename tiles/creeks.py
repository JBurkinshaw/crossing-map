"""The base map's creek layer: the small streams of both countries, drawn by one rule.

Called by tiles.build_base. Mexico's streams come from INEGI's Red Hidrográfica 1:50,000 (its Strahler order is
ORDER_1), the US side's from USGS NHD High Resolution, with the Strahler order computed from how its lines join
(crossing.hydro.strahler). Each network is clipped to its own side of the border, so the two do not double along it.

A stream is drawn from the zoom its order earns (MIN_ZOOM), chosen so that a view shows about the same length of
stream per screen at every zoom: about 1 km per km2 of ground at zoom 12, halving with each zoom out. INEGI's
first-order channels alone come to 1-2 km per km2, so they are left out. Though NHD is digitised at 1:24,000, its
network in the bootheel and southern Arizona is sparser than INEGI's in Sonora and Chihuahua: about half the
length at each order. So NHD_SHIFT is added to NHD's orders before the rule is applied, which brings the two
countries to the same density at every zoom (measured in review/stage-8/streams/README.md).
"""

import json
import unicodedata
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import mapping

from crossing.hydro import Hydro, nodes
from crossing.vector import segments
from tiles import BASE_ZOOMS

# Added to NHD's computed order so that it compares with INEGI's (see the module docstring).
NHD_SHIFT = 1
# The zoom from which a stream of each order is drawn; the style repeats this table. Higher orders from FIRST_ZOOM;
# order 1 is not drawn. Order 2 is in the zoom 11 tiles but drawn only from zoom 12 (MapLibre draws zoom 12 from
# the zoom 11 tiles).
MIN_ZOOM = {2: 12, 3: 11, 4: 10, 5: 9, 6: 8}
FIRST_ZOOM = 7
# Order 2 streams, drawn only at zoom 12, would double the archive across the whole box, so they are kept only in
# the country the journeys ride through (west, south, east, north): from the Sonora river towns and the bootheel
# to the Babícora, Silver City and Lordsburg.
FINEST_ORDER_BOX = (-110.75, 28.25, -106.25, 33.25)
# Lines are simplified to within this (degrees, about 30 m, a pixel at zoom 12) before tiling, which keeps the
# zoom 11 tiles, where nearly all the creeks are, small.
SIMPLIFY = 0.0003
# An INEGI place name for a stream (its toponym layer, one point per name) is given to the nearest stream within
# this distance (degrees, about 300 m), and then along that stream, upstream and down, while its order holds.
NAME_REACH = 0.003
# INEGI's generic terms for a stream; the toponym layer also names springs, dams and lakes.
STREAM_TERMS = {"ARROYO", "RÍO", "CAÑADA", "BARRANCA", "CAÑÓN"}
# Lower-case words inside a Spanish name.
SMALL_WORDS = {"de", "del", "la", "las", "el", "los", "y"}


def min_zoom(order: int) -> int | None:
    """The zoom a stream of this order is drawn from, or None if it is not drawn."""
    if order < min(MIN_ZOOM):
        return None
    return MIN_ZOOM.get(order, FIRST_ZOOM)


def title(name: str) -> str:
    """INEGI's capitals as a name: 'ARROYO DE LA CORÚA' becomes 'Arroyo de la Corúa'."""
    words = name.lower().split()
    return " ".join(w if i and w in SMALL_WORDS else w[:1].upper() + w[1:] for i, w in enumerate(words))


def inegi(hydro: Hydro) -> list[tuple[shapely.LineString, int, bool, str]]:
    """INEGI's streams as (line, order, intermittent, name), named from the toponym layer."""
    points = [(xy, title(name)) for xy, term, name in hydro.inegi_toponyms if term in STREAM_TERMS and name]
    lines = hydro.inegi_lines
    names = name_streams([g for g, _, _ in lines], np.array([o for _, o, _ in lines]), points)
    return [(g, o, i, n) for (g, o, i), n in zip(lines, names, strict=True)]


def name_streams(lines: list[shapely.LineString], order: np.ndarray, points: list) -> list[str]:
    """A name for each line: each named point names its nearest line, and the name runs along that stream while its
    order holds (upstream to where two smaller streams meet, downstream to where an equal stream joins). Lines are
    digitised downstream, as rivers.strahler assumes."""
    names = [""] * len(lines)
    if not points:
        return names
    start, end = nodes(lines).T
    leaving, arriving = {}, {}
    for e, (s, t) in enumerate(zip(start, end, strict=True)):
        leaving.setdefault(s, []).append(e)
        arriving.setdefault(t, []).append(e)
    tree = shapely.STRtree(lines)
    xy = shapely.points([p for p, _ in points])
    (hit, nearest), _ = tree.query_nearest(xy, max_distance=NAME_REACH, return_distance=True, all_matches=False)
    for k, e in zip(hit, nearest, strict=True):
        name = points[k][1]
        todo = [e]
        while todo:
            e = todo.pop()
            if names[e]:
                continue
            names[e] = name
            neighbours = leaving.get(end[e], []) + arriving.get(start[e], [])
            todo += [n for n in neighbours if order[n] == order[e] and not names[n]]
    return names


def plain(name: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", name.lower()) if unicodedata.category(c) != "Mn")


def clip(lines: list, area: shapely.Geometry, keep_inside: bool) -> list:
    """The lines' parts inside (or outside) the area, split back into single lines."""
    geoms = np.array([g for g, *_ in lines], dtype=object)
    shapely.prepare(area)
    inside = shapely.contains(area, geoms)
    crossing = ~inside & shapely.intersects(area, geoms)
    out = []
    for k, (g, *rest) in enumerate(lines):
        if crossing[k]:
            part = g.intersection(area) if keep_inside else g.difference(area)
            merged = shapely.line_merge(part) if part.geom_type == "MultiLineString" else part
            out += [(s, *rest) for s in segments(merged)]
        elif inside[k] == keep_inside:
            out.append((g, *rest))
    return out


def write_layer(hydro: Hydro, mexico: shapely.Geometry, tmp: Path, rivers: list[Path]) -> Path:
    """creek.geojson in tmp, for tippecanoe. `rivers` are the river layers already written: a stream named after one
    of them (the Río Bavispe under the Bavispe) is drawn but not labelled, as the river carries the name."""
    us = [(g, o + NHD_SHIFT, i, name) for g, o, i, name in hydro.nhd_lines]
    # The order is read from the whole network; only then are the streams too small to draw dropped.
    streams = [s for s in clip(inegi(hydro), mexico, True) + clip(us, mexico, False) if min_zoom(s[1])]
    finest = shapely.box(*FINEST_ORDER_BOX)
    streams = [s for s in streams if s[1] > min(MIN_ZOOM) or finest.intersects(s[0])]
    river_names = {plain(f["properties"]["name"]) for path in rivers for f in json.loads(path.read_text())["features"]
                   if f["properties"].get("name")}
    return write(streams, river_names, tmp / "creek.geojson")


def write(streams: list, river_names: set[str], out: Path) -> Path:
    """The streams as GeoJSON, the lines of one stream joined end to end: both networks break their streams at
    every confluence, and a line per piece would make the tiles several times larger."""
    groups: dict[tuple, list] = {}
    for g, order, intermittent, name in streams:
        if name and any(r in plain(name) for r in river_names):
            name = ""
        groups.setdefault((order, intermittent, name), []).append(g)
    features = []
    for (order, intermittent, name), lines in groups.items():
        props = {"o": order} | ({"i": 1} if intermittent else {}) | ({"name": name} if name else {})
        merged = shapely.simplify(shapely.line_merge(shapely.multilinestrings(lines)), SIMPLIFY)
        for g in segments(merged):
            features.append({"type": "Feature", "geometry": mapping(g), "properties": props,
                             "tippecanoe": {"minzoom": min(min_zoom(order), BASE_ZOOMS[1])}})
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"creeks: {len(features)} lines, {sum('name' in f['properties'] for f in features)} named")
    return out
