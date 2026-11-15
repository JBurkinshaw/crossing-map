"""Springs, wells, tanks, ranches and stations along the journeys, from the cached gazetteers.

Run from the repo root:
    uv run --project pipeline python -m crossing.water_places

The Wheeler Survey sheets name every spring, water hole, tank, ranch and station, because in dry country those
are the places a rider goes to (review/stage-8/wheeler/README.md, finding 13). This builds the story layer
data/water_places.geojson inside the journeys corridor (the stretches ridden or walked, 20 km each side, the
region the fine relief covers: crossing.hachures.corridor), from local files:

- GNIS Domestic Names (public domain): feature class Spring, and Locale or Populated Place records whose name says
  ranch or station.
- GeoNames Mexico (CC BY 4.0): springs and water holes by feature code; reservoirs and tanks only when the name
  begins with a water word (Aguaje, Tanque, Ojo, Pozo, Represo), because the rest are modern earth dams (Bordo ...)
  or bare names that do not say what they are; ranches and farms by code, and populated places named Rancho ...;
  railway stations.
- data/places.geojson: the ranches and springs the book names, with the book's spelling and first_seen.

Gazetteer points never named in the book carry first_seen 1-01, as context features do. The book's own carry the
place's first_seen and point at it (place_ref); the site draws only the gazetteer points, because the story layers
draw the book's. A gazetteer point within 1 km of any book place is dropped as its duplicate, and two gazetteer
points of the same kind and name within 1 km are kept once. Every drop is printed.
"""

import json
import re
from collections import Counter
from pathlib import Path

import shapely
from pyproj import Geod, Transformer

from crossing.gazetteer import geonames_rows, gnis_rows
from crossing.hachures import corridor
from crossing.paths import DATA, UTM_CRS
from crossing.text import fold_name

OUT = DATA / "water_places.geojson"
PLACES = DATA / "places.geojson"
DUPLICATE_KM = 1.0
GEOD = Geod(ellps="WGS84")
TO_UTM = Transformer.from_crs("EPSG:4326", UTM_CRS, always_xy=True)

LICENCE = {"gnis": "Public domain", "geonames": "CC BY 4.0"}
# How each source names a record's class, for the reader's note.
CLASS_NOTE = {"gnis": "GNIS feature class", "geonames": "GeoNames feature code"}
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


class Corridor:
    """The journeys corridor in UTM, prepared once for fast point tests."""

    def __init__(self) -> None:
        self.area = corridor()
        shapely.prepare(self.area)

    def __contains__(self, lonlat: tuple[float, float]) -> bool:
        x, y = TO_UTM.transform(*lonlat)
        return bool(shapely.contains_xy(self.area, x, y))


def km(a: dict, b: dict) -> float:
    (ax, ay), (bx, by) = a["geometry"]["coordinates"], b["geometry"]["coordinates"]
    return GEOD.inv(ax, ay, bx, by)[2] / 1000


def feature(source: str, source_id: str, name: str, kind: str, lon: float, lat: float, code: str) -> dict:
    """A gazetteer point the book never names: context, shown from the start (1-01)."""
    props = {"id": f"water-{source}-{source_id}", "name": name, "kind": kind, "part": 1, "first_seen": "1-01",
             "certainty": "located", "method": "gazetteer", "source": source, "source_id": source_id,
             "source_licence": LICENCE[source], "note_safe": f"{CLASS_NOTE[source]} {code}.", "place_ref": None}
    point = {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}
    return {"type": "Feature", "properties": props, "geometry": point}


def from_gnis(area: Corridor) -> list[dict]:
    out = []
    for row in gnis_rows():
        lat, lon = float(row["prim_lat_dec"] or 0), float(row["prim_long_dec"] or 0)
        if row["feature_id"] in GNIS_EXCLUDE:
            continue
        name, cls = row["feature_name"], row["feature_class"]
        if cls == "Spring":
            kind = "spring"
        elif cls in ("Locale", "Populated Place") and (m := GNIS_PLACE.search(name)):
            kind = "ranch" if m.group(1) else "station"
        else:
            continue
        if (lon, lat) in area:
            out.append(feature("gnis", row["feature_id"], name, kind, lon, lat, cls))
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


def from_geonames(area: Corridor) -> list[dict]:
    out = []
    for row in geonames_rows():
        lat, lon = float(row[4]), float(row[5])
        if (kind := geonames_kind(row[1], row[7])) and (lon, lat) in area:
            out.append(feature("geonames", row[0], row[1], kind, lon, lat, row[7]))
    return out


def from_book(area: Corridor) -> list[dict]:
    out = []
    for f in json.loads(PLACES.read_text(encoding="utf-8"))["features"]:
        p, g = f["properties"], f["geometry"]
        if p["kind"] not in BOOK_KINDS or not g or g["type"] != "Point" or tuple(g["coordinates"][:2]) not in area:
            continue
        out.append({"type": "Feature", "geometry": g, "properties": {
            "id": f"water-{p['id']}", "name": p["name"], "kind": BOOK_KINDS[p["kind"]], "part": p["part"],
            "first_seen": p["first_seen"], "certainty": p["certainty"], "method": p["method"], "source": p["source"],
            "source_id": p.get("source_id"), "source_licence": p["source_licence"], "note_safe": p["note_safe"],
            "place_ref": p["id"]}})
    return out


def book_points() -> list[dict]:
    """Every point place the book names, of any kind, for the duplicate test."""
    feats = json.loads(PLACES.read_text(encoding="utf-8"))["features"]
    return [f for f in feats if f["geometry"] and f["geometry"]["type"] == "Point"]


def build() -> tuple[list[dict], list[str]]:
    area = Corridor()
    book = book_points()
    kept: list[dict] = from_book(area)
    dropped: list[str] = []
    for f in from_gnis(area) + from_geonames(area):
        p = f["properties"]
        near = next((b for b in book if km(f, b) <= DUPLICATE_KM), None)
        if near:
            what = f"{km(f, near):.2f} km from book place {near['properties']['name']}"
            dropped.append(f"{p['id']} {p['name']} [{p['note_safe']}]: {what}")
            continue
        twin = next((k for k in kept if k["properties"]["kind"] == p["kind"]
                     and fold_name(k["properties"]["name"]) == fold_name(p["name"]) and km(f, k) <= DUPLICATE_KM), None)
        if twin:
            dropped.append(f"{p['id']} {p['name']}: same name and kind as {twin['properties']['id']}")
            continue
        kept.append(f)
    kept.sort(key=lambda f: f["properties"]["id"])
    return kept, dropped


def write(path: Path, features: list[dict]) -> None:
    fc = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(fc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    features, dropped = build()
    write(OUT, features)
    for line in dropped:
        print("dropped", line)
    print(f"{len(features)} places -> {OUT}")
    counts = Counter((p["kind"], p["source"], p["place_ref"] is not None) for p in (f["properties"] for f in features))
    for (kind, source, book), n in sorted(counts.items()):
        print(f"  {kind:8} {source:9} {'book' if book else 'gazetteer':9} {n}")


if __name__ == "__main__":
    main()
