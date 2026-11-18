# 0057. Stop rows checked against the book while writing the synopses

Status: accepted (2026-11-17)
Phase: P1

## Context

Writing the synopses for Parts II to IV (decision 0051) meant reading each stop's episode against its row in `pipeline/seeds/stops.csv`. The writers and the second readers found rows whose placement reasoning disagreed with the book or showed too early, scenes with no stop to hold them, and one stop order in doubt. The owner asked for all of them to be fixed.

The site hides a stop's reasoning while it cites, by number, an episode the reader has not reached (`site/src/spoiler/filter.ts`). A reasoning that tells a later fact without the number shows too early.

## Decision

- **Reasoning that showed too early now cites its episode.** `j3-websters` says what 2-06 tells of the place, and cites 2-07 for Boyd lodging there. The old `j3-lordsburg` reasoning told the sheriff's interview and Boyd's lodging from a 2-05 stop. It now says only what places the stop.
- **Reasoning that disagreed with the book now follows it.**
  - `j3-sk-bar`: the book never shows what Sanders and Leona tell Billy.
  - `j4-casas-grandes` and `j4-colonia-juarez`: the plank bridge is at Colonia Juárez.
  - `j4-escarpment-rim`: the rim is days from Bacerac, not one morning.
  - `j5-san-diego`: Boyd asks Billy to go to Namiquipa, not to meet “the girl” at Santa Ana.
  - `j6-san-lorenzo`: Quijada says killed and taken away. The citation of 4-07, which hid the reasoning from readers of 4-05 and 4-06 for no gain, is gone.
  - `j7-attack`: the gypsies' doctoring is cited to 4-06 alone.
  - `j7-cemetery`: Billy is digging when the sheriff stops him, and the book does not say the burial is finished.
  - `j7-deming`: a doctor in town finds the heart murmur, and the ten days at the stable come before El Paso.
  - `j7-magdalena`: nine more months' work.
- **A scene with no stop is told in the synopsis of the nearest stop that may hold it.** A synopsis may tell anything up to the end of its stop's episode, earlier episodes included.
  - **2-06, the sheriff's interview in Lordsburg.** `j3-lordsburg` moves from 2-05 to 2-06 and tells both the noon arrival and the interview. The arrival is the last line of 2-05, so a reader in 2-05 loses little, and 2-06 gains its main scene. The leg to Lordsburg moves with it.
  - **2-08, the second scene at Bacerac** (the old man's map in the dust): at the start of `j4-escarpment-rim`, the next stop in 2-08.
  - **3-07, the one-armed man's fall at La Boquilla:** at the start of `j4-leave-road` (3-08). `j4-boquilla` keeps 3-06, where the brothers ride in.
  - **4-05, the wake at Namiquipa:** at the start of `j7-temosachic`, the first stop in 4-05. `j7-namiquipa` keeps 4-04, where Billy camps and sees the old man laid out.
- **Temósachic stays before Madera.** The book tells of the corrido heard at Temósachic during weeks of riding, before the Madera fair of late April, and after the fair Billy rides south toward Temósachic again. The reasoning says so.

## Alternatives

- **New stops for the four scenes.** Each would sit on or beside an existing pin, adding a leg of almost no length, and new stops need their oblique positions drawn. A synopsis can carry the scene without either.
- **Re-dating `j4-boquilla` to 3-07 and `j7-namiquipa` to 4-05.** Each would then tell its scene, but a reader in 3-06 or 4-04 would lose the stop where the episode takes place.
- **Re-dating `j3-websters` to 2-07.** It would match its reasoning, but it would then repeat `j4-lordsburg`, where 2-07 opens at the same house.

## Consequences

- `j3-lordsburg` and the leg into it show from 2-06, not 2-05.
- Stop names that match the book for six words remain (`j4-escarpment-rim`, `j5-lake-camp`, `j7-magdalena-ranch`, `j7-babicora-high-country`). They are under the eight-word limit of `crossing.echo_check`.
