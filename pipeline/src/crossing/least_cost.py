"""Least-cost paths for the sierra and valley legs that the book does not trace (decision 0021).

`crossing.build_story` calls `route()` for each leg listed in pipeline/seeds/modeled-legs.csv, in place of the
schematic curve. A modelled line is `method: modeled`: a plausible way over the ground, never the book's path.
Results are cached in private/cache/least-cost/routes/, keyed by the two stop points, the leg's settings and the
model version, so a rebuild reruns only legs whose stops moved. Run on its own to model every listed leg and print
the numbers:
    uv run --project pipeline python -m crossing.least_cost

Reads the Copernicus GLO-30 DEM, INEGI's 1:50,000 streams (RH09, RH34), INEGI's Red Nacional de Caminos tracks
(private/cache/roads/inegi/tracks.geojson), and Natural Earth's railroads, lakes and admin areas. Each leg is routed
between its two stop points over a grid in a local transverse Mercator projection (90 m cells, coarser for long
legs), as a directed graph with eight neighbours per cell (scipy's Dijkstra). An edge costs the time to cross it:

  speed      Tobler's hiking function (Tobler 1993, "Three presentations on geographical analysis and
             modeling", NCGIA technical report 93-1): v = 6 exp(-3.5 |s + 0.05|) km/h on slope s along the
             edge, so uphill and downhill differ. For a rider it is scaled so that flat ground gives 6 km/h,
             a horse's walk (design section 7); for the wolf it is unscaled.
  steep      along-edge slope over 30 % costs up to three times more by 50 %, and ten times beyond
             (a horse does not climb a cliff); the thresholds are an assumption.
  canyon     side slope: a cell whose steepest gradient is over 25 % costs more to cross even along the
             contour, up to three times at 50 % and six times at 60 % and over (canyon walls, sidehill).
             Cells on an INEGI stream of order 4 and up, and their neighbours, are exempt: a canyon floor
             is where the trail runs, and at 90 m its cells take the gradient of the walls beside them.
  rivers     entering an INEGI stream cell costs a fixed delay by Strahler order (ORDER_1), for a ford:
             3 and 4 -> 0.5 min, 5 -> 1, 6 -> 2, 7 and up -> 4. Riding along a river does not pay it again.
             The delays are small on purpose: at 90 m a meandering river fills its valley floor, so a path
             up a valley "enters" it dozens of times, and delays of 15 to 30 minutes pushed paths out of the
             valleys onto the ridges.
  lakes      Natural Earth's lakes cost five times more: they are shallow and seasonal, boggy at the edges.
  towns      the wolf keeps away from people: cells within 2 km of a town in data/places.geojson cost five
             times more for her.
  corridors  only where the seed names one for the leg: a road (INEGI's unpaved tracks and footpaths and
             Natural Earth's railroads, which are of the period, within 1 km, times 0.8) or a riverside trail
             (INEGI streams of the leg's order and up within 300 m, times 0.8). Today's paved highways are left
             out: they follow modern alignments.
  border     a rider in Mexico may not cross into the United States except within 2 km of a stop on or
             over the line.
"""

import argparse
import csv
import hashlib
import json
import math
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import rasterio
import rasterio.enums
import shapely
from pyproj import CRS, Geod, Transformer
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from shapely import STRtree
from shapely.geometry import LineString, Point, box, shape
from shapely.ops import unary_union

from crossing.paths import CACHE as CACHE_ROOT
from crossing.paths import DATA, SEEDS

CACHE = CACHE_ROOT / "least-cost"
ROUTES = CACHE / "routes"
DEM_DIRS = [CACHE_ROOT / "dem" / "copernicus", CACHE_ROOT / "dem" / "copernicus-region"]
INEGI = CACHE_ROOT / "hydro" / "inegi"
TRACKS = CACHE_ROOT / "roads" / "inegi" / "tracks.geojson"
BASEMAP = CACHE_ROOT / "basemap"
BBOX = (-110.4, 27.9, -106.3, 32.1)  # lon/lat box around every Mexican leg
GEOD = Geod(ellps="WGS84")
MODEL = "lc-0.4"
# INEGI RNC classes (TIPO_VIAL, then surface) that count as a period road corridor: dirt and gravel tracks, footpaths.
TRACK_KINDS = ("camino, tierra", "camino, grava", "vereda")
# The model's simplification of a cell path for the published line: Douglas-Peucker at this tolerance, then one
# round of Chaikin's corner cutting, which keeps a modelled line about as light as a schematic curve.
SIMPLIFY_M = 150.0
RIVER_DELAY_H = {3: 0.5 / 60, 4: 0.5 / 60, 5: 1 / 60, 6: 2 / 60, 7: 4 / 60}


def legs() -> dict[tuple[str, int], dict]:
    """The modelled legs from the seed, by (journey, from_seq): mode (horse or wolf), corridor (road, river or
    empty), river_order for a river corridor, and a note for the leg's reasoning."""
    with (SEEDS / "modeled-legs.csv").open(encoding="utf-8", newline="") as f:
        out = {}
        for r in csv.DictReader(f):
            leg = {"mode": r["mode"], "note": r["note"]}
            if r["corridor"] == "road":
                leg["road"] = True
            elif r["corridor"] == "river":
                leg["river"] = int(r["river_order"])
            out[(r["journey"], int(r["from_seq"]))] = leg
        return out


def ogr_geojson(source: str, sql: str | None, out: Path, extra: tuple[str, ...] = ()) -> None:
    args = ["ogr2ogr", "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-spat", *map(str, BBOX),
            "-dim", "XY", "--config", "SHAPE_ENCODING", "ISO-8859-1", *extra]
    if sql:
        args += ["-dialect", "OGRSQL", "-sql", sql]
    subprocess.run([*args, str(out), source], check=True, capture_output=True)


def prepare() -> None:
    """One-off: a DEM mosaic (VRT) and the vector layers clipped to the box, under private/cache/least-cost."""
    if not TRACKS.exists():
        raise SystemExit(f"Missing {TRACKS}: INEGI's Red Nacional de Caminos tracks, clipped to {BBOX} "
                         "(docs/data-sources.md)")
    CACHE.mkdir(parents=True, exist_ok=True)
    vrt = CACHE / "dem.vrt"
    if not vrt.exists():
        tiles = sorted({p.name: p for d in DEM_DIRS for p in d.glob("*.tif")}.values())
        subprocess.run(["gdalbuildvrt", str(vrt), *map(str, tiles)], check=True, capture_output=True)
    rivers = CACHE / "inegi-streams.geojson"
    if not rivers.exists():
        feats = []
        for zip_path in sorted(INEGI.glob("*.zip")):
            for name in (n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith("_hl.shp")):
                tmp = CACHE / "tmp.geojson"
                tmp.unlink(missing_ok=True)
                # Wide rivers are double lines whose channel is the LINEA CENTRAL entity, not CORRIENTE DE AGUA.
                ogr_geojson(f"/vsizip/{zip_path}/{name}", f"SELECT ORDER_1 FROM {Path(name).stem} "
                            "WHERE ENTIDAD IN ('CORRIENTE DE AGUA', 'LINEA CENTRAL') AND ORDER_1 >= 3", tmp)
                feats += [f for f in json.loads(tmp.read_text())["features"] if f["geometry"]]
                tmp.unlink()
        rivers.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    for name, sql in {
        "ne_10m_railroads": "SELECT scalerank FROM ne_10m_railroads",
        "ne_10m_lakes_north_america": "SELECT name FROM ne_10m_lakes_north_america",
        "ne_10m_admin_1_states_provinces": "SELECT adm0_a3 FROM ne_10m_admin_1_states_provinces "
                                           "WHERE adm0_a3 IN ('MEX', 'USA')",
    }.items():
        out = CACHE / f"{name}.geojson"
        if not out.exists():
            ogr_geojson(str(BASEMAP / name / f"{name}.shp"), sql, out)


# Layers, loaded once per process.
LAYERS: dict = {}


def load_layers() -> None:
    prepare()

    def feats(path: Path) -> list[dict]:
        return [f for f in json.loads(path.read_text())["features"] if f["geometry"]]

    streams = feats(CACHE / "inegi-streams.geojson")
    LAYERS["streams"] = [shape(f["geometry"]) for f in streams]
    LAYERS["orders"] = np.array([f["properties"]["ORDER_1"] for f in streams])
    LAYERS["streams_tree"] = STRtree(LAYERS["streams"])
    # Only the unpaved tracks and footpaths: paved highways and town streets follow modern alignments.
    tracks = [f for f in feats(TRACKS) if f["properties"]["kind"].startswith(TRACK_KINDS)]
    LAYERS["roads"] = [shape(f["geometry"]) for f in tracks + feats(CACHE / "ne_10m_railroads.geojson")]
    LAYERS["lakes"] = [shape(f["geometry"]) for f in feats(CACHE / "ne_10m_lakes_north_america.geojson")]
    states = feats(CACHE / "ne_10m_admin_1_states_provinces.geojson")
    LAYERS["mexico"] = unary_union([shape(f["geometry"]) for f in states
                                    if f["properties"]["adm0_a3"] == "MEX"]).buffer(0)
    LAYERS["dem"] = rasterio.open(CACHE / "dem.vrt")
    LAYERS["towns"] = [shape(f["geometry"]) for f in json.loads((DATA / "places.geojson").read_text())["features"]
                       if f["properties"]["kind"] in ("town", "city")]

def tobler(s: np.ndarray, flat_kmh: float | None) -> np.ndarray:
    """Tobler's hiking function in km/h; with flat_kmh, scaled so that s = 0 gives that speed."""
    v = 6.0 * np.exp(-3.5 * np.abs(s + 0.05))
    return v * (flat_kmh / (6.0 * math.exp(-3.5 * 0.05))) if flat_kmh else v


def steep_factor(s: np.ndarray) -> np.ndarray:
    a = np.abs(s)
    return np.where(a <= 0.30, 1.0, np.where(a <= 0.50, 1.0 + 10.0 * (a - 0.30), 10.0))


def canyon_factor(g: np.ndarray) -> np.ndarray:
    return np.where(g <= 0.25, 1.0, np.where(g <= 0.50, 1.0 + 8.0 * (g - 0.25), np.where(g <= 0.60, 3.0, 6.0)))


def grid_for(a: tuple[float, float], b: tuple[float, float]) -> dict:
    """A local transverse Mercator grid around two lon/lat points, padded, at 90 m or coarser."""
    lon0, lat0 = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    crs = CRS.from_proj4(f"+proj=tmerc +lat_0={lat0:.4f} +lon_0={lon0:.4f} +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m")
    fwd = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    (ax, ay), (bx, by) = fwd.transform(*a), fwd.transform(*b)
    dist = math.hypot(bx - ax, by - ay)
    pad = max(12_000.0, 0.4 * dist)
    x0, x1 = min(ax, bx) - pad, max(ax, bx) + pad
    y0, y1 = min(ay, by) - pad, max(ay, by) + pad
    res = 90.0
    while (x1 - x0) * (y1 - y0) / res**2 > 2.2e6:
        res += 30.0
    w, h = int(math.ceil((x1 - x0) / res)), int(math.ceil((y1 - y0) / res))
    return dict(crs=crs, fwd=fwd, inv=Transformer.from_crs(crs, "EPSG:4326", always_xy=True),
                transform=from_origin(x0, y0 + h * res, res, res), w=w, h=h, res=res,
                a=(ax, ay), b=(bx, by), dist=dist)


def cell_of(g: dict, x: float, y: float) -> tuple[int, int]:
    col, row = ~g["transform"] * (x, y)
    return int(row), int(col)


def to_grid(g: dict, geoms: list) -> list:
    fwd = g["fwd"]
    return [shapely.transform(geom, lambda xy: np.column_stack(fwd.transform(xy[:, 0], xy[:, 1]))) for geom in geoms]


def surfaces(g: dict, leg: dict) -> dict:
    """The rasters one leg needs: elevation, blocked cells, a per-cell cost factor and river entry delays."""
    h, w, res = g["h"], g["w"], g["res"]
    z = np.full((h, w), np.nan, dtype="float32")
    reproject(rasterio.band(LAYERS["dem"], 1), z, dst_transform=g["transform"], dst_crs=g["crs"],
              resampling=Resampling.average, dst_nodata=np.nan)
    blocked = ~np.isfinite(z)
    z = np.where(blocked, 0, z)
    gy, gx = np.gradient(z, res)
    factor = canyon_factor(np.hypot(gx, gy)).astype("float32")

    inv = g["inv"]
    local_box = box(*g["transform"] * (0, h), *g["transform"] * (w, 0))
    lon_lat_box = box(*shapely.transform(local_box, lambda xy: np.column_stack(inv.transform(xy[:, 0], xy[:, 1])))
                      .bounds).buffer(0.05)
    shape_hw = (h, w)

    def burn(geoms: list, values=None, all_touched=True, dtype="uint8") -> np.ndarray:
        geoms = [x for x in geoms if x.intersects(lon_lat_box)]
        if not geoms:
            return np.zeros(shape_hw, dtype=dtype)
        pairs = zip(to_grid(g, geoms), values if values is not None else [1] * len(geoms), strict=False)
        return rasterize(pairs, out_shape=shape_hw, transform=g["transform"], all_touched=all_touched,
                         dtype=dtype, merge_alg=rasterio.enums.MergeAlg.replace)

    idx = LAYERS["streams_tree"].query(lon_lat_box)
    order_sorted = idx[np.argsort(LAYERS["orders"][idx])]  # higher orders burned last, so they win
    streams = [LAYERS["streams"][i] for i in order_sorted]
    orders = burn(streams, [int(LAYERS["orders"][i]) for i in order_sorted])
    wolf = leg.get("mode") == "wolf"
    floor = ndimage.binary_dilation(orders >= 4)
    factor[floor] = 1.0
    delay = np.zeros((h, w), dtype="float32")
    for o, d in RIVER_DELAY_H.items():
        delay[orders >= o] = d * (0.5 if wolf else 1.0)

    lakes = burn(LAYERS["lakes"], all_touched=False)
    factor[lakes > 0] *= 5.0
    if wolf:
        near = burn([x.buffer(0.02) for x in LAYERS["towns"]], all_touched=False)
        factor[near > 0] *= 5.0

    corridor = np.zeros((h, w), dtype=bool)
    if leg.get("road"):
        roads = burn(LAYERS["roads"])
        corridor |= ndimage.distance_transform_edt(roads == 0) * res <= 1000
    if leg.get("river"):
        main = burn([s for s, i in zip(streams, order_sorted, strict=False) if LAYERS["orders"][i] >= leg["river"]])
        corridor |= ndimage.distance_transform_edt(main == 0) * res <= 300
    factor[corridor] *= 0.8

    if not wolf:
        mexico = burn([LAYERS["mexico"]], all_touched=False) > 0
        gate = np.zeros((h, w), dtype=bool)
        rr, cc = np.mgrid[0:h, 0:w]
        for x, y in (g["a"], g["b"]):
            lon, lat = g["inv"].transform(x, y)
            here = Point(lon, lat)
            if LAYERS["mexico"].boundary.distance(here) < 0.02 or not LAYERS["mexico"].contains(here):
                r, c = cell_of(g, x, y)
                gate |= (rr - r) ** 2 + (cc - c) ** 2 <= (2000 / res) ** 2
        blocked |= ~mexico & ~gate
    return dict(z=z, blocked=blocked, factor=factor, delay=delay, river=orders >= 3, corridor=corridor)


OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def least_cost(g: dict, s: dict, leg: dict) -> tuple[list[tuple[int, int]], float]:
    """The cheapest cell path from stop a to stop b, and its cost in hours."""
    h, w, res = g["h"], g["w"], g["res"]
    z, blocked, factor, delay, river = s["z"], s["blocked"], s["factor"], s["delay"], s["river"]
    flat = None if leg.get("mode") == "wolf" else 6.0
    ids = np.arange(h * w, dtype=np.int64).reshape(h, w)
    src_all, dst_all, wt_all = [], [], []
    for dy, dx in OFFSETS:
        rs = slice(max(0, -dy), h - max(0, dy))
        cs = slice(max(0, -dx), w - max(0, dx))
        rt = slice(max(0, dy), h - max(0, -dy))
        ct = slice(max(0, dx), w - max(0, -dx))
        d = res * math.hypot(dy, dx)
        slope = (z[rt, ct] - z[rs, cs]) / d
        hours = (d / 1000.0) / tobler(slope, flat)
        if leg.get("mode") != "wolf":
            hours = hours * steep_factor(slope)
        hours = hours * 0.5 * (factor[rs, cs] + factor[rt, ct])
        hours = hours + np.where(river[rt, ct] & ~river[rs, cs], delay[rt, ct], 0.0)
        ok = ~blocked[rs, cs] & ~blocked[rt, ct]
        src_all.append(ids[rs, cs][ok])
        dst_all.append(ids[rt, ct][ok])
        wt_all.append(hours[ok].astype("float64"))
    edges = (np.concatenate(src_all), np.concatenate(dst_all))
    graph = csr_matrix((np.concatenate(wt_all), edges), shape=(h * w, h * w))
    ra, ca = cell_of(g, *g["a"])
    rb, cb = cell_of(g, *g["b"])
    a, b = ids[ra, ca], ids[rb, cb]
    dist, pred = dijkstra(graph, directed=True, indices=a, return_predecessors=True)
    if not np.isfinite(dist[b]):
        raise RuntimeError("no path")
    path, node = [], b
    while node != a and node >= 0:
        path.append(divmod(int(node), w))
        node = pred[node]
    path.append(divmod(int(a), w))
    return path[::-1], float(dist[b])


def chaikin(coords: list[tuple[float, float]], rounds: int = 2) -> list[tuple[float, float]]:
    for _ in range(rounds):
        out = [coords[0]]
        for (x0, y0), (x1, y1) in zip(coords, coords[1:], strict=False):
            out += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        out.append(coords[-1])
        coords = out
    return coords



def line_km(coords: list) -> float:
    lons, lats = zip(*coords, strict=True)
    return GEOD.line_length(lons, lats) / 1000.0


def route(a: tuple[float, float], b: tuple[float, float], leg: dict) -> dict:
    """The modelled path from stop a to stop b (lon, lat) for one seed leg: the line in lon/lat, its length and the
    model's hours. Cached on disk by the inputs and the model version."""
    settings = {k: leg.get(k) for k in ("mode", "road", "river")}
    key = hashlib.sha256(json.dumps([MODEL, SIMPLIFY_M, a, b, settings]).encode()).hexdigest()[:20]
    cached = ROUTES / f"{key}.json"
    if cached.exists():
        return json.loads(cached.read_text())
    if not LAYERS:
        load_layers()
    g = grid_for(a, b)
    s = surfaces(g, leg)
    cells, hours = least_cost(g, s, leg)
    t = g["transform"]
    xy = [g["a"]] + [t * (c + 0.5, r + 0.5) for r, c in cells][1:-1] + [g["b"]]
    smooth = chaikin(list(LineString(xy).simplify(SIMPLIFY_M).coords), rounds=1)
    lonlat = [[round(v, 5) for v in g["inv"].transform(x, y)] for x, y in smooth]
    lonlat[0], lonlat[-1] = list(a), list(b)
    out = {"coords": lonlat, "km": round(line_km(lonlat), 2), "hours": round(hours, 2), "res_m": g["res"]}
    ROUTES.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(out))
    return out


def drawn(leg: dict, res_m: float) -> str:
    """How a modelled leg was drawn, in words, for the "How this line was drawn" section of its card."""
    who = ("a wolf on foot (Tobler's hiking speed, about 5 km/h on the flat)" if leg["mode"] == "wolf"
           else "a horse at a walk (Tobler's hiking function scaled to 6 km/h on the flat)")
    corridor = (" Ground within 1 km of today's unpaved tracks and the railways costs a fifth less, standing in "
                "for the roads of the time." if leg.get("road")
                else " Ground within 300 m of the river costs a fifth less, for the river trail." if leg.get("river")
                else "")
    return (f"Computed, not traced: the quickest way between the two stops for {who}, found over a {res_m:.0f} m "
            f"grid of the Copernicus 30 m elevation model. Steep ground, canyon walls, river fords and lakes cost "
            f"more time{' and the wolf keeps clear of towns' if leg['mode'] == 'wolf' else ''}.{corridor} The "
            f"cell path is then smoothed (Douglas-Peucker at {SIMPLIFY_M:.0f} m, one round of corner cutting). "
            f"Cost model {MODEL}, decision 0021.")


def main() -> None:
    argparse.ArgumentParser(description=__doc__.split("\n")[0]).parse_args()
    stops = {}
    for f in json.loads((DATA / "stops.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        stops[(p["journey"], p["sequence"])] = tuple(f["geometry"]["coordinates"])
    for (jid, seq), leg in legs().items():
        r = route(stops[(jid, seq)], stops[(jid, seq + 1)], leg)
        print(f"{jid} {seq:2d}: {r['km']:6.1f} km, {r['hours']:5.1f} h at {r['res_m']:.0f} m  {leg['mode']}"
              f"{' road' if leg.get('road') else ''}{' river' if leg.get('river') else ''}")


if __name__ == "__main__":
    main()
