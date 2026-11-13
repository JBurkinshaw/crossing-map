"""Check that no run of the novel's words is in the repo or the built site (plan section 3).

Run from the repo root: uv run --project pipeline python -m crossing.echo_check [--words N] [PATH ...]

Reads the private episode text (private/book/text/*.txt) and reports every run of N consecutive words
(default 8) that it shares with a tracked text file, or with site/dist/ if it has been built. With PATH
arguments, only those files and folders are scanned. Words are compared after folding case, accents,
curly quotes and punctuation, so "Don't" and "dont" match. Each match prints the file, the line and the
first N words of the run, never more, so the report holds no more of the novel than it must.
Exits 1 on a match. Skips with exit 0 when the private text is absent (as in CI).
"""

import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BOOK = REPO / "private" / "book" / "text"
DIST = REPO / "site" / "dist"
WORDS = 8
APOSTROPHES = re.compile(r"(?<=\w)['’ʼ](?=\w)")
WORD = re.compile(r"[a-z0-9]+")


def fold(text: str) -> str:
    """Lower case, accents dropped, and apostrophes inside words removed ("don’t" -> "dont")."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return APOSTROPHES.sub("", text.lower())


def words(text: str) -> list[tuple[str, int]]:
    """Each folded word with the line it is on (1-based)."""
    out = []
    for n, line in enumerate(fold(text).splitlines(), start=1):
        out.extend((w, n) for w in WORD.findall(line))
    return out


def novel_runs(n: int) -> set[tuple[str, ...]]:
    runs: set[tuple[str, ...]] = set()
    for path in sorted(BOOK.glob("*.txt")):
        ws = [w for w, _ in words(path.read_text(encoding="utf-8"))]
        runs.update(tuple(ws[i:i + n]) for i in range(len(ws) - n + 1))
    return runs


def targets(paths: list[str]) -> list[Path]:
    """Tracked files plus site/dist/, or the given paths (folders walked)."""
    if paths:
        found = []
        for p in map(Path, paths):
            p = p if p.is_absolute() else Path.cwd() / p
            found.extend(sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else [p])
        return found
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout
    found = [REPO / name for name in tracked.decode().split("\0") if name]
    if DIST.is_dir():
        found.extend(sorted(f for f in DIST.rglob("*") if f.is_file()))
    return [f for f in found if f.is_file()]


def read_text(path: Path) -> str | None:
    """The file as text, or None for a binary file."""
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan(text: str, runs: set[tuple[str, ...]], n: int) -> list[tuple[int, str, int]]:
    """Each maximal shared run as (line, its first n words, its length in words)."""
    ws = words(text)
    hits = [i for i in range(len(ws) - n + 1) if tuple(w for w, _ in ws[i:i + n]) in runs]
    out = []
    i = 0
    while i < len(hits):
        start = end = hits[i]
        while i + 1 < len(hits) and hits[i + 1] == end + 1:
            i += 1
            end = hits[i]
        out.append((ws[start][1], " ".join(w for w, _ in ws[start:start + n]), end - start + n))
        i += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--words", type=int, default=WORDS, help=f"run length to report (default {WORDS})")
    parser.add_argument("paths", nargs="*", help="files or folders to scan instead of the tracked files")
    args = parser.parse_args()
    if not BOOK.is_dir() or not any(BOOK.glob("*.txt")):
        print(f"Skipped: no private text in {BOOK.relative_to(REPO)}/, so there is nothing to compare.")
        return
    runs = novel_runs(args.words)
    files = targets(args.paths)
    matched, scanned = 0, 0
    for path in files:
        text = read_text(path)
        if text is None:
            continue
        scanned += 1
        for line, run, length in scan(text, runs, args.words):
            matched += 1
            name = path.relative_to(REPO) if path.is_relative_to(REPO) else path
            extra = f" (+{length - args.words} words)" if length > args.words else ""
            print(f"{name}:{line}: {run}{extra}")
    print(f"{matched} shared runs of {args.words} words in {scanned} text files.")
    sys.exit(1 if matched else 0)


if __name__ == "__main__":
    main()
