"""Build Part I story layers from the seeds, gazetteer picks, and stops.

Run from the repo root: uv run --project pipeline python -m crossing.build_part1
Reads pipeline/seeds/part1*.csv and review/stage-1/places.csv.
Writes data/places.geojson, data/stops.geojson, data/areas.geojson, data/journeys.geojson.
"""

import csv
import json
import math
import subprocess
from pathlib import Path

from pyproj import Geod
from shapely import line_merge
from shapely.geometry import MultiLineString, Point, shape
from shapely.ops import substring

REPO = Path(__file__).resolve().parents[3]
SEEDS = REPO / "pipeline" / "seeds"
DATA = REPO / "data"
GEOD = Geod(ellps="WGS84")
LICENCE = {"wikidata": "CC0", "gnis": "Public domain", "geonames": "CC BY 4.0", "this-site": "CC BY 4.0"}
# A pin for a long or wide feature stands in for it; a pin for a town or pass is the thing itself.
LOCATED_KINDS = {"town", "city", "locale", "county", "pass", "summit"}
CHARACTERS = {"J1": ["wolf"], "J2": ["billy", "wolf"]}


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def r5(x: float) -> float:
    return round(x, 5)


def point(lat: float, lon: float) -> dict:
    return {"type": "Point", "coordinates": [r5(lon), r5(lat)]}


def circle(lat: float, lon: float, radius_km: float) -> dict:
    n = 48
    lons, lats, _ = GEOD.fwd([lon] * n, [lat] * n, [i * 360 / n for i in range(n)], [radius_km * 1000] * n)
    ring = [[r5(x), r5(y)] for x, y in zip(lons, lats)]
    # RFC 7946: exterior rings run anticlockwise; fwd steps clockwise by azimuth.
    ring.reverse()
    return {"type": "Polygon", "coordinates": [ring + [ring[0]]]}


def curve(a: tuple[float, float], b: tuple[float, float], side: int) -> list[list[float]]:
    """A gentle quadratic Bézier from a to b (lon, lat), bowed 10% of its length to one side."""
    n = 16
    k = math.cos(math.radians((a[1] + b[1]) / 2))  # shrink longitude so the bow is square to the line
    dx, dy = (b[0] - a[0]) * k, b[1] - a[1]
    cx = (a[0] + b[0]) / 2 + side * -dy * 0.1 / k
    cy = (a[1] + b[1]) / 2 + side * dx * 0.1
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * cx + t**2 * b[0]
        y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * cy + t**2 * b[1]
        pts.append([r5(x), r5(y)])
    return pts


def snapped(snap: dict, a: tuple[float, float], b: tuple[float, float]) -> list[list[float]]:
    """The stretch of a named NHD line between stops a and b (lon, lat), joined to both stops."""
    sql = f"SELECT * FROM NHDFlowline WHERE gnis_name = '{snap['feature_name']}'"
    out = subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-dim", "XY", "-sql", sql,
                          "/vsistdout/", str(REPO / snap["shapefile"])], check=True, capture_output=True, text=True).stdout
    lines = [shape(f["geometry"]) for f in json.loads(out)["features"]]
    merged = line_merge(MultiLineString([g for line in lines for g in getattr(line, "geoms", [line])]))
    # Use the merged piece that passes closest to the two stops together.
    pieces = list(getattr(merged, "geoms", [merged]))
    line = min(pieces, key=lambda g: g.distance(Point(a)) + g.distance(Point(b)))
    da, db = line.project(Point(a)), line.project(Point(b))
    part = substring(line, min(da, db), max(da, db))
    coords = list(part.coords) if da <= db else list(part.coords)[::-1]
    return [[r5(a[0]), r5(a[1])]] + [[r5(x), r5(y)] for x, y in coords] + [[r5(b[0]), r5(b[1])]]


def feature(geometry: dict, **props) -> dict:
    return {"type": "Feature", "geometry": geometry, "properties": props}


def write(name: str, features: list[dict]) -> None:
    path = DATA / name
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{name}: {len(features)} features")


def main() -> None:
    # Part I places, then the context towns the book never names (shown at every reading position).
    seeds = {s["id"]: s for s in rows(SEEDS / "part1.csv") + rows(SEEDS / "context.csv")}
    picks = {p["id"]: p for p in rows(REPO / "review" / "stage-1" / "places.csv") + rows(REPO / "review" / "stage-2" / "context-places.csv")}
    overrides = {o["id"]: o for o in rows(SEEDS / "part1-place-overrides.csv")}

    places, pins = [], {}
    for sid, seed in seeds.items():
        pick, override = picks[sid], overrides.get(sid)
        if override and override["action"] == "exclude":
            continue
        src = override if override else pick
        if not src["lat"]:
            print(f"skipped {sid}: no candidate")
            continue
        lat, lon = float(src["lat"]), float(src["lon"])
        pins[sid] = (lat, lon, src["source"], src["source_id"])
        reasoning = override["reasoning"] if override else (
            "Provisional pick from several candidates, awaiting review." if pick["status"] == "review" and seed["role"] != "context" else None)
        journeys = [j for j in seed["journey"].split(";") if j]
        places.append(feature(
            point(lat, lon),
            id=f"place-{sid}", name=seed["name"], kind=seed["kind"], role=seed["role"],
            characters=[c for c in seed["characters"].split(";") if c],
            journey=journeys[0] if journeys else None, part=int(seed["first_seen"][0]), episode=seed["first_seen"], first_seen=seed["first_seen"],
            certainty="located" if seed["kind"] in LOCATED_KINDS else "approximate",
            method="gazetteer", source=src["source"], source_id=src["source_id"],
            source_licence=LICENCE[src["source"]], note_safe="", reasoning=reasoning,
        ))
    write("places.geojson", places)

    stops, areas, journeys = [], [], []
    by_journey: dict[str, list[dict]] = {}
    for s in rows(SEEDS / "part1-stops.csv"):
        place = s["place"]
        if s["lat"]:
            lat, lon = float(s["lat"]), float(s["lon"])
            source, source_id = "this-site", None
        else:
            lat, lon, source, source_id = pins[place]
        method = "computed" if s["certainty"] == "located" and not place else ("gazetteer" if source != "this-site" else "schematic")
        props = dict(
            id=s["id"], name=s["name"], kind="stop", role="stop", characters=CHARACTERS[s["journey"]],
            journey=s["journey"], sequence=int(s["seq"]), place_ref=f"place-{place}" if place else None,
            part=int(s["first_seen"][0]), episode=s["first_seen"], first_seen=s["first_seen"], certainty=s["certainty"],
            uncertainty_m=float(s["radius_km"]) * 1000 if s["radius_km"] else None,
            method=method, source=source, source_id=source_id, source_licence=LICENCE[source],
            note_safe="", reasoning=s["reasoning"] or None,
        )
        stops.append(feature(point(lat, lon), **props))
        by_journey.setdefault(s["journey"], []).append(props | {"lat": lat, "lon": lon})
        if s["radius_km"]:
            area = props | {"id": s["id"].replace("j1-", "area-j1-").replace("j2-", "area-j2-"), "kind": "inferred-area",
                            "role": None, "sequence": None}
            areas.append(feature(circle(lat, lon, float(s["radius_km"])), **area))
    write("stops.geojson", stops)
    write("areas.geojson", areas)

    snaps = {(s["journey"], int(s["from_seq"])): s for s in rows(SEEDS / "part1-snaps.csv")}
    for jid, seq in by_journey.items():
        seq.sort(key=lambda p: p["sequence"])
        for i, (a, b) in enumerate(zip(seq, seq[1:]), start=1):
            snap = snaps.get((jid, a["sequence"]))
            if snap:
                coords = snapped(snap, (a["lon"], a["lat"]), (b["lon"], b["lat"]))
                how = dict(certainty="approximate", method="narrated-path", source="usgs-nhd",
                           source_licence="Public domain", reasoning=snap["reasoning"])
            else:
                coords = curve((a["lon"], a["lat"]), (b["lon"], b["lat"]), 1 if i % 2 else -1)
                how = dict(certainty="inferred", method="schematic", source="this-site", source_licence=LICENCE["this-site"],
                           reasoning="A gentle curve between consecutive stops; the book names no road or river for this stretch.")
            journeys.append(feature(
                {"type": "LineString", "coordinates": coords},
                id=f"{jid.lower()}-seg-{i:02d}", name=f"{a['name']} to {b['name']}", kind="route-segment",
                characters=CHARACTERS[jid], journey=jid, sequence=i, part=int(b["first_seen"][0]), episode=b["first_seen"],
                first_seen=b["first_seen"], note_safe="", **how,
            ))
    write("journeys.geojson", journeys)
    write_checklist(stops, places)


def write_checklist(stops: list[dict], places: list[dict]) -> None:
    """The stage 1 sign-off list: every feature, its evidence, and links to check it on imagery."""

    def links(f: dict) -> str:
        lon, lat = f["geometry"]["coordinates"]
        return (f"[OSM](https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=13/{lat}/{lon}) · "
                f"[satellite](https://www.google.com/maps/@{lat},{lon},13z/data=!3m1!1e3)")

    def provisional(p: dict) -> bool:
        return "Provisional" in (p.get("reasoning") or "")

    unsure = {f["properties"]["id"] for f in places if provisional(f["properties"])}

    def row(f: dict, label: str) -> str:
        p = f["properties"]
        source = p["source"] + (f" {p['source_id']}" if p.get("source_id") else "")
        flag = "**check**" if provisional(p) or p.get("place_ref") in unsure else ""
        return f"| [ ] | {label} | {p['name']} | {p['certainty']} | {source} | {links(f)} | {flag} |"

    lines = [
        "# Stage 1 place checklist",
        "",
        "Generated by `pipeline/src/crossing/build_part1.py`. Tick each row once the point sits where the book puts it.",
        "Rows marked **check** are provisional picks among several candidates. Reasoning for every stop is in the app's panel.",
        "",
        "| OK | # | Name | Certainty | Source | Look | |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in stops:
        lines.append(row(f, f"{f['properties']['journey']}.{f['properties']['sequence']}"))
    lines += ["", "## Places named in passing", "", "| OK | # | Name | Certainty | Source | Look | |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for f in places:
        if f["properties"]["role"] == "passing":
            lines.append(row(f, ""))
    path = REPO / "review" / "stage-1" / "checklist.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{path.relative_to(REPO)}: {len(stops)} stops")


if __name__ == "__main__":
    main()
