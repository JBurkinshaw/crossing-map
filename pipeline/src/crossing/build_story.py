"""Build the story layers from the seeds in pipeline/seeds/.

Run from the repo root: uv run --project pipeline python -m crossing.build_story
Reads places.csv (every place the book names, plus context towns), place-picks.csv (crossing.gazetteer's picks),
place-overrides.csv (hand decisions, which win over a pick), stops.csv, snaps.csv and regions.geojson.
Writes data/places.geojson, data/stops.geojson, data/areas.geojson, data/journeys.geojson, data/elsewhere.json
(places outside the story box, listed in the panel rather than mapped) and the stage 4 sign-off checklists,
keeping any row already ticked.

A route segment follows the line its snap names, where the book names the road or river:
  nhd          a USGS NHD flowline by its GNIS name (shapefile, feature)
  tiger-road   a US Census TIGER road by its full name (shapefile, feature)
  ne-river     a Natural Earth river by name: the line the map itself draws for Mexican rivers
  inegi-road   an INEGI Red Nacional de Caminos road by its name (tracks.geojson, feature)
  inegi-river  INEGI's 1:50,000 streams of Strahler order min_order and up near the two stops; INEGI's streams
               carry no names, so the build checks that INEGI's toponyms put the river named in feature on the line
Each snap's lines form a network, and the segment is the shortest way along it between the points nearest the two
stops, so it can run from one named road onto another at a junction. Elsewhere it is a gentle curve between the
stops.
A segment's `travel` is its arriving stop's: empty for horseback, or foot, truck, car, bus, train or reported.
"""

import csv
import json
import math
import re
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
from pyproj import Geod
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from shapely import STRtree, make_valid
from shapely.geometry import LineString, MultiLineString, Point, shape

from crossing import least_cost
from crossing.paths import DATA, REPO, SEEDS, STORY_BOX

GEOD = Geod(ellps="WGS84")
LICENCE = {"wikidata": "CC0", "gnis": "Public domain", "geonames": "CC BY 4.0", "this-site": "CC BY 4.0",
           "usgs-nhd": "Public domain", "census-tiger": "Public domain", "natural-earth": "Public domain",
           "inegi": "INEGI free-use terms (Fuente: INEGI)"}
# Each snap source: the feature's source id, the name field and layer it is read by, whether it is a road or a
# river, and the dataset as the "How this line was drawn" text names it.
SNAPS = {
    "nhd": dict(source="usgs-nhd", field="gnis_name", layer="NHDFlowline", what="river",
                dataset="the USGS National Hydrography Dataset (high resolution)"),
    "tiger-road": dict(source="census-tiger", field="FULLNAME", layer=None, what="road",
                       dataset="the US Census Bureau's TIGER/Line roads (2023)"),
    "ne-river": dict(source="natural-earth", field="name", layer=None, what="river",
                     dataset="Natural Earth's 1:10m rivers"),
    "inegi-road": dict(source="inegi", field="name", layer="tracks", what="road",
                       dataset="INEGI's Red Nacional de Caminos (today's roads and tracks)"),
    "inegi-river": dict(source="inegi", field="ORDER_1", layer="inegi-streams", what="river",
                        dataset="INEGI's 1:50,000 hydrography"),
}
# The widest gap bridged between pieces of a named line, in degrees: about 1 km for roads (TIGER breaks some
# roads), about 200 m for INEGI's streams, whose many loose ends a wider bridge would join across country.
GAP_DEG = {"inegi-river": 0.002}
GAP_DEG_ROAD = 0.01
# A stop is joined to every line within this many degrees (about 50 m) of the nearest one.
JOIN_DEG = 0.00045
# How far around the two stops an inegi-river snap reads streams, in degrees, and how close one of INEGI's
# toponym points for the river must lie to the traced line, in metres.
RIVER_PAD_DEG = 0.15
RIVER_NAME_M = 300
INEGI_HYDRO = REPO / "private" / "cache" / "hydro" / "inegi"
# The false dawn at the book's end (plan 2.4): the text names no place or event, but it is widely read as the
# Trinity test, so the map draws a reported line of sight from Billy's last stop towards the Trinity Site
# (Wikidata Q19842077), SIGHTLINE_KM long, rather than a point.
TRINITY = (-106.4754, 33.6773)
# The light comes in the book's last episode, after the night at the waystation (4-08).
FALSE_DAWN = "4-09"
SIGHTLINE_KM = 30
# The sign-off checklists still open: the stops and places first seen in these Parts. Places resolved through
# the gazetteer (place-picks.csv) were signed off in stage 1 and are not listed again.
CHECKLISTS = [
    {"parts": {"2"}, "title": "Stage 4, batch A (Part II) place checklist",
     "path": REPO / "review" / "stage-4" / "batch-a" / "checklist.md"},
    {"parts": {"3", "4"}, "title": "Stage 4, batch B (Parts III and IV) place checklist",
     "path": REPO / "review" / "stage-4" / "batch-b" / "checklist.md"},
]
# A pin for a long or wide feature stands in for it; a pin for a town or pass is the thing itself.
LOCATED_KINDS = {"town", "city", "locale", "county", "pass", "summit"}
CHARACTERS = {"J1": ["wolf"], "J2": ["billy", "wolf"], "J3": ["billy"], "J4": ["billy", "boyd"], "J5": ["billy"],
              "J6": ["boyd", "girl"], "J7": ["billy"]}


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def r5(x: float) -> float:
    return round(x, 5)


def point(lat: float, lon: float) -> dict:
    return {"type": "Point", "coordinates": [r5(lon), r5(lat)]}


def circle(lat: float, lon: float, radius_km: float) -> dict:
    n = 48
    lons, lats, _ = GEOD.fwd([lon] * n, [lat] * n, [i * 360 / n for i in range(n)], [radius_km * 1000] * n)
    ring = [[r5(x), r5(y)] for x, y in zip(lons, lats, strict=True)]
    # RFC 7946: exterior rings run anticlockwise; fwd steps clockwise by azimuth.
    ring.reverse()
    return {"type": "Polygon", "coordinates": [ring + [ring[0]]]}


def curve(a: tuple[float, float], b: tuple[float, float], side: int) -> list[list[float]]:
    """A gentle quadratic Bézier from a to b (lon, lat), bowed 10% of its length to one side."""
    n = 16
    k = math.cos(math.radians((a[1] + b[1]) / 2))  # shrink longitude so the bow is square to the line
    dx, dy = (b[0] - a[0]) * k, b[1] - a[1]
    cx = (a[0] + b[0]) / 2 + side * -dy * 0.1 / k
    cy = (a[1] + b[1]) / 2 + side * dx * 0.1
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * cx + t**2 * b[0]
        y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * cy + t**2 * b[1]
        pts.append([r5(x), r5(y)])
    return pts


def ogr_lines(target: str, sql: str, bbox: tuple[float, float, float, float] | None = None) -> list:
    spat = ["-spat", *map(str, bbox)] if bbox else []  # in the source's lon/lat; -spat_srs does not work with -sql
    out = subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-dim", "XY", *spat, "-sql", sql,
                          "/vsistdout/", target], check=True, capture_output=True, text=True).stdout
    return [shape(f["geometry"]) for f in json.loads(out)["features"] if f["geometry"]]


def named_lines(snap: dict, a: tuple[float, float], b: tuple[float, float]) -> list:
    """The lines a snap names, in WGS 84: an NHD flowline, Natural Earth river, TIGER or INEGI road by name, or
    INEGI's streams of the snap's order and up around the two stops.

    A road that crosses a county line names one TIGER file per county, separated by semicolons. A way whose
    stretches carry different names (a county road that changes number, a turn from one highway onto another)
    names each, also separated by semicolons.
    """
    how = SNAPS[snap["source"]]
    if snap["source"] == "inegi-river":
        pad = RIVER_PAD_DEG
        bbox = (min(a[0], b[0]) - pad, min(a[1], b[1]) - pad, max(a[0], b[0]) + pad, max(a[1], b[1]) + pad)
        return ogr_lines(str(REPO / snap["shapefile"]),
                         f'SELECT ORDER_1 FROM "{how["layer"]}" WHERE ORDER_1 >= {int(snap["min_order"])}', bbox)
    # OGR SQL escapes a quote by doubling it.
    names = ", ".join("'{}'".format(n.replace("'", "''")) for n in snap["feature"].split(";"))
    lines = []
    for name in snap["shapefile"].split(";"):
        path = REPO / name
        layer = how["layer"] or path.name.removesuffix(".zip").removesuffix(".shp")
        target = f"/vsizip/{path}" if path.suffix == ".zip" else str(path)
        lines += ogr_lines(target, f'SELECT * FROM "{layer}" WHERE {how["field"]} IN ({names})')
    return lines


def plain(name: str) -> str:
    """A name in capitals without accents, for comparing INEGI's names with ours."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().upper()


def river_named(name: str, line) -> bool:
    """Whether one of INEGI's toponym points for the river `name` (as INEGI writes it, such as "Río Casas
    Grandes") lies within RIVER_NAME_M of the line. INEGI labels a river every 10 to 30 km, so the line is the
    whole connected channel the leg runs on, as far as the snap reads, not the leg alone."""
    x0, y0, x1, y1 = line.bounds
    k = math.cos(math.radians((y0 + y1) / 2))
    pad = RIVER_NAME_M / 111_320
    # Match on the name after its generic word (Río, Arroyo), which has no accents, then compare in full.
    tail = plain(name).split(" ", 1)[-1].replace("'", "''")
    for zip_path in sorted(INEGI_HYDRO.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as z:
            members = [m for m in z.namelist() if m.endswith("_to.shp")]
        for member in members:
            sql = f"SELECT NOMBRE_COM FROM \"{Path(member).stem}\" WHERE NOMBRE_COM LIKE '%{tail}%'"
            spat = ["-spat", str(x0 - pad / k), str(y0 - pad), str(x1 + pad / k), str(y1 + pad)]
            # INEGI's shapefiles are in Latin-1 and do not say so.
            out = subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-oo", "ENCODING=ISO-8859-1",
                                  *spat, "-sql", sql, "/vsistdout/", f"/vsizip/{zip_path}/{member}"],
                                 check=True, capture_output=True, text=True).stdout
            for f in json.loads(out)["features"]:
                if plain(f["properties"]["NOMBRE_COM"]) != plain(name):
                    continue
                x, y = f["geometry"]["coordinates"][:2]
                p = line.interpolate(line.project(Point(x, y)))
                if GEOD.inv(x, y, p.x, p.y)[2] <= RIVER_NAME_M:
                    return True
    return False


def network_path(lines: list, a: tuple[float, float], b: tuple[float, float],
                 gap_deg: float) -> tuple[list[tuple[float, float]], int, MultiLineString]:
    """The shortest way along a set of lines between the points on them nearest a and b (lon, lat), how many
    gaps it bridged, and the whole connected piece it runs on. Lines meet where they share a vertex, as TIGER's
    and INEGI's mostly do at junctions.
    Where pieces do not meet, a loose end is joined to the nearest point on a piece it is not yet connected to,
    if that lies within gap_deg, closest first: this closes the breaks in TIGER's roads and the seams between
    INEGI's sheets without short-cutting a network that is already joined."""
    k = math.cos(math.radians((a[1] + b[1]) / 2))  # shrink longitude so lengths are about right

    index: dict[tuple[float, float], int] = {}
    xy: list[tuple[float, float]] = []

    def node(c: tuple[float, float]) -> int:
        key = (round(c[0], 7), round(c[1], 7))
        if key not in index:
            index[key] = len(xy)
            xy.append(key)
        return index[key]

    edges: list[tuple[int, int, bool]] = []
    for g in lines:
        cs = list(g.coords)
        for p, q in zip(cs, cs[1:], strict=False):
            u, v = node(p), node(q)
            if u != v:
                edges.append((u, v, False))
    n_nodes = len(xy)
    adjacency = csr_matrix((np.ones(len(edges)), ([u for u, _, _ in edges], [v for _, v, _ in edges])),
                           shape=(n_nodes, n_nodes))
    piece = connected_components(adjacency, directed=False)[1]
    degree = np.bincount([n for u, v, _ in edges for n in (u, v)], minlength=n_nodes)
    loose = [n for n in range(n_nodes) if degree[n] == 1]
    segments = [LineString([xy[u], xy[v]]) for u, v, _ in edges]
    tree = STRtree(segments)
    candidates = []
    for n in loose:
        end = Point(xy[n])
        for e in tree.query(end, predicate="dwithin", distance=gap_deg):
            if piece[edges[e][0]] != piece[n]:
                q = segments[e].interpolate(segments[e].project(end))
                candidates.append((end.distance(q), n, int(e), (q.x, q.y)))
    joined = list(range(int(piece.max()) + 1))

    def root(c: int) -> int:
        while joined[c] != c:
            c = joined[c]
        return c

    for _, n, e, q in sorted(candidates):
        u, v, _ = edges[e]
        if root(piece[u]) == root(piece[n]):
            continue
        joined[root(piece[u])] = root(piece[n])
        m = node(q)
        edges += [(x, y, bridge) for x, y, bridge in ((u, m, False), (m, v, False), (n, m, True)) if x != y]
    # Use the connected piece that lies closest to the two stops together (a stray piece of the same road can lie
    # nearer one stop), and join each stop to the nearest point on every line of it within JOIN_DEG of the
    # nearest: some sources draw a river twice, overlapping, and the nearest copy can be a dead end.
    segments = [LineString([xy[u], xy[v]]) for u, v, _ in edges]
    group = [root(piece[u if u < n_nodes else v]) for u, v, _ in edges]  # a bridge node is new: use the other end
    near: dict[int, list[float]] = {}
    for e, seg in enumerate(segments):
        d = near.setdefault(group[e], [math.inf, math.inf])
        d[0], d[1] = min(d[0], seg.distance(Point(a))), min(d[1], seg.distance(Point(b)))
    best = min(near, key=lambda c: sum(near[c]))
    ends = []
    splits: dict[int, list[tuple[float, int]]] = {}  # segment -> (distance along it, node), for both stops
    mine = [i for i in range(len(segments)) if group[i] == best]
    for stop in (a, b):
        s = Point(stop)
        nearest = min(segments[i].distance(s) for i in mine)
        here = node(stop)
        for e in (i for i in mine if segments[i].distance(s) <= nearest + JOIN_DEG):
            along = segments[e].project(s)
            p = segments[e].interpolate(along)
            n = node((p.x, p.y))
            splits.setdefault(e, []).append((along, n))
            if here != n:
                edges.append((here, n, False))
        ends.append(here)
    # Split each joined segment at its stop points in order, so two stops on one long segment connect directly.
    for e, points in splits.items():
        u, v, bridge = edges[e]
        chain = [u] + [n for _, n in sorted(points)] + [v]
        edges += [(x, y, bridge) for x, y in zip(chain, chain[1:], strict=False) if x != y]
    # One weight per pair of nodes: csr_matrix adds duplicate entries together, and overlapping lines repeat edges.
    weight: dict[tuple[int, int], float] = {}
    for u, v, _ in edges:
        weight[(min(u, v), max(u, v))] = math.hypot((xy[u][0] - xy[v][0]) * k, xy[u][1] - xy[v][1]) or 1e-12
    rows = [u for u, v in weight] + [v for u, v in weight]
    cols = [v for u, v in weight] + [u for u, v in weight]
    graph = csr_matrix((list(weight.values()) * 2, (rows, cols)), shape=(len(xy), len(xy)))
    dist, pred = dijkstra(graph, indices=ends[0], return_predecessors=True)
    if not math.isfinite(dist[ends[1]]):
        raise ValueError("the stops lie on lines that do not meet")
    path = [ends[1]]
    while path[-1] != ends[0]:
        path.append(int(pred[path[-1]]))
    path.reverse()
    bridges = {frozenset((u, v)) for u, v, bridge in edges if bridge}
    gaps = sum(frozenset(pair) in bridges for pair in zip(path, path[1:], strict=False))
    piece = MultiLineString([seg for seg, g in zip(segments, group, strict=False) if g == best])
    return [xy[n] for n in path], gaps, piece


def snapped(snap: dict, a: tuple[float, float], b: tuple[float, float]) -> tuple[list[list[float]], int]:
    """The way along the snap's lines between stops a and b (lon, lat), joined to both stops, and how many gaps
    in the source lines were bridged to make it."""
    lines = [g for line in named_lines(snap, a, b) for g in getattr(line, "geoms", [line]) if g.length > 0]
    if not lines:
        sys.exit(f"{snap['journey']} {snap['from_seq']}: no lines named {snap['feature']!r} in {snap['shapefile']}")
    try:
        coords, gaps, piece = network_path(lines, a, b, GAP_DEG.get(snap["source"], GAP_DEG_ROAD))
    except ValueError as e:
        sys.exit(f"{snap['journey']} {snap['from_seq']}: {e}; name the roads that join them in snaps.csv")
    out = [[r5(a[0]), r5(a[1])]] + [[r5(x), r5(y)] for x, y in coords] + [[r5(b[0]), r5(b[1])]]
    out = [c for i, c in enumerate(out) if i == 0 or c != out[i - 1]]
    if snap["source"] == "inegi-river" and not river_named(snap["feature"], piece):
        sys.exit(f"{snap['journey']} {snap['from_seq']}: no INEGI toponym for {snap['feature']!r} within "
                 f"{RIVER_NAME_M} m of the traced line; raise min_order or check the name")
    return out, gaps


def drawn_traced(snap: dict, gaps: int) -> str:
    """How a narrated leg was drawn, in words, for the "How this line was drawn" section of its card."""
    how = SNAPS[snap["source"]]
    what = f"the {how['what']}"
    if snap["source"] == "inegi-river":
        text = (f"Traced along {snap['feature']} in {how['dataset']}: the main channel, its streams of Strahler "
                f"order {snap['min_order']} and up, which INEGI's place names label {snap['feature']}.")
    else:
        names = snap["feature"].split(";")
        names = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        text = f"Traced along {names} in {how['dataset']}."
    text += (f" The line follows {what} the shortest way from the point on it nearest one stop to the point nearest "
             f"the next, and runs straight from each stop to {what}.")
    if gaps:
        text += (f" The source breaks {what} in {'one place' if gaps == 1 else f'{gaps} places'}; each gap, under "
                 "about a kilometre, is closed with a straight line.")
    return text + (" The book names the way, but not every bend: today's line may differ from the 1940s one "
                   "(decision 0032).")


def feature(geometry: dict, **props) -> dict:
    return {"type": "Feature", "geometry": geometry, "properties": props}


def write_json(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def write(name: str, features: list[dict]) -> None:
    write_json(DATA / name, {"type": "FeatureCollection", "features": features})
    print(f"{name}: {len(features)} features")


def in_box(lat: float, lon: float) -> bool:
    return STORY_BOX[0] <= lon <= STORY_BOX[2] and STORY_BOX[1] <= lat <= STORY_BOX[3]


def build_places(picks: dict[str, dict]) -> tuple[list[dict], dict[str, tuple], list[dict]]:
    """Each place's pin: its override when there is one ("use", "exclude" or "unresolved"), else its gazetteer pick.

    Returns the place features, the pins by seed id (for stops at a place), and the places outside the story box.
    """
    overrides = {o["id"]: o for o in rows(SEEDS / "place-overrides.csv")}
    places, pins, elsewhere, unresolved = [], {}, [], []
    for seed in rows(SEEDS / "places.csv"):
        sid = seed["id"]
        override, pick = overrides.get(sid), picks.get(sid)
        if override:
            if override["action"] == "unresolved":
                unresolved.append(sid)
            if override["action"] != "use":
                continue
            src = override
        elif pick:
            src = pick
        else:
            sys.exit(f"{sid}: no pick in place-picks.csv and no override in place-overrides.csv")
        if not src["lat"]:
            print(f"skipped {sid}: no candidate")
            continue
        lat, lon = float(src["lat"]), float(src["lon"])
        if not in_box(lat, lon):
            elsewhere.append({"id": sid, "name": seed["name"], "first_seen": seed["first_seen"], "role": seed["role"]})
            continue
        pins[sid] = (lat, lon, src["source"], src["source_id"])
        provisional = pick and pick["status"] == "review" and seed["role"] != "context"
        reasoning = override["reasoning"] if override else (
            "Provisional pick from several candidates, awaiting review." if provisional else None)
        journeys = [j for j in seed["journey"].split(";") if j]
        # The book's own spellings, where they differ from the name, so translations can find the place in the text.
        in_text = {"name_in_text": seed["text_names"]} if seed["text_names"] else {}
        places.append(feature(
            point(lat, lon),
            id=f"place-{sid}", name=seed["name"], **in_text, kind=seed["kind"], role=seed["role"],
            characters=[c for c in seed["characters"].split(";") if c],
            journey=journeys[0] if journeys else None, part=int(seed["first_seen"][0]), episode=seed["first_seen"],
            first_seen=seed["first_seen"],
            certainty="located" if seed["kind"] in LOCATED_KINDS else "approximate",
            method="gazetteer", source=src["source"], source_id=src["source_id"],
            source_licence=LICENCE[src["source"]], note_safe="", reasoning=reasoning,
        ))
    if unresolved:
        print(f"{len(unresolved)} places left unresolved in place-overrides.csv: {', '.join(unresolved)}")
    return places, pins, sorted(elsewhere, key=lambda e: e["first_seen"])


def build_stops(pins: dict[str, tuple]) -> tuple[list[dict], list[dict], dict[str, list[dict]]]:
    """The stops, the inferred area around each stop with a radius, and each journey's stops for the routes."""
    stops, areas = [], []
    by_journey: dict[str, list[dict]] = {}
    # The drafted outlines (crossing.area_drafts, decision 0020); a stop without one keeps its circle.
    path = SEEDS / "areas.geojson"
    drafts = {f["properties"]["id"]: f for f in json.loads(path.read_text(encoding="utf-8"))["features"]} \
        if path.exists() else {}
    for s in rows(SEEDS / "stops.csv"):
        place = s["place"]
        if s["lat"]:
            lat, lon = float(s["lat"]), float(s["lon"])
            source, source_id = "this-site", None
        elif place in pins:
            lat, lon, source, source_id = pins[place]
        else:
            sys.exit(f"stop {s['id']}: no coordinates and place {place!r} has no pin")
        if s["certainty"] == "located" and not place:
            method = "computed"
        else:
            method = "gazetteer" if source != "this-site" else "schematic"
        props = dict(
            id=s["id"], name=s["name"], kind="stop", role="stop", characters=CHARACTERS[s["journey"]],
            journey=s["journey"], sequence=int(s["seq"]), place_ref=f"place-{place}" if place else None,
            part=int(s["first_seen"][0]), episode=s["first_seen"], first_seen=s["first_seen"], certainty=s["certainty"],
            uncertainty_m=float(s["radius_km"]) * 1000 if s["radius_km"] else None,
            method=method, source=source, source_id=source_id, source_licence=LICENCE[source],
            note_safe="", reasoning=s["reasoning"] or None,
        )
        stops.append(feature(point(lat, lon), **props))
        by_journey.setdefault(s["journey"], []).append(props | {"lat": lat, "lon": lon, "travel": s["travel"] or None})
        if s["radius_km"]:
            area = props | {"id": f"area-{s['id']}", "kind": "inferred-area",
                            "role": None, "sequence": None}
            ring = circle(lat, lon, float(s["radius_km"]))
            draft = drafts.get(area["id"])
            # A "kept" draft is the circle itself: nothing in the evidence cut it.
            if draft is None or draft["properties"]["draft_confidence"] == "kept":
                areas.append(feature(ring, **area, outline_rule=None, straight_road=False))
                continue
            # A draft is the circle cut down, so one reaching outside it was drafted around an older pin or radius.
            # make_valid: an outline saved from QGIS can have a self-touching ring.
            if not make_valid(shape(draft["geometry"])).difference(shape(ring).buffer(0.002)).is_empty:
                fix = ("redraw it in pipeline/qgis/areas.qgs, or clear its 'checked' mark and rerun "
                       "crossing.area_drafts --force" if draft["properties"]["draft_confidence"] == "checked"
                       else "rerun crossing.area_drafts --force")
                sys.exit(f"{area['id']}: the draft in areas.geojson lies outside the stop's circle; {fix}")
            areas.append(feature(draft["geometry"], **(area | {"method": "computed"}),
                                 outline_rule=draft["properties"]["draft_rule"],
                                 straight_road=draft["properties"]["straight_road"]))
    return stops, areas, by_journey


def regions() -> list[dict]:
    """The named regions, drafted by crossing.regions and checked by hand (decision 0008)."""
    out = []
    path = SEEDS / "regions.geojson"
    if not path.exists():  # a first build: crossing.regions drafts them from the places this build writes
        print(f"no {path.name} yet: run crossing.regions, then build again")
        return out
    for f in json.loads(path.read_text(encoding="utf-8"))["features"]:
        r = f["properties"]
        out.append(feature(f["geometry"], id=r["id"], name=r["name"], kind="region", role=None, characters=[],
                           journey=None, sequence=None, place_ref=f"place-{r['place']}", part=int(r["first_seen"][0]),
                           episode=r["first_seen"],
                           first_seen=r["first_seen"], certainty="approximate", uncertainty_m=None, method="computed",
                           source="this-site", source_id=None, source_licence=LICENCE["this-site"], note_safe="",
                           reasoning=r["reasoning"]))
    return out


def build_routes(by_journey: dict[str, list[dict]]) -> list[dict]:
    """A route segment between each pair of consecutive stops, and the false-dawn sightline."""
    journeys = []
    snaps = {(s["journey"], int(s["from_seq"])): s for s in rows(SEEDS / "snaps.csv")}
    modeled = least_cost.legs()
    for jid, seq in by_journey.items():
        seq.sort(key=lambda p: p["sequence"])
        for i, (a, b) in enumerate(zip(seq, seq[1:], strict=False), start=1):
            snap = snaps.get((jid, a["sequence"]))
            if snap:
                coords, gaps = snapped(snap, (a["lon"], a["lat"]), (b["lon"], b["lat"]))
                source = SNAPS[snap["source"]]["source"]
                how = dict(certainty="approximate", method="narrated-path", source=source,
                           source_licence=LICENCE[source], reasoning=snap["reasoning"],
                           drawn=drawn_traced(snap, gaps))
            elif (jid, a["sequence"]) in modeled:
                leg = modeled[(jid, a["sequence"])]
                path = least_cost.route((a["lon"], a["lat"]), (b["lon"], b["lat"]), leg)
                coords = path["coords"]
                who = "a wolf on foot" if leg["mode"] == "wolf" else "a rider at a walk"
                corridor = (", keeping near the roads and tracks" if leg.get("road")
                            else ", keeping to the river trail" if leg.get("river") else "")
                how = dict(certainty="inferred", method="modeled", source="this-site",
                           source_licence=LICENCE["this-site"], cost_model=least_cost.MODEL,
                           reasoning=f"A modelled path, not the book's: the book does not trace this stretch, so the "
                                     f"line is the way of least effort for {who} between the two stops over the "
                                     f"ground{corridor} (cost model {least_cost.MODEL}, decision 0021). It shows a "
                                     f"plausible way, not the one taken." + (f" {leg['note']}" if leg["note"] else ""),
                           drawn=least_cost.drawn(leg, path["res_m"]))
            else:
                coords = curve((a["lon"], a["lat"]), (b["lon"], b["lat"]), 1 if i % 2 else -1)
                reported = b["certainty"] == "reported"
                how = dict(certainty="reported" if reported else "inferred", method="schematic", source="this-site",
                           source_licence=LICENCE["this-site"],
                           reasoning="A gentle curve between consecutive stops; the book " +
                           ("only reports this leg, through someone's account (see the stop)." if reported
                            else "names no road or river for this stretch."),
                           drawn="A curve drawn between the two stops, bowed to one side by a tenth of its length "
                                 "(the side alternates from leg to leg so the journey does not read as one arc). It "
                                 "says only that the leg joins the stops: its shape is not evidence of the way.")
            journeys.append(feature(
                {"type": "LineString", "coordinates": coords},
                id=f"{jid.lower()}-seg-{i:02d}", name=f"{a['name']} to {b['name']}", kind="route-segment",
                characters=CHARACTERS[jid], journey=jid, sequence=i, part=int(b["first_seen"][0]),
                episode=b["first_seen"],
                first_seen=b["first_seen"], travel=b["travel"], note_safe="", **how,
            ))
    last = max(by_journey["J7"], key=lambda p: p["sequence"])
    azimuth = GEOD.inv(last["lon"], last["lat"], *TRINITY)[0]
    lon, lat, _ = GEOD.fwd(last["lon"], last["lat"], azimuth, SIGHTLINE_KM * 1000)
    journeys.append(feature(
        {"type": "LineString", "coordinates": [[r5(last["lon"]), r5(last["lat"])], [r5(lon), r5(lat)]]},
        id="j7-false-dawn", name="The false dawn", kind="sightline", characters=["billy"], journey="J7", sequence=None,
        part=4, episode=FALSE_DAWN, first_seen=FALSE_DAWN, travel=None, note_safe="",
        certainty="reported", method="computed", source="this-site", source_licence=LICENCE["this-site"],
        reasoning=f"In the last episode Billy wakes in the night to a light like desert noon, which fades; the true "
                  f"dawn comes later. The book names no place, event or direction for that light; it is widely read as "
                  f"the Trinity test of 16 July 1945. The line points from his last stop towards the "
                  f"Trinity Site (Wikidata Q19842077), bearing {azimuth % 360:.0f} degrees (pyproj, WGS 84), and is "
                  f"{SIGHTLINE_KM} km long only to show the direction."))
    return journeys


def main() -> None:
    picks = {p["id"]: p for p in rows(SEEDS / "place-picks.csv")}
    places, pins, elsewhere = build_places(picks)
    write("places.geojson", places)
    write_json(DATA / "elsewhere.json", elsewhere)
    stops, areas, by_journey = build_stops(pins)
    write("stops.geojson", stops)
    write("areas.geojson", areas + regions())
    write("journeys.geojson", build_routes(by_journey))
    for checklist in CHECKLISTS:
        listed = [f for f in places if f["properties"]["id"].removeprefix("place-") not in picks
                  and f["properties"]["episode"][0] in checklist["parts"]]
        write_checklist(checklist, [f for f in stops if f["properties"]["episode"][0] in checklist["parts"]], listed)


TICKED = re.compile(r"^\| \[[xX]\] \| ([^|]*) \| ([^|]*) \|")


def ticked(path: Path) -> set[tuple[str, str]]:
    """The (label, name) of every row already ticked in a checklist, so a rebuild keeps the owner's sign-off."""
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {(m[1].strip(), m[2].strip()) for line in lines if (m := TICKED.match(line))}


def write_checklist(batch: dict, stops: list[dict], places: list[dict]) -> None:
    """A batch's sign-off list: every feature, its evidence, and links to check it on imagery."""
    done = ticked(batch["path"])

    def links(f: dict) -> str:
        lon, lat = f["geometry"]["coordinates"]
        return (f"[OSM](https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=13/{lat}/{lon}) · "
                f"[satellite](https://www.google.com/maps/@{lat},{lon},13z/data=!3m1!1e3)")

    def provisional(p: dict) -> bool:
        return "Provisional" in (p.get("reasoning") or "")

    unsure = {f["properties"]["id"] for f in places if provisional(f["properties"])}

    def row(f: dict, label: str) -> str:
        p = f["properties"]
        source = p["source"] + (f" {p['source_id']}" if p.get("source_id") else "")
        flag = "**check**" if provisional(p) or p.get("place_ref") in unsure else ""
        box = "[x]" if (label, p["name"]) in done else "[ ]"
        return f"| {box} | {label} | {p['name']} | {p['certainty']} | {source} | {links(f)} | {flag} |"

    lines = [
        f"# {batch['title']}",
        "",
        "Generated by `pipeline/src/crossing/build_story.py`, which keeps ticked rows. Tick each row once the point "
        "sits where the book puts it.",
        "Rows marked **check** are provisional picks among several candidates. Reasoning for every stop is in the "
        "app's panel.",
        "",
        "| OK | # | Name | Certainty | Source | Look | |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in stops:
        lines.append(row(f, f"{f['properties']['journey']}.{f['properties']['sequence']}"))
    lines += ["", "## Places named in passing", "", "| OK | # | Name | Certainty | Source | Look | |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for f in places:
        if f["properties"]["role"] == "passing":
            lines.append(row(f, ""))
    path = batch["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{path.relative_to(REPO)}: {len(stops)} stops")


if __name__ == "__main__":
    main()


