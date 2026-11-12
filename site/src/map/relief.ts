import type { LayerSpecification, SourceSpecification } from 'maplibre-gl'
import { fonts, tokens } from './tokens'

// Relief (docs/plan.md, section 5.2). The map uses "Swiss, full, soft" (decision 0014):
// pale, thin hachures from relief.pmtiles over a sepia hillshade, with mountain glyphs.
// The comparison sheet (tools/relief-sheet.mjs) picks the experiment's other treatments
// with ?relief=<name>; their hachures come from tiles/out/relief-test.pmtiles, which
// exists only on the machine that builds the sheet.
export type Treatment =
  | 'glyphs' | 'survey' | 'survey-lines' | 'survey-noglyphs' | 'sierra'
  | 'swiss' | 'swiss-dense' | 'swiss-full' | 'swiss-light' | 'swiss-thin' | 'swiss-soft' | 'control'

const TREATMENTS: Treatment[] = [
  'glyphs', 'survey', 'survey-lines', 'survey-noglyphs', 'sierra',
  'swiss', 'swiss-dense', 'swiss-full', 'swiss-light', 'swiss-thin', 'swiss-soft', 'control',
]
const isSwiss = (t: Treatment) => t.startsWith('swiss')
const hasHillshade = (t: Treatment) => isSwiss(t) || t === 'control'

export function treatmentFromUrl(): Treatment {
  const asked = new URLSearchParams(window.location.search).get('relief') as Treatment | null
  return asked && TREATMENTS.includes(asked) ? asked : 'swiss-soft'
}

export function reliefSources(t: Treatment, tilesBase: string, dataBase: string): Record<string, SourceSpecification> {
  const sources: Record<string, SourceSpecification> = {
    glyphs: { type: 'geojson', data: `${dataBase}mountain_glyphs.geojson` },
  }
  if (hasHillshade(t)) {
    sources.terrain = { type: 'raster-dem', url: `pmtiles://${tilesBase}terrain.pmtiles`, encoding: 'terrarium', tileSize: 256 }
  }
  if (t !== 'glyphs' && t !== 'control') {
    const archive = t === 'swiss-soft' ? 'relief' : 'relief-test'
    sources.relief = { type: 'vector', url: `pmtiles://${tilesBase}${archive}.pmtiles` }
  }
  return sources
}

// Steeper is heavier (plan 5.2, step 6). The 90 m coarse DEM is smoother, so its slopes run lower
// (median 11-16 degrees against 18-22 at 30 m) and get their own range and steep threshold.
const SCALES = {
  // steep: the Swiss threshold (about the steepest 10-30% of lines); dense: Swiss dense (about half).
  coarse: { id: 'hachure-coarse', layer: 'hachure_coarse', zooms: [6, 9.5], slope: [5, 25], steep: 18, dense: 12 },
  fine: { id: 'hachure-fine', layer: 'hachure_fine', zooms: [9.5, 14], slope: [10, 40], steep: 25, dense: 18 },
  lines: { id: 'hachure-fine', layer: 'hachure_lines', zooms: [9.5, 14], slope: [10, 40], steep: 25, dense: 18 },
  // relief.pmtiles, built by tiles/build_relief.py: whole lines with their mean slope. Its coarse lines
  // stop at zoom 9 inside the journeys corridor, where the fine lines start at 10, and carry on outside it.
  productionCoarse: { id: 'hachure-coarse', layer: 'coarse', zooms: [6, 14], slope: [5, 25], steep: 18, dense: 12 },
  productionFine: { id: 'hachure-fine', layer: 'fine', zooms: [10, 14], slope: [10, 40], steep: 25, dense: 18 },
} as const

function hachures(t: Treatment): LayerSpecification[] {
  if (t === 'glyphs' || t === 'control') return []
  // Fine detail from the script's short split pieces, or from its whole lines with a mean slope.
  const [coarse, fine] =
    t === 'swiss-soft' ? [SCALES.productionCoarse, SCALES.productionFine]
    : [SCALES.coarse, t === 'survey-lines' || isSwiss(t) ? SCALES.lines : SCALES.fine]
  // Swiss full, light, thin and soft keep every line. Light draws them in pale sepia, thin at half
  // the stroke, and soft does both.
  const color = t === 'swiss-light' || t === 'swiss-soft' ? 'rgba(90, 66, 44, 0.55)' : tokens.ink
  const weight = t === 'sierra' ? 1.3 : t === 'swiss-thin' || t === 'swiss-soft' ? 0.5 : 1
  const make = (s: (typeof SCALES)[keyof typeof SCALES]): LayerSpecification => ({
    id: s.id,
    type: 'line',
    source: 'relief',
    'source-layer': s.layer,
    minzoom: s.zooms[0],
    maxzoom: s.zooms[1],
    // Swiss accent: hachures only on each scale's steepest ground.
    ...(t === 'swiss' ? { filter: ['>=', ['get', 'Slope'], s.steep] as never } : {}),
    ...(t === 'swiss-dense' ? { filter: ['>=', ['get', 'Slope'], s.dense] as never } : {}),
    layout: { 'line-cap': 'round' },
    paint: {
      'line-color': color,
      // The production coarse lines fade in, so the Sierra Madre does not read as speckle at zoom 6.
      'line-opacity': s === SCALES.productionCoarse ? ['interpolate', ['linear'], ['zoom'], 6, 0.35, 8, 0.75] : 0.75,
      'line-width': ['interpolate', ['linear'], ['get', 'Slope'], s.slope[0], 0.25 * weight, s.slope[1], 1.3 * weight],
      ...(t === 'sierra' ? { 'line-dasharray': [1.2, 1] } : {}),
    },
  })
  const layers = [make(coarse), make(fine)]
  if (t === 'sierra') {
    layers.push({
      id: 'stipple',
      type: 'circle',
      source: 'relief',
      'source-layer': 'stipple',
      minzoom: 8,
      paint: { 'circle-radius': 0.6, 'circle-color': tokens.ink, 'circle-opacity': 0.6 },
    })
  }
  return layers
}

function hillshade(t: Treatment): LayerSpecification[] {
  if (!hasHillshade(t)) return []
  return [
    {
      id: 'hillshade',
      type: 'hillshade',
      source: 'terrain',
      paint: {
        'hillshade-method': 'multidirectional',
        // Sepia, light: a tone under the ink, not a photograph. The control is stronger so it stands alone.
        'hillshade-shadow-color': t === 'control' ? 'rgba(70, 50, 30, 0.45)' : 'rgba(70, 50, 30, 0.22)',
        'hillshade-highlight-color': 'rgba(255, 250, 240, 0.18)',
        'hillshade-accent-color': 'rgba(70, 50, 30, 0.1)',
      },
    },
  ]
}

function glyphs(t: Treatment): LayerSpecification[] {
  if (t === 'survey-noglyphs' || t === 'control') return []
  return [
    {
      id: 'mountain-glyph',
      type: 'symbol',
      source: 'glyphs',
      // Large glyphs from zoom 6, medium from 7.5, small from 10.
      filter: [
        'any',
        ['==', ['get', 'size'], 'large'],
        ['all', ['==', ['get', 'size'], 'medium'], ['>=', ['zoom'], 7.5]],
        ['>=', ['zoom'], 10],
      ],
      layout: {
        // <landform>-<nn>[-flip], from art/glyphs/make_glyphs.py.
        'icon-image': [
          'concat', ['coalesce', ['get', 'landform'], 'peak'], '-',
          ['case', ['<', ['get', 'glyph'], 10], '0', ''], ['to-string', ['get', 'glyph']],
          ['case', ['get', 'flip'], '-flip', ''],
        ],
        'icon-size': ['*', ['match', ['get', 'size'], 'large', 0.85, 'medium', 0.65, 0.5], ['get', 'glyph_scale']],
        'icon-rotate': ['get', 'glyph_rotate'],
        'icon-anchor': 'bottom',
        'icon-padding': 2,
        // Biggest peaks win collisions; unknown prominence (the highest summits) sorts first.
        'symbol-sort-key': ['-', 0, ['coalesce', ['get', 'prominence_m'], 99999]],
        'text-field': ['case', ['all', ['!=', ['get', 'name'], 'Unnamed summit'], ['!=', ['get', 'size'], 'small']], ['get', 'name'], ''],
        'text-font': [fonts.italic],
        'text-size': 11,
        'text-anchor': 'top',
        'text-optional': true,
      },
      paint: { 'text-color': tokens.ink, 'text-opacity': 0.8, 'text-halo-color': tokens.paper, 'text-halo-width': 1.2 },
    },
  ]
}

// The relief layers for a treatment; literaryStyle places each group at its depth.
export function reliefLayers(t: Treatment): { hillshade: LayerSpecification[]; hachures: LayerSpecification[]; glyphs: LayerSpecification[] } {
  return { hillshade: hillshade(t), hachures: hachures(t), glyphs: glyphs(t) }
}
