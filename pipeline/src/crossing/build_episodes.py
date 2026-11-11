"""Write data/episodes.json from private/book/episodes.csv (made by crossing.extract).

Run from the repo root: uv run --project pipeline python -m crossing.build_episodes
Publishes only each episode's opening words, as the plan's episode list does,
and its length in words. Summaries are written by hand and kept on rebuild.
"""

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "private" / "book" / "episodes.csv"
OUT = REPO / "data" / "episodes.json"
# Capitalised words that stay capitalised when an opening is put in sentence case.
PROPER = {"billy", "boyd"}


def sentence_case(opening: str) -> str:
    # The capitals in some openings are split by letter spacing ("H E"); rejoin a lone first letter.
    words = opening.replace("’", "'").split()
    if len(words) > 1 and len(words[0]) == 1 and words[0] != "I":
        words = [words[0] + words[1]] + words[2:]
    words = [w.lower() if w.lower() not in PROPER else w.capitalize() for w in words]
    return " ".join(words)[:1].upper() + " ".join(words)[1:]


def main() -> None:
    summaries = {}
    if OUT.exists():
        summaries = {e["episode"]: e["summary"] for e in json.loads(OUT.read_text(encoding="utf-8"))}
    episodes = [
        {
            "episode": r["episode"],
            "part": int(r["part"]),
            "opening": sentence_case(r["opening"]),
            "words": int(r["words"]),
            "pages": None,
            "summary": summaries.get(r["episode"], ""),
        }
        for r in csv.DictReader(SOURCE.open(encoding="utf-8"))
    ]
    OUT.write_text(json.dumps(episodes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{OUT.relative_to(REPO)}: {len(episodes)} episodes")


if __name__ == "__main__":
    main()
