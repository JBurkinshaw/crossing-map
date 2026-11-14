from crossing.build_story import ticked


def test_ticked_rows_are_read_back(tmp_path):
    path = tmp_path / "checklist.md"
    path.write_text("| OK | # | Name |\n| [x] | J3.1 | The wolf's grave | located |\n"
                    "| [ ] | J3.2 | Promontory | inferred |\n"
                    "| [X] |  | Llanos de Carretas | approximate |\n", encoding="utf-8")
    assert ticked(path) == {("J3.1", "The wolf's grave"), ("", "Llanos de Carretas")}


def test_no_checklist_means_no_ticks(tmp_path):
    assert ticked(tmp_path / "missing.md") == set()
