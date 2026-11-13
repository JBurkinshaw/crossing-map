"""Find the Spanish in the novel, match it to the Campbell guide, and build data/translations.json.

Run from the repo root:

    uv run --project pipeline python -m crossing.translations find
    uv run --project pipeline python -m crossing.translations build

`find` reads the private book text (private/book/text/<episode>.txt) and the cached
Campbell guide PDF (private/cache/translations/), and writes private working files
only: private/translations/spans.json holds each full Spanish span with its context,
for drafting translations and for a future private search index.

`build` joins those spans with our own English (review/stage-5/translations-review.csv,
seeded from private/translations/drafts/*.json) and writes the committed files:
data/translations.json and the two review CSVs. Committed files hold only an incipit
(at most INCIPIT_WORDS words) of each Spanish span, never the full span, and nothing
from the guide but its page numbers (see docs/plan.md, sections 3 and 8).
"""

import csv
import json
import re
import sys
import unicodedata
from bisect import bisect_right
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TEXT = REPO / "private" / "book" / "text"
GUIDE_PDF = REPO / "private" / "cache" / "translations" / "campbell-crossing.pdf"
GUIDE_URL = (
    "https://d41cfaf2-ac52-4400-a6e1-aaf2dee170dc.filesusr.com/ugd/"
    "842cf5_fac7639eeb8e4ed0812f996b15164ccd.pdf"
)
WORK = REPO / "private" / "translations"
SPANS = WORK / "spans.json"
GUIDE_JSON = WORK / "guide-entries.json"
DRAFTS = WORK / "drafts"
DATA = REPO / "data"
OUT = DATA / "translations.json"
REVIEW = REPO / "review" / "stage-5"
REVIEW_CSV = REVIEW / "translations-review.csv"
GAPS_CSV = REVIEW / "translation-gaps.csv"
ROAD_CSV = REVIEW / "road-refs.csv"  # talk on the road: runs of lines judged to be spoken on one route segment
WHERE_CSV = REVIEW / "where-spoken.csv"  # single lines judged by hand to be spoken at a stop, place, area or segment

INCIPIT_WORDS = 5
MATCH_MIN = 85  # rapidfuzz partial ratio for a guide match (plan, section 8)
ANCHOR_MIN = 92  # stricter score for the page anchors
ANCHOR_WORDS = 3  # an anchor entry must have at least this many Spanish words
PAGE_WINDOW = 6  # a guide entry may match a span within this many pages of its estimate
SPANISH_MIN = 0.75  # lingua confidence for a clause to count as Spanish
PART_PAGES = {1: 1, 2: 131, 3: 215, 4: 342}  # first Vintage page of each Part, from the guide
FIRST_PAGE = 3  # the text starts on Vintage page 3
LAST_PAGE = 426

# A trailing English dialogue tag: ", he said." / "? the old man wheezed." / ", said Billy."
SPEECH_VERBS = (
    r"said|says|asked|called|wheezed|whispered|answered|replied|repeated|shouted|cried|"
    r"murmured|muttered|told|added|nodded|offered|announced|explained|insisted|continued|"
    r"spat|hissed|sang|read|began|lied|smiled|laughed|grinned|yelled|croaked|rasped|grunted"
)
TAG = re.compile(
    rf"(?:^|(?<=[,?!.]))\s+(?:(?:he|she|they|it|i|we|you|the\s[\w' -]+?|[A-Z][\w']+(?:\s[A-Z][\w']+)?)\s+"
    rf"(?:\w+ly\s+)?(?:{SPEECH_VERBS})\b|(?:{SPEECH_VERBS})\s+(?:the\s[\w' -]+?|[A-Z][\w']+))[^?!]*$"
)
SENTENCE = re.compile(r"(?<=[.?!])\s+(?=[\"“‘'¿¡]?[A-ZÁÉÍÓÚÑ0-9])")
WORD = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+")
SPANISH_CHARS = re.compile(r"[áéíóúüñÁÉÍÓÚÜÑ¿¡]")
# Short Spanish words that may sit between two Spanish words in a run inside an English sentence.
GLUE = {"de", "del", "la", "el", "los", "las", "y", "e", "o", "que", "en", "a", "al", "con", "por", "para", "un", "una"}
# Of those, the ones that may lead a run; "a", "o" and "e" are too often English.
LEAD = {"de", "del", "la", "el", "los", "las", "en", "un", "una"}
# Words McCarthy's English uses that a dictionary lacks, and borrowings that read as English here.
ENGLISH_EXTRA = {
    "aint", "yessir", "nosir", "mam", "yonder", "reckon", "onliest", "dont", "doesnt", "didnt", "wasnt",
    "werent", "cant", "wont", "couldnt", "wouldnt", "shouldnt", "hadnt", "hasnt", "havent", "isnt",
    "youre", "theyre", "thats", "whats", "theres", "heres", "lets", "ive", "id", "youd", "hed", "shed",
    "youll", "ill", "itll", "theyll", "weve", "theyve", "youve", "im", "hes", "shes", "okay", "ok",
    "gonna", "gotta", "nothin", "somethin",
    # Spanish loans that are ordinary words in the English of the Southwest
    "rancho", "ranchero", "corral", "corrals", "canyon", "canyons", "mesa", "mesas", "arroyo", "arroyos",
    "adobe", "patio", "plaza", "plazas", "rodeo", "lariat", "lasso", "bronco", "pinto", "palomino",
    "sombrero", "serape", "poncho", "tortilla", "tortillas", "chile", "chili", "coyote", "coyotes",
    "javelina", "javelinas", "cholla", "ocotillo", "mesquite", "yucca", "sotol", "vaquero", "vaqueros",
    "hacienda", "haciendas", "cantina", "cantinas", "gringo", "gringos", "peon", "peons", "remuda",
    "bosal", "riata", "reata", "tequila", "mescal", "mezcal", "chaps", "chaparral", "creosote",
    "pinon", "pinons", "pinyon", "lechuguilla",
}
# Common Spanish words a big English dictionary also lists; they do not count as English in a clause.
SPANISH_COMMON = set("""
a al de del el la las los lo le les me te se mi tu su sus y o u e en es no si sí que con por para un una
uno unos unas ella ellos ellas usted ustedes yo nos nada todo toda todos mas más pero como cómo cuando
donde dónde ya muy bien bueno buena hay ha he va voy vamos ver vino vida casa hombre mundo dios
madre padre hijo hija hermano mano cosa son era fue soy eres está esta este esto eso ese esa allá
alla aqui aquí ahora tan tanto mucho poco otro otra otros nunca siempre sabe sé saber dice dijo
""".split())
# Guide headwords that are also common English words, so are not taken as Spanish on sight.
LEXICON_STOP = {"era", "es", "tras", "otro"}
# Lowercase tokens that look Spanish to the model but are English or names in this book.
NOT_SPANISH = {"echols", "boyd", "billy", "parham", "quijada", "arnulfo"}

EPISODE_FILE = re.compile(r"^([1-4])-(\d\d)\.txt$")


def fold(s: str) -> str:
    """Accent- and case-folded text with punctuation reduced to spaces, for matching and search."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("’", "'").replace("'", "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


# A speech tag in the narration (", he said.", "? she said.", ", Billy said."): the incipit stops before it, so it
# holds only the speaker's Spanish. A rare Spanish "he" (I have) after a comma is cut too, which only shortens it.
# The text sometimes closes a line with a curly apostrophe where a comma belongs, so that counts as a break too.
SPEECH_TAG = re.compile(rf"(?<=[,?!\u2019])\s+(?:(?:{SPEECH_VERBS}|wrote|he|she|they|it|the|his|her|their)\b"
                        rf"|[A-Z][a-z]+\s+(?:{SPEECH_VERBS}|wrote)\b).*$", re.S)


def incipit(es: str, n: int = INCIPIT_WORDS) -> str:
    """The opening words of a span's Spanish, at most n, with an ellipsis when cut."""
    text = " ".join(es.split())
    spoken = SPEECH_TAG.sub("", text).rstrip(",\u2019")
    words = spoken.split()
    cut = " ".join(words[:n])
    return cut + ("…" if len(words) > n or spoken != text else "")


# ---------- the Campbell guide (matching only: its English is never kept) ----------

def parse_guide(pdf: Path = GUIDE_PDF) -> list[dict]:
    """Each guide entry's Vintage page, Part and Spanish opening. The English in brackets is dropped."""
    from pypdf import PdfReader

    if not pdf.exists():
        sys.exit(f"Missing {pdf}. Download it once with: curl -sSL -o {pdf} '{GUIDE_URL}'")
    lines = "\n".join(p.extract_text() for p in PdfReader(pdf).pages).splitlines()
    parts = {"PART ONE": 1, "PART TWO": 2, "PART THREE": 3, "PART FOUR": 4}
    entries: list[dict] = []
    page, part, depth = None, 1, 0
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("The Crossing Spanish Page", "Lt. Jim Campbell", "www.")):
            continue
        # Part and page headings also close a gloss the guide left without its ")".
        if line.upper() in parts:
            part, depth = parts[line.upper()], 0
            continue
        m = re.fullmatch(r"(?:Page\s+)?(\d{2,3})", line)  # the guide once prints a lone "70"
        if m:
            page, depth = int(m.group(1)), 0
            continue
        if depth > 0:  # inside a multi-line English gloss
            depth += line.count("(") - line.count(")")
            continue
        if "(" not in line or page is None:
            continue
        es = line.split("(", 1)[0].strip().rstrip("-–:").strip()
        depth = line.count("(") - line.count(")")
        if not fold(es):
            continue
        entries.append({"n": len(entries), "page": page, "part": part, "es": es, "es_fold": fold(es.replace("...", " ")),
                        "abbreviated": "..." in es or "…" in es})
    # The guide lists some pages out of order (Part Four's 353-357 come after 368, plan section 8).
    # Their printed page may be wrong, so they are not used as page anchors and match more loosely.
    top = 0
    for e in entries:
        e["out_of_order"] = e["page"] < top
        top = max(top, e["page"])
    return entries


# ---------- finding Spanish in the text ----------

def load_episodes() -> list[dict]:
    eps = []
    offset = 0
    for path in sorted(TEXT.glob("*.txt")):
        m = EPISODE_FILE.match(path.name)
        if not m:
            continue
        text = path.read_text(encoding="utf-8")
        eps.append({"episode": path.stem, "part": int(m.group(1)), "text": text, "offset": offset})
        offset += len(text) + 1
    return eps


class Detector:
    def __init__(self, lexicon: set[str] = frozenset()) -> None:
        """lexicon: folded one-word guide entries, used only to recognise those words in English sentences."""
        self.lexicon = set(lexicon) - LEXICON_STOP
        from lingua import Language, LanguageDetectorBuilder

        self.es, self.en = Language.SPANISH, Language.ENGLISH
        self.model = LanguageDetectorBuilder.from_languages(self.en, self.es).with_preloaded_language_models().build()
        words = Path("/usr/share/dict/words")
        self.english = {w.strip().lower() for w in words.read_text().splitlines()} if words.exists() else set()
        self.english |= ENGLISH_EXTRA
        self._cache: dict[str, float] = {}

    def spanish(self, text: str) -> float:
        if text not in self._cache:
            self._cache[text] = self.model.compute_language_confidence(text, self.es)
        return self._cache[text]

    def is_english_word(self, w: str) -> bool:
        w = w.lower().strip("'")
        if w in self.english:
            return True
        for suf, rep in (("s", ""), ("es", ""), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"), ("ly", ""),
                         ("er", ""), ("est", ""), ("'s", ""), ("ies", "y"), ("ied", "y"), ("d", "")):
            if w.endswith(suf) and len(w) - len(suf) >= 3 and w[: -len(suf)] + rep in self.english:
                return True
        return False

    def clause_is_spanish(self, clause: str) -> bool:
        words = WORD.findall(clause)
        if not words:
            return False
        conf = self.spanish(clause)
        english_share = sum(w.lower() not in SPANISH_COMMON and self.is_english_word(w) for w in words) / len(words)
        if SPANISH_CHARS.search(clause) and conf >= 0.5 and english_share < 0.6:
            return True
        if conf >= SPANISH_MIN and english_share < 0.7:
            return True
        # Short lines ("Historia?") where the model is unsure but nothing reads as English.
        return conf >= 0.5 and english_share == 0 and not any(w[0].isupper() for w in words[1:])

    def word_is_spanish(self, w: str, first: bool) -> bool:
        lw = w.lower()
        if fold(lw) in self.lexicon:
            return True
        if lw in NOT_SPANISH or len(lw) < 3 or self.is_english_word(lw):
            return False
        if w[0].isupper() and not first:  # names of people and places are mapped elsewhere
            return False
        if SPANISH_CHARS.search(w):
            return True
        return self.spanish(lw) >= 0.9


def split_tag(sentence: str) -> tuple[str, str]:
    """Split a sentence into its speech and a trailing English dialogue tag, if any."""
    m = TAG.search(sentence)
    if m and m.start() > 0:
        return sentence[: m.start()].rstrip(), sentence[m.start():]
    return sentence, ""


def find_spans(eps: list[dict], det: Detector) -> tuple[list[dict], dict]:
    """Spanish spans: runs of Spanish sentences in a paragraph, and Spanish words in English sentences."""
    spans: list[dict] = []
    heavy = {1: 0, 2: 0, 3: 0, 4: 0}  # paragraphs that are mostly Spanish, for the plan's heuristic
    for ep in eps:
        n = 0
        pos = 0
        for pi, para in enumerate(ep["text"].split("\n")):
            para_start = pos
            pos += len(para) + 1
            if not para.strip():
                continue
            run: list[tuple[int, int]] = []  # (start, end) offsets in the paragraph of a Spanish run
            es_chars = 0
            cursor = 0
            pieces: list[tuple[int, int, str]] = []
            for sent in SENTENCE.split(para):
                start = para.index(sent, cursor)
                cursor = start + len(sent)
                speech, _tag = split_tag(sent)
                if det.clause_is_spanish(speech):
                    es_chars += len(speech)
                    gap = para[run[-1][1]:start] if run else None
                    if gap is not None and (not gap.strip() or _gap_is_tag(gap)):
                        run[-1] = (run[-1][0], start + len(speech))
                    else:
                        run.append((start, start + len(speech)))
                    if _tag:
                        pieces.append((start + len(speech), cursor, "tag"))
                else:
                    for ws, we in _word_runs(sent, det):
                        pieces.append((start + ws, start + we, "word"))
            if es_chars > 0.5 * len(para):
                heavy[ep["part"]] += 1
            found = [(s, e, "speech") for s, e in run] + [(s, e, k) for s, e, k in pieces if k == "word"]
            for s, e, kind in sorted(found):
                es = para[s:e].strip().rstrip(",;:").strip()
                if set(fold(es).split()) <= {"no"}:  # empty, or a "No." that reads the same in English
                    continue
                n += 1
                spans.append({
                    "id": f"tr-{ep['episode']}-{n:03d}",
                    "part": ep["part"],
                    "episode": ep["episode"],
                    "para": pi,
                    "offset": ep["offset"] + para_start + s,
                    "kind": kind,
                    "es": es,
                    "es_fold": fold(es),
                    "words": len(es.split()),
                })
    # A Spanish word inside English narration ("the alguacil") is glossed once, where it first appears.
    first: dict[str, dict] = {}
    kept = []
    for s in spans:
        if s["kind"] == "word":
            if s["es_fold"] in first:
                first[s["es_fold"]]["occurrences"] += 1
                continue
            s["occurrences"] = 1
            first[s["es_fold"]] = s
        kept.append(s)
    return kept, heavy


def _gap_is_tag(gap: str) -> bool:
    """True if the English between two Spanish sentences is only a dialogue tag, so they form one speech."""
    return bool(re.fullmatch(rf"[^.?!]*\b(?:{SPEECH_VERBS})\b[^.?!]*[.?!]?\s*", gap.strip())) and len(gap) < 60


def _word_runs(sentence: str, det: Detector) -> list[tuple[int, int]]:
    """Runs of Spanish words inside an English sentence, joined across short Spanish function words."""
    tokens = [(m.start(), m.end(), m.group()) for m in WORD.finditer(sentence)]
    flags = [det.word_is_spanish(w, i == 0) for i, (_, _, w) in enumerate(tokens)]
    runs: list[tuple[int, int]] = []
    i = 0
    while i < len(tokens):
        if not flags[i]:
            i += 1
            continue
        j = i
        while True:
            k = j + 1
            while k < len(tokens) and tokens[k][2].lower() in GLUE and not flags[k]:
                k += 1
            if k < len(tokens) and flags[k] and k - j <= 3:
                j = k
            else:
                break
        # take in a leading article or preposition ("la querencia", "de veras")
        s = i
        while s > 0 and tokens[s - 1][2].lower() in LEAD and i - s < 2:
            s -= 1
        runs.append((tokens[s][0], tokens[j][1]))
        i = j + 1
    return runs


# ---------- guide matching and pages ----------

def page_model(anchors: list[tuple[int, int]], total: int):
    """Interpolate a Vintage page from a global character offset, between monotone (offset, page) anchors."""
    pts = sorted(anchors)
    if len(pts) < 2:
        return lambda off: None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]

    def page(off: int) -> int:
        i = bisect_right(xs, off)
        if i == 0:
            a, b = 0, 1
        elif i == len(xs):
            a, b = len(xs) - 2, len(xs) - 1
        else:
            a, b = i - 1, i
        if xs[b] == xs[a]:
            return ys[a]
        p = ys[a] + (ys[b] - ys[a]) * (off - xs[a]) / (xs[b] - xs[a])
        return max(1, min(LAST_PAGE, round(p)))

    return page


def longest_increasing(pairs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Longest chain of (offset, page) pairs with both non-decreasing, dropping anchors out of order."""
    pairs = sorted(pairs)
    tails: list[int] = []  # smallest final page of a chain of each length
    ends: list[int] = []  # index in pairs of that chain's last item
    prev: list[int | None] = []
    for idx, (_, pg) in enumerate(pairs):
        k = bisect_right(tails, pg)
        prev.append(ends[k - 1] if k > 0 else None)
        if k == len(tails):
            tails.append(pg)
            ends.append(idx)
        else:
            tails[k], ends[k] = pg, idx
    out = []
    i = ends[-1] if ends else None
    while i is not None:
        out.append(pairs[i])
        i = prev[i]
    return out[::-1]


def match_guide(spans: list[dict], guide: list[dict], total: int) -> tuple[list[tuple[int, int]], int]:
    """Set guide_page and guide_score on spans; return the page anchors and the count of guide entries matched."""
    from rapidfuzz import fuzz

    # 1. Anchors: long guide entries matched by a near-exact score, kept in page order.
    cands = []
    for g in guide:
        if len(g["es_fold"].split()) < ANCHOR_WORDS or g["out_of_order"]:
            continue

        scored = [(fuzz.partial_ratio(g["es_fold"], s["es_fold"]), s) for s in spans if s["part"] == g["part"]
                  and len(s["es_fold"]) >= len(g["es_fold"]) * 0.6]
        scored = [x for x in scored if x[0] >= ANCHOR_MIN]
        if len(scored) == 1:
            cands.append((scored[0][1]["offset"], g["page"]))
    anchors = [(0, FIRST_PAGE)] + longest_increasing(cands) + [(total, LAST_PAGE)]
    page = page_model(anchors, total)
    for s in spans:
        s["page"] = page(s["offset"])

    # 2. Every guide entry: the best span within PAGE_WINDOW pages of its printed page.
    first_word = {s["es_fold"]: s for s in spans if s["kind"] == "word"}
    matched = 0
    for g in guide:
        gf = g["es_fold"]
        window = PAGE_WINDOW * 4 if g["out_of_order"] else PAGE_WINDOW
        best = None
        for s in spans:
            if abs(s["page"] - g["page"]) > window:
                continue
            sf = s["es_fold"]
            if len(gf.split()) <= 2 or len(sf.split()) <= 2:
                # Short entries ("Y tu", "tio") must appear in the span as whole words, or nearly all of it.
                score = 100 if f" {gf} " in f" {sf} " or (
                    f" {sf} " in f" {gf} " and len(sf) >= 0.8 * len(gf)) else 0
            elif len(gf) <= len(sf):
                score = fuzz.partial_ratio(gf, sf)
            else:
                score = fuzz.partial_ratio(sf, gf) if len(sf) >= 0.5 * len(gf) else 0
            key = (score, -abs(s["page"] - g["page"]))
            if score >= MATCH_MIN and (best is None or key > best[0]):
                best = (key, s)
        if best is None and gf in first_word:
            # A word we gloss once, at its first use, where the guide glosses a later use.
            best = ((100, 0), first_word[gf])
        if best:
            matched += 1
            s = best[1]
            # A span may hold several guide entries (a speech the guide splits); link the first.
            s.setdefault("guide", []).append({"n": g["n"], "page": g["page"], "score": round(best[0][0])})
            s["guide_page"] = s["guide"][0]["page"]
    return anchors, matched


# ---------- where it was spoken ----------

def deaccent(s: str) -> str:
    """Strip accents one character at a time, keeping string length (so offsets still line up)."""
    return "".join(unicodedata.normalize("NFD", c)[0] for c in s)


def toponyms(*names: str | None) -> set[str]:
    """Proper names to look for in the text: no descriptions ("The girl, at a fire"), with short forms."""
    out = set()
    for name in names:
        if not name:
            continue
        name = deaccent(re.sub(r"\s*\(.*?\)", "", name).split(",")[0].strip())
        if not name[:1].isupper() or name.startswith(("The ", "A ")):
            continue
        out.add(name)
        short = re.sub(r"^(?:Colonia|Hacienda de|Rancho|La|El|Los|Las)\s+", "", name)
        if short != name and short[:1].isupper():
            out.add(short)
    return {n for n in out if len(n) >= 4}


def load_places() -> tuple[dict[str, list[dict]], dict[str, str]]:
    """Candidate stops and places by episode, with names to look for; and every known id's first_seen."""
    layers = {}
    for name in ("stops", "areas", "places"):
        path = DATA / f"{name}.geojson"
        layers[name] = [f["properties"] for f in json.loads(path.read_text(encoding="utf-8"))["features"]] \
            if path.exists() else []
    first_seen = {p["id"]: p.get("first_seen") or p.get("episode") or "1-01" for ps in layers.values() for p in ps}
    place = {p["id"]: p for p in layers["places"]}
    by_episode: dict[str, list[dict]] = {}
    for p in layers["stops"]:
        ref = place.get(p.get("place_ref") or "", {})
        names = toponyms(p.get("name"), ref.get("name"), ref.get("name_in_text"))
        if names and p.get("episode"):
            by_episode.setdefault(p["episode"], []).append({"id": p["id"], "rank": 0, "names": names})
    # A place first named in the episode, as a stop or in passing, stands in when no stop is named.
    for p in layers["places"]:
        names = toponyms(p.get("name"), p.get("name_in_text"))
        if names and p.get("episode") and p.get("role") in ("stop", "passing"):
            by_episode.setdefault(p["episode"], []).append({"id": p["id"], "rank": 1, "names": names})
    return by_episode, first_seen


# The layer each kind of location_ref lives in. "road" is a route segment: talk on the road, shown as a corridor.
LAYER_KIND = {"stops": "stop", "places": "place", "areas": "area", "journeys": "road"}


def load_features() -> dict[str, dict]:
    """Every id a line may point at, with its location_kind, first_seen and episode."""
    out = {}
    for layer, kind in LAYER_KIND.items():
        path = DATA / f"{layer}.geojson"
        if not path.exists():
            continue
        for f in json.loads(path.read_text(encoding="utf-8"))["features"]:
            p = f["properties"]
            out[p["id"]] = {"kind": kind, "first_seen": p.get("first_seen") or p.get("episode") or "1-01",
                            "episode": p.get("episode")}
    return out


def load_hand_refs(features: dict[str, dict], line_ids: list[str]) -> dict[str, tuple[str, bool]]:
    """Where a line was spoken, judged by hand: line id -> (ref, whether it overrides the name heuristic).

    The judgements are made from the episode's stops and segments and the narration around the lines, with
    a reason in our own words. road-refs.csv lists runs of lines (first id, last id, segment) spoken while
    travelling one route segment; a run fills only lines the heuristic left without a place.
    where-spoken.csv lists single lines (id, ref, kind) and wins over the heuristic; an empty ref records a
    line the text does not place, and changes nothing. A ref must exist with the stated kind and not be
    first seen after the line, and a segment must be travelled in the line's own episode, or the build stops.
    """
    known = set(line_ids)
    out: dict[str, tuple[str, bool]] = {}

    def add(source: str, line: str, ref: str, kind: str, override: bool) -> None:
        episode = line[3:7]
        feature = features.get(ref)
        if line not in known:
            sys.exit(f"{source}: {line} is not a line id")
        if line in out:
            sys.exit(f"{source}: {line} is placed twice")
        if not feature or feature["kind"] != kind:
            sys.exit(f"{source}: {line}: {ref} is not a {kind} id")
        if kind == "road" and feature["episode"] != episode:
            sys.exit(f"{source}: {line}: {ref} is not a route segment travelled in episode {episode}")
        if feature["first_seen"] > episode:
            sys.exit(f"{source}: {line}: {ref} is first seen after the line (a spoiler)")
        out[line] = (ref, override)

    if ROAD_CSV.exists():
        for row in csv.DictReader(ROAD_CSV.open(encoding="utf-8")):
            first, last = row["first_id"], row["last_id"]
            if last[3:7] != first[3:7] or last < first:
                sys.exit(f"{ROAD_CSV.name}: {first}..{last} is not a run within one episode")
            for line in line_ids:
                if first <= line <= last:
                    add(ROAD_CSV.name, line, row["segment"], "road", False)
    if WHERE_CSV.exists():
        for row in csv.DictReader(WHERE_CSV.open(encoding="utf-8")):
            if row["ref"]:
                add(WHERE_CSV.name, row["id"], row["ref"], row["kind"], True)
            elif row["id"] not in known:
                sys.exit(f"{WHERE_CSV.name}: {row['id']} is not a line id")
    return out


def locate(ep_text: str, para_start: int, candidates: list[dict]) -> str | None:
    """The stop (else place) of this episode whose name the text gave most recently before the span."""
    before = deaccent(ep_text[:para_start])
    for rank in (0, 1):
        best = None
        for c in candidates:
            if c["rank"] != rank:
                continue
            for name in c["names"]:
                i = before.rfind(name)
                if i >= 0 and (best is None or i > best[0]):
                    best = (i, c["id"])
        if best:
            return best[1]
    return None


# ---------- commands ----------

def cmd_find() -> None:
    eps = load_episodes()
    if not eps:
        sys.exit(f"No episode text in {TEXT}")
    WORK.mkdir(parents=True, exist_ok=True)
    guide = parse_guide()
    GUIDE_JSON.write_text(json.dumps(guide, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    det = Detector({e["es_fold"] for e in guide if len(e["es_fold"].split()) == 1 and len(e["es_fold"]) >= 3})
    spans, heavy = find_spans(eps, det)
    total = eps[-1]["offset"] + len(eps[-1]["text"])
    anchors, matched = match_guide(spans, guide, total)
    by_episode, _ = load_places()
    texts = {e["episode"]: e["text"] for e in eps}
    for s in spans:
        paras = texts[s["episode"]].split("\n")
        start = sum(len(p) + 1 for p in paras[: s["para"]])
        s["location_ref"] = locate(texts[s["episode"]], start, by_episode.get(s["episode"], []))
        lo = max(0, s["para"] - 3)
        s["context"] = "\n".join(paras[lo: s["para"] + 2])  # private: for the translator only
    SPANS.write_text(json.dumps({"anchors": anchors, "heavy_paragraphs": heavy, "guide_entries": len(guide),
                                 "guide_matched": matched, "spans": spans}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    per_part = {p: sum(1 for s in spans if s["part"] == p) for p in (1, 2, 3, 4)}
    print(f"{len(guide)} guide entries, {matched} matched to a span; {len(anchors) - 2} page anchors")
    print(f"{len(spans)} Spanish spans by Part: {per_part}; Spanish-heavy paragraphs: {heavy}")
    print(f"wrote {SPANS.relative_to(REPO)} (private)")


REVIEW_FIELDS = ["id", "part", "episode", "page", "kind", "occurrences", "es_incipit", "words", "en", "confidence",
                 "note", "speaker", "listener", "location_ref", "location_kind", "guide_page", "skip", "reviewed"]
GAP_FIELDS = ["id", "part", "episode", "page", "kind", "es_incipit", "words", "en", "confidence", "note"]
ES_SEARCH = WORK / "es-search.json"  # accent-folded full spans: private, never published (see the README)
TRUE = (True, "true", "yes", "1")


def load_drafts() -> dict[str, dict]:
    """Our English drafts by span id: private draft batches first, then any non-empty review CSV cell (wins)."""
    drafts: dict[str, dict] = {}
    for path in sorted(DRAFTS.glob("*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            drafts[row["id"]] = row
    if REVIEW_CSV.exists():
        for row in csv.DictReader(REVIEW_CSV.open(encoding="utf-8")):
            drafts[row["id"]] = {**drafts.get(row["id"], {}), **{k: v for k, v in row.items() if v not in ("", None)}}
    return drafts


def slug(value) -> str | None:
    if not value or value in ("null", "none"):
        return None
    return re.sub(r"[^a-z0-9]+", "-", fold(str(value))).strip("-") or None


def cmd_build() -> None:
    if not SPANS.exists():
        sys.exit(f"Missing {SPANS}; run the find step first")
    spans = json.loads(SPANS.read_text(encoding="utf-8"))["spans"]
    drafts = load_drafts()
    features = load_features()
    hand = load_hand_refs(features, [s["id"] for s in spans])
    records, review_rows, gap_rows, search = [], [], [], {}
    for s in spans:
        d = drafts.get(s["id"], {})
        skip = d.get("skip") in TRUE
        # The review CSV may set location_ref by hand; "none" clears it (and keeps a hand reference off too).
        # A cell that only repeats the heuristic is not an edit, so a judgement in where-spoken.csv replaces it.
        loc = d.get("location_ref", s.get("location_ref"))
        cleared = loc in ("none", "null")
        loc = None if loc in (None, "", "none", "null") else loc
        ref, override = hand.get(s["id"], (None, False))
        if ref and not cleared and (loc is None or (override and loc == s.get("location_ref"))):
            loc = ref
        if loc and features.get(loc, {}).get("first_seen", "9-99") > s["episode"]:
            loc = None  # never point at something the reader has not met yet
        rec = {
            "id": s["id"],
            "part": s["part"],
            "episode": s["episode"],
            "page": s.get("page"),
            "es_incipit": incipit(s["es"]),
            "en": d.get("en") or None,
            "source": "site",
            "confidence": d.get("confidence") or None,
            "speaker": slug(d.get("speaker")),
            "listener": slug(d.get("listener")),
            "location_ref": loc,
            "location_kind": features[loc]["kind"] if loc else None,
            "first_seen": s["episode"],
            "guide_page": s.get("guide_page"),
        }
        row = {**rec, "kind": s["kind"], "occurrences": s.get("occurrences"), "words": s["words"],
               "note": d.get("note", ""), "skip": "yes" if skip else "", "reviewed": d.get("reviewed", "")}
        review_rows.append({k: ("" if row.get(k) is None else row[k]) for k in REVIEW_FIELDS})
        if skip:
            continue  # not Spanish after all (marked by the translator or the owner)
        records.append(rec)
        search[s["id"]] = s["es_fold"]
        if s.get("guide_page") is None:
            gap_rows.append({k: ("" if row.get(k) is None else row[k]) for k in GAP_FIELDS})
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ES_SEARCH.write_text(json.dumps(search, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    REVIEW.mkdir(parents=True, exist_ok=True)
    for path, fields, rows in ((REVIEW_CSV, REVIEW_FIELDS, review_rows), (GAPS_CSV, GAP_FIELDS, gap_rows)):
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    by_part = {p: sum(1 for r in records if r["part"] == p) for p in (1, 2, 3, 4)}
    print(f"{OUT.relative_to(REPO)}: {len(records)} translations {by_part}, "
          f"{sum(1 for r in records if r['en'])} with English, "
          f"{sum(1 for r in records if r['guide_page'])} linked to a guide page, {len(gap_rows)} gaps, "
          f"{len(review_rows) - len(records)} skipped as not Spanish, "
          f"{sum(1 for r in records if r['location_kind'] not in (None, 'road'))} placed at a stop, place or area, "
          f"{sum(1 for r in records if r['location_kind'] == 'road')} spoken on the road, "
          f"{sum(1 for r in records if r['location_kind'] is None)} with no place")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "find":
        cmd_find()
    elif cmd == "build":
        cmd_build()
    else:
        sys.exit("usage: python -m crossing.translations find|build")


if __name__ == "__main__":
    main()
