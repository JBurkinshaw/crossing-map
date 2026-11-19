# 0060. On phones the story comes first, and the map carries less

Status: accepted (2026-11-18)
Phase: P1

## Context

The site has three audiences: readers using it beside the book, readers of McCarthy who already know the book, and people who come for the cartography. Many of the first two will open it on a phone, from a link on Reddit or in a chat. A review of the phone layout on 17 November 2026 (screenshots and measurements at 390 by 664 px, an iPhone 13's page area) found that it showed the site's controls before its content:

- At its opening height the drawer showed the stepper, the site's title, the progress badge, the journey picker, All stops and search. The stop's name and synopsis began 288 px down, out of view.
- The half-height map is about 390 by 330 px. It carried seven pieces of furniture: zoom in, zoom out, Home, credits, scale, the Map button and the cartouche, which covered about a fifth of it.
- All seven journeys drew at once, and the background names drew at the same zooms as on a 1,400 px screen.
- The first-visit dialog held 154 words before its question and opened scrolled past its own heading, 107 px down on an iPhone 13 and 392 px on an iPhone SE, because focus starts on "Not yet".
- Stop pins were 22 px across, the zoom buttons 29 px, and the header and footer links 17 to 18 px tall. Fifteen runs of text were 12.8 px italic at 70% ink.
- The phone layout started at a width of 720 px and ignored height. A phone on its side got the desktop layout, with the cartouche over most of the map, and an upright iPad Mini got a map column 390 px wide.

## Decision

Everything in the interface belongs to one of three layers, and a layer further down never stands in front of one above it.

| Layer | Holds | Where |
| --- | --- | --- |
| The story | The stop, its episode and synopsis, Back and Next, Read on | Always in view |
| The reader's tools | Reading progress, the journey picker, All stops, search, "Spanish here", the key | One tap or one scroll away |
| The craft | How a place was placed, open questions, the views and grounds, the data, the decisions | Folded, or on the pages |

On phones:

- **The drawer's order** is the card for a pick, the stop, then the tools (progress, journey, All stops, search), then places named elsewhere, the site's title and its page links. The drawer's body scrolls back to its top when the stop changes.
- **The stepper shows the whole stop name** on two lines, and the drawer's peek height grows from 96 to 112 px to hold it.
- **The map keeps Home, credits, the Map button and a Key button.** The zoom buttons and the scale go, and the cartouche is the Key button alone. The same holds on any screen under 500 px tall.
- **Only the journey in focus is drawn.** "Show all journeys" in the key draws the rest, and the choice stays for the visit. Wider screens start with every journey drawn and have the same switch.
- **Background names come in a zoom level and a half later:** context places, water places, passes, creek names and contour figures.
- **Type:** nothing under about 14.5 px, the stop's own text at 16 px, and the episode's summary upright.

On every screen:

- **An open question on a card or a stop folds to its title.** The Open questions page still sets each one out in full.
- **Each stop ends with "Next: " and the next stop's name.** It moves focus to the new stop's name, which also brings it into view.
- **The first-visit dialog** says what the site is in one paragraph, says that the Spanish is translated, and asks its question. It opens at its top. What it used to say about certainty and corrections is on the About page.
- **How it's built is linked from the panel's header**, beside About, so the craft has a door that is not at the foot of the panel.

On touch screens, and on phones whatever the pointer, the panel's controls are at least 44 px tall, the map's own buttons are 44 px, and each stop pin has an unseen area about 40 px across that takes the tap.

A phone on its side (wider than 720 px, under 500 px tall) keeps the side panel at 300 px, with no frame and no inset. An upright tablet (721 to 1,024 px wide) has the 300 px panel and the frame's rule without its band of labels.

## Alternatives

- **A scrolling story with a pinned map**, in place of the stepper. Studies of story maps favour scrolling over stepping through (Song and others, *Cartographic Perspectives* 100, measured on desktop only). It is the Phase 2 "story mode" and a rebuild of the panel. The Next button at the foot of each stop gives the reading a downward flow in the meantime.
- **A compact header row** holding the title, progress and search above the stop. It would keep the spoiler setting in view, but it puts tools above the story again. The progress badge is one scroll down, and the stop shown is always one the reader has reached.
- **Keep the zoom buttons on phones.** A pinch zooms, a double tap zooms in, and Home goes out to the whole journey, but there is no single-tap way to zoom out one step. WCAG 2.5.1 asks for one. The buttons can come back with one CSS rule if a reader needs them, and the roadmap carries the question.
- **A drawer on upright tablets.** It would give the map the full width. The side panel was kept because the drawer's breakpoint is shared by the key's sheet, the frame and the map's padding, and a narrower panel solves most of the problem with two CSS rules.
- **Fade the other journeys further on phones**, not hide them. At the opening zoom even faint lines cross the journey being read.
- **Units out of the Map menu** and into the reader's tools. Left where it is until there is a place for it that does not add a control to the drawer.

## Consequences

- The reading-progress badge is no longer in view when the drawer opens on a phone. The stop under it is always a reached one, and "Read on" still shows on the last of them.
- On phones the map no longer shows the site's title. The title is in the first-visit dialog, the browser's tab and the foot of the drawer.
- A window resized across 720 px keeps the label zooms it loaded with, as they are part of the map's style.
- The roads of the base map are drawn in thin dashed lines that can be read as routes once the other journeys are hidden. Their drawing is on the roadmap.
- `docs/design.md`, section 9, describes the layout as built. What the review left open is in `docs/roadmap.md`, section 2.

## Sources

- Nielsen Norman Group, [Progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/) and [Bottom sheets](https://www.nngroup.com/articles/bottom-sheet/).
- Archie Tse, [Why we are doing fewer interactives](https://github.com/archietse/malofiej-2016/blob/master/tse-malofiej-2016-slides.pdf), Malofiej 2016.
- Ordnance Survey, [Map legends](https://docs.os.uk/more-than-maps/geographic-data-visualisation/guide-to-cartography/map-legends).
- Datawrapper, [Locator maps for mobile devices](https://www.datawrapper.de/docs/locator-maps-for-mobile-devices).
- Song, Roth and others, [Visual storytelling with maps](https://cartographicperspectives.org/index.php/journal/article/view/1759), *Cartographic Perspectives* 100.
- W3C, WCAG 2.2: [Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) and [Pointer Gestures](https://www.w3.org/WAI/WCAG22/Understanding/pointer-gestures.html).
