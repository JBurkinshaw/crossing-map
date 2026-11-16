import { describe, expect, it } from 'vitest'
import type { Feature, Geometry } from 'geojson'
import type { StoryProps } from '../data/story'
import { resumeStop } from './resume'

// A stop of `journey` at `sequence`, first seen in `episode`.
const stop = (journey: string, sequence: number, episode: string, certainty: StoryProps['certainty'] = 'located'): Feature<Geometry, StoryProps> => ({
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [0, 0] },
  properties: {
    id: `${journey}-${sequence}`,
    name: '',
    journey,
    sequence,
    certainty,
    uncertainty_m: null,
    source: 'test',
    source_id: null,
    first_seen: episode,
    note_safe: '',
    reasoning: null,
  },
})

// Shaped like the book: the wolf's journey hands over to Billy's in 1-08; a reported journey runs alongside
// another in 3-08.
const stops = [
  stop('J1', 1, '1-04'),
  stop('J1', 2, '1-06'),
  stop('J1', 3, '1-08'),
  stop('J2', 1, '1-08'),
  stop('J2', 2, '1-09'),
  stop('J4', 1, '2-07'),
  stop('J4', 2, '3-08'),
  stop('J4', 3, '3-10'),
  stop('J6', 1, '3-08', 'reported'),
  stop('J6', 2, '4-05', 'reported'),
]

describe('resumeStop', () => {
  it('opens at the start for not started and finished', () => {
    expect(resumeStop(stops, 'none')).toBeNull()
    expect(resumeStop(stops, 'all')).toBeNull()
  })
  it('chooses nothing before the first stop', () => {
    expect(resumeStop(stops, '1-03')).toBeNull()
  })
  it('takes the last stop at or before the episode', () => {
    expect(resumeStop(stops, '1-04')).toEqual({ journey: 'J1', id: 'J1-1' })
    expect(resumeStop(stops, '1-07')).toEqual({ journey: 'J1', id: 'J1-2' })
    expect(resumeStop(stops, '3-14')).toEqual({ journey: 'J4', id: 'J4-3' })
  })
  it('takes the journey the story has moved on to when two reach the episode together', () => {
    expect(resumeStop(stops, '1-08')).toEqual({ journey: 'J2', id: 'J2-1' })
  })
  it('prefers a journey told first-hand over a reported one', () => {
    expect(resumeStop(stops, '3-08')).toEqual({ journey: 'J4', id: 'J4-2' })
  })
  it('takes a reported journey when it alone is the latest', () => {
    expect(resumeStop(stops, '4-05')).toEqual({ journey: 'J6', id: 'J6-2' })
  })
  it('does not depend on the order of the stops', () => {
    expect(resumeStop([...stops].reverse(), '1-08')).toEqual({ journey: 'J2', id: 'J2-1' })
  })
})
