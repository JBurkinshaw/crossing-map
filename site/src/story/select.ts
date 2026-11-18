import type { Feature, Geometry, Point, Position } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import { corridor as corridorOf } from '../map/corridor'

// Pure lookups over the story data, shared by App's navigation (navigation.ts) and its tests.

export type StoryLayer = 'places' | 'stops' | 'areas' | 'journeys'
// A story feature under a click: a place, an area, or a route segment (with its journey and sequence). `edge` is
// set when the click fell on an area's edge strip rather than inside it.
export type MapPick = { layer: 'places' | 'areas' | 'journeys'; id: string; journey: string | null; sequence: number | null; edge?: boolean }
type StoryFeature = Feature<Geometry, StoryProps>

export function positions(g: Geometry): Position[] {
  if (g.type === 'Point') return [g.coordinates]
  if (g.type === 'LineString' || g.type === 'MultiPoint') return g.coordinates
  if (g.type === 'Polygon' || g.type === 'MultiLineString') return g.coordinates.flat()
  if (g.type === 'MultiPolygon') return g.coordinates.flat(2)
  return []
}

export function bounds(features: Feature[]): [number, number, number, number] {
  const all = features.flatMap((f) => positions(f.geometry))
  const lons = all.map((p) => p[0])
  const lats = all.map((p) => p[1])
  return [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)]
}

// A journey's stops in order.
export const journeyStops = (story: Story | null, journey: string) =>
  (story?.stops.features ?? [])
    .filter((f) => f.properties.journey === journey)
    .sort((a, b) => (a.properties.sequence ?? 0) - (b.properties.sequence ?? 0))

export const byId = (story: Story | null, layer: StoryLayer, id: string) =>
  (story?.[layer].features as StoryFeature[] | undefined)?.find((f) => f.properties.id === id)

// A stop worked out from clues has an area it could be anywhere in, built from the stop and named after it
// (crossing.build_story): stop j2-hacienda, area area-j2-hacienda.
const AREA_PREFIX = 'area-'
export const areaOfStop = (story: Story | null, stopId: string) => byId(story, 'areas', `${AREA_PREFIX}${stopId}`)
export const stopOfArea = (story: Story | null, areaId: string) =>
  areaId.startsWith(AREA_PREFIX) ? byId(story, 'stops', areaId.slice(AREA_PREFIX.length)) : undefined

// The journeys with a stop in the story, each with the episode of its first stop, in id order.
export function journeysOf(story: Story | null): { id: string; first_seen: string }[] {
  const first = new Map<string, string>()
  for (const f of story?.stops.features ?? []) {
    const { journey: id, first_seen } = f.properties
    if (id && (!first.has(id) || first_seen < first.get(id)!)) first.set(id, first_seen)
  }
  return [...first].map(([id, first_seen]) => ({ id, first_seen })).sort((a, b) => a.id.localeCompare(b.id))
}

// Talk on the road (design section 8): a route segment is named by the places at its two ends, or by its stops
// where a stop is not at a named place. Both ends are reached once the segment is (spoiler/filter.ts).
export function roadLabel(story: Story | null, segment: StoryFeature): string {
  const end = (sequence: number | null) => {
    const stop = (story?.stops.features ?? []).find((s) => s.properties.journey === segment.properties.journey && s.properties.sequence === sequence)
    const place = stop?.properties.place_ref ? byId(story, 'places', stop.properties.place_ref) : undefined
    return place?.properties.name ?? stop?.properties.name
  }
  const seq = segment.properties.sequence
  const [from, to] = [end(seq), end(seq === null ? null : seq + 1)]
  return from && to ? `On the road between ${from} and ${to}` : segment.properties.name
}

// The bounds of a segment's corridor, else of the segment.
export function corridorBounds(f: StoryFeature) {
  const area = corridorOf(f.geometry)
  return bounds(area ? [{ type: 'Feature', geometry: area, properties: {} }] : [f])
}

// How far (km) a stop may sit from its place's pin and still stand at the same spot.
const SAME_SPOT_KM = 1

// The places whose pin stands apart from every stop at it, as a range's gazetteer point does from a pass on its
// flank (decision 0029). Such a pin is drawn and named but does not open its stops: the stop's own marker does.
export function pinsApart(story: Story): Set<string> {
  const near = new Set<string>()
  const referenced = new Set<string>()
  const pins = new Map(story.places.features.map((f) => [f.properties.id, f.geometry.coordinates]))
  for (const s of story.stops.features) {
    const ref = s.properties.place_ref
    const pin = ref ? pins.get(ref) : undefined
    if (!ref || !pin) continue
    referenced.add(ref)
    const [x, y] = s.geometry.coordinates
    const km = 111.32 * Math.hypot((x - pin[0]) * Math.cos((y * Math.PI) / 180), y - pin[1])
    if (km <= SAME_SPOT_KM) near.add(ref)
  }
  return new Set([...referenced].filter((id) => !near.has(id)))
}

// What a click on the map opens. A route or a place where a journey stops goes to that stop: in the journey in
// focus if it is one of the journeys there (several can share a road or a town), else in the journey of the
// topmost route clicked, else the first journey that stops there. On a route, the stop is the end of the clicked
// segment nearer the click. Any other place or area opens its card; a click on empty map clears the pick.
// An area's size, for ranking only: square degrees of longitude shrunk by the cosine of the latitude, so roughly
// proportional to its true area at this map's latitudes.
function size(g: Geometry): number {
  const ring = (r: Position[]) => {
    const k = Math.cos(((r[0]?.[1] ?? 0) * Math.PI) / 180)
    let sum = 0
    for (let i = 1; i < r.length; i++) sum += (r[i - 1][0] - r[i][0]) * k * (r[i - 1][1] + r[i][1])
    return Math.abs(sum) / 2
  }
  const polygon = (p: Position[][]) => ring(p[0] ?? []) - p.slice(1).reduce((t, h) => t + ring(h), 0)
  if (g.type === 'Polygon') return polygon(g.coordinates)
  if (g.type === 'MultiPolygon') return g.coordinates.reduce((t, p) => t + polygon(p), 0)
  return Infinity
}

// Which of the areas under a click opens (decision 0049): an edge before an inside, so any outline can be
// picked; then an area of the journey in focus, the ones drawn strongly; then the smallest, the most specific.
// Regions have no journey and are the largest, so an inferred area inside one always wins over it.
export function areaPick(picks: MapPick[], story: Story | null, journey: string): MapPick | undefined {
  const sizeOf = (id: string) => {
    const f = byId(story, 'areas', id)
    return f ? size(f.geometry) : Infinity
  }
  const rank = (p: MapPick): [number, number, number] => [p.edge ? 0 : 1, p.journey === journey ? 0 : 1, sizeOf(p.id)]
  return picks
    .filter((p) => p.layer === 'areas')
    .sort((a, b) => {
      const [x, y] = [rank(a), rank(b)]
      return x[0] - y[0] || x[1] - y[1] || x[2] - y[2]
    })[0]
}

export type ClickResult =
  | { kind: 'step'; index: number }
  | { kind: 'stop'; id: string }
  | { kind: 'select'; layer: 'places' | 'areas'; id: string }
  | { kind: 'clear' }

export function clickResult(
  picks: MapPick[],
  [lng, lat]: [number, number],
  story: Story | null,
  journey: string,
  stops: Feature<Point, StoryProps>[],
  stopIndex: number,
): ClickResult {
  const top = picks[0]
  const all = (story?.stops.features ?? []) as Feature<Point, StoryProps>[]
  const stopAt = (j: string | null, sequence: number | null) =>
    all.find((s) => s.properties.journey === j && s.properties.sequence === sequence)
  const far = (s: Feature<Point, StoryProps>) => {
    const [x, y] = s.geometry.coordinates
    return ((x - lng) * Math.cos((lat * Math.PI) / 180)) ** 2 + (y - lat) ** 2
  }
  let candidates: Feature<Point, StoryProps>[] = []
  if (top?.layer === 'journeys') {
    for (const p of picks.filter((x) => x.layer === 'journeys')) {
      const ends = [stopAt(p.journey, p.sequence), stopAt(p.journey, p.sequence === null ? null : p.sequence + 1)]
      const near = ends.filter((s) => s !== undefined).sort((a, b) => far(a) - far(b))[0]
      if (near) candidates.push(near)
    }
  } else if (top?.layer === 'places') {
    // In the order of the routes under the click, then of the journeys.
    const order = picks.filter((x) => x.layer === 'journeys').map((x) => x.journey)
    const rank = (s: Feature<Point, StoryProps>) => {
      const at = order.indexOf(s.properties.journey)
      return at < 0 ? order.length : at
    }
    candidates = all
      .filter((s) => s.properties.place_ref === top.id)
      .sort((a, b) => rank(a) - rank(b) || (a.properties.journey ?? '').localeCompare(b.properties.journey ?? ''))
  }
  const here = candidates.filter((s) => s.properties.journey === journey)
  if (here.length > 0) {
    // A journey that comes back to a place stops there more than once: the visit nearest the current stop.
    const index = (s: Feature<Point, StoryProps>) => stops.findIndex((x) => x.properties.id === s.properties.id)
    return { kind: 'step', index: here.map(index).sort((a, b) => Math.abs(a - stopIndex) - Math.abs(b - stopIndex))[0] }
  }
  if (candidates.length > 0) return { kind: 'stop', id: candidates[0].properties.id }
  if (top?.layer === 'areas') return { kind: 'select', layer: 'areas', id: areaPick(picks, story, journey)!.id }
  return top && top.layer !== 'journeys' ? { kind: 'select', layer: top.layer, id: top.id } : { kind: 'clear' }
}
