"""The Raised view's line work (decision 0017): plan oblique relief around the Pilares.

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

Inputs, for two fine hachure tiles (TILES): the smoothed 30 m DEMs and short strokes cached by crossing.hachures,
and INEGI's 1:50,000 river network (private/cache/hydro/inegi/). Writes tiles/out/oblique.pmtiles, zoom 9-12,
one layer `oblique` whose `kind` is stroke (with Slope, Aspect and Rand, as in relief.pmtiles), contour
(200 m form lines), stream (`ord`, Strahler order), journey, crest or ridge (`rel`, relief in metres), and
copies it to site/public/tiles/.
"""

import json
import math
import shutil
import subprocess
import tempfile
import zipfile
import zlib
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from scipy.ndimage import map_coordinates, minimum_filter
from scipy.spatial import cKDTree

from crossing.hachures import COPERNICUS, CRS, OUT, REPO, SCALES

FINE = OUT / SCALES["fine"]["folder"]
TILES = ["620e-3400n", "660e-3400n"]
EXTENT = (620_000, 3_400_000, 700_000, 3_440_000)  # the two tiles, UTM 12N
CELL = 30
STEP = 8  # metres between samples along a line
LEAN = 2  # metres north per metre of height
TRIM = 0.2  # share of each stroke cut from each end
FOLD = 0.5  # smallest north-south stretch at which strokes are kept
FORM_INTERVAL = 200  # metres between form lines
INEGI = REPO / "private" / "cache" / "hydro" / "inegi"
JOURNEYS = REPO / "data" / "journeys.geojson"
ARCHIVE = REPO / "tiles" / "out" / "oblique.pmtiles"
# Shown in the map's attribution while the Raised view is on.
ATTRIBUTION = f"Streams: Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0; {COPERNICUS}"

to_utm = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform
to_wgs = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform


def densify(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dist = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
    s = np.arange(0, dist[-1] + STEP / 2, STEP) if dist[-1] > 0 else np.array([0.0])
    return np.interp(s, dist, xy[:, 0]), np.interp(s, dist, xy[:, 1])


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


def streams(tmp: Path) -> list[tuple[np.ndarray, int]]:
    """INEGI streams of Strahler order 3 and up over the tiles, in UTM, with their order."""
    west, south = to_wgs(EXTENT[0], EXTENT[1])
    east, north = to_wgs(EXTENT[2], EXTENT[3])
    box = [str(v) for v in (west - 0.05, south - 0.05, east + 0.05, north + 0.05)]
    out = []
    for zip_path in sorted(INEGI.glob("*.zip")):
        for i, name in enumerate(n for n in zipfile.ZipFile(zip_path).namelist() if n.endswith("_hl.shp")):
            lines = tmp / f"{zip_path.stem}-{i}.geojson"
            subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-t_srs", CRS, "-spat", *box, "-spat_srs", "EPSG:4326",
                            "-select", "ORDER_1", "-where", "ENTIDAD = 'CORRIENTE DE AGUA' AND ORDER_1 >= 3",
                            str(lines), f"/vsizip/{zip_path}/{name}", Path(name).stem], check=True, capture_output=True)
            for f in json.loads(lines.read_text())["features"]:
                g = f["geometry"]
                for coords in g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]:
                    out.append((np.array(coords)[:, :2], f["properties"]["ORDER_1"]))
    return out


def build() -> list[dict]:
    x0, y0, x1, y1 = EXTENT
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        vrt = tmp / "dem.vrt"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *[str(FINE / f"{t}.tif") for t in TILES]], check=True)
        with rasterio.open(vrt) as src:
            dem, t = src.read(1).astype(float), src.transform
        subprocess.run(["gdal_contour", "-q", "-a", "Ele", "-i", str(FORM_INTERVAL), "-f", "GeoJSON", str(vrt), str(tmp / "f.geojson")],
                       check=True)
        form_lines = [np.array(f["geometry"]["coordinates"]) for f in json.loads((tmp / "f.geojson").read_text())["features"]]
        rivers = streams(tmp)
    gy, gx = np.gradient(dem, t.e, t.a)

    def height(x, y):
        cols, rows = ~t * (np.asarray(x), np.asarray(y))
        return map_coordinates(dem, [rows - 0.5, cols - 0.5], order=1, mode="nearest")

    # The grid runs south to north, so a running maximum along its rows is the horizon each point must clear.
    xs, ys = np.arange(x0, x1, CELL) + CELL / 2, np.arange(y0, y1, CELL) + CELL / 2
    X, Y = np.meshgrid(xs, ys)
    Z = height(X, Y)
    base = float(Z.min())
    shifted = Y + (Z - base) * LEAN
    horizon = np.vstack([np.full(len(xs), -np.inf), np.maximum.accumulate(shifted, axis=0)[:-1]])
    tolerance = CELL / 2
    # How much the shift stretches the ground north to south: 1 on the flat, more on slopes facing the viewer
    # (south), less on slopes facing away, and below 0 where the ground folds out of sight.
    stretch = 1 + LEAN * np.gradient(Z, CELL, axis=0)

    def cell(x, y):
        return (np.clip(np.round((y - ys[0]) / CELL).astype(int), 0, len(ys) - 1),
                np.clip(np.round((x - xs[0]) / CELL).astype(int), 0, len(xs) - 1))

    def project(x, y):
        """Shifted northings for a polyline, and which points are inside the area and not hidden."""
        yp = y + (height(x, y) - base) * LEAN
        inside = (x >= x0) & (x < x1) & (y >= y0) & (y < y1)
        return yp, inside & (yp >= horizon[cell(x, y)] - tolerance)

    def runs(x, yp, shown, kind, props):
        out, start = [], None
        for k, s in enumerate(list(shown) + [False]):
            if s and start is None:
                start = k
            elif not s and start is not None:
                if k - start >= 2:
                    lon, lat = to_wgs(x[start:k], yp[start:k])
                    out.append({"type": "Feature", "properties": {"kind": kind, **props},
                                "geometry": {"type": "LineString",
                                             "coordinates": [(round(a, 5), round(b, 5)) for a, b in zip(lon, lat)]}})
                start = None
        return out

    features = []

    # Short hachure strokes, trimmed, and dropped where the ground is squeezed.
    for tile in TILES:
        for f in json.loads((FINE / f"{tile}-split.geojson").read_text())["features"]:
            xy = np.array([to_utm(*c[:2]) for c in f["geometry"]["coordinates"]])
            x, y = densify(xy)
            mx, my = x[len(x) // 2], y[len(y) // 2]
            if not (x0 <= mx < x1 and y0 <= my < y1):
                continue
            cols, rows = ~t * (mx, my)
            sx, sy = gx[int(rows), int(cols)], gy[int(rows), int(cols)]
            props = {"Slope": round(math.degrees(math.atan(math.hypot(sx, sy)))),
                     "Aspect": round(math.degrees(math.atan2(-sx, -sy))) // 5 * 5 % 360,
                     "Rand": zlib.crc32(json.dumps([round(v, 1) for v in xy[0]]).encode()) % 10}
            k = int(len(x) * TRIM)
            if len(x) - 2 * k >= 2:
                x, y = x[k:len(x) - k], y[k:len(y) - k]
            yp, shown = project(x, y)
            features += runs(x, yp, shown & (stretch[cell(x, y)] >= FOLD), "stroke", props)

    # Form lines, INEGI streams and the journeys.
    for xy in form_lines:
        x, y = densify(xy)
        features += runs(x, *project(x, y), "contour", {})
    for xy, order in rivers:
        x, y = densify(xy)
        features += runs(x, *project(x, y), "stream", {"ord": order})
    for f in json.loads(JOURNEYS.read_text())["features"]:
        x, y = densify(np.array([to_utm(*c[:2]) for c in f["geometry"]["coordinates"]]))
        features += runs(x, *project(x, y), "journey", {})

    # Crests: the edges of the hidden ground, where the shifted surface meets its own horizon.
    margin = np.clip(shifted - horizon, -500, 500).astype("float32")
    margin[0] = 500
    # Northward change in the margin: falling where ground drops out of sight (a crest), rising where it returns.
    falling = np.gradient(margin, axis=0) < 0
    with tempfile.TemporaryDirectory() as folder:
        raster, lines = Path(folder) / "m.tif", Path(folder) / "c.geojson"
        with rasterio.open(raster, "w", driver="GTiff", width=len(xs), height=len(ys), count=1, dtype="float32", crs=CRS,
                           transform=from_origin(x0, y0 + len(ys) * CELL, CELL, CELL)) as dst:
            dst.write(margin[::-1], 1)  # rows north to south, as GeoTIFF expects
        subprocess.run(["gdal_contour", "-q", "-fl", str(-tolerance), "-f", "GeoJSON", str(raster), str(lines)], check=True)
        crests = json.loads(lines.read_text())["features"]
    for f in crests:
        xy = np.array(f["geometry"]["coordinates"])
        if len(xy) < 2 or np.hypot(*np.diff(xy, axis=0).T).sum() < 150:
            continue
        x, y = densify(xy)
        yp = y + (height(x, y) - base) * LEAN
        features += runs(x, yp, falling[cell(x, y)], "crest", {})

    # Ridgelines, shifted and hidden like the strokes, except within three cells of a crest outline.
    outline = np.array([to_utm(*c) for f in features if f["properties"]["kind"] == "crest" for c in f["geometry"]["coordinates"]])
    near = cKDTree(outline) if len(outline) else None
    for xy, rel in ridges(Z, x0, y0):
        x, y = densify(xy)
        yp, shown = project(x, y)
        if near is not None:
            shown &= near.query(np.column_stack([x, yp]), distance_upper_bound=3 * CELL)[0] == np.inf
        features += runs(x, yp, shown, "ridge", {"rel": rel})
    print(f"Lowest ground {base:.0f} m, shifts up to {(Z.max() - base) * LEAN / 1000:.1f} km; "
          + ", ".join(f"{k} {sum(f['properties']['kind'] == k for f in features):,}" for k in ("stroke", "contour", "stream", "journey", "crest", "ridge")))
    return features


def main() -> None:
    features = build()
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "oblique.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}))
        # Relative names keep local paths out of the archive's metadata.
        subprocess.run(["tippecanoe", "-q", "-f", "-o", "oblique.pmtiles", "-Z9", "-z12", "--no-line-simplification",
                        "--no-tile-size-limit", "--no-feature-limit", "-n", "The Crossing: raised relief (test area)", "-A", ATTRIBUTION,
                        "-L", "oblique:oblique.geojson"], check=True, cwd=tmp)
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(Path(tmp) / "oblique.pmtiles", ARCHIVE)
    shutil.copy(ARCHIVE, REPO / "site" / "public" / "tiles" / "oblique.pmtiles")
    print(f"Wrote {ARCHIVE.relative_to(REPO)} ({ARCHIVE.stat().st_size / 1e6:.1f} MB) and copied it to site/public/tiles/")


if __name__ == "__main__":
    main()
