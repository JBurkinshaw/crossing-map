# 0061. Each route is lettered with its journey's number

Status: accepted (2026-11-18)
Phase: P1

## Context

The seven journeys are told apart by ink alone (decision 0033). A line's dashes cannot help, because they say how sure the line is. Stop numbers show only on the journey in focus.

The inks were chosen to be at least 12 apart from each other (OKLab distance times 100). Simulated for colour-vision deficiency with the matrices of Machado, Oliveira and Fernandes (2009) at full severity, the closest pairs fall well under that:

| Simulated | Closest pairs |
| --- | --- |
| Protanopia | J2 and J4: 5.3. J4 and J5: 6.7 |
| Deuteranopia | J2 and J5: 5.1. J2 and J4: 8.3 |
| Tritanopia | J2 and J7: 6.2. J1 and J4: 6.9 |

WCAG 1.4.1 asks that colour not be the only way to tell things apart where they must be matched to a key.

## Decision

Each route is lettered with its journey's number ("J2") along the line, in the journey's ink with a paper halo, in 13 px roman. The key already names each journey by that number. The lettering follows the line, as the base map sets a river's name along its course (decision 0027), and repeats about every 300 px.

Roman, not the italic the map uses for quiet names: IM Fell's italic J has a swash that is hard to read at this size on a slant.

## Alternatives

- **A different dash or mark for each journey.** Dashes already carry certainty (decision 0033), and a second pattern on top would make both hard to read.
- **Stop numbers on every journey's pins.** Pins out of focus are not drawn, and drawing 171 numbered pins is the clutter the phone layout removes (decision 0060).
- **The journey's short name along the line** ("First crossing"). Most legs are too short to hold it.
- **New inks chosen for colour-vision deficiency.** No set of seven keeps the period palette and stays apart under all three simulations, and the lettering is needed either way.

## Consequences

- A reader who cannot tell two inks apart can read which journey a line belongs to, and the key's "J2 First crossing" says what that is.
- The lettering shows in every view and over satellite imagery. Its size, spacing and offset are first settings and may want tuning on the tiles of the Oblique view.
- `journeys-name` is a story layer, so spoiler mode cuts it with the routes.
