"""Draft outlines for the inferred areas, cut from each stop's circle by the clues in its reasoning (decision 0020).

Run from the repo root:
    uv run --project pipeline python -m crossing.area_drafts [--force]  # write pipeline/seeds/areas.geojson
    uv run --project pipeline python -m crossing.area_drafts --inspect  # what lies in each circle, for writing rules
    uv run --project pipeline --with matplotlib python -m crossing.area_drafts --images  # also the contact sheets
    uv run --project pipeline python -m crossing.area_drafts --qgis     # La Babícora comparison and QGIS layers

Writes the seed pipeline/seeds/areas.geojson, which crossing.build_story reads in place of each stop's circle. Like
crossing.regions, it refuses to overwrite the seed without --force, and with --force it keeps every area whose
draft_confidence is "checked" (finished by hand in the QGIS project, pipeline/qgis/areas.qgs). A report per area
(rule, confidence, old and new km², whether the pin is inside) and the images go to private/review/areas/; the
extracted source layers stay in private/overnight/areas/.

Decision 0008 has each inferred area drawn by hand in QGIS. These drafts are the starting point for that drawing:
each area keeps the stop's circle (radius_km about the pin) as its upper bound and cuts it to the ground the
evidence describes (a valley floor, a river's banks, a road's verge, a playa, the side of a line). Each rule is
written out in plain words in the seed, with a confidence:
  high    the clue names the ground (on the river, on the playa, on the boundary) and the data finds it;
  medium  the clue points at the ground, but the cut takes a judgement (a width, a threshold, a proxy line);
  low     the cut leans on a reading of the text that could be wrong;
  kept    the evidence gives nothing to cut by, so the circle stays.
"""

import argparse
import csv
import json
import math
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
import rasterio.enums
import rasterio.features
import rasterio.warp
import shapely
from pyproj import Geod, Transformer
from rasterio.transform import from_origin
from scipy.ndimage import distance_transform_edt, gaussian_filter
from shapely import LineString, MultiPolygon, Point, Polygon, box, unary_union
from shapely.geometry import mapping, shape

from crossing.paths import CACHE, DATA, PRIVATE, REPO, SEEDS

DEM_FOLDERS = [CACHE / "dem" / "copernicus", CACHE / "dem" / "copernicus-region"]
WORK = PRIVATE / "overnight" / "areas"
LAYERS = WORK / "layers.gpkg"
SEED = SEEDS / "areas.geojson"
# The QGIS project for hand edits, and the layers it needs beside the seed.
QGIS = REPO / "pipeline" / "qgis"
# The per-area report and the images: review material, so outside git.
REPORT = PRIVATE / "review" / "areas"
GEOD = Geod(ellps="WGS84")
# Every frame lies inside this box (lon/lat), so the extracted layers need cover no more.
EXTRACT_BOX = (-109.9, 28.7, -107.1, 33.2)
GEOBOUNDARIES = CACHE / "boundaries" / "geoboundaries" / "geoBoundaries-MEX-ADM2.geojson"
BABICORA_MUNICIPIOS = ["Temósachic", "Namiquipa", "Madera", "Gómez Farías"]
COPERNICUS = (
    "Copernicus DEM GLO-30, © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, "
    "provided under COPERNICUS by the European Union and ESA"
)


# ---------------------------------------------------------------------------------------------------------------
# Source layers, extracted once into one GeoPackage (lon/lat) so each frame can query it by box.


def ogr(*args: str) -> None:
    subprocess.run(["ogr2ogr", *args], check=True, capture_output=True)


def prepare() -> None:
    """Extract the streams, water bodies, roads and Natural Earth lines the rules use into LAYERS."""
    if LAYERS.exists():
        return
    WORK.mkdir(parents=True, exist_ok=True)
    tmp = LAYERS.with_suffix(".tmp.gpkg")
    tmp.unlink(missing_ok=True)
    spat = ["-spat", *map(str, EXTRACT_BOX)]
    first = {"streams": True, "water": True, "roads": True}

    def add(layer: str, src: str, sql: str, extra: tuple[str, ...] = (), dialect: str = "OGRSQL") -> None:
        mode = ["-update"] if tmp.exists() else []
        mode += [] if first[layer] else ["-append"]
        first[layer] = False
        ogr(
            "-f",
            "GPKG",
            *mode,
            "-nln",
            layer,
            "-t_srs",
            "EPSG:4326",
            "-nlt",
            "PROMOTE_TO_MULTI",
            "-dim",
            "XY",
            *spat,
            "-dialect",
            dialect,
            "-sql",
            sql,
            *extra,
            str(tmp),
            src,
        )

    latin1 = ("--config", "SHAPE_ENCODING", "ISO-8859-1")
    for zip_path in sorted((CACHE / "hydro" / "inegi").glob("*.zip")):
        names = zipfile.ZipFile(zip_path).namelist()
        for name in (n for n in names if n.endswith("_hl.shp")):
            stem = Path(name).stem
            add(
                "streams",
                f"/vsizip/{zip_path}/{name}",
                "SELECT CAST(ORDER_1 AS integer) AS ord, CVE_SUBC AS subc, 'inegi' AS src, "
                f"CAST(NULL AS character(100)) AS name "
                f"FROM {stem} WHERE ENTIDAD IN ('CORRIENTE DE AGUA', 'LINEA CENTRAL') AND ORDER_1 >= 2",
                latin1,
            )
        for name in (n for n in names if n.endswith("_ha.shp")):
            add(
                "water",
                f"/vsizip/{zip_path}/{name}",
                "SELECT CONDICION AS kind, 'inegi' AS src, CAST(NULL AS character(100)) AS name "
                f"FROM {Path(name).stem}",
                latin1,
            )
    # NHD flowlines carry no stream order here; as in crossing.plan_oblique, the scale NHD shows a line from stands
    # in for it (500,000 is about INEGI's order 3). Small unnamed streams get order 1.
    for shp in sorted((CACHE / "hydro" / "nhd").glob("*/Shape/NHDFlowline.shp")):
        add(
            "streams",
            str(shp),
            "SELECT CASE WHEN visibility >= 5000000 THEN 6 WHEN visibility >= 2000000 THEN 5 "
            "WHEN visibility >= 1000000 "
            "THEN 4 WHEN visibility >= 500000 THEN 3 WHEN gnis_name IS NOT NULL THEN 2 ELSE 1 END AS ord, "
            "CAST(NULL AS TEXT) AS subc, 'nhd' AS src, gnis_name AS name, geometry FROM NHDFlowline WHERE ftype = 460",
            dialect="SQLITE",
        )
        add(
            "water",
            str(shp.with_name("NHDWaterbody.shp")),
            "SELECT CAST(ftype AS character) AS kind, 'nhd' AS src, gnis_name AS name FROM NHDWaterbody",
        )
    for zip_path in sorted((CACHE / "roads" / "tiger").glob("*.zip")):
        stem = zip_path.stem
        add(
            "roads",
            f"/vsizip/{zip_path}/{stem}.shp",
            f"SELECT FULLNAME AS name, MTFCC AS class, 'tiger' AS src FROM {stem}",
        )
    ne = CACHE / "basemap"
    add(
        "roads",
        str(ne / "ne_10m_roads" / "ne_10m_roads.shp"),
        "SELECT name, type AS class, 'ne' AS src FROM ne_10m_roads WHERE continent = 'North America'",
    )
    for layer in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_north_america"):
        ogr(
            "-f",
            "GPKG",
            "-update",
            "-append",
            "-nln",
            "ne_rivers",
            "-t_srs",
            "EPSG:4326",
            "-nlt",
            "PROMOTE_TO_MULTI",
            "-dim",
            "XY",
            *spat,
            "-dialect",
            "OGRSQL",
            "-sql",
            f"SELECT name FROM {layer} WHERE name IS NOT NULL",
            str(tmp),
            str(ne / layer / f"{layer}.shp"),
        )
    ogr(
        "-f",
        "GPKG",
        "-update",
        "-append",
        "-nln",
        "ne_lakes",
        "-t_srs",
        "EPSG:4326",
        "-nlt",
        "PROMOTE_TO_MULTI",
        *spat,
        "-dialect",
        "OGRSQL",
        "-sql",
        "SELECT name FROM ne_10m_lakes_north_america",
        str(tmp),
        str(ne / "ne_10m_lakes_north_america" / "ne_10m_lakes_north_america.shp"),
    )
    tmp.rename(LAYERS)
    print(f"Wrote {LAYERS.relative_to(REPO)}")


# ---------------------------------------------------------------------------------------------------------------
# A frame: the ground around one stop, in an azimuthal equidistant projection centred on the stop, so the old
# geodesic circle is an exact circle of radius_km about the origin.


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def places() -> dict[str, tuple[float, float]]:
    out = {}
    for f in json.loads((DATA / "places.geojson").read_text(encoding="utf-8"))["features"]:
        out[f["properties"]["id"].removeprefix("place-")] = tuple(f["geometry"]["coordinates"])
    return out


PLACES = places()


class Frame:
    def __init__(self, sid: str, lon: float, lat: float, radius_km: float, pad: float = 1.6):
        self.sid, self.lon, self.lat = sid, lon, lat
        self.crs = f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m +no_defs"
        self.r = radius_km * 1000
        self.cell = 30 if radius_km <= 5 else 60 if radius_km <= 12 else 90
        n = math.ceil(2 * max(self.r * pad, 4000) / self.cell)
        self.half = n * self.cell / 2
        self.transform = from_origin(-self.half, self.half, self.cell, self.cell)
        self.shape = (n, n)
        fwd = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)
        inv = Transformer.from_crs(self.crs, "EPSG:4326", always_xy=True)
        self.to_local, self.to_wgs = fwd.transform, inv.transform
        corners = [inv.transform(x, y) for x in (-self.half, self.half) for y in (-self.half, self.half)]
        self.bbox = (
            min(c[0] for c in corners) - 0.01,
            min(c[1] for c in corners) - 0.01,
            max(c[0] for c in corners) + 0.01,
            max(c[1] for c in corners) + 0.01,
        )
        self.bound = Point(0, 0).buffer(self.r, quad_segs=64)
        self.pin = Point(0, 0)
        self.extent = box(-self.half, -self.half, self.half, self.half)
        self._dem = None
        self.notes: list[str] = []

    # --- rasters -------------------------------------------------------------------------------------------
    @property
    def dem(self) -> np.ndarray:
        if self._dem is None:
            dem = np.full(self.shape, np.nan, dtype="float32")
            w, s, e, n = self.bbox
            for folder in DEM_FOLDERS:
                for tif in sorted(folder.glob("*.tif")):
                    with rasterio.open(tif) as src:
                        b = src.bounds
                        if b.right <= w or b.left >= e or b.top <= s or b.bottom >= n:
                            continue
                        part = np.full(self.shape, np.nan, dtype="float32")
                        rasterio.warp.reproject(
                            rasterio.band(src, 1),
                            part,
                            dst_transform=self.transform,
                            dst_crs=self.crs,
                            resampling=rasterio.enums.Resampling.bilinear,
                            dst_nodata=np.nan,
                        )
                        dem = np.where(np.isnan(dem), part, dem)
            if np.isnan(dem).any():
                self.notes.append(f"DEM has {np.isnan(dem).mean():.0%} gaps in the frame")
            self._dem = dem
        return self._dem

    def xy(self) -> tuple[np.ndarray, np.ndarray]:
        """Cell-centre coordinates (x, y) of the grid, row 0 at the top."""
        c = (np.arange(self.shape[0]) + 0.5) * self.cell
        return np.meshgrid(-self.half + c, self.half - c)

    def slope(self, sigma: float = 1.0) -> np.ndarray:
        z = gaussian_filter(np.nan_to_num(self.dem, nan=float(np.nanmean(self.dem))), sigma)
        gy, gx = np.gradient(z, self.cell)
        return np.degrees(np.arctan(np.hypot(gx, gy)))

    def poly(self, mask: np.ndarray):
        """The cells of a boolean grid as one (multi)polygon in local metres."""
        mask = mask & ~np.isnan(self.dem)
        if not mask.any():
            return Polygon()
        return unary_union(
            [
                shape(g)
                for g, v in rasterio.features.shapes(mask.astype("uint8"), mask=mask, transform=self.transform)
                if v == 1
            ]
        )

    def raster(self, geom) -> np.ndarray:
        if geom.is_empty:
            return np.zeros(self.shape, bool)
        return rasterio.features.rasterize(
            [geom], out_shape=self.shape, transform=self.transform, all_touched=True, dtype="uint8"
        ).astype(bool)

    def below(self, m: float):
        return self.poly(self.dem < m)

    def above(self, m: float):
        return self.poly(self.dem >= m)

    def flat(self, deg: float, sigma: float = 2.0):
        """Ground with a smoothed slope under `deg` degrees."""
        return self.poly(self.slope(sigma) < deg)

    def low_ground(self, rise: float, near_km: float | None = None):
        """Ground within `rise` metres of the lowest ground in the circle: a playa or a valley floor."""
        inside = self.raster(self.bound if near_km is None else self.pin.buffer(near_km * 1000))
        floor = np.nanpercentile(self.dem[inside], 1)
        return self.poly(self.dem < floor + rise)

    def hand(self, lines) -> np.ndarray:
        """Height of each cell above the nearest cell of `lines` (a height-above-drainage for a chosen river)."""
        on = self.raster(lines)
        if not on.any():
            return np.full(self.shape, np.inf)
        _, (iy, ix) = distance_transform_edt(~on, return_indices=True)
        return self.dem - self.dem[iy, ix]

    def beside(self, lines, side: str, near_km: float, far_km: float):
        """Ground on one side of a river ("west" or "east"): cells between `near_km` and `far_km` from the lines
        whose nearest point on them lies the other way."""
        on = self.raster(lines)
        dist, (iy, ix) = distance_transform_edt(~on, return_indices=True, sampling=self.cell)
        cols = np.arange(self.shape[1])[None, :]
        way = ix > cols if side == "west" else ix < cols
        return self.poly(way & (dist >= near_km * 1000) & (dist <= far_km * 1000))

    def valley_floor(self, lines, rise: float, km: float):
        """Ground within `km` of the lines and no more than `rise` metres above them."""
        return self.poly(self.hand(lines) < rise).intersection(lines.buffer(km * 1000))

    def above_river(self, lines, rise: float, km: float):
        """Ground within `km` of the lines and at least `rise` metres above them: a rim or promontory over a river."""
        return self.poly(self.hand(lines) >= rise).intersection(lines.buffer(km * 1000))

    def drop_toward(self, bearing: float, km: float, drop: float):
        """Ground that looks down at least `drop` metres within `km` toward `bearing` (degrees from north):
        the edge of an escarpment facing that way."""
        z = np.nan_to_num(self.dem, nan=1e6)
        lowest = np.full(self.shape, np.inf, dtype="float32")
        dx, dy = math.sin(math.radians(bearing)), -math.cos(math.radians(bearing))  # rows grow southward
        for k in range(1, int(km * 1000 / self.cell) + 1):
            sx, sy = int(round(dx * k)), int(round(dy * k))
            shifted = np.full(self.shape, np.inf, dtype="float32")
            h, w = self.shape
            src = z[max(sy, 0) : h + min(sy, 0), max(sx, 0) : w + min(sx, 0)]
            shifted[max(-sy, 0) : h + min(-sy, 0), max(-sx, 0) : w + min(-sx, 0)] = src
            lowest = np.minimum(lowest, shifted)
        return self.poly(z - lowest >= drop)

    def viewshed(self, point: Point, height: float = 10, target: float = 2, km: float | None = None):
        """Ground from which a light `height` metres up at `point` could be seen (a target `target` m up)."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "dem.tif", Path(tmp) / "view.tif"
            with rasterio.open(
                src,
                "w",
                driver="GTiff",
                width=self.shape[1],
                height=self.shape[0],
                count=1,
                dtype="float32",
                crs=self.crs,
                transform=self.transform,
                nodata=-9999,
            ) as d:
                d.write(np.nan_to_num(self.dem, nan=-9999).astype("float32"), 1)
            args = [
                "gdal_viewshed",
                "-q",
                "-ox",
                str(point.x),
                "-oy",
                str(point.y),
                "-oz",
                str(height),
                "-tz",
                str(target),
                "-vv",
                "1",
                "-iv",
                "0",
                "-ov",
                "0",
            ]
            if km:
                args += ["-md", str(km * 1000)]
            subprocess.run([*args, str(src), str(dst)], check=True, capture_output=True)
            with rasterio.open(dst) as v:
                return self.poly(v.read(1) == 1)

    # --- vectors -------------------------------------------------------------------------------------------
    def features(self, layer: str, where: str | None = None) -> list[tuple]:
        args = ["ogr2ogr", "-f", "GeoJSON", "-t_srs", self.crs, "-spat", *map(str, self.bbox), "-dim", "XY"]
        if where:
            args += ["-where", where]
        out = subprocess.run(
            [*args, "/vsistdout/", str(LAYERS), layer], check=True, capture_output=True, text=True
        ).stdout
        return [(shape(f["geometry"]), f["properties"]) for f in json.loads(out)["features"] if f["geometry"]]

    def streams(self, min_order: int = 3, where: str | None = None):
        clause = f"ord >= {min_order}" + (f" AND ({where})" if where else "")
        return unary_union([g for g, _ in self.features("streams", clause)])

    def nhd(self, name: str):
        return unary_union([g for g, _ in self.features("streams", f"name = '{name}'")])

    def river(self, name: str, snap_km: float = 2.5, min_order: int = 3):
        """A named river: Natural Earth gives the name, INEGI or NHD the channel. The channel is the streams lying
        mostly (70% of their length) within `snap_km` of Natural Earth's line, of the order that makes up most of
        that length or higher, less one (the main stem changes order as it gathers tributaries)."""
        ne = unary_union([g for g, _ in self.features("ne_rivers", f"name = '{name}'")])
        if ne.is_empty:
            raise ValueError(f"{self.sid}: no Natural Earth river named {name}")
        zone = ne.buffer(snap_km * 1000)
        near = [
            (g, p["ord"])
            for g, p in self.features("streams", f"ord >= {min_order}")
            if g.length and g.intersection(zone).length >= 0.7 * g.length
        ]
        if not near:
            self.notes.append(f"no INEGI/NHD channel near Natural Earth's {name}; used Natural Earth's line")
            return ne
        length: dict[int, float] = {}
        for g, o in near:
            if g.intersects(self.bound):
                length[o] = length.get(o, 0) + g.length
        main = max(length, key=length.get) if length else max(o for _, o in near)
        return unary_union([g for g, o in near if o >= main - 1])

    def main_stream(self):
        """The highest-order stream crossing the circle."""
        segs = [(g, p["ord"]) for g, p in self.features("streams", "ord >= 3") if g.intersects(self.bound)]
        top = max(o for _, o in segs)
        return unary_union([g for g, o in segs if o == top])

    def between(self, a: Point, b: Point, margin: float) -> Polygon:
        """The strip between two points, bounded by lines through each that run down the general slope of the
        circle: the ground between two draws that run side by side."""
        z = gaussian_filter(np.nan_to_num(self.dem, nan=float(np.nanmean(self.dem))), 3)
        grow, gcol = np.gradient(z, self.cell)
        inside = self.raster(self.bound)
        u = np.array([-gcol[inside].mean(), grow[inside].mean()])
        u /= np.hypot(*u)
        d = 50_000
        pa, pb = np.array(a.coords[0]), np.array(b.coords[0])
        return shapely.MultiPoint([pa - u * d, pa + u * d, pb - u * d, pb + u * d]).convex_hull.buffer(margin)

    def stem(self, at: Point, min_order: int = 3, max_km: float = 3):
        """The stream nearest `at` (order `min_order` or more) and the connected segments of the same order."""
        segs = [(g, p["ord"]) for g, p in self.features("streams", f"ord >= {min_order}")]
        g0, o0 = min(segs, key=lambda s: s[0].distance(at))
        if g0.distance(at) > max_km * 1000:
            self.notes.append(f"nearest stream is {g0.distance(at) / 1000:.1f} km away")
        same = [g for g, o in segs if o == o0]
        merged = unary_union(same).buffer(5)
        part = min(getattr(merged, "geoms", [merged]), key=lambda p: p.distance(g0))
        return unary_union([g for g in same if g.intersects(part)])

    def roads(self, where: str):
        return unary_union([g for g, _ in self.features("roads", where)])

    def water(self, near: Point, max_km: float = 5, where: str | None = None):
        polys = [g for g, _ in self.features("water", where) if g.distance(near) < max_km * 1000]
        if not polys:
            return Polygon()
        merged = unary_union(polys)
        return max(getattr(merged, "geoms", [merged]), key=lambda p: p.area if p.distance(near) < max_km * 1000 else 0)

    def ne_lake(self, name: str):
        return unary_union([g for g, _ in self.features("ne_lakes", f"name = '{name}'")])

    def place(self, pid: str) -> Point:
        return Point(self.to_local(*PLACES[pid]))

    def ll(self, lon: float, lat: float) -> Point:
        return Point(self.to_local(lon, lat))

    def line(self, *points) -> LineString:
        """A line through places (ids) or (lon, lat) pairs, densified so it follows the geodesic."""
        pts = [PLACES[p] if isinstance(p, str) else p for p in points]
        coords = []
        for a, b in zip(pts, pts[1:], strict=False):
            n = 50
            mid = GEOD.npts(a[0], a[1], b[0], b[1], n)
            coords += [a, *mid]
        coords.append(pts[-1])
        return LineString([self.to_local(x, y) for x, y in coords])

    def wgs_box(self, west: float, south: float, east: float, north: float) -> Polygon:
        """A lon/lat box, densified, in local metres: for 'east of a meridian' or 'north of a parallel'."""
        ring = (
            [(west + (east - west) * i / 40, south) for i in range(41)]
            + [(east, south + (north - south) * i / 40) for i in range(41)]
            + [(east - (east - west) * i / 40, north) for i in range(41)]
            + [(west, north - (north - south) * i / 40) for i in range(41)]
        )
        return Polygon([self.to_local(x, y) for x, y in ring])

    def east_of(self, lon: float) -> Polygon:
        return self.wgs_box(lon, self.lat - 2, lon + 3, self.lat + 2)

    def west_of(self, lon: float) -> Polygon:
        return self.wgs_box(lon - 3, self.lat - 2, lon, self.lat + 2)

    def north_of(self, lat: float) -> Polygon:
        return self.wgs_box(self.lon - 3, lat, self.lon + 3, lat + 2)

    def south_of(self, lat: float) -> Polygon:
        return self.wgs_box(self.lon - 3, lat - 2, self.lon + 3, lat)

    def side(self, line, toward: Point, reach_km: float = 200) -> Polygon:
        """The side of a line (extended at both ends) that `toward` lies on."""
        coords = list(line.coords) if isinstance(line, LineString) else list(shapely.line_merge(line).geoms[0].coords)
        (x0, y0), (x1, y1) = coords[0], coords[1]
        (xa, ya), (xb, yb) = coords[-2], coords[-1]
        d = reach_km * 1000

        def ext(x, y, px, py):
            L = math.hypot(x - px, y - py) or 1
            return x + (x - px) / L * d, y + (y - py) / L * d

        long = LineString([ext(x0, y0, x1, y1), *coords, ext(xb, yb, xa, ya)])
        left = long.buffer(d, single_sided=True)
        right = long.buffer(-d, single_sided=True)
        return left if left.distance(toward) <= right.distance(toward) else right


# ---------------------------------------------------------------------------------------------------------------
# Tidying a cut: the circle stays the upper bound; slivers under two cells wide and holes under a quarter of a
# square kilometre go; parts under 5% of the largest go unless every part is kept.


def holes_filled(g, min_area: float):
    def fill(p: Polygon) -> Polygon:
        return Polygon(p.exterior, [i for i in p.interiors if Polygon(i).area >= min_area])

    parts = getattr(g, "geoms", [g])
    return unary_union([fill(p) for p in parts if isinstance(p, Polygon) and not p.is_empty])


def tidy(geom, F: Frame, keep: str):
    c = F.cell
    g = geom.intersection(F.bound)
    if g.is_empty:
        return g
    g = g.buffer(c).buffer(-2 * c).buffer(c)
    g = holes_filled(g, max(250_000, 0.03 * g.area)).intersection(F.bound)
    parts = [p for p in getattr(g, "geoms", [g]) if isinstance(p, Polygon) and not p.is_empty]
    if not parts:
        return Polygon()
    if keep == "pin":
        parts = [min(parts, key=lambda p: p.distance(F.pin))]
    else:
        biggest = max(p.area for p in parts)
        parts = [p for p in parts if p.area >= 0.05 * biggest]
    g = shapely.make_valid(unary_union(parts).simplify(c / 2).intersection(F.bound))
    # make_valid can return a collection with a stray line or point where two parts touch; keep the area only.
    return unary_union([p for p in getattr(g, "geoms", [g]) if isinstance(p, (Polygon, MultiPolygon))])


def to_geojson(g, F: Frame) -> dict:
    g = (
        shapely.geometry.polygon.orient(g, 1.0)
        if isinstance(g, Polygon)
        else MultiPolygon([shapely.geometry.polygon.orient(p, 1.0) for p in g.geoms])
    )
    geo = mapping(shapely.transform(g, lambda xy: np.column_stack(F.to_wgs(xy[:, 0], xy[:, 1]))))
    rnd = lambda ring: [[round(x, 5), round(y, 5)] for x, y in ring]  # noqa: E731
    if geo["type"] == "Polygon":
        geo["coordinates"] = [rnd(r) for r in geo["coordinates"]]
    else:
        geo["coordinates"] = [[rnd(r) for r in poly] for poly in geo["coordinates"]]
    return geo


def km2(geo: dict) -> float:
    g = shape(geo)
    return sum(abs(GEOD.geometry_area_perimeter(p)[0]) for p in getattr(g, "geoms", [g])) / 1e6


# ---------------------------------------------------------------------------------------------------------------
# The rules, one per area. Each returns the ground the evidence allows, in the frame's metres; the circle stays the
# upper bound. `keep` is "pin" when only the part nearest the stop counts, "all" otherwise.


@dataclass
class Rule:
    confidence: str
    rule: str
    cut: Callable[[Frame], object] | None = None
    keep: str = "all"


RULES: dict[str, Rule] = {}
# The areas whose rule stands a straight line between the book's places in for an old Mexican road or trail that
# no open source maps. The cards say so, and that a historical road map would improve them.
STRAIGHT_ROADS = {
    "j4-escarpment-rim",
    "j4-the-girl",
    "j4-opera-camp",
    "j4-river-camps",
    "j4-wagon-road-crossing",
    "j4-steer-herd",
    "j4-horses-found",
    "j4-manco-roadblock",
    "j7-lake-camp",
}


def lake(F: Frame):
    """The Babícora lake: INEGI's water body nearest the GeoNames point (29.35 N, 107.83 W), else Natural Earth's."""
    g = F.water(F.ll(-107.83, 29.35), max_km=8)
    return g if not g.is_empty and g.area > 5e6 else F.ne_lake("Laguna Babícora")


BORDER_31_20 = ((-111.07, 31 + 20 / 60), (-108.2083, 31 + 20 / 60))  # the line along 31°20′ N
BORDER_31_47 = ((-108.2083, 31 + 47 / 60), (-106.53, 31 + 47 / 60))  # the line along 31°47′ N
CLOVERDALE_ROADS = (
    "name IN ('Cloverdale Rd', 'Cloverdale Rd C001', 'Co Rd C001', 'Cloverdale Rd/c001', 'Geronimo Trl', "
    "'State Hwy 338')"
)
CREEK_ROAD = "name IN ('Cloverdale Rd C001', 'Co Rd C001', 'Co Rd C106')"
SK_BAR = Rule(
    "medium",
    "The ranch house is on the road: within 2.5 km of the road north from Cloverdale (today's State "
    "Highway 338 and Cloverdale Road, Census TIGER). The book gives nine miles by road from the Parham house, "
    "so the circle still fixes where along the road.",
    lambda F: F.roads(CLOVERDALE_ROADS).buffer(2500),
)
TRUCK = Rule(
    "kept",
    "Kept the circle. The truck meets them on a dirt road in open country; no road of the period is "
    "mapped here and most of the circle is open country, so nothing narrows it.",
)
LORDSBURG = Rule(
    "medium",
    "The east side of Lordsburg: the town's streets (within 250 m of Census TIGER local streets) "
    "east of the town's centre point. Today's town is larger than the town of the 1940s.",
    lambda F: F.roads("class = 'S1400'").buffer(250).intersection(F.east_of(PLACES["lordsburg"][0])),
)
SANTA_MARIA = "Santa María"

RULES.update(
    {
        "j1-bavispe-crossing": Rule(
            "medium",
            "On the river: the Bavispe's channel (the highest-order INEGI stream in the circle, its main "
            "stem) and 1.5 km either side. She crosses the river, so the crossing is on it; where along this "
            "reach is still open, so the whole reach in the circle stays.",
            lambda F: F.main_stream().buffer(1500),
        ),
        "j1-clanton-foster": Rule(
            "medium",
            "The ground between the two draws: the strip between lines through the GNIS points of Clanton "
            "Draw and Foster Draw that run down the general slope of the circle (the way the draws run), with 400 m "
            "beyond each. NHD does not name the draws' channels here.",
            lambda F: F.between(F.place("clanton-draw"), F.place("foster-draw"), 400),
        ),
        "j2-robertson-crossfence": Rule(
            "medium",
            "On the creek road he leads the wolf down (1-08): within 500 m of the Cloverdale Creek road "
            "(Census TIGER 2023, Cloverdale Rd C001, Co Rd C001 and Co Rd C106). The circle says where along the road.",
            lambda F: F.roads(CREEK_ROAD).buffer(500),
        ),
        "j1-cloverdale-creek": Rule(
            "kept",
            "Kept the circle. The trap was off the creek road, across a pasture, about two hours' ride from "
            "Cloverdale; the circle already covers the road's upper reach and the pastures either side.",
        ),
        "j2-cloverdale-creek": Rule(
            "kept", "Kept the circle: the same trap site as the wolf's last stop (J1, stop 13)."
        ),
        "j2-volcanic-plain-ranch": Rule(
            "medium",
            "The plain: ground with a slope under 3 degrees (smoothed 30 m DEM) north of the boundary at "
            "31°20′ N, the part joined to the stop. The ranch is on the broad volcanic plain before the boundary.",
            lambda F: F.flat(3, 3).intersection(F.north_of(31 + 20 / 60)),
            "pin",
        ),
        "j2-boundary-monument": Rule(
            "high",
            "Within 3 km of the boundary along 31°20′ N, where the monuments stand: they are at the line with "
            "a monument in sight.",
            lambda F: F.line(*BORDER_31_20).buffer(3000),
        ),
        "j2-mud-settlement": Rule(
            "medium",
            "The Bavispe's valley floor: ground within 4 km of the river and no more than 60 m above it. They "
            "ride down the river path, across a meadow to a road and south along it to the settlement (1-09).",
            lambda F: F.valley_floor(F.main_stream(), 60, 4),
        ),
        "j2-hacienda": Rule(
            "medium",
            "Flat ground beside the Batepito: within 2 km of the river (INEGI streams along Natural Earth's "
            "Río Batepito), no more than 30 m above it, with a slope under 5 degrees. The book has the road on the "
            "other bank, but not which bank that is.",
            lambda F: F.valley_floor(F.river("Rio Batepito"), 30, 2).intersection(F.flat(5)),
        ),
        "j3-bavispe-promontory": Rule(
            "medium",
            "A promontory over the north-running Bavispe on the sierra's side: ground west of the river (its "
            "main stem in INEGI), at least 150 m above it and within 8 km of it.",
            lambda F: F.above_river(F.main_stream(), 150, 8).intersection(F.beside(F.main_stream(), "west", 0, 8)),
        ),
        "j3-indian-rancherias": Rule(
            "low",
            "The high country: ground above 1,500 m west of the upper Bavispe (west of the line Bacerac to "
            "Bavispe, extended). The book names no range, so this only drops the valleys.",
            lambda F: F.above(1500).intersection(F.side(F.line("bacerac", "bavispe"), Point(-1e5, 0))),
        ),
        "j3-eastern-escarpment": Rule(
            "low",
            "The escarpment's edge: ground that looks down at least 300 m within 6 km to the east, on the west "
            "side of the upper Bavispe (its main stem in INEGI) and within 8 km of it. He looks east over the barranca "
            "and then goes down to the river.",
            lambda F: F.drop_toward(90, 6, 300).intersection(F.beside(F.main_stream(), "west", 0, 8)),
        ),
        "j3-huisiachepic": Rule(
            "medium",
            "The river town: ground within 1.5 km of the upper Bavispe (the circle's main stem in INEGI) and no "
            "more than 150 m above it, so benches above the canyon floor stay. The town is across a ford on the river; "
            "which bank is not known.",
            lambda F: F.valley_floor(F.main_stream(), 150, 1.5),
        ),
        "j3-guadalupe-pass": Rule(
            "medium",
            "On the road over the range: within 1.5 km of the Douglas to Cloverdale roads (Geronimo Trail and "
            "Cloverdale Road in Census TIGER).",
            lambda F: F.roads(CLOVERDALE_ROADS).buffer(1500),
        ),
        "j3-sk-bar": SK_BAR,
        "j3-websters": LORDSBURG,
        "j4-lordsburg": LORDSBURG,
        "j4-alkali-flats": Rule(
            "medium",
            "The alkali flats: the flat ground (slope under 1.5 degrees) joined to the stop, which drops the "
            "hills in the south-west. The DEM cannot tell alkali from grass, so the whole flat stays.",
            lambda F: F.flat(1.5),
            "pin",
        ),
        "j4-san-simon": Rule(
            "high",
            "At the river: within 1 km of the San Simon River (NHD flowline). Where along the river is the "
            "circle's estimate.",
            lambda F: F.nhd("San Simon River").buffer(1000),
        ),
        "j4-bowie": Rule(
            "medium",
            "At the highway crossing, east of Bowie: within 1 km of the highway (Census TIGER primary and "
            "secondary roads) and east of the town's centre point.",
            lambda F: F.roads("class IN ('S1100', 'S1200')").buffer(1000).intersection(F.east_of(PLACES["bowie"][0])),
        ),
        "j4-escarpment-rim": Rule(
            "low",
            "The eastern rim: ground that looks down at least 300 m within 10 km to the east, within 8 km of the "
            "line from Bacerac to Colonia Juárez.",
            lambda F: F.drop_toward(90, 10, 300).intersection(F.line("bacerac", "colonia-juarez").buffer(8000)),
        ),
        "j4-plains-camp": Rule(
            "kept",
            "Kept the circle. The book has prairie below the rim; the DEM finds no plain in the circle, only "
            "small flats along the streams, so the circle may sit too far west of the open ground toward Colonia "
            "Juárez. Worth a look by hand.",
        ),
        "j4-the-girl": Rule(
            "medium",
            "East of the road: east of the straight line from Casas Grandes to the Hacienda de San Diego (no "
            "map of the old road is to hand) and within 3 km of it, where a fire can be seen from the road.",
            lambda F: F.side(F.line("casas-grandes", "hacienda-de-san-diego"), Point(1e5, 0)).intersection(
                F.line("casas-grandes", "hacienda-de-san-diego").buffer(3000)
            ),
        ),
        "j4-opera-camp": Rule(
            "medium",
            "A roadside field on the Madera road: within 2 km of the line from Las Varas to Madera (the road "
            "is not mapped here) on ground flatter than 4 degrees.",
            lambda F: F.line("las-varas", "madera").buffer(2000).intersection(F.flat(4)),
        ),
        "j4-river-camps": Rule(
            "low",
            "By a river near the road: within 1 km of INEGI streams of order 4 and up, and within 4 km of the "
            "line from Las Varas to Madera. The book names neither the river nor the road.",
            lambda F: F.streams(4).buffer(1000).intersection(F.line("las-varas", "madera").buffer(4000)),
        ),
        "j4-wagon-road-crossing": Rule(
            "low",
            "On the wagon road: within 8 km of the line La Norteña, La Babícora, Namiquipa, the road's ends and "
            "middle as the book gives them. The book's compass does not close here, so the band is wide.",
            lambda F: F.line("la-nortena", "la-babicora", "namiquipa").buffer(8000),
        ),
        "j4-steer-herd": Rule(
            "medium",
            "On the road east to Boquilla: within 3 km of the line from Las Varas to La Boquilla.",
            lambda F: F.line("las-varas", "boquilla").buffer(3000),
        ),
        "j4-horses-found": Rule(
            "medium",
            "On the road, with the lake to the south: within 2.5 km of the line from Las Varas to La "
            "Boquilla, north of the lake and not in it.",
            lambda F: F.line("las-varas", "boquilla").buffer(2500).difference(lake(F).buffer(300)),
        ),
        "j4-manco-roadblock": Rule(
            "medium",
            "On the road west of La Boquilla, east of the lake: within 2.5 km of the line from Las Varas to La "
            "Boquilla, west of the town and out of the lake.",
            lambda F: (
                F.line("las-varas", "boquilla")
                .buffer(2500)
                .intersection(F.west_of(PLACES["boquilla"][0]))
                .difference(lake(F).buffer(300))
            ),
        ),
        "j4-tracking-north": Rule(
            "kept",
            "Kept the circle. They follow the tracks north from the road all afternoon and camp in a swale; the "
            "circle already lies north of the road and the lake, and a swale cannot be told from the DEM.",
        ),
        "j4-quijada-remuda": Rule(
            "kept",
            "Kept the circle. The book gives an east-west road, a crossroads and a track down from the mountains, "
            "but no distance or landmark to cut by.",
        ),
        "j4-leave-road": Rule(
            "medium",
            "Between the road north of Boquilla and the river to its west: west of La Boquilla and north of the "
            "lake. They leave the road a mile above the town and ride west to a river (3-08).",
            lambda F: (
                F.west_of(PLACES["boquilla"][0] + 0.01)
                .difference(lake(F).buffer(300))
                .intersection(F.north_of(PLACES["boquilla"][1] - 0.01))
            ),
        ),
        "j4-dry-camp": Rule(
            "kept",
            "Kept the circle. The camp is on a rise a mile west of the river after a night's ride (3-08), but "
            "which of the circle's streams is that river is not known: cutting to the side of the largest one (in the "
            "circle's north-east corner) left a sliver, which the night's ride does not support.",
        ),
        "j4-shooting": Rule(
            "high",
            "By the river: within 800 m of the stream nearest San José (INEGI, order 4 and up). The camp is in "
            "a cottonwood grove by the river and Boyd is shot from the far bank.",
            lambda F: F.stem(F.place("san-jose"), 4).buffer(800),
        ),
        "j4-truck": TRUCK,
        "j4-blind-man": Rule(
            "kept", "Kept the circle. An arroyo, a light to the north, a fence and a clay track: nothing to cut by."
        ),
        "j4-crossroads": Rule(
            "low",
            "Near the river breaks: within 4 km of the main river (INEGI streams of order 7). He meets the main "
            "road north at a crossroads and sleeps in a field near the river breaks.",
            lambda F: F.streams(7).buffer(4000),
        ),
        "j5-las-varas-night": Rule(
            "medium",
            "Within earshot of the crossing: within 15 km of Las Varas, a generous reach for a train whistle at night.",
            lambda F: F.place("las-varas").buffer(15000),
        ),
        "j5-santa-maria-stream": Rule(
            "medium",
            "Beside a stream: within 1 km of INEGI streams of order 3 and up (the Santa María headwaters on "
            "this valley floor).",
            lambda F: F.streams(3).buffer(1000),
        ),
        "j5-lake-camp": Rule(
            "medium",
            "The lake's edge: from 500 m inside INEGI's outline of the Babícora lake to 2 km outside it. The "
            "shore moves with the water level.",
            lambda F: lake(F).buffer(2000).difference(lake(F).buffer(-500)),
        ),
        "j5-river-camp": Rule(
            "medium",
            "On the river: within 600 m of the main river by Mata Ortiz (the INEGI stream nearest the stop, "
            "order 5 and up). A gravel bar by the river; 'below Mata Ortiz' could also mean downstream (north).",
            lambda F: F.stem(F.pin, 5).buffer(600),
        ),
        "j5-alamo": Rule(
            "kept", "Kept the circle. Which Álamo is meant is unresolved; the circle covers both candidates."
        ),
        "j6-truck": TRUCK,
        "j7-salt-lake": Rule(
            "high",
            "The lake bed and its flats: ground within 8 m of the lowest ground in the circle (Playas Lake's "
            "floor). He rides south along the flats and camps by a fence.",
            lambda F: F.low_ground(8),
        ),
        "j7-playas-road": Rule(
            "low",
            "In the mountains on a road: ground above 1,450 m within 2 km of Census TIGER roads. The old Playas "
            "road crosses the range with snow in the pass; which road is not known.",
            lambda F: F.above(1450).intersection(F.roads("class IN ('S1100', 'S1200', 'S1400')").buffer(2000)),
        ),
        "j7-sanders": SK_BAR,
        "j7-animas-plain": Rule(
            "high",
            "The open plain: the Animas Valley floor below 1,650 m with a slope under 2 degrees, the part joined "
            "to the stop.",
            lambda F: F.below(1650).intersection(F.flat(2, 3)),
            "pin",
        ),
        "j7-sk-bar": SK_BAR,
        "j7-lake-camp": Rule(
            "medium",
            "On the plain by the road: ground flatter than 2 degrees within 4 km of the line from Las Varas to "
            "La Boquilla, out of the lake.",
            lambda F: (
                F.flat(2, 3).intersection(F.line("las-varas", "boquilla").buffer(4000)).difference(lake(F).buffer(300))
            ),
        ),
        "j7-babicora-high-country": Rule(
            "medium",
            "The plains around the lake: ground below 2,250 m with a slope under 4 degrees (the Babícora "
            "basin floor and its swales), lake included.",
            lambda F: F.below(2250).intersection(F.flat(4, 3)).union(lake(F)),
        ),
        "j7-quijada-cabin": Rule(
            "low",
            "On the plain: ground with a slope under 3 degrees. The cabin is a lone house on the plain on a road "
            "toward a gap in the mountains.",
            lambda F: F.flat(3, 3),
        ),
        "j7-boyds-grave": Rule(
            "kept",
            "Kept the circle. It is already small (3 km²); a bench in low hills is below what the 30 m DEM can "
            "find reliably.",
        ),
        "j7-past-casas-grandes": Rule(
            "medium",
            "Where the town's lights show: ground in sight of a light 10 m up at Nuevo Casas Grandes (viewshed "
            "of the 30 m DEM, eye at 2 m) and east of the town.",
            lambda F: F.viewshed(F.place("nuevo-casas-grandes"), 10, 2, 40).intersection(
                F.east_of(PLACES["casas-grandes"][0])
            ),
        ),
        "j7-casas-grandes-river": Rule(
            "high",
            "At the river: within 1 km of the Casas Grandes River (the INEGI stream nearest Corralitos, order 6). "
            "He reaches the river and follows a trail north beside it.",
            lambda F: F.stem(F.place("corralitos"), 6).buffer(1000),
        ),
        "j7-attack": Rule(
            "high",
            "On the river trail: within 1 km of the Casas Grandes River (INEGI, order 6).",
            lambda F: F.stem(F.place("corralitos"), 6).buffer(1000),
        ),
        "j7-dog-springs": Rule(
            "high",
            "At the boundary: within 1.5 km of the line along 31°47′ N. He passes an obelisk on the line; where "
            "along it is the circle's estimate.",
            lambda F: F.line(*BORDER_31_47).buffer(1500),
        ),
        "j7-cemetery": Rule(
            "medium",
            "South of the town: the circle south of Animas's centre point.",
            lambda F: F.south_of(PLACES["animas"][1]),
        ),
        "j7-black-range": Rule(
            "high",
            "On the road over the pass: within 1 km of NM 152 (Census TIGER), the old road east over Emory Pass.",
            lambda F: F.roads("name = 'State Hwy 152'").buffer(1000),
        ),
        "j7-waystation": Rule(
            "medium",
            "By the blacktop: within 500 m of the highways in the circle (Census TIGER secondary roads, NM 152 "
            "and NM 27). The waystation's adobes stand by the highway.",
            lambda F: F.roads("class IN ('S1100', 'S1200')").buffer(500),
        ),
    }
)


# ---------------------------------------------------------------------------------------------------------------
# Output

COLOURS = {"high": "#1a9850", "medium": "#f39c12", "low": "#d73027", "kept": "#7f7f7f"}


def hillshade(dem: np.ndarray, cell: float, azimuth: float = 315, altitude: float = 45) -> np.ndarray:
    z = np.nan_to_num(dem, nan=float(np.nanmean(dem)))
    gy, gx = np.gradient(z, cell)
    slope = np.arctan(np.hypot(gx, gy) * 1.5)
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(azimuth), math.radians(altitude)
    return np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)


def draw(ax, F: Frame, draft, confidence: str, context: bool = False) -> None:
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def patch(g, **kw):
        for p in getattr(g, "geoms", [g]):
            if p.is_empty:
                continue
            verts, codes = [], []
            for ring in (p.exterior, *p.interiors):
                xy = np.asarray(ring.coords) / 1000
                verts += list(xy)
                codes += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MPath(verts, codes), **kw))

    def lines(g, **kw):
        for part in getattr(g, "geoms", [g]):
            if not part.is_empty and part.geom_type == "LineString":
                xy = np.asarray(part.coords) / 1000
                ax.plot(xy[:, 0], xy[:, 1], **kw)

    h = F.half / 1000
    ax.imshow(
        hillshade(F.dem, F.cell), cmap="gray", vmin=-0.2, vmax=1.15, extent=(-h, h, -h, h), interpolation="bilinear"
    )
    view = F.bound.buffer(F.r * 0.12 if not context else F.r * 0.5)
    clip = view
    lines(F.streams(4 if F.r > 6000 else 3).intersection(clip), color="#2b6cb0", lw=0.6 if not context else 0.9)
    if context:
        lines(
            F.roads("class IN ('S1100', 'S1200', 'S1400', 'Major Highway', 'Secondary Highway')").intersection(clip),
            color="#8a5a2b",
            lw=0.6,
        )
    colour = COLOURS[confidence]
    patch(draft, facecolor=colour, alpha=0.35, edgecolor="none")
    patch(draft, facecolor="none", edgecolor=colour, lw=1.2)
    patch(F.bound, facecolor="none", edgecolor="white", lw=1.4, ls=(0, (4, 2)))
    patch(F.bound, facecolor="none", edgecolor="black", lw=0.5, ls=(0, (4, 2)))
    ax.plot([0], [0], "o", ms=3, color="black", mec="white", mew=0.6)
    for pid, (lon, lat) in PLACES.items():
        pt = F.ll(lon, lat)
        if clip.contains(pt):
            ax.plot([pt.x / 1000], [pt.y / 1000], "s", ms=2.5, color="#333", mec="white", mew=0.4)
            if context:
                ax.annotate(
                    pid.replace("-", " "),
                    (pt.x / 1000, pt.y / 1000),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=6.5,
                    color="#111",
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7),
                )
    x0, y0, x1, y1 = view.bounds
    ax.set_xlim(x0 / 1000, x1 / 1000)
    ax.set_ylim(y0 / 1000, y1 / 1000)
    ax.set_xticks([])
    ax.set_yticks([])


def panel(F: Frame, draft, rec: dict, path: Path, context: bool = False) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import textwrap

    import matplotlib.pyplot as plt

    size = (7.5, 8.6) if context else (2.6, 2.95)
    fig, ax = plt.subplots(figsize=size, dpi=110 if context else 100)
    draw(ax, F, draft, rec["confidence"], context)
    ax.set_title(
        f"{rec['id']}\n{rec['old_km2']:.0f} → {rec['new_km2']:.0f} km² ({rec['share']:.0%}), {rec['confidence']}",
        fontsize=10 if context else 7.2,
        loc="left",
    )
    if context:
        ax.text(0, -0.02, "\n".join(textwrap.wrap(rec["rule"], 115)), transform=ax.transAxes, va="top", fontsize=7.5)
        r = F.r / 1000
        ax.plot([-r, -r + 1 if r < 4 else -r + 5], [-r * 1.4, -r * 1.4], color="black", lw=2)
        ax.text(-r, -r * 1.37, "1 km" if r < 4 else "5 km", fontsize=7)
    fig.tight_layout(pad=0.3)
    fig.savefig(path)
    plt.close(fig)


def contact_sheets(paths: list[Path], stem: str, per_sheet: int = 20, cols: int = 5) -> list[Path]:
    from PIL import Image

    out = []
    for k in range(0, len(paths), per_sheet):
        tiles = [Image.open(p).convert("RGB") for p in paths[k : k + per_sheet]]
        w, h = tiles[0].size
        rows_n = math.ceil(len(tiles) / cols)
        sheet = Image.new("RGB", (cols * w, rows_n * h), "white")
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * w, (i // cols) * h))
        path = REPORT / f"{stem}-{k // per_sheet + 1}.png"
        # A 256-colour palette keeps each sheet under about 1 MB.
        sheet.quantize(256, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)
        out.append(path)
    return out


def build(only: list[str] | None, images: bool, force: bool) -> None:
    if SEED.exists() and not force and not only:
        raise SystemExit(
            f"{SEED.relative_to(REPO)} exists and may hold hand edits; rerun with --force to rewrite it "
            "(areas marked draft_confidence 'checked' are kept)"
        )
    prepare()
    (WORK / "panels").mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    checked = {}
    if SEED.exists():
        checked = {
            f["properties"]["id"]: f
            for f in json.loads(SEED.read_text(encoding="utf-8"))["features"]
            if f["properties"].get("draft_confidence") == "checked"
        }
    features, records, panels = [], [], []
    for s in stops():
        if only and s["id"] not in only:
            continue
        if f"area-{s['id']}" in checked:
            features.append(checked[f"area-{s['id']}"])
            print(f"{s['id']:28} checked by hand, kept")
            continue
        F, rule = frame(s), RULES[s["id"]]
        circle = to_geojson(F.bound, F)
        old_km2 = km2(circle)
        if rule.cut is None:
            draft, geometry = F.bound, circle
        else:
            draft = tidy(rule.cut(F), F, rule.keep)
            if draft.is_empty or draft.area < 0.01 * F.bound.area:
                F.notes.append("the cut left nothing; kept the circle")
                draft, geometry = F.bound, circle
            else:
                geometry = to_geojson(draft, F)
        # An uncut circle is "kept" whatever the rule hoped for, so build_story shows it as a circle.
        confidence = rule.confidence if geometry is not circle else "kept"
        new_km2 = km2(geometry)
        if rule.cut is not None and new_km2 > 0.95 * old_km2:
            F.notes.append("the cut removed under 5% of the circle")
        rec = dict(
            id=s["id"],
            name=s["name"],
            confidence=confidence,
            old_km2=round(old_km2, 1),
            new_km2=round(new_km2, 1),
            share=round(new_km2 / old_km2, 3),
            pin_inside=draft.buffer(1).contains(F.pin),
            pin_km=round(draft.distance(F.pin) / 1000, 1),
            rule=rule.rule,
            notes="; ".join(F.notes),
        )
        records.append(rec)
        props = {
            "id": f"area-{s['id']}",
            "stop": s["id"],
            "draft_rule": rule.rule,
            "draft_confidence": confidence,
            "straight_road": s["id"] in STRAIGHT_ROADS,
        }
        features.append({"type": "Feature", "geometry": geometry, "properties": props})
        outside = "" if rec["pin_inside"] else f"  pin {rec['pin_km']} km outside"
        print(
            f"{s['id']:28} {confidence:6} {old_km2:8.1f} -> {new_km2:8.1f} km2 ({new_km2 / old_km2:4.0%}){outside}  "
            f"{rec['notes']}",
            flush=True,
        )
        if images:
            path = WORK / "panels" / f"{s['id']}.png"
            panel(F, draft, rec, path)
            panels.append(path)
            panel(F, draft, rec, WORK / f"large-{s['id']}.png", context=True)
    if only:
        return
    SEED.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    if not records:  # every area was checked by hand: nothing drafted, nothing to report
        print(f"Wrote {SEED.relative_to(REPO)}: {len(features)} areas, all checked by hand")
        return
    with (REPORT / "areas-draft.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)
    total_old, total_new = sum(r["old_km2"] for r in records), sum(r["new_km2"] for r in records)
    print(
        f"Wrote {SEED.relative_to(REPO)}: {len(features)} areas ({len(checked)} checked by hand); "
        f"drafted {total_old:,.0f} -> {total_new:,.0f} km2. Report in {REPORT.relative_to(REPO)}/"
    )
    if images:
        for p in contact_sheets(panels, "contact-sheet"):
            print(f"Wrote {p.relative_to(REPO)}")


# ---------------------------------------------------------------------------------------------------------------
# La Babícora: plan section 2.4 says to draw the region from the four municipios the estate spread across. This
# builds that polygon from geoBoundaries (MEX ADM2, CC BY 4.0, from the World Bank's 2012 municipios) and sets it
# beside the DEM draft that crossing.regions made.


def babicora(images: bool) -> None:
    out = subprocess.run(
        ["ogr2ogr", "-f", "GeoJSON", "-spat", "-109.5", "27.5", "-106", "30.5", "/vsistdout/", str(GEOBOUNDARIES)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    munis = {
        f["properties"]["shapeName"]: shape(f["geometry"])
        for f in json.loads(out)["features"]
        if f["properties"]["shapeName"] in BABICORA_MUNICIPIOS
    }
    assert sorted(munis) == sorted(BABICORA_MUNICIPIOS), sorted(munis)
    dem_draft = next(
        shape(f["geometry"])
        for f in json.loads((SEEDS / "regions.geojson").read_text(encoding="utf-8"))["features"]
        if f["properties"]["id"] == "region-la-babicora"
    )
    union = unary_union(list(munis.values())).buffer(0)
    # Simplify to about 100 m: the source has a vertex every few metres.
    union_s = union.simplify(0.001)
    hacienda = Point(PLACES["la-babicora"])
    lake_pt = Point(-107.83, 29.35)
    inter = dem_draft.intersection(union)

    def km2_of(g) -> float:
        return sum(abs(GEOD.geometry_area_perimeter(p)[0]) for p in getattr(g, "geoms", [g])) / 1e6

    def rounded(g) -> dict:
        geo = mapping(shapely.set_precision(g, 1e-5))
        return geo

    stats = {
        "municipios_km2": round(km2_of(union)),
        **{f"{n}_km2": round(km2_of(g)) for n, g in munis.items()},
        "dem_draft_km2": round(km2_of(dem_draft)),
        "dem_draft_inside_municipios_km2": round(km2_of(inter)),
        "dem_draft_outside_municipios_km2": round(km2_of(dem_draft.difference(union))),
        "estate_km2_reported": 3600,
        "hacienda_in_municipios": union.contains(hacienda),
        "hacienda_in_dem_draft": dem_draft.contains(hacienda),
        "lake_in_municipios": union.contains(lake_pt),
    }
    stops_in = {}
    for f in json.loads((REPO / "data" / "stops.geojson").read_text(encoding="utf-8"))["features"]:
        pt = shape(f["geometry"])
        if union.contains(pt) or dem_draft.contains(pt):
            stops_in[f["properties"]["id"]] = (union.contains(pt), dem_draft.contains(pt))
    stats["stops_in_municipios"] = sum(a for a, _ in stops_in.values())
    stats["stops_in_dem_draft"] = sum(b for _, b in stops_in.values())
    stats["stops_only_in_municipios"] = sorted(k for k, (a, b) in stops_in.items() if a and not b)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    licence = (
        "Municipio boundaries: geoBoundaries gbOpen MEX ADM2 (boundary MEX-ADM2-50627088, municipios of 2012, "
        "source World Bank), CC BY 4.0. Runfola et al. 2020, geoBoundaries, PLoS ONE 15(4): e0231866."
    )
    reasoning = (
        "The Babícora estate, Hearst's ranch, lay across the municipios of Temósachic, Namiquipa, Madera and "
        "Gómez Farías (plan section 2.4). This outline is those four municipios joined, from today's boundaries; "
        "the estate itself was about a fifth of this area and its legal bounds are not known to this project."
    )
    features = [
        {
            "type": "Feature",
            "geometry": rounded(g),
            "properties": {
                "id": f"municipio-{n}",
                "kind": "municipio",
                "name": n,
                "km2": stats[f"{n}_km2"],
                "source": licence,
            },
        }
        for n, g in munis.items()
    ]
    features += [
        {
            "type": "Feature",
            "geometry": rounded(union_s),
            "properties": {
                "id": "region-la-babicora-municipios",
                "kind": "region-alternative",
                "name": "La Babícora (Hearst)",
                "km2": stats["municipios_km2"],
                "reasoning": reasoning,
                "source": licence,
            },
        },
        {
            "type": "Feature",
            "geometry": rounded(dem_draft),
            "properties": {
                "id": "region-la-babicora",
                "kind": "region-current",
                "name": "La Babícora",
                "km2": stats["dem_draft_km2"],
                "reasoning": "The DEM draft in pipeline/seeds/regions.geojson (crossing.regions): "
                "basin floor below 2,200 m "
                "joined to the hacienda's pin.",
            },
        },
    ]
    (QGIS / "babicora-compare.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (REPORT / "babicora-compare.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    if images:
        babicora_image(munis, union_s, dem_draft)


def babicora_image(munis: dict, union, dem_draft) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    w, so, e, no = union.bounds
    lon, lat = (w + e) / 2, (so + no) / 2
    reach = max(GEOD.inv(lon, lat, x, y)[2] for x in (w, e) for y in (so, no)) / 1000 / math.sqrt(2)
    F = Frame("babicora", lon, lat, reach * 1.08, pad=1.0)
    F.cell = 400
    n = math.ceil(2 * F.half / F.cell)
    F.half = n * F.cell / 2
    F.shape, F.transform = (n, n), from_origin(-F.half, F.half, F.cell, F.cell)
    fwd = lambda g: shapely.transform(g, lambda xy: np.column_stack(F.to_local(xy[:, 0], xy[:, 1])))  # noqa: E731
    fig, ax = plt.subplots(figsize=(8, 8.6), dpi=110)
    h = F.half / 1000
    ax.imshow(hillshade(F.dem, F.cell), cmap="gray", vmin=-0.2, vmax=1.15, extent=(-h, h, -h, h))

    def outline(g, **kw):
        for p in getattr(g, "geoms", [g]):
            xy = np.asarray(p.exterior.coords) / 1000
            ax.plot(xy[:, 0], xy[:, 1], **kw)

    for name, g in munis.items():
        g = fwd(g)
        outline(g, color="#555", lw=0.7, ls=":")
        c = g.representative_point()
        ax.text(
            c.x / 1000,
            c.y / 1000,
            name,
            fontsize=8,
            ha="center",
            color="#222",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7),
        )
    outline(fwd(union), color="#7b3294", lw=2, label=f"four municipios ({km2(mapping(union)):,.0f} km²)")
    d = fwd(dem_draft)
    for p in getattr(d, "geoms", [d]):
        xy = np.asarray(p.exterior.coords) / 1000
        ax.fill(xy[:, 0], xy[:, 1], color="#1a9850", alpha=0.35, lw=0)
    outline(
        d, color="#1a9850", lw=1.5, label=f"DEM draft, basin floor below 2,200 m ({km2(mapping(dem_draft)):,.0f} km²)"
    )
    for pid in (
        "la-babicora",
        "boquilla",
        "las-varas",
        "madera",
        "namiquipa",
        "temosachic",
        "san-buenaventura",
        "santa-ana-de-babicora",
    ):
        p = F.place(pid)
        ax.plot(p.x / 1000, p.y / 1000, "s", ms=3, color="black")
        ax.annotate(
            pid.replace("-", " "), (p.x / 1000, p.y / 1000), xytext=(3, 3), textcoords="offset points", fontsize=7
        )
    ax.set_xlim(-h, h)
    ax.set_ylim(-h, h)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title(
        "La Babícora: the four municipios (geoBoundaries, CC BY 4.0) and the DEM draft", fontsize=10, loc="left"
    )
    fig.tight_layout(pad=0.3)
    path = REPORT / "babicora-compare.png"
    fig.savefig(path)
    plt.close(fig)
    from PIL import Image

    Image.open(path).convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)
    print(f"Wrote {path.relative_to(REPO)}")


# ---------------------------------------------------------------------------------------------------------------
# Support layers for the QGIS project (crossing/area_drafts_qgis.py builds the project itself).


def qgis_layers() -> None:
    """Streams near the areas (INEGI order 3 and up, NHD named or order 3 and up) as a GeoPackage in private/, and a
    VRT over the cached Copernicus tiles with paths relative to it, for the project's hillshade. Both point into
    private/, so the project shows them only on a machine with those caches."""
    prepare()
    folder = QGIS / "layers"
    folder.mkdir(parents=True, exist_ok=True)
    zone = unary_union(
        [
            Point(*PLACES[s["place"]] if not s["lat"] else (float(s["lon"]), float(s["lat"]))).buffer(
                float(s["radius_km"]) / 100 * 1.5 + 0.1
            )
            for s in stops()
        ]
    )
    zone = zone.simplify(0.01)
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "zone.geojson"
        clip.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature", "properties": {}, "geometry": mapping(zone)}],
                }
            )
        )
        # 11 MB: kept in private/ beside the other extracts rather than in the review folder.
        target = WORK / "streams.gpkg"
        target.unlink(missing_ok=True)
        ogr(
            "-f",
            "GPKG",
            "-nln",
            "streams",
            "-clipsrc",
            str(clip),
            "-simplify",
            "0.00005",
            "-where",
            "(src = 'inegi' AND ord >= 3) OR (src = 'nhd' AND (ord >= 3 OR name IS NOT NULL))",
            str(target),
            str(LAYERS),
            "streams",
        )
    print(f"Wrote {target.relative_to(REPO)} ({target.stat().st_size / 1e6:.1f} MB)")
    # Each stop's circle, the upper bound of its draft, for the project to draw under the drafts.
    circles = [
        {"type": "Feature", "properties": {"stop": s["id"]}, "geometry": to_geojson(frame(s).bound, frame(s))}
        for s in stops()
    ]
    (WORK / "circles.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": circles}) + "\n", encoding="utf-8"
    )
    w, so, e, no = zone.bounds
    tiles = []
    for folder_dem in DEM_FOLDERS:
        for tif in sorted(folder_dem.glob("*.tif")):
            with rasterio.open(tif) as src:
                b = src.bounds
            if b.right > w and b.left < e and b.top > so and b.bottom < no:
                tiles.append(tif)
    vrt = folder / "dem.vrt"
    rel = [str(Path("..", "..", "..", t.relative_to(REPO))) for t in tiles]
    subprocess.run(["gdalbuildvrt", "-q", str(vrt.name), *rel], check=True, cwd=folder)
    print(f"Wrote {vrt.relative_to(REPO)} over {len(tiles)} tiles (paths relative, into private/cache/dem)")


# ---------------------------------------------------------------------------------------------------------------


def stops() -> list[dict]:
    return [s for s in rows(SEEDS / "stops.csv") if s["radius_km"]]


def frame(s: dict) -> Frame:
    if s["lat"]:
        lat, lon = float(s["lat"]), float(s["lon"])
    else:
        lon, lat = PLACES[s["place"]]
    return Frame(s["id"], lon, lat, float(s["radius_km"]))


def inspect() -> None:
    """Print what lies in each circle: height range, flat share, named streams and roads, big INEGI orders."""
    prepare()
    for s in stops():
        F = frame(s)
        inside = F.raster(F.bound) & ~np.isnan(F.dem)
        z = F.dem[inside]
        flat = (F.slope(2)[inside] < 3).mean()
        names = sorted(
            {p["name"] for g, p in F.features("streams", "name IS NOT NULL AND ord >= 2") if g.intersects(F.bound)}
        )
        roads = sorted(
            {
                f"{p['name']} ({p['class']})"
                for g, p in F.features(
                    "roads",
                    "name IS NOT NULL AND class IN "
                    "('S1100','S1200','S1400','S1500','Major Highway','Secondary Highway','Road')",
                )
                if g.intersects(F.bound)
            }
        )
        orders = sorted(
            {p["ord"] for g, p in F.features("streams", "ord >= 4 AND src = 'inegi'") if g.intersects(F.bound)}
        )
        ne = sorted({p["name"] for g, p in F.features("ne_rivers") if g.intersects(F.bound)})
        print(
            f"## {s['id']} r={s['radius_km']} z {np.nanpercentile(z, 2):.0f}-{np.nanpercentile(z, 50):.0f}-"
            f"{np.nanpercentile(z, 98):.0f} m, flat<3deg {flat:.0%}"
        )
        print(f"   NE rivers {ne}; INEGI orders>=4 {orders}")
        print(f"   NHD names {names[:12]}")
        print(f"   roads {roads[:14]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--only", nargs="*", help="draft these stops and print them, without writing the seed")
    ap.add_argument("--force", action="store_true", help="rewrite the seed, keeping areas checked by hand")
    ap.add_argument("--qgis", action="store_true", help="only the La Babícora comparison and the QGIS layers")
    a = ap.parse_args()
    if a.inspect:
        inspect()
        return
    if a.qgis:
        QGIS.mkdir(parents=True, exist_ok=True)
        REPORT.mkdir(parents=True, exist_ok=True)
        babicora(a.images)
        qgis_layers()
        return
    build(a.only, a.images, a.force)


if __name__ == "__main__":
    main()
