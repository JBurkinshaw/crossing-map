"""Draft outlines for the story's two named regions, the Animas Valley and La Babícora (plan section 11, stage 4).

Run from the repo root: uv run --project pipeline python -m crossing.regions [--force]
Writes pipeline/seeds/regions.geojson, which crossing.build_story reads into data/areas.geojson. That file is
then edited by hand, so the script refuses to replace it unless given --force.

Build order: the drafts sit on place pins from data/places.geojson, which crossing.build_story writes, so a
first build runs build_story (which skips a missing regions file), then this, then build_story again.

Decision 0008 has inferred areas drawn by hand in QGIS. These are drafts to start from, not that drawing: each
region is the basin floor around its place, the ground below FLOOR_M that is connected to the place's pin, traced
from the Copernicus DEM at 90 m and simplified. Edit the seed file in QGIS and keep the reasoning in step.

A height threshold alone cannot hold a valley: the Animas Valley floor rises from 1,340 m at Animas town to 1,544 m
at J1's stop, and the San Simon Valley over the Peloncillos lies at 1,360 m, so any threshold that reaches the stop
floods round the low end of the range. Each region therefore has a clip ring placed by hand (decision 0048). Each
edge of the ring is a crest, set on the high ground between this basin and the next, or a cut, a deliberate limit
such as the border or a line across a low saddle. The floor may meet a cut. If it reaches a crest, the crest is
misplaced or the floor has found a way past it, and the script stops.
"""

import json
import sys

import numpy as np
import rasterio
import rasterio.enums
import rasterio.warp
from rasterio.features import geometry_mask, rasterize, shapes
from scipy.ndimage import binary_dilation, label
from shapely import LineString, Point, Polygon
from shapely.geometry import mapping, shape
from shapely.geometry.polygon import orient

from crossing.dem import COPERNICUS
from crossing.paths import DATA, REPO, SEEDS

OUT = SEEDS / "regions.geojson"
CELL_DEG = 1 / 1200  # about 90 m
BORDER_LAT = 31.3328  # the international boundary's east-west line south of the Animas Valley (31° 20' N)
# A floor that comes within this many cells of a crest edge, at more than CREST_CELLS cells, has reached it.
CREST_REACH = 2
CREST_CELLS = 10  # about 0.9 km of floor along the crest

CREST, CUT = "crest", "cut"

# id: (name, place, a point inside it (lon, lat), clip ring, floor in metres, first_seen, reasoning).
# The clip ring is a list of (lon, lat, kind): kind is that of the edge from this vertex to the next.
REGIONS = {
    "region-animas-valley": (
        # GNIS pins the valley at its north end; the story's valley is the southern floor, where J1's stop is.
        "The Animas Valley", "animas-valley", (-108.88, 31.6), [
            (-108.986, BORDER_LAT, CUT),  # the border, east to the Animas Mountains
            # The Animas Mountains' crest and the hills north of them, traced on the DEM: the highest ground in
            # each 0.03 degree band of latitude.
            (-108.757, BORDER_LAT, CREST),
            (-108.775, 31.45, CREST),
            (-108.780, 31.54, CREST),
            (-108.789, 31.57, CREST),
            (-108.770, 31.60, CREST),
            (-108.736, 31.63, CREST),
            (-108.680, 31.66, CREST),
            (-108.664, 31.69, CREST),
            (-108.678, 31.72, CREST),
            # North of here the divide with the Playas Valley is a line of knobs, 1,500 to 1,660 m, no higher than
            # the floor: the ring follows them as a cut, then runs north to the line at Animas town.
            (-108.689, 31.75, CUT),
            (-108.697, 31.78, CUT),
            (-108.702, 31.84, CUT),
            (-108.702, 31.87, CUT),
            (-108.702, 31.96, CUT),  # the line at Animas town, west
            (-108.931, 31.96, CUT),  # south across the low ground to the San Simon Valley, to the Peloncillos
            # The Peloncillos' crest, traced the same way.
            (-108.931, 31.90, CREST),
            (-108.923, 31.87, CREST),
            (-108.962, 31.84, CREST),
            (-108.982, 31.81, CREST),
            (-108.965, 31.75, CREST),
            (-108.962, 31.72, CREST),
            (-109.015, 31.66, CREST),
            (-109.007, 31.60, CREST),
            (-109.049, 31.57, CREST),
            (-109.054, 31.51, CREST),
            (-109.037, 31.48, CREST),
            (-108.982, 31.42, CREST),
            (-108.975, 31.39, CREST),
        ], 1600, "1-03",
        "The valley floor between the Animas and Peloncillo ranges, where the wolf runs and the Parhams live (Part I) "
        "and the text's Animas Plain lies (2-04, 4-02). Drafted from the DEM as the ground below 1,600 m connected to "
        "J1's Animas Valley stop, between the border and Animas town, kept east of the Peloncillos' crest and west of "
        "the Animas Mountains and the low hills north of them (decision 0048)."),
    "region-la-babicora": (
        "La Babícora", "la-babicora", None, [
            (-108.15, 29.50, CUT),  # the basin's north rim, east, cutting off the side valleys that run north
            # East, south and west the sierras hold the floor well inside the ring, so these edges only have to
            # stay clear of it.
            (-107.55, 29.50, CREST),
            (-107.55, 28.95, CREST),
            (-108.15, 28.95, CREST),
        ], 2200, "2-08",
        "The plains of the Babícora, Hearst's ranch country, named at Casas Grandes (2-08) and ridden by Billy in "
        "Part IV. Drafted from the DEM as the basin floor below 2,200 m connected to the hacienda's pin, around the "
        "Laguna de Babícora, cut at the basin's north rim where side valleys run north (decision 0048); the estate's "
        "legal bounds are not known to this project."),
}


def pin(place: str) -> tuple[float, float]:
    for f in json.loads((DATA / "places.geojson").read_text(encoding="utf-8"))["features"]:
        if f["properties"]["id"] == f"place-{place}":
            return tuple(f["geometry"]["coordinates"])
    raise KeyError(place)


def dem_grid(bounds: tuple[float, float, float, float]):
    """The Copernicus DEM resampled to CELL_DEG over `bounds`, with its transform."""
    west, south, east, north = bounds
    width, height = round((east - west) / CELL_DEG), round((north - south) / CELL_DEG)
    transform = rasterio.transform.from_bounds(west, south, east, north, width, height)
    dem = np.full((height, width), np.nan, dtype="float32")
    for tif in sorted(COPERNICUS.glob("*.tif")):
        with rasterio.open(tif) as src:
            b = src.bounds
            if b.right <= west or b.left >= east or b.top <= south or b.bottom >= north:
                continue
            part = np.full((height, width), np.nan, dtype="float32")
            rasterio.warp.reproject(rasterio.band(src, 1), part, dst_transform=transform, dst_crs="EPSG:4326",
                                    resampling=rasterio.enums.Resampling.average, dst_nodata=np.nan)
            dem = np.where(np.isnan(dem), part, dem)
    return dem, transform


def floor(rid: str, clip: list[tuple[float, float, str]], below: float, at: tuple[float, float]):
    """The connected ground below `below` metres containing `at` (lon, lat), inside the clip ring, as a WGS 84
    polygon. Stops if the floor reaches one of the ring's crest edges."""
    ring = Polygon([(x, y) for x, y, _ in clip])
    west, south, east, north = ring.bounds
    pad = 4 * CELL_DEG
    dem, transform = dem_grid((west - pad, south - pad, east + pad, north + pad))
    inside = geometry_mask([ring], dem.shape, transform, invert=True)
    low = (np.nan_to_num(dem, nan=1e9) < below) & inside
    regions, _ = label(low)
    col, row = ~transform * at
    keep = regions == regions[int(row), int(col)]
    assert keep[int(row), int(col)], f"{rid}: the pin is not below {below} m"

    for k, (x, y, kind) in enumerate(clip):
        if kind != CREST:
            continue
        nx, ny, _ = clip[(k + 1) % len(clip)]
        edge = rasterize([(LineString([(x, y), (nx, ny)]), 1)], out_shape=dem.shape, transform=transform,
                         all_touched=True).astype(bool)
        reached = int((keep & binary_dilation(edge, iterations=CREST_REACH)).sum())
        if reached > CREST_CELLS:
            sys.exit(f"{rid}: the floor reaches the crest edge from ({x}, {y}) to ({nx}, {ny}) along {reached} cells. "
                     "Move the edge onto higher ground, or mark it a cut if the floor may end there")

    poly = max((shape(g) for g, v in shapes(keep.astype("uint8"), mask=keep, transform=transform) if v == 1),
               key=lambda g: g.area)
    # Fill pits and inlets narrower than about 1 km, keep inside the ring, then simplify to about 300 m.
    poly = poly.buffer(0.01).buffer(-0.01).intersection(ring).simplify(0.003)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    return orient(poly, sign=-1.0)  # outer ring clockwise (crossing.validate)


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv[1:]:
        sys.exit(f"{OUT.relative_to(REPO)} exists and may hold hand edits; rerun with --force to replace it")
    features = []
    for rid, (name, place, inside, clip, below, first_seen, reasoning) in REGIONS.items():
        at = inside or pin(place)
        poly = floor(rid, clip, below, at)
        assert poly.contains(Point(at)), f"{rid}: the pin is not inside its region"
        geometry = mapping(poly)
        geometry["coordinates"] = [[[round(x, 5), round(y, 5)] for x, y in ring] for ring in geometry["coordinates"]]
        features.append({"type": "Feature", "geometry": geometry,
                         "properties": {"id": rid, "name": name, "place": place, "first_seen": first_seen,
                                        "reasoning": reasoning}})
        print(f"{rid}: {len(geometry['coordinates'][0])} vertices")
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
