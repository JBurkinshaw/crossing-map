import pytest

from crossing.build_story import history, ticked, with_history, with_leads


def test_ticked_rows_are_read_back(tmp_path):
    path = tmp_path / "checklist.md"
    path.write_text("| OK | # | Name |\n| [x] | J3.1 | The wolf's grave | located |\n"
                    "| [ ] | J3.2 | Promontory | inferred |\n"
                    "| [X] |  | Llanos de Carretas | approximate |\n", encoding="utf-8")
    assert ticked(path) == {("J3.1", "The wolf's grave"), ("", "Llanos de Carretas")}


def test_no_checklist_means_no_ticks(tmp_path):
    assert ticked(tmp_path / "missing.md") == set()


def test_leads_go_on_their_feature_and_its_area():
    found = {"s1": [{"source": "bell-2000", "relation": "agrees"}]}
    features = [{"properties": {"id": i}} for i in ("s1", "area-s1", "s2")]
    out = with_leads(features, found)
    assert [f["properties"].get("leads") for f in out] == [found["s1"], found["s1"], None]


HISTORY_HEADER = "feature,note,source,page,show_from\n"
FEATURES = [{"properties": {"id": "place-a", "first_seen": "1-05"}},
            {"properties": {"id": "s1", "first_seen": "2-01"}}]


def test_history_goes_on_the_features_it_names(tmp_path):
    seed = tmp_path / "history.csv"
    seed.write_text(HISTORY_HEADER + "place-a,A store opened about 1895.,bell-2000,61,1-05\n"
                    "place-a,The school closed in 1950.,bell-2000,61–62,2-01\n", encoding="utf-8")
    found = history(FEATURES, seed)
    assert found == {"place-a": [
        {"note": "A store opened about 1895.", "source": "bell-2000", "page": "61", "first_seen": "1-05"},
        {"note": "The school closed in 1950.", "source": "bell-2000", "page": "61–62", "first_seen": "2-01"}]}
    out = with_history([{"properties": {"id": i}} for i in ("place-a", "s1")], found)
    assert [f["properties"].get("history") for f in out] == [found["place-a"], None]


@pytest.mark.parametrize("row, error", [
    ("place-b,A note.,bell-2000,61,1-05", "names no place, stop or area: place-b"),
    ("place-a,A note.,wikipedia,61,1-05", "no source 'wikipedia'"),
    ("s1,A note.,bell-2000,61,1-05", "show_from '1-05' is before the feature's 2-01"),
])
def test_a_bad_history_row_stops_the_build(tmp_path, row, error):
    seed = tmp_path / "history.csv"
    seed.write_text(HISTORY_HEADER + row + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match=error):
        history(FEATURES, seed)
