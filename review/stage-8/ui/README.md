# Stage 8 review: interface changes

This packet covers the eleven interface changes you asked for. Each item has its own commit (one extra fix commit for item 6, and one to keep a name two tools use). Screenshots are in `before/` and `after/`. Desktop shots are 1400 x 900; phone shots are 390 x 844 at 3x, saved at CSS size. The reading progress was "Finished" and the units Imperial for all of them.

**Satellite on localhost.** The MapTiler key does not allow localhost (see `docs/roadmap.md`), so Satellite and Compare fail with a 403 on the dev server. For the Compare screenshots, the test browser answered MapTiler's style request with a plain green style. The green half in those shots stands for the imagery. Check Compare with real imagery on the preview.

## Commits

| Item | Commit | Subject |
| --- | --- | --- |
| 1 | `0e92e28` | Name the units switch Imperial and Metric |
| 11 | `e0ed90c` | Say what the Home button does |
| 9 | `216c5e9` | Add the railroad to the layer key |
| 5 | `fed2a56` | Draw the inset's view box as a box, and say what the inset is |
| 3 | `d3d392d` | Put Compare between Classic and Satellite, in Flat or Tilted |
| 4 | `876f751` | Gather the map's switches into one box, and rename Land colour |
| 6 | `8002f94` | Fold the layer key into the title cartouche |
| 7 | `c7e8769` | Keep "How this was placed" open from stop to stop |
| 8 | `fd50539` | Put All stops under the stepper |
| 6 | `c7f20e1` | Lift the inset clear of the cartouche's Key row |
| 2 | `3dec01e` | Make talk on the road its own block, and open its card at the top |
| 10 | `73ea188` | Step to a stop by clicking its route or place on the map |
| 4 | `450652b` | Keep the basemap switch's accessible name |

## 1. Units: Imperial and Metric

The switch read "mi" and "km". It now reads **Imperial** and **Metric**. Each button's accessible name starts with the word on screen and spells out the units ("Imperial: miles and feet"), so speech input can use the word. The words fit on phones too, because the switches now sit in the Map menu (item 4).

- Before: `before/default-desktop.jpg`, `before/default-phone.jpg` (top right)
- After: `after/item1-desktop.jpg`, `after/item1-phone.jpg`, and in the final layout `after/final-default-desktop.jpg`, `after/final-menu-phone.jpg`

## 2. "Show all 1215 lines spoken on the road"

**What was wrong.** At the mud-house settlement on J2, the stop has 12 lines of its own and the road to Colonia Morelos has 15 (all in episode 1-09, segment `j2-seg-10`). The 15 is right: the button counts only the lines placed on the road from this stop, not every road or episode. But the stop's "Show all 12" button and the "15 lines spoken on the road from this stop" button were both inline underlined text with nothing between them. So they read as one link: "Show all 1215 lines spoken on the road from this stop" (`before/road-desktop.jpg`).

- A click on the left part showed the stop's other six lines. The browser keeps the reader's place when content grows above it, so the new lines went out of view and nothing seemed to happen.
- A click on the right part did open the road's card and outline the road on the map. But the card opened above the stop, scrolled to its foot (`before/roadclick-desktop.jpg`, title cut off), so it was easy to miss.

**What should happen.** The button opens a card for that road alone: its title ("On the road between the mud-house settlement and Colonia Morelos"), how the lines were placed there, and only that road's lines. The map outlines the road's corridor and frames it.

**What I chose.**

- The stop now ends with its own block, ruled off from the stop's lines: a heading "On the road to Colonia Morelos (the fair)" and a full-width button "Show the 15 lines spoken on this road, and the road on the map" (`after/item2-stop-desktop.jpg`, `after/item2-stop-phone.jpg`).
- Every place card now scrolls into view at its top, so its title shows (`after/item2-card-desktop.jpg`, `after/item2-card-phone.jpg`). The exception is a card that marks a line picked in search: that line stays in view.
- A long list of lines (more than 6) that spans several episodes is grouped by episode. The first group starts open, and so does the group that holds a line picked in search. Each group shows 6 lines, then all of them at a click (`after/item2-groups-desktop.jpg`, `after/item2-groups-phone.jpg`: Janos on J7, 49 lines in IV-3 and 56 in IV-4). No road's lines span two episodes today, so road cards keep the single list with "Show all".
- `tools/spoiler-leak.mjs` opens the episode groups before it clicks each "Show all", so it still checks every line.

## 3. Compare between Classic and Satellite

- The basemap switch reads **Classic | Compare | Satellite | Topo**. Compare is a narrow button with a split-frame icon. Its title and accessible name are "Compare the classic map and satellite, side by side".
- With Compare on, the Compare button is filled with ink, like any chosen switch. Classic and Satellite show as **paired**: a light ink wash with an ink rule under the word. That is lighter than "on", but it shows clearly which two maps are side by side (`after/item3-desktop.jpg`, `after/item3-phone.jpg`).
- Compare works in **Flat and Tilted**. In Tilted, the satellite map and the classic underlay take the same 3D terrain as the story layers, so the halves line up. Raised is disabled in Compare (its line work is shifted north and would not line up with imagery). Choosing Compare from Raised turns on Tilted (`after/item3-raised-to-compare-desktop.jpg`: Raised, then Compare, then the swipe dragged to 30%. Result: Tilted on, pitch 40, terrain on).
- The swipe still drags with the mouse and moves with the arrow keys.
- Decision 0017 now says this.

## 4. One family of controls, and a name for Land colour

- The four separate boxes (three switches and a checkbox) are now **one framed box**, top right, with the double ink rule of the cartouche and the inset. It has four rows, each a segmented switch with a small italic label: **Map**, **View**, **Ground**, **Units** (`after/item4-desktop.jpg`).
- **View** and **Ground** hang under Map on a ruled branch, because they change the classic map (View changes compare mode too). On Satellite and Topo their buttons are disabled and their labels fade, so their link to Classic is visible.
- **Land colour is now "Satellite tint"**, chosen on the Ground row: **Paper | Satellite tint**. "Land colour" was easy to read as the relief tint the map already has. "Satellite tint" says where the colour comes from and that it is faint. "Ground colour" was the other candidate; it says what changes but not that it comes from imagery, so a reader would not expect it to need the satellite service. Decision 0017, the Credits page and the roadmap (`docs/roadmap.md`) use the new name.
- **Phones:** the box folds behind one **Map** button (layers icon, `aria-expanded`), so the switches no longer cover a third of the map (`after/item4-phone-closed.jpg`). Tapped, the box opens below the button (`after/item4-phone-open.jpg`). Escape closes it and returns focus to the button, and a tap outside closes it too. Checked at 390 x 844 with the keyboard: Enter opens it, Tab reaches the switches, the arrow keys change them, and Escape closes it.

## 5. The inset map

- **The "weird line".** The inset measured the view with the map's canvas container, which has no height of its own (the canvas inside it is positioned). So the box was always a flat line, at every zoom, and longer the further out you zoomed (`before/default-desktop-inset.png`, `before/tilted-desktop-inset.png`). It now measures the map's own container, so the box has its true shape: a rectangle in Flat (`after/item5-inset-default.png`, `after/item5-inset-zoomin.png`) and a trapezoid in Tilted (`after/item5-inset-tilted.png`).
- The box's corners are kept inside the inset's frame, so a view that runs past the region's edge still draws as a closed box. A view that lies off the region shows as a small square at the nearest edge (`after/item5-inset-offregion.png`). A view wider than half the region hides the inset, as before. MapLibre's minimum zoom (4) keeps every view far narrower than the world, so the antimeridian cannot be reached. As a guard, a span over 180 degrees or a non-finite corner also hides the box.
- The inset now has a caption, **"Where you are"**, and a tooltip: "Where you are: the whole story region, with a box around the part the map shows now". The screen reader label says the same.

## 6. The key inside the cartouche

- The separate Key button under the zoom buttons is gone. The key is now a **"Key" disclosure inside the title cartouche**, under the title, folded at first (`after/item6-desktop.jpg`). It is a native details element, so Tab reaches it, Enter or Space opens it, and the focus ring shows.
- Opened, it grows the cartouche upwards over the inset. It stops clear of the map's switches, and the cartouche scrolls when the map is short (`after/item6-key-open-desktop.jpg`).
- The key shows with the classic map and in compare mode, which both draw the classic marks. It does not show on Satellite and Topo, as before.
- **Phones** had no cartouche. They now show a small one, the title alone, holding the folded key, with the inset above it (`after/item6-phone.jpg`). Opened, the key covers the map up to the Map button and scrolls (`after/item6-key-open-phone.jpg`).
- A follow-up commit lifts the desktop inset 26 px, as the taller cartouche had run into it.

## 7. "How this was placed" stays open

Its open state now lives in App, not in each stop's card. It stays open or closed as you left it across Back, Next, picks from All stops and changes of journey, on desktop and in the phone drawer (`after/item7-desktop.jpg`, `after/item7-phone.jpg`: opened at stop 1, still open at stop 3). Tested: open, then Next twice: still open. Change journey: still open. Close, then Next: stays closed. The other folded sections (All stops, Named elsewhere) already kept their state, so they needed no change.

## 8. Panel order

The panel now reads from the general to the particular:

1. Reading progress, then search (they govern the whole map, so they stay at the top)
2. Journey picker
3. Back / Next stepper
4. **All stops** (moved up from below the stop, and ruled off from what follows)
5. The card for a pick on the map or in search, if any
6. The current stop: name, note, How this was placed, open questions, Spoken here, On the road
7. Named elsewhere
8. Page links

On phones the stepper stays in the drawer's peek row, nearest the thumb. The journey picker and All stops come straight under it, then search and progress, then the card and the stop (`after/item8-desktop.jpg`, `after/item8-phone.jpg`).

## 9. Railroad in the key

The key has a new group, "The land", with a Railroad row. The symbol uses the same measures as the map's `railroad` and `railroad-ties` layers in `style.ts`: a 0.8 px ink line under 1 px cross-ties, 4 px tall and 13 px apart (`after/item9-key.png`).

## 10. Map and panel together

A click (or tap) on a journey's route, or on a place where a journey stops, moves the panel to that stop. Back and Next then step on from there.

- **On a route:** the stop is the end of the clicked segment nearer the click (`after/item10-line-desktop.jpg`, `after/item10-line-phone.jpg`: J1 in focus, a click on J2's route north of the Guadalupes brings J2 into focus at stop 4).
- **Several journeys in one place** (Colonia Morelos has stops on J2, J3 and J4; roads are shared too): if the journey in focus is one of them, it stays in focus and goes to its own stop there. If that journey passes the place more than once, it goes to the visit nearest the current stop. Otherwise the journey of the topmost route under the click comes into focus. Failing that, the first journey (by number) that stops at the place.
- **Spoilers:** only reached journeys and stops are drawn or listed, so a click never moves the reader ahead in the book. Tested at progress 1-08: a click where J2's route would be does nothing.
- **Places that are not stops, and areas,** open their card as before (`after/item10-place-desktop.jpg`, Grant County).
- The routes get an unseen 14 px hit line, so the thin lines are easy to click. The pointer shows over anything a click would open.

## 11. The Home button

The icon was a house, which reads as "home page". It is now a frame of four corners around a dashed route. The title and accessible name are **"Show the whole journey"** (`after/item11-home.png`). It is still a native button among the zoom buttons, with its focus ring and its place in the tab order.

## How to test

From the repo root: `cd site && npm run dev -- --port 5191`, then open http://localhost:5191/. Set the reading progress to "Finished" for the full set.

1. **Units:** top-right box, Units row: Imperial | Metric. The scale bar and heights change.
2. **Road lines:** pick J2, open All stops, choose "The mud-house settlement". Scroll to "On the road to Colonia Morelos (the fair)" and press the button. The road's card opens at its title, with 15 lines, and the map outlines the corridor. For grouping, go to J7 stop 24 (Janos).
3. **Compare:** on the preview (real imagery), press the split icon between Classic and Satellite. Classic and Satellite show as paired. Drag the swipe. Switch to Tilted, then to Raised and back to Compare: it should come up Tilted.
4. **Controls:** on a phone (or a 390 px wide window), tap Map, change things, press Escape or tap the map. Try Ground: Satellite tint on the preview.
5. **Inset:** zoom in past half the region. The inset shows "Where you are" with a box, and a trapezoid in Tilted. Pan off the region: a small square at the edge. Hover for the tooltip.
6. **Key:** bottom right, "Key" under the title. Tab to it and press Enter.
7. **How this was placed:** open it, press Next a few times, change journey.
8. **Panel order:** All stops sits under Back and Next.
9. **Railroad:** open the Key, see "The land".
10. **Map clicks:** with J1 in focus, click a J2 route line, then a J2 stop's town, then with J3 in focus click Colonia Morelos (stays J3). Set progress to an early episode and check that unreached journeys cannot be clicked.
11. **Home:** hover the button under the zoom buttons for its tooltip, and Tab to it.

Checks run: `npx tsc -b`, `npm run lint`, `npm run build` before each commit; `node tools/spoiler-leak.mjs http://localhost:5191/` at the end (result below).

## Open questions

- **Desktop controls box size.** The box is about 300 x 180 px, top right. The journey framing (`frameStops`) still pads 70 px at the top and 130 px on the right, so on some journeys a stop in the far top-right corner can sit under the box. Options: larger padding there, or let the box fold on desktop too (the phone's Map button already exists).
- **Satellite tint, or Ground colour?** Your call on the name. The Ground row makes either easy to swap.
- **Should a click on a stop's town also open the town's card?** It now goes to the stop only. The stop shows the stop's own text, which is usually what the reader wants. The town's card is still a search away.
- **Compare with real imagery, and in Tilted,** is untested here because of the localhost key restriction. Please check it on the preview.

## Spoiler-leak test

`node tools/spoiler-leak.mjs http://localhost:5191/` against the final code: **"No spoiler leaks.", exit 0**, at all ten reading positions (unset, none, 1-03, 1-08, 2-04, 3-08, 3-12, 4-05, 4-08, all; 171 panel steps at "all").

The first run stopped at 4-05 on a test-harness problem, not a leak. With episode groups, a stop can have several "Show all" buttons. The test collected them all and then clicked them one by one, but each click removes its button. The helper now clicks the first remaining button until none are left. That fix is in the packet's commit.
