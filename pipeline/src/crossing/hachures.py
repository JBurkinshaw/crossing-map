"""Production hachures (plan section 5.2, layer 1; decisions 0014 and 0015).

Run from the repo root, with QGIS_ENV set to the QGIS 4 environment:
    QGIS_ENV=/path/to/qgis uv run --project pipeline python -m crossing.hachures [--scale fine|coarse] [--jobs 4]

Two scales, each with absolute settings so that tiles match where they meet:
  fine    30 m DEM, inside the journeys corridor (journeys buffered CORRIDOR_HALF_M each side)
  coarse  90 m DEM, everywhere the Copernicus tiles in private/cache/dem/copernicus cover

Each scale runs on a fixed UTM 12N tile grid, so a later run for a wider
corridor adds tiles rather than redoing them. A tile is prepared as in
crossing.relief (bilinear to 30 m, Gaussian smoothing, then averaged to 90 m
for coarse), run through pipeline/relief/run_hachures.py with an OVERLAP
margin, and its lines clipped back to the tile's core, so neighbours meet at
the seam. Where a tile runs past the DEM's edge, the gap is filled with the
nearest elevation and the lines there are dropped.

Per-tile results are cached in private/cache/relief/production/<scale>/;
delete a tile's file to run it again. The merged result,
private/cache/relief/production/<scale>.geojson, gives each line its mean
slope (`Slope`, degrees) and its zoom range: coarse to zoom 9 inside the
corridor and to 13 outside it, fine from zoom 10.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from scipy.ndimage import distance_transform_edt, gaussian_filter
import shapely
from shapely import box, LineString, Polygon, unary_union

from crossing.relief import CRS, DEM_TILES, SMOOTH_SIGMA

REPO = Path(__file__).resolve().parents[3]
HARNESS = REPO / "pipeline" / "relief" / "run_hachures.py"
OUT = REPO / "private" / "cache" / "relief" / "production"
JOURNEYS = REPO / "data" / "journeys.geojson"
CORRIDOR_HALF_M = 20_000  # the plan's corridor is about 40 km wide
GRID_ORIGIN = (500_000, 3_000_000)  # UTM 12N metres; tile edges fall on multiples of the tile size from here

# Settings in the units the generator takes: spacing in DEM cells, slopes in degrees, contours in metres.
# Fine and coarse use the same cell spacing, so coarse lines lie three times as far apart. The generator's
# spacing step compares every contour with every hachure, so run time grows faster than tile area: a
# 120 km coarse tile over the Sierra Madre ran for over 30 minutes, which 60 km tiles avoid.
SCALES = {
    "fine": {"cell": 30, "tile": 40_000, "overlap": 3_000, "min_spacing": 3, "max_spacing": 8,
             "min_slope": 10, "max_slope": 40, "interval": 10, "zooms": (10, 13)},
    "coarse": {"cell": 90, "tile": 60_000, "overlap": 6_000, "min_spacing": 3, "max_spacing": 8,
               "min_slope": 5, "max_slope": 38, "interval": 10, "zooms": (6, 9),
               # Outside the corridor no fine lines take over, so the coarse ones carry on to the last zoom.
               "zooms_outside_corridor": (6, 13)},
}

to_utm = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform
to_wgs = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform


def reproject(transform, geom):
    return shapely.transform(geom, lambda xy: np.column_stack(transform(xy[:, 0], xy[:, 1])))


def coverage() -> Polygon:
    """Where the Copernicus tiles are, in UTM: each tile name gives its south-west corner."""
    boxes = []
    for tif in DEM_TILES.glob("*.tif"):
        parts = tif.stem.split("_")  # Copernicus_DSM_COG_10_N28_00_W107_00_DEM
        lat = int(parts[4][1:]) * (1 if parts[4][0] == "N" else -1)
        lon = int(parts[6][1:]) * (-1 if parts[6][0] == "W" else 1)
        boxes.append(box(lon, lat, lon + 1, lat + 1).segmentize(0.05))
    return reproject(to_utm, unary_union(boxes))


def corridor() -> Polygon:
    lines = [LineString(f["geometry"]["coordinates"]) for f in json.loads(JOURNEYS.read_text())["features"]]
    return reproject(to_utm, unary_union(lines)).buffer(CORRIDOR_HALF_M)


def tiles(region: Polygon, size: int) -> list[tuple[str, Polygon]]:
    """Grid tiles that touch the region, named by their south-west corner in km."""
    x0, y0 = GRID_ORIGIN
    minx, miny, maxx, maxy = region.bounds
    found = []
    for i in range(math.floor((minx - x0) / size), math.ceil((maxx - x0) / size)):
        for j in range(math.floor((miny - y0) / size), math.ceil((maxy - y0) / size)):
            core = box(x0 + i * size, y0 + j * size, x0 + (i + 1) * size, y0 + (j + 1) * size)
            if core.intersects(region):
                found.append((f"{round(core.bounds[0] / 1000)}e-{round(core.bounds[1] / 1000)}n", core))
    return found


def prepare_dem(bounds: tuple[float, ...], cell: int, out: Path) -> None:
    """The tile's DEM in UTM, smoothed as in crossing.relief, gaps filled from the nearest cell."""
    with tempfile.TemporaryDirectory() as tmp:
        vrt, warped = Path(tmp) / "m.vrt", Path(tmp) / "w.tif"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *map(str, sorted(DEM_TILES.glob("*.tif")))], check=True)
        subprocess.run(["gdalwarp", "-q", "-overwrite", "-t_srs", CRS, "-te", *map(str, bounds), "-tr", "30", "30",
                        "-r", "bilinear", "-ot", "Float32", "-dstnodata", "-9999", str(vrt), str(warped)], check=True)
        with rasterio.open(warped) as src:
            profile, dem = src.profile, src.read(1)
        missing = dem <= -9000
        if missing.any():
            idx = distance_transform_edt(missing, return_distances=False, return_indices=True)
            dem = dem[tuple(idx)]
        dem = gaussian_filter(dem, sigma=SMOOTH_SIGMA)
        profile.update(driver="GTiff", nodata=None, compress="deflate", tiled=True, blockxsize=256, blockysize=256)
        smooth = Path(tmp) / "s.tif"
        with rasterio.open(smooth, "w", **profile) as dst:
            dst.write(dem, 1)
        subprocess.run(["gdalwarp", "-q", "-overwrite", "-tr", str(cell), str(cell), "-r", "average",
                        "-co", "COMPRESS=DEFLATE", str(smooth), str(out)], check=True)


def run_tile(scale: str, name: str, core: Polygon, s: dict, qgis_env: Path) -> Path:
    """Hachures for one tile, cached as <name>-main.geojson (WGS 84, unclipped)."""
    folder = OUT / scale
    folder.mkdir(parents=True, exist_ok=True)
    result = folder / f"{name}-main.geojson"
    if result.exists():
        return result
    dem = folder / f"{name}.tif"
    prepare_dem(core.buffer(s["overlap"], join_style="mitre").bounds, s["cell"], dem)
    env = {**os.environ, "PYTHONPATH": str(qgis_env / "share" / "qgis" / "python"), "QT_QPA_PLATFORM": "offscreen"}
    args = [str(qgis_env / "bin" / "python3.14"), str(HARNESS), str(dem), str(folder / name),
            "--min-spacing", str(s["min_spacing"]), "--max-spacing", str(s["max_spacing"]),
            "--min-slope", str(s["min_slope"]), "--max-slope", str(s["max_slope"]),
            "--contour-interval", str(s["interval"])]
    started = time.monotonic()
    run = subprocess.run(args, env=env, capture_output=True, text=True)
    if run.returncode != 0:
        if "No hachures were generated" not in run.stderr + run.stdout:
            raise RuntimeError(f"{scale} {name} failed:\n{run.stderr[-2000:]}")
        result.write_text('{"type": "FeatureCollection", "features": []}')  # flat ground
    print(f"{scale} {name}: {time.monotonic() - started:.0f} s", flush=True)
    return result


def slope_sampler(dem_path: Path):
    """A function giving the mean slope (degrees) under a UTM line, from the tile's DEM."""
    with rasterio.open(dem_path) as src:
        dem, t = src.read(1).astype(float), src.transform
    gy, gx = np.gradient(dem, t.e, t.a)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))

    def mean(line: LineString) -> float:
        xs, ys = np.asarray(line.xy)
        rows, cols = rasterio.transform.rowcol(t, xs, ys)
        rows = np.clip(rows, 0, slope.shape[0] - 1)
        cols = np.clip(cols, 0, slope.shape[1] - 1)
        return float(slope[rows, cols].mean())

    return mean


def clip_tile(scale: str, name: str, core: Polygon, keep: Polygon, s: dict, corridor: Polygon) -> list[dict]:
    """The tile's lines clipped to its core and to `keep`, with mean slope and zoom range.

    Coarse lines are split at the corridor's edge: inside it they stop where the fine lines start.
    """
    doc = json.loads((OUT / scale / f"{name}-main.geojson").read_text())
    if not doc["features"]:
        return []
    area = core.intersection(keep)
    mean_slope = slope_sampler(OUT / scale / f"{name}.tif")
    out = []
    for f in doc["features"]:
        clipped = reproject(to_utm, LineString(f["geometry"]["coordinates"])).intersection(area)
        if "zooms_outside_corridor" in s:
            pieces = [(clipped.intersection(corridor), s["zooms"]),
                      (clipped.difference(corridor), s["zooms_outside_corridor"])]
        else:
            pieces = [(clipped, s["zooms"])]
        for geom, (minzoom, maxzoom) in pieces:
            for part in getattr(geom, "geoms", [geom]):
                if not isinstance(part, LineString) or part.length < 2 * s["cell"]:
                    continue
                coords = [(round(x, 5), round(y, 5)) for x, y in reproject(to_wgs, part).coords]
                out.append({"type": "Feature", "tippecanoe": {"minzoom": minzoom, "maxzoom": maxzoom},
                            "properties": {"Slope": round(mean_slope(part), 1)},
                            "geometry": {"type": "LineString", "coordinates": coords}})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", choices=[*SCALES, "both"], default="both")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    if "QGIS_ENV" not in os.environ:
        sys.exit("Set QGIS_ENV to the QGIS 4 environment (the folder holding bin/python3.14).")
    qgis_env = Path(os.environ["QGIS_ENV"])

    cover = coverage()
    # Lines within two cells of the DEM's edge come from filled ground, so they are dropped.
    regions = {"fine": corridor().intersection(cover.buffer(-60)), "coarse": cover.buffer(-180)}
    for scale in (SCALES if a.scale == "both" else [a.scale]):
        s = SCALES[scale]
        grid = tiles(regions[scale], s["tile"])
        print(f"{scale}: {len(grid)} tiles of {s['tile'] // 1000} km, {regions[scale].area / 1e6:,.0f} km2", flush=True)
        with ThreadPoolExecutor(a.jobs) as pool:
            list(pool.map(lambda t: run_tile(scale, *t, s, qgis_env), grid))
        features = [f for name, core in grid for f in clip_tile(scale, name, core, regions[scale], s, regions["fine"])]
        merged = OUT / f"{scale}.geojson"
        merged.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
        print(f"{merged.relative_to(REPO)}: {len(features):,} lines, {merged.stat().st_size / 1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    main()
