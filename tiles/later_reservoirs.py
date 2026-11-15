"""Draft pipeline/seeds/later_reservoirs.csv: the base map's lakes that are reservoirs, with each dam's year.

Run by hand, not by tiles.build_base: `uv run --project pipeline python -m tiles.later_reservoirs`. Reads the Global
Dam Watch database v1.0 (Lehner et al. 2024, figshare 10.6084/m9.figshare.25988293, CC BY 4.0), which carries GRanD
v1.3, cached as private/cache/reservoirs/GDW_v1_0_shp.zip, and the lakes tiles.lakes would draw in the story box.

A lake is a GDW reservoir's when at least MIN_OVERLAP of its area lies in that reservoir's polygon (areas in an Albers
equal-area projection on WGS 84, standard parallels 27° and 35° N). Each such lake gets a row: the dam's name, river,
year (GDW's YEAR_DAM and its source), and a point inside the lake, which is what tiles.lakes matches on. The drafted
action is "drop" for a dam finished after BOOK_LAST_YEAR and "keep" otherwise; a dam that only regulates a natural
lake (GDW's LAKE_CTRL) or has no year is kept and noted for review. The action and note of a row already in the file
are left as they are, so hand edits survive a rerun (decision 0031).
"""

import csv
import tempfile
from pathlib import Path

import numpy as np
import pyproj
import shapely
from shapely.geometry import shape

from crossing import basemap
from crossing.paths import CACHE, STORY_BOX_PADDED
from crossing.vector import read
from tiles.lakes import LATER_RESERVOIRS, lake_features

GDW = CACHE / "reservoirs" / "GDW_v1_0_shp.zip"
GDW_LAYER = "GDW_v1_0_shp/GDW_reservoirs_v1_0"
# The book's last year (decision 0028: the book runs from 1939 to 1945).
BOOK_LAST_YEAR = 1945
MIN_OVERLAP = 0.5
FIELDS = ["gdw_id", "name", "river", "country", "state", "year_dam", "year_source", "lake_km2", "lon", "lat",
          "action", "note"]
ALBERS = pyproj.Transformer.from_crs(
    "EPSG:4326", "+proj=aea +lat_1=27 +lat_2=35 +lat_0=31 +lon_0=-108.5 +datum=WGS84 +units=m", always_xy=True)


def km2(g: shapely.Geometry) -> float:
    return shapely.transform(g, lambda xy: np.column_stack(ALBERS.transform(xy[:, 0], xy[:, 1]))).area / 1e6


def drafted(p: dict) -> tuple[str, str]:
    """The drafted action and note for a GDW reservoir's properties."""
    year = p["YEAR_DAM"] if p["YEAR_DAM"] and p["YEAR_DAM"] > 0 else None
    if p["LAKE_CTRL"]:
        return "keep", f"Review: a dam on a natural lake ({p['LAKE_CTRL']})."
    if year is None:
        return "keep", "Review: GDW gives no year."
    if year > BOOK_LAST_YEAR:
        return "drop", f"Built {year}, after the book."
    return "keep", f"Built {year}, by the book's last year."


def main() -> None:
    old = {}
    if LATER_RESERVOIRS.exists():
        with LATER_RESERVOIRS.open(newline="") as f:
            old = {(r["gdw_id"], r["lon"], r["lat"]): r for r in csv.DictReader(f)}
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        mexico = basemap.mexico(STORY_BOX_PADDED, tmp)
        lakes = [shape(f["geometry"]) for f in lake_features(STORY_BOX_PADDED, mexico, tmp)]
        sql = (f"SELECT GDW_ID, RES_NAME, DAM_NAME, RIVER, COUNTRY, ADMIN_UNIT, YEAR_DAM, YEAR_SRC, LAKE_CTRL "
               f"FROM {Path(GDW_LAYER).name}")
        reservoirs = [(f["properties"], shape(f["geometry"]).buffer(0))
                      for f in read(f"/vsizip/{GDW}/{GDW_LAYER}.shp", sql, STORY_BOX_PADDED, tmp / "gdw.geojson")]
    tree = shapely.STRtree([g for _, g in reservoirs])
    rows = []
    for lake in lakes:
        area = km2(lake)
        overlaps = ((km2(lake.intersection(reservoirs[i][1])), i) for i in tree.query(lake, "intersects"))
        best = max(overlaps, default=None)
        if not best or best[0] < MIN_OVERLAP * area:
            continue
        p, g = reservoirs[best[1]]
        at = lake.intersection(g).point_on_surface()
        row = {"gdw_id": str(p["GDW_ID"]), "name": p["RES_NAME"] or p["DAM_NAME"] or "", "river": p["RIVER"] or "",
               "country": p["COUNTRY"], "state": p["ADMIN_UNIT"] or "",
               "year_dam": p["YEAR_DAM"] if p["YEAR_DAM"] and p["YEAR_DAM"] > 0 else "",
               "year_source": p["YEAR_SRC"] or "", "lake_km2": f"{area:.2f}",
               "lon": f"{at.x:.5f}", "lat": f"{at.y:.5f}"}
        kept = old.get((row["gdw_id"], row["lon"], row["lat"]))
        row["action"], row["note"] = (kept["action"], kept["note"]) if kept else drafted(p)
        rows.append(row)
    rows.sort(key=lambda r: (r["action"], -float(r["lake_km2"])))
    # A row whose lake no longer matches (new lake data, or a moved point) would lose its hand edit.
    for key in old.keys() - {(r["gdw_id"], r["lon"], r["lat"]) for r in rows}:
        print(f"Warning: row {key} no longer matches a lake and is dropped; its note was: {old[key]['note']}")
    with LATER_RESERVOIRS.open("w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    drops = sum(r["action"] == "drop" for r in rows)
    print(f"Wrote {LATER_RESERVOIRS}: {len(rows)} lakes are GDW reservoirs, {drops} drafted to drop")


if __name__ == "__main__":
    main()
