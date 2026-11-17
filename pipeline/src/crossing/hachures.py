"""Production hachures and contours (design section 5.2, layer 1; decisions 0015 and 0016).

Run from the repo root, with QGIS_ENV set to the QGIS 4 environment:
    QGIS_ENV=/path/to/qgis uv run --project pipeline python -m crossing.hachures \
        [--scale fine|coarse|dense|all] [--jobs 4]
or, for the Wheeler build (crossing.wheeler_hachures; never writes to the production cache), over one box or over
the same corridor as the fine scale:
    ... python -m crossing.hachures --style wheeler --bbox W S E N --out private/cache/relief/wheeler-test
    ... python -m crossing.hachures --style wheeler --region corridor --out private/cache/relief/wheeler

Three scales, each with absolute settings so that tiles match where they meet:
  fine    30 m DEM, inside the journeys corridor (journeys buffered CORRIDOR_HALF_M each side),
          as short strokes split at each 10 m contour band (decision 0016)
  dense   the fine strokes closer together, over the same corridor, for zoom 12
  coarse  90 m DEM, everywhere the Copernicus tiles in private/cache/dem/copernicus cover;
          drawn only outside the corridor

Each scale runs on a fixed UTM 12N tile grid, so a later run for a wider
corridor adds tiles rather than redoing them. A tile is prepared as in
prepare_dem() (bilinear to 30 m, Gaussian smoothing, then averaged to 90 m
for coarse), run through pipeline/relief/run_hachures.py with an OVERLAP
margin, and its lines clipped back to the tile's core, so neighbours meet at
the seam. Where a tile runs past the DEM's edge, the gap is filled with the
nearest elevation and the lines there are dropped.

Per-tile results are cached in private/cache/relief/production/<folder>/;
delete a tile's file to run it again. The merged results,
private/cache/relief/production/<scale>.geojson, give each line the
attributes the style shades it with, rounded to keep the tiles small:
  Slope   mean slope under the line, whole degrees
  Aspect  the direction the ground under the line faces (downslope), degrees clockwise from north, in 5s
  Rand    a fixed random digit, 0-9, for drawing a share of the lines at lower zooms
Fine and coarse are tiled from zoom 10 to 12, dense at zoom 12; the map over-zooms to 13. contour.geojson
holds 50 m contours (`Ele`, metres) from the same smoothed DEMs, fine inside the
corridor and coarse outside it.
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyproj import Transformer
from scipy.ndimage import distance_transform_edt, gaussian_filter
from shapely import LineString, Polygon, box, unary_union
from shapely.geometry import shape

from crossing import dem
from crossing.paths import CACHE, DATA, REPO
from crossing.paths import UTM_CRS as CRS

# Folders of Copernicus tiles the relief covers; crossing.full_region adds the rest of the story box for its run.
DEM_FOLDERS = [dem.COPERNICUS]
SMOOTH_SIGMA = 1.5  # cells; a light Gaussian, so hachures follow landforms rather than noise
# The attribution of every relief archive.
ATTRIBUTION = f"Relief from {dem.NOTICE}"
HARNESS = REPO / "pipeline" / "relief" / "run_hachures.py"
OUT = CACHE / "relief" / "production"
JOURNEYS = DATA / "journeys.geojson"
CORRIDOR_HALF_M = 20_000  # the design's corridor is about 40 km wide
GRID_ORIGIN = (500_000, 3_000_000)  # UTM 12N metres; tile edges fall on multiples of the tile size from here

# Settings in the units the generator takes: spacing in DEM cells, slopes in degrees, contours in metres.
# Fine and coarse use the same cell spacing, so coarse lines lie three times as far apart. The generator's
# spacing step compares every contour with every hachure, so run time grows faster than tile area: a
# 120 km coarse tile over the Sierra Madre ran for over 30 minutes, which 60 km tiles avoid.
# Fine lines are split into short strokes, one per 10 m contour band ("split"); coarse lines stay whole ("main").
# Dense is the fine set closer together (density B, design 5.2), drawn from zoom 12 over the same corridor.
FINE = {"cell": 30, "tile": 40_000, "overlap": 3_000, "min_spacing": 2, "max_spacing": 4.5, "min_slope": 10,
        "max_slope": 40, "interval": 10, "folder": "fine-s2-4.5-split", "output": "split", "zooms": (10, 12)}
SCALES = {
    "fine": FINE,
    "coarse": {"cell": 90, "tile": 60_000, "overlap": 6_000, "min_spacing": 3, "max_spacing": 8,
               "min_slope": 5, "max_slope": 38, "interval": 10, "folder": "coarse", "output": "main",
               "zooms": (10, 12)},
    "dense": FINE | {"min_spacing": 1.3, "max_spacing": 3, "folder": "fine-s1.3-3-split", "zooms": (12, 12)},
}
CONTOUR_ZOOMS = (10, 12)
# Route segments travelled this way get no fine relief (design 5.2): the corridor follows the rides and walks.
NOT_IN_CORRIDOR = {"bus", "train", "reported"}
CONTOUR_INTERVAL = 50

to_utm = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform
to_wgs = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform


def reproject(transform, geom):
    return shapely.transform(geom, lambda xy: np.column_stack(transform(xy[:, 0], xy[:, 1])))


def coverage() -> Polygon:
    """Where the Copernicus tiles are, in UTM: each tile name gives its south-west corner."""
    boxes = []
    for tif in (t for folder in DEM_FOLDERS for t in folder.glob("*.tif")):
        parts = tif.stem.split("_")  # Copernicus_DSM_COG_10_N28_00_W107_00_DEM
        lat = int(parts[4][1:]) * (1 if parts[4][0] == "N" else -1)
        lon = int(parts[6][1:]) * (-1 if parts[6][0] == "W" else 1)
        boxes.append(box(lon, lat, lon + 1, lat + 1).segmentize(0.05))
    return reproject(to_utm, unary_union(boxes))


def corridor() -> Polygon:
    """The journeys buffered CORRIDOR_HALF_M each side, in UTM."""
    lines = [LineString(f["geometry"]["coordinates"]) for f in json.loads(JOURNEYS.read_text())["features"]
             if f["properties"]["kind"] == "route-segment"
             and f["properties"].get("travel") not in NOT_IN_CORRIDOR]
    return reproject(to_utm, unary_union(lines)).buffer(CORRIDOR_HALF_M)


def fine_region(cover: Polygon) -> Polygon:
    """Where the fine (and dense) scale draws: the corridor, less the lines within two cells of the DEM's edge,
    which come from filled ground. The Wheeler build's corridor mode uses the same region."""
    return corridor().intersection(cover.buffer(-60))


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
    """The tile's DEM in UTM, smoothed by SMOOTH_SIGMA cells, gaps filled from the nearest cell."""
    with tempfile.TemporaryDirectory() as tmp:
        vrt, warped = dem.build_vrt(Path(tmp) / "m.vrt", dem.tiles(*DEM_FOLDERS)), Path(tmp) / "w.tif"
        subprocess.run(["gdalwarp", "-q", "-overwrite", "-t_srs", CRS, "-te", *map(str, bounds), "-tr", "30", "30",
                        "-r", "bilinear", "-ot", "Float32", "-dstnodata", "-9999", str(vrt), str(warped)], check=True)
        with rasterio.open(warped) as src:
            profile, heights = src.profile, src.read(1)
        missing = heights <= -9000
        if missing.any():
            idx = distance_transform_edt(missing, return_distances=False, return_indices=True)
            heights = heights[tuple(idx)]
        heights = gaussian_filter(heights, sigma=SMOOTH_SIGMA)
        profile.update(driver="GTiff", nodata=None, compress="deflate", tiled=True, blockxsize=256, blockysize=256)
        smooth = Path(tmp) / "s.tif"
        with rasterio.open(smooth, "w", **profile) as dst:
            dst.write(heights, 1)
        subprocess.run(["gdalwarp", "-q", "-overwrite", "-tr", str(cell), str(cell), "-r", "average",
                        "-co", "COMPRESS=DEFLATE", str(smooth), str(out)], check=True)


def qgis_python(qgis_env: Path) -> Path:
    """The newest python3.N in the QGIS environment's bin folder."""
    found = [p for p in (qgis_env / "bin").glob("python3.*") if re.fullmatch(r"python3\.\d+", p.name)]
    if not found:
        sys.exit(f"No python3.N in {qgis_env / 'bin'}; set QGIS_ENV to the QGIS 4 environment.")
    return max(found, key=lambda p: int(p.name.split(".")[1]))


def run_tile(scale: str, name: str, core: Polygon, s: dict, qgis_env: Path) -> Path:
    """Hachures for one tile, cached as <name>-<output>.geojson (WGS 84, unclipped)."""
    folder = OUT / s["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    result = folder / f"{name}-{s['output']}.geojson"
    if result.exists():
        return result
    tile_dem = folder / f"{name}.tif"
    prepare_dem(core.buffer(s["overlap"], join_style="mitre").bounds, s["cell"], tile_dem)
    env = {**os.environ, "PYTHONPATH": str(qgis_env / "share" / "qgis" / "python"), "QT_QPA_PLATFORM": "offscreen"}
    args = [str(qgis_python(qgis_env)), str(HARNESS), str(tile_dem), str(folder / name),
            "--min-spacing", str(s["min_spacing"]), "--max-spacing", str(s["max_spacing"]),
            "--min-slope", str(s["min_slope"]), "--max-slope", str(s["max_slope"]),
            "--contour-interval", str(s["interval"]), *(["--split"] if s["output"] == "split" else [])]
    started = time.monotonic()
    run = subprocess.run(args, env=env, capture_output=True, text=True)
    if run.returncode != 0:
        if "No hachures were generated" not in run.stderr + run.stdout:
            raise RuntimeError(f"{scale} {name} failed:\n{run.stderr[-2000:]}")
        result.write_text('{"type": "FeatureCollection", "features": []}')  # flat ground
    print(f"{scale} {name}: {time.monotonic() - started:.0f} s", flush=True)
    return result


def sampler(dem_path: Path):
    """A function giving (mean slope, aspect) in degrees under a UTM line, from the tile's DEM."""
    with rasterio.open(dem_path) as src:
        heights, t = src.read(1).astype(float), src.transform
    gy, gx = np.gradient(heights, t.e, t.a)  # dz/dy (north) and dz/dx (east)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))

    def sample(line: LineString) -> tuple[float, float]:
        xs, ys = np.asarray(line.xy)
        rows, cols = rasterio.transform.rowcol(t, xs, ys)
        rows = np.clip(rows, 0, slope.shape[0] - 1)
        cols = np.clip(cols, 0, slope.shape[1] - 1)
        # Downslope is against the gradient; the azimuth runs clockwise from north.
        aspect = np.degrees(np.arctan2(-gx[rows, cols].mean(), -gy[rows, cols].mean())) % 360
        return float(slope[rows, cols].mean()), float(aspect)

    return sample


def stroke_properties(sample, line: LineString) -> tuple[dict, list[tuple[float, float]]]:
    """The style's attributes for a hachure line in UTM, and its coordinates in WGS 84 rounded for the tiles."""
    slope, aspect = sample(line)
    coords = [(round(x, 5), round(y, 5)) for x, y in reproject(to_wgs, line).coords]
    rand = zlib.crc32(json.dumps(coords[0]).encode()) % 10
    return {"Slope": round(slope), "Aspect": round(aspect) // 5 * 5 % 360, "Rand": rand}, coords


def clip_tile(name: str, core: Polygon, keep: Polygon, s: dict) -> list[dict]:
    """The tile's lines clipped to its core and to `keep`, with the attributes the style shades them with."""
    doc = json.loads((OUT / s["folder"] / f"{name}-{s['output']}.geojson").read_text())
    if not doc["features"]:
        return []
    area = core.intersection(keep)
    sample = sampler(OUT / s["folder"] / f"{name}.tif")
    # Split strokes span one 10 m contour band, so on steep ground they are only a few cells long.
    shortest = 10 if s["output"] == "split" else 2 * s["cell"]
    out = []
    for f in doc["features"]:
        clipped = reproject(to_utm, LineString(f["geometry"]["coordinates"])).intersection(area)
        for part in getattr(clipped, "geoms", [clipped]):
            if not isinstance(part, LineString) or part.length < shortest:
                continue
            props, coords = stroke_properties(sample, part)
            out.append({"type": "Feature", "tippecanoe": {"minzoom": s["zooms"][0], "maxzoom": s["zooms"][1]},
                        "properties": props, "geometry": {"type": "LineString", "coordinates": coords}})
    return out


def contours(name: str, core: Polygon, keep: Polygon, s: dict) -> list[dict]:
    """CONTOUR_INTERVAL contours (`Ele`, metres) from the tile's smoothed DEM, clipped to its core and to `keep`."""
    area = core.intersection(keep)
    if area.is_empty:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "c.geojson"
        subprocess.run(["gdal_contour", "-q", "-a", "Ele", "-i", str(CONTOUR_INTERVAL), "-f", "GeoJSON",
                        str(OUT / s["folder"] / f"{name}.tif"), str(out)], check=True)
        doc = json.loads(out.read_text())
    features = []
    for f in doc["features"]:
        clipped = shape(f["geometry"]).intersection(area)
        for part in getattr(clipped, "geoms", [clipped]):
            if not isinstance(part, LineString) or part.length < 2 * s["cell"]:
                continue
            coords = [(round(x, 5), round(y, 5)) for x, y in reproject(to_wgs, part).coords]
            zooms = {"minzoom": CONTOUR_ZOOMS[0], "maxzoom": CONTOUR_ZOOMS[1]}
            features.append({"type": "Feature", "tippecanoe": zooms,
                             "properties": {"Ele": round(f["properties"]["Ele"])},
                             "geometry": {"type": "LineString", "coordinates": coords}})
    return features


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", choices=[*SCALES, "all"], default="all")
    ap.add_argument("--jobs", type=int, default=4)
    # The Wheeler build (crossing.wheeler_hachures): one box or the corridor, into its own folder. The default runs
    # production.
    ap.add_argument("--style", choices=["production", "wheeler"], default="production")
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("W", "S", "E", "N"), help="degrees; --style wheeler only")
    ap.add_argument("--region", choices=["corridor"],
                    help="the fine scale's region, in place of --bbox; --style wheeler only")
    ap.add_argument("--out", type=Path, help="output folder; --style wheeler only")
    a = ap.parse_args()
    if "QGIS_ENV" not in os.environ:
        sys.exit("Set QGIS_ENV to the QGIS 4 environment (the folder holding bin/python3.N).")
    qgis_env = Path(os.environ["QGIS_ENV"])
    if a.style == "wheeler":
        from crossing import wheeler_hachures  # imports this module, so it is loaded only when asked for

        if bool(a.bbox) == bool(a.region) or not a.out:
            ap.error("--style wheeler needs --out and one of --bbox or --region")
        if a.out.resolve().is_relative_to(OUT.resolve()):
            ap.error(f"--out must not be inside the production cache, {OUT.relative_to(REPO)}")
        if a.region:
            wheeler_hachures.build(fine_region(coverage()), a.region, a.out, a.jobs, qgis_env)
        else:
            wheeler_hachures.build(wheeler_hachures.bbox_region(tuple(a.bbox)), a.bbox, a.out, a.jobs, qgis_env)
        return

    cover = coverage()
    # Lines within two cells of the DEM's edge come from filled ground, so they are dropped.
    # The fine lines cover the corridor; the coarse lines, everywhere else.
    fine = fine_region(cover)
    regions = {"fine": fine, "dense": fine, "coarse": cover.buffer(-180).difference(fine)}
    lines = []
    for scale in (SCALES if a.scale == "all" else [a.scale]):
        s = SCALES[scale]
        grid = tiles(regions[scale], s["tile"])
        print(f"{scale}: {len(grid)} tiles of {s['tile'] // 1000} km, {regions[scale].area / 1e6:,.0f} km2", flush=True)
        with ThreadPoolExecutor(a.jobs) as pool:
            list(pool.map(lambda t, scale=scale, s=s: run_tile(scale, *t, s, qgis_env), grid))
        features = [f for name, core in grid for f in clip_tile(name, core, regions[scale], s)]
        merged = OUT / f"{scale}.geojson"
        merged.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
        print(f"{merged.relative_to(REPO)}: {len(features):,} lines, {merged.stat().st_size / 1e6:.0f} MB", flush=True)
        if scale != "dense":
            lines += [f for name, core in grid for f in contours(name, core, regions[scale], s)]
    if a.scale == "all":
        merged = OUT / "contour.geojson"
        merged.write_text(json.dumps({"type": "FeatureCollection", "features": lines}))
        print(f"{merged.relative_to(REPO)}: {len(lines):,} contours, {merged.stat().st_size / 1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    main()
