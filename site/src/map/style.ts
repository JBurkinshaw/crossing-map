import type { StyleSpecification } from 'maplibre-gl'
import { fonts, tokens } from './tokens'

// The literary basemap (docs/plan.md, section 5.1): ink on caliche paper, the
// Mexico side a shade darker, rivers in blue-grey ink, and a dash-dot
// international line as on the 1850s-1880s survey sheets.
export function literaryStyle(tilesBase: string, fontsBase: string): StyleSpecification {
  const base = 'base'
  return {
    version: 8,
    glyphs: `${fontsBase}{fontstack}/{range}.pbf`,
    sources: {
      [base]: { type: 'vector', url: `pmtiles://${tilesBase}base.pmtiles` },
    },
    layers: [
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
        id: 'town',
        type: 'circle',
        source: base,
        'source-layer': 'town',
        minzoom: 6,
        paint: {
          'circle-radius': 2,
          'circle-color': tokens.ink,
          'circle-opacity': 0.6,
        },
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
        paint: { 'text-color': tokens.water, 'text-halo-color': tokens.paper, 'text-halo-width': 1.5 },
      },
      {
        id: 'town-label',
        type: 'symbol',
        source: base,
        'source-layer': 'town',
        minzoom: 6,
        layout: {
          'text-field': ['get', 'name'],
          'text-font': [fonts.roman],
          'text-size': 12,
          'text-anchor': 'left',
          'text-offset': [0.5, 0],
          'symbol-sort-key': ['get', 'scalerank'],
        },
        paint: { 'text-color': tokens.ink, 'text-opacity': 0.75, 'text-halo-color': tokens.paper, 'text-halo-width': 1.2 },
      },
    ],
  }
}
