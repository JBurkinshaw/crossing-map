# 0036. Stop names and drawing captions that give nothing away

Status: accepted (2026-11-16). Owner's decision, after a review of the site's text. Extended to the drawings' `stands_for` by 0038.
Phase: P1

## Context

The spoiler filter shows a stop, its legs and its drawing from the episode the stop is first seen in (decision 0010). Their names show at once: on the map, in the journey stepper, in search and in the key. A stop's body text sits behind "How this was placed", but its name does not. Some names told the episode's outcome before the reader had read it: "The river camp where Boyd is shot", "San Lorenzo, where Boyd fell", "Galeana, two men killed", "The Parham house, found empty", "Boyd's grave, on the Gallego road". A reader who sets their progress to 3-08 at the start of that episode saw the shooting in the stop list. Two drawing captions did the same: "Turned away by the army" and "North with Boyd's bones".

## Decision

- **A name says where, not what happens.** A stop's name and a drawing's name and caption name the place, the time of day or the ground ("The river camp near San José", "San Diego, after dark", "The road north of the Babícora lake"). They do not say who dies, is hurt, is lost, is found, or how an attempt ends. The event stays in the body text: the reasoning and notes, which the card shows under "How this was placed" and which the spoiler filter already hides when they cite a later episode.
- **Search still finds the place.** Each new name keeps the place name it had, or gains one (San Lorenzo becomes "San Lorenzo, Chihuahua", which also tells it from the New Mexico one), so a search for the town or road finds the stop.
- **Scene-setting stays.** A name that only sets the scene (the opera company on the Madera road, the steer herd, the red plane, "the deputies") gives no outcome away and is kept. So are names whose event the reader has read by the stop's episode (the wolf's grave, first seen in 2-01).
- **The renames:** 21 stops and 8 drawings. A drawing's name changes with its caption. The legs and areas named after a stop follow it.
- Stops:
  - Cloverdale Creek (the trap) → Up Cloverdale Creek
  - The Parham house, found empty → The Parham house
  - Lordsburg, the sheriff's office → Lordsburg
  - The Websters' (Boyd) → The Websters', Lordsburg
  - Bacerac (Keno) → Bacerac
  - Their horses, up from the lake → The road north of the Babícora lake
  - The manco's riders, the Boquilla hacienda in sight → In sight of the Boquilla hacienda
  - Boquilla y Anexas (the manco falls) → La Boquilla
  - The river camp where Boyd is shot → The river camp near San José
  - The road where the workers' truck takes Boyd (J4) → The dirt road in open country
  - Boyd lifted onto the workers' truck (J6) → The dirt road in open country
  - San Diego, where he finds Boyd → San Diego, after dark
  - Casas Grandes at 3 a.m., for the doctor → Casas Grandes at 3 a.m.
  - Back through Santa Ana, with “the girl” → Back through Santa Ana
  - Galeana, two men killed → Galeana
  - San Lorenzo, where Boyd fell → San Lorenzo, Chihuahua
  - San Buenaventura, the grave → San Buenaventura
  - Albuquerque, rejected again → Albuquerque
  - San Diego, the families gone → San Diego, on the road south
  - Boyd's grave, on the Gallego road → The cemetery on the Gallego road
  - The attack on the river trail, and the gypsies' camp → The river trail north of Corralitos
- Drawing captions:
  - Turned away by the army → The army recruiting office
  - North with Boyd's bones → North to the border
  - Boyd's grave, Gallego road → Cemetery on the Gallego road
  - Carrying her into the Pilares → Into the Pilares
  - Caught, the drag in a cholla → Cholla on the bootheel flats
  - The house, found empty → The Parham house
  - Keno, found at Bacerac → Keno at Bacerac
  - Taking “the girl” from the fire → The fire in the oak grove

## Alternatives

- **Show a stop's name only once the reader has passed its episode.** Keeps the vivid names, but a reader in the episode would see a stop with no name, and the stepper, search and the key would each need the rule.
- **Keep the names.** They are the most memorable handle on a stop, but they spoil the episode the reader is in, which design section 11 rules out.

## Consequences

Stop names are plainer, and a few share a name with another journey's stop at the same town (Bacerac, Lordsburg, Albuquerque, San Buenaventura); the stepper's journey and number tell them apart. The drawings themselves still show their scene (Billy with the travois, the wolf in the cholla); only the words change. A new stop or drawing follows the same rule, and a name with a death, a wound, a loss or an outcome in it is a review finding.
