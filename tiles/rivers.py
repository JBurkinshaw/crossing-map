"""The base map's river layers: each named river traced through the national 1:50,000 and 1:24,000 networks.

Called by tiles.build_base. Natural Earth's rivers are a 1:10 million generalisation: they cross contours and
miss valleys at the zooms the map is read at, and in Sonora some names are wrong (the Bavispe below La Angostura is
labelled "Yaqui", though the Yaqui only begins where the Aros joins it, at 29.53 N 109.24 W; GeoNames 4017237 and
4018306; Wikipedia, "Bavispe River"). So Natural Earth only decides which rivers are shown, how strongly and under
what name; the line itself comes from a detailed network (crossing.hydro: INEGI in Mexico, NHD in the US)
wherever one covers the ground. Each named Natural Earth river, its names corrected first, is traced through the
combined network as the cheapest path between its two ends. The cost favours the main stem (high Strahler order,
and on NHD a GNIS name that matches) and stays near Natural Earth's line without being tied to it. Natural Earth's
own line is the fallback where the network breaks, as at reservoirs.
"""

import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import mapping, shape
from shapely.ops import linemerge, unary_union

from crossing.basemap import BASEMAP, corrected_names
from crossing.hydro import SNAP, Hydro
from crossing.vector import chaikin, read, segments

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
# Dangling channel ends are joined to nodes this close (degrees, about 300 m).
GAP = 0.003
# Natural Earth's own line costs this many times its length at MIN_ORDER, so a traced river leaves the
# network only where it breaks.
FALLBACK = 4
# Only the network within this distance of a river's line (degrees, about 15 km) is searched.
SEARCH = 0.15
# A traced river meanders too tightly for a name to fit along it, so names follow a copy simplified to this
# tolerance (degrees, about 400 m) and rounded (crossing.vector.chaikin).
LABEL_SIMPLIFY = 0.004


def ne_rivers(layer: str, bbox: Sequence, tmp: Path) -> list[tuple[shapely.Geometry, dict]]:
    """A Natural Earth river layer with the Bavispe named down to the Aros."""
    out = []
    sql = f"SELECT name, scalerank FROM {layer}"
    for f in read(BASEMAP / layer / f"{layer}.shp", sql, bbox, tmp / f"{layer}.geojson"):
        props = f["properties"]
        for part, name in corrected_names(shape(f["geometry"]), props.get("name")):
            out.append((part, props if name == props.get("name") else props | {"name": name}))
    return out


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

    def trace(self, river: shapely.LineString, name: str) -> tuple[shapely.LineString, float] | None:
        """The channels that follow one connected Natural Earth line, end to end, and how much of the path
        (degrees) is Natural Earth's own line, where the network had no way through."""
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
        fallback = sum(geoms[k].length for _, _, k in steps if len(near) <= k < first_tie)
        return shapely.LineString(out), fallback


def label_line(geom: shapely.Geometry) -> shapely.Geometry:
    simple = segments(geom.simplify(LABEL_SIMPLIFY, preserve_topology=False))
    parts = [shapely.LineString(chaikin(g.coords)) for g in simple]
    return shapely.MultiLineString(parts) if len(parts) != 1 else parts[0]


def write_layers(hydro: Hydro, bbox: Sequence, tmp: Path) -> dict[str, Path]:
    """river.geojson and river_minor.geojson in tmp, for tippecanoe, and river_label.geojson: every named river's
    line, simplified and rounded for its name, with `rank` major (Natural Earth's main rivers) or minor."""
    # Only channels of MIN_ORDER and up form the network the rivers are traced through.
    mx_lines = [(g, o, "") for g, o, _ in hydro.inegi_lines if o >= MIN_ORDER]
    us_lines = [(g, o, name) for g, o, _, name in hydro.nhd_lines if o >= MIN_ORDER]
    coverage = unary_union(hydro.inegi_basins + hydro.nhd_basins).buffer(0.001)
    network = Network(mx_lines + us_lines)
    print(f"rivers: network of {len(mx_lines)} INEGI and {len(us_lines)} NHD channels")
    major = ne_rivers("ne_10m_rivers_lake_centerlines", bbox, tmp)
    minor = ne_rivers("ne_10m_rivers_north_america", bbox, tmp)
    layers: dict[str, list[dict]] = {"river": [], "river_minor": []}
    traced = Counter()
    fallback = Counter()
    for layer, rivers in (("river", major), ("river_minor", minor)):
        for geom, props in rivers:
            rest = geom.difference(coverage)
            if not rest.is_empty:
                feature = {"type": "Feature", "geometry": mapping(rest), "properties": props | {"source": "ne"}}
                layers[layer].append(feature)
            inside = geom.intersection(coverage)
            if inside.is_empty or not props.get("name"):
                continue
            merged = linemerge(inside) if inside.geom_type == "MultiLineString" else inside
            for part in getattr(merged, "geoms", [merged]):
                if part.geom_type != "LineString" or part.length < 0.02:
                    continue
                if (result := network.trace(part, props["name"])) is not None:
                    path, gap = result
                    fallback[props["name"]] += gap * 100
                    props_traced = props | {"source": "traced"}
                    layers[layer].append({"type": "Feature", "geometry": mapping(path), "properties": props_traced})
                    traced[props["name"]] += 1
    layers["river_label"] = [
        {"type": "Feature", "geometry": mapping(label_line(shape(f["geometry"]))),
         "properties": {"name": f["properties"]["name"], "rank": "major" if layer == "river" else "minor"}}
        for layer in ("river", "river_minor") for f in layers[layer] if f["properties"].get("name")
    ]
    out = {}
    for layer, features in layers.items():
        out[layer] = tmp / f"{layer}.geojson"
        out[layer].write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print("rivers:", {k: dict(Counter(f["properties"]["source"] for f in layers[k])) for k in ("river", "river_minor")},
          "traced:", dict(traced))
    # Where the network breaks, a river runs along Natural Earth's line instead: the km it does so, by river.
    print(f"rivers: {sum(fallback.values()):.0f} km on Natural Earth's line where the network breaks; most:",
          ", ".join(f"{n} {km:.0f}" for n, km in fallback.most_common(8)))
    return out
