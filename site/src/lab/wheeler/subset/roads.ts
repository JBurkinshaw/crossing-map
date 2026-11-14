import type { ExpressionSpecification, FilterSpecification, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { fonts } from '../../../map/tokens'

// The Wheeler card "Roads with their mileages" for the test area (review/stage-9/wheeler-roads/README.md): wagon
// roads and trails traced by hand from the USGS 1918 Cienega Springs and Animas Peak sheets, and the NPS
// Butterfield trail, in pipeline/seeds/roads/test-area.geojson (copied to site/public/lab/wheeler/). After the
// Wheeler sheets: a wagon road is a fine single line, a trail a dashed one, the name in small italic along the line,
// and the distance the book gives written on the line itself ("9 m."), as Wheeler writes 13.5 m. between stations.

const DATA = `${import.meta.env.BASE_URL}lab/wheeler/roads-test-area.geojson`

// The test area of the 14 November 2026 brief. Today's Natural Earth roads are hidden inside it, so the traced
// network is not drawn over a modern one; outside it they stay as the site draws them.
const TEST_AREA = {
  type: 'Polygon',
  coordinates: [[[-109.6, 30.5], [-108.4, 30.5], [-108.4, 31.6], [-109.6, 31.6], [-109.6, 30.5]]],
} as const

// Lines and multi-lines (the clipped Butterfield trail); the points carry the mileages.
const isLine: ExpressionSpecification = ['!=', ['geometry-type'], 'Point']
const isTrail: ExpressionSpecification = ['==', ['get', 'class'], 'trail']
// The shared type scale's sizes are set at zoom 11 and scale with zoom as the site's labels do (about 1 px a zoom).
const atZoom = (z11: number): ExpressionSpecification => ['interpolate', ['linear'], ['zoom'], 9, z11 - 1.5, 11, z11, 13, z11 + 2]

function layers(halo: string, ink: string): { lines: LayerSpecification[]; labels: LayerSpecification[] } {
  const line = (id: string, filter: FilterSpecification, dash?: number[]): LayerSpecification => ({
    id,
    type: 'line',
    source: 'wheeler-roads',
    minzoom: 8,
    filter,
    layout: { 'line-join': 'round', 'line-cap': dash ? 'butt' : 'round' },
    paint: {
      'line-color': ink,
      'line-opacity': 0.85,
      // Wheeler's roads are a hairline beside the rivers: about 0.1 mm on the sheet, so under 1 px at zoom 10.
      'line-width': ['interpolate', ['linear'], ['zoom'], 8, 0.5, 11, 0.9, 13, 1.3],
      ...(dash ? { 'line-dasharray': dash } : {}),
    },
  })
  return {
    lines: [line('wheeler-road-wagon', ['all', isLine, ['!', isTrail]]), line('wheeler-road-trail', ['all', isLine, isTrail], [4, 2.5])],
    labels: [
      {
        // The distance the book gives, at the middle of the stretch it measures and turned to the line, with a halo
        // that breaks the line around it. The point and its angle come from the seed script, because a GeoJSON
        // source cuts lines at tile edges and line-center placement would letter every piece.
        id: 'wheeler-road-mileage',
        type: 'symbol',
        source: 'wheeler-roads',
        minzoom: 10,
        filter: ['all', ['==', ['geometry-type'], 'Point'], ['has', 'mileage']],
        layout: {
          'text-field': ['get', 'mileage'],
          'text-font': [fonts.italic],
          'text-size': atZoom(9.5),
          'text-rotate': ['get', 'angle'],
          'text-rotation-alignment': 'map',
          'text-allow-overlap': true,
        },
        paint: { 'text-color': ink, 'text-halo-color': halo, 'text-halo-width': 2 },
      },
      {
        // The name printed on the sheet, or the one the book uses (no 1918 sheet names these roads), in small
        // italic beside the line, the size of the ranch and spring names in the shared scale.
        id: 'wheeler-road-name',
        type: 'symbol',
        source: 'wheeler-roads',
        minzoom: 10,
        filter: ['all', isLine, ['any', ['has', 'name'], ['has', 'book_name']]],
        layout: {
          'symbol-placement': 'line',
          'symbol-spacing': 420,
          'text-field': ['coalesce', ['get', 'name'], ['get', 'book_name']],
          'text-font': [fonts.italic],
          'text-size': atZoom(10),
          'text-letter-spacing': 0.04,
          'text-offset': [0, -0.75],
          'text-max-angle': 30,
          'text-keep-upright': true,
        },
        paint: { 'text-color': ink, 'text-opacity': 0.85, 'text-halo-color': halo, 'text-halo-width': 1.2 },
      },
    ],
  }
}

// Adds the historic roads to a style: the lines just above today's roads, the labels just under the summit
// glyphs (as the other lab labels are), and a filter that hides today's roads inside the test area. The filter
// tests each tile's piece of a road, so a road crossing the edge is cut at the nearest tile edge, not exactly at
// the box.
export function historicRoads(style: StyleSpecification, halo: string, ink: string): StyleSpecification {
  const { lines, labels } = layers(halo, ink)
  const outside: FilterSpecification = ['!', ['within', TEST_AREA as unknown as GeoJSON.Polygon]]
  const out: LayerSpecification[] = []
  for (const layer of style.layers) {
    if (layer.id === 'mountain-glyph') out.push(...labels)
    if (layer.id === 'road') {
      out.push({ ...layer, filter: 'filter' in layer && layer.filter ? ['all', layer.filter, outside] : outside } as LayerSpecification, ...lines)
      continue
    }
    out.push(layer)
  }
  return { ...style, sources: { ...style.sources, 'wheeler-roads': { type: 'geojson', data: DATA } }, layers: out }
}
