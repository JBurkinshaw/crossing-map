"""Springs, wells, tanks, ranches and stations for the Wheeler lab's test area, from the cached gazetteers.

Run from the repo root:
    uv run --project pipeline python -m crossing.water_places

The Wheeler Survey sheets name every spring, water hole, tank, ranch and station, because in dry country those
are the places a rider goes to (review/stage-8/wheeler/README.md, finding 13). This builds a small layer of them
for the lab only (site/public/lab/wheeler/water-places.geojson), inside the test area, from local files:

- GNIS Domestic Names (public domain): feature class Spring, and Locale or Populated Place records whose name says
  ranch or station.
- GeoNames Mexico (CC BY 4.0): springs and water holes by feature code; reservoirs and tanks only when the name
  begins with a water word (Aguaje, Tanque, Ojo, Pozo, Represo), because the rest are modern earth dams (Bordo ...)
  or bare names that do not say what they are; ranches and farms by code, and populated places named Rancho ...;
  railway stations.
- data/places.geojson: the ranches and springs the book names, with the book's spelling and first_seen.

Gazetteer points never named in the book carry first_seen 1-01, as context features do. A gazetteer point within
1 km of any book place is dropped as its duplicate (the book place is drawn by the site already, or listed here),
and two gazetteer points of the same kind and name within 1 km are kept once. Every drop is printed.
"""

import json
import re
from collections import Counter
from pathlib import Path

from pyproj import Geod

from crossing.gazetteer import geonames_rows, gnis_rows
from crossing.paths import DATA, SITE_PUBLIC
from crossing.text import fold_name

OUT = SITE_PUBLIC / "lab" / "wheeler" / "water-places.geojson"
PLACES = DATA / "places.geojson"
# The Wheeler lab's test area (west, south, east, north): the bootheel and the upper Bavispe.
TEST_AREA = (-109.6, 30.5, -108.4, 31.6)
DUPLICATE_KM = 1.0
GEOD = Geod(ellps="WGS84")

LICENCE = {"gnis": "Public domain", "geonames": "CC BY 4.0"}
BOOK_KINDS = {"spring": "spring", "ranch": "ranch"}

# GNIS records that the feature class gets wrong for this layer, with the reason.
GNIS_EXCLUDE = {"924821": "an oil test well (Humble Oil and Refining Number 1) filed under Spring"}
GNIS_PLACE = re.compile(r"\b(?:(ranch|rancho)|(station|stage stand|siding))\b", re.IGNORECASE)

# GeoNames codes taken whatever the name: springs and water holes, wells, ranches and farms, railway stations.
# STNB ("scientific research base") is not a stage station and is left out.
GEONAMES_KIND = {
    "SPNG": "spring", "SPNS": "spring", "SPNT": "spring", "SPNGI": "spring", "WTRH": "spring", "WTRHS": "spring",
    "WLL": "well", "WLLS": "well", "WLLQ": "well",
    "RNCH": "ranch", "FRM": "ranch", "FRMS": "ranch", "FRMT": "ranch",
    "RSTN": "station", "RSTP": "station",
}
# Codes taken only when the name begins with a water word, which also says the kind.
GEONAMES_NAMED = {"RSV", "RSVI", "RSVT", "TNKD", "PND", "PNDI", "PNDS", "PNDSI", "WLL", "WLLS", "WTRH"}
WATER_WORD = {"aguaje": "spring", "ojo": "spring", "pozo": "well", "tanque": "tank", "represo": "tank"}
# Populated places and localities named for a ranch ("Rancho Nuevo").
GEONAMES_RANCH_CODES = {"PPL", "PPLQ", "PPLL", "PPLX", "LCTY"}


def in_area(lon: float, lat: float) -> bool:
    w, s, e, n = TEST_AREA
    return w <= lon <= e and s <= lat <= n


def km(a: dict, b: dict) -> float:
    (ax, ay), (bx, by) = a["geometry"]["coordinates"], b["geometry"]["coordinates"]
    return GEOD.inv(ax, ay, bx, by)[2] / 1000


def feature(fid: str, name: str, kind: str, lon: float, lat: float, source: str, code: str, **extra) -> dict:
    props = {"id": fid, "name": name, "kind": kind, "source": source, "source_licence": LICENCE.get(source, ""),
             "certainty": "located", "first_seen": "1-01", "code": code, **extra}
    point = {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}
    return {"type": "Feature", "properties": props, "geometry": point}


def from_gnis() -> list[dict]:
    out = []
    for row in gnis_rows():
        lat, lon = float(row["prim_lat_dec"] or 0), float(row["prim_long_dec"] or 0)
        if not in_area(lon, lat) or row["feature_id"] in GNIS_EXCLUDE:
            continue
        name, cls = row["feature_name"], row["feature_class"]
        if cls == "Spring":
            kind = "spring"
        elif cls in ("Locale", "Populated Place") and (m := GNIS_PLACE.search(name)):
            kind = "ranch" if m.group(1) else "station"
        else:
            continue
        out.append(feature(f"water-gnis-{row['feature_id']}", name, kind, lon, lat, "gnis", cls))
    return out


def geonames_kind(name: str, code: str) -> str | None:
    word = fold_name(name).split(" ")[0]
    if code in GEONAMES_NAMED and word in WATER_WORD:
        return WATER_WORD[word]
    if code in GEONAMES_KIND:
        return GEONAMES_KIND[code]
    if code in GEONAMES_RANCH_CODES and word in ("rancho", "ranch"):
        return "ranch"
    return None


def from_geonames() -> list[dict]:
    out = []
    for row in geonames_rows():
        lat, lon = float(row[4]), float(row[5])
        if in_area(lon, lat) and (kind := geonames_kind(row[1], row[7])):
            out.append(feature(f"water-geonames-{row[0]}", row[1], kind, lon, lat, "geonames", row[7]))
    return out


def from_book() -> list[dict]:
    out = []
    for f in json.loads(PLACES.read_text(encoding="utf-8"))["features"]:
        p, g = f["properties"], f["geometry"]
        if p["kind"] not in BOOK_KINDS or not g or g["type"] != "Point" or not in_area(*g["coordinates"][:2]):
            continue
        out.append({"type": "Feature", "geometry": g, "properties": {
            "id": p["id"], "name": p["name"], "kind": BOOK_KINDS[p["kind"]], "source": p["source"],
            "source_licence": p["source_licence"], "certainty": p["certainty"], "first_seen": p["first_seen"],
            "code": "book"}})
    return out


def book_points() -> list[dict]:
    """Every point place the book names, of any kind, for the duplicate test."""
    feats = json.loads(PLACES.read_text(encoding="utf-8"))["features"]
    return [f for f in feats if f["geometry"] and f["geometry"]["type"] == "Point"]


def build() -> tuple[list[dict], list[str]]:
    book = book_points()
    kept: list[dict] = from_book()
    dropped: list[str] = []
    for f in from_gnis() + from_geonames():
        p = f["properties"]
        near = next((b for b in book if km(f, b) <= DUPLICATE_KM), None)
        if near:
            what = f"{km(f, near):.2f} km from book place {near['properties']['name']}"
            dropped.append(f"{p['id']} {p['name']} [{p['code']}]: {what}")
            continue
        twin = next((k for k in kept if k["properties"]["kind"] == p["kind"]
                     and fold_name(k["properties"]["name"]) == fold_name(p["name"]) and km(f, k) <= DUPLICATE_KM), None)
        if twin:
            dropped.append(f"{p['id']} {p['name']} [{p['code']}]: same name and kind as {twin['properties']['id']}")
            continue
        kept.append(f)
    kept.sort(key=lambda f: f["properties"]["id"])
    return kept, dropped


def write(path: Path, features: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def main() -> None:
    features, dropped = build()
    write(OUT, features)
    for line in dropped:
        print("dropped", line)
    print(f"{len(features)} places -> {OUT}")
    counts = Counter((p["kind"], p["source"], p["code"] == "book") for p in (f["properties"] for f in features))
    for (kind, source, book), n in sorted(counts.items()):
        print(f"  {kind:8} {source:9} {'book' if book else 'gazetteer':9} {n}")


if __name__ == "__main__":
    main()
