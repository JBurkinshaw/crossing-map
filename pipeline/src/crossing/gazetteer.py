"""Resolve seed place names to coordinates from GNIS, GeoNames, and Wikidata.

Run from the repo root:
  uv run --project pipeline python -m crossing.gazetteer              # refresh every pick in place-picks.csv
  uv run --project pipeline python -m crossing.gazetteer ID [ID ...]  # resolve these seeds and add their picks

Reads pipeline/seeds/places.csv and merges its answers into pipeline/seeds/place-picks.csv: rows for the
seeds resolved are replaced, every other row is kept. Seeds whose place is decided by hand in
place-overrides.csv need no pick.

Inputs are cached in private/cache/. Download and unzip these into private/cache/gazetteer/:
  https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_NM_Text.zip
  https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_AZ_Text.zip
  https://download.geonames.org/export/dump/MX.zip
Wikidata API answers are saved on first request, at most one request a second,
so a rerun makes no requests.

A seed is `resolved` when every candidate of the expected feature type lies in
one cluster (all within CLUSTER_KM of each other). Otherwise it is `review`,
with the best-scoring candidate proposed. Nothing is decided silently.
"""

import argparse
import csv
import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from pyproj import Geod

from crossing.http import CachedClient, Refused
from crossing.paths import CACHE, SEEDS, STORY_BOX
from crossing.text import fold_name as fold

GNIS_FILES = [CACHE / f"gazetteer/DomesticNames_{s}_Text/Text/DomesticNames_{s}.txt" for s in ("NM", "AZ")]
GEONAMES_FILE = CACHE / "gazetteer/MX/MX.txt"
WIKIDATA_CACHE = CACHE / "wikidata"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

WEST, SOUTH, EAST, NORTH = STORY_BOX
CLUSTER_KM = 5.0
GEOD = Geod(ellps="WGS84")

# Expected feature type -> (GNIS feature classes, GeoNames feature codes).
TYPES = {
    "range": ({"Range", "Ridge"}, {"MTS", "RDG", "MT"}),
    "stream": ({"Stream", "Arroyo"}, {"STM", "STMI", "STMS", "WAD"}),
    "valley": ({"Valley", "Basin", "Flat", "Plain"}, {"VAL", "PLN", "BSN", "FLT"}),
    "spring": ({"Spring"}, {"SPNG", "SPNT"}),
    "populated": ({"Populated Place", "Locale"},
                  {"PPL", "PPLA", "PPLA2", "PPLA3", "PPLC", "PPLL", "PPLX", "LCTY", "RNCH"}),
    "admin": ({"Civil"}, {"ADM2"}),
    "pass": ({"Gap"}, {"PASS", "GAP"}),
    "summit": ({"Summit"}, {"MT", "PK", "HLL", "HLLS"}),
    "plain": ({"Plain", "Flat"}, {"PLN", "PLAT"}),
}
# Wikidata items carry no comparable feature type, so they rank below a type match.
SOURCE_RANK = {"wikidata": 2, "gnis": 3, "geonames": 1}


# Places with no journey are disambiguated by distance from Part I's home
# country, the Cloverdale area (GNIS 920578).
DEFAULT_ANCHOR = (31.41705, -108.92977)
# GeoNames admin1 codes for Mexico; "00" marks features on or across the border.
GEONAMES_ADMIN1 = {"06": "MX-CHH", "26": "MX-SON"}
GNIS_STATE = {"New Mexico": "US-NM", "Arizona": "US-AZ"}


@dataclass
class Candidate:
    source: str
    source_id: str
    name: str
    feature: str
    lat: float
    lon: float
    where: str
    type_match: bool
    region: str = ""
    region_match: bool = False
    exact: bool = False

    def summary(self) -> str:
        return f"{self.source}:{self.source_id} {self.name} [{self.feature}] {self.lat:.5f},{self.lon:.5f} {self.where}"


def in_box(lat: float, lon: float) -> bool:
    return SOUTH <= lat <= NORTH and WEST <= lon <= EAST


def km(a: Candidate, b: Candidate) -> float:
    return GEOD.inv(a.lon, a.lat, b.lon, b.lat)[2] / 1000


def gnis_rows() -> Iterator[dict]:
    """Every row of the cached GNIS Domestic Names files (New Mexico, then Arizona)."""
    for path in GNIS_FILES:
        with path.open(encoding="utf-8-sig", newline="") as f:
            yield from csv.DictReader(f, delimiter="|")


def geonames_rows() -> Iterator[list[str]]:
    """Every row of the cached GeoNames Mexico dump, as its tab-separated fields."""
    with GEONAMES_FILE.open(encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n").split("\t")


def load_gnis(wanted: set[str]) -> dict[str, list[dict]]:
    by_name: dict[str, list[dict]] = {}
    for row in gnis_rows():
        key = fold(row["feature_name"])
        if key in wanted:
            by_name.setdefault(key, []).append(row)
    return by_name


def load_geonames(wanted: set[str]) -> dict[str, list[list[str]]]:
    by_name: dict[str, list[list[str]]] = {}
    for row in geonames_rows():
        names = {fold(row[1]), fold(row[2])} | {fold(n) for n in row[3].split(",") if n}
        for key in names & wanted:
            by_name.setdefault(key, []).append(row)
    return by_name


def _wikidata_cache_name(url: str, params: dict) -> str:
    """The cache file for a Wikidata call, named from its parameters (without the fixed format)."""
    key = "_".join(f"{k}-{v}" for k, v in sorted(params.items()) if k != "format")
    name = fold(key).replace(" ", "_")
    if len(name) > 180:  # keep file names legal; the hash keeps distinct keys distinct
        name = name[:160] + "_" + hashlib.sha1(key.encode()).hexdigest()[:16]
    return name + ".json"


_client = CachedClient(WIKIDATA_CACHE, 1.0, _wikidata_cache_name)


def wikidata(params: dict) -> dict:
    """Call the Wikidata API through the on-disk cache, at most one request a second."""
    return _client.get(WIKIDATA_API, {**params, "format": "json"})


def wikidata_candidates(queries: list[str]) -> list[Candidate]:
    ids: list[str] = []
    for q in queries:
        hits = wikidata({"action": "wbsearchentities", "search": q, "language": "en", "limit": 7}).get("search", [])
        for hit in hits:
            if hit["id"] not in ids:
                ids.append(hit["id"])
    found = []
    for i in range(0, len(ids), 50):
        batch = "|".join(ids[i : i + 50])
        entities = wikidata({"action": "wbgetentities", "ids": batch, "props": "claims|labels|descriptions",
                             "languages": "en|es"})
        for qid, e in entities.get("entities", {}).items():
            for claim in e.get("claims", {}).get("P625", [])[:1]:
                v = claim["mainsnak"].get("datavalue", {}).get("value")
                if not v or not in_box(v["latitude"], v["longitude"]):
                    continue
                label = (e.get("labels", {}).get("en") or e.get("labels", {}).get("es") or {}).get("value", qid)
                descriptions = e.get("descriptions", {})
                desc = (descriptions.get("en") or descriptions.get("es") or {}).get("value", "")
                found.append(Candidate("wikidata", qid, label, desc[:60], v["latitude"], v["longitude"], "", False))
    return found


def candidates(seed: dict, gnis: dict, geonames: dict) -> list[Candidate]:
    queries = [seed["name"]] + [n for n in seed["alt_names"].split(";") if n]
    # A list, not a set: set order changes between runs, and candidates keep the order they are found in.
    keys = list(dict.fromkeys(fold(q) for q in queries))
    regions = set(seed["region"].split(";"))
    gnis_classes, gn_codes = set(), set()
    for t in seed["expect"].split(";"):
        gnis_classes |= TYPES[t][0]
        gn_codes |= TYPES[t][1]

    cands: list[Candidate] = []
    for key in keys:
        for r in gnis.get(key, []):
            lat, lon = float(r["prim_lat_dec"] or 0), float(r["prim_long_dec"] or 0)
            if in_box(lat, lon):
                region = GNIS_STATE.get(r["state_name"], r["state_name"])
                where = f"{r['county_name']} County, {r['state_name']}"
                cands.append(Candidate("gnis", r["feature_id"], r["feature_name"], r["feature_class"], lat, lon,
                                       where, r["feature_class"] in gnis_classes, region, region in regions))
        for r in geonames.get(key, []):
            lat, lon = float(r[4]), float(r[5])
            if in_box(lat, lon):
                region = GEONAMES_ADMIN1.get(r[10], f"MX-{r[10]}")
                on_border = r[10] == "00" and any(x.startswith("MX") for x in regions)
                cands.append(Candidate("geonames", r[0], r[1], r[7], lat, lon, region, r[7] in gn_codes,
                                       region, region in regions or on_border))
    for c in wikidata_candidates(queries):
        c.region_match = True  # Wikidata gives no region here; distance does the work
        cands.append(c)
    cands = list({(c.source, c.source_id): c for c in cands}.values())
    for c in cands:
        c.exact = fold(c.name) == fold(seed["name"])
    return cands


def pick(cands: list[Candidate], anchor: tuple[float, float]) -> tuple[str, Candidate | None]:
    """Choose the best candidate, nearest the anchor among equals, and say whether it is certain."""
    if not cands:
        return "none", None

    def dist(c: Candidate) -> float:
        return GEOD.inv(anchor[1], anchor[0], c.lon, c.lat)[2] / 1000

    # Wikidata items carry no feature type, so a typed GNIS or GeoNames match outranks them.
    typed = [c for c in cands if c.type_match and c.region_match]
    pool = typed or [c for c in cands if c.region_match] or cands
    # A municipal seat (GeoNames PPLA*) outranks a minor place even when the minor place matches the name
    # exactly: GeoNames often adds the state to a seat's name, as in "Moctezuma (Sonora)".
    best = max(pool, key=lambda c: (c.type_match, c.feature.startswith("PPLA"), c.exact, -round(dist(c) / 25),
                                    SOURCE_RANK[c.source]))
    certain = bool(typed) and all(km(best, c) <= CLUSTER_KM for c in typed)
    return ("resolved" if certain else "review"), best


PICK_FIELDS = ["id", "name", "status", "source", "source_id", "lat", "lon", "map", "candidates"]


def resolve(seeds: list[dict]) -> dict[str, dict]:
    """A pick row for each seed, in seed order."""
    wanted = {fold(n) for s in seeds for n in [s["name"]] + s["alt_names"].split(";") if n}
    gnis, geonames = load_gnis(wanted), load_geonames(wanted)

    found = {s["id"]: candidates(s, gnis, geonames) for s in seeds}

    # Pass 1 settles the unambiguous seeds. Pass 2 anchors the rest on the
    # settled seeds next to them on the same journey (plan section 7, step 4).
    settled: dict[str, Candidate] = {}
    for s in seeds:
        status, best = pick(found[s["id"]], DEFAULT_ANCHOR)
        if status == "resolved":
            settled[s["id"]] = best

    def anchor(i: int) -> tuple[float, float]:
        journeys = set(seeds[i]["journey"].split(";")) - {""}
        near = []
        for step in (-1, 1):
            j = i + step
            while 0 <= j < len(seeds):
                if journeys & set(seeds[j]["journey"].split(";")) and seeds[j]["id"] in settled:
                    near.append(settled[seeds[j]["id"]])
                    break
                j += step
        if not near:
            return DEFAULT_ANCHOR
        return sum(c.lat for c in near) / len(near), sum(c.lon for c in near) / len(near)

    out: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for i, seed in enumerate(seeds):
        cands = found[seed["id"]]
        status, best = pick(cands, anchor(i))
        counts[status] = counts.get(status, 0) + 1
        ordered = sorted(cands, key=lambda c: (not c.type_match, -SOURCE_RANK[c.source]))
        row = {"id": seed["id"], "name": seed["name"], "status": status}
        if best:
            lat, lon = f"{best.lat:.5f}", f"{best.lon:.5f}"
            link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=12/{lat}/{lon}"
            row |= {"source": best.source, "source_id": best.source_id, "lat": lat, "lon": lon, "map": link}
        row["candidates"] = " || ".join(("* " if c.type_match else "") + c.summary() for c in ordered)
        out[seed["id"]] = row
        print(f"{status:9} {seed['id']:26} {best.summary() if best else ''}")
    print(counts)
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Resolve seed place names to gazetteer picks.")
    ap.add_argument("ids", nargs="*", help="seed ids to resolve (default: every id already in place-picks.csv)")
    ap.add_argument("--seeds", type=Path, default=SEEDS / "places.csv")
    ap.add_argument("--out", type=Path, default=SEEDS / "place-picks.csv")
    a = ap.parse_args(argv)
    existing = list(csv.DictReader(a.out.open(encoding="utf-8"))) if a.out.exists() else []
    ids = set(a.ids) or {r["id"] for r in existing}
    seeds = [s for s in csv.DictReader(a.seeds.open(encoding="utf-8")) if s["id"] in ids]
    if missing := ids - {s["id"] for s in seeds}:
        raise SystemExit(f"not in {a.seeds}: {', '.join(sorted(missing))}")
    if not a.ids:
        # A seed placed by place-overrides.csv needs no pick; any other seed without one is new.
        overrides = SEEDS / "place-overrides.csv"
        placed = {r["id"] for r in existing} | {r["id"] for r in csv.DictReader(overrides.open(encoding="utf-8"))}
        if unpicked := [s["id"] for s in csv.DictReader(a.seeds.open(encoding="utf-8")) if s["id"] not in placed]:
            print(f"Not resolved (name them to add them): {', '.join(unpicked)}")
    try:
        new = resolve(seeds)
    except Refused as e:
        raise SystemExit(f"Stopped: {e}. Responses so far are cached; rerun later.") from e
    merged = [new.pop(r["id"], r) for r in existing] + list(new.values())
    with a.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, PICK_FIELDS, restval="", lineterminator="\n")
        w.writeheader()
        w.writerows(merged)


if __name__ == "__main__":
    main()
