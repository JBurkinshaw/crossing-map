"""Build the relief archives in tiles/out/ (decision 0016; zoom 12 density, design 5.2).

Run from the repo root, after crossing.hachures:
    uv run --project pipeline python -m tiles.build_relief

From private/cache/relief/production/, three archives so each stays under 100 MB (design 5.2), and a reader who
stays zoomed out never fetches the dense strokes:
  relief.pmtiles        coarse  hachures from the 90 m DEM, outside the journeys corridor, zoom 10-12
                        fine    short hachure strokes from the 30 m DEM, inside the corridor, zoom 10-12
  relief-dense.pmtiles  dense   the fine strokes closer together, for zoom 12 and up
  contours.pmtiles      contour 50 m contours (`Ele`, metres), zoom 10-12
The map over-zooms each to 13. Hachures carry `Slope`, `Aspect` and `Rand`; crossing.hachures describes them.
"""

import shutil

from crossing.hachures import ATTRIBUTION
from crossing.hachures import OUT as SRC
from crossing.paths import REPO, TILES_OUT
from crossing.tiling import tippecanoe

# archive: (name, zooms, layers)
ARCHIVES = {
    "relief": ("The Crossing: hachures", (10, 12), ["coarse", "fine"]),
    "relief-dense": ("The Crossing: dense hachures", (12, 12), ["dense"]),
    "contours": ("The Crossing: contours", (10, 12), ["contour"]),
}


def main() -> None:
    TILES_OUT.mkdir(parents=True, exist_ok=True)
    for archive, (title, zooms, layers) in ARCHIVES.items():
        # No simplification: hachures are short, and simplifying bends them off the fall line.
        # MapLibre shows the attribution on the map; decision 0011 also wants it on the Credits page.
        tippecanoe(SRC, f"{archive}.pmtiles", [(layer, f"{layer}.geojson") for layer in layers], zooms=zooms,
                   name=title, description="From Copernicus GLO-30 (decision 0016)", attribution=ATTRIBUTION,
                   extra=("--no-line-simplification", "--no-feature-limit"))
        out = TILES_OUT / f"{archive}.pmtiles"
        shutil.move(SRC / f"{archive}.pmtiles", out)
        print(f"Wrote {out.relative_to(REPO)} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
