# 0082. Lettering at low zoom, and the land cover waits

Status: accepted (2026-11-21). Amends 0040, 0076, 0079 and 0081.
Phase: P1

## Context

The opening view (zoom about 5.5) had grown large drawings (decisions 0076 and 0079) and a red title after the Trail of Blood Meridian map (decision 0081). The owner found the title too like that map and too far north, asked for the book's own region names across the land, for the larger features to come before the stops and mountain glyphs at low zoom and give way to them closer in, for two of the book's night skies, and for the land cover and the place pins to wait until the reader zooms in, past the drawings. The map should open on the whole of this view.

## Decision

- **Region names.** Six of the book's names for open country (the Animas Plains, the bootheel, the Carretas Plain, the plains of Chihuahua, the Babícora and the Bavispe), in spaced small capitals in the map's ink at 0.8 opacity, each turned to follow its valley or river. They are about 15 px tall at the opening view, hold full strength to zoom 7.5, and fade out by 8.5 (`site/src/map/regionNames.ts`).
- **The title.** "THE CROSSING" in spaced small capitals in the map's ink, with no subheading, after the titles of the survey sheets the map follows, not the Blood Meridian map's red. It stands over the north of the story at 108.4 W, 33.75 N, just above the drawings and over the plains of Saint Augustine, whose name it replaces. It is a text symbol in the map's own fonts, not an image, and grows and fades as before.
- **Larger lettering first at low zoom.** The region names and the title are lifted above every story layer, glyphs and captions included. They never push another label aside, and as they fade on zooming in the stops and their names come forward. MapLibre cannot reorder layers by zoom, so the swap is made by the fade. The journey's stop badges are HTML laid over the map, above any map layer, so below zoom 7.5 they give way to numbered rings drawn on the map itself, under the lettering: the current stop filled, the stops behind it paler, a number shown where it fits. A click on a ring steps to that stop. From 7.5 the badges and the cluster badges come back as the names fade.
- **Place pins wait for zoom 7.** The place pins, tale diamonds and place names show from zoom 7, where the drawings start to fade. A picked place's outline shows at any zoom. The journey's stops show at every zoom.
- **The map opens on the whole opening view.** On first load the map frames every large drawing and the title, clear of the map's controls. A returning reader's saved stop is still brought into focus in the panel, but the map does not fly to it until they move. A link with a map view keeps its view.
- **Two night skies** from the book join the large drawings. The horned moon on its back with Venus above it (3-08), with riders on the plain and a low range in the west the passage does not give, stands in empty ground in the west. Cassiopeia swinging round the polestar (2-05) is the map's north arrow: the polestar, rayed, with a meridian rising to a lettered N, and the W at three of Billy's wakings four hours apart swinging round below it, its five stars and the pole placed from the Yale Bright Star Catalogue in an azimuthal projection about the pole, with a few random fainter stars. It is 1.8 degrees wide and stands just above the moon, so the book's two skies sit together. The book does not give where in the sky the W stood, so its three positions are chosen to keep the N clear.
- **The land cover waits for zoom 7.** It fades in between zoom 7 and 7.8 as the drawings and title fade out. Below 7 the Ground switch shows Paper, with Land cover disabled and the line "Land cover shows as you zoom in". The reader's choice is kept: zooming out does not change it, and land cover comes back on zooming in. Choosing Paper is a choice like any other. This follows the switch's existing rule for Satellite tint in the Oblique view, and the common practice in GIS tools: a layer outside its zoom range is dimmed in the layer list, not hidden, and says why. The choice lasts for the visit, as it did before.

## Alternatives

- **Hide the Land cover option at low zoom.** The switch would change shape as the reader zooms, and they would not learn the option exists.
- **Switch the stored choice to Paper on zooming out.** Zooming back in would leave the reader on Paper, against their choice.
- **`aria-disabled` on the option, so it stays in the tab order.** Guidance is divided. The switch's group description already carries the reason, and the native `disabled` keeps it consistent with the Satellite tint option.
- **Captions on the large drawings.** The owner left them out.
- **Cassiopeia as a large drawing in the north-east, above the title,** with Billy asleep and his horse under the sky. It sat apart from the story and crowded the title.
- **The region names and title as HTML,** above the stop badges. They would no longer be part of the map's own lettering.

## Consequences

At the opening view the map reads as country (title, region names, drawings and skies) over paper, with the story's stops as small rings under the lettering. From zoom 7 to 8 it turns into the story map with its land cover. A reader who opens on a journey at zoom 8 or closer (J1, J2 and J6) sees the land cover at once and none of the low-zoom lettering.
