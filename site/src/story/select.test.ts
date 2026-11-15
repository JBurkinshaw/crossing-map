import { describe, expect, it } from 'vitest'
import type { Feature, Geometry, Point } from 'geojson'
import type { StoryProps } from '../data/story'
import { story } from '../test/fixtures'
import { bounds, clickResult, journeysOf, journeyStops, pinsApart, roadLabel, type MapPick } from './select'

const pick = (layer: MapPick['layer'], id: string, journey: string | null = null, sequence: number | null = null): MapPick => ({
  layer,
  id,
  journey,
  sequence,
})

describe('journeys', () => {
  it('lists each journey once, with the episode of its first stop', () => {
    expect(journeysOf(story())).toEqual([
      { id: 'J1', first_seen: '1-01' },
      { id: 'J2', first_seen: '2-02' },
    ])
  })
  it('orders a journey’s stops by sequence', () => {
    const s = story()
    s.stops.features.reverse()
    expect(journeyStops(s, 'J1').map((f) => f.properties.id)).toEqual(['j1-1', 'j1-2', 'j1-3'])
  })
})

describe('roadLabel', () => {
  it('names a segment by the places at its ends, or its stops', () => {
    const s = story()
    const [first, second] = s.journeys.features as Feature<Geometry, StoryProps>[]
    expect(roadLabel(s, first)).toBe('On the road between Town and Ranch')
    expect(roadLabel(s, second)).toBe('On the road between Ranch and Camp')
  })
})

describe('pinsApart', () => {
  it('keeps a pin with a stop on it, and one no stop names', () => {
    expect([...pinsApart(story())]).toEqual([])
  })
  it('sets apart a pin whose every stop is over a kilometre away', () => {
    const s = story()
    // Move the ranch pin about 2.2 km east of the stop at it.
    s.places.features[1].geometry.coordinates = [1.02, 0]
    expect([...pinsApart(s)]).toEqual(['ranch'])
  })
  it('keeps a pin when any one of its stops is on it', () => {
    const s = story()
    s.places.features[0].geometry.coordinates = [0.02, 0]
    // J1 stops 2.2 km from the moved town pin, J2 on it.
    s.stops.features.find((f) => f.properties.id === 'j2-1')!.geometry.coordinates = [0.02, 0]
    expect([...pinsApart(s)]).toEqual([])
  })
})

describe('bounds', () => {
  it('covers every coordinate', () => {
    expect(bounds(story().journeys.features)).toEqual([0, 0, 2, 0])
  })
})

describe('clickResult', () => {
  const s = story()
  const j1 = journeyStops(s, 'J1') as Feature<Point, StoryProps>[]

  it('steps to the nearer end of a clicked route in the journey in focus', () => {
    expect(clickResult([pick('journeys', 'j1-s1', 'J1', 1)], [0.9, 0], s, 'J1', j1, 0)).toEqual({ kind: 'step', index: 1 })
    expect(clickResult([pick('journeys', 'j1-s1', 'J1', 1)], [0.1, 0], s, 'J1', j1, 2)).toEqual({ kind: 'step', index: 0 })
  })
  it('goes to the stop in another journey when the journey in focus does not stop there', () => {
    const j2 = journeyStops(s, 'J2') as Feature<Point, StoryProps>[]
    expect(clickResult([pick('places', 'ranch')], [1, 0], s, 'J2', j2, 0)).toEqual({ kind: 'stop', id: 'j1-2' })
  })
  it('prefers the journey in focus at a town several journeys share', () => {
    const j2 = journeyStops(s, 'J2') as Feature<Point, StoryProps>[]
    expect(clickResult([pick('places', 'town')], [0, 0], s, 'J2', j2, 0)).toEqual({ kind: 'step', index: 0 })
  })
  it('opens the card of a place no journey stops at, and clears on empty map', () => {
    expect(clickResult([pick('places', 'village')], [5, 5], s, 'J1', j1, 0)).toEqual({ kind: 'select', layer: 'places', id: 'village' })
    expect(clickResult([], [9, 9], s, 'J1', j1, 0)).toEqual({ kind: 'clear' })
  })
})
