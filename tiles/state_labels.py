"""Write site/public/labels/states.geojson: label points for the states in the story box, clear of the story.

Run from the repo root: uv run --project pipeline python tiles/state_labels.py
Reads the Natural Earth 10m admin 1 polygons from private/cache/basemap/ and the story layers in data/.

The labels are drawn in widely spaced small capitals at low zoom (site/src/map/style.ts, layer 'state-label'),
so each needs room: a box the size of its lettering (LABEL_* below, the same numbers the style uses) that lies
inside the state's part of the story box and clear of every journey, stop, place, place label and area.
Everything is measured in Web Mercator, where a screen pixel at zoom z is a fixed number of metres.
For each state the script tries points on a 5 km grid. Zoomed out, one label: the point that fits from the lowest
zoom, then the one nearest the middle of the state with room to spare. Closer in (CLOSE_ZOOM up), a few labels
spread over the state, so a view of part of it still finds its name. Each point carries the zooms it shows at
(`min_zoom`, `max_zoom`); the style reads them. A state with only a sliver in the box gets no label.
"""

import json
import math
import subprocess
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely import STRtree, box, prepare
from shapely.geometry import Point, shape
from shapely.ops import polylabel

REPO = Path(__file__).resolve().parents[1]
NE = REPO / "private" / "cache" / "basemap" / "ne_10m_admin_1_states_provinces" / "ne_10m_admin_1_states_provinces.shp"
DATA = REPO / "data"
OUT = REPO / "site" / "public" / "labels" / "states.geojson"
STORY_BOX = (-113, 27, -104, 36)
# The lettering, as drawn by the style: size in px at MIN_ZOOM and MAX_ZOOM (linear between), letter spacing in em.
MIN_ZOOM, MAX_ZOOM = 5, 8
LABEL_SIZE = (12, 16)
LABEL_SPACING = 0.6
# IM Fell English SC: the mean advance of a letter, in em. Measured with fontTools from IMFeENsc28P.ttf, the names
# here average 0.46 to 0.54; 0.56 leaves a little over.
GLYPH_EM = 0.56
# The overview label shows from the first of these zooms at which it fits, up to CLOSE_ZOOM; from CLOSE_ZOOM, up to
# MAX_REPEATS labels per state, at least REPEAT_PX apart at CLOSE_ZOOM, so that a closer view still finds one.
OVERVIEW = [5, 5.5, 6]
CLOSE_ZOOM = 6.5
MAX_REPEATS = 6
REPEAT_PX = 300
# Room beyond this many px counts as enough; then the point nearest the middle of the state's part wins.
ENOUGH_PX = 30
# Clear space kept round the label, in px.
MARGIN_PX = 8
# Story place labels: drawn below the point, about this wide per character and this tall, in px.
PLACE_CHAR_PX, PLACE_LABEL_PX = 7.5, 18
# A state whose part of the story box is smaller than this, in km² (roughly), gets no label.
MIN_PART_KM2 = 10000
# Spanish names on the Mexican side, as the map names other Mexican places; English on the US side.
NAME_FIELD = {"MEX": "name_es", "USA": "name"}

to_merc = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
to_wgs = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform


def merc(geom):
    return shapely.transform(geom, lambda xy: np.column_stack(to_merc(xy[:, 0], xy[:, 1])))


def px_m(zoom: float) -> float:
    """Web Mercator metres per screen pixel at a MapLibre zoom (512 px tiles)."""
    return 2 * math.pi * 6378137 / (512 * 2**zoom)


def size_at(zoom: float) -> float:
    t = (min(max(zoom, MIN_ZOOM), MAX_ZOOM) - MIN_ZOOM) / (MAX_ZOOM - MIN_ZOOM)
    return LABEL_SIZE[0] + t * (LABEL_SIZE[1] - LABEL_SIZE[0])


def label_box(x: float, y: float, name: str, zoom: float):
    """The label's footprint, centred on (x, y), with its margin, in Web Mercator metres."""
    size, m = size_at(zoom), px_m(zoom)
    # MapLibre adds the letter spacing between letters, not after the last.
    w = (len(name) * GLYPH_EM + (len(name) - 1) * LABEL_SPACING) * size + 2 * MARGIN_PX
    h = size * 1.2 + 2 * MARGIN_PX
    return box(x - w / 2 * m, y - h / 2 * m, x + w / 2 * m, y + h / 2 * m)


def states() -> list[tuple[str, str, object]]:
    sql = "SELECT name, name_es, adm0_a3 FROM ne_10m_admin_1_states_provinces WHERE adm0_a3 IN ('USA', 'MEX')"
    out = subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-spat", *map(str, STORY_BOX), "-sql", sql, "/vsistdout/", str(NE)],
                         check=True, capture_output=True, text=True).stdout
    found = []
    for f in json.loads(out)["features"]:
        p = f["properties"]
        part = shape(f["geometry"]).intersection(box(*STORY_BOX))
        # Slivers along the box edge (Baja California Sur, Sinaloa) are too small to name.
        if part.area * 111.32**2 * math.cos(math.radians(part.centroid.y)) >= MIN_PART_KM2:
            found.append((p[NAME_FIELD[p["adm0_a3"]]], p["adm0_a3"], merc(part)))
    return found


def story_obstacles(zoom: float) -> STRtree:
    """Everything a state label must not cover at this zoom, in Web Mercator."""
    m = px_m(zoom)
    geoms = []
    for name in ("journeys", "areas"):
        for f in json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))["features"]:
            geoms.append(merc( shape(f["geometry"])).buffer(3 * m))
    for name in ("stops", "places"):
        for f in json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))["features"]:
            p = f["properties"]
            x, y = to_merc(*f["geometry"]["coordinates"][:2])
            geoms.append(Point(x, y).buffer(6 * m))
            # Context towns are labelled only from zoom 9 (StoryLayers.tsx); stops are numbered markers.
            if name == "places" and p.get("role") != "context":
                w = len(p["name"]) * PLACE_CHAR_PX * m
                geoms.append(box(x - w / 2, y - (4 + PLACE_LABEL_PX) * m, x + w / 2, y))
    return STRtree(geoms)


def fits(name: str, part, tree: STRtree, zoom: float, step: float = 5000) -> list[tuple[float, float, float]]:
    """Grid points where the label fits at this zoom: (room in px, x, y). Room is the distance from the label to
    the nearest obstacle or state edge."""
    prepare(part)
    x0, y0, x1, y1 = part.bounds
    found = []
    for x in np.arange(x0 + step / 2, x1, step):
        for y in np.arange(y0 + step / 2, y1, step):
            lb = label_box(x, y, name, zoom)
            if not part.contains(lb) or len(tree.query(lb, predicate="intersects")):
                continue
            near = tree.geometries[tree.nearest(lb)]
            found.append((min(lb.distance(near), lb.distance(part.boundary)) / px_m(zoom), x, y))
    return found


def overview(name: str, part, trees: dict[float, STRtree]):
    """The overview label: the lowest zoom of OVERVIEW at which it fits, then enough room (ENOUGH_PX), then nearest
    the middle of the state's part (its pole of inaccessibility). None if it fits at none of them."""
    biggest = max(getattr(part, "geoms", [part]), key=lambda g: g.area)
    middle = polylabel(biggest, tolerance=1000)
    for zoom in OVERVIEW:
        found = fits(name, part, trees[zoom], zoom)
        if found:
            room, x, y = min(found, key=lambda f: (-min(f[0], ENOUGH_PX), Point(f[1], f[2]).distance(middle)))
            return zoom, room, x, y
    return None


def close_in(name: str, part, tree: STRtree) -> list[tuple[float, float, float]]:
    """The closer labels: points where the label fits at CLOSE_ZOOM, roomiest first, at least REPEAT_PX apart."""
    chosen: list[tuple[float, float, float]] = []
    gap = REPEAT_PX * px_m(CLOSE_ZOOM)
    for room, x, y in sorted(fits(name, part, tree, CLOSE_ZOOM), reverse=True):
        if len(chosen) == MAX_REPEATS:
            break
        if all(math.hypot(x - cx, y - cy) >= gap for _, cx, cy in chosen):
            chosen.append((room, x, y))
    return chosen


def main() -> None:
    trees = {z: story_obstacles(z) for z in [*OVERVIEW, CLOSE_ZOOM]}
    features = []

    def add(name: str, country: str, x: float, y: float, lo: float, hi: float) -> None:
        lon, lat = to_wgs(x, y)
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 4), round(lat, 4)]},
                         "properties": {"name": name, "country": country, "min_zoom": lo, "max_zoom": hi}})

    for name, country, part in states():
        found = overview(name, part, trees)
        if found:
            zoom, room, x, y = found
            add(name, country, x, y, zoom, CLOSE_ZOOM)
            lon, lat = to_wgs(x, y)
            print(f"{name}: overview at {lon:.3f}, {lat:.3f} from zoom {zoom} ({room:.0f} px clear)")
        else:
            print(f"{name}: no room for an overview label")
        repeats = close_in(name, part, trees[CLOSE_ZOOM])
        for _, x, y in repeats:
            add(name, country, x, y, CLOSE_ZOOM, MAX_ZOOM + 0.5)
        print(f"{name}: {len(repeats)} labels from zoom {CLOSE_ZOOM}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO)}: {len(features)} labels")


if __name__ == "__main__":
    main()
