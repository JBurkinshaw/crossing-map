"""Build the vignette anchors (design section 10) from pipeline/seeds/vignettes.csv.

Run from the repo root, after crossing.build_story: uv run --project pipeline python -m crossing.build_vignettes
Reads the seed and data/stops.geojson, data/places.geojson and data/journeys.geojson (each vignette's `ref` is a stop
or place id). Writes data/vignettes.geojson: one Point per vignette, on the thing it stands for, with the `side` the
map draws the drawing on (site/src/map/relief.ts), so it sits beside its pin at every zoom and never covers it. A seed
row with its own lon and lat stands for a place that is not one of the book's stops or places (the Trinity Site).

The side and the first zoom are chosen here (decision 0026, amended 2026-11-16). For each drawing, in priority order,
every side is scored by what the drawing and its caption would cover on screen: the stop markers and route lines of
every journey, the pins of other places, and the drawings already placed (place). The best side wins; a tie keeps
the side nearest the seed's `side`. If even the best side covers a stop, another drawing or more than LINE_OK of route
line at the seed's `min_zoom`, the drawing waits for a closer zoom where the country has spread out, but at most
MAX_RISE zoom steps: the owner wants the drawings in view as context, so past that it takes its clearest side there.

A drawing shows from the later of its seed's `first_seen` and its pin's (shown_from): a drawing beside a pin the reader
has not reached would say where the story goes. Its `episode` stays the seed's, the episode of the scene it shows.

Screen footprints are measured in Web Mercator (EPSG:3857) pixels, as MapLibre draws them: 512 px tiles, so a zoom z
world is 512 * 2^z px across. The coordinates are the published layers' (WGS 84) and the sizes are relief.ts's.
"""

import csv
import json
import math
from dataclasses import dataclass

from pyproj import Transformer
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

# relief.ts: the drawing grid's half width, the gap to the pin, and icon and caption sizes by zoom.
HALF, GAP = 48, 16
ICON_SIZE = [(6, 0.52), (9, 0.72), (12, 0.91)]
TEXT_SIZE = [(6, 12.5), (9, 13.3), (12, 14.5)]
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
WORLD_M = 2 * math.pi * 6378137


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


def boxes(at: Point, side: str, z: float, label: str) -> list[Polygon]:
    """The drawing's and its caption's boxes in Web Mercator metres, for a point in the same."""
    scale = px_per_m(z)
    return [box(at.x + x0 / scale, at.y - y1 / scale, at.x + x1 / scale, at.y - y0 / scale)
            for x0, y0, x1, y1 in footprint(side, z, label)]


@dataclass
class Drawing:
    at: Point  # Web Mercator metres
    side: str
    zoom: float
    label: str

    def overlaps(self, other: "Drawing") -> bool:
        """Whether the two cover each other once both show. Points spread apart faster than drawings grow, so the
        zoom where the later one first shows is the worst."""
        z = max(self.zoom, other.zoom)
        mine = boxes(self.at, self.side, z, self.label)
        return any(a.intersects(b) for a in mine for b in boxes(other.at, other.side, z, other.label))


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


def place(story: Story, at: Point, seed_side: str, min_zoom: float, label: str,
          placed: list[Drawing] = ()) -> tuple[Drawing, Clash]:
    """The side and first zoom for one drawing, and what it covers there, keeping clear of the drawings placed.

    At each zoom from min_zoom to MAX_ZOOM the best side is the one with the lowest clash level, then score, then
    nearest the seed's side. The drawing first shows at the first zoom whose best side reaches the lowest level any
    zoom reaches: clear if it can be, else off every stop marker, and so on; a drawing as crowded at every zoom keeps
    its own min_zoom, since waiting would not help (a hub where many stops and lines meet). That first zoom is at most
    MAX_RISE steps past min_zoom: a drawing that would wait longer shows there, on its clearest side at that zoom.
    """
    zooms = [min_zoom] + [float(z) for z in range(math.floor(min_zoom) + 1, MAX_ZOOM + 1)]
    best = []
    for z in zooms:
        scored = [(story.clash(d, placed), d) for d in (Drawing(at, s, z, label) for s in SIDES)]
        best.append(min(scored, key=lambda cd: (cd[0].level, cd[0].score, angle(cd[1].side, seed_side))))
    lowest = min(c.level for c, _ in best)
    first = next(k for k, (c, _) in enumerate(best) if c.level == lowest)
    clash, d = best[min(first, MAX_RISE)]
    return d, clash


def journey_of(ref: str, first_seen: str, stops: list[dict], places: dict[str, dict]) -> str:
    """A stop's journey; for a place, the journey of its first stop in reading order, or, for a place no journey
    stops at, of the nearest stop first seen in the drawing's own episode."""
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

    with SEED.open(encoding="utf-8", newline="") as f:
        seeds = list(csv.DictReader(f))
    # The most important drawings choose first; the rest keep clear of them.
    order = sorted(range(len(seeds)), key=lambda i: (int(seeds[i]["priority"]), i))
    placed: list[Drawing] = []
    chosen = {}
    for i in order:
        s = seeds[i]
        ref = points[s["ref"]]
        lon, lat = (float(s["lon"]), float(s["lat"])) if s["lon"] else ref["geometry"]["coordinates"]
        at = Point(MERC.transform(lon, lat))
        d, clash = place(story, at, s["side"], float(s["min_zoom"]), s["label"], placed)
        placed.append(d)
        chosen[i] = (lon, lat, d.side, d.zoom, clash)

    features = []
    for i, s in enumerate(seeds):
        lon, lat, side, zoom, clash = chosen[i]
        where = "its own place" if s["lon"] else points[s["ref"]]["properties"]["name"]
        placed_note = (f"The drawing is set on the {SIDES[side]} side of {where} (where it covers the fewest stops, "
                       "route lines and other drawings), beside the pin rather than on it. It is not to scale, and it "
                       "shows roughly where the scene happens, not exactly.")
        first_seen = shown_from(s["first_seen"], points[s["ref"]])
        waits = None
        if first_seen != s["first_seen"]:
            waits = (f"The scene is in {s['first_seen']}, but the drawing shows from {first_seen}, with the pin it "
                     "stands beside, so it does not show where the story goes before the reader gets there.")
        held = None
        if zoom > float(s["min_zoom"]) and clash.clear:
            held = (f"Shown from zoom {zoom:g}, not {float(s['min_zoom']):g}: further out, on every side, it would "
                    "cover a stop, a route line or another drawing.")
        elif zoom > float(s["min_zoom"]):
            held = (f"Shown from zoom {zoom:g}, not {float(s['min_zoom']):g}: further out it would cover more. At "
                    f"zoom {zoom:g} it still covers a stop, a route line or another drawing on every side, but a "
                    "drawing waits one zoom step at most, so it sits on the side where it covers least.")
        elif not clash.clear:
            held = ("On every side it covers a stop, a route line or another drawing from its first zoom, and no "
                    "closer zoom would clear it, so it shows from that zoom on the side where it covers least.")
        props = dict(
            id=f"vignette-{s['id']}", name=s["name"], kind="vignette", stands_for=s["stands_for"], place_ref=s["ref"],
            journey=journey_of(s["ref"], s["first_seen"], stops, place_by_id),
            part=int(first_seen[0]), episode=s["first_seen"], first_seen=first_seen,
            certainty="approximate", method="hand-drawn", source="this-site", source_id=None,
            source_licence="CC BY 4.0",
            note_safe=s["note"], reasoning=" ".join(x for x in (s["reasoning"], waits, placed_note, held) if x),
            vignette=f"vignette-{s['id']}", side=side, min_zoom=zoom,
            priority=int(s["priority"]), label=s["label"], credit=s["credit"],
        )
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [r5(lon), r5(lat)]},
                         "properties": props})
        moved = []
        if side != s["side"]:
            moved.append(f"side {s['side']} -> {side}")
        if zoom != float(s["min_zoom"]):
            moved.append(f"min_zoom {float(s['min_zoom']):g} -> {zoom:g}")
        if moved:
            print(f"{s['id']}: {', '.join(moved)}")
    write("vignettes.geojson", features)
    print(f"{len(features)} vignettes")


if __name__ == "__main__":
    main()
