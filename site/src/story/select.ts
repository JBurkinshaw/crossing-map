import type { Feature, Geometry, Point, Position } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import { corridor as corridorOf } from '../map/corridor'

// Pure lookups over the story data, shared by App's navigation (navigation.ts) and its tests.

export type StoryLayer = 'places' | 'stops' | 'areas' | 'journeys'
// A story feature under a click: a place, an area, or a route segment (with its journey and sequence).
export type MapPick = { layer: 'places' | 'areas' | 'journeys'; id: string; journey: string | null; sequence: number | null }
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

// What a click on the map opens. A route or a place where a journey stops goes to that stop: in the journey in
// focus if it is one of the journeys there (several can share a road or a town), else in the journey of the
// topmost route clicked, else the first journey that stops there. On a route, the stop is the end of the clicked
// segment nearer the click. Any other place or area opens its card; a click on empty map clears the pick.
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
  return top && top.layer !== 'journeys' ? { kind: 'select', layer: top.layer, id: top.id } : { kind: 'clear' }
}
