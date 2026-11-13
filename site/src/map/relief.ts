import type { ExpressionSpecification, LayerSpecification, SourceSpecification } from 'maplibre-gl'
import { fonts, type Palette } from './tokens'
import { heightLabel, type Units } from '../units'

// Relief (docs/plan.md, section 5.2; decision 0016, "S5"): an Imhof desert tint below zoom 10, then
// near-white paper, a light grey hillshade, 50 m contours and short sepia hachures from relief.pmtiles,
// with mountain glyphs.
export function reliefSources(tilesBase: string, dataBase: string): Record<string, SourceSpecification> {
  return {
    glyphs: { type: 'geojson', data: `${dataBase}mountain_glyphs.geojson` },
    vignettes: { type: 'geojson', data: `${dataBase}vignettes.geojson` },
    terrain: { type: 'raster-dem', url: `pmtiles://${tilesBase}terrain.pmtiles`, encoding: 'terrarium', tileSize: 256 },
    relief: { type: 'vector', url: `pmtiles://${tilesBase}relief.pmtiles` },
    // Split from relief.pmtiles so each archive stays under 100 MB (plan 5.2) and readers who stay zoomed out
    // never fetch the dense strokes.
    'relief-dense': { type: 'vector', url: `pmtiles://${tilesBase}relief-dense.pmtiles` },
    contours: { type: 'vector', url: `pmtiles://${tilesBase}contours.pmtiles` },
  }
}

// Named summits from medium size up, and every named pass (passes are all small), with their height.
export function glyphText(units: Units): ExpressionSpecification {
  const named: ExpressionSpecification = ['all', ['!=', ['get', 'name'], 'Unnamed summit'], ['!=', ['get', 'name'], 'Unnamed pass'],
    ['any', ['!=', ['get', 'size'], 'small'], ['==', ['get', 'landform'], 'pass']]]
  return ['case', named,
    ['case', ['!=', ['get', 'elevation_m'], null], ['concat', ['get', 'name'], '\n', heightLabel(['get', 'elevation_m'], units)], ['get', 'name']],
    '']
}

// Heights on the heavier contours (every 200 m), in feet rounded to 10, since the lines are drawn in metres.
export function contourText(units: Units): ExpressionSpecification {
  return heightLabel(['get', 'Ele'], units, 10)
}

function glyphs(p: Palette, units: Units): LayerSpecification[] {
  const size: ExpressionSpecification = ['*', ['match', ['get', 'size'], 'large', 0.85, 'medium', 0.65, 0.5], ['get', 'glyph_scale']]
  return [
    {
      id: 'contour-label',
      type: 'symbol',
      source: 'contours',
      'source-layer': 'contour',
      minzoom: 11,
      filter: ['==', ['%', ['get', 'Ele'], 200], 0],
      layout: {
        'symbol-placement': 'line',
        'symbol-spacing': 350,
        'text-field': contourText(units),
        'text-font': [fonts.italic],
        'text-size': 10,
        // Contours traced from a 30 m model wiggle; a strict angle limit leaves almost nowhere to put a label.
        'text-max-angle': 80,
        'text-padding': 4,
      },
      paint: { 'text-color': p.contour, 'text-halo-color': p.paperShown, 'text-halo-width': 1.5 },
    },
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
        'text-field': glyphText(units),
        'text-font': [fonts.italic],
        'text-size': 11,
        'text-anchor': 'top',
        'text-optional': true,
      },
      paint: { 'text-color': p.ink, 'text-opacity': 0.8, 'text-halo-color': p.paper, 'text-halo-width': 1.2 },
    },
  ]
}

// Vignettes (plan section 10): drawings of the book's creatures, buildings and objects, each in empty country near
// what it stands for, from data/vignettes.geojson and the vignette-<id> drawings in the sprite (placeholders for now).
// Each shows only in its own zoom range, which keeps them a few to a screen; symbol collision places the lowest
// `priority` first, and the labels above them win any overlap. A located site (a ruin, a hacienda) also gets a
// hairline leader from the drawing to the site; the leader still draws if its drawing loses a collision.
// The spoiler filter by `first_seen` is not applied here yet.
function vignettes(p: Palette): LayerSpecification[] {
  const inRange = (kind: string): ExpressionSpecification => ['all', ['==', ['get', 'kind'], kind],
    ['>=', ['zoom'], ['get', 'min_zoom']], ['<', ['zoom'], ['get', 'max_zoom']]]
  return [
    {
      id: 'vignette-leader',
      type: 'line',
      source: 'vignettes',
      filter: inRange('vignette-leader'),
      layout: { 'line-cap': 'round' },
      paint: { 'line-color': p.ink, 'line-width': 0.6, 'line-opacity': 0.6 },
    },
    {
      id: 'vignette',
      type: 'symbol',
      source: 'vignettes',
      filter: inRange('vignette'),
      layout: {
        'icon-image': ['get', 'vignette'],
        // Drawn on a 96 px grid: about 38 px across at zoom 6, 53 px at 9 and 67 px from 12.
        'icon-size': ['interpolate', ['linear'], ['zoom'], 6, 0.4, 9, 0.55, 12, 0.7],
        'icon-padding': 4,
        'symbol-sort-key': ['get', 'priority'],
      },
    },
  ]
}

// S5 (decision 0016). Below zoom 10: Imhof's desert colours and chromatic hillshade, and no line work.
// Over zoom 9 to 10 they fade into near-white paper and a light grey hillshade, and from 10 the contours
// and hachures draw.
const S5_SPLIT = 10
const s5Blend = <T,>(low: T, high: T) => ['interpolate', ['linear'], ['zoom'], S5_SPLIT - 1, low, S5_SPLIT, high] as never

function s5Ground(p: Palette): LayerSpecification[] {
  return [
    {
      id: 'relief-tint',
      type: 'color-relief',
      source: 'terrain',
      paint: {
        // Imhof's aerial perspective, adapted to the desert (tokens.ts).
        'color-relief-color': ['interpolate', ['linear'], ['elevation'], ...p.imhof.flat()] as ExpressionSpecification,
        'color-relief-opacity': s5Blend(0.9, 0),
      },
    },
    {
      id: 'relief-paper',
      type: 'color-relief',
      source: 'terrain',
      paint: {
        'color-relief-color': ['interpolate', ['linear'], ['elevation'], 0, p.reliefPaper[0], 3000, p.reliefPaper[1]],
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
        'hillshade-shadow-color': s5Blend(p.shadeLow.shadow, p.shadeHigh.shadow),
        'hillshade-highlight-color': s5Blend(p.shadeLow.highlight, p.shadeHigh.highlight),
        'hillshade-accent-color': s5Blend(p.shadeLow.accent, p.shadeHigh.accent),
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
// slopes, so coarse lines get their own slope range. In the corridor a denser set takes over from zoom 12:
// the fine strokes fade out (`out`) as the dense ones fade in (`in`) by zoom 12.6.
const FADE = {
  none: [10, 0.55, 13, 1],
  out: [10, 0.55, 12, 0.85, 12.6, 0],
  in: [12, 0, 12.6, 0.94, 13, 1],
} as const
function strokePaint(ink: string, slope: [number, number], copy: boolean, fade: keyof typeof FADE = 'none') {
  const w: ExpressionSpecification = ['*', 0.9, ['interpolate', ['linear'], ['get', 'Slope'], slope[0], 0.25, slope[1], 1.3], byShade(0.4)]
  const o: ExpressionSpecification = ['*', copy ? 0.4 : 1, ['min', 1, ['*', 0.65, byShade(0.6)]]]
  const stops = FADE[fade].flatMap((v, i) => (i % 2 ? [['min', 1, ['*', v, o]]] : [v]))
  return {
    'line-color': ink,
    'line-width': ['interpolate', ['linear'], ['zoom'], 10, ['*', 0.8, w], 13, w] as ExpressionSpecification,
    'line-opacity': ['interpolate', ['linear'], ['zoom'], ...stops] as unknown as ExpressionSpecification,
    // A faint second stroke beside each line gives it body.
    ...(copy ? { 'line-offset': 0.35 } : {}),
  }
}
const strokeFilter = (kind?: string): ExpressionSpecification => ['all',
  ...(kind ? [['==', ['get', 'kind'], kind] as ExpressionSpecification] : []),
  ['step', ['zoom'], ['<', ['get', 'Rand'], 7], 12, true]]

function s5Lines(p: Palette): LayerSpecification[] {
  const strokes = (id: string, source: string, layer: string, fade: keyof typeof FADE, minzoom = S5_SPLIT): LayerSpecification[] =>
    [false, true].map((copy) => ({
      id: copy ? `${id}-copy` : id, type: 'line', source, 'source-layer': layer, minzoom,
      filter: strokeFilter(), layout: { 'line-cap': 'round' },
      paint: strokePaint(p.hachure, layer === 'coarse' ? [5, 25] : [10, 40], copy, fade),
    }))
  return [
    {
      // Orange-brown, as on the Siegfried sheets: every 100 m below zoom 12, every 50 m from 12, heavier every 200 m.
      id: 'contour', type: 'line', source: 'contours', 'source-layer': 'contour', minzoom: S5_SPLIT,
      filter: ['step', ['zoom'], ['==', ['%', ['get', 'Ele'], 100], 0], 12, true],
      layout: { 'line-join': 'round' },
      paint: { 'line-color': p.contour, 'line-opacity': 0.45, 'line-width': ['case', ['==', ['%', ['get', 'Ele'], 200], 0], 0.8, 0.4] },
    },
    ...strokes('hachure-coarse', 'relief', 'coarse', 'none'),
    ...strokes('hachure-fine', 'relief', 'fine', 'out'),
    ...strokes('hachure-dense', 'relief-dense', 'dense', 'in', 12),
  ]
}

// The relief layers in the palette; literaryStyle places each group at its depth.
export function reliefLayers(p: Palette, units: Units): {
  hillshade: LayerSpecification[]; hachures: LayerSpecification[]; glyphs: LayerSpecification[]; vignettes: LayerSpecification[]
} {
  return { hillshade: s5Ground(p), hachures: s5Lines(p), glyphs: glyphs(p, units), vignettes: vignettes(p) }
}

// The Raised view (plan oblique relief): line work from oblique-<n>.pmtiles in which every point has moved north
// by its height, so ranges stand up and hide the ground behind them. It covers the corridor of the stretches
// ridden or walked in every journey (decisions 0018 and 0019); the map's layers that cannot move with the terrain are hidden by MapView.
export const RAISED_BOUNDS: [number, number, number, number] = [-109.9, 28.23, -106.66, 34.0]
export const RAISED_MIN_ZOOM = 9

// Classic base layers drawn again from the raised copies of their lines, by the `kind` in the oblique archives.
const RAISED_BASE: Record<string, string> = {
  mexico: 'mexico', 'county-line': 'county', 'state-line': 'state', 'country-line': 'country', road: 'road',
  railroad: 'railroad', 'railroad-ties': 'railroad', 'creek-label': 'stream',
}

// Each group of raised layers goes in below the classic layer named by `before`: the Mexico side under the
// paper tint, the relief under the journeys' halo, and the boundaries, water and roads over it. `classic` is the
// literary style's layers in the palette `p`.
export function raisedLayers(classic: LayerSpecification[], p: Palette): { before: string; layers: LayerSpecification[] }[] {
  const source = { source: 'oblique', 'source-layer': 'oblique' } as const
  const base = { ...source, minzoom: RAISED_MIN_ZOOM, layout: { 'line-cap': 'round', 'line-join': 'round', visibility: 'none' } } as const
  const kind = (k: string): ExpressionSpecification => ['==', ['get', 'kind'], k]
  // The classic layer's look, drawn from the raised lines of its kind.
  const copy = (id: string): LayerSpecification => {
    const layer = classic.find((l) => l.id === id) as LayerSpecification & { filter?: ExpressionSpecification; layout?: object }
    return { ...layer, ...source, id: `raised-${id}`, filter: layer.filter ? ['all', kind(RAISED_BASE[id]), layer.filter] : kind(RAISED_BASE[id]),
      layout: { ...layer.layout, visibility: 'none' } } as LayerSpecification
  }
  return [
    { before: 'relief-tint', layers: [copy('mexico')] },
    {
      before: 'contour',
      layers: [
        { ...base, id: 'raised-contour', type: 'line', filter: kind('contour'),
          paint: { 'line-color': p.contour, 'line-width': 0.4, 'line-opacity': 0.45 } },
        { ...base, id: 'raised-stroke', type: 'line', filter: strokeFilter('stroke'), paint: strokePaint(p.hachure, [10, 40], false) },
        { ...base, id: 'raised-stroke-copy', type: 'line', filter: strokeFilter('stroke'), paint: strokePaint(p.hachure, [10, 40], true) },
        // Ridgelines, heavier on higher ridges (rel: height above the ground around, metres); below zoom 12 only the higher ones.
        { ...base, id: 'raised-ridge', type: 'line',
          filter: ['all', kind('ridge'), ['step', ['zoom'], ['>=', ['get', 'rel'], 160], 12, true]],
          paint: { 'line-color': p.ink, 'line-width': ['interpolate', ['linear'], ['get', 'rel'], 100, 0.5, 300, 1.1], 'line-opacity': 0.7 } },
        { ...base, id: 'raised-crest', type: 'line', filter: kind('crest'),
          paint: { 'line-color': p.ink, 'line-width': 0.9, 'line-opacity': 0.8 } },
      ],
    },
    {
      before: 'creek-label',
      layers: [
        copy('county-line'), copy('state-line'), copy('country-line'),
        // Streams on both sides of the border, wider with Strahler order (or NHD's stand-in for it).
        { ...base, id: 'raised-stream', type: 'line', filter: kind('stream'),
          paint: { 'line-color': p.raisedStream, 'line-width': ['interpolate', ['linear'], ['get', 'ord'], 3, 0.6, 8, 2.2], 'line-opacity': 0.6 } },
        copy('road'), copy('railroad'), copy('railroad-ties'), copy('creek-label'),
      ],
    },
  ]
}
