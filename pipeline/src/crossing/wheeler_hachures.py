"""Wheeler-style hachures for a test box (review/stage-9/wheeler-hachures/README.md).

Run from the repo root, with QGIS_ENV set as for crossing.hachures:
    QGIS_ENV=/path/to/qgis uv run --project pipeline python -m crossing.hachures \
        --style wheeler --bbox -109.6 30.5 -108.4 31.6 --out private/cache/relief/wheeler-test

The Wheeler Survey sheets (review/stage-8/wheeler/README.md, "Relief (hachures)") darken steep ground by packing
short strokes closer, not by widening them, leave every crest, spur and summit as a thin white parting, keep mesa
tops and valley floors as blank paper, and draw an escarpment as one comb of wedge strokes hanging from the rim.
This builds that look for one box, on the production tile grid (crossing.hachures.tiles), and never writes to the
production cache:
  1. The vendored generator runs on each 40 km tile at the WHEELER settings (closer at the steep end, sparser at
     the gentle end, and down to MIN_SLOPE), writing whole fall lines ("main").
  2. Each fall line, taken downhill, is cut into strokes STROKE_MM long (gentle to steep ground), one per row. Rows
     follow a field (row_field()) proportional to height under a smoothed slope, so strokes on neighbouring lines
     line up across the slope, as Wheeler's do; a row is a stroke length over DUTY.
  3. Strokes are cleared within one stroke length of a ridge line (ridge_network()), inside a summit disc
     (summits()), on flat tops and valley floors (flats()), and in an escarpment's comb (rims()).
  4. Each escarpment gets one row of wedge strokes, perpendicular to the rim and thick at the rim (rim layer).

Lengths and widths are set in millimetres at DESIGN_ZOOM on a 96 dpi screen and turned into metres on the ground
with px_m(): MapLibre's zoom z is 512 px tiles, so one CSS pixel is 78,271.52 m * cos(latitude) / 2^z, and one
pixel is 25.4 / 96 = 0.2646 mm.

Writes, in the --out folder: tiles/ (the generator's tiles and smoothed DEMs), hachure.geojson (strokes: Slope,
Aspect, Rand as in crossing.hachures, plus `cls`: flat, gentle, moderate or steep, from Slope), rim.geojson (wedge
polygons) and stats.json (run time, stroke counts by class, ink cover by class).
"""

import json
import math
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
import shapely
from rasterio.features import rasterize
from rasterio.transform import rowcol
from scipy.ndimage import (
    distance_transform_edt,
    gaussian_filter,
    label,
    map_coordinates,
    maximum_filter,
    minimum_filter,
)
from shapely import LineString, Polygon, box

from crossing import hachures as h
from crossing.paths import DATA

# The design zoom and latitude: zoom 11 is where the lab's shared type scale is set; 31 N is the middle of the
# bootheel and Bavispe test box.
DESIGN_ZOOM = 11
DESIGN_LAT = 31.05
MM_PER_PX = 25.4 / 96


def px_m(px: float, zoom: float = DESIGN_ZOOM, lat: float = DESIGN_LAT) -> float:
    """Metres on the ground under `px` CSS pixels at a MapLibre zoom (512 px tiles)."""
    return px * 78_271.517 * math.cos(math.radians(lat)) / 2**zoom


def mm_m(mm: float) -> float:
    """Metres on the ground under `mm` millimetres on a 96 dpi screen at DESIGN_ZOOM."""
    return px_m(mm / MM_PER_PX)


# Wheeler's strokes (packet, finding 6): about 0.14 mm wide everywhere; median 0.45 mm long on gentle ground and
# 0.65 to 0.8 mm on steep ground. Steep is from STEEP_DEG, gentle up to GENTLE_DEG, on the smoothed 30 m DEM
# (its slopes run a few degrees below the raw DEM's).
STROKE_WIDTH_MM = 0.14
STROKE_MM = (0.45, 0.72)
GENTLE_DEG, STEEP_DEG = 10, 25
# The share of each row a stroke fills: broken strokes, near a stipple, on gentle ground; near-solid on steep
# ground. A row is a stroke length over its DUTY; each stroke starts where its line enters a row, and stops at its
# length or at ROW_END of the row, so there is always a gap before the next row.
DUTY = (0.55, 0.85)
ROW_END = 0.92
SHORTEST = 0.35  # strokes cut shorter than this share of their length are dropped
STEP = 5  # metres between samples along a fall line

# The generator: lines MIN_SLOPE and up, 4.5 cells (135 m) apart at the gentle end and 1 cell (30 m) at STEEP_DEG
# and above. The generator stops and starts lines to keep its spacing, so they lie further apart on average than
# these figures; at 1.3 to 7 cells the box drew only 18% ink on steep ground and 1.6% on gentle ground.
MIN_SLOPE = 6
WHEELER = h.FINE | {"min_spacing": 1, "max_spacing": 4.5, "min_slope": MIN_SLOPE, "max_slope": STEEP_DEG,
                    "output": "main", "zooms": (10, 12)}

# Ridge lines (ridge_network()): cells where at least RIDGE_AREA cells drain to them on the upside-down DEM, at
# least RIDGE_RELIEF metres above the lowest ground within about a kilometre (so plains have no ridges).
RIDGE_AREA = 150
RIDGE_RELIEF = 40
RIDGE_CLEAR = 1.0  # strokes are cleared within this many stroke lengths of a ridge line
# Summits (summits()): the glyph summits, and DEM peaks highest within SUMMIT_WINDOW metres and SUMMIT_RELIEF metres
# above the ground around; each gets a clear disc SUMMIT_DISC stroke lengths across.
SUMMIT_WINDOW = 600
SUMMIT_RELIEF = 60
SUMMIT_DISC = 1.0
# Flats (flats()): slope under FLAT_DEG, less than FLAT_RELIEF metres of relief within FLAT_RADIUS metres, and in the
# top or bottom FLAT_POSITION of the relief within POSITION_RADIUS metres.
FLAT_DEG = 4
FLAT_RELIEF = 15
FLAT_RADIUS = 150
FLAT_POSITION = 0.35
POSITION_RADIUS = 1_500
FLAT_AREA = 0.05e6  # m2; smaller flats are left to the generator
# Rims (rims()): slope under RIM_FLAT_DEG within RIM_REACH metres of slope over RIM_STEEP_DEG, the flat side higher by
# at least RIM_DROP metres, in runs of at least RIM_LENGTH metres. Wedges: RIM_SPACING_PX apart at the design zoom,
# RIM_TOP_MM wide at the rim (about 23% ink in the comb, as measured on sheet 70A), RIM_MM long.
RIM_FLAT_DEG, RIM_STEEP_DEG = 6, 25
RIM_REACH = 100
RIM_DROP = 30
RIM_LENGTH = 300
RIM_SPACING_PX = 3
RIM_TOP_MM = 0.37
RIM_MM = (0.5, 1.0)

GLYPHS = DATA / "mountain_glyphs.geojson"


def lerp_slope(slope: np.ndarray, pair: tuple[float, float]) -> np.ndarray:
    """`pair[0]` at GENTLE_DEG and below, `pair[1]` at STEEP_DEG and above, linear between."""
    t = np.clip((slope - GENTLE_DEG) / (STEEP_DEG - GENTLE_DEG), 0, 1)
    return pair[0] + t * (pair[1] - pair[0])


def stroke_length(slope: np.ndarray) -> np.ndarray:
    """Stroke length on the ground, metres, by slope in degrees."""
    return lerp_slope(slope, (mm_m(STROKE_MM[0]), mm_m(STROKE_MM[1])))


class Ground:
    """A tile's smoothed DEM (from crossing.hachures.prepare_dem) and the rasters the strokes are cut against."""

    def __init__(self, dem_path: Path):
        with rasterio.open(dem_path) as src:
            self.z, self.t = src.read(1).astype(float), src.transform
        self.cell = self.t.a
        gy, gx = np.gradient(self.z, self.t.e, self.t.a)
        self.gx, self.gy = gx, gy
        self.slope = np.degrees(np.arctan(np.hypot(gx, gy)))
        k = lambda metres: 2 * round(metres / self.cell) + 1  # noqa: E731  (a window this many metres either side)
        self.low_1km = minimum_filter(self.z, size=k(500))

    def sample(self, raster: np.ndarray, x: np.ndarray, y: np.ndarray, order: int = 1) -> np.ndarray:
        """Values of a raster at UTM points (bilinear by default)."""
        cols = (x - self.t.c) / self.t.a - 0.5
        rows = (y - self.t.f) / self.t.e - 0.5
        return map_coordinates(raster, [rows, cols], order=order, mode="nearest")

    def distance(self, mask: np.ndarray) -> np.ndarray:
        """Metres from each cell to the nearest cell of `mask` (infinite where the mask is empty)."""
        if not mask.any():
            return np.full(mask.shape, np.inf)
        return distance_transform_edt(~mask) * self.cell


def ridge_network(g: Ground) -> np.ndarray:
    """Ridge cells: D8 flow accumulation on the upside-down DEM, where water would gather along crests and spurs.

    Each cell passes its count to the neighbour with the steepest rise; summits receive and pass nothing. Counts
    are summed in waves from the cells nobody drains to, so every cell is added once all its donors are in.
    """
    z = g.z
    rows, cols = z.shape
    padded = np.pad(z, 1, constant_values=-np.inf)
    index = np.arange(z.size).reshape(z.shape)
    best = np.zeros(z.shape)
    receiver = np.full(z.shape, -1, dtype=np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == dx == 0:
                continue
            rise = (padded[1 + dy:1 + dy + rows, 1 + dx:1 + dx + cols] - z) / math.hypot(dy, dx)
            better = rise > best
            best[better] = rise[better]
            receiver[better] = (index + dy * cols + dx)[better]
    receiver = receiver.ravel()
    acc = np.ones(z.size)
    has = receiver >= 0
    waiting = np.bincount(receiver[has], minlength=z.size)
    front = np.flatnonzero(waiting == 0)
    while front.size:
        front = front[receiver[front] >= 0]
        to = receiver[front]
        np.add.at(acc, to, acc[front])
        np.subtract.at(waiting, to, 1)
        to = np.unique(to)
        front = to[waiting[to] == 0]
    acc = acc.reshape(z.shape)
    return (acc >= RIDGE_AREA) & (z - g.low_1km >= RIDGE_RELIEF)


def glyph_summits() -> np.ndarray:
    """The map's summit glyphs (not passes) in UTM, as an (n, 2) array."""
    feats = json.loads(GLYPHS.read_text())["features"]
    lonlat = np.array([f["geometry"]["coordinates"][:2] for f in feats if f["properties"].get("landform") != "pass"])
    return np.column_stack(h.to_utm(lonlat[:, 0], lonlat[:, 1]))


def summits(g: Ground, glyphs: np.ndarray) -> np.ndarray:
    """Summit cells: the glyph summits on the tile, and every cell that is the highest within SUMMIT_WINDOW
    metres and SUMMIT_RELIEF metres above the lowest ground within about a kilometre."""
    k = 2 * round(SUMMIT_WINDOW / 2 / g.cell) + 1
    mask = (g.z == maximum_filter(g.z, size=k)) & (g.z - g.low_1km >= SUMMIT_RELIEF)
    rows, cols = rowcol(g.t, glyphs[:, 0], glyphs[:, 1])
    rows, cols = np.asarray(rows), np.asarray(cols)
    inside = (rows >= 0) & (rows < mask.shape[0]) & (cols >= 0) & (cols < mask.shape[1])
    mask[rows[inside], cols[inside]] = True
    return mask


def flats(g: Ground) -> np.ndarray:
    """Mesa tops and valley floors: flat, with little relief close by, and at the top or bottom of the relief
    around, in patches of at least FLAT_AREA."""
    k = lambda metres: 2 * round(metres / g.cell) + 1  # noqa: E731
    near = maximum_filter(g.z, size=k(FLAT_RADIUS)) - minimum_filter(g.z, size=k(FLAT_RADIUS))
    high, low = maximum_filter(g.z, size=k(POSITION_RADIUS)), minimum_filter(g.z, size=k(POSITION_RADIUS))
    position = (g.z - low) / np.maximum(high - low, 1)
    flat = ((gaussian_filter(g.slope, 1) < FLAT_DEG) & (near < FLAT_RELIEF)
            & ((position <= FLAT_POSITION) | (position >= 1 - FLAT_POSITION)))
    labels, _ = label(flat)
    big = np.bincount(labels.ravel()) * g.cell**2 >= FLAT_AREA
    big[0] = False
    return big[labels]


def row_field(g: Ground) -> np.ndarray:
    """A field that changes by one per stroke row along a fall line: height over the height one row spans, both from
    a slope smoothed over about 300 m, so neighbouring lines share their rows."""
    slope = np.maximum(gaussian_filter(g.slope, 10), 3)
    period = stroke_length(slope) / lerp_slope(slope, DUTY)
    return g.z / (period * np.tan(np.radians(slope)))


def contour_lines(g: Ground, field: np.ndarray, level: float) -> list[np.ndarray]:
    """Lines (UTM, (n, 2) arrays) where a raster on the tile's grid crosses `level`, from gdal_contour."""
    with tempfile.TemporaryDirectory() as tmp:
        raster, lines = Path(tmp) / "f.tif", Path(tmp) / "f.geojson"
        with rasterio.open(raster, "w", driver="GTiff", width=field.shape[1], height=field.shape[0], count=1,
                           dtype="float32", crs=h.CRS, transform=g.t) as dst:
            dst.write(field.astype("float32"), 1)
        subprocess.run(["gdal_contour", "-q", "-fl", str(level), "-f", "GeoJSON", str(raster), str(lines)], check=True)
        return [np.array(f["geometry"]["coordinates"])[:, :2] for f in json.loads(lines.read_text())["features"]]


def densify(xy: np.ndarray, step: float) -> np.ndarray:
    dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
    s = np.arange(0, dist[-1] + step / 2, step) if dist[-1] > 0 else np.array([0.0])
    return np.column_stack([np.interp(s, dist, xy[:, 0]), np.interp(s, dist, xy[:, 1])])


def runs(keep: np.ndarray) -> list[tuple[int, int]]:
    """(start, end) index pairs, end exclusive, of each run of True."""
    edges = np.flatnonzero(np.diff(np.concatenate([[0], keep.astype(np.int8), [0]])))
    return list(zip(edges[::2], edges[1::2], strict=True))


def rims(g: Ground) -> tuple[list[Polygon], np.ndarray]:
    """Escarpment combs: the wedge polygons, and a mask of the ground their comb covers.

    The rim is the edge of flat ground (under RIM_FLAT_DEG, smoothed so specks of flat do not count) where slope
    over RIM_STEEP_DEG lies within RIM_REACH metres, lower than the flat side, and the ground drops RIM_DROP metres
    or more close by. Along each run of rim, a wedge every RIM_SPACING_PX at the design zoom points down the fall
    line of the face below, RIM_TOP_MM wide at the rim and as long as the face (RIM_MM).
    """
    steep = g.slope > RIM_STEEP_DEG
    if not steep.any():
        return [], np.zeros(g.z.shape, bool)
    near, (sr, sc) = distance_transform_edt(~steep, return_indices=True)
    near *= g.cell
    drop = g.z - minimum_filter(g.z, size=2 * round(300 / g.cell) + 1)
    flat = gaussian_filter((g.slope < RIM_FLAT_DEG).astype(float), 2)
    spacing, top = px_m(RIM_SPACING_PX), mm_m(RIM_TOP_MM)
    shortest, longest = mm_m(RIM_MM[0]), mm_m(RIM_MM[1])
    wedges, lines = [], []
    for xy in contour_lines(g, flat, 0.5):
        pts = densify(xy, 10)
        x, y = pts[:, 0], pts[:, 1]
        r = np.clip(np.round((y - g.t.f) / g.t.e - 0.5).astype(int), 0, g.z.shape[0] - 1)
        c = np.clip(np.round((x - g.t.c) / g.t.a - 0.5).astype(int), 0, g.z.shape[1] - 1)
        below = g.z[sr[r, c], sc[r, c]]
        ok = (near[r, c] <= RIM_REACH) & (g.sample(g.z, x, y) > below) & (g.sample(drop, x, y) >= RIM_DROP)
        for a, b in runs(ok):
            if (b - a) * 10 < RIM_LENGTH:
                continue
            rim = LineString(pts[a:b])
            lines.append(rim)
            for d in np.arange(spacing / 2, rim.length, spacing):
                p = np.array(rim.interpolate(d).coords[0])
                pr, pc = rowcol(g.t, p[0], p[1])
                pr, pc = min(max(pr, 0), g.z.shape[0] - 1), min(max(pc, 0), g.z.shape[1] - 1)
                qr, qc = sr[pr, pc], sc[pr, pc]
                fall = -np.array([g.gx[qr, qc], g.gy[qr, qc]])
                if not np.hypot(*fall):
                    continue
                fall /= np.hypot(*fall)
                # The face runs down the fall line from the rim until the slope eases below RIM_STEEP_DEG - 5.
                s = np.arange(0, longest + 1, 6.0)
                slope = g.sample(g.slope, p[0] + s * fall[0], p[1] + s * fall[1])
                entered = np.flatnonzero(slope > RIM_STEEP_DEG)
                length = longest
                if entered.size:
                    eased = np.flatnonzero((slope < RIM_STEEP_DEG - 5) & (s > s[entered[0]]))
                    if eased.size:
                        length = float(np.clip(s[eased[0]], shortest, longest))
                side = np.array([-fall[1], fall[0]]) * top / 2
                wedges.append(Polygon([p + side, p + fall * length, p - side]))
    zone = np.zeros(g.z.shape, bool)
    if lines:
        zone = rasterize([(rim, 1) for rim in lines], out_shape=g.z.shape, transform=g.t, all_touched=True) > 0
        zone = g.distance(zone) <= longest + g.cell
    return wedges, zone


# Ground classes for the counts and ink cover, by slope on the smoothed DEM: Wheeler's "gentle flanks" (packet,
# about 5% ink) and "steep mountain sides" (40 to 50%), the ground between them, and the escarpment combs (23%).
CLASSES = {"gentle": (MIN_SLOPE, 15), "moderate": (15, STEEP_DEG), "steep": (STEEP_DEG, 90)}
GROUNDS = ["flat", *CLASSES, "rim"]


def stroke_class(slope: float) -> str:
    return next((name for name, (lo, hi) in CLASSES.items() if lo <= slope < hi), "flat")


def ground_classes(g: Ground, comb: np.ndarray) -> np.ndarray:
    """Each cell's index in GROUNDS."""
    out = np.zeros(g.z.shape, np.int8)
    for i, (lo, hi) in enumerate(CLASSES.values(), start=1):
        out[(g.slope >= lo) & (g.slope < hi)] = i
    out[comb] = len(GROUNDS) - 1
    return out


def tile_strokes(name: str, core: Polygon, area: Polygon, folder: Path, glyphs: np.ndarray) -> dict:
    """The tile's strokes and wedges inside `area` (its core within the box) as GeoJSON features, and the
    tallies for the ink cover: ground area of each class, stroke lengths by the class under their middle."""
    g = Ground(folder / f"{name}.tif")
    ridge_near = g.distance(ridge_network(g))
    summit_near = g.distance(summits(g, glyphs))
    flat = flats(g)
    rows = row_field(g)
    wedges, comb = rims(g)
    sample = h.sampler(folder / f"{name}.tif")
    strokes, mids = [], []
    for f in json.loads((folder / f"{name}-main.geojson").read_text())["features"]:
        line = h.reproject(h.to_utm, LineString(f["geometry"]["coordinates"]))
        if not line.intersects(area):
            continue
        pts = densify(np.asarray(line.coords), STEP)
        if g.sample(g.z, pts[:1, 0], pts[:1, 1])[0] < g.sample(g.z, pts[-1:, 0], pts[-1:, 1])[0]:
            pts = pts[::-1]  # downhill, so each stroke hangs from the top of its row
        x, y = pts[:, 0], pts[:, 1]
        slope = g.sample(g.slope, x, y)
        length = stroke_length(slope)
        row = -g.sample(rows, x, y)  # grows downhill
        along = np.arange(len(pts)) * STEP
        entered = np.concatenate([[True], np.floor(row[1:]) != np.floor(row[:-1])])
        since = along - np.maximum.accumulate(np.where(entered, along, 0))
        keep = (since < length) & (np.mod(row, 1) < ROW_END) & shapely.contains_xy(area, x, y)
        keep &= g.sample(ridge_near, x, y) >= RIDGE_CLEAR * length
        keep &= g.sample(summit_near, x, y) >= SUMMIT_DISC * length / 2
        keep &= (g.sample(flat, x, y, order=0) == 0) & (g.sample(comb, x, y, order=0) == 0)
        for a, b in runs(keep):
            if b - a < 2 or (b - a - 1) * STEP < SHORTEST * length[a:b].mean():
                continue
            dash = LineString(pts[a:b]).simplify(2)
            props, coords = h.stroke_properties(sample, dash)
            props["cls"] = stroke_class(props["Slope"])
            strokes.append({"type": "Feature", "tippecanoe": {"minzoom": 10, "maxzoom": 12}, "properties": props,
                            "geometry": {"type": "LineString", "coordinates": coords}})
            mids.append((*pts[(a + b) // 2], dash.length))
    kept = [w for w in wedges if area.contains(w.centroid)]
    rim_feats = [{"type": "Feature", "tippecanoe": {"minzoom": 10, "maxzoom": 12}, "properties": {},
                  "geometry": {"type": "Polygon", "coordinates": [[(round(x, 6), round(y, 6)) for x, y in
                                                                   h.reproject(h.to_wgs, w).exterior.coords]]}}
                 for w in kept]
    classes = ground_classes(g, comb)
    inside = rasterize([(area, 1)], out_shape=g.z.shape, transform=g.t) > 0
    ground = np.bincount(classes[inside], minlength=len(GROUNDS)) * g.cell**2
    lengths: dict[str, list[float]] = {k: [] for k in GROUNDS}
    if mids:
        m = np.array(mids)
        for i, length in zip(g.sample(classes, m[:, 0], m[:, 1], order=0), m[:, 2], strict=True):
            lengths[GROUNDS[int(i)]].append(float(length))
    return {"strokes": strokes, "rims": rim_feats, "ground": dict(zip(GROUNDS, ground.tolist(), strict=True)),
            "lengths": lengths, "wedge_area": sum(w.area for w in kept), "comb_area": sum(map(comb_band, kept))}


def comb_band(wedge: Polygon) -> float:
    """The ground one wedge stands for: its length down the face by the spacing along the rim."""
    a, apex, b = (np.array(p) for p in wedge.exterior.coords[:3])
    return float(np.hypot(*(apex - (a + b) / 2))) * px_m(RIM_SPACING_PX)


# The lab's stroke width (site/src/lab/wheeler/subset/hachures.ts) in CSS pixels by zoom, and the share of strokes
# it draws there (by Rand), so the measured cover is the cover the lab shows.
STYLE_WIDTH_PX = {10: 0.42, 11: STROKE_WIDTH_MM / MM_PER_PX, 12: 0.8}
STYLE_SHARE = {10: 0.7, 11: 1.0, 12: 1.0}


def ink_cover(lengths: dict[str, list[float]], ground: dict[str, float], wedge_area: float) -> dict:
    """Ink as a percentage of each ground class at zooms 10-12: stroke bodies with their round caps, and the
    wedges (which are drawn to scale, so their cover is the same at every zoom). Overlaps are counted twice."""
    out = {}
    for z, width_px in STYLE_WIDTH_PX.items():
        w = px_m(width_px, z)
        row = {}
        for cls, area in ground.items():
            ink = sum(length * w + math.pi * w * w / 4 for length in lengths[cls]) * STYLE_SHARE[z]
            ink += wedge_area if cls == "rim" else 0
            row[cls] = round(100 * ink / area, 1) if area else None
        out[z] = row
    return out


def build(bbox: tuple[float, float, float, float], out: Path, jobs: int, qgis_env: Path) -> None:
    """Hachures for the box `bbox` (west, south, east, north in degrees) into the folder `out`."""
    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=True)
    folder = (out / "tiles").resolve()
    s = WHEELER | {"folder": folder}
    region = h.reproject(h.to_utm, box(*bbox).segmentize(0.01)).intersection(h.coverage().buffer(-60))
    grid = h.tiles(region, s["tile"])
    print(f"wheeler: {len(grid)} tiles of {s['tile'] // 1000} km over {region.area / 1e6:,.0f} km2", flush=True)
    with ThreadPoolExecutor(jobs) as pool:
        list(pool.map(lambda t: h.run_tile("wheeler", *t, s, qgis_env), grid))
    generated = time.monotonic() - started
    glyphs = glyph_summits()
    with ThreadPoolExecutor(jobs) as pool:
        results = list(pool.map(lambda t: tile_strokes(*t, t[1].intersection(region), folder, glyphs), grid))
    strokes = [f for r in results for f in r["strokes"]]
    wedges = [f for r in results for f in r["rims"]]
    for layer, feats in (("hachure", strokes), ("rim", wedges)):
        (out / f"{layer}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    ground = {k: sum(r["ground"][k] for r in results) for k in GROUNDS}
    lengths = {k: [v for r in results for v in r["lengths"][k]] for k in GROUNDS}
    stats = {
        "bbox": bbox, "tiles": len(grid), "area_km2": round(region.area / 1e6),
        "seconds": {"generator": round(generated), "total": round(time.monotonic() - started)},
        "strokes": {**{c: sum(f["properties"]["cls"] == c for f in strokes) for c in GROUNDS[:-1]},
                    "rim_wedges": len(wedges), "all": len(strokes)},
        "strokes_by_ground": {k: len(v) for k, v in lengths.items()},
        "median_length_m": {k: round(float(np.median(v))) for k, v in lengths.items() if v},
        "ground_km2": {k: round(v / 1e6, 1) for k, v in ground.items()},
        "ink_cover_percent": ink_cover(lengths, ground, sum(r["wedge_area"] for r in results)),
        # Within the combs themselves, as the packet measured the escarpment combs of sheet 70A.
        "comb_cover_percent": round(100 * sum(r["wedge_area"] for r in results)
                                    / max(sum(r["comb_area"] for r in results), 1), 1),
        "design": {"zoom": DESIGN_ZOOM, "m_per_px": round(px_m(1), 2), "stroke_m": [round(mm_m(v)) for v in STROKE_MM],
                   "width_px": round(STROKE_WIDTH_MM / MM_PER_PX, 2), "rim_spacing_m": round(px_m(RIM_SPACING_PX))},
    }
    (out / "stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    for layer in ("hachure", "rim"):
        path = out / f"{layer}.geojson"
        print(f"{path}: {path.stat().st_size / 1e6:.0f} MB")
