"""The cross-file rules in crossing.validate, on small hand-made documents."""

import copy

import pytest

from crossing import validate

EPISODES = {"1-01", "1-02", "2-01"}


def feature(fid, kind="stop", first_seen="1-01", geometry=None, **props):
    p = {"id": fid, "name": fid, "kind": kind, "part": int(first_seen[0]), "first_seen": first_seen,
         "certainty": "located", "method": "computed", "source": "this-site", "source_licence": "CC BY 4.0",
         "note_safe": "", "characters": [], "journey": "J1", "sequence": None, "place_ref": None,
         "uncertainty_m": None, "travel": None} | props
    point = {"type": "Point", "coordinates": [-108.5, 31.5]}
    return {"type": "Feature", "geometry": geometry or point, "properties": p}


def collection(*features):
    return {"type": "FeatureCollection", "features": list(features)}


@pytest.fixture
def layers():
    line = {"type": "LineString", "coordinates": [[-108.5, 31.5], [-108.4, 31.6]]}
    return {
        "places": collection(feature("place-a", kind="town", role="stop")),
        "stops": collection(feature("s1", sequence=1, place_ref="place-a"),
                            feature("s2", sequence=2, first_seen="1-02")),
        "areas": collection(),
        "journeys": collection(feature("j1-seg-01", kind="route-segment", sequence=1, first_seen="1-02",
                                       geometry=line)),
        "mountain_glyphs": collection(),
        "vignettes": collection(),
        "landforms": collection(feature("landform-a", kind="range", geometry=line, place_ref="place-a",
                                        name_source="gnis:1", axis="dem", elongation=2.0, len_m=1000,
                                        mpp0=134000)),
        "water_places": collection(feature("water-gnis-1", kind="spring", source="gnis", source_id="1")),
    }


def test_layers_pass(layers):
    for name, doc in layers.items():
        assert validate.check_layer(doc, name, EPISODES) == [], name
    assert validate.check_references(layers) == []


def test_unknown_episode_is_reported(layers):
    doc = collection(feature("s1", sequence=1, first_seen="2-12", part=2))
    errors = validate.check_layer(doc, "stops", EPISODES)
    assert any("2-12 is not an episode" in e for e in errors)


def test_layer_requires_its_own_properties():
    stop = feature("s1", sequence=1)
    del stop["properties"]["journey"]
    assert validate.check_layer(collection(stop), "stops", EPISODES)


def test_kind_must_belong_to_the_layer():
    assert validate.check_layer(collection(feature("x", kind="peak", sequence=1)), "stops", EPISODES)


def test_sequence_gap_is_reported(layers):
    layers["stops"]["features"][1]["properties"]["sequence"] = 3
    assert any("sequences" in e for e in validate.check_references(layers))


def test_missing_place_ref_target_is_reported(layers):
    layers["stops"]["features"][0]["properties"]["place_ref"] = "place-nowhere"
    assert any("place-nowhere" in e for e in validate.check_references(layers))


def test_raised_copy_must_match(layers):
    raised = copy.deepcopy(layers["stops"])
    raised["features"][1]["properties"]["first_seen"] = "1-01"
    raised["features"].pop(0)
    errors = validate.check_raised(layers["stops"], raised, "stops")
    assert any("only in the flat layer" in e for e in errors)
    assert any("first_seen differ" in e for e in errors)


def test_raised_copy_must_keep_the_flat_text(layers):
    raised = copy.deepcopy(layers["stops"])
    raised["features"][0]["properties"]["name"] = "An old name"
    assert any("name differ" in e for e in validate.check_raised(layers["stops"], raised, "stops"))


def question(**fields):
    return {"id": "q-a", "title": "A?", "first_seen": "1-01", "features": ["s2"], "shown": "x", "other": "y",
            "why": "z"} | fields


def test_question_before_all_its_features_is_reported(layers):
    errors = validate.check_questions([question()], layers, EPISODES)
    assert any("before any of its features" in e for e in errors)


def test_question_may_name_later_visits(layers):
    assert validate.check_questions([question(features=["s1", "s2"])], layers, EPISODES) == []


def test_question_episode_must_exist(layers):
    errors = validate.check_questions([question(first_seen="1-09", features=[])], layers, EPISODES)
    assert any("not an episode" in e for e in errors)


def test_episodes_must_be_unique_and_ordered():
    doc = [{"episode": e, "part": int(e[0]), "opening": "x", "words": 1, "pages": None, "summary": ""}
           for e in ("1-02", "1-01", "1-01")]
    errors = validate.check_episodes(doc)
    assert any("listed twice" in e for e in errors)
    assert any("reading order" in e for e in errors)


def test_missing_file_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(validate, "DATA", tmp_path)
    assert validate.main() == 1


def test_published_data_is_valid():
    assert validate.main() == 0


def test_check_sprites_reports_missing_icons():
    glyphs = {"features": [{"properties": {"landform": "mesa", "glyph": 3, "flip": True}},
                           {"properties": {"landform": None, "glyph": 11, "flip": False}}]}
    vignettes = {"features": [{"properties": {"vignette": "wolf"}}]}
    layers = {"mountain_glyphs": glyphs, "vignettes": vignettes}
    assert validate.check_sprites(layers, {"mesa-03-flip": {}, "peak-11": {}, "wolf": {}}) == []
    assert validate.check_sprites(layers, {"peak-11": {}}) == [
        "no sprite icon 'mesa-03-flip' in glyphs.json",
        "no sprite icon 'wolf' in glyphs.json",
    ]


def test_landform_may_not_show_before_its_place(layers):
    layers["places"]["features"][0]["properties"]["first_seen"] = "1-02"
    assert any("before its place" in e for e in validate.check_references(layers))


def test_water_place_may_not_show_before_its_place(layers):
    layers["landforms"]["features"].clear()
    layers["places"]["features"][0]["properties"]["first_seen"] = "1-02"
    assert validate.check_references(layers) == []
    layers["water_places"]["features"].append(feature("water-place-a", kind="spring", place_ref="place-a",
                                                      source_id=None))
    assert any("water_places.geojson water-place-a" in e for e in validate.check_references(layers))
