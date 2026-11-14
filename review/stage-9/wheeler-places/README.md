# Wheeler places: water and stations, graticule and frame (stage 9, test area)

Two cards from the Wheeler study (`review/stage-8/wheeler/README.md`, findings 13, 15 and 16), tried in the lab's test area (109.6 to 108.4° W, 30.5 to 31.6° N):

1. **Water sources and stations are first-class places.** A quiet italic layer of springs, ranches and stations from zoom 11, with a small mark per kind.
2. **Graticule and frame.** A 15′ graticule in faint ink from zoom 8, a Wheeler frame round the lab map (thin-thick-thin rule, a margin band with the graticule labels, a neatline), and a lab copy of the site's cartouche with a thin neatline inside a thin-thick rule.

Nothing on the site's main map, in `site/src/map/`, `site/src/styles/` or `data/` has changed.

## How to see it

1. `cd site && npm run dev -- --port 5193`, then open `/lab.html#wheeler`.
2. Press **Test area: bootheel and Bavispe** under "Go to".
3. Under **Test area (stage 9)**:
   - **Water and stations (test area)** shows the places layer (zoom 11 and up).
   - **Graticule and frame** shows the graticule, the frame, its margin labels and the cartouche copy.
   - **Graticule labels on the lines** adds MapLibre's own labels along the lines (the alternative to the margin labels; see below).
   - **Read up to** is a reading-progress slider (not started, every episode id 1-01 to 4-14, the end). It filters the places layer on `first_seen`.
4. "All Wheeler" turns all of these on (except the line labels). "All as today" turns them off.

To rebuild the data (local caches only, no network):

```
uv run --project pipeline python -m crossing.water_places
uv run --project pipeline python -m crossing.graticule
```

Screenshots: with the dev server running, `cd tools && node wheeler-places-shots.mjs http://localhost:5193/`. This writes to `private/review/stage-9/wheeler-places/`.

## What changed

| File | What |
| --- | --- |
| `pipeline/src/crossing/water_places.py` | New. Builds `site/public/lab/wheeler/water-places.geojson` (16 kB). |
| `pipeline/src/crossing/graticule.py` | New. Builds `site/public/lab/wheeler/graticule.geojson` (15 kB, 74 lines over the story box). |
| `site/src/lab/wheeler/subset/places.ts` | New. Sources, layers, the marks drawn in code, and the reading positions. |
| `site/src/lab/wheeler/subset/frame.ts` | New. The frame overlay, the margin labels and the cartouche copy. |
| `site/src/lab/wheeler/subset/frame.css` | New. The frame and cartouche CSS, written to move into the site. |
| `site/src/lab/wheeler/wheelerStyle.ts` | Shared. `Params.places`, the presets, and one `addPlaces(...)` call round the returned style. |
| `site/src/lab/wheeler/WheelerLab.tsx` | Shared. The test-area place button, one fieldset of controls, and two calls when the map is made (`addPlaceMarks`, `addFrame`). |
| `tools/wheeler-places-shots.mjs` | New. The screenshot script. |

## 1. Water and stations

### Sources and rules

- **GNIS Domestic Names, AZ and NM** (public domain). Feature class `Spring`. Also `Locale` and `Populated Place` records whose name contains Ranch, Rancho, Station, Stage stand or Siding. One record is excluded by id: 924821 "Humble Oil and Refining Number 1", an oil test well filed as a Spring.
- **GeoNames MX** (CC BY 4.0). Codes from `featureCodes_en.txt`:
  - By code, whatever the name:
    - springs and water holes: `SPNG`, `SPNS`, `SPNT`, `SPNGI`, `WTRH`, `WTRHS`
    - wells: `WLL`, `WLLS`, `WLLQ`
    - ranches and farms: `RNCH`, `FRM`, `FRMS`, `FRMT`
    - railway stations: `RSTN`, `RSTP`
  - Only when the name begins with Aguaje, Ojo (both spring), Pozo (well), Tanque or Represo (both tank): reservoirs, tanks and ponds (`RSV`, `RSVI`, `RSVT`, `TNKD`, `PND`, `PNDI`, `PNDS`, `PNDSI`), and wells and water holes too.
  - Populated places and localities (`PPL`, `PPLQ`, `PPLL`, `PPLX`, `LCTY`) named "Rancho ...", as ranches.
  - `STNB` is left out. In GeoNames it means "scientific research base", not a stage station, and there are none in the test area.
- **`data/places.geojson`**: the book's places of kind `spring` or `ranch` in the test area. They keep the book's spelling, `first_seen`, `certainty`, `source` and `source_licence`.
- Every other point has `first_seen` 1-01 and `certainty` located (the gazetteer's coordinate).
- A gazetteer point within 1 km of any book point place (of any kind) is dropped as a duplicate. Two gazetteer points with the same kind and folded name within 1 km are kept once. The script prints every drop.
- Properties: `id`, `name`, `kind` (spring, well, tank, ranch, station), `source`, `source_licence`, `certainty`, `first_seen`, and `code` (the gazetteer class or code, or `book`, for review).

### Counts (test area)

| Kind | Source | From | Count |
| --- | --- | --- | --- |
| spring | gnis | gazetteer (`Spring`) | 22 |
| spring | gnis | book (Hog Canyon Spring, 1-04) | 1 |
| spring | geonames | `SPNG` 2 (El Ojito, Ojo Peñuelas); `RSV` "Aguaje ..." 1 (Aguaje las Vacas) | 3 |
| ranch | geonames | `RNCH` 10; `PPL` or `PPLQ` named Rancho 19 | 29 |
| station | geonames | `RSTN` | 5 |
| well, tank | | none in the test area | 0 |
| **Total** | | | **60** |

By source: GNIS 23 (one of them the book's), GeoNames 37. By kind: 26 springs, 29 ranches, 5 stations.

The script dropped 3 points:
- GNIS Hog Canyon Spring: 0 km from the book's Hog Canyon Spring.
- GeoNames `RSTN` Fronteras: 0.17 km from the book's Fronteras.
- GeoNames `RSTN` Esqueda: 0.48 km from the book's Esqueda.

These were not taken, by the card's rules:
- GeoNames `RSV`/`RSVI` in the test area: 262, of which 98 are "Bordo ..." (modern earth dams) and most of the rest bare names (El Alamito, La Víbora).
- GNIS `Reservoir` "... Tank": 130 stock tanks.
- GeoNames populated places named for water: Ojo de Agua, Aguaje del Mariscal, Ojo de Peñuelas.
- GeoNames airstrips named Rancho ... (`AIRF`, `AIRQ`).

The test area has no GNIS `Locale` records at all, and no GNIS populated place whose name says ranch or station. So GNIS adds no ranches or stations here. Possible candidates the owner may want by hand: Bernardino (historical), Alamo Hueco, Cazador, Deer Creek Wells, High Lonesome Wells.

### Style

- One symbol layer, `wp-place`, from zoom 11. It sits under the base's first symbol layer, so summit, river and contour labels win collisions.
- The type follows the shared scale: IM Fell italic, 10 px at zoom 11 rising to 12 px at zoom 13. Text is in the `ink` token at 0.72 opacity with a paper halo. Variable anchors (left, right, top, bottom). The name is optional, so the mark stays when its name collides.
- The marks, after Wheeler, are 8 px images drawn on an `OffscreenCanvas` at runtime (no sprite art):
  - spring: a ring
  - well: a dot
  - tank: a ringed dot
  - ranch: a small solid square
  - station: an open square

  Water marks use the `water` token. Ranch and station marks use `ink`.
- The marks are added on every `style.load` and also on `styleimagemissing`. Adding them only on `styleimagemissing` left tiles that were laid out before the image arrived with names but no marks (seen at zoom 11, and fixed).
- Progress filter: `['<=', ['to-string', ['get', 'first_seen']], reached]`, the site's string rule (`site/src/spoiler/filter.ts`). The proof is `desktop-filter-1-03.jpg` (Hog Canyon Spring hidden) against `desktop-filter-1-04.jpg` (shown).

### Credit lines

- Springs, ranches and stations: U.S. Geological Survey, Geographic Names Information System (GNIS), public domain.
- GeoNames (geonames.org), CC BY 4.0. Credit: "Contains data from GeoNames, CC BY 4.0".
- The source's attribution in the lab reads "Springs and ranches: USGS GNIS (public domain), GeoNames (CC BY 4.0)".

## 2. Graticule

- 15′ lines over the whole story box: 37 meridians and 37 parallels, two vertices each. Web Mercator draws them straight.
- Properties: `axis`, `deg`, `label` ("31°15′ N"), `short` (Wheeler's margin form: "15′", or "31°" on a whole degree), `rank` (1 a degree, 2 a half, 3 a quarter) and `first_seen` 1-01.
- Drawn from zoom 8 in `ink`, opacity 0.16 (zoom 8) to 0.24 (zoom 12). Whole degrees are 0.8 to 1.1 px wide and the others 0.5 to 0.7 px. The lines sit under all type.

### Labels: what works and what does not

- **Margin labels in the frame (works; the default).** MapLibre cannot anchor a label to the viewport edge, so `frame.ts` does it in HTML. On every `move`, each 15′ meridian and parallel in view is projected once (`map.project`). Its short label is centred in the margin band where the line meets the edge: top and bottom for meridians, left and right for parallels, as on sheet 70A ("30′", "45′", "109°"). The labels are exact while the map is flat. Tilted, the lines converge and one projection is wrong, so the labels hide. Labels that would land in a corner of the band are skipped. At zoom 12 the view can be narrower than 15′, so a side may have no label (see `desktop-z12.jpg`).
- **`symbol-placement: line` (does not work well).** This is the "Graticule labels on the lines" option, with `symbol-spacing` 700. MapLibre places the labels anywhere along the line, not near the screen edge, and turns meridian labels to read sideways. As the lowest-priority layer, most labels lose collisions. At zoom 10 only two of about eight lines got a label (`desktop-z10-line-labels.jpg`). Neither `line-center` nor `symbol-spacing` can find the viewport edge. Short GeoJSON stubs near the box's edges do not help either, because they are at the edges of the story box, not of the screen.

## 3. Frame

Sheet 70A's lower-left corner was measured on the scan (about 115 px/cm; study only, nothing traced or kept). From the outside in:

| Part | Width |
| --- | --- |
| thin rule | 0.2 mm |
| gap | 0.4 mm |
| heavy rule | 1.3 mm |
| gap | 0.4 mm |
| thin rule | 0.2 mm |
| margin band, holding the graticule labels | about 5 mm |
| thin neatline | 0.2 mm |

At the sheet's printed scale (about zoom 11 on a 96 dpi screen) that is 1, 2, 5, 2, 1, 19 and 1 px.

The lab uses 1, 2, 4, 2, 1 px, then a 20 px band and a 1 px neatline: 31 px from the container edge to the neatline. On phones (max-width 720 px) it uses 1, 1, 3, 1, 1 px and a 15 px band. The margin is `#f7f4ea`: the site's paper above zoom 10 (`#f1ede2`) a step lighter, because Wheeler's margin is lighter than his map tint (70A: `#f7f6e3` against `#f9eecf`).

### How it is drawn

`frame.ts` appends a `.wp-frame` overlay (absolute, `inset: 0`, `pointer-events: none`, `z-index: 1`) to the MapLibre container. Stacked inset box shadows draw the rules, so the map keeps its size. The overlay shows while the container has the class `wp-framed`.

MapLibre's top-left, bottom-left and bottom-right controls move inside the neatline. The frame and cartouche set the page's serif (`'IM Fell English', 'Iowan Old Style', Georgia, serif`), because the MapLibre container sets its own sans-serif.

### Cartouche copy

`.wp-cartouche` is the site's `.cartouche` (map.css) with one change: its two thin rules (`border` plus `outline` at 3 px offset) become a thin neatline inside a thin-thick rule. From the inside out:

1. the 1 px border (the neatline)
2. a 3 px gap
3. a 3 px heavy rule
4. a 1.5 px gap
5. a 1 px thin rule

The rule reaches 8.5 px past the border, where the outline reached 4 px. On phones it is 2, 2, 1 and 1 px.

### Moving it into the site (for the lead)

**The cartouche.** In `site/src/styles/map.css`, in `.cartouche`, replace

```css
  border: 1px solid var(--ink);
  outline: 1px solid var(--ink);
  outline-offset: 3px;
```

with

```css
  border: 1px solid var(--ink);
  box-shadow:
    0 0 0 3px var(--paper),
    0 0 0 6px var(--ink),
    0 0 0 7.5px var(--paper),
    0 0 0 8.5px var(--ink);
```

Then add 5 px to `right` and `bottom` (12 to 17 px, 28 to 33 px), so the wider rule stays clear of the screen edge and the attribution button.

In the phone block, replace `outline-offset: 2px;` with:

```css
box-shadow: 0 0 0 2px var(--paper), 0 0 0 4px var(--ink), 0 0 0 5px var(--paper), 0 0 0 6px var(--ink);
```

Do the same for `.map-controls` and the inset if they should match: they share the double rule today.

**The map frame**, if wanted on the site:

1. Copy section A of `frame.css` (the `.wp-framed` variables, `.wp-frame`, `.wp-edge` and the control margins) into map.css under site names (`.map-framed`, `.map-frame`).
2. Move `addFrame` from `frame.ts` into `site/src/map/` without the cartouche part. The site's cartouche stays in `MapView.tsx`.
3. Lift the cartouche's `right` and `bottom` by the frame inset (31 px desktop, 23 px phone).

The frame takes 31 px from each side of a full-screen map. On a phone that is 46 px of a 390 px width.

## Screenshots

All are in `private/review/stage-9/wheeler-places/`. All Wheeler parameters are on. The desktop map is 928 × 642 px. The phone viewport is 390 × 844 at 3×.

| Shot | View |
| --- | --- |
| `desktop-z8.jpg`, `phone-z8.jpg` | zoom 8, test area centre (−109.0, 31.05) |
| `desktop-z10.jpg`, `phone-z10.jpg` | zoom 10, same centre |
| `desktop-z11.jpg`, `phone-z11.jpg` | zoom 11, Guadalupe Mountains springs (−109.05, 31.44) |
| `desktop-z12.jpg`, `phone-z12.jpg` | zoom 12, the same springs (−109.06, 31.46) |
| `desktop-z11-sonora.jpg`, `phone-z11-sonora.jpg` | zoom 11, the ranch cluster south of the Llanos de Carretas (−108.66, 30.88) |
| `desktop-filter-1-03.jpg`, `desktop-filter-1-04.jpg` | the reading filter at Hog Canyon Spring |
| `desktop-z8-line-labels.jpg`, `desktop-z10-line-labels.jpg` | the `symbol-placement: line` labels |
| `desktop-page.jpg` | the whole lab page with the controls |

## What looks crowded

- **The Guadalupe Mountains springs**, around 109.05° W, 31.45° N: 14 springs in about 8 × 12 km.
  - At zoom 11 they all fit, but they read as a field of italic names over the hachures.
  - Cedar Spring, Ledar Spring and Ledar Seep sit within 300 m of each other. Their marks overlap, and Ledar Spring's name is dropped at zoom 11 and 12.
  - Little Bunk Robinson Spring breaks onto two lines.
  - A start zoom of 12 for unnamed-in-book springs in clusters, or a thinning rule (one name per 1 km), would help.
- **The Sonoran ranches near 108.55° W, 30.9° N.** Rancho San José and Rancho el Uno Más are 1.9 km apart, and the second's name falls under the first's mark at zoom 11. GeoNames `RNCH` points are rounded to whole minutes (−108.98333), so they can sit up to about 900 m from the ranch.
- **The cartouche** covers about a fifth of the lab map's lower right. At zoom 11 it hides Spring of Contention. On the site this is the same today.
- **On phones**, names near the map edge run under the frame band (Maverick Spring, Indian Spring at zoom 11), because the frame overlays the map. Overlaying is what keeps the map's size unchanged.
- **The graticule** does not crowd. At zoom 8 to 10 the lines read faintly under the type. The margin labels give the plain country the measured look the study wanted.

## What does not work yet

- No wells or tanks: the test area has none under the card's rules (see above).
- No GNIS ranches or stations: the test area has no Locale records.
- Margin labels hide in the Tilted view.
- Graticule labels on the lines are poor (above).
- The 15′ line count is fixed at 15′ on every zoom. At zoom 8 on a phone the spacing is about 90 px, which is fine. At zoom 6 to 7 it would want 30′ or 1°, but the graticule starts at 8.
- The lab copy of the cartouche has no layer key, which the site's has.
- The progress slider offers ids 1-01 to 4-14 for every part, including ids a short part does not have. It is a lab control, not the site's progress picker.

## Open questions for the owner

1. **Which tanks?** GNIS has 130 named stock tanks in the test area, and GeoNames 98 "Bordo" earth dams and about 160 bare-named reservoirs. Wheeler names tanks, but most of these are 20th-century. Leave them all out, include GNIS "... Tank" from zoom 12, or include only those near a journey?
2. **Modern ranches.** GeoNames gives no date: "Rancho Internacional" or "Rancho Bill" may postdate 1940. Keep every ranch as context, or only those on a period map (the 1930s AMS or USGS sheets in the roads plan)?
3. **Railway stations.** The Nacozari line's stations (Cabullona, Cuchuta, Estación Elías Calles, Turicachi) are period features. Should they be "station" here (Wheeler's stage stations), or belong to the railways card?
4. **Margin labels.** Wheeler's short form ("15′", "109°"), as now, or the full form ("31°15′ N") at whole degrees? Should the site's map get the frame at all, given the 31 px it takes from each side, or only the cartouche rule?
5. **The cartouche rule** on the switches box and the inset as well, so the three framed boxes match?
