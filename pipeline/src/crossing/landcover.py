"""Land cover for the vintage map (decision 0034): the CEC's North American Land Cover 2020, read with height bands
after Brown's biotic communities, in eight classes.

crossing.plan_oblique calls classify() for each strip of the corridor, and turns the classes into polygons twice:
on the ground for the Flat and Tilted views (landcover.pmtiles), and shifted with the Oblique view's line work.

The CEC map (30 m, Landsat; crossing.fetch_landcover) is one classification for Mexico and the US, so it has no
seam at the border. It decides what height cannot: water, towns, fields, wetland, and grass against scrub. It does
not split pine from oak, so height decides which trees, after David E. Brown, ed., Biotic Communities:
Southwestern United States and Northwestern Mexico (1994): gallery forest in the valleys, Madrean oak woodland
above OAK m, pine above PINE m, a slope facing north counting as up to NORTH_DROP m higher. Shrubland above the oak
line is open oak woodland where the slope is at least WOODLAND_SLOPE degrees; on flatter ground (the high basin
floors round Cloverdale, 1,300 to 1,600 m) it stays scrub. Trees and shrubland within RIPARIAN m of a stream of
order RIPARIAN_ORDER or more, below the oak line, are gallery forest.

Coordinates: UTM zone 12N (crossing.hachures.CRS), on the 30 m grid of the strips' DEMs.
"""

import subprocess
from pathlib import Path

import numpy as np
import rasterio
import shapely
from rasterio.enums import Resampling
from rasterio.features import rasterize, shapes, sieve
from rasterio.warp import reproject
from scipy.ndimage import distance_transform_edt

from crossing.fetch_landcover import CEC
from crossing.hachures import CRS

NOTICE = ("Land cover: Commission for Environmental Cooperation (CEC), North American Land Cover 2020 30 m, "
          "NALCMS (CCRS, USGS, CONABIO, CONAFOR, INEGI), CC BY 4.0, its classes re-read with height")
CLIP = CEC / "corridor.tif"

CLASSES = ("water", "riparian", "pine", "oak", "grass", "scrub", "fields", "town")
# CEC classes: 1 to 6 forests, 7, 8 and 11 shrubland, 9, 10 and 12 grassland, 13 and 16 barren, 14 wetland,
# 15 cropland, 17 urban, 18 water.
TREES = (1, 2, 3, 4, 5, 6)
SHRUB = (7, 8, 11, 13, 16)
GRASS = (9, 10, 12)
OAK, PINE, NORTH_DROP = 1_250, 1_800, 150  # metres
RIPARIAN, RIPARIAN_ORDER = 150, 4  # metres, Strahler order
WOODLAND_SLOPE = 6  # degrees, on the DEM smoothed again for the strokes (plan_oblique.GENERALISE)
SIEVE = 40  # cells (3.6 ha): smaller patches join their neighbours
SIMPLIFY = 20  # metres


def clip(bounds: tuple[float, ...]) -> Path:
    """The CEC classes over `bounds` (UTM), on the 30 m grid, cut once from the national files and cached."""
    if CLIP.exists():
        with rasterio.open(CLIP) as src:
            b = src.bounds
            if b.left <= bounds[0] and b.bottom <= bounds[1] and b.right >= bounds[2] and b.top >= bounds[3]:
                return CLIP
    # The two files are clips of one map. Each fills the ground outside its own country with 0, not with its
    # declared no-data value (127), so each is warped on its own and a cell takes whichever file has a class there.
    merged, profile = None, None
    for country in ("usa", "mex"):
        part = CLIP.with_name(f"{country}.part.tif")
        subprocess.run(["gdalwarp", "-q", "-overwrite", "-t_srs", CRS, "-te", *map(str, bounds), "-tr", "30", "30",
                        "-tap", "-r", "near", "-srcnodata", "None", "-dstnodata", "None", "-wo", "INIT_DEST=0",
                        str(CEC / f"{country}.tif"), str(part)], check=True)
        with rasterio.open(part) as src:
            codes, profile = src.read(1), src.profile
        part.unlink()
        valid = (codes >= 1) & (codes <= 19)
        merged = np.where(valid, codes, 0) if merged is None else np.where(valid, codes, merged)
    profile.update(nodata=0, compress="deflate", tiled=True, blockxsize=512, blockysize=512)
    tmp = CLIP.with_name("corridor.tmp.tif")
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(merged, 1)
    tmp.rename(CLIP)
    return CLIP


def cec(transform, shape: tuple[int, int]) -> np.ndarray:
    """The CEC classes on a north-up UTM grid; 0 where there are none."""
    out = np.zeros(shape, dtype=np.uint8)
    with rasterio.open(CLIP) as src:
        reproject(rasterio.band(src, 1), out, src_transform=src.transform, src_crs=src.crs, src_nodata=0,
                  dst_transform=transform, dst_crs=CRS, dst_nodata=0, resampling=Resampling.nearest)
    return out


def classify(codes: np.ndarray, z: np.ndarray, slope: np.ndarray, north: np.ndarray, streams: list[np.ndarray],
             transform) -> np.ndarray:
    """Each cell's class, an index into CLASSES or -1, on a north-up grid. `codes` are the CEC's; `z` the height
    (m), `slope` (degrees) and `north` (1 on a slope facing due north) from the smoothed DEM; `streams` the UTM
    lines of streams of order RIPARIAN_ORDER and up."""
    height = z + NORTH_DROP * np.clip(north, 0, 1)
    band = np.select([height >= PINE, height >= OAK], [2, 1], 0)
    lines = [shapely.LineString(xy) for xy in streams if len(xy) > 1]
    if lines:
        wet = rasterize(lines, out_shape=codes.shape, transform=transform, all_touched=True) > 0
        near = distance_transform_edt(~wet) * abs(transform.a) < RIPARIAN
    else:
        near = np.zeros(codes.shape, bool)
    trees, shrub, grass = np.isin(codes, TREES), np.isin(codes, SHRUB), np.isin(codes, GRASS)
    k = CLASSES.index
    out = np.select(
        [codes == 18, codes == 17, codes == 15, codes == 14,
         (trees | shrub) & near & (band == 0), trees & (band == 0), trees & (band == 2), trees & (band == 1),
         shrub & (band >= 1) & (slope >= WOODLAND_SLOPE), shrub, grass],
        [k("water"), k("town"), k("fields"), k("riparian"),
         k("riparian"), k("riparian"), k("pine"), k("oak"),
         k("oak"), k("scrub"), k("grass")],
        -1,
    )
    return sieve((out + 1).astype(np.int32), size=SIEVE) - 1


def polygons(classes: np.ndarray, transform) -> list[tuple[shapely.Geometry, int]]:
    """The classes as polygons (in the grid's coordinates), simplified together so that neighbours still meet."""
    found = [(shapely.geometry.shape(g), int(v)) for g, v in shapes(classes.astype(np.int16), transform=transform)
             if v >= 0]
    if not found:
        return []
    simple = shapely.coverage_simplify([g for g, _ in found], SIMPLIFY)
    return [(g, v) for g, (_, v) in zip(simple, found, strict=True) if not g.is_empty]
