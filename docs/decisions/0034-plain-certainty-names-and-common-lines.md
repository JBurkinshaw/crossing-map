# 0034. Plain names for certainty, and common Spanish lines left out of the panel

Status: accepted (2026-11-16). Owner's request, after a review of the panel's wording.
Phase: P1

## Context

The stop section and the place cards showed the data's certainty values as they are (`located`, `approximate`, `inferred`, `reported`) on the line under the title, with the source and its id beside them. Readers who do not know the data model read "inferred · this-site" as jargon.

Many lines of Spanish are a single common word: 76 of the 916 lines are "Sí", "No", "Gracias", "Bueno", "Adiós", "Buenas noches" or "Señor" on their own. In a stop's list they push the lines worth reading out of view.

## Decision

- **Plain names.** One table in `site/src/panel/certainty.ts` names each value for readers, and the stop section, the place cards and the About page all use it: `located` is "Named and found", `approximate` "Roughly here", `inferred` "Worked out from clues", `reported` "Someone in the book says so". The line under a card's title is the plain name and the radius ("Worked out from clues · within about 3 mi"). The source and its id move under "How this was placed". A route leg keeps the key's wording for its line (decision 0033). How it's built maps the plain names to the values, because its count tables show the values.
- **Common lines.** `crossing.translations` sets a boolean `common` on each line: true when its incipit, lower-cased with its accents kept, and with the punctuation and ellipses around it removed (`¡ ! ¿ ? , . …`), is exactly one of: sí, no, gracias, bueno, adiós, buenas noches, señor. The panel leaves these out of "Spanish here", a road's lines and the count on the road-ahead button, unless the reader picked the line in search. Search still finds them, and the data keeps them. "Vámonos" and "Está bien" are not in the set: each moves a scene on. "Si" without its accent ("if") is not "sí", and longer lines such as "Sí señor" or "No. Gracias." stay.

## Alternatives

- **Drop the common lines from the data.** The data is a full record of the Spanish in the book; a reader searching for "Gracias" should find every one.
- **Fold the common lines into a "Show the short replies" toggle.** One more control for lines that need no translation for most readers.
- **Match on accent-folded text.** Would catch "Si" (if) as "sí" (yes).

## Consequences

The lists at the busiest stops are a little shorter (11 of 65 lines at the San Diego doctor's stop). Adding a word to the set is a change to `COMMON_LINES` in `pipeline/src/crossing/translations.py` and a rebuild of the translations.
