# 0033. One ink per journey, and a line's dash for how sure it is

Status: accepted (2026-11-16). Owner's request: the journeys, and the inferred areas and regions, were hard to tell apart at a glance.
Phase: P1

## Context

Design 5.1 gave each character one ink: slate for the wolf, oxblood for Billy, green for Boyd, plum for "the girl". Billy follows four of the seven journeys, so J2, J3, J5 and J7 shared one colour. The other inks were dark and greyed: the wolf's slate and Boyd's green lay 5 apart in OKLab distance (×100), and under simulated deuteranopia the closest pair was 2 apart. At a glance every route read as a dark line.

The three kinds of route line did not separate either. The modelled line's dashes (`[6, 1.5]` at 3 px with round caps) lost their gaps to the caps and read as solid; the curves' short dashes were drawn at the same weight as the traced lines; and the key drew dash patterns the map did not use. Inferred areas and regions were both a dashed edge over a faint fill, regions in ink at 4 % opacity.

## Decision

- **One ink per journey,** from the hand-coloured county tints of the Mitchell and Gray atlas maps (`docs/inspiration/rumsey.md`), with J2 taking the red route of the Trail of Blood Meridian map (`docs/inspiration/reddit.md`): J1 indigo `#2e4a8a`, J2 vermilion `#c0391b`, J3 oxblood `#6e1f1c`, J4 sap green `#2f6f2a`, J5 ochre `#a8740c`, J6 violet `#8a4fb0`, J7 rose madder `#b8457f`. Each has at least 3.2:1 contrast against the paper `#efe5c8` (WCAG's 3:1 for graphics) and lies at least 14 from the water ink. With normal vision the closest pair is 12 apart (previously 0, for the journeys that shared oxblood).
- **A line's dash says how sure it is,** graded as the period survey sheets grade roads and trails (Wheeler; the Department of Arizona sheet): solid at 3.5 px where the line follows the road or river the book names; long dashes, 12 px with 6 px gaps at 3 px, for a modelled path (decision 0021); sparse short dashes, 4 px with 6 px gaps at 2 px and 75 % opacity, for a curve that only joins the stops. Dashed lines have butt caps so their gaps stay open. Out of focus every line is half as wide. The widths and dashes are constants in `site/src/map/tokens.ts`, which the key's swatches draw from too.
- **The key** groups the three under "How sure the line is", below the journeys, in the reader's words: "Follows the road or river the book names"; "Likely route over the terrain, worked out by this site: the book doesn't trace it"; "Route not known: the line only joins the stops". A leg's card names its line the same way.
- **Inferred areas** are a flat tint in their journey's ink (18 % in focus), after the land-class tints of Wheeler sheet 84, with a dotted edge for "somewhere in here".
- **Regions** have no fill: a fine ink line with a broad soft band inside it (6 px at 15 %), after the ribboned county edges of the Mitchell and Gray maps.

## Alternatives

- **Keep one ink per character and tell Billy's journeys apart by pattern.** The dash already carries how sure a line is; a second pattern would make the two meanings fight.
- **Seven brighter, modern hues.** Clearer still, but off the paper-and-ink look of design 5.1.

## Consequences

The journeys tell apart at a glance, and the colour no longer says who travels. Seven inks cannot all stay apart for colour-blind readers: under simulated deuteranopia vermilion (J2) and ochre (J5) come within 5, and under protanopia vermilion and sap green (J4) do. Those journeys lie mostly in different country, and the numbered stops carry their journey's ink and name. The scores come from a scratch script (OKLab distance; Machado et al. 2009 simulation at full severity), not from `pipeline/measure/`, as they measure colours, not ground.
