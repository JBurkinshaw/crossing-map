"""Draft outlines for the story's two named regions, the Animas Valley and La Babícora (plan section 11, stage 4).

Run from the repo root: uv run --project pipeline python -m crossing.regions
Writes pipeline/seeds/regions.geojson, which crossing.build_story reads into data/areas.geojson.

Decision 0008 has inferred areas drawn by hand in QGIS. These are drafts to start from, not that drawing: each
region is the basin floor around its place, the ground below FLOOR_M that is connected to the place's pin, traced
from the Copernicus DEM at 90 m and simplified. Edit the seed file in QGIS and keep the reasoning in step.
"""

import json
from pathlib import Path

import numpy as np
import rasterio
import rasterio.enums
import rasterio.warp
from rasterio.features import shapes
from scipy.ndimage import label
from shapely import Point
from shapely.geometry import mapping, shape

from crossing.hachures import DEM_TILES, REPO

OUT = REPO / "pipeline" / "seeds" / "regions.geojson"
CELL_DEG = 1 / 1200  # about 90 m

# id: (name, place, a point inside it (lon, lat), (west, south, east, north), floor in metres, first_seen, reasoning)
REGIONS = {
    "region-animas-valley": (
        # GNIS pins the valley at its north end; the story's valley is the southern floor, where J1's stop is.
        "The Animas Valley", "animas-valley", (-108.88, 31.6), (-109.06, 31.335, -108.66, 31.96), 1600, "1-03",
        "The valley floor between the Animas and Peloncillo ranges, where the wolf runs and the Parhams live (Part I) "
        "and the text's Animas Plain lies (2-04, 4-02). Drafted from the DEM as the ground below 1,600 m connected to "
        "J1's Animas Valley stop, between the border and Animas town; the ranges on either side rise above 1,800 m. To be checked by hand in QGIS (decision 0008)."),
    "region-la-babicora": (
        "La Babícora", "la-babicora", None, (-108.15, 28.85, -107.45, 29.65), 2200, "2-08",
        "The plains of the Babícora, Hearst's ranch country, named at Casas Grandes (2-08) and ridden by Billy in Part IV. "
        "Drafted from the DEM as the basin floor below 2,200 m connected to the hacienda's pin, around the Laguna de "
        "Babícora; the estate's legal bounds are not known to this project. To be checked by hand in QGIS (decision 0008)."),
}


def pin(place: str) -> tuple[float, float]:
    for f in json.loads((REPO / "data" / "places.geojson").read_text(encoding="utf-8"))["features"]:
        if f["properties"]["id"] == f"place-{place}":
            return tuple(f["geometry"]["coordinates"])
    raise KeyError(place)


def floor(bounds: tuple[float, float, float, float], below: float, at: tuple[float, float]):
    """The connected ground below `below` metres containing `at` (lon, lat), as a WGS 84 polygon."""
    west, south, east, north = bounds
    width, height = round((east - west) / CELL_DEG), round((north - south) / CELL_DEG)
    transform = rasterio.transform.from_bounds(west, south, east, north, width, height)
    dem = np.full((height, width), np.nan, dtype="float32")
    for tif in DEM_TILES.glob("*.tif"):
        with rasterio.open(tif) as src:
            b = src.bounds
            if b.right <= west or b.left >= east or b.top <= south or b.bottom >= north:
                continue
            part = np.full((height, width), np.nan, dtype="float32")
            rasterio.warp.reproject(rasterio.band(src, 1), part, dst_transform=transform, dst_crs="EPSG:4326",
                                    resampling=rasterio.enums.Resampling.average, dst_nodata=np.nan)
            dem = np.where(np.isnan(dem), part, dem)
    low = np.nan_to_num(dem, nan=1e9) < below
    regions, _ = label(low)
    col, row = ~transform * at
    keep = regions == regions[int(row), int(col)]
    poly = max((shape(g) for g, v in shapes(keep.astype("uint8"), mask=keep, transform=transform) if v == 1),
               key=lambda g: g.area)
    # Fill pits and inlets narrower than about 1 km, then simplify to about 300 m.
    return poly.buffer(0.01).buffer(-0.01).simplify(0.003)


def main() -> None:
    features = []
    for rid, (name, place, inside, bounds, below, first_seen, reasoning) in REGIONS.items():
        at = inside or pin(place)
        poly = floor(bounds, below, at)
        assert poly.contains(Point(at)), f"{rid}: the pin is not inside its region"
        geometry = mapping(poly)
        geometry["coordinates"] = [[[round(x, 5), round(y, 5)] for x, y in ring] for ring in geometry["coordinates"]]
        features.append({"type": "Feature", "geometry": geometry,
                         "properties": {"id": rid, "name": name, "place": place, "first_seen": first_seen, "reasoning": reasoning}})
        print(f"{rid}: {len(geometry['coordinates'][0])} vertices")
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
