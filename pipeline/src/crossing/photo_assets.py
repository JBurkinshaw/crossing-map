"""Turn the owner's photo picks into small WebP files and data/photos.json (decision 0067).

Run from the repo root:
  uv run --project pipeline python -m crossing.photo_assets download            # fetch each picked file once
  uv run --project pipeline python -m crossing.photo_assets download --dry-run  # count the files not cached yet
  uv run --project pipeline python -m crossing.photo_assets build               # from the cache only

`download` reads the rows with a `pick` in review/stage-6/photos.csv and fetches each file's thumbnail (the
CSV's `thumbnail_url`, 960 px) once, at most one request every INTERVAL_S seconds, with the pipeline's
User-Agent. Every answer is cached in private/cache/photos/files/, so a rerun makes no request, and each
request is logged there (requests.log: time, URL, HTTP status, bytes). A 429 or 503 is retried after its
Retry-After, or after a wait that doubles from BACKOFF_S. If a refusal asks for more than MAX_WAIT_S, or a
file is refused MAX_TRIES times, the run stops asking and lists what is left.

`build` makes no request. It resizes each cached file to LONG_SIDE px on its long side, converts it to sRGB
WebP with no metadata, and writes it to site/public/photos/. Then it writes data/photos.json: for each place
(or stop with no place of its own), its picks in the CSV's rank order, each with its file, size, TASL fields
(title, author, licence, source), date, how it was found and its alt text. Credits come from the Commons
answers crossing.photos cached (private/cache/photos/), with HTML stripped. The alt text, and an author
where Commons gives none or a sentence, are written by hand in pipeline/seeds/photo-text.csv.

A photo shows with its place. Where its title, alt text or author names a place the reader meets later
than the photo's own place, it carries that later `first_seen`, so it never names a place before the
reader reaches it (the rule the spoiler-leak test checks, decision 0054).
"""

import csv
import hashlib
import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

from crossing.http import USER_AGENT
from crossing.paths import CACHE, DATA, REPO, SEEDS, SITE_PUBLIC
from crossing.photos import strip_html

PICKS = REPO / "review" / "stage-6" / "photos.csv"
SEARCH_CACHE = CACHE / "photos"
FILES = SEARCH_CACHE / "files"
LOG = FILES / "requests.log"
TEXT = SEEDS / "photo-text.csv"
OUT_DIR = SITE_PUBLIC / "photos"
OUT_JSON = DATA / "photos.json"

INTERVAL_S = 2.0  # the approved batch allows one request a second, and this stays under it
TIMEOUT_S = 60
BACKOFF_S = 60  # the first wait after a refusal without Retry-After, doubling on each refusal
MAX_TRIES = 5
MAX_WAIT_S = 600  # a longer Retry-After stops the run instead
LONG_SIDE = 640
QUALITY = 80
BUDGET_BYTES = 6_000_000  # all the WebP files together

STORY_LAYERS = ["places", "stops", "areas", "journeys", "mountain_glyphs", "vignettes"]
ALWAYS_NAMED = ["Sonora", "Chihuahua", "New Mexico"]  # the map's cartouche names them at every position


class Refused(Exception):
    """Commons refused a file for good, or asked for a longer wait than MAX_WAIT_S."""


# --- The picks ----------------------------------------------------------------

def picks(path: Path = PICKS) -> list[dict]:
    """The picked rows of the review CSV, in file order (places in data order, each in rank order)."""
    with path.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["pick"].strip()]
    return sorted(rows, key=lambda r: (_first_index(rows, r["place_id"]), int(r["rank"])))


def _first_index(rows: list[dict], place_id: str) -> int:
    return next(i for i, r in enumerate(rows) if r["place_id"] == place_id)


def cache_path(url: str) -> Path:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
    return FILES / (hashlib.sha1(url.encode()).hexdigest()[:16] + suffix)


# --- Download (the only step that uses the network) ---------------------------

def log(url: str, status: str | int, size: int) -> None:
    FILES.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(UTC).isoformat(timespec='seconds')}\t{url}\t{status}\t{size}\n")


class Fetcher:
    """GET files one at a time, at most one request every INTERVAL_S seconds."""

    def __init__(self):
        self.requests = 0
        self._last = 0.0

    def get(self, url: str) -> bytes:
        delay = BACKOFF_S
        for attempt in range(1, MAX_TRIES + 1):
            wait = INTERVAL_S - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                self.requests += 1
                with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                    body = r.read()
                    log(url, r.status, len(body))
                    return body
            except urllib.error.HTTPError as e:
                log(url, e.code, 0)
                if e.code not in (429, 503) or attempt == MAX_TRIES:
                    raise Refused(f"HTTP {e.code} for {url}") from e
                after = e.headers.get("Retry-After", "")
                pause = int(after) if after.isdigit() else delay
                if pause > MAX_WAIT_S:
                    raise Refused(f"HTTP {e.code} for {url}, Retry-After {after} s") from e
                print(f"  HTTP {e.code}, waiting {pause} s", file=sys.stderr)
                time.sleep(pause)
                delay *= 2
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                log(url, type(e).__name__, 0)
                if attempt == MAX_TRIES:
                    raise Refused(f"{url}: no answer after {MAX_TRIES} tries ({e})") from e
                time.sleep(delay)
                delay *= 2
            finally:
                self._last = time.monotonic()
        raise AssertionError("unreachable")


def download(dry_run: bool) -> int:
    urls = list(dict.fromkeys(r["thumbnail_url"] for r in picks()))
    todo = [u for u in urls if not cache_path(u).exists()]
    print(f"{len(urls)} picked files, {len(urls) - len(todo)} cached, {len(todo)} to fetch")
    if dry_run or not todo:
        return 0
    fetcher = Fetcher()
    for i, url in enumerate(todo, 1):
        try:
            body = fetcher.get(url)
        except Refused as e:
            left = len(todo) - i + 1
            print(f"Stopped asking: {e}. {fetcher.requests} requests made, {left} files not fetched.",
                  file=sys.stderr)
            return 1
        cache_path(url).write_bytes(body)
        print(f"  {i}/{len(todo)} {len(body):>8} bytes  {urllib.parse.unquote(url.rsplit('/', 1)[-1])[:70]}")
    print(f"{fetcher.requests} requests made. Every picked file is cached in {FILES.relative_to(REPO)}")
    return 0


# --- Credits from the cached Commons answers ------------------------------------

def commons_pages() -> dict[str, dict]:
    """Every file page in crossing.photos' cached Commons answers, by title ("File:...")."""
    pages: dict[str, dict] = {}
    for path in sorted(SEARCH_CACHE.glob("*.json")):
        answer = json.loads(path.read_text(encoding="utf-8")).get("response", {})
        for page in answer.get("query", {}).get("pages", []):
            if page.get("imageinfo"):
                pages[page["title"]] = page
    return pages


def commons_title(commons_url: str) -> str:
    return urllib.parse.unquote(commons_url.rsplit("/wiki/", 1)[1]).replace("_", " ")


HIDDEN = re.compile(r"<(\w+)[^>]*display:\s*none[^>]*>.*?</\1>", re.S)


def plain(value: str) -> str:
    """Commons extmetadata as plain text: hidden spans dropped, then tags stripped and spaces collapsed."""
    return re.sub(r"\s+([.,;:])", r"\1", strip_html(HIDDEN.sub("", value or "")))


def extmeta(page: dict | None, name: str) -> str:
    if not page:
        return ""
    return plain(((page.get("imageinfo") or [{}])[0].get("extmetadata") or {}).get(name, {}).get("value", ""))


def clean_date(value: str) -> str | None:
    """The date the photo was taken, as Commons gives it, without its time or notes ("according to Exif data")."""
    value = re.sub(r"\(according to Exif data\)?|^Taken on\s+", "", value).strip(" ,")
    if m := re.match(r"\d{4}-\d{2}-\d{2}", value):
        return m.group(0)
    value = re.sub(r",?\s+\d{1,2}:\d{2}(:\d{2})?.*$", "", value)
    return value or None


def licence_url(url: str) -> str | None:
    """The licence's own page, over https. None for public domain files, which Commons gives no URL."""
    url = url.strip()
    if not url:
        return None
    return re.sub(r"^http://(creativecommons\.org)", r"https://\1", url)


# --- Spoilers: the episode a photo's words are safe from --------------------------

def named_places() -> list[tuple[str, str]]:
    """Each named feature's name and the episode it is met at ('' for context places, which always show)."""
    out = [(n, "") for n in ALWAYS_NAMED]
    for layer in STORY_LAYERS:
        for f in json.loads((DATA / f"{layer}.geojson").read_text(encoding="utf-8"))["features"]:
            p = f["properties"]
            if p.get("name"):
                out.append((p["name"], "" if p.get("role") == "context" else p["first_seen"]))
    for e in json.loads((DATA / "elsewhere.json").read_text(encoding="utf-8")):
        out.append((e["name"], e["first_seen"]))
    return out


def safe_from(text: str, named: list[tuple[str, str]]) -> str:
    """The first episode at which every place `text` names is met. A name counts as met once any name
    holding it is ("Animas" with the Animas Valley), as in the spoiler-leak test."""
    since = ""
    for name, _ in named:
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            met = min(fs for n, fs in named if name in n)
            since = max(since, met)
    return since


# --- Build (from the cache only) ---------------------------------------------------

def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:48].strip("-")


def file_name(row: dict) -> str:
    """A readable, stable name for the photo's WebP file."""
    return f"{slug(row['file_title'])}-{hashlib.sha1(row['commons_url'].encode()).hexdigest()[:6]}.webp"


def to_webp(data: bytes) -> tuple[bytes, int, int]:
    """The image at LONG_SIDE px on its long side, in sRGB, as WebP with no metadata."""
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    im = im.convert("RGB")
    if icc:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
    im.thumbnail((LONG_SIDE, LONG_SIDE), Image.Resampling.LANCZOS)
    bare = Image.frombytes("RGB", im.size, im.tobytes())  # a new image: no EXIF, XMP or ICC comes along
    out = io.BytesIO()
    bare.save(out, "WEBP", quality=QUALITY, method=6)
    return out.getvalue(), bare.width, bare.height


def hand_text(path: Path = TEXT) -> dict[str, dict]:
    with path.open(encoding="utf-8") as f:
        return {r["file_title"]: r for r in csv.DictReader(f)}


def features_by_id() -> dict[str, dict]:
    out = {}
    for layer in ("places", "stops"):
        for f in json.loads((DATA / f"{layer}.geojson").read_text(encoding="utf-8"))["features"]:
            out[f["properties"]["id"]] = f["properties"]
    return out


def photo_record(row: dict, page: dict | None, text: dict, place: dict, named: list[tuple[str, str]]) -> dict:
    author = text.get("author") or extmeta(page, "Artist") or extmeta(page, "Credit")
    record = {
        "file": f"photos/{file_name(row)}",
        "title": row["file_title"],
        "author": author,
        "licence": extmeta(page, "LicenseShortName") or row["licence"],
        "licence_url": licence_url(extmeta(page, "LicenseUrl") or row["licence_url"]),
        "date": clean_date(extmeta(page, "DateTimeOriginal")) if page else None,
        "commons_url": row["commons_url"],
        "via": row["via"],
        "alt": text["alt"],
    }
    place_fs = "" if place.get("role") == "context" else place["first_seen"]
    since = safe_from(" ".join([record["title"], record["alt"], author]), named)
    if since > place_fs:
        record["first_seen"] = since
    return record


def build() -> int:
    rows = picks()
    pages = commons_pages()
    texts = hand_text()
    features = features_by_id()
    named = named_places()
    missing = [r["file_title"] for r in rows if not cache_path(r["thumbnail_url"]).exists()]
    no_alt = sorted({r["file_title"] for r in rows if not texts.get(r["file_title"], {}).get("alt")})
    if missing or no_alt:
        for t in missing:
            print(f"not downloaded yet: {t} (run `download` first)", file=sys.stderr)
        for t in no_alt:
            print(f"no alt text in {TEXT.relative_to(REPO)}: {t}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written: dict[str, tuple[int, int]] = {}
    entries: dict[str, dict] = {}
    for row in rows:
        name = file_name(row)
        if name not in written:
            data, w, h = to_webp(cache_path(row["thumbnail_url"]).read_bytes())
            (OUT_DIR / name).write_bytes(data)
            written[name] = (w, h)
        place = features[row["place_id"]]
        entry = entries.setdefault(row["place_id"], {
            "place_id": row["place_id"],
            "stop_ids": [s for s in row["stop_ids"].split(";") if s],
            "photos": [],
        })
        record = photo_record(row, pages.get(commons_title(row["commons_url"])), texts[row["file_title"]], place,
                              named)
        w, h = written[name]
        entry["photos"].append({"file": record.pop("file"), "width": w, "height": h, **record})
    for stale in sorted(set(p.name for p in OUT_DIR.glob("*.webp")) - set(written)):
        (OUT_DIR / stale).unlink()
        print(f"removed {stale}, no longer picked")
    OUT_JSON.write_text(json.dumps(list(entries.values()), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    total = sum((OUT_DIR / n).stat().st_size for n in written)
    later = [(e["place_id"], p["title"], p["first_seen"]) for e in entries.values() for p in e["photos"]
             if "first_seen" in p]
    print(f"Wrote {len(written)} WebP files ({total / 1e6:.2f} MB) to {OUT_DIR.relative_to(REPO)} and "
          f"{sum(len(e['photos']) for e in entries.values())} photos for {len(entries)} places to "
          f"{OUT_JSON.relative_to(REPO)}")
    for place_id, title, fs in later:
        print(f"  {place_id}: {title!r} names a place met at {fs}, so it shows from {fs}")
    if total > BUDGET_BYTES:
        print(f"Over the {BUDGET_BYTES / 1e6:.0f} MB budget", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["download"]:
        return download("--dry-run" in argv)
    if argv[:1] == ["build"]:
        return build()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
