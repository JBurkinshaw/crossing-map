// What the two Wheeler Survey sheets teach the vintage map: our own descriptions and measurements, made from the
// David Rumsey Map Collection scans (CC BY-NC-SA). No image or crop of the sheets is kept in the repository.
// Measurements: sheet 70A scanned at about 115 px per cm, sheet 83 at about 119 px per cm (from the graticule);
// sizes are on the printed sheet. Full notes: review/stage-8/wheeler/README.md.

export type Sheet = { id: string; title: string; date: string; scale: string; list: string; url: string }

// Catalogue records. The collection's search is a bot-checked page, so these are links for a person to open;
// list numbers are from the records the owner downloaded.
export const SHEETS: Sheet[] = [
  {
    id: '70A',
    title: 'Parts of Southern Colorado and Northern New Mexico, Atlas Sheet No. 70 (A)',
    date: 'issued 7 May 1877',
    scale: '1:253,440 (4 miles to the inch)',
    list: '2738.076',
    url: 'https://www.davidrumsey.com/luna/servlet/view/search?q=2738.076',
  },
  {
    id: '83',
    title: 'Parts of Eastern and South Eastern Arizona, Western and South Western New Mexico, Atlas Sheet No. 83',
    date: 'issued 18 March 1876',
    scale: '1:506,880 (8 miles to the inch)',
    list: '2738.097',
    url: 'https://www.davidrumsey.com/luna/servlet/view/search?q=2738.097',
  },
]

export type Param = 'water' | 'spotHeights' | 'landforms' | 'contrast' | 'darkInk' | 'taper' | 'paper' | 'type'
export type Learning = { topic: string; title: string; wheeler: string; ours: string; proposal: string; param?: Param; sheets: string[] }

export const LEARNINGS: Learning[] = [
  {
    topic: 'Lettering',
    title: 'Big rivers in spaced capitals',
    wheeler:
      'PURGATORY RIVER and CANADIAN RIVER are set in roman capitals about 2.2 mm high, each letter about one letter-width from the next (0.9 em). The name follows the general run of the river, not each bend, and is repeated only once or twice across the sheet. On sheet 83 the Salt and Gila names use the same spaced capitals.',
    ours: 'River names are small italics (13 px, 0.1 em spacing) on the traced river lines. Those lines follow every meander of the 1:50,000 networks, so MapLibre finds no straight enough stretch: the Bavispe shows no name at zoom 9, nor the Santa María at zoom 11.',
    proposal: 'Label the rivers from a separate, smoothed label line (Natural Earth simplified to about 3 km and rounded; a river_label layer in base.pmtiles), in roman capitals 11 to 16 px by zoom, letter-spacing 0.45 to 0.9 em. The lab does this from riverLines.ts.',
    param: 'water',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Lettering',
    title: 'Creeks and small rivers in small italic',
    wheeler:
      'Creeks, forks and cañons are in italic upper and lower case about two-thirds the river size (Chicoso Creek, Tenaja Creek, Reilly’s Cañon), close-set, along the stream.',
    ours: 'NHD creeks are labelled in italics from zoom 10; the smaller Natural Earth rivers (river_minor) carry names in the tiles but are never labelled.',
    proposal: 'Label the smaller rivers too, on the same smoothed lines, in italic 10 to 12 px from zoom 8; creek labels a size smaller and tighter.',
    param: 'water',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Lettering',
    title: 'Landform names along the landform',
    wheeler:
      'TRINIDAD MESA, RATON PLATEAU, PRIETO PLATEAU, SAN FRANCISCO RANGE, PELONCILLO RANGE, SAN SIMEON PLAINS and PUEBLO VIEJO VALLEY are set in roman capitals along the feature’s long axis, straight or gently curved, spread to fill it. The spacing comes from the feature: about 0.5 em in TRINIDAD, 1.2 em in MESA, 2.5 em in the range names and up to 4.5 em in RATON PLATEAU. Capitals are 1.9 to 2.6 mm, the largest type inside the frame.',
    ours: 'Ranges, valleys and plains are point labels: horizontal italics, 14 px, 0.15 em, wrapped onto two lines when long.',
    proposal: 'A label-line layer for named landforms (from gazetteer points and the DEM, see Data sources), lettered in spaced capitals whose spacing grows with zoom so the name always spans about 85% of the axis.',
    param: 'landforms',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Lettering',
    title: 'Heights without names',
    wheeler:
      'Unnamed high points, rim points and road summits carry only a height in feet, a small numeral about 0.9 mm high (7268, 8332, 9760). Along the Raton rim there are eight within a few miles. Named peaks get the name over the height (TRINCHERA PK, 13611).',
    ours: '199 unnamed summits in mountain_glyphs.geojson have a height but draw no text, and small named summits draw neither name nor height.',
    proposal: 'Give those glyphs the height alone, 9.5 px italic, in the units chosen; the existing glyph layer, its collision order and its spoiler filter stay as they are.',
    param: 'spotHeights',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Lettering',
    title: 'A strict type hierarchy, in few faces',
    wheeler:
      'Measured cap heights: landform and range names 1.9 to 2.6 mm; big rivers 2.2 mm; county towns and peaks 1.2 to 1.5 mm (roman, bold-ish, mixed case, or capitals for the larger towns: TRINIDAD); ranches, stations and springs about 1 mm italic (Arm’s R., Crow Cr. Sta., Chicoso Spr.); spot heights 0.9 mm. Passes are in roman capitals along the road through them (RATON PASS, MANCO BURRO PASS, RAILROAD PASS).',
    ours: 'Settlements in roman, landforms and water in italic, at 11 to 14 px: a narrower range of sizes (about 1.3 to 1) than Wheeler’s (about 2.8 to 1).',
    proposal: 'Widen the range: landform and river capitals at about 2× the spot-height size, towns at about 1.4×; passes in small capitals along the pass.',
    param: 'type',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Relief',
    title: 'Hachure contrast follows the slope',
    wheeler:
      'Ink cover runs from about 5% on gentle ground (short broken strokes in rows, almost a stipple) through 23% on an escarpment comb to 40-50% on steep mountain sides. Strokes are about 0.14 mm wide, 0.45 mm long on gentle ground and 0.65 to 0.8 mm (up to 1.6 mm) on steep ground; width barely changes, so the darkness comes from length and packing.',
    ours: 'Our strokes vary in width (0.25 to 1.3 px by slope, ±40% by shade) and opacity (by shade only), but they are fewer and longer, and the foothills and bajadas carry nearly as much ink as the crests, so the ranges lack Wheeler’s dark cores (see the Hatchet ranges at zoom 10.5).',
    proposal: 'Stretch the slope response, mostly through opacity: opacity × (1 + t·k) with k from −0.6 on gentle ground to +0.45 on steep, width × (1 + t·k) with k from −0.4 to +0.25, t a contrast setting. The real fix is in the hachure build: shorter, more numerous strokes on steep ground (Wheeler’s darkness comes from packing, not width).',
    param: 'contrast',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Relief',
    title: 'Ridges, flat tops and valley floors left white',
    wheeler:
      'Every crest and spur line is a thin white parting between the hachures of its two sides; summits are white dots inside a rosette of radial strokes; mesa and plateau tops are pure paper inside a hard rim. Valley floors are blank, so the drainage reads as a white tree.',
    ours: 'Done in the Wheeler hachure build (decision 0024, tiles-v11): strokes are cleared within one stroke length of every ridge line (ridge_network) and inside a disc at each summit (summits), and flats are left blank. Wider summit discs and ridge clearance were left for later.',
    proposal: 'In the hachure build, drop strokes within one stroke length of a ridge line (from the geomorphons), and add a short white gap at summits.',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Relief',
    title: 'Escarpments as a single comb',
    wheeler:
      'The Raton and Trinidad mesa rims are one row of short heavy strokes, perpendicular to the rim, about 0.5 to 1 mm long and 0.25 mm apart, thick at the top and tapering downslope. The rim itself is never drawn as a line; it is the top of the comb.',
    ours: 'Escarpments get the same strokes as any steep slope, so a mesa edge reads as a smudge at zoom 10 to 11.',
    proposal: 'A "rim" stroke class in the hachure build: where slope breaks from under 6° to over 25° within 100 m, draw one row of wedge strokes from the break, spaced 3 px, and skip the ordinary strokes there.',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Relief',
    title: 'Ink, not sepia',
    wheeler: 'The hachures print in a brown-black (#110600 to #221802 in the darkest strokes); all line work and type share the one ink.',
    ours: 'Hachures in a mid sepia (#6e5443), lighter than the type ink (#2b2118).',
    proposal: 'Try the hachures in the type ink, lifted a little (#2e2010), with the contrast setting carrying the gentle slopes.',
    param: 'darkInk',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Drainage',
    title: 'Line weight by rank, dry washes dotted',
    wheeler:
      'Main rivers are a heavier wavy line with a stippled bank; tributaries thin to a hairline toward their heads; dry streams and washes are fine dotted lines. Canyons are drawn by their walls (a comb each side) with the stream between.',
    ours: 'Rivers 0.9 to 2 px, minor rivers 0.5 to 1.2 px, every one at the same weight in its class; intermittent NHD creeks dashed 3-2.',
    proposal: 'Weight rivers by Natural Earth scalerank (1.3 to 3.6 px for the main stems), creeks as hairlines, intermittent creeks a fine dotted 0.5-2 pattern. A true taper along each line needs Strahler order on the river lines (the Oblique view’s streams already carry it).',
    param: 'taper',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Paper',
    title: 'A light under-tint inside a whiter margin',
    wheeler:
      'Sheet 70A: margin #f7f6e3, the map’s "gray cream" under-tint #f9eecf. Sheet 83: margin #f6f3de, "light gray" under-tint #efead4. The tint stops at the neatline, so the map sits as a panel on the sheet.',
    ours: 'Caliche paper #e4ddcc below zoom 10, near-white #f1ede2 above; a shade darker on the Mexico side.',
    proposal: 'Try a lighter, warmer cream (or the grey of sheet 83) below zoom 10, keeping Mexico a shade darker. Halo colours follow the paper.',
    param: 'paper',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Roads',
    title: 'Roads with their mileages',
    wheeler:
      'Wagon roads are a fine single line; trails dashed; railroads a line with the name in capitals along it (DENVER & RIO GRANDE R.R.). Road names are italic along the road (Dry Cimarron Road, Simpson’s to Trinidad), with the miles between stations written on the line (13.5 m., 27.5 m.).',
    ours: 'Today’s Natural Earth roads, dashed, unnamed; railroads with ties.',
    proposal: 'Replace the modern road layer with historic roads of the story’s years (see the Roads plan in the packet), named in italic along the line, with the book’s distances where it gives them.',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Places',
    title: 'Water sources and stations are first-class places',
    wheeler: 'Springs, water holes, ciénegas, tanks and water pockets are named (Water Holes, Whitlock’s Ciénega, Water Pocket); so are stage and forage stations, ranches and ruins.',
    ours: 'Springs appear only when the book names them.',
    proposal: 'A small, quiet layer of GNIS springs and GeoNames aguajes and tanques in the corridor, italic, from zoom 11.',
    sheets: ['70A', '83'],
  },
  {
    topic: 'Frame',
    title: 'Graticule and frame',
    wheeler:
      'A thin neatline inside a heavy thin-thick rule; 15′ graticule lines across the map, labelled in the margin (30′, 15′, 105°); title in capitals with small "of the"; imprint and draughtsmen in small italic below.',
    ours: 'No graticule; a cartouche panel in the corner.',
    proposal: 'An optional 15′ graticule in faint ink at zoom 8 and up; it gives the plain country the measured look of the survey sheets.',
    sheets: ['70A', '83'],
  },
]
