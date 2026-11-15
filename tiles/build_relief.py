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

With `--style wheeler [--src private/cache/relief/wheeler-test]`, it packs the Wheeler test build of
crossing.wheeler_hachures instead, into tiles/out/lab-wheeler-hachures.pmtiles (layers `hachure` and `rim`, zoom
10-12), for the lab only; the production archives are left alone.

With `--style wheeler --region corridor [--src private/cache/relief/wheeler]`, it packs the Wheeler corridor build
for the site (decision 0024), split by zoom so each archive stays under 100 MB:
  relief-wheeler.pmtiles     zoom 10-11  coarse (the production coarse strokes, outside the corridor), hachure, rim
  relief-wheeler-12.pmtiles  zoom 12     the same layers
The coarse strokes are copied in so the site's Wheeler set needs no other hachure archive. The production archives
are left alone, so site/src/map/relief.ts can switch back to them (HACHURE_SET).
"""

import argparse
import shutil
from pathlib import Path

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


WHEELER_SRC = SRC.parent / "wheeler-test"
WHEELER_ARCHIVE = "lab-wheeler-hachures"
CORRIDOR_SRC = SRC.parent / "wheeler"
# archive: zooms. The strokes are the same at every zoom (no simplification), so each zoom costs about the same.
CORRIDOR_ARCHIVES = {"relief-wheeler": (10, 11), "relief-wheeler-12": (12, 12)}
LIMIT_MB = 100


def wheeler(src: Path) -> None:
    """The Wheeler test build's strokes and rim wedges in one archive. The wedges are tiny triangles, so
    tippecanoe is told not to merge or drop small polygons."""
    tippecanoe(src, f"{WHEELER_ARCHIVE}.pmtiles", [("hachure", "hachure.geojson"), ("rim", "rim.geojson")],
               zooms=(10, 12), name="The Crossing: Wheeler hachures (test area)",
               description="From Copernicus GLO-30 (review/stage-9/wheeler-hachures)", attribution=ATTRIBUTION,
               extra=("--no-line-simplification", "--no-feature-limit", "--no-tiny-polygon-reduction"))
    out = TILES_OUT / f"{WHEELER_ARCHIVE}.pmtiles"
    shutil.move(src / f"{WHEELER_ARCHIVE}.pmtiles", out)
    print(f"Wrote {out.relative_to(REPO)} ({out.stat().st_size / 1e6:.1f} MB)")


def wheeler_corridor(src: Path) -> None:
    """The Wheeler corridor build's strokes and rim wedges, with the production coarse strokes, in CORRIDOR_ARCHIVES."""
    shutil.copy2(SRC / "coarse.geojson", src / "coarse.geojson")
    layers = [("coarse", "coarse.geojson"), ("hachure", "hachure.geojson"), ("rim", "rim.geojson")]
    for archive, zooms in CORRIDOR_ARCHIVES.items():
        tippecanoe(src, f"{archive}.pmtiles", layers, zooms=zooms, name="The Crossing: Wheeler hachures",
                   description="From Copernicus GLO-30 (decision 0024)", attribution=ATTRIBUTION,
                   extra=("--no-line-simplification", "--no-feature-limit", "--no-tiny-polygon-reduction"))
        out = TILES_OUT / f"{archive}.pmtiles"
        shutil.move(src / f"{archive}.pmtiles", out)
        size = out.stat().st_size / 1e6
        warning = "; over the limit, split it" if size >= LIMIT_MB else ""
        print(f"Wrote {out.relative_to(REPO)} ({size:.1f} MB){warning}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=["production", "wheeler"], default="production")
    ap.add_argument("--region", choices=["corridor"],
                    help="the Wheeler corridor build, for the site; --style wheeler only")
    ap.add_argument("--src", type=Path, help="the Wheeler build's folder; --style wheeler only (default: "
                    f"{WHEELER_SRC.relative_to(REPO)}, or {CORRIDOR_SRC.relative_to(REPO)} with --region corridor)")
    a = ap.parse_args()
    TILES_OUT.mkdir(parents=True, exist_ok=True)
    if a.style == "wheeler":
        if a.region:
            wheeler_corridor((a.src or CORRIDOR_SRC).resolve())
        else:
            wheeler((a.src or WHEELER_SRC).resolve())
        return
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
