# 0034. The Oblique view: oblique-map strokes, and land cover from the CEC read with Brown's bands

Status: accepted (2026-11-16); the land cover is drawn in ink over its tints by 0036. Supersedes the name Raised, and the Raised lean, strokes, form lines and ridgelines of 0017, and the strokes and southern reach of 0018; extends 0019.
Phase: P1

## Context

The owner found the Raised view flat, and asked for it to be called Oblique. The experiment in `review/experiments/raised-styles/` drew two 36 by 34 km test boxes (the Sierra de los Pilares de Teras, and the Guadalupe Mountains across the border) in 25 looks, after the oblique maps in Carl Churchill's post [Variety in hachure](https://churchillgeo.com/variety-in-hachure/) (`docs/inspiration/churchill.md`). The owner chose one: long strokes after Tau Rho Alpha's *Atlas of Oblique Maps* (USGS I-1799, 1988), stippled flats after Frank Holmes's *Estado da Guanabara* (1965, in Percy Lau's manner), the line-only parts of Charles Owens's comic-book shading in *The Panama Canal* (1928), and a classic tint of land cover. The owner also asked for the land cover as a choice in the Flat and Tilted views.

Land cover from two national sources (INEGI's land use and vegetation in Mexico, NLCD in the US) changed colour at the border, because the two class the same semi-desert ground differently. The CEC's *North American Land Cover 2020* is one classification for both countries, but it does not split pine from oak.

## Decision

- **Name.** The view called Raised in 0017 to 0019 is Oblique: in the app, the code, and its story layers, now `data/oblique/` (was `data/raised/`). Its archives were already `oblique-*.pmtiles`.
- **Projection.** Plan oblique relief as before (Jenny and Patterson, "Introducing plan oblique relief", *Cartographic Perspectives* 57, 2007), at a lean of 4 instead of 2: each point moves north 4 m per metre above the corridor's lowest ground. The DEM reaches 11 km south of each strip, so that the highest ground (about 9.6 km of shift) can still hide ground in it. A lean of 3 stays open if the larger shift proves hard to read.
- **Strokes.** The Oblique view no longer reuses Daniel Huffman's hachure strokes. `crossing.plan_oblique` traces its own, down the fall line of the DEM smoothed again over 4 cells (120 m), 140 to 320 m long, from seeds on a jittered grid 52 m apart. A seed is kept with a chance that rises with shade and slope; faces lit above 0.72 (light from the north-west, 45° up) get none, and the deepest shade (below 0.3) gets a second set of seeds 30 m apart. The grid and its jitter are fixed for the whole corridor, so strips meet and rebuilds repeat. Each stroke carries `shade` (0 to 100) and `Rand` (0 to 9); the style sets the width from `shade` and draws fewer strokes below zoom 12 by `Rand`, as the flat view's hachures do. Strokes are simplified to 5 m once shifted.
- **Stipple.** Points 95 m apart where the ground is flatter than 4° and within 40 m of the lowest ground about 1 km round, drawn as dots.
- **Line work.** Crest outlines heavier (1.6 px); rivers drawn as two ink banks with water between. Form lines and ridgelines are no longer tiled, because the strokes and crests carry the form.
- **Land cover.** The CEC's *North American Land Cover 2020* (30 m, version 2), read with height bands after Brown's biotic communities (David E. Brown, ed., *Biotic Communities: Southwestern United States and Northwestern Mexico*, 1994). The CEC decides water, towns, fields, wetland, and grass against scrub. Height decides which trees: below 1,250 m gallery forest, above it oak woodland, above 1,800 m pine, a north-facing slope counting as up to 150 m higher. CEC shrubland above the oak line on a slope of 6° or more is open oak woodland; on flatter ground (the high basin floors round Cloverdale) it stays scrub. Trees and shrubland within 150 m of a stream of order 4 or more, below the oak line, are gallery forest. Patches under 40 cells (3.6 ha) join their neighbours.
- **Land cover in every view.** The classes become polygons twice: on the ground for Flat and Tilted (`landcover.pmtiles`), and shifted and cut by the hidden ground for Oblique (`kind` `landcover` in the oblique archives). The style colours them by class, flat school-atlas tints mixed 60% over the paper. The map's Ground switch becomes Paper, Land cover, or Satellite tint; land cover works in all three views, and the satellite tint still only in Flat and Tilted. Paper stays the default.
- **Data.** `crossing.fetch_landcover` downloads the CEC's Mexico and US GeoTIFFs from their zips by byte range (four requests, 1.1 GB) into `private/cache/landcover/cec/`, and the build clips them once to the corridor.
- **Credit.** The CEC land cover is credited in the Oblique and land cover archives' attribution and on the Credits page. The style references (Churchill's post and the maps it shows), Brown, and Jenny and Patterson are credited on the Credits and How it's built pages, not on the map.

## Alternatives

- **INEGI in Mexico and NLCD in the US.** Richer classes (INEGI splits pine from oak), but the tints change at the border, and NLCD has its own seam at about 109.05° W.
- **Land cover by height alone** (the experiment's `upolu` look). Brown's bands without mapped data put woodland on the high basin floors and miss the towns, fields and water.
- **Land cover as a pre-shifted raster.** One more archive and source, colours baked in rather than in the palette, and blurred or blocky edges past zoom 12.
- **The comic look's black flames.** Polygons, about three times the vertices, and the darkest of the looks.
- **A lean of 2.** The terrain the owner wanted to stand out stays flat.

## Consequences

- The Oblique build no longer needs the fine hachure cache's strokes, only its tile grid, so it runs without QGIS. The flat view still draws Huffman's strokes.
- The Oblique view grows from 109 MB in two archives to 192 MB in three (`oblique-1.pmtiles` 51 MB, `oblique-2.pmtiles` 92 MB, `oblique-3.pmtiles` 49 MB), and `landcover.pmtiles` adds 71 MB. The stipple is the largest new part: 7.7 million dots. Both must be released together with `data/oblique/`.
- A full build takes about 9 minutes.
- The story layers move twice as far between Flat and Oblique.
- Land cover covers the same corridor as the Oblique view, not the whole story box.
- Some valley trees the rule calls gallery forest are likely mesquite bosque.
