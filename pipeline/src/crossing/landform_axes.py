"""Label lines for landform names: one line along each range, valley, plain, mesa and plateau in the story box,
so the name can be set in spaced capitals along the landform, as the Wheeler Survey sheets letter them
(review/stage-8/wheeler/README.md; decision 0023).

Run from the repo root: uv run --project pipeline python -m crossing.landform_axes
Reads data/places.geojson, the GNIS (AZ, NM) and GeoNames (MX) dumps in private/cache/gazetteer/, the GMBA
Mountain Inventory v2 zip in private/cache/gmba/, the Copernicus DEM, and pipeline/seeds/landform_axes.toml.
Writes data/landforms.geojson and prints one line per landform kept, then the names it could not place.

Which landforms:
  - every range, valley and plain in data/places.geojson, under the book's name and from its `first_seen`;
  - named landforms the book never names, from `first_seen` 1-01: GNIS Range (names ending in "Mountains" or
    "Range"), Valley (names ending in "Valley", with a head point), Plain, and Summit records named as mesas;
    GeoNames MTS (names starting "Sierra" or "Serranía"), VAL, PLN, PLAT and MESA; GMBA ranges (basic and
    point-defined ranges with a recognised name, up to GMBA_MAX_KM2, not the aggregates and support polygons).
    The rule that keeps the count sane (choose()): GMBA ranges and GNIS valleys first, longest first; then the
    DEM lines, ranges by the height of their core above the valley floor, the others longest first. Each kind
    has a minimum length and a cap (MIN_KM, CAP), and a line whose middle lies within SPACING_KM (or OVERLAP of
    the longer line) of a kept line of the same kind is dropped as a second name for the same ground. The build
    keeps about 310 lines in the box.

How each line is made (the `axis` property):
  - gmba: the principal axis of the GMBA polygon, where the gazetteer range has one of the same name close by.
  - gnis: for GNIS valleys, the line from the primary point (the mouth) to the source point (the head).
  - dem: elsewhere, the principal axis of the region of the DEM that the gazetteer point sits in (dem_axis()).
    Where that region runs on past its window (most sierras of Sonora and Chihuahua), only its part near the
    point is used and the line follows the grain of the ground there (grain()); such lines have certainty
    "inferred".
  - The hand-edit table, applied last, can rotate, lengthen, move, bend or drop a line, or keep one the rules
    left out, each with a reason (written to `reasoning`).
A principal axis is the long axis of a cloud of points: the eigenvector of their covariance with the larger
eigenvalue. The line runs AXIS_SPAN standard deviations each way along it through the cloud's centroid and is
turned to read left to right. `elongation` is the square root of the eigenvalue ratio (1 for a round region);
below ROUND the line is laid east-west, as a horizontal label.

`len_m` is the line's length and `mpp0` the metres per pixel at zoom 0 (256 px tiles) at its middle, so a style
can work out how many pixels the line spans at any zoom and space the letters to fill it.
"""

import json
import math
import re
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyproj import Geod
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy import ndimage

from crossing.dem import COPERNICUS, COPERNICUS_REGION, build_vrt, tiles
from crossing.gazetteer import geonames_rows, gnis_rows
from crossing.paths import CACHE, DATA, SEEDS
from crossing.text import fold_name

OUT = DATA / "landforms.geojson"
EDITS = SEEDS / "landform_axes.toml"
GMBA_ZIP = CACHE / "gmba" / "GMBA_Inventory_v2.0_standard.zip"
GMBA_LAYER = "GMBA_Inventory_v2.0_standard"
# The packet's box (review/stage-8/wheeler/README.md, Data sources): every journey and every named landform of
# the book lies inside it. West, south, east, north.
BOX = (-112.0, 28.0, -104.0, 34.0)
GEOD = Geod(ellps="WGS84")
# Metres per degree of latitude, and of longitude at the equator, on the WGS 84 ellipsoid near 31° N: close
# enough for the local plane each landform is measured in (a few tens of kilometres across).
M_PER_DEG_LAT = 110_850
M_PER_DEG_LON = 111_320

# Lines run this many standard deviations each way from the centroid. For an even strip of length L the standard
# deviation along it is L / sqrt(12), so 1.8 gives a line about as long as the landform.
AXIS_SPAN = 1.8

# The DEM method, by kind (dem_axis()). Ranges are found by height above the local valley floor; mesas and
# plateaus by flat ground near their top; plains and valleys by flat ground low in the window.
CELL_M = {"range": 150, "mesa": 90, "plateau": 150, "plain": 150, "valley": 150}
RADIUS_KM = {"range": 30, "mesa": 12, "plateau": 30, "plain": 30, "valley": 30}
# The share of the local relief a cell must rise above the floor (ranges) or stay below (plains).
SHARE = {"range": 0.25, "plain": 0.25, "valley": 0.25}
# Mesa and plateau tops, plains and valley floors: slopes below this many degrees.
FLAT_DEG = {"mesa": 8, "plateau": 8, "plain": 2, "valley": 2}
# A top is the ground no more than this far below the highest ground near the point (m).
TOP_DROP_M = {"mesa": 80, "plateau": 200}
# The landform's own top or core is measured this close to the point (km), so a higher neighbour does not set it.
NEAR_KM = {"range": 6, "mesa": 1.5, "plateau": 6, "plain": 30, "valley": 30}
# Ranges: the valley floor is the lowest ground within this distance (km), smoothed.
VALLEY_KM = 8

# Gazetteer landforms the book never names are kept if at least this long (km), the longest first, up to CAP of
# each kind. Mesas must also be clearly longer than wide (MESA_MIN_ELONG): GeoNames calls many rough summit
# areas of the Sierra Madre "Mesa", and only a long flat top suits a name along an axis.
MIN_KM = {"range": 12, "valley": 15, "plain": 10, "plateau": 10, "mesa": 2.5}
CAP = {"range": 200, "valley": 60, "plain": 30, "plateau": 10, "mesa": 40}
MESA_MIN_ELONG = 1.6
# A second line whose middle is within this share of a longer line's length from that line's middle names the
# same ground (two GeoNames points in one massif find the same DEM region). However short the lines, two middles
# of one kind are kept at least SPACING_KM apart, so the Sierra Madre's many named sierras do not crowd the map.
OVERLAP = 0.3
SPACING_KM = 15
# Ranges the book does not name: only names that call the landform a range, not hills, cerros or ridges.
RANGE_WORDS = re.compile(r"^(Sierra|Sierrita|Serrania|Serranía) |( Mountains| Range)$")
# GMBA polygons attach to a gazetteer range of the same name whose point is at most this far outside (km).
GMBA_NEAR_KM = 10
# Duplicate gazetteer entries: the same name and kind within this distance (km) are one landform.
SAME_KM = 20
GMBA_FEATURES = {"Mountain range with well-recognized name", "Point Defined Range"}
# GMBA outlines larger than this (km²) are physiographic provinces (Sierras Plegadas del Norte), not ranges.
GMBA_MAX_KM2 = 3000
# A DEM region that runs into the edge of its window along more than this share of the edge is not a landform
# of its own but part of something larger (a gazetteer "mesa" point out on a plain finds the whole plain, a sierra
# point the whole Sierra Madre). Such a line is cut to the region's part within LOCAL_KM of the point and has
# certainty "inferred"; among landforms the book does not name, only ranges keep such lines.
EDGE_SHARE = 0.03
LOCAL_KM = 12
# Below this elongation a region has no clear long axis, and its line is laid east-west, as a horizontal label.
ROUND = 1.5
# A gazetteer landform with the name of one of the book's within this distance (km) is the same one, under
# another source (GeoNames' "Animas Valley" is the Mexican end of the book's).
BOOK_KM = 60

LICENCE = {"gnis": "Public domain", "geonames": "CC BY 4.0", "gmba": "CC BY 4.0",
           "copernicus-glo30": "Copernicus WorldDEM-30 licence"}
NOTE = {
    "gmba": "Label line along the long axis of the GMBA Mountain Inventory outline of the range.",
    "gnis": "Label line from the mouth to the head of the valley, as GNIS records them.",
    "dem": "Label line along the long axis of the ground around the gazetteer point, found in the Copernicus DEM.",
}
METHOD = {"gmba": "computed", "gnis": "gazetteer", "dem": "generated"}


@dataclass
class Landform:
    name: str
    kind: str
    lon: float
    lat: float
    name_source: str  # gnis, geonames or gmba
    name_id: str
    head: tuple[float, float] | None = None  # GNIS valleys: the source point
    place: dict | None = None  # the places.geojson properties, if the book names it
    polygon: shapely.Geometry | None = None
    gmba_id: str | None = None
    unbounded: bool = False
    relief: float = 0.0
    # Filled in by place_line().
    line: list[tuple[float, float]] = field(default_factory=list)
    axis: str = ""
    elongation: float | None = None
    reason: str | None = None

    @property
    def ends(self) -> list[tuple[float, float]]:
        return [(self.lon, self.lat)] + ([self.head] if self.head else [])

    @property
    def key(self) -> str:
        return match_key(self.name)


def match_key(name: str) -> str:
    """The name folded for matching across sources: no accents, case, articles or qualifiers in brackets."""
    words = fold_name(re.sub(r"\(.*?\)", "", name)).split()
    return " ".join(w for w in words if w not in {"de", "del", "la", "las", "el", "los", "the"})


def in_box(lon: float, lat: float) -> bool:
    return BOX[0] <= lon <= BOX[2] and BOX[1] <= lat <= BOX[3]


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    return GEOD.inv(a[0], a[1], b[0], b[1])[2] / 1000


def slug(name: str) -> str:
    return "-".join(fold_name(name).split())


# --- Sources -------------------------------------------------------------------------------------------------------

def gnis_landforms() -> dict[str, Landform]:
    """GNIS records in the box that name a range, valley, plain, plateau or mesa, by feature id."""
    out = {}
    for r in gnis_rows():
        lat, lon = float(r["prim_lat_dec"] or 0), float(r["prim_long_dec"] or 0)
        if not in_box(lon, lat):
            continue
        name, cls = r["feature_name"], r["feature_class"]
        words = fold_name(name).split()
        if cls == "Range":
            kind = "range"
        elif cls == "Valley":
            kind = "valley"
        elif cls == "Plain":
            kind = "plateau" if "plateau" in words else "plain"
        elif cls == "Summit" and "mesa" in words:
            kind = "mesa"
        else:
            continue
        head = None
        if r["source_lat_dec"] and float(r["source_lat_dec"]):
            head = (float(r["source_long_dec"]), float(r["source_lat_dec"]))
        out[r["feature_id"]] = Landform(name, kind, lon, lat, "gnis", r["feature_id"], head=head)
    return out


GEONAMES_KINDS = {"MTS": "range", "VAL": "valley", "PLN": "plain", "PLAT": "plateau", "MESA": "mesa"}


def geonames_landforms() -> dict[str, Landform]:
    """GeoNames Mexico records in the box that name a range, valley, plain, plateau or mesa, by geonameid."""
    out = {}
    for r in geonames_rows():
        lat, lon = float(r[4]), float(r[5])
        if r[7] in GEONAMES_KINDS and in_box(lon, lat):
            out[r[0]] = Landform(r[1], GEONAMES_KINDS[r[7]], lon, lat, "geonames", r[0])
    return out


def gmba_ranges() -> list[Landform]:
    """GMBA ranges whose outline's centre lies in the box (the named ranges, not aggregates or support polygons)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "gmba.geojson"
        sql = f'SELECT GMBA_V2_ID, MapName, Feature, Area FROM "{GMBA_LAYER}"'
        subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-spat", *map(str, BOX), "-dialect", "OGRSQL", "-sql", sql,
                        str(out), f"/vsizip/{GMBA_ZIP}/{GMBA_LAYER}.shp"], check=True, capture_output=True)
        features = json.loads(out.read_text())["features"]
    ranges = []
    for f in features:
        p = f["properties"]
        if p["Feature"] not in GMBA_FEATURES or p["Area"] > GMBA_MAX_KM2:
            continue
        poly = shapely.geometry.shape(f["geometry"])
        c = poly.centroid
        if in_box(c.x, c.y):
            ranges.append(Landform(p["MapName"], "range", c.x, c.y, "gmba", str(p["GMBA_V2_ID"]), polygon=poly,
                                   gmba_id=str(p["GMBA_V2_ID"])))
    return ranges


def book_landforms(gnis: dict[str, Landform], geonames: dict[str, Landform]) -> list[Landform]:
    """The ranges, valleys and plains that places.geojson maps, under the book's name, from their gazetteer record."""
    out = []
    for f in json.loads((DATA / "places.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        if p["kind"] not in ("range", "valley", "plain"):
            continue
        record = {"gnis": gnis, "geonames": geonames}.get(p["source"], {}).get(p["source_id"])
        lon, lat = f["geometry"]["coordinates"]
        if record is None:
            # A place fixed by Wikidata or by hand: its own point stands in for a gazetteer record.
            record = Landform(p["name"], p["kind"], lon, lat, p["source"], p["source_id"] or p["id"])
        out.append(Landform(p["name"], p["kind"], record.lon, record.lat, record.name_source, record.name_id,
                            head=record.head, place=p))
    return out


# --- Axes ----------------------------------------------------------------------------------------------------------

def principal_line(px: np.ndarray, py: np.ndarray, w: np.ndarray, lon0: float, lat0: float,
                   grain: tuple[np.ndarray, float] | None = None):
    """The label line (two lon/lat points) and the elongation of a weighted cloud of points, given in metres east
    and north of (lon0, lat0). With `grain` (a direction and its strength, from grain()) of at least ROUND, the line
    takes that direction instead of the cloud's own long axis, and its length is the cloud's spread along it."""
    kx = M_PER_DEG_LON * math.cos(math.radians(lat0))
    cx, cy = np.average(px, weights=w), np.average(py, weights=w)
    ev, vec = np.linalg.eigh(np.cov(np.vstack([px - cx, py - cy]), aweights=w))
    elongation = math.sqrt(ev[1] / max(ev[0], 1.0))
    major = vec[:, 1]
    half = AXIS_SPAN * math.sqrt(max(ev[1], 0))
    if grain is not None and grain[1] >= ROUND:
        major, elongation = grain
        along = (px - cx) * major[0] + (py - cy) * major[1]
        half = AXIS_SPAN * math.sqrt(np.average(along**2, weights=w))
    elif elongation < ROUND:
        major, half = np.array([1.0, 0.0]), AXIS_SPAN * math.sqrt(max(ev.mean(), 0))
    if major[0] < 0:
        major = -major
    ends = [(cx - major[0] * half, cy - major[1] * half), (cx + major[0] * half, cy + major[1] * half)]
    line = [(lon0 + x / kx, lat0 + y / M_PER_DEG_LAT) for x, y in ends]
    return line, elongation


def polygon_axis(poly: shapely.Geometry):
    """The principal axis of a polygon, from a grid of about 4,000 points inside it."""
    c = poly.centroid
    kx = M_PER_DEG_LON * math.cos(math.radians(c.y))
    x0, y0, x1, y1 = poly.bounds
    step = math.sqrt(poly.area / 4000)
    gx, gy = np.meshgrid(np.arange(x0, x1, step), np.arange(y0, y1, step * kx / M_PER_DEG_LAT))
    inside = shapely.contains_xy(poly, gx, gy)
    px, py = (gx[inside] - c.x) * kx, (gy[inside] - c.y) * M_PER_DEG_LAT
    return principal_line(px, py, np.ones(len(px)), c.x, c.y)


def dem_axis(dem: rasterio.DatasetReader, lon: float, lat: float, kind: str):
    """The label line, its elongation, whether the region ran off the window, and its relief (m), for the DEM
    region the point sits in; None where none is found.

    1. Read a window of the DEM around the point (RADIUS_KM), averaged to CELL_M.
    2. Ranges: keep the cells whose height above the local valley floor (the lowest ground within VALLEY_KM,
       smoothed) is more than SHARE of that height near the point; this cuts a range off from a higher neighbour
       by the valley between. Mesas and plateaus: the flat cells within TOP_DROP_M of the top near the point.
       Plains and valleys: the flat cells lower than SHARE of the window's relief above its 20th percentile.
    3. Keep the connected region that contains the point, or the nearest one (nearest_region()). If it runs into
       the window's edge (EDGE_SHARE), keep only its part within LOCAL_KM of the point, and flag the line.
    4. Its principal axis, the cells weighted by their height above the base, so a crest counts for more than
       the foothills.
    """
    r = RADIUS_KM[kind] * 1000
    kx = M_PER_DEG_LON * math.cos(math.radians(lat))
    dlon, dlat = r / kx, r / M_PER_DEG_LAT
    cell = CELL_M[kind]
    n = int(2 * r / cell)
    win = from_bounds(lon - dlon, lat - dlat, lon + dlon, lat + dlat, dem.transform)
    z = dem.read(1, window=win, out_shape=(n, n), resampling=Resampling.average, boundless=True, masked=True)
    if z.mask.any():
        # Beyond the edge of the DEM (the box's east edge): fill with the window's median, which is flat and so
        # joins no region.
        z = z.filled(np.ma.median(z))
    z = np.asarray(z, dtype=float)
    c = n // 2
    near = int(NEAR_KM[kind] * 1000 / cell)
    core = (slice(max(c - near, 0), c + near), slice(max(c - near, 0), c + near))
    base = np.percentile(z, 20)
    top = np.percentile(z[core], 99)
    if kind == "range":
        k = int(VALLEY_KM * 1000 / cell) | 1
        floor = ndimage.uniform_filter(ndimage.minimum_filter(z, size=k), size=k)
        z = z - floor
        mask = z > SHARE[kind] * np.percentile(z[core], 99)
        base = 0.0
    elif kind in TOP_DROP_M:
        mask = z > top - TOP_DROP_M[kind]
    else:
        mask = z < base + SHARE[kind] * (top - base)
    if kind in FLAT_DEG:
        gy, gx = np.gradient(z, cell)
        mask &= np.degrees(np.arctan(np.hypot(gx, gy))) < FLAT_DEG[kind]
    mask = ndimage.binary_fill_holes(ndimage.binary_opening(mask, iterations=1))
    region = nearest_region(mask, c)
    if region is None:
        return None
    # Plains and valley floors run on past any window by nature; their lines stay as found.
    edge = np.concatenate([region[0], region[-1], region[:, 0], region[:, -1]]).mean()
    unbounded = kind in ("range", "mesa", "plateau") and edge > EDGE_SHARE
    if unbounded:
        # Part of something larger: in the sierras of Sonora and Chihuahua one massif runs on past any window.
        # Take only the part of it within LOCAL_KM of the point, and lay the line along the grain of that ground
        # (grain()): the clipped region is round by construction, so its own long axis means little.
        yy, xx = np.ogrid[:n, :n]
        region = nearest_region(mask & ((yy - c) ** 2 + (xx - c) ** 2 <= (LOCAL_KM * 1000 / cell) ** 2), c)
        if region is None:
            return None
    ys, xs = np.nonzero(region)
    if len(xs) < 8:
        return None
    w = np.clip(z[ys, xs] - base, 1, None) if kind in ("range", "mesa", "plateau") else np.ones(len(xs))
    line, elongation = principal_line((xs - c) * cell, (c - ys) * cell, w, lon, lat,
                                      grain(z, region, cell) if unbounded else None)
    # How high the landform stands: for ranges the height of its core above the valley floor, otherwise the relief
    # of the window. Used to rank the ranges that run on past their window, which have no length of their own.
    relief = float(np.percentile(z[core], 99) - (0 if kind == "range" else base))
    return line, elongation, unbounded, relief


def grain(z: np.ndarray, region: np.ndarray, cell: float) -> tuple[np.ndarray, float]:
    """The direction the ridges and valleys of a region run (a unit vector east and north) and how strongly they
    keep to it: the structure tensor of the slope. Slopes face across the grain, so the grain is the direction of
    least slope. The strength is the square root of the tensor's eigenvalue ratio, like `elongation`."""
    gy, gx = np.gradient(z, cell)
    gx, gn = gx[region], -gy[region]  # rows run south, so north is minus the row gradient
    tensor = np.array([[np.sum(gx * gx), np.sum(gx * gn)], [np.sum(gx * gn), np.sum(gn * gn)]])
    ev, vec = np.linalg.eigh(tensor)
    return vec[:, 0], math.sqrt(ev[1] / max(ev[0], 1e-9))


def nearest_region(mask: np.ndarray, c: int) -> np.ndarray | None:
    """The connected region of the mask that contains the centre cell, or the one nearest to it: gazetteer points
    sit on a summit or in the middle of a name, not always inside the region the thresholds find."""
    lab, count = ndimage.label(mask)
    if not count:
        return None
    if lab[c, c]:
        return lab == lab[c, c]
    _, (iy, ix) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    return lab == lab[iy[c, c], ix[c, c]]


def place_line(lf: Landform, dem: rasterio.DatasetReader) -> bool:
    """Give the landform its label line and axis method; False where none could be made."""
    if lf.polygon is not None:
        lf.line, lf.elongation = polygon_axis(lf.polygon)
        lf.axis = "gmba"
    elif lf.kind == "valley" and lf.head:
        lf.line = sorted([(lf.lon, lf.lat), lf.head])
        lf.axis = "gnis"
    else:
        found = dem_axis(dem, lf.lon, lf.lat, lf.kind)
        if not found:
            return False
        lf.line, lf.elongation, lf.unbounded, lf.relief = found
        lf.axis = "dem"
    return True


# --- Hand edits ----------------------------------------------------------------------------------------------------

def to_xy(line, lon0, lat0):
    kx = M_PER_DEG_LON * math.cos(math.radians(lat0))
    return [((x - lon0) * kx, (y - lat0) * M_PER_DEG_LAT) for x, y in line], kx


def apply_edit(lf: Landform, edit: dict) -> None:
    """Rotate (degrees anticlockwise), set the length (km) of, move (`centre`, lon and lat), or bend (`curve`: the
    arc's rise at the middle as a share of the length, positive to the left of the reading direction) one line
    about its middle."""
    a, b = lf.line[0], lf.line[-1]
    (p, q), _ = to_xy([a, b], *middle([a, b]))
    mx, my = edit.get("centre", middle([a, b]))
    kx = M_PER_DEG_LON * math.cos(math.radians(my))
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy)
    angle = math.atan2(dy, dx) + math.radians(edit.get("rotate", 0))
    length = edit.get("length", length / 1000) * 1000
    ux, uy = math.cos(angle), math.sin(angle)
    rise = edit.get("curve", 0) * length
    pts = []
    for i in range(9 if rise else 2):
        t = i / (8 if rise else 1) - 0.5
        # A parabola through the ends with its top `rise` to the left of the chord: close to a circular arc for
        # the gentle bends a label can follow.
        off = rise * (1 - 4 * t * t)
        x, y = t * length * ux - off * uy, t * length * uy + off * ux
        pts.append((mx + x / kx, my + y / M_PER_DEG_LAT))
    lf.line = pts
    lf.reason = edit["reason"]


# --- Choosing ------------------------------------------------------------------------------------------------------

def length_m(line) -> float:
    return sum(GEOD.inv(a[0], a[1], b[0], b[1])[2] for a, b in zip(line, line[1:], strict=False))


def middle(line) -> tuple[float, float]:
    return ((line[0][0] + line[-1][0]) / 2, (line[0][1] + line[-1][1]) / 2)


def attach_gmba(cands: list[Landform], gmba: list[Landform]) -> list[Landform]:
    """Give each range its GMBA outline where one of the same name lies close by; the outlines left over are
    ranges of their own, named from GMBA."""
    left = []
    for g in gmba:
        hits = [c for c in cands if c.kind == "range" and c.key == g.key
                and g.polygon.distance(shapely.Point(c.lon, c.lat)) * M_PER_DEG_LAT / 1000 <= GMBA_NEAR_KM]
        for c in hits:
            if c.polygon is None:
                c.polygon, c.gmba_id = g.polygon, g.gmba_id
        if not hits:
            left.append(g)
    return left


def dedupe(cands: list[Landform]) -> list[Landform]:
    """One landform per name and kind within SAME_KM, the first listed winning (the book, then GNIS, GeoNames,
    GMBA)."""
    kept: list[Landform] = []
    for c in cands:
        if not any(k.kind == c.kind and k.key == c.key and km((k.lon, k.lat), (c.lon, c.lat)) < SAME_KM
                   for k in kept):
            kept.append(c)
    return kept


def choose(placed: list[Landform], keep: set[str]) -> list[Landform]:
    """The book's landforms, then the others: the GMBA ranges and the lines with a length of their own, longest
    first, then the ranges cut out of a larger massif, highest first. Each kind keeps lines above MIN_KM, up to
    CAP, and drops a line whose middle is within SPACING of a kept line's middle."""
    kept = [lf for lf in placed if lf.place or line_id(lf) in keep]

    def rank(lf: Landform):
        # GMBA outlines and GNIS valleys have a true extent, so the longest go first; a DEM line's length says
        # less than how high its ground stands.
        return (lf.axis == "dem", -lf.relief if lf.axis == "dem" and lf.kind == "range" else -length_m(lf.line))

    taken = {kind: 0 for kind in CAP}
    for lf in sorted((lf for lf in placed if lf not in kept), key=rank):
        length = length_m(lf.line)
        if length < MIN_KM[lf.kind] * 1000 or taken[lf.kind] >= CAP[lf.kind]:
            continue
        if (lf.unbounded and lf.kind != "range") or (lf.kind == "mesa" and (lf.elongation or 0) < MESA_MIN_ELONG):
            continue
        mid = middle(lf.line)
        if any(k.kind == lf.kind
               and km(mid, middle(k.line)) < max(SPACING_KM, OVERLAP * max(length, length_m(k.line)) / 1000)
               for k in kept):
            continue
        kept.append(lf)
        taken[lf.kind] += 1
    return kept


def line_id(lf: Landform) -> str:
    """The book's landforms take their place's id; the others their name and gazetteer id, which stay put when
    the build's choices change."""
    if lf.place:
        return lf.place["id"].replace("place-", "landform-", 1)
    return f"landform-{slug(lf.name)}-{lf.name_id}"


def feature(lf: Landform, ids: set[str]) -> dict:
    p = lf.place
    fid = line_id(lf)
    assert fid not in ids, fid
    ids.add(fid)
    first_seen = p["first_seen"] if p else "1-01"
    source = {"gmba": "gmba", "gnis": "gnis", "dem": "copernicus-glo30"}[lf.axis]
    source_id = {"gmba": lf.gmba_id, "gnis": lf.name_id, "dem": lf.name_id}[lf.axis]
    mid = middle(lf.line)
    props = {
        "id": fid,
        "name": p["name"] if p else lf.name,
        "kind": lf.kind,
        "part": int(first_seen[0]),
        "first_seen": first_seen,
        "certainty": "inferred" if lf.unbounded else "approximate",
        "method": METHOD[lf.axis],
        "source": source,
        "source_id": source_id,
        "source_licence": LICENCE[source],
        "note_safe": NOTE[lf.axis],
        "reasoning": lf.reason,
        "place_ref": p["id"] if p else None,
        "name_source": f"{lf.name_source}:{lf.name_id}",
        "axis": lf.axis,
        "elongation": round(lf.elongation, 2) if lf.elongation is not None else None,
        "len_m": round(length_m(lf.line)),
        "mpp0": round(156543.03 * math.cos(math.radians(mid[1]))),
    }
    coords = [[round(x, 5), round(y, 5)] for x, y in lf.line]
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}, "properties": props}


def main() -> None:
    gnis, geonames = gnis_landforms(), geonames_landforms()
    book = book_landforms(gnis, geonames)
    taken = {(lf.name_source, lf.name_id) for lf in book}
    # Of the landforms the book does not name: GNIS valleys only if called a valley (not the draws, canyons and
    # washes) and with a head to draw the line to; ranges only if the name calls them one (RANGE_WORDS).
    rest = [lf for lf in [*gnis.values(), *geonames.values()] if (lf.name_source, lf.name_id) not in taken
            and not (lf.kind == "valley" and lf.name_source == "gnis" and not (lf.name.endswith(" Valley") and lf.head))
            and not (lf.kind == "range" and not RANGE_WORDS.search(lf.name))]
    rest += attach_gmba(book + rest, gmba_ranges())
    rest = [lf for lf in rest if not any(b.key == lf.key and min(km(end, (lf.lon, lf.lat)) for end in b.ends) < BOOK_KM
                                         for b in book)]
    cands = book + dedupe(rest)
    edits = tomllib.loads(EDITS.read_text(encoding="utf-8")).get("edit", [])
    placed, missing = [], []
    with tempfile.TemporaryDirectory() as tmp, \
            rasterio.open(build_vrt(Path(tmp) / "dem.vrt", tiles(COPERNICUS, COPERNICUS_REGION))) as dem:
        for lf in cands:
            if place_line(lf, dem):
                placed.append(lf)
            else:
                missing.append(lf)
    kept = choose(placed, {e["id"] for e in edits if e.get("keep")})
    ids: set[str] = set()
    features = [feature(lf, ids) for lf in kept]
    by_id = {f["properties"]["id"]: (f, lf) for f, lf in zip(features, kept, strict=True)}
    unused = []
    for edit in edits:
        hit = by_id.get(edit.get("id", ""))
        if not hit:
            unused.append(edit.get("id"))
            continue
        f, lf = hit
        if edit.get("drop"):
            features.remove(f)
            continue
        apply_edit(lf, edit)
        ids.discard(f["properties"]["id"])
        features[features.index(f)] = feature(lf, ids)
    features.sort(key=lambda f: (f["properties"]["kind"], f["properties"]["id"]))
    doc = {"type": "FeatureCollection", "features": features}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for f in features:
        p = f["properties"]
        print(f"{p['kind']:8s} {p['axis']:5s} {p['len_m'] / 1000:6.1f} km  {p['first_seen']}  {p['name']}")
    counts = {k: sum(f["properties"]["kind"] == k for f in features) for k in CAP}
    print(f"{len(features)} lines: {counts}. Wrote {OUT.relative_to(DATA.parent)}.")
    for lf in missing:
        if lf.place:
            print(f"no line for the book's {lf.name} ({lf.name_source}:{lf.name_id})")
    for lf in kept:
        if lf.unbounded and lf.place:
            print(f"the book's {lf.name}: the DEM region runs off its window; check the line")
    for fid in unused:
        print(f"landform_axes.toml: no line {fid}")


if __name__ == "__main__":
    main()
