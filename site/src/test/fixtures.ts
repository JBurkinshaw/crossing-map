import type { Feature, FeatureCollection, Geometry, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'

// A small story for unit tests: two journeys sharing a town, with route segments between their stops.
const props = (p: Partial<StoryProps> & { id: string }): StoryProps => ({
  name: p.id,
  journey: null,
  sequence: null,
  certainty: 'located',
  uncertainty_m: null,
  source: 'test',
  source_id: null,
  first_seen: '1-01',
  note_safe: '',
  reasoning: null,
  ...p,
})
const point = (lon: number, lat: number, p: Partial<StoryProps> & { id: string }): Feature<Point, StoryProps> => ({
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [lon, lat] },
  properties: props(p),
})
const line = (coords: [number, number][], p: Partial<StoryProps> & { id: string }): Feature<Geometry, StoryProps> => ({
  type: 'Feature',
  geometry: { type: 'LineString', coordinates: coords },
  properties: props(p),
})
const fc = <G extends Geometry>(features: Feature<G, StoryProps>[]): FeatureCollection<G, StoryProps> => ({ type: 'FeatureCollection', features })

export function story(): Story {
  return {
    places: fc([
      point(0, 0, { id: 'town', name: 'Town', role: 'stop', first_seen: '1-01' }),
      point(1, 0, { id: 'ranch', name: 'Ranch', role: 'stop', first_seen: '1-02' }),
      point(5, 5, { id: 'village', name: 'Village', role: 'context', first_seen: '4-01' }),
    ]),
    stops: fc([
      point(0, 0, { id: 'j1-1', name: 'At town', journey: 'J1', sequence: 1, place_ref: 'town', first_seen: '1-01', episode: '1-01' }),
      point(1, 0, { id: 'j1-2', name: 'At ranch', journey: 'J1', sequence: 2, place_ref: 'ranch', first_seen: '1-02', episode: '1-02' }),
      point(2, 0, { id: 'j1-3', name: 'Camp', journey: 'J1', sequence: 3, first_seen: '2-01', episode: '2-01' }),
      point(0, 0, { id: 'j2-1', name: 'Back at town', journey: 'J2', sequence: 1, place_ref: 'town', first_seen: '2-02', episode: '2-02' }),
    ]),
    areas: fc([]),
    journeys: fc([
      line([[0, 0], [1, 0]], { id: 'j1-s1', name: 'J1 1', journey: 'J1', sequence: 1, first_seen: '1-02' }),
      line([[1, 0], [2, 0]], { id: 'j1-s2', name: 'J1 2', journey: 'J1', sequence: 2, first_seen: '2-01' }),
    ]),
  }
}
