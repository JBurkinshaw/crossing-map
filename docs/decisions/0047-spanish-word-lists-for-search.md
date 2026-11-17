# 0047. Spanish word lists for search, and the translations outside CC BY

Status: accepted (2026-11-17). Amends 0045.
Phase: P1

## Context

The site's purpose for the Spanish is to let a reader find this site's English for a line quickly. Each line publishes only its first five words of Spanish (design section 3), so search could find a long line only by its opening. A reader who remembers a word from the middle of a line, or whose eye lands on the end of it, found nothing.

The full Spanish cannot be published. McCarthy's text is under copyright to the end of 2093, and some of the longer lines are plainly expressive. The English translations are this site's wording, but translating a work is a right of its author, so they cannot carry this site's CC BY licence either.

Of 916 published lines, 151 have Spanish words beyond the incipit, 682 words in all.

## Decision

- Each line whose incipit leaves words out publishes `es_words`: those words, folded (lower case, no accents or punctuation), each once, in alphabetical order. A line whose incipit is the whole line has `null`.
- Search indexes `es_words` with the incipit and the English. The site never shows `es_words`.
- `crossing.validate` fails if a list is not in alphabetical order. In the line's own order the list would be the line.
- The words come from both sides of a speech tag ("…, he said. …"), and the tag's own English is left out.
- `data/LICENSE` leaves the English translations, as well as the incipits and word lists, out of the CC BY grant. The rest of each record stays CC BY 4.0.

## Alternatives

- **Publish the full Spanish.** The most useful for search, and the most exposed: it is a verbatim copy of every Spanish line, including the long speeches.
- **Publish the full Spanish only for short lines.** Lines of seven words or fewer would cover 858 of 928 spans with little risk, but the lines search needs help with are the long ones.
- **Hash each word.** It hides nothing: Spanish has few enough words that a dictionary reverses the hashes in seconds.
- **Bring your own book.** The reader opens their own EPUB and the browser finds the lines. Nothing new is published, but the Vintage ebook is sold with DRM, so few readers could use it.

## Consequences

- Any word of a line's Spanish finds it, accent-insensitive, and the reader sees the incipit and the English as before.
- A sorted word list with the English beside it lets a determined reader guess at a line. That is far less than the line, and less than the English already published.
- `crossing.echo_check` finds no shared run of eight words, because the lists are sorted.
- Design section 3 and acceptance criterion 4 (section 11) now allow the word lists beside the incipits.
