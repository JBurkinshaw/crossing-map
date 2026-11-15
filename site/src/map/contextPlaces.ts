import type { ExpressionSpecification, LayerSpecification } from 'maplibre-gl'
import { fonts, QUIET_OPACITY, typeScale, zoomedSize, type Palette } from './tokens'

// The period places the Wheeler sheets would name beside the waters (forts, ghost towns, mines, sawmills,
// churches, cemeteries, schools, post offices, corrals, camps, wells and windmills) and the dry lakes and flats,
// as quiet names along the journeys (data/context_places.geojson, crossing.context_places, decision 0028; trimmed
// by scripts/copy-data.mjs). Each kind has a tiny mark drawn in code, after Wheeler's manner; lakes, flats and the
// railway's name are names only. waterPlaces.ts registers the marks with its own.

type Draw = (ctx: CanvasRenderingContext2D) => void
const PX = 8
const RATIO = 2
const line = (ctx: CanvasRenderingContext2D, ...xy: number[]) => {
  ctx.beginPath()
  ctx.moveTo(xy[0], xy[1])
  for (let i = 2; i < xy.length; i += 2) ctx.lineTo(xy[i], xy[i + 1])
  ctx.stroke()
}
const openSquare: Draw = (ctx) => ctx.strokeRect(2, 2, 4, 4)
const cross: Draw = (ctx) => {
  line(ctx, 4, 0.8, 4, 7.2)
  line(ctx, 2, 2.8, 6, 2.8)
}

// Mark name -> how to draw it. Wheeler's own: a flag for a fort, crossed picks for a mine, a cross for a church,
// a small open square for a ruin or an abandoned place. The rest are simple marks in the same spirit.
const MARKS: Record<string, { draw: Draw; water?: boolean }> = {
  flag: {
    draw: (ctx) => {
      line(ctx, 2, 7.5, 2, 0.6)
      ctx.beginPath()
      ctx.moveTo(2, 0.6)
      ctx.lineTo(7, 2)
      ctx.lineTo(2, 3.6)
      ctx.fill()
    },
  },
  picks: {
    draw: (ctx) => {
      line(ctx, 1.5, 6.5, 6.5, 1.5)
      line(ctx, 1.5, 1.5, 6.5, 6.5)
      line(ctx, 4.8, 0.8, 7.2, 3.2)
      line(ctx, 0.8, 3.2, 3.2, 0.8)
    },
  },
  cross: { draw: cross },
  // A cemetery's cross stands on a short ground line.
  grave: {
    draw: (ctx) => {
      line(ctx, 4, 1, 4, 6.5)
      line(ctx, 2.5, 2.8, 5.5, 2.8)
      line(ctx, 1.5, 6.8, 6.5, 6.8)
    },
  },
  ruin: { draw: openSquare },
  // A sawblade: a short row of teeth on its back.
  saw: { draw: (ctx) => line(ctx, 0.8, 3, 7.2, 3, 7.2, 4, 6, 5.6, 4.8, 4, 3.6, 5.6, 2.4, 4, 1.2, 5.6, 0.8, 4, 0.8, 3) },
  ring: { draw: (ctx) => (ctx.beginPath(), ctx.arc(4, 4, 2.2, 0, 2 * Math.PI), ctx.stroke()) },
  dot: { draw: (ctx) => (ctx.beginPath(), ctx.arc(4, 4, 1.5, 0, 2 * Math.PI), ctx.fill()) },
  square: { draw: (ctx) => ctx.fillRect(1.5, 1.5, 5, 5) },
  station: { draw: (ctx) => ctx.strokeRect(1.3, 1.3, 5.4, 5.4) },
  tent: { draw: (ctx) => line(ctx, 1, 6.5, 4, 1.5, 7, 6.5, 1, 6.5) },
  // A railway tunnel: its two portals, as brackets facing out, a little heavier than the rest so they read over
  // the hachures of the mountains tunnels go through.
  tunnel: {
    draw: (ctx) => {
      ctx.lineWidth = 1.4
      line(ctx, 1, 1, 2.6, 1, 2.6, 7, 1, 7)
      line(ctx, 7, 1, 5.4, 1, 5.4, 7, 7, 7)
    },
  },
  well: { water: true, draw: (ctx) => (ctx.beginPath(), ctx.arc(4, 4, 2, 0, 2 * Math.PI), ctx.fill()) },
  // A windmill: the well's dot with four short sails.
  windmill: {
    water: true,
    draw: (ctx) => {
      ctx.beginPath()
      ctx.arc(4, 4, 1.2, 0, 2 * Math.PI)
      ctx.fill()
      line(ctx, 1, 1, 7, 7)
      line(ctx, 7, 1, 1, 7)
    },
  },
}

// Kind -> mark; a kind with none is set as a name only.
const KIND_MARK: Record<string, string> = {
  military: 'flag',
  mine: 'picks',
  church: 'cross',
  cemetery: 'grave',
  abandoned: 'ruin',
  ruin: 'ruin',
  sawmill: 'saw',
  corral: 'ring',
  school: 'dot',
  'post-office': 'dot',
  customs: 'dot',
  ranch: 'square',
  station: 'station',
  camp: 'tent',
  tunnel: 'tunnel',
  well: 'well',
  windmill: 'windmill',
}
// Names only: the dry lakes and flats (soon drawn as shapes), the railway's name, and no name for a tunnel.
const NAME_ONLY = ['lake', 'flat', 'railway']
// The order in which the names win collisions among themselves: the rarest, most telling, first.
const SORT = ['military', 'abandoned', 'ruin', 'lake', 'flat', 'station', 'post-office', 'sawmill', 'customs', 'railway', 'church', 'cemetery', 'school']

export const contextImageId = (mark: string) => `context-${mark}`
export const CONTEXT_IMAGE_IDS = Object.keys(MARKS).map(contextImageId)

export function drawContextMark(id: string, p: Palette): ImageData {
  const mark = MARKS[id.replace(/^context-/, '')]
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = PX * RATIO
  const ctx = canvas.getContext('2d')!
  ctx.scale(RATIO, RATIO)
  ctx.strokeStyle = ctx.fillStyle = mark.water ? p.water : p.ink
  ctx.lineWidth = 1
  mark.draw(ctx)
  return ctx.getImageData(0, 0, PX * RATIO, PX * RATIO)
}
export const CONTEXT_PIXEL_RATIO = RATIO

// Below the water places, so every other label wins a collision with these; marks give way too, so a dense mining
// district thins out rather than piling up. The reading filter is added by spoiler/filter.ts (PROGRESS_LAYERS).
export function contextPlaceLayer(p: Palette): LayerSpecification {
  const kind = ['get', 'kind'] as unknown as ExpressionSpecification
  return {
    id: 'context-place',
    type: 'symbol',
    source: 'context-places',
    minzoom: 11,
    layout: {
      'icon-image': ['match', kind, ...Object.entries(KIND_MARK).flatMap(([k, m]) => [k, contextImageId(m)]), ''] as unknown as ExpressionSpecification,
      'icon-optional': true,
      'symbol-sort-key': ['match', kind, ...SORT.flatMap((k, i) => [k, i]), SORT.length] as unknown as ExpressionSpecification,
      // A tunnel is a mark on the railway, with no name.
      'text-field': ['match', kind, 'tunnel', '', ['get', 'name']] as unknown as ExpressionSpecification,
      'text-font': [fonts.italic],
      'text-size': zoomedSize(typeScale.quiet),
      'text-variable-anchor': ['left', 'right', 'top', 'bottom'],
      // A name with no mark sits on its point.
      'text-radial-offset': ['match', kind, NAME_ONLY, 0, 0.7] as unknown as ExpressionSpecification,
      'text-justify': 'auto',
      'text-max-width': 8,
      'text-optional': true,
      'text-padding': 3,
    },
    paint: {
      'text-color': ['match', kind, 'lake', p.waterLabel, p.ink] as unknown as ExpressionSpecification,
      'text-opacity': QUIET_OPACITY,
      'text-halo-color': p.paperShown,
      'text-halo-width': 1.2,
      'icon-opacity': 0.8,
    },
  }
}
