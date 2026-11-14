"""Each fold variant is pinned: changing one changes what its caller matches."""

from crossing.text import fold_name, fold_prose, fold_search, strip_accents


def test_strip_accents_keeps_other_characters():
    assert strip_accents("Río Bavispe’s") == "Rio Bavispe’s"


def test_fold_name_drops_non_ascii_and_spaces_straight_apostrophes():
    assert fold_name("Ascención") == "ascencion"
    assert fold_name("Taylor’s Draw") == "taylors draw"
    assert fold_name("Taylor's Draw") == "taylor s draw"
    assert fold_name("  Colonia  Morelos (Sonora) ") == "colonia morelos sonora"


def test_fold_search_removes_both_apostrophes():
    assert fold_search("¿Dónde está?") == "donde esta"
    assert fold_search("Taylor's") == fold_search("Taylor’s") == "taylors"
    assert fold_search("a—b") == "a b"


def test_fold_prose_keeps_punctuation_and_lines():
    assert fold_prose("Don’t go,\nBilly.") == "dont go,\nbilly."
    assert fold_prose("'Quoted'") == "'quoted'"
