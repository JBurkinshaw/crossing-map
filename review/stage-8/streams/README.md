# Creeks: one rule for both countries

The owner's question: south of Colonia Morelos the map showed only the large rivers at high zoom, too little for context; north of it there were many small streams, almost too many. How to find the balance?

## Why it happened

The creek layer was every NHD natural stream in six US watersheds (HU8), some of which run into Sonora, shown from zoom 9 (named) and 10 (all). Elsewhere in Mexico only the named rivers were drawn. Colonia Morelos sits near the southern edge of those watersheds, so the density jumped about fortyfold there (table below).

## The rule

`tiles/creeks.py` builds the `creek` layer of `base.pmtiles` from both networks:

- **Mexico:** INEGI Red Hidrográfica 1:50,000 (all seven regions in the cache), `CORRIENTE DE AGUA` and `LINEA CENTRAL`, Strahler order from `ORDER_1`, intermittent from `CONDICION = 'INTERMITENTE'`.
- **US:** NHD High Resolution (all 73 HU8s in the cache), ftype 460 and 558, Strahler order computed from how the lines join, intermittent from fcode 46003 and 46007.
- Each network is clipped to its own side of the border (Natural Earth admin 1), so the two do not double along it.

A stream is drawn from a zoom set by its order (INEGI's order, or NHD's plus one, see below):

| Order | 2 | 3 | 4 | 5 | 6 | 7 and up |
|---|---|---|---|---|---|---|
| Drawn from zoom | 12 | 11 | 10 | 9 | 8 | 7 |

Order 1 is never drawn. The target was a constant amount of line per screen: about 1 km of stream per km² of ground at zoom 12, halving with each zoom out (about 100, 50, 25, 12 and 6 km per 100 km² at zoom 12, 11, 10, 9 and 8). On screen that is one stream line every 30 px or so at any zoom. INEGI's order 1 alone is 100-185 km per 100 km², which would more than double the zoom 12 density. That is close to the "almost too many" the owner saw north of Morelos (222).

Styling (`site/src/map/style.ts`, `creek` and `creek-label` only): width tapers with order (at zoom 12, about 0.8 px for order 2 to 2 px for order 7). Intermittent streams are solid at 65% opacity and perennial ones at 95%, with no dashes. Names show from zoom 11, only on creeks drawn at that zoom. US names come from GNIS. Mexican names come from INEGI's toponym points (`_to`, terms ARROYO, RÍO, CAÑADA, BARRANCA, CAÑÓN): each point names the nearest stream within 300 m, and the name runs up and down that stream while its order holds. A creek named after a river that the river layer already labels (for example "Río Bavispe") is drawn but not labelled.

### NHD against INEGI: the offset goes the other way

The brief expected NHD (1:24,000) to have higher orders than INEGI (1:50,000). Measured, it is the reverse. Cumulative density (km per 100 km²) of streams of order k and up:

| Order k and up | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| INEGI, Bavispe crossing | 288 | 103 | 53 | 24 | 11 |
| INEGI, south of Morelos | 255 | 87 | 46 | 21 | 9 |
| INEGI, Babícora | 164 | 68 | 38 | 17 | 8 |
| NHD, Peloncillos (US) | 119 | 47 | 24 | 11 | 4 |
| NHD, Animas Valley (US) | 127 | 56 | 26 | 12 | 4 |

NHD carries about half INEGI's length at each order, so NHD's order k matches INEGI's order k+1 closely. NHD's orders are therefore raised by one (`NHD_SHIFT = 1`). Where both networks cover the same Mexican ground (the six border HU8s inside Sonora and Chihuahua, 25,700 km²), NHD and INEGI are almost identical at every order (183/75/38/17/8 against 183/76/40/19/9). NHD's Mexican part seems to be drawn at INEGI's density, so it says nothing about the US side. Whether the US side is sparser because of the land or because of how it was mapped is not settled. In either case the density target applies.

### A bug in the shared Strahler helper

`rivers.strahler` adds one wherever two equal orders meet. Where a channel splits and joins itself again (braids, irrigation ditches, and 193 NHD lines repeated in two watersheds), it adds one at every rejoin, and NHD orders reached 242 along the Rio Grande. `creeks.strahler` is the same walk, but each order remembers the node where it was reached, and two equal orders raise it only if they were reached at different nodes. NHD's highest order is now 7. As asked, `rivers.py` is not changed. There the inflated orders only make main stems cheaper to trace, so the traced rivers are probably fine, but see the open questions.

## Density before and after

Drawn stream length, creeks plus rivers, in km per 100 km² of ground. It is measured from the tiles with the style's filters, in seven windows of about 0.5° by 0.45° (`tiles/out/scratch/measure.py`, not committed; equal-area projection per window). Zoom 12 is drawn from the zoom 11 tiles.

| Region | Before z8 | z9 | z10 | z11 | z12 | After z8 | z9 | z10 | z11 | z12 |
|---|---|---|---|---|---|---|---|---|---|---|
| North of Colonia Morelos (30.85-31.3 N) | 3.8 | 3.9 | 217 | 222 | 222 | 9.0 | 13.0 | 23.0 | 43.2 | 86.0 |
| South of Colonia Morelos (30.35-30.8 N) | 4.5 | 4.6 | 4.8 | 4.9 | 4.9 | 9.1 | 13.1 | 24.9 | 48.9 | 88.4 |
| Bavispe crossing (30.0 N, 109.29 W) | 3.3 | 3.4 | 3.4 | 3.4 | 3.4 | 8.8 | 13.4 | 26.1 | 54.3 | 102 |
| Babícora | 0 | 0 | 0 | 0 | 0 | 1.7 | 7.3 | 16.0 | 36.0 | 65.8 |
| Casas Grandes | 0 | 0 | 66.7 | 67.4 | 67.4 | 4.6 | 8.0 | 18.4 | 40.1 | 70.1 |
| Peloncillos (US) | 1.1 | 5.9 | 115 | 117 | 117 | 4.5 | 10.9 | 23.9 | 45.9 | 116 |
| Animas Valley (US) | 0 | 7.8 | 122 | 124 | 124 | 3.8 | 11.2 | 25.5 | 54.2 | 123 |
| Target | | | | | | 6 | 12 | 25 | 50 | 100 |

North and south of Morelos now agree within 10% at every zoom. Across all seven windows the spread at each zoom is under two to one, where before it was over forty to one. The Babícora is the sparsest: it is a closed basin with a plain in the middle.

## Size and build

- `base.pmtiles`: **15.0 MB** (tiles-v7: 6.0 MB). Three things keep it under 20 MB. First, order 2 streams (drawn only at zoom 12) are kept only inside `FINEST_ORDER_BOX` (110.75-106.25 W, 28.25-33.25 N, the journeys' country from the Sonora river towns to the Babícora, Silver City and Lordsburg). Second, the pieces of one stream are joined into one line. Third, lines are simplified to 30 m (a pixel at zoom 12). Without the box, order 2 everywhere took the creek layer alone to 24 MB. Without joining and simplifying, it was 36 MB.
- `uv run --project pipeline python tiles/build_base.py` now takes about 20 minutes, up from about 6, because it reads both full networks (1.5 million INEGI lines and 860,000 NHD lines).
- **Needs tiles-v8.** Only `base.pmtiles` changes. `tiles/release.txt` is unchanged (still tiles-v7). The style commit reads the new `o` and `i` attributes, so with the tiles-v7 base the creeks disappear and old NHD names would still label. Release tiles-v8 with this base before deploying the style.

## Screenshots

`screenshots/before-<place>-z<zoom>.jpg` and `after-<place>-z<zoom>.jpg` for Colonia Morelos, the Peloncillos, the Bavispe crossing (30.0 N, 109.29 W) and the Babícora, at zoom 9, 10, 11 and 12, desktop 1400x900. Also `after-morelos-phone.jpg` (390x844 at 3x, zoom 11.5) and `after-raised-z11.jpg` (the Raised view, which keeps its own streams; no console errors). Retake them with `node tools/creek-shots.mjs review/stage-8/streams/screenshots after` against a dev server on port 5194.

Compare `before-morelos-z10.jpg` with `after-morelos-z10.jpg`, and `before-bavispe-z11.jpg` with `after-bavispe-z11.jpg`. Before, the creeks were hard to see at all in Sonora. They were either absent, or faint and dashed among the contours.

## How to test

1. `cp tiles/out/base.pmtiles site/public/tiles/` (or build it first) and `cd site && npm run dev -- --port 5194`.
2. Open `#map=11/30.83/-109.22` (Colonia Morelos) and pan south: the stream density should not change where it used to stop. Do the same across the border near the Peloncillos (`#map=10/31.5/-109.0`): NHD and INEGI should meet without doubling.
3. Zoom 9 to 12 anywhere: each zoom in adds the next order, wider lines are the larger streams, and perennial streams are darker.

## Open questions

1. **Zoom 12 density.** It is now about 1 km per km² (one line every ~30 px). If the owner wants more at zoom 12, order 1 could come in at zoom 13, but it would need zoom 12 tiles and would cost several MB.
2. **The order 2 box.** Outside `FINEST_ORDER_BOX`, zoom 12 shows the same streams as zoom 11. Is the box right, or should it follow the journeys more closely? A box shows nothing about where later journeys go. A corridor around the routes could hint at them.
3. **US coverage.** The NHD cache covers only the 73 HU8s that the named rivers cross, so parts of New Mexico and Arizona inside the story box (for example around Magdalena and north of the Gila) have no creeks. Fetching the missing HU8s would close the gaps and lengthen the build.
4. **`rivers.strahler`.** Should it take the same braid fix? It would change the order weights the river tracer uses (orders above about 8 on NHD). The traced rivers would need comparing before and after.
5. **Labels.** Mexican names come from toponym points, so a name can stop short of a stream's full length or, rarely, land on a neighbour. Spot-checked near Morelos (Arroyo Cajón Bonito, Arroyo la Aguaja). The names are geography, not story, so they are not spoiler-filtered, as before.
6. **Plan and stage 2 notes.** The plan's backlog note on creeks and the stage 2 README ("the creeks ... are not done") could be updated once this is accepted.
