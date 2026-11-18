# 0052. Episodes named by their quoted opening words, and the stop card's two blocks

Status: accepted (2026-11-17)
Phase: P1

## Context

A stop's card showed its episode as "Part I · *They crossed*", then the episode's summary, then the stop's synopsis (decision 0051). The summary and the synopsis were set in the same type, one under the other, so the card read as one block of text, though one is about the episode and the other about the stop.

The opening words also gave no sign of what they were. The book has no chapter titles. The site names each of its 41 episodes by the words it opens with, which the book sets in capitals, but bare in italics "They crossed" could be read as a title or a quotation from anywhere in the episode. "Part I" could also be read as part of the journey, since J1 and J2 both fall in Part I, while J4 and J6 cross from one Part into the next.

## Decision

- **Opening words are quoted and trail off**: ‘They crossed…’, with UK single quotes (decision 0037) and the ellipsis character. One function, `quotedOpening` in `site/src/spoiler/progress.ts`, writes them for the card, the progress badge and the "Where are you up to?" list. The book's own words inside are not changed.
- **The card names the episode as the badge does**: "Part I, episode 9: ‘They crossed…’". Readers already see "episode" on the badge, in the picker and in search results, so the card uses that word and not a second one such as "section". The line's tooltip says that the book has no chapter titles and that each episode is named by its opening words.
- **The episode's text and the stop's text are two blocks.** The episode line and its summary are both in the faint, small, italic meta style. A thin rule follows, then the stop's synopsis (or its "What happens here" fold) at full size and full ink. Stops without a synopsis show the faint block alone.
- **About explains episodes**: the book has four Parts and no chapter titles, the site splits each Part where a new scene starts, and names each episode by its opening words.

## Alternatives

- **Labelled rows ("Section", "Here") in a left column.** Clear, but the labels take about 60 px of a 340 px phone panel.
- **The summary on the episode line**, after a colon. Compact, but the summary and the synopsis keep the same weight, which was the problem.
- **A margin rule beside the episode block.** The site already sets the Spanish lines this way, and the two should not look alike.
- **"Section" as the readers' word.** It is plainer than "episode", but the site already says "episode" in four places, and two names for one thing would confuse more than either.

## Consequences

- The progress badge and picker labels change from "episode 9: They crossed" to "episode 9: ‘They crossed…’".
- The episode's summary on a stop card is smaller and fainter than before. It is still 5.2:1 against the paper (WCAG AA), as all meta text is.
