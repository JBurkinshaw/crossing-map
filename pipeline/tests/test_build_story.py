from crossing.build_story import ticked, with_leads


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
