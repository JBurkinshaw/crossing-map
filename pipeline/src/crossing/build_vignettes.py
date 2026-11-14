"""Build the vignette anchors (design section 10) from pipeline/seeds/vignettes.csv.

Run from the repo root, after crossing.build_story: uv run --project pipeline python -m crossing.build_vignettes
Reads the seed and data/stops.geojson and data/places.geojson (each vignette's `ref` is a stop or place id).
Writes data/vignettes.geojson: one Point per vignette, on the thing it stands for, with the `side` the map draws
the drawing on (site/src/map/relief.ts), so it sits beside its pin at every zoom and never covers it. A seed row
with its own lon and lat stands for a place that is not one of the book's stops or places (the Trinity Site).
"""

import csv
import json

from crossing.build_story import r5, write
from crossing.paths import DATA, SEEDS

SEED = SEEDS / "vignettes.csv"
SIDES = {"n": "north", "ne": "north-east", "e": "east", "se": "south-east", "s": "south", "sw": "south-west",
         "w": "west", "nw": "north-west"}


def main() -> None:
    points = {}
    for name in ("stops", "places"):
        for f in json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))["features"]:
            points[f["properties"]["id"]] = (f["properties"]["name"], *f["geometry"]["coordinates"])

    features = []
    with SEED.open(encoding="utf-8", newline="") as f:
        seeds = list(csv.DictReader(f))
    for s in seeds:
        ref_name, lon, lat = points[s["ref"]]
        if s["lon"]:
            lon, lat = float(s["lon"]), float(s["lat"])
            where = "its own place"
        else:
            where = ref_name
        placed = (f"The drawing is set on the {SIDES[s['side']]} side of {where}, beside the pin rather than on it; "
                  "it is not to scale, and it shows roughly where the scene happens, not exactly.")
        props = dict(
            id=f"vignette-{s['id']}", name=s["name"], kind="vignette", stands_for=s["stands_for"], place_ref=s["ref"],
            part=int(s["first_seen"][0]), episode=s["first_seen"], first_seen=s["first_seen"],
            certainty="approximate", method="hand-drawn", source="this-site", source_id=None,
            source_licence="CC BY 4.0",
            note_safe=s["note"], reasoning=" ".join(x for x in (s["reasoning"], placed) if x),
            vignette=f"vignette-{s['id']}", side=s["side"], min_zoom=float(s["min_zoom"]),
            max_zoom=float(s["max_zoom"]), priority=int(s["priority"]), label=s["label"], credit=s["credit"],
        )
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [r5(lon), r5(lat)]},
                         "properties": props})
    write("vignettes.geojson", features)
    print(f"{len(features)} vignettes")


if __name__ == "__main__":
    main()
