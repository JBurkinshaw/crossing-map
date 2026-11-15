# 0027. Wheeler frame, water places and type scale on the map

Status: accepted (2026-11-14). Rolls out three cards the owner adopted from the Wheeler lab's test area (review/stage-9/wheeler-places, review/stage-9/wheeler-type) over the whole classic map.
Phase: P1

## Context

The lab tried a graticule and frame, springs and stations as places, and a strict type hierarchy in a test box (109.6 to 108.4° W, 30.5 to 31.6° N). The owner adopted them for the site, except historic roads. Each needed choices the test box did not force: where the water places stop, what the frame costs on a phone, which unit the type scale counts from, and how a pass name fits at low zoom. The rollout packet is review/stage-9/wheeler-site/README.md.

## Decision

- **Graticule and frame.** The 15′ graticule over the story box from zoom 8, in faint ink, and on the classic map in the Flat and Tilted views the frame of sheet 70A: a thin-thick-thin rule (1, 2, 4, 2, 1 px), a 20 px margin band with the graticule's labels in Wheeler's short form (15′, 30′, 109°), and a 1 px neatline. The labels hide while the map is tilted, because one projection per line is wrong there. Everything set on the map moves inside the neatline. On phones (720 px and narrower) the frame is the rule alone, 6 px, with no band or labels: a 20 px band each side would take a tenth of a 390 px screen. The cartouche's rule becomes a thin neatline inside a thin-thick rule.
- **Water places.** Springs, wells, tanks, ranches and stations from GNIS and GeoNames, by the lab's rules, inside the journeys corridor (20 km either side of the legs ridden or walked, the fine relief's region). The whole story box would bring several thousand GeoNames ranches the reader never passes. The layer is published (`data/water_places.geojson`) with the book's own springs and ranches in it, pointing at their places; the map draws only the gazetteer's, from zoom 11, as the lowest labels, because the story layers already draw the book's.
- **Type scale.** The unit is the site's spot height, 10.5 px at zoom 11 (the size the owner chose when the map's small type was enlarged), not the lab's 9.5 px. Towns are 14.5 px roman, the `city` kind in capitals; ranches and springs 10.5 px italic at 0.72 opacity unless the journey stops there; passes 10.5 px small capitals. Sizes are 0.85 of that at zoom 9 and 1.15 at 13. Landform names along their axes are unchanged.
- **Passes.** Every named pass (162 in the box) has a line through it from `crossing.pass_lines`: along a Natural Earth road within 1 km of the saddle (5 passes), else across the saddle by the DEM's curvature. The map sets the name as a point label turned to that line, not along it: a 5 km line is shorter than the name below zoom 11, and MapLibre drops a line label longer than its line. A named pass then has no glyph, as on Wheeler's sheets. Pass names sit just under the summit glyphs in the label order, so summits win. A pass the book names takes the place's `first_seen`, so its name shows only from that episode, where its glyph named it from the start.

## Alternatives

- **Water places over the whole story box.** Too many, and mostly far from the story.
- **The frame's band on phones at 15 px, as in the lab.** 46 px of a 390 px width for labels that a phone reader rarely needs.
- **The lab's 9.5 px unit.** It would shrink the spot heights the owner enlarged.
- **Pass names along their line (`line-center`).** Dropped below zoom 11, where the reader first meets the passes.

## Consequences

The map loses 31 px of view on each side on a desktop. Pass glyphs for named passes are gone, and where a pass name loses a collision nothing marks the pass. The water places carry GeoNames ranches with no date, some of them later than the 1940s. Roads for the passes are today's highways until traced period roads exist.
