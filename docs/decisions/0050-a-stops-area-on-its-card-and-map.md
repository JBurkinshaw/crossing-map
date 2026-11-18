# 0050. A stop's area on its card and map

Status: accepted (2026-11-17)
Phase: P1

## Context

Each of the 59 stops worked out from clues, and one reported stop, has an inferred area it could be anywhere in, named after it (stop `j2-hacienda`, area `area-j2-hacienda`). The stop's card named its certainty only inside "How this was placed", which is often shut, and nothing tied the pin to the tinted area round it. The owner, at J2's hacienda, wanted the card to say plainly that the point is uncertain, and a way to reach the area and see it highlighted.

## Decision

- **The stop says so on its card.** Under the episode and note, outside "How this was placed": "*Worked out from clues.* The point is a best guess: the book puts this stop somewhere in the area outlined on the map." The certainty words are the shared ones (decision 0035).
- **The map outlines the area while its stop is current**, with the solid ink line a picked area has. Stepping on clears it.
- **A "Show the whole area" button** frames the area on the map, and the stop stays current.
- **The area's card links back** to its stop: "The area for J2, stop 12: The hacienda" steps to it.
- A stop and its area are paired by id (`areaOfStop` and `stopOfArea` in `site/src/story/select.ts`). Both share a `first_seen`, so the spoiler rule needs nothing new.

## Alternatives

- **An open marker for stops worked out from clues**, a ring in place of the filled dot, so the uncertainty shows before any click. Left for later: it is a change of style, which wants a precedent from `docs/inspiration/` first.
- **The button opens the area's card.** It would replace the stop's section with a card that repeats its reasoning. Framing the area keeps the reader on the stop.
- **Outline only on request.** The outline is the point: a pin alone reads as more certain than it is.

## Consequences

- With a picked area and a current stop's area, two areas can be outlined at once, in the same style.
- The pairing rests on the `area-` id prefix that `crossing.build_story` gives every stop's area.
