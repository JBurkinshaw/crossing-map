"""Find candidate photos on Wikimedia Commons for each place and stop.

Run from the repo root:
  uv run --project pipeline python -m crossing.photos            # cached run, writes the CSV
  uv run --project pipeline python -m crossing.photos --dry-run  # count the requests still needed
  uv run --project pipeline python -m crossing.photos --offline  # write the CSV from the cache only

For each place and stop with a real location, the search follows plan
section 10: the Wikidata item's image (P18), then files in its Commons
category (P373), then Commons geosearch within RADIUS_M of the point.
Wikidata items come from the gazetteer's cached entities (no request): the
feature's own Wikidata id, or the item with its GeoNames (P1566) or GNIS (P590) id.

Licences come from each file's extmetadata. Only public domain, CC0, CC BY
and CC BY-SA files are kept (plan section 3); NC, ND, GFDL-only and non-free
files are dropped. No image is downloaded: the CSV holds the thumbnail URL.

Every API answer is cached in private/cache/photos/, one request every
INTERVAL_S seconds, so a rerun makes no requests. If an API refuses or rate-limits a
request, the run asks nothing more: it writes the CSV from the cache and
lists the places not searched yet. Nothing retries around a refusal.

The owner picks from review/stage-6/photos.csv; nothing here touches the
app or the data layers.
"""

import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from pyproj import Geod

from crossing.gazetteer import EAST, NORTH, SOUTH, WEST, in_box

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / "private" / "cache" / "photos"
OUT = REPO / "review" / "stage-6" / "photos.csv"
USER_AGENT = "crossing-map-pipeline/0.1 (reading-guide map; contact via repository)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_CACHE = REPO / "private" / "cache" / "wikidata"  # the gazetteer's cache, read only

RADIUS_M = 5000  # plan section 10: geosearch within 5 km
INTERVAL_S = 3.0  # Commons sent a 429 at one request a second (12 November 2026)
MAX_UNCERTAINTY_M = 3000  # stops inferred more loosely than this get no photo search
GEO_LIMIT = 30
CATEGORY_LIMIT = 20
PER_PLACE = 5
THUMB_WIDTH = 800
GEOD = Geod(ellps="WGS84")

EXTMETA = "|".join([
    "ObjectName", "Artist", "Credit", "LicenseShortName", "License", "LicenseUrl", "UsageTerms",
    "AttributionRequired", "Copyrighted", "NonFree", "Restrictions", "DateTimeOriginal", "DateTime", "Categories",
])
PHOTO_MIME = {"image/jpeg", "image/png", "image/webp", "image/tiff"}

# Category words that suggest what a file shows, matched at the start of a
# word in the categories and the file title together, first kind first.
# "not a photo" files (maps, arms, flags) and "aerial" views (astronaut
# photos, USDA orthophotos; the map has satellite already) are dropped.
# "wildlife" (plant and animal close-ups) ranks last.
DROP_KINDS = {"not a photo", "aerial"}
KIND_WORDS = {
    "not a photo": ["maps of", "map of", "topographic map", "locator map", "location map", "coat of arms",
                    "coats of arms", "escudo", "flag", "logo", "seal of", "diagram", "drawing", "svg"],
    "aerial": ["view of earth", "iss0", "iss expedition", "astronaut photograph", "satellite image", "landsat",
               "photographs taken on the international space station", "pd usda", "orthophoto", "orthoimage"],
    "wildlife": ["inaturalist", "fauna", "flora", "birds of", "insects", "reptiles", "mammals", "plants"],
    "building": ["church", "chapel", "cathedral", "mission", "building", "house", "architecture", "hacienda",
                 "school", "store", "street", "plaza", "monument", "museum", "station", "hotel", "interior",
                 "temple", "templo", "iglesia", "bridge", "cemetery", "ruins", "archaeological", "facade", "courthouse", "post office"],
    "landscape": ["landscape", "mountain", "sierra", "river", "río", "rio ", "valley", "desert", "canyon", "cañón",
                  "creek", "hills", "peak", "range", "panorama", "scenery", "nature", "vegetation", "grassland",
                  "lake", "laguna", "arroyo", "mesa", "pass", "puerto", "playa", "views of", "forest", "wilderness", "sky island"],
}


class Refused(Exception):
    """An API refused or rate-limited a request; the run stops."""


_last_request = 0.0
_requests = 0
_offline = False  # cache only: --dry-run, --offline, or after a refusal
_missing = 0


def fetch(url: str, params: dict) -> dict:
    """GET a JSON API through the on-disk cache, one request every INTERVAL_S seconds."""
    global _last_request, _requests, _missing
    key = url + "?" + urllib.parse.urlencode(sorted(params.items()))
    path = CACHE / (hashlib.sha1(key.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if _offline:
        _missing += 1
        return {}
    wait = INTERVAL_S - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(key, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise Refused(f"HTTP {e.code} from {url} (Retry-After: {e.headers.get('Retry-After')})") from e
    finally:
        _last_request = time.monotonic()
        _requests += 1
    if "error" in data:  # MediaWiki errors, maxlag among them, come back as 200
        raise Refused(f"{url}: {data['error'].get('code')}: {data['error'].get('info')}")
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"request": key, "response": data}), encoding="utf-8")
    return {"request": key, "response": data}


def commons(params: dict) -> dict:
    return fetch(COMMONS_API, {**params, "format": "json", "formatversion": "2", "maxlag": "5"}).get("response", {})


# --- The places to search ---------------------------------------------------

@dataclass
class Unit:
    id: str
    name: str
    role: str
    kind: str
    lat: float
    lon: float
    source: str
    source_id: str
    stop_ids: list[str] = field(default_factory=list)
    qid: str = ""
    p18: str = ""
    commons_cat: str = ""


def units() -> tuple[list[Unit], list[tuple[str, str]]]:
    """Places and stops to search, and the skipped ones with the reason."""
    places = json.loads((REPO / "data/places.geojson").read_text(encoding="utf-8"))["features"]
    stops = json.loads((REPO / "data/stops.geojson").read_text(encoding="utf-8"))["features"]
    found: dict[str, Unit] = {}
    skipped: list[tuple[str, str]] = []
    for f in places:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        if p["role"] == "tale" and not in_box(lat, lon):
            skipped.append((p["id"], "tale place outside the story box"))
            continue
        found[p["id"]] = Unit(p["id"], p["name"], p["role"], p["kind"], lat, lon, p["source"], p.get("source_id") or "")
    for f in stops:
        p = f["properties"]
        if p.get("place_ref"):
            if p["place_ref"] in found:
                found[p["place_ref"]].stop_ids.append(p["id"])
            continue
        lon, lat = f["geometry"]["coordinates"]
        r = p.get("uncertainty_m")
        if p["certainty"] in ("inferred", "reported") and (r is None or r > MAX_UNCERTAINTY_M):
            skipped.append((p["id"], f"{p['certainty']}, radius {r and round(r / 1000)} km"))
            continue
        if not in_box(lat, lon):
            skipped.append((p["id"], "outside the story box"))
            continue
        found[p["id"]] = Unit(p["id"], p["name"], "stop", p["kind"], lat, lon, p["source"], p.get("source_id") or "",
                              [p["id"]])
    return list(found.values()), skipped


def link_wikidata(us: list[Unit]) -> None:
    """Find each unit's Wikidata item, image (P18) and Commons category (P373).

    Read from the Wikidata entities the gazetteer already cached, with no
    request: the item is the unit's own Wikidata source id, or the one item
    whose GeoNames id (P1566) or GNIS id (P590) is the unit's source id. The
    Wikidata Query Service was rate-limiting during an outage when this was
    written (12 November 2026), so it is not called.
    """
    def values(claims: dict, prop: str) -> list[str]:
        return [c["mainsnak"]["datavalue"]["value"] for c in claims.get(prop, []) if "datavalue" in c["mainsnak"]]

    entities: dict[str, dict] = {}
    for path in sorted(WIKIDATA_CACHE.glob("*wbgetentities*.json")):
        entities.update(json.loads(path.read_text(encoding="utf-8")).get("entities", {}))
    by_source: dict[tuple[str, str], set[str]] = {}
    for qid, e in entities.items():
        claims = e.get("claims", {})
        by_source.setdefault(("wikidata", qid), set()).add(qid)
        for source, prop in (("geonames", "P1566"), ("gnis", "P590")):
            for v in values(claims, prop):
                by_source.setdefault((source, v), set()).add(qid)
    for u in us:
        qids = sorted(by_source.get((u.source, u.source_id), set()))
        if len(qids) != 1:
            if qids:  # two items claim one id; take none rather than guess
                print(f"  {u.id}: {u.source} {u.source_id} matches {', '.join(qids)}; not linked", file=sys.stderr)
            continue
        claims = entities[qids[0]].get("claims", {})
        u.qid = qids[0]
        u.p18 = (values(claims, "P18") or [""])[0]
        u.commons_cat = (values(claims, "P373") or [""])[0]


# --- Commons files ----------------------------------------------------------

def strip_html(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())


def meta(page: dict, name: str) -> str:
    info = (page.get("imageinfo") or [{}])[0]
    return strip_html((info.get("extmetadata") or {}).get(name, {}).get("value", ""))


def licence_ok(page: dict) -> tuple[bool, str]:
    """Allowed: public domain, CC0, CC BY, CC BY-SA (plan section 3). The reason if not."""
    short = meta(page, "LicenseShortName")
    code = meta(page, "License").lower()
    if meta(page, "NonFree").lower() == "true":
        return False, "non-free"
    words = f"{short} {code}".lower()
    if re.search(r"\bnc\b|-nc-|noncommercial|\bnd\b|-nd-|noderiv", words):
        return False, "NC or ND"
    if code in ("pd", "cc0") or code.startswith("pd-") or "public domain" in words or "cc0" in words:
        return True, ""
    if re.fullmatch(r"cc-by(-sa)?(-\d(\.\d)?)?(-[a-z]{2})?", code):
        return True, ""
    if re.match(r"cc by(-sa)? \d", short.lower()):
        return True, ""
    return False, short or code or "no licence"


def kind_of(title: str, categories: str) -> str:
    text = f"{title} {categories}".lower().replace("_", " ")
    for kind, words in KIND_WORDS.items():
        if any(re.search(r"\b" + re.escape(w), text) for w in words):
            return kind
    return "other"


def file_pages(params: dict) -> list[dict]:
    """Run a Commons query that returns file pages, following continuation for imageinfo."""
    base = {**params, "prop": "imageinfo|coordinates", "iiprop": "url|mime|extmetadata",
            "iiextmetadatafilter": EXTMETA, "iiurlwidth": str(THUMB_WIDTH), "coprimary": "all"}
    pages: dict[int, dict] = {}
    cont: dict = {}
    for _ in range(5):
        data = commons({**base, **cont})
        for p in data.get("query", {}).get("pages", []):
            have = pages.setdefault(p["pageid"], p) if "pageid" in p else None
            if have is not None and "imageinfo" in p:
                have["imageinfo"] = p["imageinfo"]
            if have is not None and "coordinates" in p:
                have["coordinates"] = p["coordinates"]
        if "continue" not in data:
            break
        cont = dict(data["continue"])
        if not any(k.startswith(("ii", "co")) for k in cont):
            break  # only the file list goes on; the limit asked for is enough
    return list(pages.values())


@dataclass
class Photo:
    title: str
    via: str  # wikidata-p18, commons-category, geosearch
    page: dict
    distance_m: float | None = None
    kind: str = ""

    @property
    def info(self) -> dict:
        return (self.page.get("imageinfo") or [{}])[0]


def candidates(u: Unit) -> tuple[list[Photo], dict[str, int]]:
    """All allowed photo candidates for one unit, unranked, and counts of what was dropped."""
    found: dict[str, Photo] = {}
    if u.p18:
        for p in file_pages({"action": "query", "titles": "File:" + u.p18}):
            found.setdefault(p["title"], Photo(p["title"], "wikidata-p18", p))
    if u.commons_cat:
        for p in file_pages({"action": "query", "generator": "categorymembers", "gcmtitle": "Category:" + u.commons_cat,
                             "gcmtype": "file", "gcmlimit": str(CATEGORY_LIMIT)}):
            found.setdefault(p["title"], Photo(p["title"], "commons-category", p))
    for p in file_pages({"action": "query", "generator": "geosearch", "ggscoord": f"{u.lat}|{u.lon}",
                         "ggsradius": str(RADIUS_M), "ggslimit": str(GEO_LIMIT), "ggsnamespace": "6"}):
        found.setdefault(p["title"], Photo(p["title"], "geosearch", p))

    kept: list[Photo] = []
    dropped: dict[str, int] = {}
    for ph in found.values():
        if ph.info.get("mime") not in PHOTO_MIME:
            dropped["not a photo"] = dropped.get("not a photo", 0) + 1
            continue
        ok, why = licence_ok(ph.page)
        if not ok:
            dropped[why] = dropped.get(why, 0) + 1
            continue
        ph.kind = kind_of(ph.title, meta(ph.page, "Categories"))
        if ph.kind in DROP_KINDS:
            dropped[ph.kind] = dropped.get(ph.kind, 0) + 1
            continue
        coords = ph.page.get("coordinates") or []
        if coords:
            c = coords[0]
            ph.distance_m = GEOD.inv(u.lon, u.lat, c["lon"], c["lat"])[2]
        kept.append(ph)
    return kept, dropped


def rank(photos: list[Photo]) -> list[Photo]:
    """Wikidata image first, then landscape views by distance, then the rest by distance."""
    order = {"landscape": 0, "other": 1, "building": 2, "wildlife": 3}

    def key(ph: Photo) -> tuple:
        far = ph.distance_m if ph.distance_m is not None else RADIUS_M * 2
        return (ph.via != "wikidata-p18", order[ph.kind], far)

    return sorted(photos, key=key)


# --- Output -----------------------------------------------------------------

COLUMNS = ["place_id", "place_name", "role", "kind", "stop_ids", "wikidata", "rank", "pick", "file_title", "via",
           "looks_like", "distance_m", "author", "licence", "licence_url", "date", "commons_url", "thumbnail_url"]


def row(u: Unit, i: int, ph: Photo) -> dict:
    title = meta(ph.page, "ObjectName") or ph.title.removeprefix("File:").rsplit(".", 1)[0]
    return {
        "place_id": u.id, "place_name": u.name, "role": u.role, "kind": u.kind, "stop_ids": ";".join(u.stop_ids),
        "wikidata": u.qid, "rank": i, "pick": "", "file_title": title, "via": ph.via, "looks_like": ph.kind,
        "distance_m": "" if ph.distance_m is None else round(ph.distance_m),
        "author": meta(ph.page, "Artist") or meta(ph.page, "Credit"),
        "licence": meta(ph.page, "LicenseShortName"), "licence_url": meta(ph.page, "LicenseUrl"),
        "date": (meta(ph.page, "DateTimeOriginal") or meta(ph.page, "DateTime"))[:40],
        "commons_url": ph.info.get("descriptionurl", ""), "thumbnail_url": ph.info.get("thumburl", "").split("?")[0],
    }


def main(argv: list[str]) -> int:
    """Search, rank and write the CSV. After a refusal, finish from the cache only."""
    global _offline
    dry_run = "--dry-run" in argv
    _offline = dry_run or "--offline" in argv
    us, skipped = units()
    print(f"{len(us)} places and stops to search, {len(skipped)} skipped "
          f"(story box {WEST} to {EAST}, {SOUTH} to {NORTH})")
    link_wikidata(us)
    rows: list[dict] = []
    stats = {"with": 0, "without": [], "unsearched": [], "dropped": {}, "licences": {}, "allowed": 0}
    for u in us:
        missing = _missing
        try:
            photos, dropped = candidates(u)
        except Refused as e:
            print(f"Stopped asking at {u.id}: {e}. {_requests} requests made; the rest comes from the cache only.",
                  file=sys.stderr)
            _offline = True
            photos, dropped = candidates(u)
        if _missing > missing:
            stats["unsearched"].append(u)
            continue
        for k, n in dropped.items():
            stats["dropped"][k] = stats["dropped"].get(k, 0) + n
        stats["allowed"] += len(photos)
        top = rank(photos)[:PER_PLACE]
        if top:
            stats["with"] += 1
        else:
            stats["without"].append(u)
        for i, ph in enumerate(top, 1):
            r = row(u, i, ph)
            stats["licences"][r["licence"]] = stats["licences"].get(r["licence"], 0) + 1
            rows.append(r)
    if dry_run:
        print(f"Dry run: {_missing} uncached requests for {len(stats['unsearched'])} places "
              "(category and continuation requests may add a few)")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"{_requests} requests made. Wrote {len(rows)} candidates to {OUT.relative_to(REPO)}")
    print(f"Searched: {len(us) - len(stats['unsearched'])}; with candidates: {stats['with']}; "
          f"without: {len(stats['without'])}; not searched yet: {len(stats['unsearched'])} "
          f"({_missing} uncached requests); allowed files seen: {stats['allowed']}")
    print(f"Linked to Wikidata: {sum(1 for u in us if u.qid)}; with P18: {sum(1 for u in us if u.p18)}; "
          f"with P373: {sum(1 for u in us if u.commons_cat)}")
    print("Dropped:", json.dumps(stats["dropped"], ensure_ascii=False))
    print("Licences in the CSV:", json.dumps(dict(sorted(stats["licences"].items(), key=lambda x: -x[1])),
                                              ensure_ascii=False))
    print("Kinds in the CSV:", json.dumps({k: sum(1 for r in rows if r["looks_like"] == k)
                                           for k in ("landscape", "other", "building", "wildlife")}))
    print("Without candidates:", "; ".join(f"{u.id} ({u.role})" for u in stats["without"]))
    print("Not searched yet:", "; ".join(u.id for u in stats["unsearched"]))
    print("Skipped:", "; ".join(f"{i} ({why})" for i, why in skipped))
    return 1 if stats["unsearched"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
