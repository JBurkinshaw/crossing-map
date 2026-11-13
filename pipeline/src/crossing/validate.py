"""Validate every published story layer in data/ against its schema.

Run from the repo root: uv run --project pipeline python -m crossing.validate
Exits non-zero on the first file with errors, after listing all its errors.
"""

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data"
SCHEMA = DATA / "schema" / "story-layer.schema.json"
MAX_DECIMALS = 5  # about 1 m; the plan rounds all coordinates to this
INCIPIT_WORDS = 5  # the most Spanish words of a line the site may publish (plan, section 3)


def too_precise(coords) -> bool:
    """True if any coordinate in a nested GeoJSON coordinate array has more than MAX_DECIMALS places."""
    if isinstance(coords, (int, float)):
        return round(coords, MAX_DECIMALS) != coords
    return any(too_precise(c) for c in coords)


def check_file(path: Path, validator: Draft202012Validator) -> list[str]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in validator.iter_errors(doc)]
    seen: set[str] = set()
    features = doc.get("features") if isinstance(doc, dict) else None
    for i, feature in enumerate(features if isinstance(features, list) else []):
        # Malformed features are already reported by the schema; skip the extra checks.
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            continue
        fid = feature["properties"].get("id")
        if fid in seen:
            errors.append(f"features/{i}: duplicate id {fid}")
        seen.add(fid)
        if too_precise(feature.get("geometry", {}).get("coordinates", [])):
            errors.append(f"features/{i} ({fid}): coordinates have more than {MAX_DECIMALS} decimals")
    return errors


def check_translations(path: Path) -> list[str]:
    """Schema, plus the copyright guardrail (incipits only) and links to known features."""
    schema = json.loads((DATA / "schema" / "translations.schema.json").read_text(encoding="utf-8"))
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
              for e in Draft202012Validator(schema).iter_errors(doc)]
    if errors or not isinstance(doc, list):
        return errors
    first_seen, kind = {}, {}
    # A line points at a stop, place or area, or (talk on the road) at a route segment.
    for name, k in (("stops", "stop"), ("places", "place"), ("areas", "area"), ("journeys", "road")):
        layer = DATA / f"{name}.geojson"
        if layer.exists():
            for f in json.loads(layer.read_text(encoding="utf-8"))["features"]:
                first_seen[f["properties"]["id"]] = f["properties"].get("first_seen")
                kind[f["properties"]["id"]] = k
    seen: set[str] = set()
    for i, t in enumerate(doc):
        where = f"{i} ({t['id']})"
        if t["id"] in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(t["id"])
        if len(t["es_incipit"].split()) > INCIPIT_WORDS:
            errors.append(f"{where}: es_incipit is longer than {INCIPIT_WORDS} words; only an opening may be published")
        if not t["episode"].startswith(f"{t['part']}-") or t["first_seen"] < t["episode"]:
            errors.append(f"{where}: part, episode and first_seen disagree")
        ref = t["location_ref"]
        if ref is not None and ref not in first_seen:
            errors.append(f"{where}: location_ref {ref} is not a stop, place, area or route segment id")
        elif ref is not None and (first_seen[ref] or "") > t["first_seen"]:
            errors.append(f"{where}: location_ref {ref} is first seen after the line (a spoiler)")
        if t["location_kind"] != (kind.get(ref) if ref is not None else None):
            errors.append(f"{where}: location_kind {t['location_kind']} does not match location_ref {ref}")
    return errors


def check_questions(path: Path) -> list[str]:
    """Each open question has its fields, an episode id, and features that exist and are reached by then."""
    first = {}
    for layer in DATA.glob("*.geojson"):
        for f in json.loads(layer.read_text(encoding="utf-8"))["features"]:
            first[f["properties"]["id"]] = f["properties"].get("first_seen")
    errors = []
    for q in json.loads(path.read_text(encoding="utf-8")):
        missing = {"id", "title", "first_seen", "features", "shown", "other", "why"} - set(q)
        if missing:
            errors.append(f"{q.get('id')}: missing {sorted(missing)}")
            continue
        if not re.fullmatch(r"[1-4]-(0[1-9]|1[0-4])", q["first_seen"]):
            errors.append(f"{q['id']}: first_seen {q['first_seen']!r} is not an episode")
        for fid in q["features"]:
            if fid not in first:
                errors.append(f"{q['id']}: no feature {fid}")
    return errors


def main() -> int:
    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    files = sorted(DATA.glob("*.geojson"))
    failed = False
    for path in files:
        errors = check_file(path, validator)
        print(f"{path.name}: {'ok' if not errors else f'{len(errors)} errors'}")
        for e in errors:
            print(f"  {e}")
        failed = failed or bool(errors)
    episodes = DATA / "episodes.json"
    if episodes.exists():
        schema = json.loads((DATA / "schema" / "episodes.schema.json").read_text(encoding="utf-8"))
        errors = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
                  for e in Draft202012Validator(schema).iter_errors(json.loads(episodes.read_text(encoding="utf-8")))]
        print(f"episodes.json: {'ok' if not errors else f'{len(errors)} errors'}")
        for e in errors:
            print(f"  {e}")
        failed = failed or bool(errors)
        files.append(episodes)
    translations = DATA / "translations.json"
    if translations.exists():
        errors = check_translations(translations)
        print(f"translations.json: {'ok' if not errors else f'{len(errors)} errors'}")
        for e in errors:
            print(f"  {e}")
        failed = failed or bool(errors)
        files.append(translations)
    questions = DATA / "open-questions.json"
    if questions.exists():
        errors = check_questions(questions)
        print(f"open-questions.json: {'ok' if not errors else f'{len(errors)} errors'}")
        for e in errors:
            print(f"  {e}")
        failed = failed or bool(errors)
        files.append(questions)
    print(f"Checked {len(files)} files.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
