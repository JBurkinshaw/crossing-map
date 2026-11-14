"""Build the story layers from the seeds in pipeline/seeds/.

Run from the repo root: uv run --project pipeline python -m crossing.build_story
Reads places.csv (every place the book names, plus context towns), place-picks.csv (crossing.gazetteer's picks),
place-overrides.csv (hand decisions, which win over a pick), stops.csv, snaps.csv and regions.geojson.
Writes data/places.geojson, data/stops.geojson, data/areas.geojson, data/journeys.geojson, data/elsewhere.json
(places outside the story box, listed in the panel rather than mapped) and the stage 4 sign-off checklists,
keeping any row already ticked.

A route segment follows the line its snap names, where the book names the road or river:
  nhd          a USGS NHD flowline by its GNIS name (shapefile, feature)
  tiger-road   a US Census TIGER road by its full name (shapefile, feature)
  ne-river     a Natural Earth river by name: the line the map itself draws for Mexican rivers
Elsewhere it is a gentle curve between the stops.
A segment's `travel` is its arriving stop's: empty for horseback, or foot, truck, car, bus, train or reported.
"""

import csv
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from pyproj import Geod
from shapely import line_merge
from shapely.geometry import LineString, MultiLineString, Point, shape
from shapely.ops import substring

from crossing.paths import DATA, REPO, SEEDS, STORY_BOX

GEOD = Geod(ellps="WGS84")
LICENCE = {"wikidata": "CC0", "gnis": "Public domain", "geonames": "CC BY 4.0", "this-site": "CC BY 4.0",
           "usgs-nhd": "Public domain", "census-tiger": "Public domain", "natural-earth": "Public domain"}
SNAP_SOURCES = {"nhd": "usgs-nhd", "tiger-road": "census-tiger", "ne-river": "natural-earth"}
# The widest gap bridged between pieces of a named line, in degrees (about 1 km).
GAP_DEG = 0.01
# The false dawn at the book's end (plan 2.4): the text names no place or event, but it is widely read as the
# Trinity test, so the map draws a reported line of sight from Billy's last stop towards the Trinity Site
# (Wikidata Q19842077), SIGHTLINE_KM long, rather than a point.
TRINITY = (-106.4754, 33.6773)
# The light comes in the book's last episode, after the night at the waystation (4-08).
FALSE_DAWN = "4-09"
SIGHTLINE_KM = 30
# The sign-off checklists still open: the stops and places first seen in these Parts. Places resolved through
# the gazetteer (place-picks.csv) were signed off in stage 1 and are not listed again.
CHECKLISTS = [
    {"parts": {"2"}, "title": "Stage 4, batch A (Part II) place checklist",
     "path": REPO / "review" / "stage-4" / "batch-a" / "checklist.md"},
    {"parts": {"3", "4"}, "title": "Stage 4, batch B (Parts III and IV) place checklist",
     "path": REPO / "review" / "stage-4" / "batch-b" / "checklist.md"},
]
# A pin for a long or wide feature stands in for it; a pin for a town or pass is the thing itself.
LOCATED_KINDS = {"town", "city", "locale", "county", "pass", "summit"}
CHARACTERS = {"J1": ["wolf"], "J2": ["billy", "wolf"], "J3": ["billy"], "J4": ["billy", "boyd"], "J5": ["billy"],
              "J6": ["boyd", "girl"], "J7": ["billy"]}


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
    ring = [[r5(x), r5(y)] for x, y in zip(lons, lats, strict=True)]
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


def named_lines(snap: dict) -> list:
    """The lines a snap names, in WGS 84: an NHD flowline, Natural Earth river or TIGER road by name.

    A road that crosses a county line names one TIGER file per county, separated by semicolons. A road whose
    stretches carry different names in TIGER (a county road that changes number) names each, also separated by
    semicolons.
    """
    field = {"nhd": "gnis_name", "ne-river": "name", "tiger-road": "FULLNAME"}[snap["source"]]
    # OGR SQL escapes a quote by doubling it.
    names = ", ".join("'{}'".format(n.replace("'", "''")) for n in snap["feature"].split(";"))
    lines = []
    for name in snap["shapefile"].split(";"):
        path = REPO / name
        layer = path.name.removesuffix(".zip").removesuffix(".shp")
        sql = f"SELECT * FROM {'NHDFlowline' if snap['source'] == 'nhd' else layer} WHERE {field} IN ({names})"
        target = f"/vsizip/{path}" if path.suffix == ".zip" else str(path)
        out = subprocess.run(["ogr2ogr", "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-dim", "XY", "-sql", sql,
                              "/vsistdout/", target],
                             check=True, capture_output=True, text=True).stdout
        lines += [shape(f["geometry"]) for f in json.loads(out)["features"]]
    return lines


def snapped(snap: dict, a: tuple[float, float], b: tuple[float, float]) -> list[list[float]]:
    """The stretch of the snap's line between stops a and b (lon, lat), joined to both stops."""
    lines = [g for line in named_lines(snap) for g in getattr(line, "geoms", [line])]
    # TIGER breaks some roads with gaps of a few hundred metres: join loose ends of different lines in pairs,
    # closest first, if they are within about a kilometre.
    ends = [(i, c) for i, g in enumerate(lines) for c in (g.coords[0], g.coords[-1])]
    loose = [(i, c) for i, c in ends if sum(c == d for _, d in ends) == 1]
    pairs = sorted((Point(c).distance(Point(d)), c, d)
                   for k, (i, c) in enumerate(loose) for j, d in loose[k + 1:] if j != i)
    used, bridges = set(), []
    for dist, c, d in pairs:
        if dist < GAP_DEG and c not in used and d not in used:
            used |= {c, d}
            bridges.append(LineString([c, d]))
    merged = line_merge(MultiLineString(lines + bridges))
    # Use the merged piece that passes closest to the two stops together.
    pieces = list(getattr(merged, "geoms", [merged]))
    line = min(pieces, key=lambda g: g.distance(Point(a)) + g.distance(Point(b)))
    da, db = line.project(Point(a)), line.project(Point(b))
    part = substring(line, min(da, db), max(da, db))
    coords = list(part.coords) if da <= db else list(part.coords)[::-1]
    return [[r5(a[0]), r5(a[1])]] + [[r5(x), r5(y)] for x, y in coords] + [[r5(b[0]), r5(b[1])]]


def feature(geometry: dict, **props) -> dict:
    return {"type": "Feature", "geometry": geometry, "properties": props}


def write_json(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def write(name: str, features: list[dict]) -> None:
    write_json(DATA / name, {"type": "FeatureCollection", "features": features})
    print(f"{name}: {len(features)} features")


def in_box(lat: float, lon: float) -> bool:
    return STORY_BOX[0] <= lon <= STORY_BOX[2] and STORY_BOX[1] <= lat <= STORY_BOX[3]


def build_places(picks: dict[str, dict]) -> tuple[list[dict], dict[str, tuple], list[dict]]:
    """Each place's pin: its override when there is one ("use", "exclude" or "unresolved"), else its gazetteer pick.

    Returns the place features, the pins by seed id (for stops at a place), and the places outside the story box.
    """
    overrides = {o["id"]: o for o in rows(SEEDS / "place-overrides.csv")}
    places, pins, elsewhere, unresolved = [], {}, [], []
    for seed in rows(SEEDS / "places.csv"):
        sid = seed["id"]
        override, pick = overrides.get(sid), picks.get(sid)
        if override:
            if override["action"] == "unresolved":
                unresolved.append(sid)
            if override["action"] != "use":
                continue
            src = override
        elif pick:
            src = pick
        else:
            sys.exit(f"{sid}: no pick in place-picks.csv and no override in place-overrides.csv")
        if not src["lat"]:
            print(f"skipped {sid}: no candidate")
            continue
        lat, lon = float(src["lat"]), float(src["lon"])
        if not in_box(lat, lon):
            elsewhere.append({"id": sid, "name": seed["name"], "first_seen": seed["first_seen"], "role": seed["role"]})
            continue
        pins[sid] = (lat, lon, src["source"], src["source_id"])
        provisional = pick and pick["status"] == "review" and seed["role"] != "context"
        reasoning = override["reasoning"] if override else (
            "Provisional pick from several candidates, awaiting review." if provisional else None)
        journeys = [j for j in seed["journey"].split(";") if j]
        # The book's own spellings, where they differ from the name, so translations can find the place in the text.
        in_text = {"name_in_text": seed["text_names"]} if seed["text_names"] else {}
        places.append(feature(
            point(lat, lon),
            id=f"place-{sid}", name=seed["name"], **in_text, kind=seed["kind"], role=seed["role"],
            characters=[c for c in seed["characters"].split(";") if c],
            journey=journeys[0] if journeys else None, part=int(seed["first_seen"][0]), episode=seed["first_seen"],
            first_seen=seed["first_seen"],
            certainty="located" if seed["kind"] in LOCATED_KINDS else "approximate",
            method="gazetteer", source=src["source"], source_id=src["source_id"],
            source_licence=LICENCE[src["source"]], note_safe="", reasoning=reasoning,
        ))
    if unresolved:
        print(f"{len(unresolved)} places left unresolved in place-overrides.csv: {', '.join(unresolved)}")
    return places, pins, sorted(elsewhere, key=lambda e: e["first_seen"])


def build_stops(pins: dict[str, tuple]) -> tuple[list[dict], list[dict], dict[str, list[dict]]]:
    """The stops, the inferred area around each stop with a radius, and each journey's stops for the routes."""
    stops, areas = [], []
    by_journey: dict[str, list[dict]] = {}
    # The drafted outlines (crossing.area_drafts, decision 0020); a stop without one keeps its circle.
    path = SEEDS / "areas.geojson"
    drafts = {f["properties"]["id"]: f for f in json.loads(path.read_text(encoding="utf-8"))["features"]} \
        if path.exists() else {}
    for s in rows(SEEDS / "stops.csv"):
        place = s["place"]
        if s["lat"]:
            lat, lon = float(s["lat"]), float(s["lon"])
            source, source_id = "this-site", None
        elif place in pins:
            lat, lon, source, source_id = pins[place]
        else:
            sys.exit(f"stop {s['id']}: no coordinates and place {place!r} has no pin")
        if s["certainty"] == "located" and not place:
            method = "computed"
        else:
            method = "gazetteer" if source != "this-site" else "schematic"
        props = dict(
            id=s["id"], name=s["name"], kind="stop", role="stop", characters=CHARACTERS[s["journey"]],
            journey=s["journey"], sequence=int(s["seq"]), place_ref=f"place-{place}" if place else None,
            part=int(s["first_seen"][0]), episode=s["first_seen"], first_seen=s["first_seen"], certainty=s["certainty"],
            uncertainty_m=float(s["radius_km"]) * 1000 if s["radius_km"] else None,
            method=method, source=source, source_id=source_id, source_licence=LICENCE[source],
            note_safe="", reasoning=s["reasoning"] or None,
        )
        stops.append(feature(point(lat, lon), **props))
        by_journey.setdefault(s["journey"], []).append(props | {"lat": lat, "lon": lon, "travel": s["travel"] or None})
        if s["radius_km"]:
            area = props | {"id": f"area-{s['id']}", "kind": "inferred-area",
                            "role": None, "sequence": None}
            ring = circle(lat, lon, float(s["radius_km"]))
            draft = drafts.get(area["id"])
            # A "kept" draft is the circle itself: nothing in the evidence cut it.
            if draft is None or draft["properties"]["draft_confidence"] == "kept":
                areas.append(feature(ring, **area, outline_rule=None, straight_road=False))
                continue
            # A draft is the circle cut down, so one reaching outside it was drafted around an older pin or radius.
            if not shape(draft["geometry"]).difference(shape(ring).buffer(0.002)).is_empty:
                sys.exit(f"{area['id']}: the draft in areas.geojson lies outside the stop's circle; "
                         "rerun crossing.area_drafts --force")
            areas.append(feature(draft["geometry"], **(area | {"method": "computed"}),
                                 outline_rule=draft["properties"]["draft_rule"],
                                 straight_road=draft["properties"]["straight_road"]))
    return stops, areas, by_journey


def regions() -> list[dict]:
    """The named regions, drafted by crossing.regions and checked by hand (decision 0008)."""
    out = []
    path = SEEDS / "regions.geojson"
    if not path.exists():  # a first build: crossing.regions drafts them from the places this build writes
        print(f"no {path.name} yet: run crossing.regions, then build again")
        return out
    for f in json.loads(path.read_text(encoding="utf-8"))["features"]:
        r = f["properties"]
        out.append(feature(f["geometry"], id=r["id"], name=r["name"], kind="region", role=None, characters=[],
                           journey=None, sequence=None, place_ref=f"place-{r['place']}", part=int(r["first_seen"][0]),
                           episode=r["first_seen"],
                           first_seen=r["first_seen"], certainty="approximate", uncertainty_m=None, method="computed",
                           source="this-site", source_id=None, source_licence=LICENCE["this-site"], note_safe="",
                           reasoning=r["reasoning"]))
    return out


def build_routes(by_journey: dict[str, list[dict]]) -> list[dict]:
    """A route segment between each pair of consecutive stops, and the false-dawn sightline."""
    journeys = []
    snaps = {(s["journey"], int(s["from_seq"])): s for s in rows(SEEDS / "snaps.csv")}
    for jid, seq in by_journey.items():
        seq.sort(key=lambda p: p["sequence"])
        for i, (a, b) in enumerate(zip(seq, seq[1:], strict=False), start=1):
            snap = snaps.get((jid, a["sequence"]))
            if snap:
                coords = snapped(snap, (a["lon"], a["lat"]), (b["lon"], b["lat"]))
                source = SNAP_SOURCES[snap["source"]]
                how = dict(certainty="approximate", method="narrated-path", source=source,
                           source_licence=LICENCE[source], reasoning=snap["reasoning"])
            else:
                coords = curve((a["lon"], a["lat"]), (b["lon"], b["lat"]), 1 if i % 2 else -1)
                reported = b["certainty"] == "reported"
                how = dict(certainty="reported" if reported else "inferred", method="schematic", source="this-site",
                           source_licence=LICENCE["this-site"],
                           reasoning="A gentle curve between consecutive stops; the book " +
                           ("only reports this leg, through someone's account (see the stop)." if reported
                            else "names no road or river for this stretch."))
            journeys.append(feature(
                {"type": "LineString", "coordinates": coords},
                id=f"{jid.lower()}-seg-{i:02d}", name=f"{a['name']} to {b['name']}", kind="route-segment",
                characters=CHARACTERS[jid], journey=jid, sequence=i, part=int(b["first_seen"][0]),
                episode=b["first_seen"],
                first_seen=b["first_seen"], travel=b["travel"], note_safe="", **how,
            ))
    last = max(by_journey["J7"], key=lambda p: p["sequence"])
    azimuth = GEOD.inv(last["lon"], last["lat"], *TRINITY)[0]
    lon, lat, _ = GEOD.fwd(last["lon"], last["lat"], azimuth, SIGHTLINE_KM * 1000)
    journeys.append(feature(
        {"type": "LineString", "coordinates": [[r5(last["lon"]), r5(last["lat"])], [r5(lon), r5(lat)]]},
        id="j7-false-dawn", name="The false dawn", kind="sightline", characters=["billy"], journey="J7", sequence=None,
        part=4, episode=FALSE_DAWN, first_seen=FALSE_DAWN, travel=None, note_safe="",
        certainty="reported", method="computed", source="this-site", source_licence=LICENCE["this-site"],
        reasoning=f"In the last episode Billy wakes in the night to a light like desert noon, which fades; the true "
                  f"dawn comes later. The book names no place, event or direction for that light; it is widely read as "
                  f"the Trinity test of 16 July 1945. The line points from his last stop towards the "
                  f"Trinity Site (Wikidata Q19842077), bearing {azimuth % 360:.0f} degrees (pyproj, WGS 84), and is "
                  f"{SIGHTLINE_KM} km long only to show the direction."))
    return journeys


def main() -> None:
    picks = {p["id"]: p for p in rows(SEEDS / "place-picks.csv")}
    places, pins, elsewhere = build_places(picks)
    write("places.geojson", places)
    write_json(DATA / "elsewhere.json", elsewhere)
    stops, areas, by_journey = build_stops(pins)
    write("stops.geojson", stops)
    write("areas.geojson", areas + regions())
    write("journeys.geojson", build_routes(by_journey))
    for checklist in CHECKLISTS:
        listed = [f for f in places if f["properties"]["id"].removeprefix("place-") not in picks
                  and f["properties"]["episode"][0] in checklist["parts"]]
        write_checklist(checklist, [f for f in stops if f["properties"]["episode"][0] in checklist["parts"]], listed)


TICKED = re.compile(r"^\| \[[xX]\] \| ([^|]*) \| ([^|]*) \|")


def ticked(path: Path) -> set[tuple[str, str]]:
    """The (label, name) of every row already ticked in a checklist, so a rebuild keeps the owner's sign-off."""
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {(m[1].strip(), m[2].strip()) for line in lines if (m := TICKED.match(line))}


def write_checklist(batch: dict, stops: list[dict], places: list[dict]) -> None:
    """A batch's sign-off list: every feature, its evidence, and links to check it on imagery."""
    done = ticked(batch["path"])

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
        box = "[x]" if (label, p["name"]) in done else "[ ]"
        return f"| {box} | {label} | {p['name']} | {p['certainty']} | {source} | {links(f)} | {flag} |"

    lines = [
        f"# {batch['title']}",
        "",
        "Generated by `pipeline/src/crossing/build_story.py`, which keeps ticked rows. Tick each row once the point "
        "sits where the book puts it.",
        "Rows marked **check** are provisional picks among several candidates. Reasoning for every stop is in the "
        "app's panel.",
        "",
        "| OK | # | Name | Certainty | Source | Look | |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in stops:
        lines.append(row(f, f"{f['properties']['journey']}.{f['properties']['sequence']}"))
    lines += ["", "## Places named in passing", "", "| OK | # | Name | Certainty | Source | Look | |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for f in places:
        if f["properties"]["role"] == "passing":
            lines.append(row(f, ""))
    path = batch["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{path.relative_to(REPO)}: {len(stops)} stops")


if __name__ == "__main__":
    main()


