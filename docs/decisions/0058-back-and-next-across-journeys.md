# 0058. Back and Next go on across journeys

Status: accepted (2026-11-17)
Phase: P1

## Context

Back and Next stepped through one journey's stops and stopped at its ends. At J1's last stop, Next was disabled, and the only way on to J2 was the journey picker. "Read on" (decision 0053) crosses into a new journey only for a reader at the stop they reached most recently, because it moves their progress. A reader stepping back through journeys they have already read had no way on from a journey's end.

## Decision

- **At a journey's last stop, Next goes on to the first stop of the next journey. At its first stop, Back goes to the last stop of the journey before.** Only journeys the reader has reached and that have stops on the map count, so this never shows anything past their progress.
- **"Next" is journey number order**, as the journey picker lists them. J6 (Boyd and the girl, reported) starts in Part III, episode 8, before J5 starts in episode 12, but the journeys are numbered by the figure they follow, and the picker already teaches that order.
- **The change of journey is said four ways**, so it cannot pass unnoticed:
  - The button names the journey: "On to J2" in place of Next, "Back to J1" in place of Back. Its accessible name gives the journey's full name.
  - The last stop of a journey ends with a note: "The last stop of J1. “On to J2” goes on to the next journey: Billy's first crossing, with the wolf."
  - On arrival, a note under the stop's name says what happened: "Finished J1. This is the first stop of J2: …", or "Back from J2 to the last stop of J1: …". It goes when the reader moves again.
  - The map frames the whole of the new journey, in its own ink, as picking it in the journey picker does, and does not fly straight to the stop.

## Alternatives

- **Leave the stepper inside one journey**, as design section 9 had it. Readers following the book from end to end would hit a disabled button at each journey's end.
- **Book order by each journey's first episode.** It would put J6 before J5 and disagree with the picker and the layer key.
- **A separate "Next journey" button beside the stepper.** It adds a third control for something that happens six times. Relabelling Next keeps one place to press.
- **Fly to the new journey's first stop.** The stop is close to where J1 ended, so the reader would see little move and could miss that the journey changed.

## Consequences

- Next is disabled only at the last stop of the last journey reached, and Back only at the first stop of the first.
- `neighbourJourneys` in `site/src/story/select.ts` picks the journeys either side and is tested.
