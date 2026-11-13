"""The Raised view (decisions 0017 and 0018): plan oblique relief over the corridor of the journeys in RAISED_JOURNEYS.

Run from the repo root, after crossing.hachures:
    uv run --project pipeline python -m crossing.plan_oblique

Plan oblique relief (Jenny and Patterson, Cartographic Perspectives 57, 2007) keeps a flat, north-up map but
moves every point north in proportion to its height, so high ground stands up and leans over the ground behind
it, as in Raisz's physiographic diagrams. Here it is applied to the map's own line work, not to a raster:
  1. Every point of every line moves north by (height - lowest height in the area) * LEAN.
  2. A point is hidden where ground to its south has moved further north than it has: the running maximum
     of shifted northing, south to north, in each 30 m column.
  3. The southern edges of the hidden ground, traced on the 30 m grid, are the crests seen against the land
     behind; they are drawn as outlines. (The northern edges, where ground comes back into view, project to the
     same place, so they are left out rather than drawn twice.)
  4. Ridgelines, the crests of every ridge whether or not it hides ground, are traced on the DEM (ridges()),
     shifted and hidden like the other lines, and left out where a crest outline already runs.
The direction of view is the same everywhere, so the result can be tiled like any other line data.

The strokes of one hachure meet end to end, so once stretched by the shift they would join into long lines,
and where the shift squeezes a slope nearly flat, strokes from neighbouring slopes cross. So each stroke loses
TRIM of its length at each end, and strokes are dropped where the ground is squeezed below FOLD of its depth.

The area is every fine hachure tile of the corridor of RAISED_JOURNEYS, with one lowest height for all of it.
The horizon runs along each north-south column of the grid, so columns are independent: the area is built in
strips, one per column of tiles, in parallel. Each strip has its own smoothed DEM (hachures.prepare_dem),
reaching PAD further east, west and north for gradients, contours and ridges, and SOUTH further south, so that
ground just outside the area can hide ground inside it.

Inputs: the short strokes cached by crossing.hachures (fine tiles), the Copernicus tiles, INEGI's 1:50,000
river network for Mexico, USGS NHD flowlines for the US, and the Natural Earth and Census layers that
tiles/build_base.py uses. Writes tiles/out/oblique.pmtiles, zoom 9-12, one layer `oblique` whose `kind` is
  stroke (Slope, Aspect and Rand, as in relief.pmtiles), contour (200 m form lines), crest,
  ridge (`rel`, relief in metres), stream (`ord`, Strahler order or a stand-in; `name` on the US side),
  country, state, county, road, railroad (lines) and mexico (the Mexico side, a polygon),
copies it to site/public/tiles/, and writes the story layers shifted by the same rule to data/raised/.
"""

import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.windows import from_bounds
from scipy.ndimage import map_coordinates, minimum_filter
from scipy.spatial import cKDTree
from shapely import LineString, Polygon, box, unary_union
from shapely.geometry import mapping, shape

from crossing.hachures import COPERNICUS, CRS, DEM_TILES, OUT, REPO, SCALES, corridor, coverage, prepare_dem, tiles

FINE = OUT / SCALES["fine"]["folder"]
TILE = SCALES["fine"]["tile"]
RAISED_JOURNEYS = ("J1", "J2", "J3", "J4")
CELL = 30
STEP = 8  # metres between samples along a line
STORY_STEP = 60  # metres between samples along the story's lines and area edges
LEAN = 2  # metres north per metre of height
TRIM = 0.2  # share of each stroke cut from each end
FOLD = 0.5  # smallest north-south stretch at which strokes are kept
FORM_INTERVAL = 200  # metres between form lines
PAD = 20 * CELL  # covers the ridges' 1 km relief window and the smoothing's edge
SOUTH = 6_000  # ground this far south of the area can still hide ground in it: shifts reach about 4.8 km
INEGI = REPO / "private" / "cache" / "hydro" / "inegi"
NHD = REPO / "private" / "cache" / "hydro" / "nhd"
BASEMAP = REPO / "private" / "cache" / "basemap"
DATA = REPO / "data"
RAISED_DATA = DATA / "raised"
STORY = ("stops", "places", "areas", "journeys")
ARCHIVE = REPO / "tiles" / "out" / "oblique.pmtiles"
# Shown in the map's attribution while the Raised view is on.
ATTRIBUTION = ("Streams: Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0; USGS National Hydrography Dataset "
               f"courtesy of the U.S. Geological Survey; county lines courtesy of the U.S. Census Bureau (TIGER); {COPERNICUS}")

to_utm = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform
to_wgs = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform


def densify(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
    s = np.arange(0, dist[-1] + STEP / 2, STEP) if dist[-1] > 0 else np.array([0.0])
    return np.interp(s, dist, xy[:, 0]), np.interp(s, dist, xy[:, 1])


def to_lonlat(xy: np.ndarray) -> np.ndarray:
    return np.round(np.column_stack(to_wgs(xy[:, 0], xy[:, 1])), 5)


# Ridgelines: a ridge is where the ground peaks across its strongest downward curvature. Thresholds for the
# smoothed 30 m DEM: curvature sharper than RIDGE_CURVATURE (1/m), at least RIDGE_RELIEF metres above the
# lowest ground within about a kilometre, and lines at least RIDGE_LENGTH metres long.
RIDGE_CURVATURE = 0.002
RIDGE_RELIEF = 100
RIDGE_LENGTH = 500


def ridges(Z: np.ndarray, x0: float, y0: float) -> list[tuple[np.ndarray, int]]:
    """Ridgelines in UTM from a south-to-north grid of heights, each with its relief (metres, in 20s).

    Each of four directions finds the ridges running across it, where the slope along it turns from rising to
    falling; a ridge is taken from the direction closest to its line of strongest curvature (within 30 degrees),
    so fixed directions avoid the sign flips of an eigenvector and neighbouring directions overlap slightly.
    """
    zy, zx = np.gradient(Z, CELL)
    zyy, zyx = np.gradient(zy, CELL)
    _, zxx = np.gradient(zx, CELL)
    # The Hessian's lower eigenvalue (strongest downward curvature) and the direction of its eigenvector.
    mean, half = (zxx + zyy) / 2, np.hypot((zxx - zyy) / 2, zyx)
    low = mean - half
    across = 0.5 * np.arctan2(2 * zyx, zxx - zyy) + np.pi / 2
    relief = Z - minimum_filter(Z, size=33)
    ok = (low < -RIDGE_CURVATURE) & (relief >= RIDGE_RELIEF)
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, theta in enumerate(np.radians([0, 45, 90, 135])):
            c, s = math.cos(theta), math.sin(theta)
            along = np.where(ok & (np.abs(np.cos(across - theta)) >= math.cos(math.radians(30))), zx * c + zy * s, np.nan)
            raster, lines = Path(tmp) / f"d{k}.tif", Path(tmp) / f"d{k}.geojson"
            with rasterio.open(raster, "w", driver="GTiff", width=Z.shape[1], height=Z.shape[0], count=1, dtype="float32",
                               crs=CRS, nodata=np.nan, transform=from_origin(x0, y0 + Z.shape[0] * CELL, CELL, CELL)) as dst:
                dst.write(along[::-1].astype("float32"), 1)
            subprocess.run(["gdal_contour", "-q", "-fl", "0", "-f", "GeoJSON", str(raster), str(lines)], check=True)
            for f in json.loads(lines.read_text())["features"]:
                xy = np.array(f["geometry"]["coordinates"])
                if len(xy) < 2 or np.hypot(*np.diff(xy, axis=0).T).sum() < RIDGE_LENGTH:
                    continue
                cols, rows = (xy[:, 0] - x0) / CELL - 0.5, (xy[:, 1] - y0) / CELL - 0.5
                r = map_coordinates(relief, [rows, cols], order=1, mode="nearest")
                out.append((xy, int(np.median(r)) // 20 * 20))
    return out


def parts(geom) -> list[np.ndarray]:
    """The coordinate arrays of a (multi)line, or of a (multi)polygon's rings."""
    if geom.is_empty:
        return []
    if isinstance(geom, LineString):
        return [np.asarray(geom.coords)[:, :2]]
    if isinstance(geom, Polygon):
        return [np.asarray(r.coords)[:, :2] for r in (geom.exterior, *geom.interiors)]
    return [xy for g in getattr(geom, "geoms", []) for xy in parts(g)]


def ogr(source: str, sql: str, bbox: tuple[float, ...], tmp: Path, extra: tuple[str, ...] = ()) -> list[dict]:
    """Features of a vector source inside a lon/lat box, in UTM, as GeoJSON dicts. Every source here is in
    longitude and latitude, so the box needs no reprojection (ogr2ogr allows none alongside -sql)."""
    out = tmp / f"{abs(hash((source, sql)))}.geojson"
    subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-t_srs", CRS, "-spat", *map(str, bbox),
                    "-dialect", "OGRSQL", "-sql", sql, "-dim", "XY", *extra, str(out), source],
                   check=True, capture_output=True)
    return [f for f in json.loads(out.read_text())["features"] if f["geometry"]]


def base_lines(bbox: tuple[float, ...], tmp: Path) -> tuple[list[tuple[str, dict, np.ndarray]], Polygon]:
    """The base map's lines in UTM as (kind, properties, coordinates), from the sources tiles/build_base.py uses,
    and the Mexico side as a polygon."""
    shp = lambda name: str(BASEMAP / name / f"{name}.shp")  # noqa: E731
    mexico = unary_union([shape(f["geometry"]) for f in ogr(
        shp("ne_10m_admin_1_states_provinces"), "SELECT name FROM ne_10m_admin_1_states_provinces WHERE adm0_a3 = 'MEX'",
        bbox, tmp)]).buffer(0)
    lines = []
    sources = {
        "country": ("ne_10m_admin_0_boundary_lines_land", "SELECT featurecla FROM ne_10m_admin_0_boundary_lines_land", ()),
        "state": ("ne_10m_admin_1_states_provinces_lines",
                  "SELECT adm0_a3 FROM ne_10m_admin_1_states_provinces_lines WHERE adm0_a3 IN ('USA', 'MEX')", ()),
        "road": ("ne_10m_roads", "SELECT type FROM ne_10m_roads WHERE continent = 'North America'", ()),
        "railroad": ("ne_10m_railroads_north_america", "SELECT scalerank FROM ne_10m_railroads_north_america", ()),
    }
    for kind, (name, sql, extra) in sources.items():
        for f in ogr(shp(name), sql, bbox, tmp, extra):
            lines += [(kind, {}, xy) for xy in parts(shape(f["geometry"]))]
    # County outlines share their edges, so the outlines are merged to draw each edge once.
    counties = ogr(shp("cb_2023_us_county_500k"), "SELECT NAME FROM cb_2023_us_county_500k WHERE STATEFP IN ('04', '35', '48')",
                   bbox, tmp, ("-nlt", "MULTILINESTRING"))
    edges = shapely.line_merge(unary_union([shape(f["geometry"]) for f in counties]))
    lines += [("county", {}, xy) for xy in parts(edges)]

    # Streams: INEGI's on the Mexico side (Strahler order 3 and up), NHD's on the US side, each clipped to its
    # own side of the border so that the two networks do not double along it.
    rivers = []
    for zip_path in sorted(INEGI.glob("*.zip")):
        for name in (n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith("_hl.shp")):
            for f in ogr(f"/vsizip/{zip_path}/{name}", f"SELECT ORDER_1 FROM {Path(name).stem} "
                         "WHERE ENTIDAD = 'CORRIENTE DE AGUA' AND ORDER_1 >= 3", bbox, tmp):
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
    for (_, props, in_mexico), inside_part, outside_part in zip(rivers, geoms, outside):
        lines += [("stream", props, xy) for xy in parts(inside_part if in_mexico else outside_part)]
    return lines, mexico


def strips() -> list[dict]:
    """One strip per column of fine tiles in the corridor: its core (UTM), the tiles in it, and its DEM's bounds."""
    region = corridor(RAISED_JOURNEYS).intersection(coverage().buffer(-60))
    columns: dict[float, list] = {}
    for name, core in tiles(region, TILE):
        columns.setdefault(core.bounds[0], []).append((name, core.bounds))
    out = []
    for x0, cells in sorted(columns.items()):
        y0, y1 = min(b[1] for _, b in cells), max(b[3] for _, b in cells)
        if len(cells) * TILE != y1 - y0:
            raise ValueError(f"tiles at {x0:.0f} E do not form one column")
        snap = lambda v, up: (math.ceil if up else math.floor)(v / CELL) * CELL  # noqa: E731
        out.append({"name": f"{round(x0 / 1000)}e", "core": (x0, y0, x0 + TILE, y1), "tiles": cells,
                    "bounds": (snap(x0 - PAD, False), snap(y0 - SOUTH, False), snap(x0 + TILE + PAD, True), snap(y1 + PAD, True))})
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
    for start, stop in zip(edges[::2], edges[1::2]):
        if stop - start >= 2:
            out.append((kind, props, x[start:stop], yp[start:stop]))


def build_strip(strip: dict, dem_path: Path, base: float, lines: list, mexico: Polygon, out_path: Path) -> dict:
    """The raised line work of one strip, written to `out_path` as one GeoJSON feature per line."""
    g = Grid(dem_path, base)
    core = strip["core"]
    found: list = []

    # Short hachure strokes, trimmed, and dropped where the ground is squeezed. Each tile keeps the strokes
    # on its own core, so where cached tiles overlap no stroke is drawn twice.
    gy, gx = np.gradient(g.dem, g.t.e, g.t.a)
    for tile, tile_core in strip["tiles"]:
        doc = json.loads((FINE / f"{tile}-split.geojson").read_text())["features"]
        if not doc:
            continue
        coords = [np.asarray(f["geometry"]["coordinates"])[:, :2] for f in doc]
        ex, ey = to_utm(*np.concatenate(coords).T)
        for xy in np.split(np.column_stack([ex, ey]), np.cumsum([len(c) for c in coords])[:-1]):
            x, y = densify(xy)
            mx, my = x[len(x) // 2], y[len(y) // 2]
            cols, rows = ~g.t * (mx, my)
            r, c = min(max(int(rows), 0), gx.shape[0] - 1), min(max(int(cols), 0), gx.shape[1] - 1)
            sx, sy = gx[r, c], gy[r, c]
            props = {"Slope": round(math.degrees(math.atan(math.hypot(sx, sy)))),
                     "Aspect": round(math.degrees(math.atan2(-sx, -sy))) // 5 * 5 % 360,
                     "Rand": zlib.crc32(json.dumps([round(v, 1) for v in xy[0]]).encode()) % 10}
            k = int(len(x) * TRIM)
            if len(x) - 2 * k >= 2:
                x, y = x[k:len(x) - k], y[k:len(y) - k]
            yp, shown = g.project(x, y, tile_core)
            runs(x, yp, shown & (g.stretch[g.cell(x, y)] >= FOLD), "stroke", props, found)

    # Form lines and the base map's lines.
    with tempfile.TemporaryDirectory() as folder:
        form = Path(folder) / "f.geojson"
        subprocess.run(["gdal_contour", "-q", "-i", str(FORM_INTERVAL), "-f", "GeoJSON", str(dem_path), str(form)], check=True)
        form_lines = [np.array(f["geometry"]["coordinates"]) for f in json.loads(form.read_text())["features"]]
    for xy in form_lines:
        x, y = densify(xy)
        runs(x, *g.project(x, y, core), "contour", {}, found)
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
        with rasterio.open(raster, "w", driver="GTiff", width=len(g.xs), height=len(g.ys), count=1, dtype="float32", crs=CRS,
                           transform=from_origin(g.x0, g.y0 + len(g.ys) * CELL, CELL, CELL)) as dst:
            dst.write(margin[::-1], 1)  # rows north to south, as GeoTIFF expects
        subprocess.run(["gdal_contour", "-q", "-fl", str(-CELL / 2), "-f", "GeoJSON", str(raster), str(contour)], check=True)
        crests = json.loads(contour.read_text())["features"]
    outline = []
    for f in crests:
        xy = np.array(f["geometry"]["coordinates"])
        if len(xy) < 2 or np.hypot(*np.diff(xy, axis=0).T).sum() < 150:
            continue
        x, y = densify(xy)
        yp = y + (g.height(x, y) - base) * LEAN
        inside = (x >= core[0]) & (x < core[2]) & (y >= core[1]) & (y < core[3])
        before = len(found)
        runs(x, yp, falling[g.cell(x, y)] & inside, "crest", {}, found)
        outline += [np.column_stack(run[2:]) for run in found[before:]]

    # Ridgelines, shifted and hidden like the strokes, except within three cells of a crest outline.
    near = cKDTree(np.concatenate(outline)) if outline else None
    for xy, rel in ridges(g.Z, g.x0, g.y0):
        x, y = densify(xy)
        yp, shown = g.project(x, y, core)
        if near is not None:
            shown &= near.query(np.column_stack([x, yp]), distance_upper_bound=3 * CELL)[0] == np.inf
        runs(x, yp, shown, "ridge", {"rel": rel}, found)

    # The Mexico side, a polygon, shifted but not hidden: the paper colour under the line work.
    sides = []
    side = mexico.intersection(box(*core))
    for poly in getattr(side, "geoms", [side]):
        if isinstance(poly, Polygon) and not poly.is_empty:
            sides.append(shapely.transform(poly.segmentize(STORY_STEP),
                                           lambda xy: np.column_stack([xy[:, 0], xy[:, 1] + (g.height(xy[:, 0], xy[:, 1]) - base) * LEAN])))

    # One projection back to longitude and latitude for the whole strip.
    lon, lat = to_wgs(np.concatenate([[], *(r[2] for r in found)]), np.concatenate([[], *(r[3] for r in found)]))
    ends = np.cumsum([len(r[2]) for r in found])
    counts: dict[str, int] = {}
    with out_path.open("w") as out:
        for (kind, props, _, _), start, stop in zip(found, np.concatenate([[0], ends[:-1]]), ends):
            coords = [(round(a, 5), round(b, 5)) for a, b in zip(lon[start:stop].tolist(), lat[start:stop].tolist())]
            feature = {"type": "Feature", "properties": {"kind": kind, **props},
                       "geometry": {"type": "LineString", "coordinates": coords}}
            # Below zoom 12 the style draws 70% of the strokes, so the rest are tiled only at 12.
            if kind == "stroke" and props["Rand"] >= 7:
                feature["tippecanoe"] = {"minzoom": 12}
            out.write(json.dumps(feature) + "\n")
            counts[kind] = counts.get(kind, 0) + 1
        for poly in sides:
            out.write(json.dumps({"type": "Feature", "properties": {"kind": "mexico"},
                                  "geometry": mapping(shapely.transform(poly, to_lonlat))}) + "\n")
            counts["mexico"] = counts.get("mexico", 0) + 1
    return counts


class Heights:
    """Heights for the story layers: from the strips' smoothed DEMs inside the area, the Copernicus tiles
    outside it, and the lowest height (no shift) beyond them."""

    def __init__(self, area: list[tuple[dict, Path]], base: float, tmp: Path):
        self.strips = []
        for strip, dem_path in area:
            with rasterio.open(dem_path) as src:
                self.strips.append((strip["core"], src.read(1).astype(float), src.transform))
        self.base = base
        self.vrt = tmp / "copernicus.vrt"
        subprocess.run(["gdalbuildvrt", "-q", str(self.vrt), *map(str, sorted(DEM_TILES.glob("*.tif")))], check=True)

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        z = np.full(len(x), np.nan)
        for core, dem, t in self.strips:
            inside = (x >= core[0]) & (x < core[2]) & (y >= core[1]) & (y < core[3])
            if inside.any():
                cols, rows = ~t * (x[inside], y[inside])
                z[inside] = map_coordinates(dem, [rows - 0.5, cols - 0.5], order=1, mode="nearest")
        rest = np.isnan(z)
        if rest.any():
            with rasterio.open(self.vrt) as src:
                found = np.array([v[0] for v in src.sample(zip(*to_wgs(x[rest], y[rest])))], dtype=float)
                z[rest] = np.where(found == src.nodata, self.base, found) if src.nodata is not None else found
        return z


def raise_story(heights: Heights) -> dict[str, int]:
    """data/raised/: the story layers with every point moved north by its height, as the line work is.
    Lines and area edges are first sampled every STORY_STEP metres so that they follow the ground."""
    def shift(x: np.ndarray, y: np.ndarray) -> list:
        return to_lonlat(np.column_stack([x, y + (heights(x, y) - heights.base) * LEAN])).tolist()

    def line(lonlat: list) -> list:
        xy = np.column_stack(to_utm(*np.array(lonlat)[:, :2].T))
        # Every STORY_STEP metres, keeping the last point, so that rings stay closed.
        dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
        s = np.unique(np.concatenate([np.arange(0, dist[-1], STORY_STEP), [dist[-1]]]))
        return shift(np.interp(s, dist, xy[:, 0]), np.interp(s, dist, xy[:, 1]))

    def raised(geom: dict) -> dict:
        kind, c = geom["type"], geom["coordinates"]
        if kind == "Point":
            return {"type": kind, "coordinates": shift(*(np.array([v]) for v in to_utm(*c[:2])))[0]}
        if kind == "LineString":
            return {"type": kind, "coordinates": line(c)}
        if kind in ("Polygon", "MultiLineString"):
            return {"type": kind, "coordinates": [line(r) for r in c]}
        if kind == "MultiPolygon":
            return {"type": kind, "coordinates": [[line(r) for r in p] for p in c]}
        raise ValueError(f"cannot raise a {kind}")

    RAISED_DATA.mkdir(exist_ok=True)
    counts = {}
    for name in STORY:
        doc = json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))
        if name == "journeys":
            doc["features"] = [f for f in doc["features"] if f["properties"].get("journey") in RAISED_JOURNEYS]
        for f in doc["features"]:
            f["geometry"] = raised(f["geometry"])
        (RAISED_DATA / f"{name}.geojson").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        counts[name] = len(doc["features"])
    return counts


def main() -> None:
    started = time.monotonic()
    area = strips()
    west, south = to_wgs(min(s["bounds"][0] for s in area), min(s["bounds"][1] for s in area))
    east, north = to_wgs(max(s["bounds"][2] for s in area), max(s["bounds"][3] for s in area))
    bbox = (west - 0.1, south - 0.1, east + 0.1, north + 0.1)
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        dems = [tmp / f"{s['name']}.tif" for s in area]
        with ProcessPoolExecutor(min(len(area), os.cpu_count() or 1)) as pool:
            list(pool.map(prepare_dem, [s["bounds"] for s in area], [CELL] * len(area), dems))
            # One lowest height for the whole area, so the strips meet.
            lows = []
            for s, dem in zip(area, dems):
                with rasterio.open(dem) as src:
                    window = from_bounds(*s["core"], transform=src.transform).round_offsets().round_lengths()
                    lows.append(float(src.read(1, window=window).min()))
            base = min(lows)
            lines, mexico = base_lines(bbox, tmp)
            print(f"{len(area)} strips, lowest ground {base:.0f} m; base lines ready after {time.monotonic() - started:.0f} s", flush=True)
            jobs = []
            for s, dem in zip(area, dems):
                x0, y0, x1, y1 = s["bounds"]
                mine = [line for line in lines if line[2][:, 0].max() >= x0 and line[2][:, 0].min() <= x1
                        and line[2][:, 1].max() >= y0 and line[2][:, 1].min() <= y1]
                jobs.append(pool.submit(build_strip, s, dem, base, mine, mexico.intersection(box(*s["core"])), tmp / f"{s['name']}.geojsonl"))
            counts: dict[str, int] = {}
            for job in jobs:
                for kind, n in job.result().items():
                    counts[kind] = counts.get(kind, 0) + n
        print(", ".join(f"{k} {n:,}" for k, n in sorted(counts.items())) + f"; after {time.monotonic() - started:.0f} s", flush=True)
        story = raise_story(Heights(list(zip(area, dems)), base, tmp))
        print("data/raised/: " + ", ".join(f"{k} {n}" for k, n in story.items()), flush=True)
        # Relative names keep local paths out of the archive's metadata.
        layers = [arg for s in area for arg in ("-L", f"oblique:{s['name']}.geojsonl")]
        subprocess.run(["tippecanoe", "-q", "-f", "-o", "oblique.pmtiles", "-Z9", "-z12", "--no-line-simplification",
                        "--no-tile-size-limit", "--no-feature-limit", "-n", "The Crossing: raised relief, journeys 1 and 2",
                        "-A", ATTRIBUTION, *layers], check=True, cwd=tmp)
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp / "oblique.pmtiles", ARCHIVE)
    shutil.copy(ARCHIVE, REPO / "site" / "public" / "tiles" / "oblique.pmtiles")
    print(f"Wrote {ARCHIVE.relative_to(REPO)} ({ARCHIVE.stat().st_size / 1e6:.1f} MB) and copied it to site/public/tiles/; "
          f"{time.monotonic() - started:.0f} s in all")


if __name__ == "__main__":
    main()
