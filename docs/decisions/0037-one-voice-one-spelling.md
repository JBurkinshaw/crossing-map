# 0037. One voice, one spelling, and plain words in the site's text

Status: accepted (2026-11-16). Owner's decisions after a review of the site's text.
Phase: P1

## Context

A review of everything a reader sees found the same things written several ways. The site spoke as "I", "we" and "our" by turns. Inferred areas were called circles on their cards and in their rules, although decision 0020 cuts most of them to the ground. Place names had two or three spellings (Cajon Bonita and Cajón Bonito, Sierra La Madera and Sierra de la Madera, Boquilla, La Boquilla and Boquilla y Anexas), and US spellings sat beside UK ones. Leg cards showed the model's internals ("cost model lc-0.4", "Douglas-Peucker at 150 m", "Strahler order", "HU8 13030201"), and some published text still held working notes ("To be checked by hand in QGIS", "is a separate seed").

## Decision

- **One voice.** "I" appears only in the owner's blurb at the top of the About page. Everywhere else the site says "this site" or "the map", not "we" or "our". The project's owner is "the owner", and "the author" means McCarthy only, so the How it's built page runs the pipeline on "the owner's computer". The decision records keep their own wording, as accepted records do not change.
- **Areas, not circles.** Reader text calls an inferred area an area. Where a draft kept everything it was given, its rule says "Kept the whole area". The code and the schema may still say that the first, widest guess is a circle of `uncertainty_m` about the pin, because that is how it is computed.
- **One spelling per place.** A place takes the spelling of its name on the map: the Cajón Bonito, the Sierra de la Madera, La Boquilla. The book's own spelling is kept where the text says it is the book's ("The book spells it Cajon Bonita", `name_in_text`), and a source's spelling where the text cites that source. Boquilla y Anexas, the INEGI town 135 km away that the open question rules out, is named only in that question and the place's reasoning; the episode summaries and stops that meant the lakeside town now say La Boquilla. Gazetteer names of other ranges (GeoNames' "Sierra la Madera") stay as the gazetteer spells them.
- **UK spelling.** Reader text uses UK spelling: towards, grey, travelling. "Railway" is used for the lines and the key, and "Railroad" only in the proper name of a real company. The book's own words (the episode opening "Gray sky") are not respelled.
- **Plain leg cards.** A leg's "How this line was drawn" text says in plain words how the line was made. The technical side moves to a new field, `drawn_detail` (dataset and features, Strahler order or NHD watershed, grid, smoothing, cost model), which the card does not show. A modelled leg's card links to How it's built, which explains the model.
- **No working notes in published text.** Notes to the project ("to be checked by hand", "worth a look by hand", "a separate seed") are removed from reasoning and rules. Open doubts that matter to a reader belong in the open questions.

## Alternatives

- **"We" throughout.** Warmer, but the site is run by one person, and "we" reads as a team.
- **Keep the jargon on the card, folded.** A reader who opens it still meets "Douglas-Peucker". The data keeps the detail for those who want it.
- **Respell the book's names to the gazetteer's everywhere.** Would lose the book's own spelling, which readers search for; `name_in_text` keeps it.

## Consequences

The site reads as one voice. A new text follows these rules; a review that finds "we", "circle" on a card, a US spelling or a second spelling of a place treats it as a defect. Episode summaries 3-01, 3-11 and 4-01 are left as they are until the owner decides on their wording, so 3-01 still says "traveling" and "a girl".
