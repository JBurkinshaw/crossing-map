"""Build the vignette anchors (plan section 10) from pipeline/seeds/vignettes.csv.

Run from the repo root, after crossing.build_story: uv run --project pipeline python -m crossing.build_vignettes
Reads the seed and data/stops.geojson and data/places.geojson (each vignette's `ref` is a stop or place id).
Writes data/vignettes.geojson: one Point per vignette, at its anchor in empty country near the thing it stands
for, and a hairline leader (a LineString, kind `vignette-leader`) from the anchor to the thing itself where the
seed asks for one, which it does only for real, located sites.

Each anchor's reasoning gets its distance and bearing from the thing it stands for and its distance from the
nearest stop or place, measured on the WGS 84 ellipsoid with pyproj. An anchor closer than CLEAR_KM to any stop
or place stops the build: at zoom 9 that is about 30 px, under half a drawing's width.
"""

import csv
import json
from pathlib import Path

from pyproj import Geod

REPO = Path(__file__).resolve().parents[3]
SEED = REPO / "pipeline" / "seeds" / "vignettes.csv"
DATA = REPO / "data"
GEOD = Geod(ellps="WGS84")
CLEAR_KM = 8


def r5(x: float) -> float:
    return round(x, 5)


def main() -> None:
    points = {}
    for name in ("stops", "places"):
        for f in json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))["features"]:
            points[f["properties"]["id"]] = (f["properties"]["name"], *f["geometry"]["coordinates"])

    features, problems = [], []
    with SEED.open(encoding="utf-8", newline="") as f:
        seeds = list(csv.DictReader(f))
    for s in seeds:
        lon, lat = float(s["lon"]), float(s["lat"])
        ref_name, ref_lon, ref_lat = points[s["ref"]]
        azimuth, _, dist = GEOD.inv(ref_lon, ref_lat, lon, lat)
        nearest = min(((GEOD.inv(x, y, lon, lat)[2], n) for n, x, y in points.values()))
        if nearest[0] < CLEAR_KM * 1000:
            problems.append(f"{s['id']}: {nearest[0] / 1000:.1f} km from {nearest[1]}, under {CLEAR_KM} km")
        measured = (f" The anchor is {dist / 1000:.0f} km from {ref_name}, bearing {azimuth % 360:.0f} degrees; the nearest "
                    f"stop or place, {nearest[1]}, is {nearest[0] / 1000:.0f} km away (pyproj, WGS 84).")
        props = dict(
            id=f"vignette-{s['id']}", name=s["name"], kind="vignette", stands_for=s["stands_for"], place_ref=s["ref"],
            part=int(s["first_seen"][0]), episode=s["first_seen"], first_seen=s["first_seen"],
            certainty="approximate", method="hand-drawn", source="this-site", source_id=None, source_licence="CC BY 4.0",
            note_safe=s["note"], reasoning=s["reasoning"] + measured,
            vignette=f"vignette-{s['id']}", min_zoom=float(s["min_zoom"]), max_zoom=float(s["max_zoom"]),
            priority=int(s["priority"]),
        )
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [r5(lon), r5(lat)]}, "properties": props})
        if s["leader"] == "yes":
            leader = props | {"id": f"vignette-{s['id']}-leader", "kind": "vignette-leader",
                              "reasoning": f"A hairline from the drawing to {ref_name}, a located site."}
            features.append({"type": "Feature", "properties": leader, "geometry": {
                "type": "LineString", "coordinates": [[r5(lon), r5(lat)], [r5(ref_lon), r5(ref_lat)]]}})
    if problems:
        raise SystemExit("Anchors too close to a stop or place:\n  " + "\n  ".join(problems))
    path = DATA / "vignettes.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"vignettes.geojson: {len(seeds)} vignettes, {len(features) - len(seeds)} leaders")


if __name__ == "__main__":
    main()
