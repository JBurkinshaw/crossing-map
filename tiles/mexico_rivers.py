"""The base map's river layers: INEGI's 1:50,000 network inside the basins it covers, Natural Earth elsewhere.

Called by tiles/build_base.py. Natural Earth's rivers are a 1:10 million generalisation, and in Sonora their names
are wrong in places: the Bavispe below La Angostura is labelled "Yaqui", though the Yaqui only begins where the Aros
joins the Bavispe, at 29.53 N 109.24 W (GeoNames 4017237 and 4018306; Wikipedia, "Bavispe River"). Where the INEGI
Red Hidrográfica (RH09 Sonora Sur, RH34 Cuencas Cerradas del Norte) covers the ground, its channels replace Natural
Earth's geometry. Natural Earth still decides which rivers are shown, how strongly and under what name (INEGI's
lines carry no names, and its Strahler orders restart in each sub-basin): each named Natural Earth river, its names
corrected first, is traced through INEGI's network as the shortest path between its two ends, with a cost that
keeps the path close to Natural Earth's line.
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
NE = REPO / "private" / "cache" / "basemap"
# The Aros-Bavispe confluence: Natural Earth's "Yaqui" north of it is the Bavispe.
YAQUI_STARTS = 29.53
# Channels of this Strahler order and up form the network the rivers are traced through.
MIN_ORDER = 3
# How strongly a traced path is held to Natural Earth's line: a channel this far from it (degrees, about 1 km)
# costs twice its length, and the cost grows with the square of the distance.
HOLD = 0.01
# Endpoints closer than this (degrees, about 10 m) are one node of the network.
SNAP = 1e-4
# Dangling channel ends are joined to nodes this close (degrees, about 300 m).
GAP = 0.003
# Natural Earth's own line costs this many times its length, so a traced river leaves INEGI's channels only where
# they break, as at La Angostura reservoir.
FALLBACK = 4


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


def inegi(bbox: list[str], tmp: Path) -> tuple[shapely.Geometry, list[shapely.LineString]]:
    """The area INEGI's sub-basins cover, and its channels of MIN_ORDER and up, one line per segment."""
    basins, lines = [], []
    for i, zip_path in enumerate(sorted(INEGI.glob("*.zip"))):
        for j, name in enumerate(n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith(("_subc.shp", "_hl.shp"))):
            layer, source = Path(name).stem, f"/vsizip/{zip_path}/{name}"
            if name.endswith("_subc.shp"):
                basins += [shape(f["geometry"]) for f in read(source, f"SELECT CVE_SUBC FROM {layer}", bbox, tmp, f"b{i}-{j}", latin1=True)]
            else:
                for f in read(source, f"SELECT ORDER_1 FROM {layer} WHERE ENTIDAD = 'CORRIENTE DE AGUA' AND ORDER_1 >= {MIN_ORDER}",
                              bbox, tmp, f"h{i}-{j}", latin1=True):
                    geom = shape(f["geometry"])
                    lines += list(getattr(geom, "geoms", [geom]))
    return unary_union([b.buffer(0) for b in basins]).buffer(0.001), lines


class Network:
    """INEGI's channels as a graph: nodes are segment ends, edges the segments. The channels break at reservoirs
    and between sub-basins, so dangling ends are joined to any node within GAP, and each traced river may also run
    along its own Natural Earth line, at FALLBACK times the length, where INEGI has no channel."""

    def __init__(self, lines: list[shapely.LineString]):
        ends = np.array([[ln.coords[0], ln.coords[-1]] for ln in lines]).reshape(-1, 2)
        _, node = np.unique(np.round(ends / SNAP).astype(np.int64), axis=0, return_inverse=True)
        node = node.reshape(-1)
        self.nodes = np.zeros((node.max() + 1, 2))
        self.nodes[node] = ends
        edges = node.reshape(-1, 2)
        geoms = list(lines)
        # Join each dangling end to the nearest other node within GAP that it is not already joined to.
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
        self.edges = np.vstack([edges, np.array(extra, dtype=edges.dtype).reshape(-1, 2)])
        self.geoms = geoms
        self.lengths = np.array([g.length for g in geoms])
        self.mids = shapely.points([g.interpolate(0.5, normalized=True).coords[0] for g in geoms])
        self.tree = tree

    def trace(self, river: shapely.LineString) -> shapely.Geometry | None:
        """The channels that follow one connected Natural Earth line, end to end."""
        n0 = len(self.nodes)
        # The river's own line as a fallback: its vertices as new nodes, each tied to the nearest channel node.
        coords = np.array(river.coords)
        rid = np.arange(n0, n0 + len(coords))
        geoms = list(self.geoms)
        eu, ev, ec = [self.edges[:, 0]], [self.edges[:, 1]], [self.lengths * (1 + (shapely.distance(self.mids, river) / HOLD) ** 2)]
        seg = [shapely.LineString(coords[k:k + 2]) for k in range(len(coords) - 1)]
        geoms += seg
        eu.append(rid[:-1]); ev.append(rid[1:]); ec.append(np.array([s.length for s in seg]) * FALLBACK)
        dist, near = self.tree.query(coords)
        tie = [shapely.LineString([coords[k], self.nodes[near[k]]]) for k in range(len(coords))]
        geoms += tie
        eu.append(rid); ev.append(near); ec.append(np.maximum(dist, 1e-6) * FALLBACK)
        u, v, cost = np.concatenate(eu), np.concatenate(ev), np.concatenate(ec)
        n = n0 + len(coords)
        graph = coo_matrix((np.r_[cost, cost], (np.r_[u, v], np.r_[v, u])), shape=(n, n)).tocsr()
        start, end = int(rid[0]), int(rid[-1])
        d, pred = dijkstra(graph, indices=start, return_predecessors=True)
        if not np.isfinite(d[end]):
            return None
        best = {}
        for k in np.argsort(cost)[::-1]:
            best[(u[k], v[k])] = best[(v[k], u[k])] = k
        path, node = [], end
        while node != start:
            prev = pred[node]
            path.append(geoms[best[(prev, node)]])
            node = prev
        merged = linemerge(path)
        return merged


def write_layers(bbox: list[str], tmp: Path) -> dict[str, Path]:
    """river.geojson and river_minor.geojson in tmp, for tippecanoe."""
    coverage, channels = inegi(bbox, tmp)
    network = Network(channels)
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
                if (path := network.trace(part)) is not None:
                    layers[layer].append({"type": "Feature", "geometry": mapping(path), "properties": props | {"source": "inegi"}})
                    traced[props["name"]] += 1
    out = {}
    for layer, features in layers.items():
        out[layer] = tmp / f"{layer}.geojson"
        out[layer].write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print("rivers:", {k: dict(Counter(f["properties"]["source"] for f in v)) for k, v in layers.items()},
          "traced through INEGI:", dict(traced))
    return out
