"""Forts, ghost towns, mines, sawmills, churches and other period places along the journeys, from the gazetteers.

Run from the repo root, after crossing.water_places:
    uv run --project pipeline python -m crossing.context_places

The water places (crossing.water_places) give the rider's waters, ranches and stations. This sibling layer,
data/context_places.geojson, gives the rest of what a Wheeler sheet names and what stood in the 1940s, inside the
same journeys corridor (crossing.water_places.Corridor), from local files:

- GNIS Domestic Names (public domain, the current files): Military (forts, camps and army air fields), Populated
  Place marked "(historical)" (ghost towns), Lake and Flat (many of them dry lakes and playas, set as names only).
- The GNIS national file of 25 August 2021 (public domain), the last before USGS moved the man-made classes out of
  Domestic Names, cached as private/cache/gazetteer/Features_20210825/{NM,AZ}_Features_20210825.txt from
  https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/Archive/MainDomestic/: Locale by its name
  (ranches, windmills, corrals, stations and sidings, camps and cabins), Mine, Cemetery, Church, School, Post
  Office "(historical)" and named wells.
- GeoNames Mexico (CC BY 4.0): abandoned places, mines, sawmills and logging camps, corrals, a chapel, customs
  houses, archaeological sites, an abandoned station and a siding; railway tunnels and railway names only near
  a railway the map draws (Natural Earth 10m railroads, the base map's).

No gazetteer dates its features, so era is judged by class and name (docs/decisions/0028-context-places.md): no
modern class (airports, fire stations, shopping centres), no school named as a modern one (Elementary, High ...),
no town church or school (within TOWN_KM of a town), no well numbered or named only as "Water Well", and no post
office still open (the town's name already marks it). A gazetteer name "X (historical)" is set as "X", with
historical true. Every point is context the book never names: first_seen 1-01.

Duplicates go as in crossing.water_places: a point within 1 km of any book place, or within 1 km of a water place
or a kept point of the same name, is dropped; a post office within 2 km of a kept place of its town's name too.
Every drop is printed.
"""

import csv
import json
import re
import tempfile
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import shapely
from shapely.geometry import shape
from shapely.ops import unary_union

from crossing.basemap import LAYERS as BASEMAP_LAYERS
from crossing.basemap import shapefile
from crossing.gazetteer import geonames_rows, gnis_rows
from crossing.paths import CACHE, DATA, STORY_BOX
from crossing.text import fold_name
from crossing.vector import read
from crossing.water_places import DUPLICATE_KM, TO_UTM, Corridor, book_points, km, write

OUT = DATA / "context_places.geojson"
WATER = DATA / "water_places.geojson"
OLD_GNIS = [CACHE / f"gazetteer/Features_20210825/{s}_Features_20210825.txt" for s in ("NM", "AZ")]
TOWN_KM = 1.5
POST_OFFICE_KM = 2.0
# Tunnels and railway names further than this from a railway the map draws would stand in empty country.
RAILWAY_M = 2000

LICENCE = {"gnis": "Public domain", "gnis-2021": "Public domain", "geonames": "CC BY 4.0"}
CLASS_NOTE = {"gnis": "GNIS feature class", "gnis-2021": "GNIS national file of 25 August 2021, feature class",
              "geonames": "GeoNames feature code"}
HISTORICAL = re.compile(r"\s*\(historical\)\s*", re.IGNORECASE)

# Current GNIS classes taken whatever the name.
GNIS_KIND = {"Military": "military", "Lake": "lake", "Flat": "flat"}
# GNIS records (either file) that the class and name rules let through but that are not period places, with why.
GNIS_EXCLUDE = {
    "2090229": "Winslow Air Force Station: the Air Force dates from 1947",
    "1680716": "Fort Bayard Military Reservation: the reservation's point, 2 km from Fort Bayard's own",
    "900243": "Harrison A Schmitt School: named for the astronaut, so after 1945",
    "900237": "Camp Thunderbird: a youth camp",
}

# The 2021 file's Locale class holds anything with no class of its own, so its name says the kind. Checked in
# order; the first match wins. Stations exclude the modern sorts (weather, ranger, pumping, substations).
LOCALE_KIND = [
    ("windmill", re.compile(r"\bWindmill\b")),
    ("well", re.compile(r"\bWells?\b")),
    ("corral", re.compile(r"\b(?:Corrals?|Pens)\b")),
    ("ranch", re.compile(r"\b(?:Ranch|Rancho|Place|Homestead)\b")),
    ("station", re.compile(r"\b(?:Station|Siding|Stage Stand|Stage Station|Depot|Switch)\b")),
    ("camp", re.compile(r"\b(?:Camp|Cabin)\b")),
]
LOCALE_MODERN = re.compile(
    r"\b(?:Weather|Ranger|Pumping|Substation|Compressor|Fire|Gaging|Gauging|Service|Gas|Radio|Relay|Microwave|Guard|"
    r"Experiment|Experimental|Patrol|Police|Campground|Campgrounds|Scout|Trailer|RV|Girl|Boy|Bible|Youth|Picnic|"
    r"Trailhead|Center|Shopping|Fairgrounds|Park|Historic|Site|District|Subdivision|Estates|Addition|Heights|"
    r"Mobile|Motel|Lodge|Resort|Golf|Industrial|Plant|Landfill|Dump|Rest Area|Mill Site|Inspection|Turbine|Radar|"
    r"Camera|Monitoring|Lookout|Tower)\b")
# Mines: a working or a claim group, not a prospect, pit, quarry or deposit (most of those are later, or never
# worked).
MINE_KEEP = re.compile(r"\b(?:Mine|Mines|Shaft|Adit|Tunnel|Lode|Group)\b")
MINE_DROP = re.compile(r"\b(?:Prospects?|Pit|Deposit|Quarry|Claims?|Gravel|Sand|Uranium|Cinder|Caliche)\b")
SCHOOL_MODERN = re.compile(
    r"\b(?:Elementary|High|Middle|Junior|College|Campus|Academy|Learning|Center|University|Preschool|Kindergarten|"
    r"Intermediate|Charter|Head Start|Montessori|Christian|Primary|Memorial)\b")
# Congregations whose names are of the later twentieth century.
CHURCH_MODERN = re.compile(
    r"\b(?:Kingdom Hall|Center|Covenant|Fellowship|Ministries|Worship|Calvary|Victory|Harvest|Vineyard)\b")
NAMED_WELL = re.compile(r"\bWells?\b")
UNNAMED_WELL = re.compile(r"Water Well|\d|\bNumber\b|\bTest\b|\bOil\b|\bMonitor")

# GeoNames codes and their kinds. TNLRR and RR only near a drawn railway.
GEONAMES_KIND = {
    "PPLQ": "abandoned", "FRMQ": "abandoned", "ANS": "ruin",
    "MN": "mine", "MNQ": "mine", "MNAU": "mine", "MNCU": "mine", "MNAG": "mine", "MNFE": "mine", "MNPB": "mine",
    "MLSW": "sawmill", "CMPL": "camp", "CRRL": "corral", "CH": "church", "CSTM": "customs",
    "RSTNQ": "station", "SPUR": "station", "TNLRR": "tunnel", "RR": "railway",
}
NEAR_RAILWAY = {"TNLRR", "RR"}


def feature(source: str, source_id: str, name: str, kind: str, lon: float, lat: float, code: str) -> dict:
    """A gazetteer point the book never names: context, shown from the start (1-01)."""
    historical = bool(HISTORICAL.search(name))
    props = {"id": f"context-{source}-{source_id}", "name": HISTORICAL.sub(" ", name).strip(), "kind": kind,
             "part": 1, "first_seen": "1-01", "certainty": "located", "method": "gazetteer", "source": source,
             "source_id": source_id, "source_licence": LICENCE[source], "note_safe": f"{CLASS_NOTE[source]} {code}.",
             "historical": historical, "place_ref": None}
    point = {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}
    return {"type": "Feature", "properties": props, "geometry": point}


def old_gnis_rows() -> Iterator[dict]:
    for path in OLD_GNIS:
        with path.open(encoding="utf-8-sig", newline="") as f:
            yield from csv.DictReader(f, delimiter="|")


def railways() -> shapely.Geometry:
    """The base map's railways in the story box, in UTM, prepared for distance tests."""
    name, sql, _ = BASEMAP_LAYERS["railroad"]
    with tempfile.TemporaryDirectory() as tmp:
        lines = read(shapefile(name), sql, STORY_BOX, Path(tmp) / "railroad.geojson")
    geom = shapely.transform(unary_union([shape(f["geometry"]) for f in lines]), TO_UTM.transform, interleaved=False)
    shapely.prepare(geom)
    return geom


def utm_point(f: dict) -> shapely.Point:
    return shapely.Point(TO_UTM.transform(*f["geometry"]["coordinates"]))


def towns() -> list[tuple[float, float]]:
    """Today's towns: GNIS populated places (not historical) and census places, and the book's towns and cities."""
    out = [(float(r["prim_long_dec"]), float(r["prim_lat_dec"])) for r in gnis_rows()
           if (r["feature_class"] == "Census" or r["feature_class"] == "Populated Place"
               and "(historical)" not in r["feature_name"]) and r["prim_lat_dec"]]
    out += [tuple(f["geometry"]["coordinates"][:2]) for f in book_points()
            if f["properties"]["kind"] in ("town", "city")]
    return out


def from_gnis(area: Corridor) -> list[dict]:
    out = []
    for row in gnis_rows():
        name, cls = row["feature_name"], row["feature_class"]
        kind = GNIS_KIND.get(cls) or ("abandoned" if cls == "Populated Place" and HISTORICAL.search(name) else None)
        lon, lat = float(row["prim_long_dec"] or 0), float(row["prim_lat_dec"] or 0)
        if kind and row["feature_id"] not in GNIS_EXCLUDE and (lon, lat) in area:
            out.append(feature("gnis", row["feature_id"], name, kind, lon, lat, cls))
    return out


def old_gnis_kind(name: str, cls: str) -> str | None:
    bare = HISTORICAL.sub(" ", name)
    if cls == "Locale":
        if LOCALE_MODERN.search(bare):
            return None
        return next((kind for kind, words in LOCALE_KIND if words.search(bare)), None)
    if cls == "Mine":
        return "mine" if MINE_KEEP.search(bare) and not MINE_DROP.search(bare) else None
    if cls == "Well":
        if not NAMED_WELL.search(bare) or UNNAMED_WELL.search(bare):
            return None
        return "windmill" if "Windmill" in bare else "well"
    if cls == "School":
        return None if SCHOOL_MODERN.search(bare) else "school"
    if cls == "Post Office":
        return "post-office" if HISTORICAL.search(name) else None
    if cls == "Church":
        return None if CHURCH_MODERN.search(bare) else "church"
    return "cemetery" if cls == "Cemetery" else None


def from_old_gnis(area: Corridor, town_points: list[tuple[float, float]], dropped: list[str]) -> list[dict]:
    out = []
    for row in old_gnis_rows():
        name, cls = row["FEATURE_NAME"], row["FEATURE_CLASS"]
        if not (kind := old_gnis_kind(name, cls)) or row["FEATURE_ID"] in GNIS_EXCLUDE:
            continue
        lon, lat = float(row["PRIM_LONG_DEC"] or 0), float(row["PRIM_LAT_DEC"] or 0)
        if (lon, lat) not in area:
            continue
        f = feature("gnis-2021", row["FEATURE_ID"], name, kind, lon, lat, cls)
        # A town's church or school is most likely a later building, and the town's name already marks the place.
        if kind in ("church", "school") and not f["properties"]["historical"]:
            near = min((km(f, {"geometry": {"coordinates": t}}) for t in town_points), default=99)
            if near <= TOWN_KM:
                dropped.append(f"{f['properties']['id']} {name} [{cls}]: {near:.2f} km from a town")
                continue
        out.append(f)
    return out


def from_geonames(area: Corridor, rail: shapely.Geometry, dropped: list[str]) -> list[dict]:
    out = []
    for row in geonames_rows():
        code = row[7]
        if code not in GEONAMES_KIND:
            continue
        lat, lon = float(row[4]), float(row[5])
        if (lon, lat) not in area:
            continue
        f = feature("geonames", row[0], row[1], GEONAMES_KIND[code], lon, lat, code)
        if code in NEAR_RAILWAY and (d := rail.distance(utm_point(f))) > RAILWAY_M:
            dropped.append(f"{f['properties']['id']} {row[1]} [{code}]: {d / 1000:.1f} km from a drawn railway")
            continue
        out.append(f)
    return out


def stem(name: str) -> str:
    """A name without its class word, so "Hachita Post Office" matches the place Hachita."""
    return fold_name(re.sub(r"\s+Post Office$", "", name))


def build() -> tuple[list[dict], list[str]]:
    area = Corridor()
    book = book_points()
    water = [f for f in json.loads(WATER.read_text(encoding="utf-8"))["features"]
             if f["properties"]["place_ref"] is None]
    dropped: list[str] = []
    candidates = from_gnis(area) + from_old_gnis(area, towns(), dropped) + from_geonames(area, railways(), dropped)
    kept: list[dict] = []
    for f in candidates:
        p = f["properties"]
        near = next((b for b in book if km(f, b) <= DUPLICATE_KM), None)
        if near:
            dropped.append(f"{p['id']} {p['name']} [{p['note_safe']}]: {km(f, near):.2f} km from book place "
                           f"{near['properties']['name']}")
            continue
        twin = next((k for k in water + kept if fold_name(k["properties"]["name"]) == fold_name(p["name"])
                     and km(f, k) <= DUPLICATE_KM), None)
        if not twin and p["kind"] == "post-office":
            twin = next((k for k in kept if fold_name(k["properties"]["name"]) == stem(p["name"])
                         and km(f, k) <= POST_OFFICE_KM), None)
        if twin:
            dropped.append(f"{p['id']} {p['name']}: same name as {twin['properties']['id']}")
            continue
        kept.append(f)
    kept.sort(key=lambda f: f["properties"]["id"])
    return kept, dropped


def main() -> None:
    features, dropped = build()
    write(OUT, features)
    for line in dropped:
        print("dropped", line)
    print(f"{len(features)} places -> {OUT}")
    counts = Counter((p["kind"], p["source"]) for p in (f["properties"] for f in features))
    for (kind, source), n in sorted(counts.items()):
        print(f"  {kind:11} {source:9} {n}")


if __name__ == "__main__":
    main()
