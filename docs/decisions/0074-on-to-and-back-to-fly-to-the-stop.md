# 0074. On to and Back to fly to the stop

Status: accepted (2026-11-19). Supersedes the framing in decision 0058.
Phase: P1

## Context

Decision 0058 lets Back and Next go on across journeys: "On to J2" at the last stop of J1, "Back to J1" at the first stop of J2. To make the change of journey show, the map framed the whole of the new journey rather than flying to its stop. In use, the owner found that framing unhelpful. The reader pressed a button to go to a stop, and the map showed a whole journey, often at a far-out zoom, with the stop a small mark somewhere in it.

## Decision

- **"On to" and "Back to" fly to the stop they go to**: the first stop of the next journey, or the last stop of the journey before, as Next and Back do within a journey.
- **The rest of decision 0058 stands.** The button names the journey, the last stop of a journey says what "On to" does, and the note under the stop's name says which journey the reader has come from. The new journey's route draws in its own ink. Those still make the change of journey plain.
- Picking a journey in the journey picker, and the Home button, still frame the whole journey.

## Alternatives

- **Keep the framing** (decision 0058). It shows the whole of the new journey, but the reader asked for a stop.
- **Frame the journey, then fly to the stop.** Two camera moves for one press, and slow.

## Consequences

The camera moves less at a journey's end when the next journey starts near where the last one ended (J1 to J2, for example), so the change of journey rests on the button, the note and the route's ink. The reader can still see the whole journey with Home.
