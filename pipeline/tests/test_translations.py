"""Which lines count as common, so the panel leaves them out of a place's Spanish."""

from crossing.translations import is_common


def test_common_lines_match_with_their_punctuation():
    for line in ("Sí.", "Bueno…", "No?…", "¡Adiós!", "Buenas noches.", "señor", "Gracias..."):
        assert is_common(line), line


def test_longer_or_other_lines_are_not_common():
    # Accents are kept, the whole incipit must match, and "Vámonos" and "Está bien" stay in the panel.
    for line in ("Si", "Sí señor.", "No. Gracias.", "Vámonos.", "Está bien.", "Buenos días", "Señora"):
        assert not is_common(line), line
