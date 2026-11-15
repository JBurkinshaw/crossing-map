import type { ExpressionSpecification, LayerSpecification, Map as MapLibreMap, MapStyleImageMissingEvent } from 'maplibre-gl'
import { fonts, QUIET_OPACITY, typeScale, zoomedSize, type Palette } from './tokens'

// Springs, wells, tanks, ranches and stations as quiet named places, after the Wheeler sheets, which name every
// water and every station because in dry country they are where a rider goes (review/stage-8/wheeler/README.md,
// finding 13). The data are the gazetteer's points in the journeys corridor (data/water_places.geojson, trimmed by
// scripts/copy-data.mjs: the book's own springs and ranches are drawn by the story layers). Each has a small mark
// for its kind, drawn in code, and its name in small italic from zoom 11.

type Mark = 'ring' | 'dot' | 'ringdot' | 'square' | 'open-square'
// After Wheeler: a ring for a spring, a dot for a well, a ringed dot for a tank, a small solid square for a ranch
// and an open one for a station.
const MARK: Record<string, Mark> = { spring: 'ring', well: 'dot', tank: 'ringdot', ranch: 'square', station: 'open-square' }
const WATER_MARKS = new Set<Mark>(['ring', 'dot', 'ringdot'])
const MARK_PX = 8
const MARK_RATIO = 2
const imageId = (mark: Mark) => `water-${mark}`

// Water marks in the water's ink, buildings in the type's.
function drawMark(mark: Mark, p: Palette): ImageData {
  const n = MARK_PX * MARK_RATIO
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = n
  const ctx = canvas.getContext('2d')!
  ctx.scale(MARK_RATIO, MARK_RATIO)
  ctx.strokeStyle = ctx.fillStyle = WATER_MARKS.has(mark) ? p.water : p.ink
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

function addMarks(map: MapLibreMap, p: Palette, only?: string) {
  for (const mark of Object.values(MARK)) {
    const id = imageId(mark)
    if ((!only || only === id) && !map.hasImage(id)) map.addImage(id, drawMark(mark, p), { pixelRatio: MARK_RATIO })
  }
}

// Adds the marks to a map as soon as it exists, before any tile is laid out: a symbol laid out without its image
// keeps its name but not its mark until the tile reloads. A style image found missing later is added on demand.
// Returns the function that stops listening. WaterMarks.tsx does the same for a react-maplibre Map.
export function addWaterMarks(map: MapLibreMap, p: Palette): () => void {
  addMarks(map, p)
  const missing = (e: MapStyleImageMissingEvent) => addMarks(map, p, e.id)
  map.on('styleimagemissing', missing)
  return () => map.off('styleimagemissing', missing)
}

// The layer: under every other label, so summit, river and story names win a collision; the mark stays when its
// name gives way. The reading filter is added by spoiler/filter.ts (PROGRESS_LAYERS).
export function waterPlaceLayer(p: Palette): LayerSpecification {
  return {
    id: 'water-place',
    type: 'symbol',
    source: 'water-places',
    minzoom: 11,
    layout: {
      'icon-image': ['concat', 'water-', ['match', ['get', 'kind'], ...Object.entries(MARK).flat(), 'ring']] as unknown as ExpressionSpecification,
      'icon-allow-overlap': true,
      'icon-ignore-placement': true,
      'text-field': ['get', 'name'],
      'text-font': [fonts.italic],
      'text-size': zoomedSize(typeScale.quiet),
      'text-variable-anchor': ['left', 'right', 'top', 'bottom'],
      'text-radial-offset': 0.7,
      'text-justify': 'auto',
      'text-max-width': 8,
      'text-optional': true,
      'text-padding': 3,
    },
    paint: { 'text-color': p.ink, 'text-opacity': QUIET_OPACITY, 'text-halo-color': p.paperShown, 'text-halo-width': 1.2, 'icon-opacity': 0.9 },
  }
}
