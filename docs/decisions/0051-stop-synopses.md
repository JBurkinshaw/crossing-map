# 0051. A synopsis for each stop, folded while its episode is read

Status: accepted (2026-11-17)
Phase: P1

## Context

A stop's card said what happens there with its episode's summary from `episodes.json`. Every stop in an episode shares that summary, and it is written to give nothing away past the episode's opening. So it describes the first stop or two and then goes stale: the seven stops of 1-09, from the ranch on the volcanic plain to the fair at Colonia Morelos, all say that Billy rides south across the border. The owner wanted one to three sentences for each stop that say what happens at that place.

A stop's own text cannot keep the summary's rule. A useful synopsis of the hacienda (1-10) tells how the episode ends, and a reader who has just started 1-10 can already open that stop, because the map shows the episode being read in full (decision 0034).

## Decision

- **Each stop has a `synopsis`**: one to three sentences, in the site's own words, about what happens at the stop. It may tell anything up to the end of the stop's episode, and nothing after. It sits under the episode's summary, which stays as the overview. Stops without one yet have `null`, and their card shows the summary alone.
- **The synopsis of a stop in the episode being read is folded** under "What happens here", closed by default. The fold closes again on every stop, and the site does not remember it, so each stop's synopsis is the reader's own choice. A stop in an episode the reader has finished shows its synopsis in full, as does every stop once the book is finished.
- **"Spanish here" is folded too**, closed by default, with its count of lines in the heading. Its state is saved in the browser (`crossing-map.spanish-here` in `localStorage`, like the units setting), so it stays as the reader left it on every stop and on later visits. A line picked in search opens the fold so that the line can be seen. That does not change the saved setting, and the reader can still close it.
- **`crossing.validate` holds each synopsis to the house rules**: at most three sentences and 70 words, and no em dashes or semicolons.
- **The synopses are written from the owner's copy of the book and checked with `crossing.echo_check`.** Part I's 26 stops were written first and the other 145 the same day. Each of those was drafted from its episode's text and then checked against the text by a second reader, for facts, place, spoilers and wording. The draft sheet, with a column that marks the synopses which tell a later turn of their episode, is `review/synopses/part1.csv`. The sheets for Parts II to IV are `part2.csv` to `part4.csv`. The stop rows those checks found at odds with the book were corrected (decision 0057).

## Alternatives

- **Show a stop's synopsis only after its episode is finished.** This is the safest option, but a reader would never see the synopses for the episode they are reading, which is where a synopsis is most useful.
- **Write the synopses of the episode being read to tell nothing past their stop.** The hacienda and the Pilares Teras, among others, would then say no more than the summary they were meant to improve.
- **Replace the episode's summary with the synopsis.** The summary is still the best one-line overview of the episode, and the owner wanted both.
- **Remember the "What happens here" fold, as "Spanish here" is remembered.** A reader who opened it once would then see every later synopsis in the episode without choosing to.

## Consequences

- Stops gain a field. The areas that `crossing.build_story` makes from a stop's properties do not carry it.
- The fold's text is in the page while it is closed. The spoiler-leak test does not flag it, because every stop shown is reached.
- With 171 stops, the synopses are the largest body of the site's own prose about the plot. Every Part needs an `echo_check` pass before it is published.
