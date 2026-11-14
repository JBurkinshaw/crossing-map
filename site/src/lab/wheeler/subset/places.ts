import type { ExpressionSpecification, LayerSpecification, Map as MapLibreMap, MapStyleImageMissingEvent, StyleSpecification } from 'maplibre-gl'
import { fonts, palette } from '../../../map/tokens'

// Two Wheeler cards for the lab's test area (review/stage-9/wheeler-places/README.md): springs, tanks, ranches and
// stations as quiet named places (Wheeler finding 13), and a 15′ graticule in faint ink (finding 16). The data are
// small GeoJSON files made by crossing.water_places and crossing.graticule.

export type PlacesParams = {
  // Springs, wells, tanks, ranches and stations in the test area, from zoom 11.
  water: boolean
  // The 15′ graticule from zoom 8, with the frame and its margin labels (Frame.tsx).
  graticule: boolean
  // Graticule labels set along the lines on the map, as well as (or instead of) in the frame's margin.
  lineLabels: boolean
  // The last episode read: features first seen later are hidden ('9-99' shows all).
  reached: string
}

export const PLACES_OFF: PlacesParams = { water: false, graticule: false, lineLabels: false, reached: '9-99' }
export const PLACES_ON: PlacesParams = { water: true, graticule: true, lineLabels: false, reached: '9-99' }

// Reading positions for the lab's slider: before the book, every episode id the schema allows, and the end.
// Ids sort as strings in reading order (site/src/spoiler/progress.ts), so a string comparison filters them.
export const READING: string[] = [
  '0-00',
  ...[1, 2, 3, 4].flatMap((part) => Array.from({ length: 14 }, (_, i) => `${part}-${String(i + 1).padStart(2, '0')}`)),
  '9-99',
]

const lab = (file: string) => new URL(`${import.meta.env.BASE_URL}lab/wheeler/${file}`, window.location.origin).href

// The symbol per kind, after Wheeler: a ring for a spring, a dot for a well, a ringed dot for a tank, a small solid
// square for a ranch and an open one for a station. Water in the water ink, buildings in the type's ink.
type Mark = 'ring' | 'dot' | 'ringdot' | 'square' | 'open-square'
const MARK: Record<string, Mark> = { spring: 'ring', well: 'dot', tank: 'ringdot', ranch: 'square', station: 'open-square' }
const MARK_INK: Record<Mark, string> = { ring: palette.water, dot: palette.water, ringdot: palette.water, square: palette.ink, 'open-square': palette.ink }
const MARK_PX = 8
const MARK_RATIO = 2

function drawMark(mark: Mark): ImageData {
  const n = MARK_PX * MARK_RATIO
  const ctx = new OffscreenCanvas(n, n).getContext('2d')!
  ctx.scale(MARK_RATIO, MARK_RATIO)
  ctx.strokeStyle = ctx.fillStyle = MARK_INK[mark]
  ctx.lineWidth = 1.3
  const c = MARK_PX / 2
  if (mark === 'ring' || mark === 'ringdot') {
    ctx.beginPath()
    ctx.arc(c, c, c - 0.8, 0, 2 * Math.PI)
    ctx.stroke()
  }
  if (mark === 'dot' || mark === 'ringdot') {
    ctx.beginPath()
    ctx.arc(c, c, mark === 'dot' ? 2.2 : 1.1, 0, 2 * Math.PI)
    ctx.fill()
  }
  if (mark === 'square') ctx.fillRect(1.5, 1.5, MARK_PX - 3, MARK_PX - 3)
  if (mark === 'open-square') ctx.strokeRect(1.3, 1.3, MARK_PX - 2.6, MARK_PX - 2.6)
  return ctx.getImageData(0, 0, n, n)
}

// The marks are drawn in code, so they need no sprite art. They are added as each style loads: added only on
// `styleimagemissing`, tiles laid out before the image arrived kept their names without the mark or its offset.
export function addPlaceMarks(map: MapLibreMap) {
  const add = (mark: Mark) => {
    if (!map.hasImage(`wp-${mark}`)) map.addImage(`wp-${mark}`, drawMark(mark), { pixelRatio: MARK_RATIO })
  }
  const addAll = () => (Object.keys(MARK_INK) as Mark[]).forEach(add)
  map.on('style.load', addAll)
  map.on('styleimagemissing', (e: MapStyleImageMissingEvent) => {
    const mark = e.id.slice(3) as Mark
    if (e.id.startsWith('wp-') && mark in MARK_INK) add(mark)
  })
}

const upTo = (reached: string): ExpressionSpecification => ['<=', ['to-string', ['get', 'first_seen']], reached]

// The shared type scale: ranches, stations, springs and tanks at about 10 px italic at zoom 11, in the one ink at
// lower opacity, growing a pixel a zoom like the site's labels.
function waterLayers(p: PlacesParams, halo: string): LayerSpecification[] {
  const filter = upTo(p.reached)
  return [
    {
      id: 'wp-place',
      type: 'symbol',
      source: 'wp-water',
      minzoom: 11,
      filter,
      layout: {
        'icon-image': ['concat', 'wp-', ['match', ['get', 'kind'], ...Object.entries(MARK).flat(), 'ring']] as unknown as ExpressionSpecification,
        'icon-allow-overlap': true,
        'icon-ignore-placement': true,
        'text-field': ['get', 'name'],
        'text-font': [fonts.italic],
        'text-size': ['interpolate', ['linear'], ['zoom'], 11, 10, 13, 12],
        'text-variable-anchor': ['left', 'right', 'top', 'bottom'],
        'text-radial-offset': 0.7,
        'text-justify': 'auto',
        'text-max-width': 8,
        'text-optional': true,
        'text-padding': 3,
      },
      paint: { 'text-color': palette.ink, 'text-opacity': 0.72, 'text-halo-color': halo, 'text-halo-width': 1.2, 'icon-opacity': 0.9 },
    },
  ]
}

// The graticule in faint ink: whole degrees a little heavier than the quarters, as on sheet 70A.
function graticuleLayers(p: PlacesParams, halo: string): LayerSpecification[] {
  const layers: LayerSpecification[] = [
    {
      id: 'wp-graticule',
      type: 'line',
      source: 'wp-graticule',
      minzoom: 8,
      paint: {
        'line-color': palette.ink,
        'line-opacity': ['interpolate', ['linear'], ['zoom'], 8, 0.16, 12, 0.24],
        'line-width': ['interpolate', ['linear'], ['zoom'], 8, ['match', ['get', 'rank'], 1, 0.8, 0.5], 12, ['match', ['get', 'rank'], 1, 1.1, 0.7]],
      },
    },
  ]
  if (p.lineLabels) {
    layers.push({
      id: 'wp-graticule-label',
      type: 'symbol',
      source: 'wp-graticule',
      minzoom: 8,
      layout: {
        'symbol-placement': 'line',
        'symbol-spacing': 700,
        'text-field': ['get', 'label'],
        'text-font': [fonts.italic],
        'text-size': 9.5,
        'text-keep-upright': true,
        'text-padding': 2,
      },
      paint: { 'text-color': palette.ink, 'text-opacity': 0.55, 'text-halo-color': halo, 'text-halo-width': 1 },
    })
  }
  return layers
}

// Adds the cards' sources and layers to a style. Everything goes under the base's first symbol layer: the
// graticule lies over the relief and the water but under all type, and the place names are placed last, so
// summit names and river names win a collision.
export function addPlaces(style: StyleSpecification, p: PlacesParams, halo: string): StyleSpecification {
  if (!p.water && !p.graticule) return style
  const ours = [...(p.graticule ? graticuleLayers(p, halo) : []), ...(p.water ? waterLayers(p, halo) : [])]
  const at = style.layers.findIndex((l) => l.type === 'symbol')
  const layers = at < 0 ? [...style.layers, ...ours] : [...style.layers.slice(0, at), ...ours, ...style.layers.slice(at)]
  return {
    ...style,
    sources: {
      ...style.sources,
      'wp-water': { type: 'geojson', data: lab('water-places.geojson'), attribution: 'Springs and ranches: USGS GNIS (public domain), GeoNames (CC BY 4.0)' },
      'wp-graticule': { type: 'geojson', data: lab('graticule.geojson') },
    },
    layers,
  }
}
