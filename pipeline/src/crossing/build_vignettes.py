"""Build the vignette anchors (design section 10) from pipeline/seeds/vignettes.csv.

Run from the repo root, after crossing.build_story: uv run --project pipeline python -m crossing.build_vignettes
Reads the seed and data/stops.geojson, data/places.geojson and data/journeys.geojson (each vignette's `ref` is a stop
or place id). Writes data/vignettes.geojson: one Point per vignette, on or near the thing it stands for, with the
`side` the map draws the drawing on (site/src/map/relief.ts), so it sits beside its point and never covers it. A seed
row with its own lon and lat stands for a place that is not one of the book's stops or places (the Trinity Site).
A seed row may instead name a journey leg (`leg`, a route-segment id) and a fraction along it (`along`, 0 to 1): its
point is that share of the leg's length along the line, by geodesic length on WGS 84 (decision 0066).

The side and the first zoom are chosen here (decision 0026, amended 2026-11-16, and decision 0077). For each
drawing, in priority order, every side is scored by what the drawing and its caption would cover on screen: the stop
markers and route lines of every journey and the pins of other places (place). No side may touch a drawing already
placed, GAP_PX apart, at the zoom where both show: a drawing with no such side waits for a closer zoom, as far as
MAX_ZOOM, where the points have spread out. Among the sides that keep clear, the best wins; a tie keeps the side
nearest the seed's `side`. If even the best covers a stop or more than LINE_OK of route line, the drawing waits for a
closer zoom where the country has spread out, but at most MAX_RISE zoom steps past the first zoom where it keeps clear
of the other drawings. A drawing that touches another on every side even at MAX_ZOOM moves its point a little
(NEAR_PX), never across the international boundary.

A drawing shows from the later of its seed's `first_seen` and its pin's (shown_from): a drawing beside a pin the reader
has not reached would say where the story goes. Its `episode` stays the seed's, the episode of the scene it shows.

Screen footprints are measured in Web Mercator (EPSG:3857) pixels, as MapLibre draws them: 512 px tiles, so a zoom z
world is 512 * 2^z px across. The coordinates are the published layers' (WGS 84) and the sizes are relief.ts's.
"""

import csv
import json
import math
from dataclasses import dataclass

from pyproj import Geod, Transformer
from shapely import STRtree
from shapely.geometry import LineString, Point, Polygon, box

from crossing.build_story import r5, write
from crossing.paths import DATA, SEEDS

SEED = SEEDS / "vignettes.csv"
SIDES = {"n": "north", "ne": "north-east", "e": "east", "se": "south-east", "s": "south", "sw": "south-west",
         "w": "west", "nw": "north-west"}
MAX_ZOOM = 12
# How many zoom steps a drawing may wait past its seed `min_zoom` for a clear side (decision 0026, amended).
MAX_RISE = 1
# The least gap between two drawings (with their captions) on screen, so that none touch (decision 0077).
GAP_PX = 4
# How far a drawing with no side clear of the others may move its point, in screen px at MAX_ZOOM (about 0.4 to 4 km
# on the ground at any zoom), and what each such pixel moved costs in the score: the nearest clear spot wins.
NEAR_PX = (12, 24, 48, 80, 120)
MOVE_W = 0.5
DIRECTIONS = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 45)]
# The international boundary across the story's country, lon and lat, west to east: a drawing that moves stays on
# its scene's side of it (decisions 0075 and 0077). From the Colorado River the line runs to Nogales, along 31°20′ N
# to the meridian of 108°12.5′ W, north on it to 31°47′ N, east along that to the Rio Grande (the Gadsden Purchase
# lines, as area_drafts.py has them), then down the Rio Grande, which these points follow only roughly.
BORDER = [(-114.81, 32.49), (-111.07, 31 + 20 / 60), (-108.2083, 31 + 20 / 60), (-108.2083, 31 + 47 / 60),
          (-106.53, 31 + 47 / 60), (-106.2, 31.47), (-105.0, 30.68), (-104.45, 29.6), (-103.0, 29.0)]

# relief.ts: the drawing grid's half width, the gap to the pin, and icon and caption sizes by zoom.
HALF, GAP = 48, 16
ICON_SIZE = [(6, 0.52), (9, 0.72), (12, 0.91)]
# Captions are at the Wheeler size times tokens.ts's TEXT_SCALE.
TEXT_SCALE = 1.2
TEXT_SIZE = [(z, size * TEXT_SCALE) for z, size in [(6, 12.5), (9, 13.3), (12, 14.5)]]
TEXT_MAX_WIDTH = 9  # ems
# Estimates for the IM Fell English italic caption: the mean width of a character and the line height, in ems.
CHAR_EM, LINE_EM = 0.47, 1.2
# On screen: a stop marker's radius (map.css, 22 px), a route line's half width with a little room, and each place
# pin's radius by role (StoryLayers.tsx). Places with role `stop` lie under a stop marker and are not counted twice.
STOP_R, LINE_HALF = 11, 2
PLACE_R = {"passing": 5, "tale": 6, "context": 2}
# Kinds named by a label across the country rather than drawn as a pin.
UNPINNED = {"range", "valley", "county", "plain", "stream", "river", "canyon"}
# Stops and places this close to the drawing's own point are its own pin, which the gap keeps clear of the drawing.
OWN_M = 100
# A score in screen pixels of route line: a stop or another drawing weighs about two marker widths of line, a place
# pin one.
STOP_W, DRAWING_W, PLACE_W = 40, 40, 20
# A drawing is clear of the story when it covers no stop marker and at most this much route line, in drawing widths:
# one line passing across it, not a crossroads or a line run along it.
LINE_OK = 1.0

MERC = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
UNMERC = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
WORLD_M = 2 * math.pi * 6378137
WGS84 = Geod(ellps="WGS84")


def along_leg(coords: list[list[float]], share: float) -> tuple[float, float]:
    """The point `share` (0 to 1) of the way along a line of lon, lat pairs, by geodesic length on WGS 84: the
    target length is found among the parts' lengths, then the point is that far along its part's geodesic."""
    if not 0 <= share <= 1:
        raise ValueError(f"along must be from 0 to 1, not {share}")
    parts = [WGS84.inv(*a, *b) for a, b in zip(coords, coords[1:], strict=False)]
    left = share * sum(dist for _, _, dist in parts)
    for (lon, lat), (az, _, dist) in zip(coords, parts, strict=False):
        if left <= dist:
            lon, lat, _ = WGS84.fwd(lon, lat, az, left)
            return lon, lat
        left -= dist
    return tuple(coords[-1])


def anchor(seed: dict, points: dict[str, dict], legs: dict[str, dict]) -> tuple[float, float, dict]:
    """A seed row's point (lon, lat) and the feature it stands beside, which dates it: its stop or place (`ref`),
    with the row's own lon and lat if it has them, or its journey leg (`leg` and `along`)."""
    if bool(seed.get("leg")) == bool(seed["ref"]):
        raise SystemExit(f"vignettes.csv {seed['id']}: give either a ref or a leg, not both or neither")
    if seed.get("leg"):
        if seed["leg"] not in legs:
            raise SystemExit(f"vignettes.csv {seed['id']}: {seed['leg']} is not a route segment")
        leg = legs[seed["leg"]]
        return *along_leg(leg["geometry"]["coordinates"], float(seed["along"])), leg
    pin = points[seed["ref"]]
    lon, lat = (float(seed["lon"]), float(seed["lat"])) if seed["lon"] else pin["geometry"]["coordinates"]
    return lon, lat, pin


def px_per_m(z: float) -> float:
    """Screen pixels per Web Mercator metre at zoom z. Mercator metres stretch with latitude just as the screen does,
    so the scale is the same everywhere."""
    return 512 * 2**z / WORLD_M


def interp(table: list[tuple[float, float]], z: float) -> float:
    if z <= table[0][0]:
        return table[0][1]
    for (z0, v0), (z1, v1) in zip(table, table[1:], strict=False):
        if z <= z1:
            return v0 + (v1 - v0) * (z - z0) / (z1 - z0)
    return table[-1][1]


def step(side: str) -> tuple[int, int]:
    """The direction of a side, screen x east and y south, as relief.ts's SIDES."""
    return (1 if "e" in side else -1 if "w" in side else 0), (-1 if "n" in side else 1 if "s" in side else 0)


def footprint(side: str, z: float, label: str) -> list[tuple[float, float, float, float]]:
    """The drawing's box and, with a label, its caption's box, in screen px from the point (x east, y south)."""
    size = interp(ICON_SIZE, z)
    dx, dy = step(side)
    diagonal = dx != 0 and dy != 0
    reach = HALF + (GAP * math.sqrt(0.5) if diagonal else GAP)
    cx, cy = dx * reach * size, dy * reach * size
    h = HALF * size
    boxes = [(cx - h, cy - h, cx + h, cy + h)]
    if label:
        text = interp(TEXT_SIZE, z)
        ems = len(label) * CHAR_EM
        lines = max(1, math.ceil(ems / TEXT_MAX_WIDTH))
        w = ems / lines * text
        top = cy + h + 2
        boxes.append((cx - w / 2, top, cx + w / 2, top + lines * LINE_EM * text))
    return boxes


def rects(at: Point, side: str, z: float, label: str) -> list[tuple[float, float, float, float]]:
    """The drawing's and its caption's boxes in Web Mercator metres (west, south, east, north), for a point in the
    same."""
    scale = px_per_m(z)
    return [(at.x + x0 / scale, at.y - y1 / scale, at.x + x1 / scale, at.y - y0 / scale)
            for x0, y0, x1, y1 in footprint(side, z, label)]


def boxes(at: Point, side: str, z: float, label: str) -> list[Polygon]:
    """The same boxes as shapely polygons."""
    return [box(*r) for r in rects(at, side, z, label)]


@dataclass
class Drawing:
    at: Point  # Web Mercator metres
    side: str
    zoom: float
    label: str

    def overlaps(self, other: "Drawing") -> bool:
        """Whether the two come within GAP_PX of each other at any zoom where both show, up to MAX_ZOOM, past which
        nothing grows. Two points apart spread faster than their drawings grow, but two drawings on one point do not
        spread, and their captions grow at another rate than the drawings, so every half zoom is checked."""
        first = max(self.zoom, other.zoom)
        for z in [first] + [k / 2 for k in range(math.floor(first * 2) + 1, MAX_ZOOM * 2 + 1)]:
            gap = GAP_PX / px_per_m(z)
            theirs = rects(other.at, other.side, z, other.label)
            if any(a[0] - gap < b[2] and b[0] - gap < a[2] and a[1] - gap < b[3] and b[1] - gap < a[3]
                   for a in rects(self.at, self.side, z, self.label) for b in theirs):
                return True
        return False


@dataclass
class Clash:
    stops: int = 0
    places: int = 0
    route_px: float = 0.0
    drawings: int = 0
    width_px: float = 0.0  # the drawing's width at this zoom

    @property
    def score(self) -> float:
        return self.stops * STOP_W + self.places * PLACE_W + self.route_px + self.drawings * DRAWING_W

    @property
    def level(self) -> int:
        """0: clear of the story (no stop marker, and no more route line than LINE_OK allows); 1: on route lines
        only; 2: on a stop marker; 3: on another drawing, where the two read as neither."""
        if self.drawings:
            return 3
        return 2 if self.stops else 1 if self.route_px > LINE_OK * self.width_px else 0

    @property
    def clear(self) -> bool:
        return self.level == 0


class Story:
    """The stops, other place pins and route lines of every journey, in Web Mercator metres."""

    def __init__(self, stops: list[dict], places: list[dict], journeys: list[dict]) -> None:
        def xy(f: dict) -> Point:
            return Point(MERC.transform(*f["geometry"]["coordinates"]))

        self.stops = [xy(f) for f in stops]
        pinned = [f for f in places if f["properties"].get("role") in PLACE_R
                  and f["properties"].get("kind") not in UNPINNED]
        self.places = [xy(f) for f in pinned]
        self.place_r = [PLACE_R[f["properties"]["role"]] for f in pinned]
        self.lines = [LineString([MERC.transform(*c) for c in f["geometry"]["coordinates"]]) for f in journeys]
        self.stop_tree, self.place_tree, self.line_tree = STRtree(self.stops), STRtree(self.places), STRtree(self.lines)

    def clash(self, d: Drawing, placed: list[Drawing] = ()) -> Clash:
        """What the drawing covers at its zoom: stops, place pins and route line, and the drawings already placed."""
        scale = px_per_m(d.zoom)
        c = Clash(width_px=2 * HALF * interp(ICON_SIZE, d.zoom))
        for k, b in enumerate(boxes(d.at, d.side, d.zoom, d.label)):
            # The drawing's own pin counts only under the caption, which can reach back over it; the gap keeps the
            # drawing itself clear of it.
            def other(p: Point, k: int = k) -> bool:
                return k > 0 or p.distance(d.at) > OWN_M

            c.stops += sum(1 for i in self.stop_tree.query(b, predicate="dwithin", distance=STOP_R / scale)
                           if other(self.stops[i]))
            c.places += sum(1 for i in self.place_tree.query(b.buffer(max(PLACE_R.values()) / scale))
                            if self.places[i].distance(b) <= self.place_r[i] / scale and other(self.places[i]))
            grown = b.buffer(LINE_HALF / scale, join_style="mitre")
            for i in self.line_tree.query(grown):
                c.route_px += self.lines[i].intersection(grown).length * scale
        c.route_px = round(c.route_px, 1)
        c.drawings = sum(1 for p in placed if d.overlaps(p))
        return c


def angle(a: str, b: str) -> int:
    """How many eighths of a turn apart two sides are."""
    order = list(SIDES)
    d = abs(order.index(a) - order.index(b)) % 8
    return min(d, 8 - d)


def in_us(lon: float, lat: float) -> bool:
    """Whether a point lies north of BORDER (in the United States). The vertical stretch along 108°12.5′ W belongs to
    the line east of it, so a point west of that meridian is judged against 31°20′ N."""
    if lon < BORDER[0][0]:
        return lat > BORDER[0][1]
    for (x0, y0), (x1, y1) in zip(BORDER, BORDER[1:], strict=False):
        if x0 <= lon < x1:
            return lat > y0 + (y1 - y0) * (lon - x0) / (x1 - x0)
    return lat > BORDER[-1][1]


def place(story: Story, at: Point, seed_side: str, min_zoom: float, label: str,
          placed: list[Drawing] = ()) -> tuple[Drawing, Clash]:
    """The side, first zoom and point for one drawing, and what it covers there, never touching the drawings placed.

    At each zoom from min_zoom to MAX_ZOOM the best side is, of those that touch no drawing placed, the one with the
    lowest clash level, then score, then nearest the seed's side. Where no side of the drawing's own point is free at
    that zoom, points a little way off (NEAR_PX at MAX_ZOOM, the same distance on the ground at every zoom, on the
    scene's side of the boundary) are tried too. The first zoom with a free spot is the earliest the drawing can
    show. From there it shows at the first zoom whose best reaches the lowest level any zoom reaches (clear if it can
    be, else off every stop marker), but at most MAX_RISE steps later.
    """
    zooms = [min_zoom] + [float(z) for z in range(math.floor(min_zoom) + 1, MAX_ZOOM + 1)]
    us = in_us(*UNMERC.transform(at.x, at.y))

    def same_side(d: Drawing) -> bool:
        """Whether the drawing itself, not only its point, is on its scene's side of the border."""
        x0, y0, x1, y1 = rects(d.at, d.side, d.zoom, "")[0]
        return in_us(*UNMERC.transform((x0 + x1) / 2, (y0 + y1) / 2)) == us

    def best(z: float, points: list[tuple[Point, float]]) -> tuple[Clash, Drawing, float] | None:
        """The best candidate at zoom z that touches no drawing placed, or None."""
        free = [(c, d, px) for p, px in points for d in (Drawing(p, s, z, label) for s in SIDES)
                if (c := story.clash(d, placed)).drawings == 0 and (px == 0 or same_side(d))]
        return min(free, key=lambda c: (c[0].level, c[0].score + MOVE_W * c[2], angle(c[1].side, seed_side)),
                   default=None)

    scale = px_per_m(MAX_ZOOM)
    near = [(Point(at.x + dx * px / scale, at.y - dy * px / scale), px) for px in NEAR_PX for dx, dy in DIRECTIONS]
    found = [best(z, [(at, 0.0)]) or best(z, near) for z in zooms]
    free = [k for k, b in enumerate(found) if b]
    if free:
        window = [k for k in free if k <= free[0] + MAX_RISE]
        lowest = min(found[k][0].level for k in free)
        first = next(k for k in free if found[k][0].level == lowest)
        clash, d, _ = found[first if first in window else window[-1]]
        return d, clash
    # Nowhere free: the side at MAX_ZOOM that touches fewest drawings.
    d = min((Drawing(at, s, float(MAX_ZOOM), label) for s in SIDES), key=lambda d: story.clash(d, placed).drawings)
    return d, story.clash(d, placed)


def journey_of(ref: str, first_seen: str, stops: list[dict], places: dict[str, dict],
               legs: dict[str, dict] | None = None) -> str:
    """A stop's or a leg's journey; for a place, the journey of its first stop in reading order, or, for a place no
    journey stops at, of the nearest stop first seen in the drawing's own episode."""
    if legs and ref in legs:
        return legs[ref]["properties"]["journey"]
    by_id = {f["properties"]["id"]: f["properties"] for f in stops}
    if ref in by_id:
        return by_id[ref]["journey"]
    at = [p for p in by_id.values() if p.get("place_ref") == ref]
    if at:
        return min(at, key=lambda p: (p["first_seen"], p["journey"], p["sequence"]))["journey"]
    lon, lat = places[ref]["geometry"]["coordinates"]
    same = [f for f in stops if f["properties"]["first_seen"] == first_seen]
    nearest = min(same, key=lambda f: math.dist(f["geometry"]["coordinates"], (lon, lat)))
    return nearest["properties"]["journey"]


def shown_from(scene: str, pin: dict) -> str:
    """The episode a drawing shows from: its scene's, or its pin's if the pin shows later."""
    return max(scene, pin["properties"]["first_seen"])


def load() -> tuple[list[dict], list[dict], list[dict]]:
    return tuple(json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))["features"]
                 for name in ("stops", "places", "journeys"))


def main() -> None:
    stops, places, journeys = load()
    story = Story(stops, places, journeys)
    points = {f["properties"]["id"]: f for f in stops + places}
    place_by_id = {f["properties"]["id"]: f for f in places}
    legs = {f["properties"]["id"]: f for f in journeys if f["properties"]["kind"] == "route-segment"}

    with SEED.open(encoding="utf-8", newline="") as f:
        seeds = list(csv.DictReader(f))
    # The most important drawings choose first; the rest keep clear of them.
    order = sorted(range(len(seeds)), key=lambda i: (int(seeds[i]["priority"]), i))
    placed: list[Drawing] = []
    chosen = {}
    for i in order:
        s = seeds[i]
        lon, lat, pin = anchor(s, points, legs)
        at = Point(MERC.transform(lon, lat))
        d, clash = place(story, at, s["side"], float(s["min_zoom"]), s["label"], placed)
        placed.append(d)
        chosen[i] = (lon, lat, *UNMERC.transform(d.at.x, d.at.y), pin, d.side, d.zoom, clash)

    features = []
    for i, s in enumerate(seeds):
        lon, lat, shown_lon, shown_lat, pin, side, zoom, clash = chosen[i]
        az, _, moved_m = WGS84.inv(lon, lat, shown_lon, shown_lat)
        on_leg = None
        if s.get("leg"):
            where = "its point on the route"
            leg = pin["properties"]
            on_leg = (f"Its point is on the route line, {float(s['along']):.0%} of the way along the {leg['journey']} "
                      f"leg “{leg['name']}” ({s['leg']}) by length, measured on the WGS 84 ellipsoid.")
        else:
            where = "its own place" if s["lon"] else pin["properties"]["name"]
        placed_note = (f"The drawing is set on the {SIDES[side]} side of {where} (where it covers the fewest stops, "
                       f"route lines and other drawings), beside the {'point' if on_leg else 'pin'} rather than on "
                       "it. It is not to scale, and it shows roughly where the scene happens, not exactly.")
        if moved_m >= 100:
            compass = list(SIDES.values())[round((az % 360) / 45) % 8]
            placed_note = (f"The drawing is set on the {SIDES[side]} side of a point {moved_m / 1000:.1f} km "
                           f"{compass} of {where} (geodesic distance on WGS 84), moved off it because on every side "
                           "it would touch another drawing there. It is not to scale, and it shows roughly where the "
                           "scene happens, not exactly.")
        first_seen = shown_from(s["first_seen"], pin)
        waits = None
        if first_seen != s["first_seen"]:
            waits = (f"The scene is in {s['first_seen']}, but the drawing shows from {first_seen}, with the "
                     f"{'leg' if on_leg else 'pin'} it stands beside, so it does not show where the story goes before "
                     "the reader gets there.")
        held = None
        if zoom > float(s["min_zoom"]) and clash.clear:
            held = (f"Shown from zoom {zoom:g}, not {float(s['min_zoom']):g}: further out, on every side, it would "
                    "touch another drawing, or cover a stop or a route line.")
        elif zoom > float(s["min_zoom"]):
            held = (f"Shown from zoom {zoom:g}, not {float(s['min_zoom']):g}: further out it would touch another "
                    f"drawing or cover more. At zoom {zoom:g} it still covers a stop or a route line on every side, "
                    "but a drawing waits no longer than it must to keep clear of the others, so it sits on the side "
                    "where it covers least.")
        elif not clash.clear:
            held = ("On every side it covers a stop or a route line from its first zoom, and no closer zoom would "
                    "clear it, so it shows from that zoom on the side where it covers least.")
        ref = s.get("leg") or s["ref"]
        props = dict(
            id=f"vignette-{s['id']}", name=s["name"], kind="vignette", stands_for=s["stands_for"], place_ref=ref,
            journey=journey_of(ref, s["first_seen"], stops, place_by_id, legs),
            part=int(first_seen[0]), episode=s["first_seen"], first_seen=first_seen,
            certainty="approximate", method="hand-drawn", source="this-site", source_id=None,
            source_licence="CC BY 4.0",
            note_safe=s["note"], reasoning=" ".join(x for x in (s["reasoning"], on_leg, waits, placed_note, held) if x),
            vignette=f"vignette-{s['id']}", side=side, min_zoom=zoom,
            priority=int(s["priority"]), label=s["label"], credit=s["credit"],
        )
        point = {"type": "Point", "coordinates": [r5(shown_lon), r5(shown_lat)]}
        features.append({"type": "Feature", "geometry": point, "properties": props})
        moved = []
        if side != s["side"]:
            moved.append(f"side {s['side']} -> {side}")
        if zoom != float(s["min_zoom"]):
            moved.append(f"min_zoom {float(s['min_zoom']):g} -> {zoom:g}")
        if moved_m >= 100:
            moved.append(f"moved {moved_m / 1000:.1f} km")
        if moved:
            print(f"{s['id']}: {', '.join(moved)}")
    write("vignettes.geojson", features)
    print(f"{len(features)} vignettes")


if __name__ == "__main__":
    main()
