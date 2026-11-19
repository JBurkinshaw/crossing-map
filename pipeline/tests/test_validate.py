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


def test_synopsis_within_the_rules_passes():
    doc = collection(feature("s1", sequence=1, synopsis="Billy rides south. He crosses the line at noon."))
    assert validate.check_layer(doc, "stops", EPISODES) == []


@pytest.mark.parametrize("text, error", [
    ("One. Two. Three. Four.", "4 sentences"),
    ("He says “Go.” She waits. He rides. She follows.", "4 sentences"),
    (" ".join(["word"] * 71) + ".", "71 words"),
    ("Billy rides south\u2014alone.", "an em dash"),
    ("Billy rides south; the wolf follows.", "a semicolon"),
])
def test_synopsis_breaking_the_rules_is_reported(text, error):
    doc = collection(feature("s1", sequence=1, synopsis=text))
    errors = validate.check_layer(doc, "stops", EPISODES)
    assert any(error in e for e in errors), errors


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


def test_oblique_copy_must_match(layers):
    oblique = copy.deepcopy(layers["stops"])
    oblique["features"][1]["properties"]["first_seen"] = "1-01"
    oblique["features"].pop(0)
    errors = validate.check_oblique(layers["stops"], oblique, "stops")
    assert any("only in the flat layer" in e for e in errors)
    assert any("first_seen differ" in e for e in errors)


def test_oblique_copy_must_keep_the_flat_text(layers):
    oblique = copy.deepcopy(layers["stops"])
    oblique["features"][0]["properties"]["name"] = "An old name"
    assert any("name differ" in e for e in validate.check_oblique(layers["stops"], oblique, "stops"))


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


def test_vignette_may_not_show_before_its_pin(layers):
    layers["vignettes"]["features"].append(feature("vignette-a", kind="vignette", first_seen="1-01", place_ref="s2"))
    assert any("vignettes.geojson vignette-a" in e for e in validate.check_references(layers))
    layers["vignettes"]["features"][0]["properties"]["first_seen"] = "1-02"
    assert not any("vignette-a" in e for e in validate.check_references(layers))


def test_vignette_on_a_leg_may_not_show_before_the_leg(layers):
    layers["vignettes"]["features"].append(feature("vignette-a", kind="vignette", first_seen="1-01",
                                                   place_ref="j1-seg-01"))
    assert any("before its pin's 1-02" in e for e in validate.check_references(layers))
    layers["vignettes"]["features"][0]["properties"]["first_seen"] = "1-02"
    assert validate.check_references(layers) == []
    # Only a route segment is a leg.
    layers["vignettes"]["features"][0]["properties"]["place_ref"] = "j1-seg-99"
    assert any("place_ref j1-seg-99" in e for e in validate.check_references(layers))


def test_water_place_may_not_show_before_its_place(layers):
    layers["landforms"]["features"].clear()
    layers["places"]["features"][0]["properties"]["first_seen"] = "1-02"
    assert validate.check_references(layers) == []
    layers["water_places"]["features"].append(feature("water-place-a", kind="spring", place_ref="place-a",
                                                      source_id=None))
    assert any("water_places.geojson water-place-a" in e for e in validate.check_references(layers))


def test_position_notes_list_flagged_stops_without_a_current_verdict(tmp_path, monkeypatch):
    monkeypatch.setattr(validate, "POSITIONS", tmp_path)
    (tmp_path / "results.csv").write_text(
        "stop,journey,seq,name,position,lon,lat,check,flagged,candidates,note\n"
        "a,J1,1,A,pass,-108.1,31.1,ok,false,1,\n"
        "b,J1,2,B,pass,-108.2,31.2,flag: slope,true,1,\n"
        "c,J1,3,C,floor,-108.3,31.3,flag: spur,true,1,\n"
        "d,J1,4,D,head,-108.4,31.4,ok,false,1,\n", encoding="utf-8")
    (tmp_path / "review.csv").write_text(
        "id,verdict,choice,note,point,updated\n"
        "b,accept,,,\"-108.20000,31.20000\",2026-11-18T00:00:00Z\n"
        "c,accept,,,\"-108.00000,31.00000\",2026-11-18T00:00:00Z\n", encoding="utf-8")
    stops = {"features": [{"properties": {"id": i}, "geometry": {"coordinates": xy}} for i, xy in
                          [("a", [-108.1, 31.1]), ("b", [-108.2, 31.2]), ("c", [-108.3, 31.3]), ("d", [-108.5, 31.4])]]}
    notes = validate.position_notes(stops)
    # c's verdict was for an older point, and d has moved since the results were computed.
    assert notes == ["d: the stop has moved since crossing.positions ran; rerun it",
                     "1 flagged stops without a verdict (?review=positions): c"]


def test_a_stop_point_must_lie_inside_its_area():
    ring = [[-108.6, 31.4], [-108.4, 31.4], [-108.4, 31.6], [-108.6, 31.6], [-108.6, 31.4]]
    areas = {"features": [{"properties": {"id": "area-a"}, "geometry": {"type": "Polygon", "coordinates": [ring]}},
                          {"properties": {"id": "area-b"}, "geometry": {"type": "Polygon", "coordinates": [ring]}}]}
    stops = {"features": [{"properties": {"id": "a"}, "geometry": {"coordinates": [-108.5, 31.5]}},
                          {"properties": {"id": "b"}, "geometry": {"coordinates": [-108.7, 31.5]}}]}
    assert validate.check_points_in_areas(stops, areas) == ["b: its point lies outside area-b"]


def test_leads_pass():
    leads = [{"source": "bell-2000", "relation": "agrees", "page": "394"},
             {"source": "reddit-gaia", "relation": "differs", "distance_km": 81, "note": "Pins the other range.",
              "first_seen": "2-01"}]
    doc = collection(feature("place-a", kind="town", role="stop", leads=leads))
    assert validate.check_layer(doc, "places", EPISODES) == []


@pytest.mark.parametrize("lead, error", [
    ({"source": "wikipedia", "relation": "agrees"}, "is not one of"),
    ({"source": "bell-2000", "relation": "maybe"}, "is not one of"),
    ({"source": "reddit-gaia", "relation": "differs", "lat": 31.5, "lon": -108.9}, "Additional properties"),
    ({"source": "reddit-gaia", "relation": "differs", "note": "Pinned at 31.4526, -108.9012."}, "gives a coordinate"),
    ({"source": "reddit-gaia", "relation": "differs", "note": "Pinned near 108° W."}, "gives a coordinate"),
    ({"source": "reddit-gaia", "relation": "agrees", "page": "12"}, "only Bell's leads have a page"),
    ({"source": "bell-2000", "relation": "agrees", "first_seen": "1-01"}, "before its feature's 1-02"),
    ({"source": "bell-2000", "relation": "agrees", "first_seen": "2-12"}, "not an episode"),
])
def test_bad_lead_is_reported(lead, error):
    doc = collection(feature("place-a", kind="town", role="stop", first_seen="1-02", leads=[lead]))
    errors = validate.check_layer(doc, "places", EPISODES)
    assert any(error in e for e in errors), errors


def test_a_source_leads_once_per_feature():
    lead = {"source": "bell-2000", "relation": "agrees"}
    doc = collection(feature("place-a", kind="town", role="stop", leads=[lead, lead]))
    assert any("name bell-2000 twice" in e for e in validate.check_layer(doc, "places", EPISODES))


def test_leads_only_on_places_stops_and_areas():
    line = {"type": "LineString", "coordinates": [[-108.5, 31.5], [-108.4, 31.6]]}
    doc = collection(feature("j1-seg-01", kind="route-segment", sequence=1, geometry=line,
                             leads=[{"source": "bell-2000", "relation": "agrees"}]))
    assert any("leads are only for" in e for e in validate.check_layer(doc, "journeys", EPISODES))
