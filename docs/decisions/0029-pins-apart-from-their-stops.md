# 0029. Place pins apart from their stops

Status: proposed (2026-11-15). Owner's request after the J2 Guadalupe pass review.
Phase: P1

## Context

A place's pin is its gazetteer point. A click on the pin opens the stops whose `place_ref` names it. Most stops stand on their pin, but a few stand elsewhere on a large place: the low pass of J2 (stop 4) is on the east flank of the Guadalupe Mountains, 2.7 km from GNIS 920606, the range's point. The range's name is set along its axis (decision 0023), so the pin had no label. It showed as a nameless ink dot that opened stop 4, a few kilometres away. The owner judged the range and the pass to be different places: the pin and its name should stay, but the pin should not open the stop.

## Decision

- **A pin stands apart** when every stop that names its place is more than 1 km from it (`pinsApart` in `site/src/story/select.ts`). A pin with any stop within 1 km is the same spot as that stop. A pin no stop names is unchanged.
- **A pin that stands apart is drawn as before but cannot be clicked.** It is on its own circle layer (`places-apart`, `zone-places-apart`), which MapView does not make interactive. The stop's own marker still opens the stop.
- **It keeps its point label**, also where the name is set along the landform's axis, so the map shows both names.
- On the data of 2026-11-15 this covers six stops at four pins: the Guadalupe Mountains (J2 stop 4 at 2.7 km, the J3 pass at 9.3 km), Cloverdale Creek (the trap site of J1 and J2, 9.1 km), the Animas Valley (108 km) and Bowie (J4, "just past Bowie, on its east side", 2.6 km).

## Alternatives

- **Hide the pin of every range and valley.** Rejected by the owner: the gazetteer point is a fact the map can show.
- **A flag per place in `places.csv`.** It would need a judgement for each place. The 1 km rule decides the same cases without one, and the stops' reasoning already explains why each stop is not on its pin.
- **Move the stop onto the pin.** Rejected: the stop's reasoning puts the pass on the flank.

## Consequences

- A reader cannot open the Guadalupe Mountains, Cloverdale Creek, the Animas Valley or Bowie from the map. Search still finds them.
- The rule reads the story as the reading progress shows it, so a pin may stand apart early in the book and become clickable when a stop on it is reached.
- The 1 km is a judgement: a stop meant to be at its place but placed more loosely than that would lose its pin's click.
