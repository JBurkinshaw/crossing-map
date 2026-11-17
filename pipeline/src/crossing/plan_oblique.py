"""The Raised view (decisions 0017 to 0019): plan oblique relief over the corridor of the journeys.

Run from the repo root, after crossing.hachures:
    uv run --project pipeline python -m crossing.plan_oblique
    uv run --project pipeline python -m crossing.plan_oblique --properties  # after a text-only story change
    uv run --project pipeline python -m crossing.plan_oblique --vignettes   # the drawings only (under a minute)

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

The area is every fine hachure tile of the corridor, with one lowest height for all of it.
The horizon runs along each north-south column of the grid, so columns are independent: the area is built in
strips, one per column of tiles, in parallel. Each strip has its own smoothed DEM (hachures.prepare_dem),
reaching PAD further east, west and north for gradients, contours and ridges, and SOUTH further south, so that
ground just outside the area can hide ground inside it.

Inputs: the short strokes cached by crossing.hachures (fine tiles, with each tile's smoothed DEM), the Copernicus
tiles, INEGI's 1:50,000 river network for Mexico, USGS NHD flowlines for the US, and the Natural Earth and Census
layers of crossing.basemap. Writes tiles/out/oblique-<n>.pmtiles (split by strips to stay under 100 MB each;
data/raised/archives.json lists them), zoom 9-12, one layer `oblique` whose `kind` is
  stroke (Slope, Aspect and Rand, computed by crossing.hachures.stroke_properties exactly as in relief.pmtiles),
  contour (200 m form lines), crest, ridge (`rel`, relief in metres), stream (`ord`, Strahler order or a
  stand-in; `name` on the US side), country, state, county, road, railroad (lines) and mexico (the Mexico side,
  a polygon), and writes the story layers shifted by the same rule to data/raised/. `python -m tiles.install`
copies the archives into the local site.
"""

import json
import math
import os
import shutil
import subprocess
import sys
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
from scipy.ndimage import map_coordinates, minimum_filter
from scipy.spatial import cKDTree
from shapely import LineString, Polygon, box, unary_union
from shapely.geometry import mapping, shape

from crossing import basemap, dem
from crossing.hachures import ATTRIBUTION as RELIEF_ATTRIBUTION
from crossing.hachures import CRS, OUT, SCALES, corridor, coverage, prepare_dem, sampler, stroke_properties, tiles
from crossing.hydro import INEGI, NHD
from crossing.paths import DATA, TILES_OUT
from crossing.tiling import tippecanoe
from crossing.vector import read

FINE = OUT / SCALES["fine"]["folder"]
TILE = SCALES["fine"]["tile"]
CELL = 30
STEP = 8  # metres between samples along a line
STORY_STEP = 60  # metres between samples along the story's lines and area edges
# How far, in degrees, --vignettes lets the other raised layers move when raised again (about 10 m, the rounding
# of the published lines): a DEM tile added outside the corridor shifts a far point by a metre or two.
RAISE_TOLERANCE = 0.0001
LEAN = 2  # metres north per metre of height
TRIM = 0.2  # share of each stroke cut from each end
FOLD = 0.5  # smallest north-south stretch at which strokes are kept
FORM_INTERVAL = 200  # metres between form lines
PAD = 20 * CELL  # covers the ridges' 1 km relief window and the smoothing's edge
SOUTH = 6_000  # ground this far south of the area can still hide ground in it: shifts reach about 4.8 km
RAISED_DATA = DATA / "raised"
STORY = ("stops", "places", "areas", "journeys", "vignettes")
# Archives over this size are split, by groups of whole strips, to stay under the design's 100 MB per file.
MAX_ARCHIVE_MB = 95
# Shown in the map's attribution while the Raised view is on.
ATTRIBUTION = ("Streams: Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0; "
               "USGS National Hydrography Dataset courtesy of the U.S. Geological Survey; "
               "county lines courtesy of the U.S. Census Bureau (cartographic boundary files); "
               f"Made with Natural Earth; {RELIEF_ATTRIBUTION}")

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
            facing = np.abs(np.cos(across - theta)) >= math.cos(math.radians(30))
            along = np.where(ok & facing, zx * c + zy * s, np.nan)
            raster, lines = Path(tmp) / f"d{k}.tif", Path(tmp) / f"d{k}.geojson"
            transform = from_origin(x0, y0 + Z.shape[0] * CELL, CELL, CELL)
            with rasterio.open(raster, "w", driver="GTiff", width=Z.shape[1], height=Z.shape[0], count=1,
                               dtype="float32", crs=CRS, nodata=np.nan, transform=transform) as dst:
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


def build_strip(strip: dict, dem_path: Path, base: float, lines: list, mexico: Polygon, out_path: Path) -> dict:
    """The raised line work of one strip, written to `out_path` as one GeoJSON feature per line."""
    g = Grid(dem_path, base)
    core = strip["core"]
    found: list = []

    # Short hachure strokes, trimmed, and dropped where the ground is squeezed. Each tile keeps the strokes
    # on its own core, so where cached tiles overlap no stroke is drawn twice. Each stroke's Slope, Aspect and
    # Rand come from its tile's own DEM, as crossing.hachures gives them in the flat view.
    for tile, tile_core in strip["tiles"]:
        doc = json.loads((FINE / f"{tile}-split.geojson").read_text())["features"]
        if not doc:
            continue
        sample = sampler(FINE / f"{tile}.tif")
        coords = [np.asarray(f["geometry"]["coordinates"])[:, :2] for f in doc]
        ex, ey = to_utm(*np.concatenate(coords).T)
        for xy in np.split(np.column_stack([ex, ey]), np.cumsum([len(c) for c in coords])[:-1]):
            props, _ = stroke_properties(sample, LineString(xy))
            x, y = densify(xy)
            k = int(len(x) * TRIM)
            if len(x) - 2 * k >= 2:
                x, y = x[k:len(x) - k], y[k:len(y) - k]
            yp, shown = g.project(x, y, tile_core)
            runs(x, yp, shown & (g.stretch[g.cell(x, y)] >= FOLD), "stroke", props, found)

    # Form lines and the base map's lines.
    with tempfile.TemporaryDirectory() as folder:
        form = Path(folder) / "f.geojson"
        subprocess.run(["gdal_contour", "-q", "-i", str(FORM_INTERVAL), "-f", "GeoJSON", str(dem_path), str(form)],
                       check=True)
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
        with rasterio.open(raster, "w", driver="GTiff", width=len(g.xs), height=len(g.ys), count=1, dtype="float32",
                           crs=CRS,
                           transform=from_origin(g.x0, g.y0 + len(g.ys) * CELL, CELL, CELL)) as dst:
            dst.write(margin[::-1], 1)  # rows north to south, as GeoTIFF expects
        subprocess.run(["gdal_contour", "-q", "-fl", str(-CELL / 2), "-f", "GeoJSON", str(raster), str(contour)],
                       check=True)
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
            def lift(xy):
                return np.column_stack([xy[:, 0], xy[:, 1] + (g.height(xy[:, 0], xy[:, 1]) - base) * LEAN])
            sides.append(shapely.transform(poly.segmentize(STORY_STEP), lift))

    # One projection back to longitude and latitude for the whole strip.
    lon, lat = to_wgs(np.concatenate([[], *(r[2] for r in found)]), np.concatenate([[], *(r[3] for r in found)]))
    ends = np.cumsum([len(r[2]) for r in found])
    counts: dict[str, int] = {}
    with out_path.open("w") as out:
        for (kind, props, _, _), start, stop in zip(found, np.concatenate([[0], ends[:-1]]), ends, strict=False):
            pairs = zip(lon[start:stop].tolist(), lat[start:stop].tolist(), strict=True)
            coords = [(round(a, 5), round(b, 5)) for a, b in pairs]
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


def raise_story(heights: Heights, out: Path = RAISED_DATA) -> dict[str, int]:
    """data/raised/: the story layers with every point moved north by its height, as the line work is.
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

    def raised(geom: dict) -> dict:
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
            f["geometry"] = raised(f["geometry"])
        text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        (out / f"{name}.geojson").write_text(text, encoding="utf-8")
        counts[name] = len(doc["features"])
    return counts


def copy_story_properties() -> list[str]:
    """data/raised/: copy each feature's properties from the flat layer, keeping the raised geometry.

    For a change to the story's text only (names, reasoning), which moves nothing: the geometry is the same as a full
    run would give, and this takes a second instead of hours. A feature added or removed still needs the full run."""
    changed = []
    for name in STORY:
        flat = {f["properties"]["id"]: f["properties"]
                for f in json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))["features"]}
        path = RAISED_DATA / f"{name}.geojson"
        doc = json.loads(path.read_text(encoding="utf-8"))
        if {f["properties"]["id"] for f in doc["features"]} != flat.keys():
            raise SystemExit(f"raised/{name}.geojson holds other features than {name}.geojson: run the full build")
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
    """--vignettes: data/raised/vignettes.geojson alone, in minutes, without the line work or the archives.

    The strips' DEMs and the lowest height are prepared as in a full run, and every story layer is raised again into
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
        scratch = tmp / "raised"
        counts = raise_story(Heights(list(zip(area, dems, strict=True)), base, tmp), scratch)
        moved = {name: max_move(RAISED_DATA / f"{name}.geojson", scratch / f"{name}.geojson")
                 for name in STORY if name != "vignettes"}
        if max(moved.values()) > RAISE_TOLERANCE:
            raise SystemExit(f"The published raised layers come out differently ({moved}, in degrees): the DEM or the "
                             "story changed, so run the full build")
        shutil.copy(scratch / "vignettes.geojson", RAISED_DATA / "vignettes.geojson")
    print(f"data/raised/vignettes.geojson: {counts['vignettes']} drawings; the other layers within "
          f"{max(moved.values()):.5f} degrees of their published copies; {time.monotonic() - started:.0f} s",
          flush=True)


def max_move(a: Path, b: Path) -> float:
    """The largest difference, in degrees, between the coordinates of two copies of a layer, feature by feature."""
    def coords(g: dict) -> np.ndarray:
        return np.array(list(shapely.get_coordinates(shape(g))))
    old = {f["properties"]["id"]: f["geometry"] for f in json.loads(a.read_text(encoding="utf-8"))["features"]}
    worst = 0.0
    for f in json.loads(b.read_text(encoding="utf-8"))["features"]:
        x, y = coords(old[f["properties"]["id"]]), coords(f["geometry"])
        worst = max(worst, float(np.abs(x - y).max()) if x.shape == y.shape else math.inf)
    return worst


def main() -> None:
    if sys.argv[1:] == ["--properties"]:
        changed = copy_story_properties()
        print(f"data/raised/: properties copied for {len(changed)} features")
        return
    if sys.argv[1:] == ["--vignettes"]:
        raise_vignettes()
        return
    started = time.monotonic()
    area = strips()
    west, south = to_wgs(min(s["bounds"][0] for s in area), min(s["bounds"][1] for s in area))
    east, north = to_wgs(max(s["bounds"][2] for s in area), max(s["bounds"][3] for s in area))
    bbox = (west - 0.1, south - 0.1, east + 0.1, north + 0.1)
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
                jobs.append(pool.submit(build_strip, s, dem_path, base, mine, side, tmp / f"{s['name']}.geojsonl"))
            counts: dict[str, int] = {}
            for job in jobs:
                for kind, n in job.result().items():
                    counts[kind] = counts.get(kind, 0) + n
        summary = ", ".join(f"{k} {n:,}" for k, n in sorted(counts.items()))
        print(f"{summary}; after {time.monotonic() - started:.0f} s", flush=True)
        story = raise_story(Heights(list(zip(area, dems, strict=True)), base, tmp))
        print("data/raised/: " + ", ".join(f"{k} {n}" for k, n in story.items()), flush=True)
        archives = write_archives(area, tmp)
    print(f"Wrote {', '.join(f'{n} ({mb:.1f} MB)' for n, mb in archives)} to tiles/out/; "
          f"{time.monotonic() - started:.0f} s in all")


def write_archives(area: list[dict], tmp: Path) -> list[tuple[str, float]]:
    """oblique-<n>.pmtiles, each from a run of neighbouring strips and under MAX_ARCHIVE_MB, and their list in
    data/raised/archives.json for the app. A group that comes out too big is halved and built again."""
    groups, done, built = [area], [], 0
    while groups:
        group = groups.pop(0)
        built += 1
        layers = [("oblique", f"{s['name']}.geojsonl") for s in group]
        out = tippecanoe(tmp, f"part-{built}.pmtiles", layers, zooms=(9, 12), name="The Crossing: raised relief",
                         attribution=ATTRIBUTION, extra=("--no-line-simplification", "--no-feature-limit"))
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
    (RAISED_DATA / "archives.json").write_text(json.dumps([n for n, _ in names]) + "\n", encoding="utf-8")
    return names


if __name__ == "__main__":
    main()
