# 0079. The large drawings closer in

Status: accepted (2026-11-20). Amends 0076.
Phase: P1

## Context

Decision 0076 set six large drawings in the empty quarters east and west of the story, each 3 degrees wide, fading out between zoom 6 and 7. The owner found them not really visible in most situations. Two things hid them. The boxes stood at the far edges of the story box, often off a narrower screen. And the map opens on a reader's journey at zoom 6.1 (J7) to 9.1 (J2), where they had already faded.

## Decision

- **Each box is 2.2 degrees wide and stands as near the story as a box can with no stop or route line under it.** A search over the story's stops and legs, in 0.2 degree steps, scored each box by the route line inside it and its distance from the story's centre (108.6 W, 31.0 N). The six best sit 2.3 to 3.8 degrees from that centre, against 4 to 5 before: the she-wolf south in Sonora, the riders in the sierra to the west, the cranes in Arizona, the horse herd in the Chihuahua desert east of Casas Grandes, the lone rider in New Mexico and the ruined church in south-east Chihuahua.
- **They are at full strength out to zoom 7 and gone by 8**, where one would fill the screen.

## Alternatives

- **Show them at any zoom.** Past zoom 8 one drawing would be wider than the screen and cover the story.
- **Fixed-size icons instead of georeferenced images.** They would show at every zoom at one size, but decision 0076 keeps them out of the sprite, and a drawing that grows with the land reads as part of the map.

## Consequences

The drawings show at the whole-story view and in the opening views of J3, J4, J5 and J7, and fade as the reader zooms in. J1, J2 and J6 open at zoom 8 or more, where they are gone. Place pins and their names may draw over them, as over the relief.
