"""Which lines count as common, and the word lists that let search find a long line."""

from crossing.translations import is_common, other_words


def test_common_lines_match_with_their_punctuation():
    for line in ("Sí.", "Bueno…", "No?…", "¡Adiós!", "Buenas noches.", "señor", "Gracias..."):
        assert is_common(line), line


def test_longer_or_other_lines_are_not_common():
    # Accents are kept, the whole incipit must match, and "Vámonos" and "Está bien" stay in the panel.
    for line in ("Si", "Sí señor.", "No. Gracias.", "Vámonos.", "Está bien.", "Buenos días", "Señora"):
        assert not is_common(line), line


def test_other_words_are_sorted_folded_and_leave_out_the_incipit():
    words = other_words("Uno dos tres cuatro cinco, señor, más allá del río.")
    assert words == ["alla", "del", "mas", "rio", "senor"]


def test_other_words_are_none_when_the_incipit_is_the_whole_line():
    assert other_words("Está bien.") is None
    assert other_words("Vámonos, he said.") is None


def test_other_words_skip_the_speech_tag_and_keep_the_spanish_after_it():
    assert other_words("Sí, he said. Vámonos ahora.") == ["ahora", "vamonos"]
