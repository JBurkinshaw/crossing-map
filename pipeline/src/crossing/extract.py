"""Find episodes and place mentions in the author's private copy of the novel.

Run from the repo root:
  uv run --project pipeline python -m crossing.extract [SEEDS_CSV]   (default pipeline/seeds/places.csv)

Reads private/book/the-crossing.epub. Writes only to private/book/:
  episodes.csv          part, episode, opening words, paragraph index, word count
  mentions.csv          seed id, name matched, part, episode, paragraph index
  text/<episode>.txt    each episode's paragraphs, separated by blank lines, which crossing.echo_check and
                        crossing.translations read
The text files never leave private/. The repo receives only episode numbers derived from these files,
by hand or by build scripts.

Episodes: McCarthy opens each scene with words in capitals. A paragraph that
starts with a run of four or more capital letters, followed later by lower
case, opens an episode. Parts are the book's own headings.
"""

import csv
import html
import posixpath
import re
import sys
import zipfile
from pathlib import Path

from crossing.paths import PRIVATE, SEEDS
from crossing.text import fold_name as fold

BOOK = PRIVATE / "book"
EPUB = BOOK / "the-crossing.epub"
TEXT = BOOK / "text"

OPENING = re.compile(r"^[A-Z][A-Z’'\- ]{3,}(?=[ ,.;:]|$)")
PART = re.compile(r"^\s*(?:Part\s+)?(I{1,3}|IV|One|Two|Three|Four)\s*$", re.I)
PART_NUMBER = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "one": 1, "two": 2, "three": 3, "four": 4}


def blocks(epub: Path) -> list[tuple[str, str]]:
    """The book as (tag, text) blocks in reading order."""
    z = zipfile.ZipFile(epub)
    # The package file may sit in a subfolder (often OEBPS/); META-INF/container.xml names it.
    opf_path = re.search(r'full-path="([^"]+)"', z.read("META-INF/container.xml").decode())[1]
    opf = z.read(opf_path).decode()
    root = posixpath.dirname(opf_path)
    manifest = {i: h for h, i in re.findall(r'<item[^>]*href="([^"]+)"[^>]*id="([^"]+)"', opf)}
    out = []
    for idref in re.findall(r'<itemref[^>]*idref="([^"]+)"', opf):
        doc = z.read(posixpath.join(root, manifest[idref])).decode()
        for tag, inner in re.findall(r"<(h\d|p)\b[^>]*>(.*?)</\1>", doc, re.S):
            text = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
            if text:
                out.append((tag, " ".join(text.split())))
    return out


def episodes(book: list[tuple[str, str]]) -> list[dict]:
    found, part, n = [], 0, 0
    for i, (tag, text) in enumerate(book):
        m = PART.match(text) if tag.startswith("h") else None
        if m:
            part, n = PART_NUMBER[m.group(1).lower()], 0
            continue
        if part and tag == "p" and OPENING.match(text) and re.search(r"[a-z]", text):
            n += 1
            words = OPENING.match(text).group(0).split()
            found.append({"part": part, "episode": f"{part}-{n:02d}", "opening": " ".join(words[:4]).title(),
                          "start": i})
    for e, nxt in zip(found, found[1:] + [{"start": len(book)}], strict=True):
        e["end"] = nxt["start"]
        e["words"] = sum(len(t.split()) for _, t in book[e["start"]:e["end"]])
    return found


def write_text(book: list[tuple[str, str]], eps: list[dict], folder: Path = TEXT) -> None:
    """Each episode's paragraphs (headings dropped), separated by blank lines, as folder/<episode>.txt."""
    folder.mkdir(parents=True, exist_ok=True)
    for e in eps:
        paragraphs = [text for tag, text in book[e["start"]:e["end"]] if tag == "p"]
        (folder / f"{e['episode']}.txt").write_text("\n\n".join(paragraphs), encoding="utf-8")


def main(seeds_path: str = str(SEEDS / "places.csv")) -> None:
    book = blocks(EPUB)
    eps = episodes(book)
    write_text(book, eps)
    with (BOOK / "episodes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["part", "episode", "opening", "start", "words"], extrasaction="ignore")
        w.writeheader()
        w.writerows(eps)
    counts = {p: sum(1 for e in eps if e["part"] == p) for p in (1, 2, 3, 4)}
    print(f"{len(eps)} episodes by Part: {counts} (plan section 2.1: 10, 8, 14, 9)")

    def episode_at(i: int) -> str:
        started = [e for e in eps if e["start"] <= i]
        return max(started, key=lambda e: e["start"])["episode"] if started else "front"

    folded = [fold(t) for _, t in book]
    with (BOOK / "mentions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "matched", "part", "episode", "paragraph"])
        for seed in csv.DictReader(open(seeds_path, encoding="utf-8")):
            others = [n for col in ("alt_names", "text_names") for n in seed.get(col, "").split(";") if n]
            names = [seed["name"], *others]
            hits = 0
            for name in names:
                pattern = re.compile(rf"\b{re.escape(fold(name))}\b")
                for i, text in enumerate(folded):
                    if pattern.search(text):
                        ep = episode_at(i)
                        w.writerow([seed["id"], name, ep.split("-")[0], ep, i])
                        hits += 1
            print(f"{seed['id']:26} {hits} mentions")


if __name__ == "__main__":
    main(*sys.argv[1:2])
