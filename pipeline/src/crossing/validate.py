"""Validate every published story layer in data/ against its schema.

Run from the repo root: uv run --project pipeline python -m crossing.validate
Exits non-zero on the first file with errors, after listing all its errors.
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data"
SCHEMA = DATA / "schema" / "story-layer.schema.json"
MAX_DECIMALS = 5  # about 1 m; the plan rounds all coordinates to this


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
    print(f"Checked {len(files)} files.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
