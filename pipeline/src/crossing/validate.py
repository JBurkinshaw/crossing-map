"""Validate every published file in data/ against its schema and against the other files.

Run from the repo root: uv run --project pipeline python -m crossing.validate
Checks every file, lists every error, and exits 1 if any file has errors or is missing.

Besides each schema, it checks what a schema cannot: every episode id names a real episode, every
reference points at a feature that exists and is reached no later than the thing pointing at it,
each journey's stops and segments are numbered without gaps, and the Raised view's copies hold the
same features, first seen at the same episodes, as the flat layers. It also checks that every glyph and
vignette the data names has an icon in the committed sprite, which CI cannot rebuild.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

from crossing.paths import DATA, SITE_PUBLIC

SCHEMAS = DATA / "schema"
SPRITE_INDEX = SITE_PUBLIC / "sprites" / "glyphs.json"
LAYERS = ["places", "stops", "areas", "journeys", "mountain_glyphs", "vignettes", "landforms", "water_places",
          "context_places"]
RAISED_LAYERS = ["places", "stops", "areas", "journeys"]
MAX_DECIMALS = 5  # about 1 m; docs/design.md, section 6, rounds all coordinates to this
INCIPIT_WORDS = 5  # the most Spanish words of a line the site may publish (docs/design.md, section 3)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(doc, schema: dict) -> list[str]:
    return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
            for e in Draft202012Validator(schema).iter_errors(doc)]


def layer_schema(layer: str) -> dict:
    """The story-layer schema narrowed to one layer: the shared rules plus that layer's own."""
    return load(SCHEMAS / "story-layer.schema.json") | {"$ref": f"#/$defs/layers/{layer}"}


def too_precise(coords) -> bool:
    """True if any coordinate in a nested GeoJSON coordinate array has more than MAX_DECIMALS places."""
    if isinstance(coords, (int, float)):
        return round(coords, MAX_DECIMALS) != coords
    return any(too_precise(c) for c in coords)


def check_layer(doc, layer: str, episodes: set[str]) -> list[str]:
    errors = schema_errors(doc, layer_schema(layer))
    seen: set[str] = set()
    features = doc.get("features") if isinstance(doc, dict) else None
    for i, feature in enumerate(features if isinstance(features, list) else []):
        # Malformed features are already reported by the schema; skip the extra checks.
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            continue
        p = feature["properties"]
        fid = p.get("id")
        if fid in seen:
            errors.append(f"features/{i}: duplicate id {fid}")
        seen.add(fid)
        if too_precise(feature.get("geometry", {}).get("coordinates", [])):
            errors.append(f"features/{i} ({fid}): coordinates have more than {MAX_DECIMALS} decimals")
        for key in ("first_seen", "episode"):
            if isinstance(p.get(key), str) and p[key] not in episodes:
                errors.append(f"features/{i} ({fid}): {key} {p[key]} is not an episode in episodes.json")
        part, first = p.get("part"), p.get("first_seen")
        if isinstance(part, int) and isinstance(first, str) and first[:1] != str(part):
            errors.append(f"features/{i} ({fid}): part {p['part']} does not match first_seen {p['first_seen']}")
    return errors


def properties(doc) -> list[dict]:
    # Cross-file checks run even on a file whose schema check failed, so a malformed file must not crash them.
    features = doc.get("features", []) if isinstance(doc, dict) else []
    if not isinstance(features, list):
        return []
    return [f["properties"] for f in features if isinstance(f, dict) and isinstance(f.get("properties"), dict)]


def check_references(layers: dict[str, dict]) -> list[str]:
    """place_ref targets exist, and each journey is numbered 1, 2, 3 ... with no gaps."""
    targets = {
        "stops": {p["id"] for p in properties(layers["places"])},
        "areas": {p["id"] for p in properties(layers["places"])},
        "vignettes": {p["id"] for name in ("places", "stops") for p in properties(layers[name])},
        "landforms": {p["id"] for p in properties(layers["places"])},
        "water_places": {p["id"] for p in properties(layers["places"])},
    }
    errors = []
    for layer, allowed in targets.items():
        for p in properties(layers[layer]):
            ref = p.get("place_ref")
            if ref is None:
                continue
            # A stop may come before the book names its place (the place card stays hidden until then), so only
            # the target's existence is checked here.
            if ref not in allowed:
                errors.append(f"{layer}.geojson {p['id']}: place_ref {ref} is not a feature it may point at")
    # A landform line or water place carries the book's name, so it may not show before the place it stands for.
    place_seen = {p["id"]: p.get("first_seen") for p in properties(layers["places"])}
    for layer in ("landforms", "water_places"):
        for p in properties(layers[layer]):
            seen = place_seen.get(p.get("place_ref"))
            if seen and isinstance(p.get("first_seen"), str) and p["first_seen"] < seen:
                errors.append(f"{layer}.geojson {p['id']}: first_seen {p['first_seen']} is before its place's {seen}")
    for layer, kind, offset in (("stops", "stop", 0), ("journeys", "route-segment", 1)):
        by_journey: dict[str, list[int]] = defaultdict(list)
        stops = Counter(p.get("journey") for p in properties(layers["stops"]))
        for p in properties(layers[layer]):
            if p.get("kind") == kind and isinstance(p.get("sequence"), int):
                by_journey[p.get("journey")].append(p["sequence"])
        for journey, seqs in sorted(by_journey.items()):
            # A journey of n stops has n - 1 segments between them.
            expected = list(range(1, stops[journey] - offset + 1))
            if sorted(seqs) != expected:
                errors.append(f"{layer}.geojson {journey}: {kind} sequences are {sorted(seqs)}, "
                              f"not 1 to {len(expected)}")
    return errors


def check_raised(flat: dict, raised: dict, layer: str) -> list[str]:
    """The Raised copy holds the same features as the flat layer, each first seen at the same episode."""
    a = {p["id"]: p.get("first_seen") for p in properties(flat)}
    b = {p["id"]: p.get("first_seen") for p in properties(raised)}
    errors = [f"{fid}: only in the flat layer" for fid in sorted(a.keys() - b.keys())]
    errors += [f"{fid}: only in the raised layer" for fid in sorted(b.keys() - a.keys())]
    errors += [f"{fid}: first_seen {b[fid]} differs from the flat layer's {a[fid]}"
               for fid in sorted(a.keys() & b.keys()) if a[fid] != b[fid]]
    return errors


def check_episodes(doc) -> list[str]:
    errors = schema_errors(doc, load(SCHEMAS / "episodes.schema.json"))
    if errors:
        return errors
    ids = [e["episode"] for e in doc]
    errors += [f"{e}: listed twice" for e, n in Counter(ids).items() if n > 1]
    errors += [f"{e['episode']}: part {e['part']} does not match the episode id"
               for e in doc if e["episode"][0] != str(e["part"])]
    if ids != sorted(ids):
        errors.append("episodes are not in reading order")
    return errors


def check_translations(doc, layers: dict[str, dict], episodes: set[str]) -> list[str]:
    """Schema, plus the copyright guardrail (incipits only) and links to known features."""
    errors = schema_errors(doc, load(SCHEMAS / "translations.schema.json"))
    if errors or not isinstance(doc, list):
        return errors
    first_seen, kind = {}, {}
    # A line points at a stop, place or area, or (talk on the road) at a route segment.
    for name, k in (("stops", "stop"), ("places", "place"), ("areas", "area"), ("journeys", "road")):
        for p in properties(layers[name]):
            first_seen[p["id"]] = p.get("first_seen")
            kind[p["id"]] = k
    seen: set[str] = set()
    for i, t in enumerate(doc):
        where = f"{i} ({t['id']})"
        if t["id"] in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(t["id"])
        if len(t["es_incipit"].split()) > INCIPIT_WORDS:
            errors.append(f"{where}: es_incipit is longer than {INCIPIT_WORDS} words; only an opening may be published")
        for key in ("episode", "first_seen"):
            if t[key] not in episodes:
                errors.append(f"{where}: {key} {t[key]} is not an episode in episodes.json")
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


def check_questions(doc, layers: dict[str, dict], episodes: set[str]) -> list[str]:
    """Schema, plus: each question's episode exists, its features exist, and one of them is reached by then."""
    errors = schema_errors(doc, load(SCHEMAS / "open-questions.schema.json"))
    if errors:
        return errors
    first = {p["id"]: p.get("first_seen", "") for d in layers.values() for p in properties(d)}
    errors += [f"{q}: listed twice" for q, n in Counter(q["id"] for q in doc).items() if n > 1]
    for q in doc:
        if q["first_seen"] not in episodes:
            errors.append(f"{q['id']}: first_seen {q['first_seen']} is not an episode in episodes.json")
        for fid in q["features"]:
            if fid not in first:
                errors.append(f"{q['id']}: no feature {fid}")
        # A question may name later visits to its place (hidden until reached), but not show before all of them.
        reached = [first[fid] for fid in q["features"] if fid in first]
        if reached and min(reached) > q["first_seen"]:
            errors.append(f"{q['id']}: shown at {q['first_seen']}, before any of its features "
                          f"(first at {min(reached)})")
    return errors


def check_elsewhere(doc, places: dict, episodes: set[str]) -> list[str]:
    errors = schema_errors(doc, load(SCHEMAS / "elsewhere.schema.json"))
    if errors:
        return errors
    mapped = {p["id"].removeprefix("place-") for p in properties(places)}
    errors += [f"{i}: listed twice" for i, n in Counter(e["id"] for e in doc).items() if n > 1]
    errors += [f"{e['id']}: first_seen {e['first_seen']} is not an episode in episodes.json"
               for e in doc if e["first_seen"] not in episodes]
    errors += [f"{e['id']}: also mapped in places.geojson" for e in doc if e["id"] in mapped]
    return errors


def icon_names(layers: dict[str, dict]) -> set[str]:
    """The sprite icons the style asks for: site/src/map/relief.ts builds glyph names as
    <landform>-<NN>[-flip] and uses a vignette's `vignette` property as is."""
    names = set()
    for p in properties(layers["mountain_glyphs"]):
        if not isinstance(p.get("glyph"), int):
            continue  # the schema check reports it
        names.add(f"{p.get('landform') or 'peak'}-{p['glyph']:02d}{'-flip' if p.get('flip') else ''}")
    for p in properties(layers["vignettes"]):
        if p.get("vignette"):
            names.add(p["vignette"])
    return names


def check_sprites(layers: dict[str, dict], sprite: dict) -> list[str]:
    return [f"no sprite icon {name!r} in {SPRITE_INDEX.name}" for name in sorted(icon_names(layers) - set(sprite))]


def report(name: str, errors: list[str]) -> bool:
    print(f"{name}: {'ok' if not errors else f'{len(errors)} errors'}")
    for e in errors:
        print(f"  {e}")
    return bool(errors)


def main() -> int:
    expected = ([f"{name}.geojson" for name in LAYERS] + [f"raised/{name}.geojson" for name in RAISED_LAYERS]
                + ["raised/archives.json", "episodes.json", "translations.json", "open-questions.json",
                   "elsewhere.json"])
    missing = [name for name in expected if not (DATA / name).exists()]
    if missing:
        report("data/", [f"{name} is missing" for name in missing])
        return 1
    failed = False
    episodes_doc = load(DATA / "episodes.json")
    failed |= report("episodes.json", check_episodes(episodes_doc))
    episodes = {e.get("episode") for e in episodes_doc if isinstance(e, dict)}
    layers = {name: load(DATA / f"{name}.geojson") for name in LAYERS}
    for name, doc in layers.items():
        failed |= report(f"{name}.geojson", check_layer(doc, name, episodes))
    for name in RAISED_LAYERS:
        doc = load(DATA / "raised" / f"{name}.geojson")
        errors = check_layer(doc, name, episodes) + check_raised(layers[name], doc, name)
        failed |= report(f"raised/{name}.geojson", errors)
    failed |= report("raised/archives.json", schema_errors(load(DATA / "raised" / "archives.json"),
                                                          load(SCHEMAS / "archives.schema.json")))
    failed |= report("references", check_references(layers))
    failed |= report("sprites", check_sprites(layers, load(SPRITE_INDEX)))
    failed |= report("translations.json", check_translations(load(DATA / "translations.json"), layers, episodes))
    failed |= report("open-questions.json", check_questions(load(DATA / "open-questions.json"), layers, episodes))
    failed |= report("elsewhere.json", check_elsewhere(load(DATA / "elsewhere.json"), layers["places"], episodes))
    print(f"Checked {len(expected)} files.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
