import type { ExpressionSpecification, LayerSpecification, SourceSpecification } from 'maplibre-gl'
import { fonts, tokens } from './tokens'

// Relief (docs/plan.md, section 5.2; decision 0016, "S5"): an Imhof desert tint below zoom 10, then
// near-white paper, a light grey hillshade, 50 m contours and short sepia hachures from relief.pmtiles,
// with mountain glyphs.
export function reliefSources(tilesBase: string, dataBase: string): Record<string, SourceSpecification> {
  return {
    glyphs: { type: 'geojson', data: `${dataBase}mountain_glyphs.geojson` },
    terrain: { type: 'raster-dem', url: `pmtiles://${tilesBase}terrain.pmtiles`, encoding: 'terrarium', tileSize: 256 },
    relief: { type: 'vector', url: `pmtiles://${tilesBase}relief.pmtiles` },
  }
}

function glyphs(): LayerSpecification[] {
  const size: ExpressionSpecification = ['*', ['match', ['get', 'size'], 'large', 0.85, 'medium', 0.65, 0.5], ['get', 'glyph_scale']]
  return [
    {
      id: 'mountain-glyph',
      type: 'symbol',
      source: 'glyphs',
      // Large glyphs from zoom 6, medium from 7, small from 9: below zoom 10 the Imhof tint has no line work,
      // so the glyphs carry the relief there.
      filter: [
        'any',
        ['==', ['get', 'size'], 'large'],
        ['all', ['==', ['get', 'size'], 'medium'], ['>=', ['zoom'], 7]],
        ['>=', ['zoom'], 9],
      ],
      layout: {
        // <landform>-<nn>[-flip], from art/glyphs/make_glyphs.py.
        'icon-image': [
          'concat', ['coalesce', ['get', 'landform'], 'peak'], '-',
          ['case', ['<', ['get', 'glyph'], 10], '0', ''], ['to-string', ['get', 'glyph']],
          ['case', ['get', 'flip'], '-flip', ''],
        ],
        // A fifth smaller up to zoom 8, so more glyphs pass collision where they first appear.
        'icon-size': ['interpolate', ['linear'], ['zoom'], 8, ['*', 0.8, size], 10, size],
        'icon-rotate': ['get', 'glyph_rotate'],
        'icon-anchor': 'bottom',
        'icon-padding': 2,
        // Biggest peaks win collisions; unknown prominence (the highest summits) sorts first. Passes come after
        // every summit, named before unnamed, each by the prominence of the summit whose key col it is.
        'symbol-sort-key': ['case', ['==', ['get', 'landform'], 'pass'],
          ['-', ['case', ['==', ['get', 'name'], 'Unnamed pass'], 200000, 100000], ['get', 'prominence_m']],
          ['-', 0, ['coalesce', ['get', 'prominence_m'], 99999]]],
        // Named summits from medium size up; every named pass, since passes are all small.
        'text-field': ['case', ['all', ['!=', ['get', 'name'], 'Unnamed summit'], ['!=', ['get', 'name'], 'Unnamed pass'],
          ['any', ['!=', ['get', 'size'], 'small'], ['==', ['get', 'landform'], 'pass']]], ['get', 'name'], ''],
        'text-font': [fonts.italic],
        'text-size': 11,
        'text-anchor': 'top',
        'text-optional': true,
      },
      paint: { 'text-color': tokens.ink, 'text-opacity': 0.8, 'text-halo-color': tokens.paper, 'text-halo-width': 1.2 },
    },
  ]
}

// S5 (decision 0016). Below zoom 10: Imhof's desert colours and chromatic hillshade, and no line work.
// Over zoom 9 to 10 they fade into near-white paper and a light grey hillshade, and from 10 the contours
// and hachures draw.
const S5_SPLIT = 10
const s5Blend = <T,>(low: T, high: T) => ['interpolate', ['linear'], ['zoom'], S5_SPLIT - 1, low, S5_SPLIT, high] as never
// What the paper looks like above the split: the base paper under 70% of the near-white tint. Halos match it.
export const S5_PAPER_SHOWN = '#f1ede2'

function s5Ground(): LayerSpecification[] {
  return [
    {
      id: 'relief-tint',
      type: 'color-relief',
      source: 'terrain',
      paint: {
        // Imhof's aerial perspective, adapted to the desert: hazy grey-green basins, pale sand plains,
        // warm ochre on the high sierra, paler summits. Metres; the region runs from 0 to about 3,000 m.
        'color-relief-color': ['interpolate', ['linear'], ['elevation'], 0, '#d3d7c4', 600, '#dedbbf', 1100, '#e6dcbb',
          1600, '#e9d9b1', 1950, '#e0c498', 2300, '#d3ae88', 2700, '#d8bfa8', 3200, '#e9e0d6'],
        'color-relief-opacity': s5Blend(0.9, 0),
      },
    },
    {
      id: 'relief-paper',
      type: 'color-relief',
      source: 'terrain',
      paint: {
        'color-relief-color': ['interpolate', ['linear'], ['elevation'], 0, '#f7f4ec', 3000, '#f3eee2'],
        'color-relief-opacity': s5Blend(0, 0.7),
      },
    },
    {
      id: 'hillshade',
      type: 'hillshade',
      source: 'terrain',
      paint: {
        'hillshade-method': 'combined',
        'hillshade-illumination-direction': 315,
        'hillshade-exaggeration': s5Blend(0.65, 0.5),
        // Imhof: blue-violet shadows and warm light; above the split, a light swisstopo grey.
        'hillshade-shadow-color': s5Blend('rgba(74, 88, 128, 0.5)', 'rgba(74, 79, 92, 0.22)'),
        'hillshade-highlight-color': s5Blend('rgba(255, 240, 192, 0.35)', 'rgba(255, 255, 255, 0.3)'),
        'hillshade-accent-color': s5Blend('rgba(74, 88, 128, 0.12)', 'rgba(74, 79, 92, 0.05)'),
      },
    },
  ]
}

// Shade under a light from the north-west, 40 degrees up: 0 lit, 1 in full shade, from each line's Slope and Aspect.
const rad = Math.PI / 180
const zenith = 50 * rad
const slopeRad: ExpressionSpecification = ['*', ['get', 'Slope'], rad]
const shade: ExpressionSpecification = ['-', 1, ['max', 0, ['min', 1, ['+', ['*', Math.cos(zenith), ['cos', slopeRad]],
  ['*', Math.sin(zenith), ['*', ['sin', slopeRad], ['cos', ['-', 315 * rad, ['*', ['get', 'Aspect'], rad]]]]]]]]]
// Between 1 - amount and 1 + 1.5 * amount: about 1 on typical ground, more on slopes facing away from the light.
const byShade = (amount: number): ExpressionSpecification => ['+', 1 - amount, ['*', amount * 2.5, shade]]

// Sepia strokes, heavier and darker on shaded slopes, steeper is wider. They fade in from zoom 10 to 13,
// and below zoom 12 only 70% of them draw (Rand is a fixed digit, 0-9). The 90 m coarse DEM gives gentler
// slopes, so coarse lines get their own slope range.
const S5_INK = '#6e5443'
function strokePaint(slope: [number, number], copy: boolean) {
  const w: ExpressionSpecification = ['*', 0.9, ['interpolate', ['linear'], ['get', 'Slope'], slope[0], 0.25, slope[1], 1.3], byShade(0.4)]
  const o: ExpressionSpecification = ['*', copy ? 0.4 : 1, ['min', 1, ['*', 0.65, byShade(0.6)]]]
  return {
    'line-color': S5_INK,
    'line-width': ['interpolate', ['linear'], ['zoom'], 10, ['*', 0.8, w], 13, w] as ExpressionSpecification,
    'line-opacity': ['interpolate', ['linear'], ['zoom'], 10, ['min', 1, ['*', 0.55, o]], 13, ['min', 1, o]] as ExpressionSpecification,
    // A faint second stroke beside each line gives it body.
    ...(copy ? { 'line-offset': 0.35 } : {}),
  }
}
const strokeFilter = (kind?: string): ExpressionSpecification => ['all',
  ...(kind ? [['==', ['get', 'kind'], kind] as ExpressionSpecification] : []),
  ['step', ['zoom'], ['<', ['get', 'Rand'], 7], 12, true]]

function s5Lines(): LayerSpecification[] {
  const strokes = (id: string, layer: string, slope: [number, number]): LayerSpecification[] => [false, true].map((copy) => ({
    id: copy ? `${id}-copy` : id, type: 'line', source: 'relief', 'source-layer': layer, minzoom: S5_SPLIT,
    filter: strokeFilter(), layout: { 'line-cap': 'round' }, paint: strokePaint(slope, copy),
  }))
  return [
    {
      // Orange-brown, as on the Siegfried sheets: every 100 m below zoom 12, every 50 m from 12, heavier every 200 m.
      id: 'contour', type: 'line', source: 'relief', 'source-layer': 'contour', minzoom: S5_SPLIT,
      filter: ['step', ['zoom'], ['==', ['%', ['get', 'Ele'], 100], 0], 12, true],
      layout: { 'line-join': 'round' },
      paint: { 'line-color': '#b0622e', 'line-opacity': 0.45, 'line-width': ['case', ['==', ['%', ['get', 'Ele'], 200], 0], 0.8, 0.4] },
    },
    ...strokes('hachure-coarse', 'coarse', [5, 25]),
    ...strokes('hachure-fine', 'fine', [10, 40]),
  ]
}

// The relief layers; literaryStyle places each group at its depth.
export function reliefLayers(): { hillshade: LayerSpecification[]; hachures: LayerSpecification[]; glyphs: LayerSpecification[] } {
  return { hillshade: s5Ground(), hachures: s5Lines(), glyphs: glyphs() }
}

// The Raised view (plan oblique relief): line work from oblique.pmtiles in which every point has moved north
// by its height, so ranges stand up and hide the ground behind them. For now it covers only a test area
// around the Pilares; the map's other layers cannot move with the terrain, so MapView hides them.
export const RAISED_BOUNDS: [number, number, number, number] = [-109.74, 30.72, -108.92, 31.08]
export const RAISED_MIN_ZOOM = 9

export function raisedLayers(): LayerSpecification[] {
  const base = { source: 'oblique', 'source-layer': 'oblique', minzoom: RAISED_MIN_ZOOM, layout: { 'line-cap': 'round', 'line-join': 'round', visibility: 'none' } } as const
  return [
    { ...base, id: 'raised-contour', type: 'line', filter: ['==', ['get', 'kind'], 'contour'],
      paint: { 'line-color': '#b0622e', 'line-width': 0.4, 'line-opacity': 0.45 } },
    { ...base, id: 'raised-stream', type: 'line', filter: ['==', ['get', 'kind'], 'stream'],
      paint: { 'line-color': '#6f8796', 'line-width': ['interpolate', ['linear'], ['get', 'ord'], 3, 0.6, 8, 2.2], 'line-opacity': 0.6 } },
    { ...base, id: 'raised-stroke', type: 'line', filter: strokeFilter('stroke'), paint: strokePaint([10, 40], false) },
    { ...base, id: 'raised-stroke-copy', type: 'line', filter: strokeFilter('stroke'), paint: strokePaint([10, 40], true) },
    // Ridgelines, heavier on higher ridges (rel: height above the ground around, metres); below zoom 12 only the higher ones.
    { ...base, id: 'raised-ridge', type: 'line',
      filter: ['all', ['==', ['get', 'kind'], 'ridge'], ['step', ['zoom'], ['>=', ['get', 'rel'], 160], 12, true]],
      paint: { 'line-color': tokens.ink, 'line-width': ['interpolate', ['linear'], ['get', 'rel'], 100, 0.5, 300, 1.1], 'line-opacity': 0.7 } },
    { ...base, id: 'raised-crest', type: 'line', filter: ['==', ['get', 'kind'], 'crest'],
      paint: { 'line-color': tokens.ink, 'line-width': 0.9, 'line-opacity': 0.8 } },
    { ...base, id: 'raised-journey', type: 'line', filter: ['==', ['get', 'kind'], 'journey'],
      paint: { 'line-color': tokens.ink, 'line-width': 2, 'line-dasharray': [3, 1.5] } },
  ]
}
