import type { LayerSpecification, SourceSpecification } from 'maplibre-gl'
import { fonts, tokens } from './tokens'

// Relief (docs/plan.md, section 5.2). Until the relief experiment picks a
// treatment, the site shows mountain glyphs only. The comparison sheet
// (tools/relief-sheet.mjs) chooses a treatment with ?relief=<name>; hachures
// come from tiles/out/relief-test.pmtiles, which exists only on the machine
// that builds the sheet, so the deployed site never requests it.
export type Treatment = 'glyphs' | 'survey' | 'survey-noglyphs' | 'sierra' | 'swiss' | 'control'

const TREATMENTS: Treatment[] = ['glyphs', 'survey', 'survey-noglyphs', 'sierra', 'swiss', 'control']

export function treatmentFromUrl(): Treatment {
  const asked = new URLSearchParams(window.location.search).get('relief') as Treatment | null
  return asked && TREATMENTS.includes(asked) ? asked : 'glyphs'
}

export function reliefSources(t: Treatment, tilesBase: string, dataBase: string): Record<string, SourceSpecification> {
  const sources: Record<string, SourceSpecification> = {
    glyphs: { type: 'geojson', data: `${dataBase}mountain_glyphs.geojson` },
  }
  if (t === 'swiss' || t === 'control') {
    sources.terrain = { type: 'raster-dem', url: `pmtiles://${tilesBase}terrain.pmtiles`, encoding: 'terrarium', tileSize: 256 }
  }
  if (t === 'survey' || t === 'survey-noglyphs' || t === 'sierra' || t === 'swiss') {
    sources.relief = { type: 'vector', url: `pmtiles://${tilesBase}relief-test.pmtiles` }
  }
  return sources
}

// Coarse hachures to zoom 9.5, fine above; steeper is heavier (plan 5.2, step 6).
const hachureWidth = (scale: number) =>
  ['interpolate', ['linear'], ['get', 'Slope'], 10, 0.25 * scale, 40, 1.3 * scale] as unknown as number

function hachures(t: Treatment): LayerSpecification[] {
  if (t === 'glyphs' || t === 'control') return []
  // Swiss accent: hachures only on the steepest, rockiest ground.
  const steep = t === 'swiss' ? [['>=', ['get', 'Slope'], 25]] : []
  const dash = t === 'sierra' ? { 'line-dasharray': [1.2, 1] } : {}
  const make = (id: string, layer: string, range: [number, number]): LayerSpecification => ({
    id,
    type: 'line',
    source: 'relief',
    'source-layer': layer,
    minzoom: range[0],
    maxzoom: range[1],
    ...(steep.length ? { filter: ['all', ...steep] as never } : {}),
    layout: { 'line-cap': 'round' },
    // Whole coarse lines carry no slope, so they take one weight; fine pieces are weighted by slope.
    paint: { 'line-color': tokens.ink, 'line-opacity': 0.75, 'line-width': layer === 'hachure_coarse' ? 0.7 : hachureWidth(t === 'sierra' ? 1.3 : 1), ...dash },
  })
  const layers = [make('hachure-coarse', 'hachure_coarse', [6, 9.5]), make('hachure-fine', 'hachure_fine', [9.5, 14])]
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
  if (t !== 'swiss' && t !== 'control') return []
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
      // Large peaks from zoom 6, medium from 7.5, small from 9.
      filter: [
        'any',
        ['==', ['get', 'size'], 'large'],
        ['all', ['==', ['get', 'size'], 'medium'], ['>=', ['zoom'], 7.5]],
        ['>=', ['zoom'], 9],
      ],
      layout: {
        'icon-image': [
          'concat', 'mountain-', ['case', ['<', ['get', 'glyph'], 10], '0', ''], ['to-string', ['get', 'glyph']],
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
