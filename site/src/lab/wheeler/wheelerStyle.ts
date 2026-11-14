import type { ExpressionSpecification, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { literaryStyle } from '../../map/style'
import { fonts } from '../../map/tokens'
import { landforms } from './landforms'
import { riverLines } from './riverLines'

// The Wheeler study's parameters (review/stage-8/wheeler/README.md). Each one, at its "today" value, leaves the
// classic style exactly as the site draws it, so the lab can show the map before and after one change at a time.
export type Paper = 'today' | 'cream' | 'grey'
export type Params = {
  // Major rivers in spaced roman capitals along the line, the smaller rivers and creeks in small italic.
  water: boolean
  // The height alone, as a small numeral, on summits the map leaves unlabelled.
  spotHeights: boolean
  // Range, mesa, valley and plain names set along the landform's long axis, in spaced capitals.
  landforms: boolean
  // 0: today's hachures; 1: Wheeler's range, heavy and dark on steep ground, faint and fine on gentle ground.
  contrast: number
  // Hachures in Wheeler's brown-black instead of today's sepia.
  darkInk: boolean
  // Rivers wider the more important they are, creeks hairlines, intermittent streams dotted.
  taper: boolean
  paper: Paper
  tilted: boolean
}

export const TODAY: Params = { water: false, spotHeights: false, landforms: false, contrast: 0, darkInk: false, taper: false, paper: 'today', tilted: false }
export const WHEELER: Params = { water: true, spotHeights: true, landforms: true, contrast: 1, darkInk: true, taper: true, paper: 'cream', tilted: false }

// The two papers measured on the sheets (median of the blank ground inside the neatline, review README): sheet 70A's
// cream under-tint and sheet 83's light grey one, each a little darkened so the sepia hachures still read on screen.
// `low` is the paper below zoom 10 (under the Imhof tint), `high` the near-white paper the relief draws from 10.
const PAPERS: Record<Exclude<Paper, 'today'>, { low: string; mexico: string; high: [string, string]; halo: string }> = {
  cream: { low: '#efe5c8', mexico: '#e6d9b9', high: ['#f8f0d8', '#f4ead0'], halo: '#f6eed6' },
  grey: { low: '#e9e5d2', mexico: '#dfd9c4', high: ['#f4f1e2', '#efebdb'], halo: '#f2efe0' },
}
// Wheeler's darkest ink, measured at #110600 to #221802 in the dense hachures, lifted a little for the screen.
const WHEELER_INK = '#2e2010'

const tilesBase = new URL(`${import.meta.env.BASE_URL}tiles/`, window.location.origin).href
const fontsBase = new URL(`${import.meta.env.BASE_URL}fonts/`, window.location.origin).href
const dataBase = new URL(`${import.meta.env.BASE_URL}data/`, window.location.origin).href

type Layer = LayerSpecification & { paint?: Record<string, unknown>; layout?: Record<string, unknown>; 'source-layer'?: string }

// Each output of a zoom curve (['interpolate', ..., ['zoom'], z, out, ...]) passed through f: a zoom expression
// can only sit at the top of a property, so a factor has to go inside each stop.
function perStop(value: unknown, f: (out: unknown) => unknown): unknown {
  const v = value as unknown[]
  if (!Array.isArray(v) || v[0] !== 'interpolate' || JSON.stringify(v[2]) !== '["zoom"]') return f(value)
  return [...v.slice(0, 3), ...v.slice(3).map((x, i) => (i % 2 ? f(x) : x))]
}

const lerp = (slope: [number, number], gentle: number, steep: number): ExpressionSpecification =>
  ['interpolate', ['linear'], ['get', 'Slope'], slope[0], gentle, slope[1], steep]

// Wheeler's hachures run from a faint broken stipple on gentle ground (about 5% ink cover) to a near-solid mass
// on the steepest slopes (40-50%); today's strokes vary much less. At contrast t the stroke width and opacity are
// scaled by 1 + t * k, with k from -0.4 (gentle) to +0.25 (steep) for width and -0.6 to +0.45 for opacity. Width
// grows only a little: Wheeler's strokes keep one width and darken by packing, and ours are fewer and longer, so
// wide steep strokes read as scattered sticks.
function hachure(layer: Layer, p: Params): Layer {
  if (!layer.id.startsWith('hachure-') && !layer.id.startsWith('raised-stroke')) return layer
  const slope: [number, number] = layer['source-layer'] === 'coarse' ? [5, 25] : [10, 40]
  const t = p.contrast
  const paint: Record<string, unknown> = { ...layer.paint }
  if (t > 0) {
    const width: ExpressionSpecification = ['+', 1, ['*', t, lerp(slope, -0.4, 0.25)]]
    const opacity: ExpressionSpecification = ['+', 1, ['*', t, lerp(slope, -0.6, 0.45)]]
    paint['line-width'] = perStop(paint['line-width'], (out) => ['*', out, width])
    paint['line-opacity'] = perStop(paint['line-opacity'], (out) => ['min', 1, ['*', out, opacity]])
  }
  if (p.darkInk) paint['line-color'] = WHEELER_INK
  return { ...layer, paint } as Layer
}

// Wheeler sets a river's name in roman capitals spaced about one letter apart (PURGATORY RIVER, CANADIAN RIVER,
// about 2.2 mm high at 1:253,440), following the river's general run rather than each bend; creeks and the
// smaller rivers in italic upper and lower case, about two thirds the size, close-set. The site's river labels sit
// on the traced lines, whose meanders leave MapLibre no room for a name; here the names go on smoothed copies
// (riverLines.ts) and the site's river label is hidden.
function water(layer: Layer, halo: string): Layer {
  if (layer.id === 'river-label') return { ...layer, layout: { ...layer.layout, visibility: 'none' } } as Layer
  if (layer.id === 'creek-label') {
    return {
      ...layer,
      layout: { ...layer.layout, 'text-size': ['interpolate', ['linear'], ['zoom'], 10, 10.5, 12, 11.5], 'text-letter-spacing': 0.04 },
      paint: { ...layer.paint, 'text-halo-color': halo, 'text-halo-width': 1.2 },
    } as Layer
  }
  return layer
}

// Names on the smoothed river lines: Natural Earth's main rivers in spaced roman capitals, its North America
// layer's smaller rivers (which have no label on the site today) in italic.
function riverLabel(halo: string, ink: string): LayerSpecification {
  const major: ExpressionSpecification = ['==', ['get', 'rank'], 'major']
  return {
    id: 'wheeler-river-label',
    type: 'symbol',
    source: 'wheeler-rivers',
    minzoom: 7,
    filter: ['any', major, ['>=', ['zoom'], 8]],
    layout: {
      'symbol-placement': 'line',
      'text-field': ['case', major, ['upcase', ['get', 'name']], ['get', 'name']],
      'text-font': ['case', major, ['literal', [fonts.roman]], ['literal', [fonts.italic]]],
      'text-size': ['interpolate', ['linear'], ['zoom'], 7, ['case', major, 11, 10], 10, ['case', major, 14, 11], 12, ['case', major, 16, 12]],
      'text-letter-spacing': ['interpolate', ['linear'], ['zoom'], 7, ['case', major, 0.45, 0.05], 11, ['case', major, 0.9, 0.05]],
      'text-max-angle': 30,
      'symbol-spacing': 500,
    },
    paint: { 'text-color': ink, 'text-halo-color': halo, 'text-halo-width': 1.2 },
  }
}

// Line weight by rank: Natural Earth's scalerank (0 the most important) for the rivers, hairline creeks, and
// intermittent creeks (NHD fcode 46003 and 46007) as a fine dotted line, as Wheeler draws dry washes.
function taper(layer: Layer): Layer {
  const byRank = (heavy: number, light: number): ExpressionSpecification =>
    ['interpolate', ['linear'], ['coalesce', ['get', 'scalerank'], 8], 2, heavy, 10, light]
  if (layer.id === 'river') {
    return { ...layer, paint: { ...layer.paint, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, byRank(1.3, 0.7), 10, byRank(2.8, 1.4), 13, byRank(3.6, 1.8)] } } as Layer
  }
  if (layer.id === 'river-minor') {
    return { ...layer, paint: { ...layer.paint, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.4, 10, 0.9, 13, 1.3] } } as Layer
  }
  if (layer.id === 'creek') {
    return {
      ...layer,
      paint: {
        ...layer.paint,
        'line-width': ['interpolate', ['linear'], ['zoom'], 9, ['case', ['has', 'name'], 0.5, 0.3], 12, ['case', ['has', 'name'], 0.9, 0.5]],
        'line-dasharray': ['match', ['get', 'fcode'], [46003, 46007], ['literal', [0.5, 2]], ['literal', [1, 0]]],
      },
    } as Layer
  }
  return layer
}

// Glyphs on summits the map leaves unlabelled (unnamed ones, and small named ones) get their height alone, in feet
// as Wheeler printed them (7268, 9760): a small italic numeral under the summit, with no unit.
function spotHeights(layer: Layer): Layer {
  if (layer.id !== 'mountain-glyph') return layer
  const height: ExpressionSpecification = ['number-format', ['round', ['*', ['get', 'elevation_m'], 3.28084]], { locale: 'en-GB' }]
  const bare: ExpressionSpecification = ['all', ['!=', ['get', 'landform'], 'pass'], ['!=', ['get', 'elevation_m'], null],
    ['any', ['==', ['get', 'name'], 'Unnamed summit'], ['==', ['get', 'size'], 'small']]]
  return {
    ...layer,
    layout: {
      ...layer.layout,
      'text-field': ['case', bare, height, layer.layout?.['text-field'] as ExpressionSpecification],
      'text-size': ['case', bare, 9.5, 11],
    },
  } as Layer
}

// Landform names along the landform's axis (landforms.ts): spaced so the name spans about 80% of the axis at every
// zoom, as Wheeler spreads TRINIDAD MESA or RATON PLATEAU across the whole feature (letter gaps from 0.5 to 4.5 em).
// Each capital is taken as 0.8 em wide. Where the axis is too short for the name at full size, the type gets smaller
// (down to 9 px) before the letters close up to 0.15 em; past that MapLibre drops the label. Spacing tops out at 4 em.
const LANDFORM_SIZE: Record<string, [number, number]> = { range: [12, 17], valley: [11, 15], plain: [11, 15], mesa: [10, 13] }
const CAP_EM = 0.8
const FILL = 0.8
function landformLayer(halo: string, ink: string): LayerSpecification {
  const zooms = [6, 7, 8, 9, 10, 11, 12, 13]
  const size = (kind: string, z: number) => {
    const [a, b] = LANDFORM_SIZE[kind]
    return a + ((b - a) * Math.min(Math.max(z - 7, 0), 5)) / 5
  }
  const chars: ExpressionSpecification = ['length', ['get', 'name']]
  // MapLibre's zoom 0 is one 512 px tile, so metres per pixel at zoom z = mpp0 / 2 / 2^z (mpp0 is for 256 px tiles).
  const room = (z: number): ExpressionSpecification => ['*', FILL, ['/', ['get', 'len_m'], ['/', ['get', 'mpp0'], 2 * 2 ** z]]]
  const sizeAt = (z: number): ExpressionSpecification => ['max', 9, ['min',
    ['match', ['get', 'kind'], ...Object.keys(LANDFORM_SIZE).flatMap((k) => [k, size(k, z)]), 12],
    ['/', room(z), ['*', chars, CAP_EM + 0.15]]]] as unknown as ExpressionSpecification
  const spacingAt = (z: number): ExpressionSpecification => ['max', 0.15, ['min', 4,
    ['/', ['-', ['/', room(z), sizeAt(z)], ['*', CAP_EM, chars]], ['max', 1, ['-', chars, 1]]]]]
  return {
    id: 'wheeler-landform-label',
    type: 'symbol',
    source: 'wheeler-landforms',
    minzoom: 7,
    filter: ['any', ['!=', ['get', 'kind'], 'mesa'], ['>=', ['zoom'], 10]],
    layout: {
      'symbol-placement': 'line-center',
      'text-field': ['upcase', ['get', 'name']],
      'text-font': [fonts.roman],
      'text-size': ['interpolate', ['linear'], ['zoom'], ...zooms.flatMap((z) => [z, sizeAt(z)])] as ExpressionSpecification,
      'text-letter-spacing': ['interpolate', ['linear'], ['zoom'], ...zooms.flatMap((z) => [z, spacingAt(z)])] as ExpressionSpecification,
      'text-max-angle': 60,
      'text-keep-upright': true,
      'text-padding': 4,
    },
    paint: { 'text-color': ink, 'text-opacity': 0.78, 'text-halo-color': halo, 'text-halo-width': 1 },
  }
}

function paperLayer(layer: Layer, p: Params): Layer {
  if (p.paper === 'today') return layer
  const c = PAPERS[p.paper]
  if (layer.id === 'paper') return { ...layer, paint: { 'background-color': c.low } } as Layer
  if (layer.id === 'mexico' || layer.id === 'raised-mexico') return { ...layer, paint: { ...layer.paint, 'fill-color': c.mexico } } as Layer
  if (layer.id === 'relief-paper') {
    return { ...layer, paint: { ...layer.paint, 'color-relief-color': ['interpolate', ['linear'], ['elevation'], 0, c.high[0], 3000, c.high[1]] } } as Layer
  }
  return layer
}

// The classic style with the parameters applied. Units are imperial: the spot heights are in feet, as on the sheets.
export function wheelerStyle(p: Params): StyleSpecification {
  const base = literaryStyle(tilesBase, fontsBase, dataBase, 'imperial')
  const halo = p.paper === 'today' ? '#e4ddcc' : PAPERS[p.paper].halo
  const waterInk = '#465a65'
  let layers = (base.layers as Layer[]).map((l) => {
    let out = paperLayer(l, p)
    out = hachure(out, p)
    if (p.water) out = water(out, halo)
    if (p.taper) out = taper(out)
    if (p.spotHeights) out = spotHeights(out)
    return out
  }) as LayerSpecification[]
  // The river labels go just under the summit glyphs; the landform names just over them, so a long name is
  // placed first and a glyph's optional text gives way to it, as Wheeler letters a range over its peaks.
  const glyph = layers.findIndex((l) => l.id === 'mountain-glyph')
  layers = [
    ...layers.slice(0, glyph),
    ...(p.water ? [riverLabel(halo, waterInk)] : []),
    layers[glyph],
    ...(p.landforms ? [landformLayer(halo, '#2b2118')] : []),
    ...layers.slice(glyph + 1),
  ]
  return {
    ...base,
    sources: {
      ...base.sources,
      'wheeler-landforms': { type: 'geojson', data: landforms },
      'wheeler-rivers': { type: 'geojson', data: riverLines },
      // Its own source, as MapLibre recommends for 3D terrain, so the hillshade keeps its tiles.
      terrain3d: { type: 'raster-dem', url: `pmtiles://${tilesBase}terrain.pmtiles`, encoding: 'terrarium', tileSize: 256 },
    },
    ...(p.tilted ? { terrain: { source: 'terrain3d', exaggeration: 1.5 } } : {}),
    layers,
  }
}
