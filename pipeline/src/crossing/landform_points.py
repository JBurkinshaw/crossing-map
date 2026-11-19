"""Experiment: where in a landform the book puts a stop, found from data, and a check of each stop's ground.

Run from the repo root:
    uv run --project pipeline python -m crossing.landform_points            # J1, and the calibration
    uv run --project pipeline --with matplotlib python -m crossing.landform_points_images   # the figures, after

Writes review/experiments/landform-points/ (results.csv, calibration.csv, points.geojson, img/). See its README.

The book often places a stop at one part of a landform: the head of a draw, the gap through a range, the high
country between two draws. A gazetteer's point for the landform is somewhere else (a stream's mouth, a range's
middle). Each position is resolved by three tiers, run independently here so they can be compared:

  1 gazetteer  GNIS records a valley, canyon or stream with a primary point at its mouth and a source point at its
               head; a gap or pass is its own feature (class Gap).
  2 vector     USGS NHD flowlines carrying the feature's GNIS name: the head is the upstream end of the named line
               farthest from the mouth (NHD lines are digitised downstream).
  3 DEM        Copernicus GLO-30 (private/cache/least-cost/dem.vrt), resampled to a local transverse Mercator grid
               (WGS 84 ellipsoid) centred on the feature. Flow routing: depressions filled by priority flood
               (Barnes et al. 2014, with a small epsilon so flats drain), D8 directions (O'Callaghan and Mark 1984),
               flow accumulation. The head is found by following the main stem up from the mouth, always into the
               upstream cell with the largest catchment, until the catchment falls below a channel-head area
               (Montgomery and Dietrich 1988 tie channel heads to a support area; the area is calibrated below).
               "Between" two draws is the drainage divide between their catchments, at the point nearest the
               midpoint of their heads. A gap is the highest point within the range of a least-cost path
               (crossing.least_cost, the wolf's model) from the stop before to the stop after.

The check (option C) classifies the ground at a point with geomorphons (Jasiewicz and Stepinski 2013, the lookup
table of GRASS r.geomorphon): eight rays out to a lookout distance, each marked higher, lower or level by the
largest angle above and below the horizon (a 1 degree flat threshold), and the counts of higher and lower rays give
one of ten landforms. It is computed at two lookouts (500 m and 2 km), with a saddle test (two opposite rays higher,
the two across them lower) and the point's height as a percentile of the ground around it, over a window that
grows with the landform (3 km, 5 km for a foot, rim, high point or slopes, 8 km for a valley floor).
Each stop's position names the ground it should be on, and a mismatch is flagged.

Calibration: every GNIS valley, stream and arroyo around J1 that has a source point 1 km or more from its mouth is
resolved by tier 3 from its mouth, and the distance from the DEM head to the GNIS head is reported for several
channel-head areas.
"""

import argparse
import csv
import heapq
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyproj import CRS, Geod, Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from shapely.geometry import shape

from crossing import least_cost
from crossing.paths import CACHE, DATA, REPO

DEM = CACHE / "least-cost" / "dem.vrt"
GNIS = CACHE / "gazetteer" / "Features_20210825"
NHD = CACHE / "hydro" / "nhd"
OUT = REPO / "review" / "experiments" / "landform-points"
GEOD = Geod(ellps="WGS84")

# Channel-head support areas tried, km². The first is the one J1's results use; calibration reports all.
HEAD_AREAS = [0.1, 0.02, 0.5, 2.0]
FLOW_RES, FLOW_HALF = 60, 16_000          # m: the flow grid's cell and half width around the feature
LOOKOUTS = [500, 2000]                    # m: geomorphon lookout distances
FLAT_DEG = 1.0
PCT_RADIUS = 3000                         # m: the disc a point's height percentile is taken over
RANGE_KM = 15                             # how far from a range's point its gaps are looked for
SADDLE_NEAR = 300                         # m: how far a pass's saddle may lie from its point
GENTLE_DEG = 3.0                          # slope of the ground within 500 m below which ground can be a valley floor

# J1's stops and the part of a landform the book puts each at. At rollout this is a `position` column in
# pipeline/seeds/stops.csv. head: the head of the stop's draw or canyon (GNIS id); between: the high country between
# two draws (GNIS ids); pass: a gap through the range (the range's place id); floor: a valley floor or river.
POSITIONS = {
    "j1-bavispe-crossing": {"position": "floor"},
    "j1-san-luis-mountains": {"position": "pass", "range": "san-luis-mountains"},
    "j1-animas-mountains": {"position": "pass", "range": "animas-mountains"},
    "j1-animas-valley": {"position": "floor"},
    "j1-foster-draw": {"position": "head", "gnis": 889164},
    "j1-starvation-canyon": {"position": "head", "gnis": 11797},
    "j1-clanton-foster": {"position": "between", "gnis": [887634, 889164]},
}

N8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]  # N, NE, E, SE, S, SW, W, NW
# Geomorphon landforms by [rays lower][rays higher] (Jasiewicz and Stepinski 2013, table 1, as in r.geomorphon).
FORMS = [
    ["flat", "flat", "flat", "footslope", "footslope", "valley", "valley", "valley", "pit"],
    ["flat", "flat", "footslope", "footslope", "footslope", "valley", "valley", "valley"],
    ["flat", "shoulder", "slope", "slope", "hollow", "hollow", "valley"],
    ["shoulder", "shoulder", "slope", "slope", "slope", "hollow"],
    ["shoulder", "shoulder", "spur", "slope", "slope"],
    ["ridge", "ridge", "spur", "spur"],
    ["ridge", "ridge", "ridge"],
    ["ridge", "ridge"],
    ["peak"],
]
# The ground each position should be on: allowed landforms at either lookout, a height percentile range, and the
# radius in metres the percentile is taken over. The radius grows with the landform: a valley floor is judged
# against a whole valley, which can be 15 km wide, and a draw's head against the ground around it.
LOW = {"flat", "footslope", "valley", "pit", "hollow"}
HIGH = {"ridge", "spur", "shoulder", "peak"}
EXPECT = {
    "head": ({"hollow", "valley", "slope", "spur", "shoulder"}, (40, 100), PCT_RADIUS),
    "mouth": (LOW, (0, 50), PCT_RADIUS),
    "between": (HIGH | {"slope"}, (50, 100), PCT_RADIUS),
    "pass": ({"saddle"}, (0, 100), PCT_RADIUS),
    "floor": (LOW, (0, 40), 8000),
    "foot": (LOW | {"slope"}, (0, 50), 5000),
    "rim": (HIGH, (60, 100), 5000),
    "high": (HIGH, (60, 100), 5000),
    "slopes": ({"slope", "footslope", "spur", "hollow", "shoulder"}, (10, 70), 5000),
}


# --- data -------------------------------------------------------------------------------------------------------

def gnis() -> dict[int, dict]:
    out = {}
    for path in sorted(GNIS.glob("*_Features_*.txt")):
        with path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter="|"):
                try:
                    mouth = (float(r["PRIM_LONG_DEC"]), float(r["PRIM_LAT_DEC"]))
                except ValueError:
                    continue
                head = (float(r["SOURCE_LONG_DEC"]), float(r["SOURCE_LAT_DEC"])) if r["SOURCE_LAT_DEC"] else None
                out[int(r["FEATURE_ID"])] = {"id": int(r["FEATURE_ID"]), "name": r["FEATURE_NAME"],
                                             "class": r["FEATURE_CLASS"], "mouth": mouth, "head": head}
    return out


def stops_at(ref: str | None) -> dict[str, dict]:
    """J1's stops from data/stops.geojson, at HEAD (ref) or on disk (None)."""
    text = subprocess.check_output(["git", "show", f"{ref}:data/stops.geojson"], cwd=REPO, text=True) if ref \
        else (DATA / "stops.geojson").read_text(encoding="utf-8")
    return {f["properties"]["id"]: {**f["properties"], "lonlat": tuple(f["geometry"]["coordinates"])}
            for f in json.loads(text)["features"] if f["properties"]["journey"] == "J1"}


def place_points() -> dict[str, tuple[float, float]]:
    doc = json.loads((DATA / "places.geojson").read_text(encoding="utf-8"))
    return {f["properties"]["id"].removeprefix("place-"): tuple(f["geometry"]["coordinates"]) for f in doc["features"]}


def km(a, b) -> float:
    return GEOD.inv(a[0], a[1], b[0], b[1])[2] / 1000


# --- grids ------------------------------------------------------------------------------------------------------

@dataclass
class Grid:
    z: np.ndarray
    res: float
    half: float
    fwd: Transformer
    inv: Transformer

    def cell(self, lonlat) -> tuple[int, int]:
        x, y = self.fwd.transform(*lonlat)
        return int((self.half - y) // self.res), int((x + self.half) // self.res)

    def lonlat(self, rc) -> tuple[float, float]:
        x = -self.half + (rc[1] + 0.5) * self.res
        y = self.half - (rc[0] + 0.5) * self.res
        lon, lat = self.inv.transform(x, y)
        return round(lon, 5), round(lat, 5)


def grid(centre, half: float, res: float) -> Grid:
    """The DEM on a square transverse Mercator grid (WGS 84) centred on `centre` (lon, lat)."""
    crs = CRS.from_proj4(f"+proj=tmerc +lat_0={centre[1]} +lon_0={centre[0]} +k=1 +x_0=0 +y_0=0 +ellps=WGS84 "
                         "+units=m +no_defs")
    n = int(2 * half / res)
    z = np.full((n, n), np.nan, dtype=np.float64)
    with rasterio.open(DEM) as src:
        reproject(rasterio.band(src, 1), z, dst_transform=from_origin(-half, half, res, res), dst_crs=crs,
                  resampling=Resampling.average if res > 30 else Resampling.bilinear, src_nodata=src.nodata,
                  dst_nodata=np.nan)
    if np.isnan(z).any():
        z[np.isnan(z)] = np.nanmin(z)
    return Grid(z, res, half, Transformer.from_crs(4326, crs, always_xy=True),
                Transformer.from_crs(crs, 4326, always_xy=True))


# --- flow routing -----------------------------------------------------------------------------------------------

@dataclass
class Flow:
    g: Grid
    down: np.ndarray   # flat index of each cell's D8 receiver, -1 at an outlet
    acc: np.ndarray    # cells draining through each cell, itself included

    def upstream(self, i: int) -> list[int]:
        n = self.g.z.shape[1]
        r, c = divmod(i, n)
        out = []
        for dr, dc in N8:
            rr, cc = r + dr, c + dc
            if 0 <= rr < self.g.z.shape[0] and 0 <= cc < n and self.down[rr * n + cc] == i:
                out.append(rr * n + cc)
        return out


def flow(g: Grid) -> Flow:
    z = g.z
    rows, cols = z.shape
    filled = z.copy()
    seen = np.zeros(z.shape, bool)
    heap = []
    for r in range(rows):
        for c in (0, cols - 1):
            heap.append((z[r, c], r, c))
            seen[r, c] = True
    for c in range(1, cols - 1):
        for r in (0, rows - 1):
            heap.append((z[r, c], r, c))
            seen[r, c] = True
    heapq.heapify(heap)
    eps = 1e-4
    while heap:
        e, r, c = heapq.heappop(heap)
        for dr, dc in N8:
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and not seen[rr, cc]:
                seen[rr, cc] = True
                v = max(z[rr, cc], e + eps)
                filled[rr, cc] = v
                heapq.heappush(heap, (v, rr, cc))
    pad = np.pad(filled, 1, constant_values=np.inf)
    slopes = np.stack([(filled - pad[1 + dr:1 + dr + rows, 1 + dc:1 + dc + cols]) / math.hypot(dr, dc)
                       for dr, dc in N8])
    best = slopes.argmax(axis=0)
    has = slopes.max(axis=0) > 0
    rr = np.arange(rows)[:, None] + np.array([d[0] for d in N8])[best]
    cc = np.arange(cols)[None, :] + np.array([d[1] for d in N8])[best]
    down = np.where(has, rr * cols + cc, -1).ravel()
    acc = np.ones(rows * cols, dtype=np.int64)
    for i in np.argsort(-filled.ravel(), kind="stable"):
        d = down[i]
        if d >= 0:
            acc[d] += acc[i]
    return Flow(g, down, acc)


def snap(f: Flow, lonlat, radius_m: float = 300) -> int:
    """The cell with the largest catchment within radius_m of a point: the channel the point is on."""
    r0, c0 = f.g.cell(lonlat)
    k = int(radius_m // f.g.res)
    n = f.g.z.shape[1]
    best = max((f.acc[r * n + c], r * n + c) for r in range(r0 - k, r0 + k + 1) for c in range(c0 - k, c0 + k + 1)
                if (r - r0) ** 2 + (c - c0) ** 2 <= k * k)
    return best[1]


def main_stem(f: Flow, mouth: int) -> list[int]:
    """Cells from the mouth up the main stem to the divide, always into the upstream cell with the largest catchment."""
    path = [mouth]
    while ups := f.upstream(path[-1]):
        path.append(max(ups, key=lambda i: f.acc[i]))
    return path


def head_on(f: Flow, stem: list[int], area_km2: float) -> int:
    cells = area_km2 * 1e6 / f.g.res ** 2
    for i in stem:
        if f.acc[i] < cells:
            return i
    return stem[-1]


def catchment(f: Flow, outlet: int) -> np.ndarray:
    mask = np.zeros(f.acc.size, bool)
    todo = [outlet]
    while todo:
        i = todo.pop()
        mask[i] = True
        todo += f.upstream(i)
    return mask.reshape(f.g.z.shape)


def dem_head(mouth, area_km2: float = HEAD_AREAS[0], f: Flow | None = None) -> tuple[tuple, list, Flow]:
    f = f or flow(grid(mouth, FLOW_HALF, FLOW_RES))
    stem = main_stem(f, snap(f, mouth))
    n = f.g.z.shape[1]
    return f.g.lonlat(divmod(head_on(f, stem, area_km2), n)), [f.g.lonlat(divmod(i, n)) for i in stem], f


def dem_between(mouth_a, mouth_b, heads_at=None) -> tuple[tuple, list]:
    """The point on the divide between two catchments nearest the midpoint of their DEM heads, or of `heads_at`
    (lon, lat pairs, such as the gazetteer's heads) when given."""
    mid = ((mouth_a[0] + mouth_b[0]) / 2, (mouth_a[1] + mouth_b[1]) / 2)
    f = flow(grid(mid, FLOW_HALF, FLOW_RES))
    n = f.g.z.shape[1]
    heads, masks = [], []
    for m in (mouth_a, mouth_b):
        outlet = snap(f, m)
        heads.append(head_on(f, main_stem(f, outlet), HEAD_AREAS[0]))
        masks.append(catchment(f, outlet))
    a, b = masks
    grown_a, grown_b = np.zeros_like(a), np.zeros_like(b)
    for dr, dc in N8:
        grown_a |= np.roll(np.roll(a, dr, 0), dc, 1)
        grown_b |= np.roll(np.roll(b, dr, 0), dc, 1)
    # The cells either side of the divide, so the answer does not depend on which catchment comes first.
    divide = np.argwhere((a & grown_b) | (b & grown_a))
    if not len(divide):
        return None, []
    ha, hb = (np.array(g) for g in map(f.g.cell, heads_at)) if heads_at else (np.array(divmod(h, n)) for h in heads)
    target = (ha + hb) / 2
    # "High country": divide cells on a ridge, spur, shoulder or peak at a 500 m lookout, if there are any.
    forms, _ = forms_grid(f.g, LOOKOUTS[0])
    high = np.isin(forms[divide[:, 0], divide[:, 1]], ["ridge", "spur", "shoulder", "peak"])
    pool = divide[high] if high.any() else divide
    best = pool[np.argmin(((pool - target) ** 2).sum(axis=1))]
    return f.g.lonlat(tuple(best)), [f.g.lonlat(tuple(d)) for d in divide[::4]]


def forms_grid(g: Grid, lookout: float) -> tuple[np.ndarray, np.ndarray]:
    """Geomorphon landform names and the saddle test for every cell of a grid, at one lookout distance."""
    rows, cols = g.z.shape
    kmax = int(lookout // g.res)
    pad = np.pad(g.z, kmax, constant_values=np.nan)
    marks = []
    for dr, dc in N8:
        step = math.hypot(dr, dc) * g.res
        k_n = int(lookout // step)
        up = np.zeros(g.z.shape)
        down = np.zeros(g.z.shape)
        for k in range(1, k_n + 1):
            zs = pad[kmax + dr * k:kmax + dr * k + rows, kmax + dc * k:kmax + dc * k + cols]
            a = np.degrees(np.arctan((zs - g.z) / (k * step)))
            up = np.fmax(up, a)
            down = np.fmax(down, -a)
        marks.append(np.where(up - down > FLAT_DEG, 1, np.where(down - up > FLAT_DEG, -1, 0)))
    m = np.stack(marks)
    lower, higher = (m == -1).sum(axis=0), (m == 1).sum(axis=0)
    names = np.array([[FORMS[lo][hi] if hi < len(FORMS[lo]) else "" for hi in range(9)] for lo in range(9)])
    saddle = np.zeros(g.z.shape, bool)
    for a in range(4):
        saddle |= (m[a] == 1) & (m[a + 4] == 1) & (m[(a + 2) % 8] == -1) & (m[(a + 6) % 8] == -1)
    return names[lower, higher], saddle


# --- the vector tier --------------------------------------------------------------------------------------------

def nhd_head(name: str, mouth) -> tuple | None:
    """The upstream end of NHD's flowlines named `name` near the mouth: the source farthest from the mouth."""
    lon, lat = mouth
    box = (lon - 0.25, lat - 0.25, lon + 0.25, lat + 0.25)
    lines = []
    for shp in sorted(NHD.glob("*/Shape/NHDFlowline.shp")):
        sql = f"SELECT gnis_name FROM NHDFlowline WHERE gnis_name = '{name.replace(chr(39), chr(39) * 2)}'"
        out = subprocess.run(["ogr2ogr", "-f", "GeoJSON", "/vsistdout/", str(shp), "-dialect", "OGRSQL", "-sql", sql,
                              "-spat", *map(str, box), "-t_srs", "EPSG:4326"], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            lines += [shape(f["geometry"]) for f in json.loads(out.stdout)["features"]]
    parts = [p for g in lines for p in getattr(g, "geoms", [g])]
    if not parts:
        return None
    # A single named channel network near this mouth: the lines that touch the one nearest the mouth, grown outwards.
    near = min(parts, key=lambda p: p.distance(shapely.Point(mouth)))
    if near.distance(shapely.Point(mouth)) > 0.03:
        return None
    net = [near]
    rest = [p for p in parts if p is not near]
    grew = True
    while grew:
        grew = False
        for p in list(rest):
            if any(p.distance(q) < 1e-5 for q in net):
                net.append(p)
                rest.remove(p)
                grew = True
    ends = {tuple(round(v, 6) for v in p.coords[-1]) for p in net}
    sources = [p.coords[0][:2] for p in net if tuple(round(v, 6) for v in p.coords[0]) not in ends]
    best = max(sources, key=lambda s: km(s, mouth))
    return round(best[0], 5), round(best[1], 5)


# --- passes -----------------------------------------------------------------------------------------------------

def gnis_gap(features: dict, range_point, before, after) -> tuple | None:
    """The GNIS gap within RANGE_KM of the range's point nearest the straight way from the stop before to the one
    after."""
    way = shapely.LineString([before, after])
    gaps = [f for f in features.values() if f["class"] == "Gap" and km(f["mouth"], range_point) <= RANGE_KM]
    if not gaps:
        return None
    best = min(gaps, key=lambda f: way.distance(shapely.Point(f["mouth"])))
    return best["mouth"], best["name"], best["id"]


def dem_gap(range_point, before, after) -> tuple[tuple | None, list]:
    """A gap found on the DEM: of the saddle cells (geomorphons at a 1 km lookout, 90 m cells) within RANGE_KM of the
    range's point and in the lower half of its ground, the one that adds least to the straight way from the stop before
    to the stop after. Also returns the wolf's least-cost path between those stops, for comparison."""
    path = least_cost.route(tuple(before), tuple(after), {"mode": "wolf"})["coords"]
    g = grid(range_point, RANGE_KM * 1000, 90)
    _, saddle = forms_grid(g, 1000)
    yy, xx = np.mgrid[:g.z.shape[0], :g.z.shape[1]]
    centre = g.z.shape[0] / 2
    disc = (yy - centre) ** 2 + (xx - centre) ** 2 <= (RANGE_KM * 1000 / 90) ** 2
    low = g.z <= np.median(g.z[disc])
    cells = np.argwhere(saddle & disc & low)
    if not len(cells):
        return None, path
    direct = km(before, after)
    points = [g.lonlat(tuple(c)) for c in cells]
    best = min(points, key=lambda p: km(before, p) + km(p, after) - direct)
    return best, path


# --- the check --------------------------------------------------------------------------------------------------

def ground(lonlat, pct_radius: float = PCT_RADIUS) -> dict:
    """Geomorphon landform at each lookout, a saddle test, and the height percentile within `pct_radius` metres."""
    out = {}
    for lookout in LOOKOUTS:
        res = 30
        g = grid(lonlat, lookout + 2 * res, res)
        r0, c0 = g.cell(lonlat)
        z0 = g.z[r0, c0]
        marks = []
        for dr, dc in N8:
            step = math.hypot(dr, dc) * res
            k = np.arange(1, int(lookout // step) + 1)
            rr, cc = r0 + dr * k, c0 + dc * k
            ok = (rr >= 0) & (rr < g.z.shape[0]) & (cc >= 0) & (cc < g.z.shape[1])
            angles = np.degrees(np.arctan((g.z[rr[ok], cc[ok]] - z0) / (k[ok] * step)))
            up, down = max(angles.max(), 0), max(-angles.min(), 0)
            marks.append("h" if up - down > FLAT_DEG else "l" if down - up > FLAT_DEG else "0")
        lower, higher = marks.count("l"), marks.count("h")
        form = FORMS[lower][higher]
        saddle = any(marks[a] == marks[(a + 4) % 8] == "h" and marks[(a + 2) % 8] == marks[(a + 6) % 8] == "l"
                     for a in range(4))
        out[f"form_{lookout}"] = form
        out[f"saddle_{lookout}"] = saddle
    g = grid(lonlat, pct_radius, 60)
    r0, c0 = g.cell(lonlat)
    yy, xx = np.mgrid[:g.z.shape[0], :g.z.shape[1]]
    disc = (yy - r0) ** 2 + (xx - c0) ** 2 <= (pct_radius / 60) ** 2
    out["height_m"] = round(float(g.z[r0, c0]))
    out["height_pct"] = round(float((g.z[disc] < g.z[r0, c0]).mean() * 100))
    # The slope of a plane fitted to the ground within 500 m: the lie of the land, which the walls of a small
    # arroyo cutting a valley floor do not steepen.
    near = (yy - r0) ** 2 + (xx - c0) ** 2 <= (LOOKOUTS[0] / 60) ** 2
    a = np.column_stack([xx[near] * 60.0, yy[near] * 60.0, np.ones(near.sum())])
    (sx, sy, _), *_ = np.linalg.lstsq(a, g.z[near], rcond=None)
    out["slope_deg"] = round(float(np.degrees(np.arctan(np.hypot(sx, sy)))), 1)
    return out


def saddle_near(lonlat, within: float = SADDLE_NEAR) -> float | None:
    """Metres to the nearest saddle cell (30 m grid, 250 m lookout) within `within` metres, or None."""
    g = grid(lonlat, within + 300, 30)
    _, saddle = forms_grid(g, 250)
    r0, c0 = g.cell(lonlat)
    cells = np.argwhere(saddle)
    if not len(cells):
        return None
    d = np.hypot(cells[:, 0] - r0, cells[:, 1] - c0).min() * 30
    return round(float(d)) if d <= within else None


def check(position: str, lonlat) -> tuple[dict, str]:
    """The ground at a point, measured over the window its position needs, and the verdict on it. A pass may be a
    short way off its point: gazetteer points for gaps are often set beside the col, so a saddle within
    SADDLE_NEAR metres counts."""
    gr = ground(lonlat, EXPECT[position][2])
    if position == "pass" and not (gr["saddle_500"] or gr["saddle_2000"]):
        gr["saddle_near_m"] = saddle_near(lonlat)
    return gr, verdict(position, gr)


def verdict(position: str, gr: dict) -> str:
    forms, (lo, hi), _ = EXPECT[position]
    found = {gr[f"form_{x}"] for x in LOOKOUTS} | ({"saddle"} if any(gr[f"saddle_{x}"] for x in LOOKOUTS) else set())
    near = gr.get("saddle_near_m")
    if position == "pass" and near is not None:
        found.add("saddle")
    # A wide valley floor or plain slopes gently, so the geomorphon can read it as a slope or spur. Gentle ground
    # low in its window counts as floor.
    if position == "floor" and gr.get("slope_deg", 90) <= GENTLE_DEG:
        found |= forms
    if found & forms and lo <= gr["height_pct"] <= hi:
        return f"ok, saddle {near} m away" if near is not None else "ok"
    why = []
    if not found & forms:
        why.append(f"{'/'.join(sorted(found))}, not {'/'.join(sorted(forms))}")
    if not lo <= gr["height_pct"] <= hi:
        why.append(f"height percentile {gr['height_pct']}, not {lo}-{hi}")
    return "flag: " + "; ".join(why)


# --- runs -------------------------------------------------------------------------------------------------------

def resolve_j1(features: dict) -> tuple[list[dict], list[dict]]:
    before, now = stops_at("HEAD"), stops_at(None)
    places = place_points()
    order = sorted(now, key=lambda i: now[i]["sequence"])
    rows, shapes = [], []

    def add_point(stop, kind, lonlat, **props):
        shapes.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": list(lonlat)},
                       "properties": {"stop": stop, "kind": kind, **props}})

    for sid in order:
        spec = POSITIONS.get(sid, {"position": "none"})
        pos = spec["position"]
        row = {"stop": sid, "seq": now[sid]["sequence"], "position": pos,
               "original": before[sid]["lonlat"], "updated": now[sid]["lonlat"]}
        tiers: dict[str, tuple | None] = {}
        if pos == "head":
            f = features[spec["gnis"]]
            tiers["gazetteer"] = f["head"]
            tiers["vector"] = nhd_head(f["name"], f["mouth"])
            head, stem, _ = dem_head(f["mouth"])
            tiers["dem"] = head
            shapes.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": stem},
                           "properties": {"stop": sid, "kind": "dem-main-stem"}})
        elif pos == "between":
            a, b = (features[i] for i in spec["gnis"])
            if a["head"] and b["head"]:
                tiers["gazetteer"] = ((a["head"][0] + b["head"][0]) / 2, (a["head"][1] + b["head"][1]) / 2)
            va, vb = nhd_head(a["name"], a["mouth"]), nhd_head(b["name"], b["mouth"])
            tiers["vector"] = ((va[0] + vb[0]) / 2, (va[1] + vb[1]) / 2) if va and vb else None
            point, divide = dem_between(a["mouth"], b["mouth"])
            tiers["dem"] = point
            if a["head"] and b["head"]:
                tiers["dem+gazetteer"] = dem_between(a["mouth"], b["mouth"], (a["head"], b["head"]))[0]
            if divide:
                shapes.append({"type": "Feature", "geometry": {"type": "MultiPoint", "coordinates": divide},
                               "properties": {"stop": sid, "kind": "dem-divide"}})
        elif pos == "pass":
            i = order.index(sid)
            prev, nxt = now[order[i - 1]]["lonlat"], now[order[i + 1]]["lonlat"]
            rp = places[spec["range"]]
            gap = gnis_gap(features, rp, prev, nxt)
            tiers["gazetteer"] = gap[0] if gap else None
            row["gazetteer_name"] = f"{gap[1]} (GNIS {gap[2]})" if gap else ""
            tiers["vector"] = None
            top, path = dem_gap(rp, prev, nxt)
            tiers["dem"] = top
            shapes.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": path},
                           "properties": {"stop": sid, "kind": "least-cost-path"}})
        for name, p in tiers.items():
            row[name] = p
            if p:
                add_point(sid, name, p)
        add_point(sid, "original", row["original"])
        add_point(sid, "updated", row["updated"])
        # The first tier that answers is the resolver's pick.
        pick = next((tiers[t] for t in ("gazetteer", "vector", "dem") if tiers.get(t)), None)
        row["pick_tier"] = next((t for t in ("gazetteer", "vector", "dem") if tiers.get(t)), "")
        for name in ("original", "updated", "gazetteer", "vector", "dem", "dem+gazetteer"):
            p = row.get(name)
            row[f"{name}_to_updated_km"] = round(km(p, row["updated"]), 2) if p else ""
        if pos != "none":
            for name in ("original", "updated") + tuple(t for t in ("dem", "dem+gazetteer") if tiers.get(t)):
                gr, row[f"check_{name}"] = check(pos, row[name])
                row[f"ground_{name}"] = (f"{gr['form_500']} / {gr['form_2000']}"
                                         f"{' (saddle)' if gr['saddle_500'] or gr['saddle_2000'] else ''}, "
                                         f"{gr['height_m']} m, pct {gr['height_pct']}")
        row["pick"] = pick
        rows.append(row)
        print(f"{sid}: {pos}; " + ", ".join(f"{k}={row[k]}" for k in row if k.startswith(("check_", "pick_tier"))))
    return rows, shapes


def calibrate(features: dict) -> list[dict]:
    """Tier 3 heads against GNIS heads, for every linear GNIS feature around J1 with a head 1 km or more from its
    mouth."""
    box = (-109.4, 31.3, -108.4, 31.9)
    picks = [f for f in features.values() if f["class"] in ("Valley", "Stream", "Arroyo") and f["head"]
             and box[0] < f["mouth"][0] < box[2] and box[1] < f["mouth"][1] < box[3] and km(f["mouth"], f["head"]) >= 1]
    rows = []
    for f in sorted(picks, key=lambda f: f["id"]):
        _, stem, flow_ = dem_head(f["mouth"])
        n = flow_.g.z.shape[1]
        stem_cells = main_stem(flow_, snap(flow_, f["mouth"]))
        row = {"gnis": f["id"], "name": f["name"], "class": f["class"],
               "mouth_to_head_km": round(km(f["mouth"], f["head"]), 2)}
        for area in HEAD_AREAS:
            head = flow_.g.lonlat(divmod(head_on(flow_, stem_cells, area), n))
            row[f"err_km_{area}"] = round(km(head, f["head"]), 2)
        # How far the GNIS head lies from the traced main stem: whether the trace went up the right valley at all.
        row["gnis_head_off_stem_km"] = round(min(km(p, f["head"]) for p in stem), 2)
        rows.append(row)
        print(f"{f['name']} ({f['class']}, {row['mouth_to_head_km']} km): "
              + ", ".join(f"{a}: {row[f'err_km_{a}']}" for a in HEAD_AREAS)
              + f"; off stem {row['gnis_head_off_stem_km']}")
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, keys, lineterminator="\n")
        w.writeheader()
        w.writerows({k: (f"{v[1]:.5f},{v[0]:.5f}" if isinstance(v, tuple) else v) for k, v in r.items()} for r in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--skip-calibration", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    features = gnis()
    rows, shapes = resolve_j1(features)
    write_csv(OUT / "results.csv", rows)
    (OUT / "points.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": shapes}) + "\n")
    if not args.skip_calibration:
        cal = calibrate(features)
        write_csv(OUT / "calibration.csv", cal)
        for area in HEAD_AREAS:
            errs = np.array([r[f"err_km_{area}"] for r in cal])
            print(f"area {area} km²: n {len(errs)}, median {np.median(errs):.2f} km, "
                  f"within 1 km {np.mean(errs <= 1) * 100:.0f} %, within 2 km {np.mean(errs <= 2) * 100:.0f} %")


if __name__ == "__main__":
    main()
