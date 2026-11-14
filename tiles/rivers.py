"""The base map's river layers: each named river traced through the national 1:50,000 and 1:24,000 networks.

Called by tiles/build_base.py. Natural Earth's rivers are a 1:10 million generalisation: they cross contours and
miss valleys at the zooms the map is read at, and in Sonora some names are wrong (the Bavispe below La Angostura is
labelled "Yaqui", though the Yaqui only begins where the Aros joins it, at 29.53 N 109.24 W; GeoNames 4017237 and
4018306; Wikipedia, "Bavispe River"). So Natural Earth only decides which rivers are shown, how strongly and under
what name; the line itself comes from a detailed network wherever one covers the ground:
  - Mexico: INEGI's Red Hidrográfica 1:50,000 (edición 2.0), one zip per hydrological region. Its lines carry
    no names; ORDER_1 is the Strahler order. The channel of a wide river is a centre line (`LINEA CENTRAL`),
    kept with the ordinary streams (`CORRIENTE DE AGUA`): without it the main stems are missing.
  - The US: USGS NHD High Resolution, one zip per HU8 watershed, streams and the artificial paths through lakes
    and wide channels (ftype 460 and 558), with their GNIS names. Its value-added table (NHDFlowlineVAA) ships
    empty, so the Strahler order is computed here from how the lines join, as they are digitised downstream.
Each named Natural Earth river, its names corrected first, is traced through the combined network as the cheapest
path between its two ends. The cost favours the main stem (high Strahler order, and on NHD a GNIS name that
matches) and stays near Natural Earth's line without being tied to it. Natural Earth's own line is the fallback
where the network breaks, as at reservoirs.
"""

import json
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import box, mapping, shape
from shapely.ops import linemerge, unary_union

REPO = Path(__file__).resolve().parents[1]
INEGI = REPO / "private" / "cache" / "hydro" / "inegi"
NHD = REPO / "private" / "cache" / "hydro" / "nhd"
NE = REPO / "private" / "cache" / "basemap"
# The Aros-Bavispe confluence: Natural Earth's "Yaqui" north of it is the Bavispe.
YAQUI_STARTS = 29.53
# Channels of this Strahler order and up form the network the rivers are traced through.
MIN_ORDER = 3
# A channel this far from Natural Earth's line (degrees, about 2 km) costs twice its length; the cost grows with
# the square of the distance. Loose enough for the main stem, which can lie a few km from the generalised line.
HOLD = 0.02
# Each Strahler order above MIN_ORDER divides a channel's cost by this, so the trace keeps to the main stem
# rather than a side channel that happens to run closer to Natural Earth's line.
ORDER_PREFERENCE = 2.0
# On NHD, a channel whose GNIS name contains the river's name costs this much (a fraction) of what it would.
NAME_PREFERENCE = 0.5
# Endpoints closer than this (degrees, about 10 m) are one node of the network.
SNAP = 1e-4
# Dangling channel ends are joined to nodes this close (degrees, about 300 m).
GAP = 0.003
# Natural Earth's own line costs this many times its length at MIN_ORDER, so a traced river leaves the
# network only where it breaks.
FALLBACK = 4
# Only the network within this distance of a river's line (degrees, about 15 km) is searched.
SEARCH = 0.15


def read(source: str, sql: str, bbox: list[str], tmp: Path, name: str, latin1: bool = False) -> list[dict]:
    out = tmp / f"{name}.geojson"
    # INEGI's attribute tables are Latin-1; GeoJSON comes out as UTF-8.
    encoding = ["--config", "SHAPE_ENCODING", "ISO-8859-1"] if latin1 else []
    subprocess.run(["ogr2ogr", *encoding, "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-spat", *bbox, "-dialect", "OGRSQL",
                    "-sql", sql, "-dim", "XY", str(out), source], check=True, capture_output=True)
    return [f for f in json.loads(out.read_text())["features"] if f["geometry"]]


def ne_rivers(layer: str, bbox: list[str], tmp: Path) -> list[tuple[shapely.Geometry, dict]]:
    """A Natural Earth river layer with the Bavispe named down to the Aros."""
    out = []
    for f in read(str(NE / layer / f"{layer}.shp"), f"SELECT name, scalerank FROM {layer}", bbox, tmp, layer):
        geom, props = shape(f["geometry"]), f["properties"]
        if props.get("name") == "Yaqui":
            north = box(-180, YAQUI_STARTS, 180, 90)
            for part, name in ((geom.intersection(north), "Bavispe"), (geom.difference(north), "Yaqui")):
                if not part.is_empty:
                    out.append((part, props | {"name": name}))
        else:
            out.append((geom, props))
    return out


def segments(geom: shapely.Geometry) -> list[shapely.LineString]:
    return [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "LineString" and len(g.coords) > 1]


def inegi(bbox: list[str], tmp: Path) -> tuple[list[shapely.Geometry], list[tuple[shapely.LineString, int, str]]]:
    """INEGI's sub-basins in the box, and its channels of MIN_ORDER and up as (line, order, name '')."""
    basins, lines = [], []
    for i, zip_path in enumerate(sorted(INEGI.glob("*.zip"))):
        names = [n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith(("_subc.shp", "_hl.shp"))]
        for j, name in enumerate(names):
            layer, source = Path(name).stem, f"/vsizip/{zip_path}/{name}"
            if name.endswith("_subc.shp"):
                basins += [shape(f["geometry"]).buffer(0) for f in read(source, f"SELECT CVE_SUBC FROM {layer}", bbox, tmp, f"ib{i}-{j}", latin1=True)]
            else:
                sql = (f"SELECT ORDER_1 FROM {layer} WHERE ENTIDAD IN ('CORRIENTE DE AGUA', 'LINEA CENTRAL') "
                       f"AND ORDER_1 >= {MIN_ORDER}")
                for f in read(source, sql, bbox, tmp, f"ih{i}-{j}", latin1=True):
                    lines += [(g, int(f["properties"]["ORDER_1"]), "") for g in segments(shape(f["geometry"]))]
    return basins, lines


def strahler(lines: list[shapely.LineString]) -> np.ndarray:
    """The Strahler order of each line of a network digitised downstream: 1 at a source; where lines meet, the
    highest order coming in, plus one if two or more lines bring it. Lines in loops (braids, which are rare)
    take the order of what flows into them."""
    ends = np.array([[g.coords[0], g.coords[-1]] for g in lines]).reshape(-1, 2)
    _, node = np.unique(np.round(ends / SNAP).astype(np.int64), axis=0, return_inverse=True)
    start, end = node.reshape(-1, 2).T
    n = node.max() + 1
    incoming = [[] for _ in range(n)]
    for e, t in enumerate(end):
        incoming[t].append(e)
    leaving = [[] for _ in range(n)]
    for e, s in enumerate(start):
        leaving[s].append(e)
    waiting = np.array([len(x) for x in incoming])
    order = np.zeros(len(lines), dtype=int)
    ready = list(np.flatnonzero(waiting == 0))
    done = np.zeros(n, dtype=bool)
    while True:
        while ready:
            v = ready.pop()
            done[v] = True
            got = [order[e] for e in incoming[v]]
            m = max(got, default=0)
            o = 1 if m == 0 else m + (got.count(m) >= 2)
            for e in leaving[v]:
                order[e] = o
                t = end[e]
                waiting[t] -= 1
                if waiting[t] == 0:
                    ready.append(t)
        # A loop stops the walk; release its node with the highest order known so far coming in.
        stuck = [v for v in np.flatnonzero(~done & (waiting > 0)) if any(order[e] for e in incoming[v])]
        if not stuck:
            break
        v = max(stuck, key=lambda v: max(order[e] for e in incoming[v]))
        waiting[v] = 0
        ready.append(v)
    return order


def nhd(bbox: list[str], tmp: Path) -> tuple[list[shapely.Geometry], list[tuple[shapely.LineString, int, str]]]:
    """NHD's HU8 watersheds in the box, and its streams of MIN_ORDER and up as (line, order, GNIS name)."""
    basins, flowlines = [], []
    for i, shp_dir in enumerate(sorted(NHD.glob("*/Shape"))):
        basins += [shape(f["geometry"]).buffer(0) for f in read(str(shp_dir / "WBDHU8.shp"), "SELECT huc8 FROM WBDHU8", bbox, tmp, f"nb{i}")]
        # Every stream is read, not only the larger ones, as the order depends on the whole network upstream.
        for f in read(str(shp_dir / "NHDFlowline.shp"), "SELECT gnis_name FROM NHDFlowline WHERE ftype IN (460, 558)",
                      bbox, tmp, f"nf{i}"):
            flowlines += [(g, f["properties"]["gnis_name"] or "") for g in segments(shape(f["geometry"]))]
    if not flowlines:
        return basins, []
    order = strahler([g for g, _ in flowlines])
    lines = [(g, int(o), name) for (g, name), o in zip(flowlines, order) if o >= MIN_ORDER]
    return basins, lines


class Network:
    """Channels as a graph: nodes are segment ends, edges the segments, each with its Strahler order and name.
    The networks break at reservoirs, between sub-basins and at the border, so dangling ends are joined to any
    node within GAP, and each traced river may also run along its own Natural Earth line, at FALLBACK times the
    length, where the network has no channel."""

    def __init__(self, lines: list[tuple[shapely.LineString, int, str]]):
        geoms = [g for g, _, _ in lines]
        ends = np.array([[g.coords[0], g.coords[-1]] for g in geoms]).reshape(-1, 2)
        _, node = np.unique(np.round(ends / SNAP).astype(np.int64), axis=0, return_inverse=True)
        node = node.reshape(-1)
        self.nodes = np.zeros((node.max() + 1, 2))
        self.nodes[node] = ends
        edges = node.reshape(-1, 2)
        orders = [o for _, o, _ in lines]
        names = [n.lower() for _, _, n in lines]
        degree = np.bincount(edges.ravel(), minlength=len(self.nodes))
        tree = cKDTree(self.nodes)
        joined = {tuple(e) for e in edges} | {tuple(e[::-1]) for e in edges}
        extra = []
        for i in np.flatnonzero(degree == 1):
            for j in tree.query_ball_point(self.nodes[i], GAP):
                if j != i and (i, j) not in joined:
                    extra.append((i, j))
                    joined |= {(i, j), (j, i)}
                    geoms.append(shapely.LineString([self.nodes[i], self.nodes[j]]))
                    orders.append(MIN_ORDER)
                    names.append("")
        self.edges = np.vstack([edges, np.array(extra, dtype=edges.dtype).reshape(-1, 2)])
        self.geoms = geoms
        self.orders = np.array(orders, dtype=float)
        self.names = names
        self.lengths = np.array([g.length for g in geoms])
        self.mids = shapely.points([g.interpolate(0.5, normalized=True).coords[0] for g in geoms])
        self.index = shapely.STRtree(geoms)
        self.tree = tree

    def trace(self, river: shapely.LineString, name: str) -> shapely.Geometry | None:
        """The channels that follow one connected Natural Earth line, end to end."""
        near = self.index.query(river.buffer(SEARCH))
        if len(near) == 0:
            return None
        weight = ORDER_PREFERENCE ** -(self.orders[near] - MIN_ORDER)
        if name:
            key = name.lower()
            weight = weight * np.where([key in self.names[k] for k in near], NAME_PREFERENCE, 1.0)
        cost = self.lengths[near] * (1 + (shapely.distance(self.mids[near], river) / HOLD) ** 2) * weight
        # Renumber the nodes of the nearby edges, then add the river's own vertices as fallback nodes.
        local, inverse = np.unique(self.edges[near].ravel(), return_inverse=True)
        eu, ev = inverse.reshape(-1, 2).T
        n0 = len(local)
        coords = np.array(river.coords)
        rid = np.arange(n0, n0 + len(coords))
        seg = [shapely.LineString(coords[k:k + 2]) for k in range(len(coords) - 1)]
        sub = cKDTree(self.nodes[local])
        dist, tie_to = sub.query(coords)
        tie = [shapely.LineString([coords[k], self.nodes[local[tie_to[k]]]]) for k in range(len(coords))]
        geoms = [self.geoms[k] for k in near] + seg + tie
        u = np.concatenate([eu, rid[:-1], rid])
        v = np.concatenate([ev, rid[1:], tie_to])
        c = np.concatenate([cost, np.array([s.length for s in seg]) * FALLBACK, np.maximum(dist, 1e-6) * FALLBACK])
        n = n0 + len(coords)
        graph = coo_matrix((np.r_[c, c], (np.r_[u, v], np.r_[v, u])), shape=(n, n)).tocsr()
        start, end = int(rid[0]), int(rid[-1])
        d, pred = dijkstra(graph, indices=start, return_predecessors=True)
        if not np.isfinite(d[end]):
            return None
        best = {}
        for k in np.argsort(c)[::-1]:
            best[(u[k], v[k])] = best[(v[k], u[k])] = k
        steps, node = [], end
        while node != start:
            prev = pred[node]
            steps.append((prev, node, best[(prev, node)]))
            node = prev
        steps.reverse()
        # The straight ties from Natural Earth's two ends to the network are only a way in and out: drawn, they
        # would show as spurs where Natural Earth's end lies off the channel.
        first_tie = len(near) + len(seg)
        while steps and steps[0][2] >= first_tie:
            steps.pop(0)
        while steps and steps[-1][2] >= first_tie:
            steps.pop()
        if not steps:
            return None
        # One line, each step turned to run downstream of the last; channel ends can sit a few metres off the
        # node they were snapped to, so the steps are chained by order rather than merged by touching ends.
        pos = np.vstack([self.nodes[local], coords])
        out: list[tuple[float, float]] = []
        for prev, _, k in steps:
            xy = list(geoms[k].coords)
            if np.hypot(*(np.array(xy[0]) - pos[prev])) > np.hypot(*(np.array(xy[-1]) - pos[prev])):
                xy.reverse()
            out += xy if not out else xy[1:]
        return shapely.LineString(out)


def write_layers(bbox: list[str], tmp: Path) -> dict[str, Path]:
    """river.geojson and river_minor.geojson in tmp, for tippecanoe."""
    mx_basins, mx_lines = inegi(bbox, tmp)
    us_basins, us_lines = nhd(bbox, tmp)
    coverage = unary_union(mx_basins + us_basins).buffer(0.001)
    network = Network(mx_lines + us_lines)
    print(f"rivers: network of {len(mx_lines)} INEGI and {len(us_lines)} NHD channels")
    major, minor = ne_rivers("ne_10m_rivers_lake_centerlines", bbox, tmp), ne_rivers("ne_10m_rivers_north_america", bbox, tmp)
    layers: dict[str, list[dict]] = {"river": [], "river_minor": []}
    traced = Counter()
    for layer, rivers in (("river", major), ("river_minor", minor)):
        for geom, props in rivers:
            rest = geom.difference(coverage)
            if not rest.is_empty:
                layers[layer].append({"type": "Feature", "geometry": mapping(rest), "properties": props | {"source": "ne"}})
            inside = geom.intersection(coverage)
            if inside.is_empty or not props.get("name"):
                continue
            merged = linemerge(inside) if inside.geom_type == "MultiLineString" else inside
            for part in getattr(merged, "geoms", [merged]):
                if part.geom_type != "LineString" or part.length < 0.02:
                    continue
                if (path := network.trace(part, props["name"])) is not None:
                    layers[layer].append({"type": "Feature", "geometry": mapping(path), "properties": props | {"source": "traced"}})
                    traced[props["name"]] += 1
    out = {}
    for layer, features in layers.items():
        out[layer] = tmp / f"{layer}.geojson"
        out[layer].write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print("rivers:", {k: dict(Counter(f["properties"]["source"] for f in v)) for k, v in layers.items()},
          "traced:", dict(traced))
    return out
