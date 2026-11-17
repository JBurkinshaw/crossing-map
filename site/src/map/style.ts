import type { ExpressionSpecification, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { reliefLayers, reliefSources, VIGNETTE_LAYERS } from './relief'
import { fonts, palette as tokens, SPRITE } from './tokens'
import { contextPlaceLayer } from './contextPlaces'
import { waterPlaceLayer } from './waterPlaces'
import type { Units } from '../units'

// Every layer literaryStyle draws is part of the literary base, which satellite, topo and compare modes hide,
// except the international line, which stays over the imagery.
const OVER_IMAGERY = new Set(['country-line'])
// The Raised view hides the base layers that cannot move with the terrain (raisedLayers in relief.ts redraws
// the boundaries, roads, streams and the Mexico side from raised copies). The paper, the paper tint above zoom
// 10 and the lakes stay, and so do the drawings, which MapView feeds from their raised copy so each stays beside
// its raised pin (decision 0039).
const KEPT_IN_RAISED = new Set(['paper', 'relief-paper', 'lake', VIGNETTE_LAYERS.drawing, VIGNETTE_LAYERS.caption])

export const baseLayerIds = (style: StyleSpecification) => style.layers.map((l) => l.id).filter((id) => !OVER_IMAGERY.has(id))
export const notRaisedIds = (style: StyleSpecification) => style.layers.map((l) => l.id).filter((id) => !KEPT_IN_RAISED.has(id))

const byRank = (heavy: number, light: number): ExpressionSpecification =>
  ['interpolate', ['linear'], ['coalesce', ['get', 'scalerank'], 8], 2, heavy, 10, light]

// A creek of Strahler order `o` is drawn from this zoom on (creeks.MIN_ZOOM in tiles/creeks.py; order 7 and up from 7).
const creekShown: ExpressionSpecification = ['>=', ['zoom'], ['match', ['get', 'o'], 2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]]

// State names (tiles/state_labels.py): points placed where the lettering clears the story, each shown between its
// min_zoom and max_zoom: one per state zoomed out, a few spread over it closer in. Small capitals, widely spaced
// and faint, from zoom 5, fading out by 8.5. The size and spacing here are the ones tiles/state_labels.py measures with.
const STATE_ZOOMS = [5, 5.5, 6, 6.5, 7, 7.5, 8]
const stateName = (zoom: number): ExpressionSpecification =>
  ['case', ['all', ['<=', ['get', 'min_zoom'], zoom], ['>', ['get', 'max_zoom'], zoom]], ['get', 'name'], '']
const stateLabel = (source: string): LayerSpecification => ({
  id: 'state-label',
  type: 'symbol',
  source,
  minzoom: 5,
  maxzoom: 8.5,
  layout: {
    'text-field': ['step', ['zoom'], stateName(5), ...STATE_ZOOMS.slice(1).flatMap((z) => [z, stateName(z)])] as ExpressionSpecification,
    'text-font': [fonts.smallCaps],
    'text-size': ['interpolate', ['linear'], ['zoom'], 5, 12, 8, 16],
    'text-letter-spacing': 0.6,
    'text-max-width': 40,
    'text-padding': 4,
  },
  paint: {
    'text-color': tokens.ink,
    'text-opacity': ['interpolate', ['linear'], ['zoom'], 7.5, 0.55, 8.5, 0],
    'text-halo-color': tokens.paper,
    'text-halo-width': 1,
  },
})

// The 15′ graticule (crossing.graticule), as on Wheeler's sheet 70A: faint ink from zoom 8, the whole degrees a
// little heavier, over the relief and the water and under all type. MapFrame labels it in the frame's margin.
const graticule: LayerSpecification = {
  id: 'graticule',
  type: 'line',
  source: 'graticule',
  minzoom: 8,
  paint: {
    'line-color': tokens.ink,
    'line-opacity': ['interpolate', ['linear'], ['zoom'], 8, 0.16, 12, 0.24],
    'line-width': ['interpolate', ['linear'], ['zoom'], 8, ['match', ['get', 'rank'], 1, 0.8, 0.5], 12, ['match', ['get', 'rank'], 1, 1.1, 0.7]],
  },
}

// The literary basemap (docs/design.md, section 5.1): ink on caliche paper, the
// Mexico side a shade darker, rivers in blue-grey ink, and a dash-dot
// international line as on the 1850s-1880s survey sheets.
export function literaryStyle(tilesBase: string, fontsBase: string, dataBase: string, units: Units): StyleSpecification {
  const base = 'base'
  // Label data made for the map beside the tiles (tiles.state_labels, crossing.graticule, crossing.pass_lines).
  const labels = `${tilesBase.replace(/tiles\/$/, '')}labels/`
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
        // Streams on both sides of the border (tiles/creeks.py): INEGI's in Mexico, NHD's in the US, each by its
        // Strahler order `o`, shown from the zoom that order earns, wider with order. Intermittent ones (`i`), nearly
        // all of them in this desert, are solid but lighter, so the few perennial streams stand out.
        id: 'creek',
        type: 'line',
        source: base,
        'source-layer': 'creek',
        minzoom: 7,
        filter: creekShown,
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': tokens.water,
          'line-width': ['interpolate', ['linear'], ['zoom'], 8, ['*', 0.15, ['get', 'o']], 12, ['+', 0.35, ['*', 0.22, ['get', 'o']]]],
          'line-opacity': ['case', ['has', 'i'], 0.65, 0.95],
        },
      },
      {
        id: 'river-minor',
        type: 'line',
        source: base,
        'source-layer': 'river_minor',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': tokens.water, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.4, 10, 0.9, 13, 1.3] },
      },
      {
        // Wider the more important the river (Natural Earth's scalerank, 0 the most), as the Wheeler sheets draw
        // a main river heavier than its tributaries.
        id: 'river',
        type: 'line',
        source: base,
        'source-layer': 'river',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': tokens.water, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, byRank(1.3, 0.7), 10, byRank(2.8, 1.4), 13, byRank(3.6, 1.8)] },
      },
      {
        // Over the rivers and creeks, and opaque, so a river ends at the shore instead of running through the
        // water, as on the survey sheets. Intermittent water bodies (`i`, INEGI's and NHD's) are lighter: often
        // a dry playa.
        id: 'lake',
        type: 'fill',
        source: base,
        'source-layer': 'lake',
        paint: { 'fill-color': ['case', ['has', 'i'], tokens.lakeDry, tokens.lake], 'fill-outline-color': tokens.water },
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
        minzoom: 11,
        // Only on the creeks drawn at this zoom. The Raised view reuses this filter on its own streams, which
        // carry no `o`, so they count as shown.
        filter: ['all', ['has', 'name'], ['any', ['!', ['has', 'o']], creekShown]],
        layout: {
          'symbol-placement': 'line',
          'text-field': ['get', 'name'],
          'text-font': [fonts.italic],
          'text-size': ['interpolate', ['linear'], ['zoom'], 11, 10.5, 12, 11.5],
          'text-letter-spacing': 0.04,
        },
        paint: { 'text-color': tokens.waterLabel, 'text-halo-color': tokens.paper, 'text-halo-width': 1.5 },
      },
      // River names follow a simplified, rounded copy of each river (river_label): the traced lines meander too
      // tightly for a name to fit along them.
      {
        id: 'river-minor-label',
        type: 'symbol',
        source: base,
        'source-layer': 'river_label',
        minzoom: 9,
        filter: ['==', ['get', 'rank'], 'minor'],
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
        'source-layer': 'river_label',
        minzoom: 7,
        filter: ['==', ['get', 'rank'], 'major'],
        // The main rivers in spaced roman capitals, as the Wheeler sheets letter PURGATORY RIVER: about one letter's
        // space between letters, once or twice along the river's general run.
        layout: {
          'symbol-placement': 'line',
          'text-field': ['upcase', ['get', 'name']],
          'text-font': [fonts.roman],
          'text-size': ['interpolate', ['linear'], ['zoom'], 7, 11, 10, 14, 12, 16],
          'text-letter-spacing': ['interpolate', ['linear'], ['zoom'], 7, 0.45, 11, 0.9],
          'text-max-angle': 30,
          'symbol-spacing': 500,
        },
        paint: { 'text-color': tokens.waterLabel, 'text-halo-color': tokens.paper, 'text-halo-width': 1.5 },
      },
    ]
  // Hillshade sits on the paper; hachures under the water and lines; the graticule over the lines; the water
  // places, glyphs, then vignettes, above the lines and below the labels. The water places are the lowest
  // symbols but for the context places under them, so every other name wins a collision with them.
  const at = (id: string) => layers.findIndex((l) => l.id === id)
  layers.splice(at('creek-label'), 0, graticule, contextPlaceLayer(tokens), waterPlaceLayer(tokens), ...r.glyphs, ...r.vignettes)
  layers.splice(at('county-line'), 0, ...r.hillshade)
  layers.splice(at('county-line'), 0, ...r.hachures)
  // Last of the base, so the story's labels (added above it) win any collision.
  layers.push(stateLabel('state-labels'))
  return {
    version: 8,
    glyphs: `${fontsBase}{fontstack}/{range}.pbf`,
    // The sprite sits beside the fonts in this build; the tiles may come from another build (setup.ts).
    sprite: `${fontsBase.replace(/fonts\/$/, '')}sprites/${SPRITE}`,
    sources: {
      [base]: { type: 'vector', url: `pmtiles://${tilesBase}base.pmtiles` },
      ...reliefSources(tilesBase, dataBase),
      'state-labels': { type: 'geojson', data: `${labels}states.geojson` },
      graticule: { type: 'geojson', data: `${labels}graticule.geojson` },
      passes: { type: 'geojson', data: `${labels}passes.geojson` },
      // The gazetteer's water places, trimmed by scripts/copy-data.mjs (waterPlaces.ts).
      'water-places': {
        type: 'geojson',
        data: `${dataBase}map/water_places.geojson`,
        attribution: 'Springs, ranches and stations: USGS GNIS, GeoNames (CC BY 4.0)',
      },
      // The gazetteer's other period places, trimmed the same way (contextPlaces.ts).
      'context-places': { type: 'geojson', data: `${dataBase}map/context_places.geojson` },
    },
    layers,
  }
}
