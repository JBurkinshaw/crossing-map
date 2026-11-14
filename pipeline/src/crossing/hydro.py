"""The two national stream networks the base map draws from, read once per build.

  - Mexico: INEGI's Red Hidrográfica 1:50,000 (edición 2.0), one zip per hydrological region. Its lines carry
    no names; ORDER_1 is the Strahler order. The channel of a wide river is a centre line (`LINEA CENTRAL`),
    kept with the ordinary streams (`CORRIENTE DE AGUA`): without it the main stems are missing. The toponym
    layer (`_to`) names streams with one point per name.
  - The US: USGS NHD High Resolution, one zip per HU8 watershed, streams and the artificial paths through lakes
    and wide channels (ftype 460 and 558), with their GNIS names. Its value-added table (NHDFlowlineVAA) ships
    empty, so the Strahler order is computed here from how the lines join, as they are digitised downstream.
"""

import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import shape

from crossing.paths import CACHE
from crossing.vector import read, segments

INEGI = CACHE / "hydro" / "inegi"
NHD = CACHE / "hydro" / "nhd"
# Endpoints closer than this (degrees, about 10 m) are one node of a network.
SNAP = 1e-4
# NHD fcodes of intermittent (46003) and ephemeral (46007) streams.
NHD_INTERMITTENT = (46003, 46007)


@dataclass
class Hydro:
    """Both networks inside one box, in WGS 84."""

    inegi_basins: list[shapely.Geometry]
    # (line, Strahler order, intermittent)
    inegi_lines: list[tuple[shapely.LineString, int, bool]]
    # (lon/lat, generic term, name) from INEGI's toponym layer
    inegi_toponyms: list[tuple[list[float], str, str]]
    nhd_basins: list[shapely.Geometry]
    # (line, computed Strahler order, intermittent, GNIS name or "")
    nhd_lines: list[tuple[shapely.LineString, int, bool, str]]


def nodes(lines: list[shapely.LineString]) -> np.ndarray:
    """Each line's start and end node, as an (n, 2) array: ends within SNAP of each other share a node."""
    ends = np.array([[g.coords[0], g.coords[-1]] for g in lines]).reshape(-1, 2)
    _, node = np.unique(np.round(ends / SNAP).astype(np.int64), axis=0, return_inverse=True)
    return node.reshape(-1, 2)


def strahler(lines: list[shapely.LineString]) -> np.ndarray:
    """The Strahler order of each line of a network digitised downstream: 1 at a source; where lines meet, the
    highest order coming in, plus one if two or more lines bring it from different sources. A stream that splits
    and joins itself again keeps its order: NHD's braided channels, irrigation ditches and the few lines repeated
    in two watersheds would otherwise add one at every rejoin, and orders reach the hundreds along the Rio Grande,
    which would make those channels nearly free to the trace. Each order is tagged with the node where it was
    reached; two equal orders meeting raise it only if they were reached at different nodes. Lines in loops take
    the order of what flows into them."""
    start, end = nodes(lines).T
    n = max(start.max(), end.max()) + 1
    incoming = [[] for _ in range(n)]
    for e, t in enumerate(end):
        incoming[t].append(e)
    leaving = [[] for _ in range(n)]
    for e, s in enumerate(start):
        leaving[s].append(e)
    waiting = np.array([len(x) for x in incoming])
    order = np.zeros(len(lines), dtype=int)
    origin = np.full(len(lines), -1)
    ready = list(np.flatnonzero(waiting == 0))
    done = np.zeros(n, dtype=bool)
    while True:
        while ready:
            v = ready.pop()
            done[v] = True
            got = [(order[e], origin[e]) for e in incoming[v] if order[e]]
            m = max((o for o, _ in got), default=0)
            sources = {s for o, s in got if o == m}
            if m == 0:
                o, src = 1, v
            elif len(sources) >= 2:
                o, src = m + 1, v
            else:
                o, src = m, sources.pop()
            for e in leaving[v]:
                order[e], origin[e] = o, src
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


def load_inegi(bbox: Sequence, tmp: Path) -> tuple[list, list, list]:
    """INEGI's sub-basins, streams and stream toponyms in the box, from every region zip in the cache."""
    basins, lines, toponyms = [], [], []
    for i, zip_path in enumerate(sorted(INEGI.glob("*.zip"))):
        names = [n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith(("_subc.shp", "_hl.shp", "_to.shp"))]
        for j, name in enumerate(names):
            layer, source = Path(name).stem, f"/vsizip/{zip_path}/{name}"
            out = tmp / f"inegi-{i}-{j}.geojson"
            if name.endswith("_subc.shp"):
                basins += [shape(f["geometry"]).buffer(0)
                           for f in read(source, f"SELECT CVE_SUBC FROM {layer}", bbox, out, latin1=True)]
            elif name.endswith("_to.shp"):
                for f in read(source, f"SELECT TERMINO_GE, NOMBRE_COM FROM {layer}", bbox, out, latin1=True):
                    p = f["properties"]
                    toponyms.append((f["geometry"]["coordinates"], p["TERMINO_GE"], p["NOMBRE_COM"]))
            else:
                sql = f"SELECT ORDER_1, CONDICION FROM {layer} WHERE ENTIDAD IN ('CORRIENTE DE AGUA', 'LINEA CENTRAL')"
                for f in read(source, sql, bbox, out, latin1=True):
                    p = f["properties"]
                    intermittent = p["CONDICION"] == "INTERMITENTE"
                    lines += [(g, int(p["ORDER_1"]), intermittent) for g in segments(shape(f["geometry"]))]
    return basins, lines, toponyms


def load_nhd(bbox: Sequence, tmp: Path) -> tuple[list, list]:
    """NHD's HU8 watersheds and its streams in the box, every HU8 in the cache, with the order computed over the
    whole network (the order of a stream depends on everything upstream)."""
    basins, flowlines = [], []
    for i, shp_dir in enumerate(sorted(NHD.glob("*/Shape"))):
        hu8 = read(shp_dir / "WBDHU8.shp", "SELECT huc8 FROM WBDHU8", bbox, tmp / f"nhd-basins-{i}.geojson")
        basins += [shape(f["geometry"]).buffer(0) for f in hu8]
        sql = "SELECT gnis_name, fcode FROM NHDFlowline WHERE ftype IN (460, 558)"
        for f in read(shp_dir / "NHDFlowline.shp", sql, bbox, tmp / f"nhd-lines-{i}.geojson"):
            p = f["properties"]
            intermittent = p["fcode"] in NHD_INTERMITTENT
            flowlines += [(g, intermittent, p["gnis_name"] or "") for g in segments(shape(f["geometry"]))]
    if not flowlines:
        return basins, []
    order = strahler([g for g, _, _ in flowlines])
    return basins, [(g, int(o), i, name) for (g, i, name), o in zip(flowlines, order, strict=True)]


def load(bbox: Sequence, tmp: Path) -> Hydro:
    inegi_basins, inegi_lines, toponyms = load_inegi(bbox, tmp)
    nhd_basins, nhd_lines = load_nhd(bbox, tmp)
    return Hydro(inegi_basins, inegi_lines, toponyms, nhd_basins, nhd_lines)
