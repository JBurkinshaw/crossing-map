import { describe, expect, it } from 'vitest'
import type { StyleSpecification } from 'maplibre-gl'
import { story } from '../test/fixtures'
import { GLYPH_ALWAYS, layerFilterUpTo, shownAt, storyUpTo, styleUpTo, translationsUpTo } from './filter'

describe('shownAt', () => {
  it('shows a feature from its first_seen on', () => {
    expect(shownAt({ first_seen: '1-02' }, '1-01')).toBe(false)
    expect(shownAt({ first_seen: '1-02' }, '1-02')).toBe(true)
    expect(shownAt({ first_seen: '1-02' }, '9-99')).toBe(true)
  })
  it('shows context towns at every position, before the book included', () => {
    expect(shownAt({ role: 'context', first_seen: '4-01' }, '0-00')).toBe(true)
  })
  it('hides a feature with no first_seen', () => {
    expect(shownAt({}, '9-99')).toBe(false)
    expect(shownAt(null, '9-99')).toBe(false)
  })
})

describe('storyUpTo', () => {
  it('keeps only features reached', () => {
    const s = storyUpTo(story(), '1-02', true)
    expect(s.places.features.map((f) => f.properties.id)).toEqual(['town', 'ranch', 'village'])
    expect(s.stops.features.map((f) => f.properties.id)).toEqual(['j1-1', 'j1-2'])
  })
  it('ends each journey at its last stop reached', () => {
    // Segment 1 joins stops 1 and 2, both reached; segment 2 leads on to stop 3, which is not.
    expect(storyUpTo(story(), '1-02', true).journeys.features.map((f) => f.properties?.id)).toEqual(['j1-s1'])
    expect(storyUpTo(story(), '2-01', true).journeys.features.map((f) => f.properties?.id)).toEqual(['j1-s1', 'j1-s2'])
  })
  it('drops note_full and hides reasoning that cites a later episode while spoilers are hidden', () => {
    const s = story()
    s.stops.features[0].properties.note_full = 'The end.'
    s.stops.features[0].properties.reasoning = 'Confirmed in 3-04.'
    const hidden = storyUpTo(s, '1-01', true).stops.features[0].properties
    expect(hidden.note_full).toBeUndefined()
    expect(hidden.reasoning).not.toContain('3-04')
    const open = storyUpTo(s, '9-99', false).stops.features[0].properties
    expect(open.note_full).toBe('The end.')
    expect(open.reasoning).toBe('Confirmed in 3-04.')
  })
  it('hides how a leg was drawn when it cites a later episode while spoilers are hidden', () => {
    const s = story()
    s.journeys.features[0].properties = { ...s.journeys.features[0].properties, drawn: 'Traced along the road he takes in 3-04.' }
    const hidden = storyUpTo(s, '1-02', true).journeys.features[0].properties
    expect(hidden?.drawn).not.toContain('3-04')
    expect(hidden?.drawn).toMatch(/later episodes/)
    expect(storyUpTo(s, '3-04', true).journeys.features[0].properties?.drawn).toBe('Traced along the road he takes in 3-04.')
    expect(storyUpTo(s, '1-02', false).journeys.features[0].properties?.drawn).toBe('Traced along the road he takes in 3-04.')
  })
  it('hides the technical detail of a leg when it cites a later episode while spoilers are hidden', () => {
    const s = story()
    s.journeys.features[0].properties = { ...s.journeys.features[0].properties, drawn_detail: 'Grid as in 3-04.' }
    expect(storyUpTo(s, '1-02', true).journeys.features[0].properties?.drawn_detail).toMatch(/later episodes/)
    expect(storyUpTo(s, '3-04', true).journeys.features[0].properties?.drawn_detail).toBe('Grid as in 3-04.')
  })
  it('keeps reasoning that cites only episodes reached', () => {
    const s = story()
    s.stops.features[0].properties.reasoning = 'Named in 1-01.'
    expect(storyUpTo(s, '1-01', true).stops.features[0].properties.reasoning).toBe('Named in 1-01.')
  })
})

describe('translationsUpTo', () => {
  it('keeps lines from episodes reached', () => {
    const lines = [{ first_seen: '1-01' }, { first_seen: '2-03' }]
    expect(translationsUpTo(lines, '2-02')).toEqual([{ first_seen: '1-01' }])
  })
})

describe('layerFilterUpTo', () => {
  it('shows glyphs dated 1-01 even before the book starts', () => {
    expect(layerFilterUpTo('mountain-glyph', undefined, '0-00')).toEqual(['<=', ['to-string', ['get', 'first_seen']], GLYPH_ALWAYS])
  })
  it('filters vignettes to the reader’s progress and keeps the base filter', () => {
    const base = ['==', ['get', 'kind'], 'vignette'] as never
    expect(layerFilterUpTo('vignette', base, '2-01')).toEqual(['all', base, ['<=', ['to-string', ['get', 'first_seen']], '2-01']])
  })
})

describe('styleUpTo', () => {
  it('filters only the progress layers', () => {
    const style: StyleSpecification = {
      version: 8,
      sources: {},
      layers: [
        { id: 'paper', type: 'background' },
        { id: 'vignette', type: 'symbol', source: 'v' },
      ],
    }
    const out = styleUpTo(style, '1-03')
    expect(out.layers[0]).toBe(style.layers[0])
    expect((out.layers[1] as { filter: unknown }).filter).toEqual(['<=', ['to-string', ['get', 'first_seen']], '1-03'])
  })
})
