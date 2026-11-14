"""Build tiles/out/base.pmtiles: the literary basemap's vector layers.

Run from the repo root: uv run --project pipeline python tiles/build_base.py
Reads Natural Earth 10m and US Census cartographic boundary files from
private/cache/basemap/, USGS NHD flowlines from private/cache/hydro/nhd/ and INEGI's
river network from private/cache/hydro/inegi/ (see review/stage-2/README.md for the
download list), clips them to the story box, and tiles them with tippecanoe at
zoom 4-11. NHD streams (CREEK_HU8 only) appear from zoom 9; the named rivers come from tiles/rivers.py,
which uses every NHD watershed and INEGI region in the cache.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from rivers import write_layers

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "private" / "cache" / "basemap"
NHD = REPO / "private" / "cache" / "hydro" / "nhd"
OUT = REPO / "tiles" / "out" / "base.pmtiles"
# The story box (plan section 7), widened by half a degree so lines run off the edge cleanly.
BOX = ["-113.5", "26.5", "-103.5", "36.5"]
# The watersheds whose small streams are drawn as creeks: the bootheel and the border country. The other NHD
# watersheds in the cache are there for the named rivers only.
CREEK_HU8 = ["13030201", "13030202", "15040006", "15080301", "15080302", "15080303"]

# layer name -> (source file, SQL selecting and renaming the fields we keep, extra ogr2ogr args)
LAYERS = {
    "mexico": ("ne_10m_admin_1_states_provinces",
               "SELECT name FROM ne_10m_admin_1_states_provinces WHERE adm0_a3 = 'MEX'", []),
    "country_line": ("ne_10m_admin_0_boundary_lines_land",
                     "SELECT featurecla AS kind FROM ne_10m_admin_0_boundary_lines_land", []),
    "state_line": ("ne_10m_admin_1_states_provinces_lines",
                   "SELECT adm0_a3 AS country FROM ne_10m_admin_1_states_provinces_lines WHERE adm0_a3 IN ('USA', 'MEX')", []),
    "county_line": ("cb_2023_us_county_500k",
                    "SELECT NAME AS name FROM cb_2023_us_county_500k WHERE STATEFP IN ('04', '35', '48')",
                    ["-nlt", "MULTILINESTRING"]),
    "lake": ("ne_10m_lakes_north_america", "SELECT name FROM ne_10m_lakes_north_america", []),
    "railroad": ("ne_10m_railroads_north_america", "SELECT scalerank FROM ne_10m_railroads_north_america", []),
    "road": ("ne_10m_roads", "SELECT type, scalerank FROM ne_10m_roads WHERE continent = 'North America'", []),
}


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        args = []
        for layer, (name, sql, extra) in LAYERS.items():
            dst = Path(tmp) / f"{layer}.geojson"
            subprocess.run(
                ["ogr2ogr", "-f", "GeoJSON", "-spat", *BOX, "-clipsrc", "spat_extent", "-t_srs", "EPSG:4326",
                 "-lco", "COORDINATE_PRECISION=5", "-dialect", "OGRSQL", "-sql", sql, *extra,
                 str(dst), str(SRC / name / f"{name}.shp")],
                check=True,
            )
            args += ["-L", f"{layer}:{dst.name}"]
        for layer, path in write_layers(BOX, Path(tmp)).items():
            args += ["-L", f"{layer}:{path.name}"]
        # NHD natural streams (ftype 460), one file per HU8 watershed, merged into one "creek" layer.
        for i, shp in enumerate(NHD / f"NHD_H_{huc}_HU8_Shape" / "Shape" / "NHDFlowline.shp" for huc in CREEK_HU8):
            dst = Path(tmp) / f"creek-{i}.geojson"
            subprocess.run(
                ["ogr2ogr", "-f", "GeoJSON", "-spat", *BOX, "-clipsrc", "spat_extent", "-t_srs", "EPSG:4326",
                 "-lco", "COORDINATE_PRECISION=5", "-dialect", "OGRSQL", "-dim", "XY",
                 "-sql", "SELECT gnis_name AS name, fcode FROM NHDFlowline WHERE ftype = 460", str(dst), str(shp)],
                check=True,
            )
            args += ["-L", f"creek:{dst.name}"]
        # Run inside the temporary folder with relative names: tippecanoe records its command line
        # in the archive's metadata, and the archive is published.
        subprocess.run(
            ["tippecanoe", "-q", "-f", "-o", "base.pmtiles", "-Z4", "-z11", "--no-tile-size-limit",
             "-n", "The Crossing: base", "-N", "Natural Earth, Census, NHD and INEGI layers for the literary map",
             "-A", "Rivers: Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0; USGS National Hydrography Dataset",
             "-j", '{"creek": [">=", "$zoom", 9]}',
             "--detect-shared-borders", "--simplification=4", *args],
            check=True, cwd=tmp,
        )
        shutil.move(Path(tmp) / "base.pmtiles", OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
