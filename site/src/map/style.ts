import type { LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { reliefLayers, reliefSources } from './relief'
import { fonts, palette as tokens, SPRITE } from './tokens'
import type { Units } from '../units'

// The literary base: everything drawn from base.pmtiles, the paper, and relief. Satellite mode hides these.
export const BASE_LAYERS = [
  'paper', 'mexico', 'lake', 'county-line', 'state-line', 'creek', 'river-minor', 'river',
  'road', 'railroad', 'railroad-ties', 'creek-label', 'river-label',
  'relief-tint', 'relief-paper', 'hillshade', 'contour', 'contour-label', 'hachure-coarse', 'hachure-coarse-copy', 'hachure-fine', 'hachure-fine-copy', 'hachure-dense', 'hachure-dense-copy',
  'mountain-glyph', 'vignette-leader', 'vignette',
]

// The literary basemap (docs/plan.md, section 5.1): ink on caliche paper, the
// Mexico side a shade darker, rivers in blue-grey ink, and a dash-dot
// international line as on the 1850s-1880s survey sheets.
export function literaryStyle(tilesBase: string, fontsBase: string, dataBase: string, units: Units): StyleSpecification {
  const base = 'base'
  const r = reliefLayers(tokens, units)
  const layers: LayerSpecification[] = [
      { id: 'paper', type: 'background', paint: { 'background-color': tokens.paper } },
      {
        id: 'mexico',
        type: 'fill',
        source: base,
        'source-layer': 'mexico',
        paint: { 'fill-color': tokens.paperMexico },
      },
      {
        id: 'lake',
        type: 'fill',
        source: base,
        'source-layer': 'lake',
        paint: { 'fill-color': tokens.water, 'fill-opacity': 0.25, 'fill-outline-color': tokens.water },
      },
      {
        id: 'county-line',
        type: 'line',
        source: base,
        'source-layer': 'county_line',
        minzoom: 7,
        paint: { 'line-color': tokens.inkFaint, 'line-width': 0.6, 'line-dasharray': [1, 3] },
      },
      {
        id: 'state-line',
        type: 'line',
        source: base,
        'source-layer': 'state_line',
        paint: { 'line-color': tokens.ink, 'line-opacity': 0.55, 'line-width': 0.9, 'line-dasharray': [4, 2] },
      },
      {
        id: 'country-line',
        type: 'line',
        source: base,
        'source-layer': 'country_line',
        paint: {
          'line-color': tokens.ink,
          'line-width': ['interpolate', ['linear'], ['zoom'], 5, 1.2, 10, 2.2],
          // dash, gap, dot, gap: the dash-dot boundary of period survey maps
          'line-dasharray': [6, 2, 1, 2],
        },
      },
      {
        // USGS NHD streams, US side only; intermittent and ephemeral ones (fcode 46003, 46007) dashed.
        id: 'creek',
        type: 'line',
        source: base,
        'source-layer': 'creek',
        minzoom: 9,
        // Named streams from zoom 9; the dense unnamed network only from zoom 10, and fainter.
        filter: ['any', ['has', 'name'], ['>=', ['zoom'], 10]],
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': tokens.water,
          'line-width': ['interpolate', ['linear'], ['zoom'], 9, 0.4, 12, 1],
          'line-opacity': ['case', ['has', 'name'], 0.9, 0.35],
          'line-dasharray': ['match', ['get', 'fcode'], [46003, 46007], ['literal', [3, 2]], ['literal', [1, 0]]],
        },
      },
      {
        id: 'river-minor',
        type: 'line',
        source: base,
        'source-layer': 'river_minor',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': tokens.water, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.5, 10, 1.2] },
      },
      {
        id: 'river',
        type: 'line',
        source: base,
        'source-layer': 'river',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': tokens.water, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.9, 10, 2] },
      },
      {
        id: 'road',
        type: 'line',
        source: base,
        'source-layer': 'road',
        minzoom: 6,
        paint: { 'line-color': tokens.ink, 'line-opacity': 0.45, 'line-width': 0.7, 'line-dasharray': [2, 2] },
      },
      {
        id: 'railroad',
        type: 'line',
        source: base,
        'source-layer': 'railroad',
        paint: { 'line-color': tokens.ink, 'line-width': 0.8 },
      },
      {
        // Short cross-ties over the rail line.
        id: 'railroad-ties',
        type: 'line',
        source: base,
        'source-layer': 'railroad',
        minzoom: 7,
        paint: { 'line-color': tokens.ink, 'line-width': 4, 'line-dasharray': [0.25, 3] },
      },
      {
        id: 'creek-label',
        type: 'symbol',
        source: base,
        'source-layer': 'creek',
        minzoom: 10,
        filter: ['has', 'name'],
        layout: {
          'symbol-placement': 'line',
          'text-field': ['get', 'name'],
          'text-font': [fonts.italic],
          'text-size': 11.5,
        },
        paint: { 'text-color': tokens.waterLabel, 'text-halo-color': tokens.paper, 'text-halo-width': 1.5 },
      },
      {
        id: 'river-label',
        type: 'symbol',
        source: base,
        'source-layer': 'river',
        minzoom: 7,
        layout: {
          'symbol-placement': 'line',
          'text-field': ['get', 'name'],
          'text-font': [fonts.italic],
          'text-size': 13,
          'text-letter-spacing': 0.1,
        },
        paint: { 'text-color': tokens.waterLabel, 'text-halo-color': tokens.paper, 'text-halo-width': 1.5 },
      },
    ]
  // Hillshade sits on the paper; hachures under the water and lines; glyphs, then vignettes, above the lines and
  // below the labels.
  const at = (id: string) => layers.findIndex((l) => l.id === id)
  layers.splice(at('creek-label'), 0, ...r.glyphs, ...r.vignettes)
  layers.splice(at('county-line'), 0, ...r.hachures)
  layers.splice(at('lake'), 0, ...r.hillshade)
  return {
    version: 8,
    glyphs: `${fontsBase}{fontstack}/{range}.pbf`,
    sprite: `${tilesBase.replace(/tiles\/$/, '')}sprites/${SPRITE}`,
    sources: {
      [base]: { type: 'vector', url: `pmtiles://${tilesBase}base.pmtiles` },
      ...reliefSources(tilesBase, dataBase),
    },
    layers,
  }
}
