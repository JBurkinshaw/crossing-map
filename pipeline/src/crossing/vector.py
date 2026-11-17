"""Reading vector sources through ogr2ogr, and small line helpers shared by the tile and Oblique builds."""

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import shapely


def ogr2geojson(source: str | Path, sql: str, bbox: Sequence, out: Path, *, crs: str = "EPSG:4326",
                latin1: bool = False, extra: Sequence[str] = ()) -> Path:
    """Write the features of `source` selected by `sql` inside the lon/lat `bbox` to `out` as GeoJSON in `crs`.

    Every source here is in longitude and latitude, so the box needs no reprojection (ogr2ogr allows none
    alongside -sql). INEGI's attribute tables are Latin-1 (`latin1`); GeoJSON comes out as UTF-8.
    """
    encoding = ["--config", "SHAPE_ENCODING", "ISO-8859-1"] if latin1 else []
    subprocess.run(["ogr2ogr", *encoding, "-f", "GeoJSON", "-t_srs", crs, "-spat", *map(str, bbox),
                    "-dialect", "OGRSQL", "-sql", sql, "-dim", "XY", *extra, str(out), str(source)],
                   check=True, capture_output=True)
    return out


def read(source: str | Path, sql: str, bbox: Sequence, out: Path, **kwargs) -> list[dict]:
    """The features ogr2geojson() writes to `out`, those without a geometry dropped."""
    features = json.loads(ogr2geojson(source, sql, bbox, out, **kwargs).read_text())["features"]
    return [f for f in features if f["geometry"]]


def segments(geom: shapely.Geometry) -> list[shapely.LineString]:
    """The LineStrings of a geometry that have at least two points."""
    return [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "LineString" and len(g.coords) > 1]


def chaikin(xy: np.ndarray, rounds: int = 2) -> np.ndarray:
    """Chaikin's corner cutting: each round replaces every corner with two points a quarter of the way along its
    sides, keeping the ends."""
    xy = np.asarray(xy, dtype=float)
    for _ in range(rounds):
        if len(xy) < 3:
            break
        a, b = xy[:-1], xy[1:]
        cut = np.empty((2 * len(a), 2))
        cut[0::2] = 0.75 * a + 0.25 * b
        cut[1::2] = 0.25 * a + 0.75 * b
        xy = np.vstack([xy[:1], cut, xy[-1:]])
    return xy
