"""Build tiles/out/base.pmtiles: the literary basemap's vector layers.

Run from the repo root: uv run --project pipeline python -m tiles.build_base
Reads Natural Earth 10m and US Census cartographic boundary files from private/cache/basemap/ (crossing.basemap),
USGS NHD flowlines from private/cache/hydro/nhd/ and INEGI's river network from private/cache/hydro/inegi/
(crossing.hydro; docs/data-sources.md has the download list), clips them to the story box, and tiles them with
tippecanoe at BASE_ZOOMS. Both stream networks are read once, then drawn three ways: the named rivers
(tiles/rivers.py), the creeks, both countries' smaller streams shown by Strahler order and zoom (tiles/creeks.py),
and, from INEGI's water bodies, Mexico's lakes (tiles/lakes.py).
"""

import shutil
import tempfile
from pathlib import Path

from crossing import basemap, hydro
from crossing.paths import STORY_BOX_PADDED, TILES_OUT
from crossing.tiling import tippecanoe
from crossing.vector import ogr2geojson
from tiles import BASE_ZOOMS, creeks, lakes, rivers

OUT = TILES_OUT / "base.pmtiles"
# Shown in the map's attribution; the Credits page and data/README.md list the same sources.
ATTRIBUTION = ("Rivers, creeks and lakes in Mexico: Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0; "
               "US streams: USGS National Hydrography Dataset courtesy of the U.S. Geological Survey; "
               "county lines courtesy of the U.S. Census Bureau (cartographic boundary files); Made with Natural Earth")


def write_layers(tmp: Path) -> dict[str, Path]:
    """Every layer of the archive as GeoJSON in tmp, by layer name."""
    box = STORY_BOX_PADDED
    layers = {}
    for layer, (name, sql, extra) in basemap.LAYERS.items():
        layers[layer] = ogr2geojson(basemap.shapefile(name), sql, box, tmp / f"{layer}.geojson",
                                    extra=("-clipsrc", "spat_extent", "-lco", "COORDINATE_PRECISION=5", *extra))
    streams = hydro.load(box, tmp)
    mexico = basemap.mexico(box, tmp)
    river_layers = rivers.write_layers(streams, box, tmp)
    layers |= river_layers
    # Each creek carries its own first zoom (creeks.MIN_ZOOM), so no layer-wide filter is needed.
    layers["creek"] = creeks.write_layer(streams, mexico, tmp, list(river_layers.values()))
    layers["lake"] = lakes.write_layer(box, mexico, tmp)
    return layers


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        layers = write_layers(tmp)
        tippecanoe(tmp, "base.pmtiles", [(layer, path.name) for layer, path in layers.items()], zooms=BASE_ZOOMS,
                   name="The Crossing: base",
                   description="Natural Earth, Census, NHD and INEGI layers for the literary map",
                   attribution=ATTRIBUTION, extra=("--detect-shared-borders", "--simplification=4"))
        shutil.move(tmp / "base.pmtiles", OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
