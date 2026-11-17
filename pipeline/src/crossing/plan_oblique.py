"""The Oblique view (decisions 0017, 0019 and 0040): plan oblique relief over the corridor of the journeys.

Run from the repo root, after crossing.hachures (whose fine tile grid sets the area) and crossing.fetch_landcover:
    uv run --project pipeline python -m crossing.plan_oblique
    uv run --project pipeline python -m crossing.plan_oblique --properties  # after a text-only story change
    uv run --project pipeline python -m crossing.plan_oblique --vignettes   # the drawings only (under a minute)

Plan oblique relief (Jenny and Patterson, "Introducing plan oblique relief", Cartographic Perspectives 57, 2007)
keeps a flat, north-up map but moves every point north in proportion to its height, so high ground stands up and
leans over the ground behind it, as in Raisz's physiographic diagrams. Here it is applied to the map's own line
work and land cover, not to a raster:
  1. Every point moves north by (height - lowest height in the area) * LEAN.
  2. A point is hidden where ground to its south has moved further north than it has: the running maximum
     of shifted northing, south to north, in each 30 m column.
  3. The southern edges of the hidden ground, traced on the 30 m grid, are the crests seen against the land
     behind; they are drawn as outlines. (The northern edges, where ground comes back into view, project to the
     same place, so they are left out rather than drawn twice.)
The direction of view is the same everywhere, so the result can be tiled like any other line data.

The strokes follow the oblique maps the style is drawn after (decision 0040; docs/inspiration/churchill.md): long
strokes down the fall line, packed on the faces turned from the light and left out on lit ones, after Tau Rho
Alpha's Atlas of Oblique Maps (1988); a second, closer set in the deepest shade, after the comic-book shading of
Charles Owens's The Panama Canal (1928); and stipple on the flats, after Frank Holmes's Estado da Guanabara (1965).
They are traced on the DEM smoothed again over GENERALISE cells, so they follow the main faces, as an engraver
generalises, not every gully. Seeds lie on one jittered grid for the whole corridor, fixed by a hash of each grid
cell, so strips meet and a rebuild draws the same strokes. Strokes are dropped where the ground is squeezed below
FOLD of its depth.

Land cover (crossing.landcover) is classed on each strip's grid, then drawn twice: as polygons on the ground for
the Flat and Tilted views, and shifted, with the hidden ground cut out, for this view.

The area is every fine hachure tile of the corridor, with one lowest height for all of it.
The horizon runs along each north-south column of the grid, so columns are independent: the area is built in
strips, one per column of tiles, in parallel. Each strip has its own smoothed DEM (hachures.prepare_dem),
reaching PAD further east, west and north for gradients, and SOUTH further south, so that ground just outside
the area can hide ground inside it.

Inputs: the Copernicus tiles, the CEC land cover, INEGI's 1:50,000 river network for Mexico, USGS NHD flowlines
for the US, and the Natural Earth and Census layers of crossing.basemap. Writes
  - tiles/out/oblique-<n>.pmtiles (split by strips to stay under 100 MB each; data/oblique/archives.json lists
    them), zoom 9-12, one layer `oblique` whose `kind` is stroke (`shade`, 0 lit to 100 in full shade, and
    `Rand`, 0 to 9, for thinning by zoom), dot (stipple), crest, stream (`ord`, Strahler order or a stand-in;
    `name` on the US side), country, state, county, road, railroad (lines), landcover (`class`, polygons) and
    mexico (the Mexico side, a polygon);
  - tiles/out/landcover.pmtiles, zoom 7-12, one layer `landcover` of polygons by `class`, on the ground;
  - the story layers shifted by the same rule, to data/oblique/.
`python -m tiles.install` copies the archives into the local site.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.windows import from_bounds
from scipy.ndimage import gaussian_filter, map_coordinates, minimum_filter
from shapely import LineString, Polygon, box, unary_union
from shapely.geometry import mapping, shape

from crossing import basemap, dem, landcover
from crossing.hachures import ATTRIBUTION as RELIEF_ATTRIBUTION
from crossing.hachures import CRS, GRID_ORIGIN, SCALES, corridor, coverage, prepare_dem, tiles
from crossing.hydro import INEGI, NHD
from crossing.paths import DATA, TILES_OUT
from crossing.tiling import tippecanoe
from crossing.vector import read

TILE = SCALES["fine"]["tile"]
CELL = 30
STEP = 8  # metres between samples along a line
STORY_STEP = 60  # metres between samples along the story's lines and area edges
LEAN = 4  # metres north per metre of height (decision 0040; 3 stays open if the larger shift reads badly)
FOLD = 0.5  # smallest north-south stretch at which strokes are kept
PAD = 20 * CELL  # covers the 1 km relief window and the smoothing's edge
# How far, in degrees, --vignettes lets the other shifted layers move when shifted again: 0.0001 degrees (about
# 10 m) is the tolerance the published lines are simplified to, and a DEM tile added outside the corridor moves a far
# point by a metre or two.
RAISE_TOLERANCE = 0.0001
SOUTH = 11_000  # ground this far south of the area can still hide ground in it: shifts reach about 9.6 km

# The strokes (decision 0040). Light from the north-west, 45 degrees up, on the DEM smoothed again over GENERALISE
# cells. A seed on the STROKE_SPACING grid is kept with a chance that rises with shade and with slope above
# STROKE_SLOPE; faces lit above LIT get none, and ground in shade below DEEP, steeper than DEEP_SLOPE, gets a second
# grid DEEP_SPACING apart. Strokes run STROKE_LENGTH metres down the fall line, traced every TRACE_STEP metres, and
# are simplified to STROKE_SIMPLIFY metres once shifted. Stipple lies on the DOT_SPACING grid where the ground is
# flatter than DOT_SLOPE and within DOT_RELIEF metres of the lowest ground about 1 km round.
GENERALISE = 4
AZIMUTH, ALTITUDE = 315, 45
STROKE_SPACING, DEEP_SPACING, DOT_SPACING = 52, 30, 95
STROKE_SLOPE, DEEP_SLOPE, DOT_SLOPE = 5, 8, 4
LIT, DEEP = 0.72, 0.3
STROKE_LENGTH = (140, 320)
TRACE_STEP = 10
STROKE_SIMPLIFY = 5  # metres, for every line once shifted
DOT_RELIEF = 40
# Thinning by zoom: the strokes are spaced for about zoom 12.5, so at each zoom out only some of them, by Rand, are
# tiled: Rand 0 from zoom 9, up to 1 from 10, up to 3 from 11, and the rest at 12 (the style draws Rand 7 to 9
# only from 13).
RAND_MINZOOM = (9, 10, 11, 11, 12, 12, 12, 12, 12, 12)
LANDCOVER_ZOOMS = (7, 12)
OBLIQUE_DATA = DATA / "oblique"
STORY = ("stops", "places", "areas", "journeys", "vignettes")
# Archives over this size are split, by groups of whole strips, to stay under the design's 100 MB per file.
MAX_ARCHIVE_MB = 95
# Shown in the map's attribution while the Oblique view is on.
ATTRIBUTION = ("Streams: Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0; "
               "USGS National Hydrography Dataset courtesy of the U.S. Geological Survey; "
               "county lines courtesy of the U.S. Census Bureau (cartographic boundary files); "
               f"Made with Natural Earth; {RELIEF_ATTRIBUTION}; {landcover.NOTICE}")

to_utm = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform
to_wgs = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform


def densify(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
    s = np.arange(0, dist[-1] + STEP / 2, STEP) if dist[-1] > 0 else np.array([0.0])
    return np.interp(s, dist, xy[:, 0]), np.interp(s, dist, xy[:, 1])


def to_lonlat(xy: np.ndarray) -> np.ndarray:
    return np.round(np.column_stack(to_wgs(xy[:, 0], xy[:, 1])), 5)


class Fields:
    """Light, slope, aspect and the fall line on a strip's south-to-north grid of heights, smoothed again over
    GENERALISE cells; and how far each cell stands above the lowest ground about 1 km round."""

    def __init__(self, Z: np.ndarray, x0: float, y0: float):
        self.x0, self.y0 = x0, y0
        gy, gx = np.gradient(gaussian_filter(Z, GENERALISE), CELL)
        self.gx, self.gy = gx.astype("float32"), gy.astype("float32")
        s = np.arctan(np.hypot(gx, gy))
        aspect = np.arctan2(-gx, -gy)  # downhill direction, clockwise from north
        z = math.radians(90 - ALTITUDE)
        self.slope = np.degrees(s).astype("float32")
        self.light = np.clip(math.cos(z) * np.cos(s)
                             + math.sin(z) * np.sin(s) * np.cos(math.radians(AZIMUTH) - aspect), 0, 1).astype("float32")
        self.north = np.cos(aspect).astype("float32")  # 1 on a slope facing due north
        self.relief = (Z - minimum_filter(Z, 67)).astype("float32")

    def at(self, raster: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        rows, cols = (y - self.y0) / CELL - 0.5, (x - self.x0) / CELL - 0.5
        return map_coordinates(raster, [rows, cols], order=1, mode="nearest")


def hashed(i: np.ndarray, j: np.ndarray, salt: int) -> np.ndarray:
    """A number in [0, 1) fixed by a grid cell (i, j) and a salt: splitmix64 over the three."""
    with np.errstate(over="ignore"):
        h = i.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)
        h ^= j.astype(np.uint64) * np.uint64(0xC2B2AE3D27D4EB4F)
        h ^= np.uint64(salt) * np.uint64(0x165667B19E3779F9)
        h = (h ^ (h >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        h = (h ^ (h >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        h ^= h >> np.uint64(31)
    return (h >> np.uint64(11)).astype(np.float64) / 2.0**53


def seeds(core: tuple[float, ...], spacing: float, salt: int) -> tuple[np.ndarray, ...]:
    """Seeds on the corridor's jittered grid `spacing` metres apart (from crossing.hachures.GRID_ORIGIN) whose
    cells start in `core`, and three more numbers in [0, 1) fixed for each: the same seeds whichever strip asks."""
    x0, y0 = GRID_ORIGIN
    i = np.arange(math.ceil((core[0] - x0) / spacing), math.ceil((core[2] - x0) / spacing))
    j = np.arange(math.ceil((core[1] - y0) / spacing), math.ceil((core[3] - y0) / spacing))
    i, j = (a.ravel() for a in np.meshgrid(i, j))
    u = [hashed(i, j, salt * 8 + k) for k in range(5)]
    return x0 + (i + u[0]) * spacing, y0 + (j + u[1]) * spacing, u[2], u[3], u[4]


def fall_lines(f: Fields, x: np.ndarray, y: np.ndarray, length: np.ndarray) -> list[np.ndarray]:
    """From each seed, a line `length` metres long down the fall line."""
    n = int(length.max() // TRACE_STEP) + 1
    px, py = [x.copy()], [y.copy()]
    for _ in range(n - 1):
        gx, gy = f.at(f.gx, x, y), f.at(f.gy, x, y)
        norm = np.maximum(np.hypot(gx, gy), 1e-6)
        x, y = x - TRACE_STEP * gx / norm, y - TRACE_STEP * gy / norm
        px.append(x)
        py.append(y)
    px, py = np.array(px).T, np.array(py).T
    keep = np.maximum((length // TRACE_STEP).astype(int) + 1, 2)
    return [np.column_stack([px[i, :k], py[i, :k]]) for i, k in enumerate(keep)]


def parts(geom) -> list[np.ndarray]:
    """The coordinate arrays of a (multi)line, or of a (multi)polygon's rings."""
    if geom.is_empty:
        return []
    if isinstance(geom, LineString):
        return [np.asarray(geom.coords)[:, :2]]
    if isinstance(geom, Polygon):
        return [np.asarray(r.coords)[:, :2] for r in (geom.exterior, *geom.interiors)]
    return [xy for g in getattr(geom, "geoms", []) for xy in parts(g)]


def ogr(source: str | Path, sql: str, bbox: tuple[float, ...], tmp: Path, extra: tuple[str, ...] = ()) -> list[dict]:
    """Features of a vector source inside a lon/lat box, in UTM, as GeoJSON dicts."""
    return read(source, sql, bbox, tmp / f"{abs(hash((str(source), sql)))}.geojson", crs=CRS, extra=extra)


def base_lines(bbox: tuple[float, ...], tmp: Path) -> tuple[list[tuple[str, dict, np.ndarray]], Polygon]:
    """The base map's lines in UTM as (kind, properties, coordinates), from the base map's own sources
    (crossing.basemap), and the Mexico side as a polygon. Only the geometry is kept."""
    mexico = basemap.mexico(bbox, tmp, crs=CRS)
    lines = []
    kinds = (("country", "country_line"), ("state", "state_line"), ("road", "road"), ("railroad", "railroad"))
    for kind, layer in kinds:
        name, sql, extra = basemap.LAYERS[layer]
        for f in ogr(basemap.shapefile(name), sql, bbox, tmp, extra):
            lines += [(kind, {}, xy) for xy in parts(shape(f["geometry"]))]
    # County outlines share their edges, so the outlines are merged to draw each edge once.
    name, sql, extra = basemap.LAYERS["county_line"]
    counties = ogr(basemap.shapefile(name), sql, bbox, tmp, extra)
    edges = shapely.line_merge(unary_union([shape(f["geometry"]) for f in counties]))
    lines += [("county", {}, xy) for xy in parts(edges)]

    # Streams: INEGI's on the Mexico side (Strahler order 3 and up, with the centre lines that INEGI uses for the
    # channels of wide rivers), NHD's on the US side, each clipped to its own side of the border so that the two
    # networks do not double along it.
    rivers = []
    for zip_path in sorted(INEGI.glob("*.zip")):
        for name in (n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith("_hl.shp")):
            for f in ogr(f"/vsizip/{zip_path}/{name}", f"SELECT ORDER_1 FROM {Path(name).stem} "
                         "WHERE ENTIDAD IN ('CORRIENTE DE AGUA', 'LINEA CENTRAL') AND ORDER_1 >= 3", bbox, tmp):
                rivers.append((shape(f["geometry"]), {"ord": f["properties"]["ORDER_1"]}, True))
    # NHD flowlines carry no stream order here, so the scale NHD shows a line from (visibility) stands in for
    # it: streams shown at 1:500,000 or smaller, about INEGI's order 3 and up, and every named stream.
    order = {500_000: 3, 1_000_000: 4, 2_000_000: 5, 5_000_000: 6}
    for shp_path in sorted(NHD.glob("*/Shape/NHDFlowline.shp")):
        for f in ogr(str(shp_path), "SELECT gnis_name, visibility FROM NHDFlowline WHERE ftype = 460 "
                     "AND (gnis_name IS NOT NULL OR visibility >= 500000)", bbox, tmp):
            p = f["properties"]
            props = {"ord": order.get(p["visibility"], 3), **({"name": p["gnis_name"]} if p["gnis_name"] else {})}
            rivers.append((shape(f["geometry"]), props, False))
    geoms = shapely.intersection([g for g, _, _ in rivers], mexico)
    outside = shapely.difference([g for g, _, _ in rivers], mexico)
    for (_, props, in_mexico), inside_part, outside_part in zip(rivers, geoms, outside, strict=True):
        lines += [("stream", props, xy) for xy in parts(inside_part if in_mexico else outside_part)]
    return lines, mexico


def strips() -> list[dict]:
    """One strip per unbroken column of fine tiles in the corridor: its core (UTM), its tiles, and its DEM's bounds."""
    region = corridor().intersection(coverage().buffer(-60))
    columns: dict[float, list] = {}
    for name, core in tiles(region, TILE):
        columns.setdefault(core.bounds[0], []).append((name, core.bounds))
    out = []
    snap = lambda v, up: (math.ceil if up else math.floor)(v / CELL) * CELL  # noqa: E731
    for x0, cells in sorted(columns.items()):
        # A column can hold separate stretches of the corridor; each unbroken run of tiles is its own strip.
        # The gaps are whole tiles, far more than the ground a ridge can hide, and each DEM reaches SOUTH below its run.
        runs: list[list] = []
        for cell in sorted(cells, key=lambda c: c[1][1]):
            if runs and runs[-1][-1][1][3] == cell[1][1]:
                runs[-1].append(cell)
            else:
                runs.append([cell])
        for run in runs:
            y0, y1 = run[0][1][1], run[-1][1][3]
            bounds = (snap(x0 - PAD, False), snap(y0 - SOUTH, False),
                      snap(x0 + TILE + PAD, True), snap(y1 + PAD, True))
            name = f"{round(x0 / 1000)}e-{round(y0 / 1000)}n"
            out.append({"name": name, "core": (x0, y0, x0 + TILE, y1), "tiles": run, "bounds": bounds})
    return out


class Grid:
    """A strip's smoothed DEM, as a south-to-north grid, with the shift and the horizon each point must clear."""

    def __init__(self, dem_path: Path, base: float):
        with rasterio.open(dem_path) as src:
            self.dem, self.t = src.read(1).astype(float), src.transform
        self.base = base
        self.Z = self.dem[::-1]
        ny, nx = self.Z.shape
        self.x0, self.y0 = self.t.c, self.t.f + self.t.e * ny
        self.xs = self.x0 + (np.arange(nx) + 0.5) * CELL
        self.ys = self.y0 + (np.arange(ny) + 0.5) * CELL
        self.shifted = self.ys[:, None] + (self.Z - base) * LEAN
        # The grid runs south to north, so a running maximum along its rows is the horizon each point must clear.
        self.horizon = np.vstack([np.full(nx, -np.inf), np.maximum.accumulate(self.shifted, axis=0)[:-1]])
        # How much the shift stretches the ground north to south: 1 on the flat, more on slopes facing the viewer
        # (south), less on slopes facing away, and below 0 where the ground folds out of sight.
        self.stretch = 1 + LEAN * np.gradient(self.Z, CELL, axis=0)

    def height(self, x, y):
        cols, rows = ~self.t * (np.asarray(x), np.asarray(y))
        return map_coordinates(self.dem, [rows - 0.5, cols - 0.5], order=1, mode="nearest")

    def cell(self, x, y):
        return (np.clip(np.round((y - self.ys[0]) / CELL).astype(int), 0, len(self.ys) - 1),
                np.clip(np.round((x - self.xs[0]) / CELL).astype(int), 0, len(self.xs) - 1))

    def project(self, x, y, core):
        """Shifted northings for a polyline, and which points are inside `core` and not hidden."""
        yp = y + (self.height(x, y) - self.base) * LEAN
        inside = (x >= core[0]) & (x < core[2]) & (y >= core[1]) & (y < core[3])
        return yp, inside & (yp >= self.horizon[self.cell(x, y)] - CELL / 2)


def runs(x, yp, shown, kind, props, out):
    """Append each run of shown points, as (kind, properties, x, shifted y), to `out`."""
    edges = np.flatnonzero(np.diff(np.concatenate([[0], shown.astype(np.int8), [0]])))
    for start, stop in zip(edges[::2], edges[1::2], strict=True):
        if stop - start >= 2:
            out.append((kind, props, x[start:stop], yp[start:stop]))


def build_strip(strip: dict, dem_path: Path, base: float, lines: list, mexico: Polygon, out_path: Path,
                land_path: Path) -> dict:
    """The oblique line work and land cover of one strip, written to `out_path` as one GeoJSON feature per line,
    point or polygon; and the strip's land cover on the ground, to `land_path`."""
    g = Grid(dem_path, base)
    f = Fields(g.Z, g.x0, g.y0)
    core = strip["core"]
    found: list = []

    # Strokes down the fall line: a chance by shade and slope on the main grid, all of the deep-shade grid.
    x, y, keep_u, length_u, rand_u = seeds(core, STROKE_SPACING, 1)
    slope, light = f.at(f.slope, x, y), f.at(f.light, x, y)
    chance = np.clip(0.04 + 1.3 * (1 - light) ** 2.2, 0, 1) * np.clip(slope / 14, 0, 1)
    keep = (slope > STROKE_SLOPE) & (light < LIT) & (keep_u < chance)
    dx, dy, _, dlength_u, drand_u = seeds(core, DEEP_SPACING, 2)
    deep = (f.at(f.slope, dx, dy) > DEEP_SLOPE) & (f.at(f.light, dx, dy) < DEEP)
    x, y = np.concatenate([x[keep], dx[deep]]), np.concatenate([y[keep], dy[deep]])
    share = np.concatenate([length_u[keep], dlength_u[deep]])
    length = STROKE_LENGTH[0] + (STROKE_LENGTH[1] - STROKE_LENGTH[0]) * share
    rand = (np.concatenate([rand_u[keep], drand_u[deep]]) * 10).astype(int)
    shade = np.round((1 - f.at(f.light, x, y)) * 100).astype(int)
    for xy, sh, r in zip(fall_lines(f, x, y, length), shade, rand, strict=True):
        if (g.stretch[g.cell(xy[:, 0], xy[:, 1])] >= FOLD).mean() < 0.6:
            continue
        yp, shown = g.project(xy[:, 0], xy[:, 1], core)
        runs(xy[:, 0], yp, shown, "stroke", {"shade": int(sh), "Rand": int(r)}, found)

    # Stipple on the flats: points, hidden like the lines.
    x, y, _, _, rand_u = seeds(core, DOT_SPACING, 3)
    flat = (f.at(f.slope, x, y) < DOT_SLOPE) & (f.at(f.relief, x, y) < DOT_RELIEF)
    x, y, rand = x[flat], y[flat], (rand_u[flat] * 10).astype(int)
    yp, shown = g.project(x, y, core)
    dots = [(xx, yy, int(r)) for xx, yy, r, ok in zip(x, yp, rand, shown, strict=True) if ok]

    # The base map's lines.
    for kind, props, xy in lines:
        x, y = densify(xy)
        runs(x, *g.project(x, y, core), kind, props, found)

    # Crests: the edges of the hidden ground, where the shifted surface meets its own horizon.
    margin = np.clip(g.shifted - g.horizon, -500, 500).astype("float32")
    margin[0] = 500
    # Northward change in the margin: falling where ground drops out of sight (a crest), rising where it returns.
    falling = np.gradient(margin, axis=0) < 0
    with tempfile.TemporaryDirectory() as folder:
        raster, contour = Path(folder) / "m.tif", Path(folder) / "c.geojson"
        with rasterio.open(raster, "w", driver="GTiff", width=len(g.xs), height=len(g.ys), count=1, dtype="float32",
                           crs=CRS,
                           transform=from_origin(g.x0, g.y0 + len(g.ys) * CELL, CELL, CELL)) as dst:
            dst.write(margin[::-1], 1)  # rows north to south, as GeoTIFF expects
        subprocess.run(["gdal_contour", "-q", "-fl", str(-CELL / 2), "-f", "GeoJSON", str(raster), str(contour)],
                       check=True)
        crests = json.loads(contour.read_text())["features"]
    for feature in crests:
        xy = np.array(feature["geometry"]["coordinates"])
        if len(xy) < 2 or np.hypot(*np.diff(xy, axis=0).T).sum() < 150:
            continue
        x, y = densify(xy)
        yp = y + (g.height(x, y) - base) * LEAN
        inside = (x >= core[0]) & (x < core[2]) & (y >= core[1]) & (y < core[3])
        runs(x, yp, falling[g.cell(x, y)] & inside, "crest", {}, found)

    # The Mexico side, a polygon, shifted but not hidden: the paper colour under the line work.
    sides = []
    side = mexico.intersection(box(*core))
    for poly in getattr(side, "geoms", [side]):
        if isinstance(poly, Polygon) and not poly.is_empty:
            def lift(xy):
                return np.column_stack([xy[:, 0], xy[:, 1] + (g.height(xy[:, 0], xy[:, 1]) - base) * LEAN])
            sides.append(shapely.transform(poly.segmentize(STORY_STEP), lift))

    flat_land, oblique_land = land_cover(g, f, core, lines)

    # Lines are sampled every STEP metres to be shifted and hidden; once shifted they are simplified to
    # STROKE_SIMPLIFY metres, then everything goes back to longitude and latitude in one projection.
    for i, (kind, props, x, yp) in enumerate(found):
        if len(x) > 2:
            xy = np.asarray(LineString(np.column_stack([x, yp])).simplify(STROKE_SIMPLIFY).coords)
            found[i] = (kind, props, xy[:, 0], xy[:, 1])
    lon, lat = to_wgs(np.concatenate([[], *(r[2] for r in found)]), np.concatenate([[], *(r[3] for r in found)]))
    ends = np.cumsum([len(r[2]) for r in found])
    counts: dict[str, int] = {}

    def tally(kind: str) -> None:
        counts[kind] = counts.get(kind, 0) + 1

    with out_path.open("w") as out:
        for (kind, props, _, _), start, stop in zip(found, np.concatenate([[0], ends[:-1]]), ends, strict=False):
            pairs = zip(lon[start:stop].tolist(), lat[start:stop].tolist(), strict=True)
            coords = [(round(a, 5), round(b, 5)) for a, b in pairs]
            feature = {"type": "Feature", "properties": {"kind": kind, **props},
                       "geometry": {"type": "LineString", "coordinates": coords}}
            if kind == "stroke":
                feature["tippecanoe"] = {"minzoom": RAND_MINZOOM[props["Rand"]]}
            out.write(json.dumps(feature) + "\n")
            tally(kind)
        if dots:
            dlon, dlat = to_wgs(np.array([d[0] for d in dots]), np.array([d[1] for d in dots]))
            for a, b, (_, _, r) in zip(dlon.tolist(), dlat.tolist(), dots, strict=True):
                out.write(json.dumps({"type": "Feature", "properties": {"kind": "dot", "Rand": r},
                                      "tippecanoe": {"minzoom": RAND_MINZOOM[r]},
                                      "geometry": {"type": "Point", "coordinates": [round(a, 5), round(b, 5)]}}) + "\n")
                tally("dot")
        for poly in sides:
            out.write(json.dumps({"type": "Feature", "properties": {"kind": "mexico"},
                                  "geometry": mapping(shapely.transform(poly, to_lonlat))}) + "\n")
            tally("mexico")
        for geom, k in oblique_land:
            out.write(json.dumps({"type": "Feature", "properties": {"kind": "landcover", "class": landcover.CLASSES[k]},
                                  "geometry": mapping(shapely.transform(geom, to_lonlat))}) + "\n")
            tally("landcover")
    with land_path.open("w") as out:
        for geom, k in flat_land:
            out.write(json.dumps({"type": "Feature", "properties": {"class": landcover.CLASSES[k]},
                                  "geometry": mapping(shapely.transform(geom, to_lonlat))}) + "\n")
    return counts


def land_cover(g: Grid, f: Fields, core: tuple[float, ...], lines: list) -> tuple[list, list]:
    """The strip's land cover as polygons in UTM: on the ground, and shifted with the hidden ground cut out. Both
    reach one cell past the core to the east and west, so that neighbouring strips' fills overlap rather than
    leave a hairline between them."""
    ny, nx = g.Z.shape
    transform = from_origin(g.x0, g.y0 + ny * CELL, CELL, CELL)
    codes = landcover.cec(transform, (ny, nx))
    streams = [xy for kind, props, xy in lines if kind == "stream" and props.get("ord", 0) >= landcover.RIPARIAN_ORDER]
    north_up = landcover.classify(codes, g.Z[::-1], f.slope[::-1], f.north[::-1], streams, transform)
    classes = north_up[::-1]  # south to north, like the Grid
    # The core's cells, one more to the east and west.
    c0 = max(0, int((core[0] - g.x0) // CELL) - 1)
    c1 = min(nx, int(math.ceil((core[2] - g.x0) / CELL)) + 1)
    r0 = max(0, int((core[1] - g.y0) // CELL))
    r1 = min(ny, int(math.ceil((core[3] - g.y0) / CELL)))
    ground = np.full_like(classes, -1)
    ground[r0:r1, c0:c1] = classes[r0:r1, c0:c1]
    flat = landcover.polygons(ground[::-1], transform)

    # Shifted: for each column and each shifted northing, the first row whose running maximum reaches it is the
    # ground seen there. Ground outside the core's rows is another strip's, or outside the area.
    runmax = np.maximum.accumulate(g.shifted, axis=0)
    low, high = g.shifted[r0, c0:c1].min(), runmax[r1 - 1, c0:c1].max()
    top = math.ceil(high / CELL) * CELL
    ys = np.arange(math.floor(low / CELL) * CELL, top, CELL) + CELL / 2
    seen = np.full((len(ys), nx), -1, dtype=classes.dtype)
    for c in range(c0, c1):
        rows = np.searchsorted(runmax[:, c], ys)
        ok = (rows >= r0) & (rows < r1) & (ys >= g.shifted[r0, c])
        seen[ok, c] = classes[rows[ok], c]
    oblique = landcover.polygons(seen[::-1], from_origin(g.x0, top, CELL, CELL))
    return flat, oblique


class Heights:
    """Heights for the story layers: from the strips' smoothed DEMs inside the area, the Copernicus tiles
    outside it, and the lowest height (no shift) beyond them."""

    def __init__(self, area: list[tuple[dict, Path]], base: float, tmp: Path):
        self.strips = []
        for strip, dem_path in area:
            with rasterio.open(dem_path) as src:
                self.strips.append((strip["core"], src.read(1).astype(float), src.transform))
        self.base = base
        self.vrt = dem.build_vrt(tmp / "copernicus.vrt", dem.tiles(dem.COPERNICUS))

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        z = np.full(len(x), np.nan)
        for core, heights, t in self.strips:
            inside = (x >= core[0]) & (x < core[2]) & (y >= core[1]) & (y < core[3])
            if inside.any():
                cols, rows = ~t * (x[inside], y[inside])
                z[inside] = map_coordinates(heights, [rows - 0.5, cols - 0.5], order=1, mode="nearest")
        rest = np.isnan(z)
        if rest.any():
            with rasterio.open(self.vrt) as src:
                found = np.array([v[0] for v in src.sample(zip(*to_wgs(x[rest], y[rest]), strict=True))], dtype=float)
                z[rest] = np.where(found == src.nodata, self.base, found) if src.nodata is not None else found
        return z


def raise_story(heights: Heights, out: Path = OBLIQUE_DATA) -> dict[str, int]:
    """data/oblique/: the story layers with every point moved north by its height, as the line work is.
    Lines and area edges are first sampled every STORY_STEP metres so that they follow the ground."""
    def shift(x: np.ndarray, y: np.ndarray) -> list:
        return to_lonlat(np.column_stack([x, y + (heights(x, y) - heights.base) * LEAN])).tolist()

    def line(lonlat: list) -> list:
        xy = np.column_stack(to_utm(*np.array(lonlat)[:, :2].T))
        # Every STORY_STEP metres, keeping the last point, so that rings stay closed.
        dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
        s = np.unique(np.concatenate([np.arange(0, dist[-1], STORY_STEP), [dist[-1]]]))
        shifted = shift(np.interp(s, dist, xy[:, 0]), np.interp(s, dist, xy[:, 1]))
        # Once shifted, drop the samples that add nothing at map scale (about 10 m), as the flat files are rounded.
        kept = LineString(shifted).simplify(0.0001).coords if len(shifted) > 2 else shifted
        return [[round(x, 5), round(y, 5)] for x, y in kept]

    def oblique(geom: dict) -> dict:
        kind, c = geom["type"], geom["coordinates"]
        if kind == "Point":
            point = shift(*(np.array([v]) for v in to_utm(*c[:2])))[0]
            return {"type": kind, "coordinates": [round(v, 5) for v in point]}
        if kind == "LineString":
            return {"type": kind, "coordinates": line(c)}
        if kind in ("Polygon", "MultiLineString"):
            return {"type": kind, "coordinates": [line(r) for r in c]}
        if kind == "MultiPolygon":
            return {"type": kind, "coordinates": [[line(r) for r in p] for p in c]}
        raise ValueError(f"cannot raise a {kind}")

    out.mkdir(exist_ok=True)
    counts = {}
    for name in STORY:
        doc = json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))
        for f in doc["features"]:
            f["geometry"] = oblique(f["geometry"])
        text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        (out / f"{name}.geojson").write_text(text, encoding="utf-8")
        counts[name] = len(doc["features"])
    return counts


def copy_story_properties() -> list[str]:
    """data/oblique/: copy each feature's properties from the flat layer, keeping the shifted geometry.

    For a change to the story's text only (names, reasoning), which moves nothing: the geometry is the same as a full
    run would give, and this takes a second instead of hours. A feature added or removed still needs the full run."""
    changed = []
    for name in STORY:
        flat = {f["properties"]["id"]: f["properties"]
                for f in json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))["features"]}
        path = OBLIQUE_DATA / f"{name}.geojson"
        doc = json.loads(path.read_text(encoding="utf-8"))
        if {f["properties"]["id"] for f in doc["features"]} != flat.keys():
            raise SystemExit(f"oblique/{name}.geojson holds other features than {name}.geojson: run the full build")
        for f in doc["features"]:
            if f["properties"] != flat[f["properties"]["id"]]:
                f["properties"] = flat[f["properties"]["id"]]
                changed.append(f["properties"]["id"])
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return changed


def prepare_heights(area: list[dict], dems: list[Path], pool: ProcessPoolExecutor) -> float:
    """Each strip's smoothed DEM, written to `dems`, and the one lowest height of the whole area, so the strips meet."""
    list(pool.map(prepare_dem, [s["bounds"] for s in area], [CELL] * len(area), dems))
    lows = []
    for s, dem_path in zip(area, dems, strict=True):
        with rasterio.open(dem_path) as src:
            window = from_bounds(*s["core"], transform=src.transform).round_offsets().round_lengths()
            lows.append(float(src.read(1, window=window).min()))
    return min(lows)


def raise_vignettes() -> None:
    """--vignettes: data/oblique/vignettes.geojson alone, in under a minute, without the line work or the archives.

    The strips' DEMs and the lowest height are prepared as in a full run, and every story layer is shifted again into
    a scratch folder by raise_story(), so each drawing moves by the same rule as the stops: by the height under its
    own point. The other layers are not written; they must come out within RAISE_TOLERANCE of the published copies,
    or the DEM or the story has changed and the full run is needed."""
    started = time.monotonic()
    area = strips()
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        dems = [tmp / f"{s['name']}.tif" for s in area]
        with ProcessPoolExecutor(min(len(area), os.cpu_count() or 1)) as pool:
            base = prepare_heights(area, dems, pool)
        scratch = tmp / "oblique"
        counts = raise_story(Heights(list(zip(area, dems, strict=True)), base, tmp), scratch)
        moved = {name: max_move(OBLIQUE_DATA / f"{name}.geojson", scratch / f"{name}.geojson")
                 for name in STORY if name != "vignettes"}
        if max(moved.values()) > RAISE_TOLERANCE:
            raise SystemExit(f"The published oblique layers come out differently ({moved}, in degrees): the DEM or the "
                             "story changed, so run the full build")
        shutil.copy(scratch / "vignettes.geojson", OBLIQUE_DATA / "vignettes.geojson")
    print(f"data/oblique/vignettes.geojson: {counts['vignettes']} drawings; the other layers within "
          f"{max(moved.values()):.5f} degrees of their published copies; {time.monotonic() - started:.0f} s",
          flush=True)


def max_move(a: Path, b: Path) -> float:
    """The largest Hausdorff distance, in degrees, between the features of two copies of a layer, matched by id.
    Hausdorff, not vertex by vertex, because simplifying a line can keep a different number of vertices."""
    def features(path: Path) -> dict:
        return {f["properties"]["id"]: shape(f["geometry"])
                for f in json.loads(path.read_text(encoding="utf-8"))["features"]}
    old, new = features(a), features(b)
    if old.keys() != new.keys():
        raise SystemExit(f"{a.name}: the features differ from the published copy ({len(old.keys() ^ new.keys())} ids "
                         "in one copy only): the story changed, so run the full build")
    return max((shapely.hausdorff_distance(old[fid], new[fid]) for fid in old), default=0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="The Oblique view's archives and data/oblique/ (a full run: hours).",
                                     allow_abbrev=False)
    only = parser.add_mutually_exclusive_group()
    only.add_argument("--properties", action="store_true",
                      help="copy the flat layers' properties into data/oblique/ only, after a text-only story change")
    only.add_argument("--vignettes", action="store_true", help="write data/oblique/vignettes.geojson only")
    args = parser.parse_args()
    if args.properties:
        changed = copy_story_properties()
        print(f"data/oblique/: properties copied for {len(changed)} features")
        return
    if args.vignettes:
        raise_vignettes()
        return
    started = time.monotonic()
    area = strips()
    west, south = to_wgs(min(s["bounds"][0] for s in area), min(s["bounds"][1] for s in area))
    east, north = to_wgs(max(s["bounds"][2] for s in area), max(s["bounds"][3] for s in area))
    bbox = (west - 0.1, south - 0.1, east + 0.1, north + 0.1)
    # The CEC land cover, cut once to the area so the strips read a small file.
    landcover.clip(tuple(f(s["bounds"][k] for s in area) for f, k in ((min, 0), (min, 1), (max, 2), (max, 3))))
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        dems = [tmp / f"{s['name']}.tif" for s in area]
        with ProcessPoolExecutor(min(len(area), os.cpu_count() or 1)) as pool:
            base = prepare_heights(area, dems, pool)
            lines, mexico = base_lines(bbox, tmp)
            print(f"{len(area)} strips, lowest ground {base:.0f} m; "
                  f"base lines ready after {time.monotonic() - started:.0f} s", flush=True)
            jobs = []
            for s, dem_path in zip(area, dems, strict=True):
                x0, y0, x1, y1 = s["bounds"]
                mine = [line for line in lines if line[2][:, 0].max() >= x0 and line[2][:, 0].min() <= x1
                        and line[2][:, 1].max() >= y0 and line[2][:, 1].min() <= y1]
                side = mexico.intersection(box(*s["core"]))
                jobs.append(pool.submit(build_strip, s, dem_path, base, mine, side, tmp / f"{s['name']}.geojsonl",
                                        tmp / f"{s['name']}-landcover.geojsonl"))
            counts: dict[str, int] = {}
            for job in jobs:
                for kind, n in job.result().items():
                    counts[kind] = counts.get(kind, 0) + n
        summary = ", ".join(f"{k} {n:,}" for k, n in sorted(counts.items()))
        print(f"{summary}; after {time.monotonic() - started:.0f} s", flush=True)
        story = raise_story(Heights(list(zip(area, dems, strict=True)), base, tmp))
        print("data/oblique/: " + ", ".join(f"{k} {n}" for k, n in story.items()), flush=True)
        archives = write_archives(area, tmp)
        archives.append(write_landcover(area, tmp))
    print(f"Wrote {', '.join(f'{n} ({mb:.1f} MB)' for n, mb in archives)} to tiles/out/; "
          f"{time.monotonic() - started:.0f} s in all")


def write_landcover(area: list[dict], tmp: Path) -> tuple[str, float]:
    """landcover.pmtiles: the land cover on the ground, for the Flat and Tilted views. Neighbouring polygons share
    their edges, so tippecanoe simplifies those edges once."""
    layers = [("landcover", f"{s['name']}-landcover.geojsonl") for s in area]
    out = tippecanoe(tmp, "landcover.pmtiles", layers, zooms=LANDCOVER_ZOOMS, name="The Crossing: land cover",
                     attribution=landcover.NOTICE,
                     extra=("--detect-shared-borders", "--coalesce-densest-as-needed", "--no-feature-limit"))
    TILES_OUT.mkdir(parents=True, exist_ok=True)
    shutil.move(out, TILES_OUT / "landcover.pmtiles")
    return "landcover.pmtiles", (TILES_OUT / "landcover.pmtiles").stat().st_size / 1e6


def write_archives(area: list[dict], tmp: Path) -> list[tuple[str, float]]:
    """oblique-<n>.pmtiles, each from a run of neighbouring strips and under MAX_ARCHIVE_MB, and their list in
    data/oblique/archives.json for the app. A group that comes out too big is halved and built again."""
    groups, done, built = [area], [], 0
    while groups:
        group = groups.pop(0)
        built += 1
        layers = [("oblique", f"{s['name']}.geojsonl") for s in group]
        out = tippecanoe(tmp, f"part-{built}.pmtiles", layers, zooms=(9, 12), name="The Crossing: oblique relief",
                         attribution=ATTRIBUTION,
                         extra=("--no-line-simplification", "--no-feature-limit", "--detect-shared-borders"))
        if out.stat().st_size / 1e6 > MAX_ARCHIVE_MB and len(group) > 1:
            half = len(group) // 2
            groups[:0] = [group[:half], group[half:]]
        else:
            done.append((min(s["bounds"][0] for s in group), out))
    TILES_OUT.mkdir(parents=True, exist_ok=True)
    for old in TILES_OUT.glob("oblique*.pmtiles"):
        old.unlink()
    names = []
    for i, (_, out) in enumerate(sorted(done), start=1):
        name = f"oblique-{i}.pmtiles"
        shutil.move(out, TILES_OUT / name)
        names.append((name, (TILES_OUT / name).stat().st_size / 1e6))
    (OBLIQUE_DATA / "archives.json").write_text(json.dumps([n for n, _ in names]) + "\n", encoding="utf-8")
    return names


if __name__ == "__main__":
    main()
