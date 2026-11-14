"""Text folding for matching names and words across sources with different accents and punctuation.

Each caller needs a slightly different fold, so each has its own function here; all start from the same
accent stripping. Changing one changes what that caller matches, so the tests pin every variant.
"""

import re
import unicodedata

APOSTROPHES = re.compile(r"(?<=\w)['’ʼ](?=\w)")
NON_ALNUM = re.compile(r"[^a-z0-9]+")


def strip_accents(s: str) -> str:
    """Decompose and drop the combining marks, so "Río" -> "Rio". Other characters are kept."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def fold_name(s: str) -> str:
    """For gazetteer and seed name matching: ASCII lower case, punctuation to spaces, spaces collapsed.

    Characters with no ASCII form (curly quotes, dashes) are dropped outright, so "Taylor’s" -> "taylors",
    while a straight apostrophe becomes a space: "Taylor's" -> "taylor s".
    """
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def fold_search(s: str) -> str:
    """For Spanish spans and guide entries: like fold_name, but both apostrophes are removed, not spaced,
    and any other character outside a-z and 0-9 becomes a space."""
    s = strip_accents(s).lower().replace("’", "'").replace("'", "")
    return " ".join(NON_ALNUM.sub(" ", s).split())


def fold_prose(s: str) -> str:
    """For comparing prose word by word: lower case, accents dropped, apostrophes inside words removed
    ("don’t" -> "dont"). Punctuation and line breaks are kept, so callers can split lines and words."""
    return APOSTROPHES.sub("", strip_accents(s).lower())
