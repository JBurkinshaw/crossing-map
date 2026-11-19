"""Validate every published file in data/ against its schema and against the other files.

Run from the repo root: uv run --project pipeline python -m crossing.validate
Checks every file, lists every error, and exits 1 if any file has errors or is missing.

Besides each schema, it checks what a schema cannot: every episode id names a real episode, every
reference points at a feature that exists and is reached no later than the thing pointing at it,
each journey's stops and segments are numbered without gaps, and the Oblique view's copies hold the
same features, first seen at the same episodes, as the flat layers, and every stop's point lies inside
its own area. A feature's leads (the second sources that place it too) must name each source once, give no
coordinate and show no earlier than their feature. Each photo must be on a place or stop that exists, with its
file in site/public/ at its stated size. It also checks that every glyph and vignette the data names
has an icon in the committed sprite, which CI cannot rebuild.

It also reports, without failing, the landform positions still to review: stops the terrain check flags
(review/positions/results.csv, from crossing.positions) that have no verdict for their current point in
review/positions/review.csv, and results computed for a point the stop no longer has.
"""

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator
from PIL import Image
from shapely.geometry import Point, shape

from crossing.paths import DATA, REPO, SITE_PUBLIC

SCHEMAS = DATA / "schema"
POSITIONS = REPO / "review" / "positions"
SPRITE_INDEX = SITE_PUBLIC / "sprites" / "glyphs.json"
LAYERS = ["places", "stops", "areas", "journeys", "mountain_glyphs", "vignettes", "landforms", "water_places",
          "context_places"]
OBLIQUE_LAYERS = ["places", "stops", "areas", "journeys", "vignettes"]
MAX_DECIMALS = 5  # about 1 m; docs/design.md, section 6, rounds all coordinates to this
INCIPIT_WORDS = 5  # the most Spanish words of a line the site may publish (docs/design.md, section 3)
SYNOPSIS_SENTENCES, SYNOPSIS_WORDS = 3, 70  # a stop's synopsis is a short card text (decision 0051)
LEAD_LAYERS = {"places", "stops", "areas"}  # the layers whose features may carry leads (decision 0065)
# A coordinate written into a lead's note: a decimal degree (31.4526) or degrees with a sign (108°). Leads state
# facts in words, and a second source's pin must not be republished through one.
COORDINATE = re.compile(r"\d+\.\d{3,}|\d+\s*°")


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
        if isinstance(p.get("synopsis"), str):
            errors += [f"features/{i} ({fid}): synopsis {e}" for e in synopsis_errors(p["synopsis"])]
        if "leads" in p:
            errors += [f"features/{i} ({fid}): {e}" for e in lead_errors(p, layer, episodes)]
    return errors


def lead_errors(p: dict, layer: str, episodes: set[str]) -> list[str]:
    """What the schema cannot check in a feature's leads: where they may be, one per source, a page only for Bell,
    no coordinates, and no lead dated before its feature."""
    if layer not in LEAD_LAYERS:
        return [f"leads are only for {', '.join(sorted(LEAD_LAYERS))}"]
    leads = [lead for lead in p["leads"] if isinstance(lead, dict)] if isinstance(p["leads"], list) else []
    errors = [f"leads name {source} twice" for source, n in Counter(lead.get("source") for lead in leads).items()
              if n > 1]
    for lead in leads:
        source = lead.get("source")
        if "page" in lead and source != "bell-2000":
            errors.append(f"lead {source}: only Bell's leads have a page")
        note = lead.get("note")
        if isinstance(note, str):
            if COORDINATE.search(note):
                errors.append(f"lead {source}: the note gives a coordinate")
            errors += [f"lead {source}: the note contains {name}"
                       for char, name in (("\u2014", "an em dash"), (";", "a semicolon")) if char in note]
        seen = lead.get("first_seen")
        if isinstance(seen, str):
            if seen not in episodes:
                errors.append(f"lead {source}: first_seen {seen} is not an episode in episodes.json")
            elif isinstance(p.get("first_seen"), str) and seen < p["first_seen"]:
                errors.append(f"lead {source}: first_seen {seen} is before its feature's {p['first_seen']}")
    return errors


def synopsis_errors(text: str) -> list[str]:
    """What breaks the house rules for a stop's synopsis: its length, and the punctuation the site never uses."""
    errors = []
    sentences = len(re.findall(r"[.!?][”’\")\]]*(?=\s|$)", text.strip()))
    if sentences > SYNOPSIS_SENTENCES:
        errors.append(f"has {sentences} sentences, more than {SYNOPSIS_SENTENCES}")
    if len(text.split()) > SYNOPSIS_WORDS:
        errors.append(f"has {len(text.split())} words, more than {SYNOPSIS_WORDS}")
    errors += [f"contains {name}" for char, name in (("\u2014", "an em dash"), (";", "a semicolon")) if char in text]
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
        # A drawing stands beside a stop or place, or at a point along a journey leg (decision 0066).
        "vignettes": {p["id"] for name in ("places", "stops") for p in properties(layers[name])}
        | {p["id"] for p in properties(layers["journeys"]) if p.get("kind") == "route-segment"},
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
    # A drawing beside a pin the reader has not reached would say where the story goes (crossing.build_vignettes).
    pin_seen = {p["id"]: p.get("first_seen") for name in ("places", "stops", "journeys")
                for p in properties(layers[name])}
    for p in properties(layers["vignettes"]):
        seen = pin_seen.get(p.get("place_ref"))
        if seen and isinstance(p.get("first_seen"), str) and p["first_seen"] < seen:
            errors.append(f"vignettes.geojson {p['id']}: first_seen {p['first_seen']} is before its pin's {seen}")
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


def check_points_in_areas(stops: dict, areas: dict) -> list[str]:
    """A stop with an area is drawn as its area, and its point is the best guess inside it."""
    points = {f["properties"]["id"]: f["geometry"]["coordinates"] for f in stops["features"]}
    errors = []
    for area in areas["features"]:
        stop = area["properties"]["id"].removeprefix("area-")
        if stop in points and not shape(area["geometry"]).contains(Point(points[stop])):
            errors.append(f"{stop}: its point lies outside {area['properties']['id']}")
    return errors


def check_region_rings(doc) -> list[str]:
    """Regions' outer rings must run clockwise and their holes anticlockwise: the map draws a region's band with a
    line offset to the right of the ring (site/src/map/StoryLayers.tsx), which is inside only in that direction."""

    def clockwise(ring: list) -> bool:
        return sum(x0 * y1 - x1 * y0 for (x0, y0, *_), (x1, y1, *_) in zip(ring, ring[1:], strict=False)) < 0

    errors = []
    for p, g in ((f["properties"], f["geometry"]) for f in doc["features"] if f["properties"].get("kind") == "region"):
        for polygon in [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]:
            if not clockwise(polygon[0]) or any(clockwise(hole) for hole in polygon[1:]):
                errors.append(f"{p['id']}: rings must run clockwise outside and anticlockwise in holes")
                break
    return errors


def check_oblique(flat: dict, oblique: dict, layer: str) -> list[str]:
    """The Oblique copy holds the same features as the flat layer, with the same properties: only the points move.
    A text change in the flat layer needs `crossing.plan_oblique --properties`, or the copy keeps the old text."""
    a = {p["id"]: p for p in properties(flat)}
    b = {p["id"]: p for p in properties(oblique)}
    errors = [f"{fid}: only in the flat layer" for fid in sorted(a.keys() - b.keys())]
    errors += [f"{fid}: only in the oblique layer" for fid in sorted(b.keys() - a.keys())]
    for fid in sorted(a.keys() & b.keys()):
        differ = sorted(k for k in a[fid].keys() | b[fid].keys() if a[fid].get(k) != b[fid].get(k))
        if differ:
            errors.append(f"{fid}: {', '.join(differ)} differ from the flat layer's; "
                          "run crossing.plan_oblique --properties")
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
    """Schema, plus the copyright guardrail (incipits only, word lists sorted) and links to known features."""
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
        # The word list must stay in alphabetical order: in the line's own order it would publish the line.
        if t["es_words"] is not None and t["es_words"] != sorted(t["es_words"]):
            errors.append(f"{where}: es_words is not in alphabetical order")
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
        # Evidence links open the repository on GitHub at the build's commit, so each must name a file in it.
        errors += [f"{q['id']}: evidence {e['path']} is not in the repository"
                   for e in q.get("evidence", []) if not (REPO / e["path"]).exists()]
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


def check_photos(doc, layers: dict[str, dict], episodes: set[str], public: Path = SITE_PUBLIC) -> list[str]:
    """Schema, plus: each place and stop exists and each stop stands at the place, each photo's file is in
    site/public/ at the size given, and a photo's own first_seen is a real episode later than its place's."""
    errors = schema_errors(doc, load(SCHEMAS / "photos.schema.json"))
    if errors:
        return errors
    places = {p["id"]: p for p in properties(layers["places"])}
    stops = {p["id"]: p for p in properties(layers["stops"])}
    errors += [f"{i}: listed twice" for i, n in Counter(e["place_id"] for e in doc).items() if n > 1]
    for e in doc:
        pid = e["place_id"]
        owner = places.get(pid) or stops.get(pid)
        if owner is None:
            errors.append(f"{pid}: no such place or stop")
            continue
        if pid in stops and stops[pid].get("place_ref"):
            errors.append(f"{pid}: a stop at {stops[pid]['place_ref']}, so list its photos under that place")
        for sid in e["stop_ids"]:
            if sid not in stops:
                errors.append(f"{pid}: no stop {sid}")
            elif sid != pid and stops[sid].get("place_ref") != pid:
                errors.append(f"{pid}: stop {sid} does not stand at it (place_ref {stops[sid].get('place_ref')})")
        own = "" if owner.get("role") == "context" else owner["first_seen"]
        errors += [f"{pid}: {f} listed twice" for f, n in Counter(p["file"] for p in e["photos"]).items() if n > 1]
        for photo in e["photos"]:
            path = public / photo["file"]
            if not path.exists():
                errors.append(f"{pid}: no file {photo['file']}")
            else:
                with Image.open(path) as im:
                    if im.size != (photo["width"], photo["height"]):
                        errors.append(f"{pid}: {photo['file']} is {im.size[0]}x{im.size[1]}, "
                                      f"not {photo['width']}x{photo['height']}")
            fs = photo.get("first_seen")
            if fs is not None and fs not in episodes:
                errors.append(f"{pid}: {photo['file']} first_seen {fs} is not an episode in episodes.json")
            elif fs is not None and fs <= own:
                errors.append(f"{pid}: {photo['file']} first_seen {fs} is not later than its place's {own}, so drop it")
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


def same_point(a: str, b: str) -> bool:
    """Whether two "lon,lat" texts name the same point to 5 decimals. The review page writes "-109.05,30.55"
    where results.csv has "-109.05000,30.55000"."""
    try:
        return all(round(float(x), 5) == round(float(y), 5) for x, y in zip(a.split(","), b.split(","), strict=True))
    except ValueError:
        return False


def position_notes(stops: dict) -> list[str]:
    """Stops whose landform position needs the owner's review. Notes only: a flagged stop never fails the build."""
    results = POSITIONS / "results.csv"
    if not results.exists():
        return []
    verdicts = {}
    if (POSITIONS / "review.csv").exists():
        with (POSITIONS / "review.csv").open(encoding="utf-8") as f:
            verdicts = {r["id"]: r for r in csv.DictReader(f)}
    points = {f["properties"]["id"]: f["geometry"]["coordinates"] for f in stops["features"]}
    notes, unreviewed = [], []
    with results.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            here = points.get(r["stop"])
            point = f"{float(r['lon']):.5f},{float(r['lat']):.5f}"
            if here is None or f"{here[0]:.5f},{here[1]:.5f}" != point:
                notes.append(f"{r['stop']}: the stop has moved since crossing.positions ran; rerun it")
                continue
            v = verdicts.get(r["stop"])
            if r["flagged"] == "true" and not (v and v["verdict"] and same_point(v["point"], point)):
                unreviewed.append(r["stop"])
    if unreviewed:
        notes.append(f"{len(unreviewed)} flagged stops without a verdict (?review=positions): {', '.join(unreviewed)}")
    return notes


def report(name: str, errors: list[str]) -> bool:
    print(f"{name}: {'ok' if not errors else f'{len(errors)} errors'}")
    for e in errors:
        print(f"  {e}")
    return bool(errors)


def main() -> int:
    expected = ([f"{name}.geojson" for name in LAYERS] + [f"oblique/{name}.geojson" for name in OBLIQUE_LAYERS]
                + ["oblique/archives.json", "episodes.json", "translations.json", "open-questions.json",
                   "elsewhere.json", "photos.json"])
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
        failed |= report(f"{name}.geojson", check_layer(doc, name, episodes)
                         + (check_region_rings(doc) + check_points_in_areas(layers["stops"], doc)
                            if name == "areas" else []))
    for name in OBLIQUE_LAYERS:
        doc = load(DATA / "oblique" / f"{name}.geojson")
        errors = (check_layer(doc, name, episodes) + check_oblique(layers[name], doc, name)
                  + (check_region_rings(doc) if name == "areas" else []))
        failed |= report(f"oblique/{name}.geojson", errors)
    failed |= report("oblique/archives.json", schema_errors(load(DATA / "oblique" / "archives.json"),
                                                          load(SCHEMAS / "archives.schema.json")))
    failed |= report("references", check_references(layers))
    failed |= report("sprites", check_sprites(layers, load(SPRITE_INDEX)))
    failed |= report("translations.json", check_translations(load(DATA / "translations.json"), layers, episodes))
    failed |= report("open-questions.json", check_questions(load(DATA / "open-questions.json"), layers, episodes))
    failed |= report("elsewhere.json", check_elsewhere(load(DATA / "elsewhere.json"), layers["places"], episodes))
    failed |= report("photos.json", check_photos(load(DATA / "photos.json"), layers, episodes))
    for note in position_notes(layers["stops"]):
        print(f"positions (note, not an error): {note}")
    print(f"Checked {len(expected)} files.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
