import type { ExpressionSpecification, FilterSpecification, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { dataBase } from '../../../map/setup'
import { fonts, palette } from '../../../map/tokens'
import { landforms as demoLandforms } from '../landforms'

// The Wheeler card "A strict type hierarchy, in few faces" (review/stage-9/wheeler-type/README.md), for the test
// area only (109.6 to 108.4° W, 30.5 to 31.6° N). Three faces of IM Fell (roman, italic, small capitals) and one ink
// set every name the map draws there, on the shared scale of the Wheeler cards. Sizes are at zoom 11, where the
// sheets were measured; each grows a little with zoom (zoomed()).

export const TEST_AREA: [number, number, number, number] = [-109.6, 30.5, -108.4, 31.6]

// The small capitals of IM Fell English, built into the map's glyphs beside the roman and italic
// (tiles/build_glyphs.sh). The site's tokens do not name it yet.
const SMALL_CAPS = 'IMFeENsc28P'

// The shared scale: the spot height (9.5 px italic) is the unit. Landform and big-river names are about twice it,
// towns about 1.4 times, the small italic of ranches and springs and the small capitals of passes about 1.05.
const SIZE = { landform: 19, town: 13.5, quiet: 10, pass: 10 }
// Quiet names (ranches, stations, springs, draws) in the same ink, lighter.
const QUIET_OPACITY = 0.7

// Sizes at zoom 9, 11 and 13 as a share of the zoom 11 size: type grows less than the ground does, so names
// spaced along a landform at zoom 11 still span it at 13.
const GROWTH: [number, number][] = [
  [9, 0.85],
  [11, 1],
  [13, 1.15],
]
const zoomed = (size: number): ExpressionSpecification => ['interpolate', ['linear'], ['zoom'], ...GROWTH.flatMap(([z, k]) => [z, size * k])]
// The same curve at one zoom, for expressions that need the size as a number.
function growth(z: number): number {
  const i = GROWTH.findIndex(([gz]) => gz >= z)
  if (i === -1) return GROWTH[GROWTH.length - 1][1]
  if (i === 0) return GROWTH[0][1]
  const [[z0, k0], [z1, k1]] = [GROWTH[i - 1], GROWTH[i]]
  return k0 + ((k1 - k0) * (z - z0)) / (z1 - z0)
}

// Landform names fill about 80% of their line (Wheeler spreads TRINIDAD MESA or RATON PLATEAU over the whole
// feature). A capital of IM Fell roman is taken as 0.75 em wide; the letter gap is what is left over, between 0.1
// and 4 em. Where even 0.1 em is too long for the line at this zoom, MapLibre drops the name, which is how the
// smaller landforms wait for the closer zooms.
const FILL = 0.8
const CAP_EM = 0.75
// MapLibre places a line label within one tile's piece of the line (a 512 px tile and its buffer), so a name
// longer than about this many pixels is never drawn, however long the line: past it the letters close up.
const MAX_PX = 460
const SPACING_ZOOMS = [8, 9, 10, 11, 12, 13]

function landformSpacing(size: number): ExpressionSpecification {
  const chars: ExpressionSpecification = ['length', ['get', 'name']]
  // MapLibre's zoom 0 is one 512 px tile, so metres per pixel at zoom z is mpp0 / 2 / 2^z (mpp0 is for 256 px tiles).
  const roomEm = (z: number): ExpressionSpecification => [
    '/',
    ['min', MAX_PX, ['*', FILL, ['/', ['get', 'len_m'], ['/', ['get', 'mpp0'], 2 * 2 ** z]]]],
    size * growth(z),
  ]
  const at = (z: number): ExpressionSpecification => [
    'max',
    0.1,
    ['min', 4, ['/', ['-', roomEm(z), ['*', CAP_EM, chars]], ['max', 1, ['-', chars, 1]]]],
  ]
  return ['interpolate', ['linear'], ['zoom'], ...SPACING_ZOOMS.flatMap((z) => [z, at(z)])] as ExpressionSpecification
}

const labBase = new URL(`${import.meta.env.BASE_URL}lab/wheeler/`, window.location.origin).href
const [W, S, E, N] = TEST_AREA
const area: GeoJSON.Polygon = {
  type: 'Polygon',
  coordinates: [
    [
      [W, S],
      [E, S],
      [E, N],
      [W, N],
      [W, S],
    ],
  ],
}
const inArea: ExpressionSpecification = ['within', area]

type Layer = LayerSpecification & { filter?: FilterSpecification; layout?: Record<string, unknown> }

// Keep a base layer's own filter and add one more clause.
const andFilter = (layer: Layer, clause: ExpressionSpecification): Layer =>
  ({ ...layer, filter: (layer.filter ? ['all', layer.filter, clause] : clause) as FilterSpecification }) as Layer

// The lab's demonstration landform lines that reach into the test area: this card draws its own there.
const demoInArea = demoLandforms.features
  .filter((f) => f.geometry.coordinates.some(([x, y]) => x >= W && x <= E && y >= S && y <= N))
  .map((f) => f.properties.name)

function typeLayers(halo: string): LayerSpecification[] {
  const ink = palette.ink
  const paint = { 'text-color': ink, 'text-halo-color': halo, 'text-halo-width': 1.2 }
  const quietPaint = { ...paint, 'text-opacity': QUIET_OPACITY }
  return [
    // Ranches, stations, springs and crossings: a small dot and quiet italic.
    {
      id: 'type-quiet-dot',
      type: 'circle',
      source: 'type-places',
      filter: ['all', inArea, ['in', ['get', 'kind'], ['literal', ['ranch', 'locale', 'spring', 'crossing', 'ruin', 'military']]]],
      paint: { 'circle-radius': 1.8, 'circle-color': ink, 'circle-opacity': QUIET_OPACITY },
    },
    {
      id: 'type-quiet',
      type: 'symbol',
      source: 'type-places',
      filter: ['all', inArea, ['in', ['get', 'kind'], ['literal', ['ranch', 'locale', 'spring', 'crossing', 'ruin', 'military']]]],
      layout: {
        'text-field': ['get', 'name'],
        'text-font': [fonts.italic],
        'text-size': zoomed(SIZE.quiet),
        'text-anchor': 'left',
        'text-offset': [0.5, 0],
        'text-optional': true,
      },
      paint: quietPaint,
    },
    // Draws and canyons, which GNIS files as valleys: small italic along the line, like the creeks.
    {
      id: 'type-landform-minor',
      type: 'symbol',
      source: 'type-landforms',
      filter: ['==', ['get', 'tier'], 'minor'],
      layout: {
        'symbol-placement': 'line-center',
        'text-field': ['get', 'name'],
        'text-font': [fonts.italic],
        'text-size': zoomed(SIZE.quiet),
        'text-letter-spacing': 0.05,
        'text-max-angle': 30,
      },
      paint: quietPaint,
    },
    // Passes: small capitals along the way over (the base map's road where one crosses, else across the saddle).
    {
      id: 'type-pass',
      type: 'symbol',
      source: 'type-passes',
      minzoom: 10,
      layout: {
        'symbol-placement': 'line-center',
        'text-field': ['get', 'name'],
        'text-font': [SMALL_CAPS],
        'text-size': zoomed(SIZE.pass),
        'text-letter-spacing': 0.08,
        'text-max-angle': 30,
        'text-keep-upright': true,
      },
      paint,
    },
    // Big rivers: spaced roman capitals, the size of the landform names, along the river's general run.
    {
      id: 'type-river',
      type: 'symbol',
      source: 'type-rivers',
      layout: {
        'symbol-placement': 'line',
        'text-field': ['upcase', ['get', 'name']],
        'text-font': [fonts.roman],
        'text-size': zoomed(SIZE.landform),
        'text-letter-spacing': 0.6,
        'text-max-angle': 30,
        'symbol-spacing': 300,
      },
      paint,
    },
    // Landforms: spaced roman capitals filling the line.
    {
      id: 'type-landform',
      type: 'symbol',
      source: 'type-landforms',
      filter: ['==', ['get', 'tier'], 'major'],
      layout: {
        'symbol-placement': 'line-center',
        'text-field': ['upcase', ['get', 'name']],
        'text-font': [fonts.roman],
        'text-size': zoomed(SIZE.landform),
        'text-letter-spacing': landformSpacing(SIZE.landform),
        'text-max-angle': 45,
        'text-keep-upright': true,
        'text-padding': 4,
      },
      paint,
    },
    // Towns: a dot and roman upper and lower case at 1.4 times the unit; the large towns (those places.geojson
    // marks as cities: Agua Prieta and Douglas here) in capitals, a little spaced.
    {
      id: 'type-town-dot',
      type: 'circle',
      source: 'type-places',
      filter: ['all', inArea, ['in', ['get', 'kind'], ['literal', ['town', 'city']]]],
      paint: { 'circle-radius': ['match', ['get', 'kind'], 'city', 3, 2.2], 'circle-color': ink },
    },
    {
      id: 'type-town',
      type: 'symbol',
      source: 'type-places',
      filter: ['all', inArea, ['in', ['get', 'kind'], ['literal', ['town', 'city']]]],
      layout: {
        'text-field': ['case', ['==', ['get', 'kind'], 'city'], ['upcase', ['get', 'name']], ['get', 'name']],
        'text-font': [fonts.roman],
        'text-size': zoomed(SIZE.town),
        'text-letter-spacing': ['case', ['==', ['get', 'kind'], 'city'], 0.08, 0.02],
        'text-anchor': 'left',
        'text-offset': [0.55, 0],
        'text-variable-anchor': ['left', 'right', 'top', 'bottom'],
        'text-optional': true,
      },
      paint,
    },
  ]
}

// The style with the card applied: the base map's big-river labels, summit glyph names of passes and the lab's
// demonstration landform lines give way inside the test area, and the card's own layers go on top of the style.
// MapLibre places symbols from the top layer down, so the hierarchy's names are placed before every other label
// (typeLayers() lists them bottom to top: towns win, then landforms and rivers, then passes and quiet names).
export function addTypeHierarchy(style: StyleSpecification, halo: string): StyleSpecification {
  const notInArea: ExpressionSpecification = ['!', inArea]
  const pass: ExpressionSpecification = ['==', ['get', 'landform'], 'pass']
  let layers = (style.layers as Layer[]).flatMap((l): Layer[] => {
    if (l.id === 'river-label' || l.id === 'wheeler-river-label' || l.id === 'pass-label') return [andFilter(l, notInArea)]
    if (l.id === 'wheeler-landform-label') return [andFilter(l, ['!', ['in', ['get', 'name'], ['literal', demoInArea]]])]
    if (l.id === 'mountain-glyph') {
      // Passes in the test area keep their glyph but lose its italic name, which type-pass sets instead.
      const passGlyph = { ...l, id: 'type-pass-glyph', filter: ['all', ...(l.filter ? [l.filter] : []), pass, inArea], layout: { ...l.layout, 'text-field': '' } } as Layer
      return [andFilter(l, ['!', ['all', pass, inArea]]), passGlyph]
    }
    return [l]
  }) as LayerSpecification[]
  layers = [...layers, ...typeLayers(halo)]
  return {
    ...style,
    sources: {
      ...style.sources,
      'type-landforms': { type: 'geojson', data: `${labBase}type-landforms.geojson` },
      'type-rivers': { type: 'geojson', data: `${labBase}type-rivers.geojson` },
      'type-passes': { type: 'geojson', data: `${labBase}type-passes.geojson` },
      'type-places': { type: 'geojson', data: `${dataBase}places.geojson` },
    },
    layers,
  }
}
