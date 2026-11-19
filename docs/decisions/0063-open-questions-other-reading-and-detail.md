# 0063. An open question can show its other reading on the map, and say more on request

Status: accepted (2026-11-18)
Phase: P1

## Context

An open question gives three short fields: what the map shows, the other reading, and why. Some calls rest on measurements a reader cannot see from those lines. For the eastern escarpment (decision 0059), the other reading is "about 75 km north", which means little until it is on the map, and the reason is a viewshed test over 617 points. The roadmap's Phase 2 backlog already asked for alternative readings drawn on the map.

## Decision

- **Three optional fields on an open question** (`data/schema/open-questions.schema.json`):
  - `detail`: a few plain sentences with the numbers behind the call, folded under "More about this".
  - `other_at`: a centre, a radius and a label for the other reading. A button on the stop's card, "Show the other reading on the map", draws a dashed ring there and frames it with the stop's area (or its point), so a question always opens on the same view. Pressing it again hides the ring and returns to the stop at the zoom the reader had before. Leaving the stop clears the ring without moving the camera. While it shows, the key has a row for it.
  - `evidence`: links to how the call was made, as paths in the repository, opened on GitHub at the build's commit. `crossing.validate` checks each path exists.
- **The method links stay off the map's cards.** They show only on the Open questions page, in the same fold. A card should tell a reader what is uncertain and why, not send them into the code.
- **How it's built explains the method once,** in a new section, "How places are worked out", which links to `docs/placement-method.md`. The Open questions page points to it, with the correction form.
- `q-eastern-escarpment` is the first question to use the fields.

## Alternatives

- **The method linked from every card.** It invites the curious reader into the repository at the moment they are reading the story, and repeats the same link on many cards.
- **The other reading always drawn.** It would put dashed rings all over the map for every open question, most of them about small distances.

## Consequences

- Questions without the new fields look as before.
- The ring's label is drawn over other labels, so it may cover a stop's number nearby. A placement that avoids other labels is left for when more questions use it.
