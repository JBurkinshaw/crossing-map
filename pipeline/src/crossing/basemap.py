"""The base map's Natural Earth and Census layers: one definition for tiles/build_base.py and crossing.plan_oblique."""

from collections.abc import Sequence
from pathlib import Path

import shapely
from shapely.geometry import box, shape
from shapely.ops import unary_union

from crossing.paths import CACHE
from crossing.vector import read

BASEMAP = CACHE / "basemap"
# The Aros-Bavispe confluence (GeoNames 4017237 and 4018306): Natural Earth's "Yaqui" north of it is the Bavispe.
YAQUI_STARTS = 29.53

# Base-map layer -> (shapefile, SQL selecting and renaming the fields the style reads, extra ogr2ogr arguments).
LAYERS = {
    "mexico": ("ne_10m_admin_1_states_provinces",
               "SELECT name FROM ne_10m_admin_1_states_provinces WHERE adm0_a3 = 'MEX'", ()),
    "country_line": ("ne_10m_admin_0_boundary_lines_land",
                     "SELECT featurecla AS kind FROM ne_10m_admin_0_boundary_lines_land", ()),
    "state_line": ("ne_10m_admin_1_states_provinces_lines",
                   "SELECT adm0_a3 AS country FROM ne_10m_admin_1_states_provinces_lines "
                   "WHERE adm0_a3 IN ('USA', 'MEX')",
                   ()),
    "county_line": ("cb_2023_us_county_500k",
                    "SELECT NAME AS name FROM cb_2023_us_county_500k WHERE STATEFP IN ('04', '35', '48')",
                    ("-nlt", "MULTILINESTRING")),
    "railroad": ("ne_10m_railroads_north_america", "SELECT scalerank FROM ne_10m_railroads_north_america", ()),
    "road": ("ne_10m_roads", "SELECT type, scalerank FROM ne_10m_roads WHERE continent = 'North America'", ()),
}


def shapefile(name: str) -> Path:
    return BASEMAP / name / f"{name}.shp"


def mexico(bbox: Sequence, tmp: Path, crs: str = "EPSG:4326") -> shapely.Geometry:
    """The Mexico side of the border inside the box, as one polygon in `crs`."""
    name, sql, _ = LAYERS["mexico"]
    features = read(shapefile(name), sql, bbox, tmp / f"mexico-{crs[5:]}.geojson", crs=crs)
    return unary_union([shape(f["geometry"]) for f in features]).buffer(0)


def corrected_names(geom: shapely.Geometry, name: str | None) -> list[tuple[shapely.Geometry, str | None]]:
    """A Natural Earth river split where its name is wrong: its "Yaqui" north of the Aros confluence is the Bavispe."""
    if name != "Yaqui":
        return [(geom, name)]
    north = box(-180, YAQUI_STARTS, 180, 90)
    parts = ((geom.intersection(north), "Bavispe"), (geom.difference(north), "Yaqui"))
    return [(part, n) for part, n in parts if not part.is_empty]
