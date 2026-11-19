import { describe, expect, it } from 'vitest'
import { featureFilter } from '@maplibre/maplibre-gl-style-spec'
import type { Feature, FeatureCollection, GeoJsonProperties } from 'geojson'
import type { Story } from '../data/story'
import type { Translation } from '../data/translations'
import { layerFilterUpTo, PROGRESS_LAYERS, shownAt, storyUpTo, translationsUpTo } from './filter'
import { reachedEpisode, spoilersHidden, type Episode } from './progress'

// The spoiler filters run on the published data at every reading position: nothing first seen after the reader's
// progress may pass. This is the data half of the spoiler-leak test (design section 11). The browser half,
// tools/spoiler-leak.mjs, checks that the site shows only what these filters pass (decision 0054).

const files = import.meta.glob<string>(['../../../data/**/*.{json,geojson}', '../../public/labels/passes.geojson'], { query: '?raw', import: 'default', eager: true })
const read = <T,>(path: string): T => JSON.parse(files[path])
const data = <T,>(name: string): T => read(`../../../data/${name}`)
const layers = (dir = '') => Object.fromEntries(['places', 'stops', 'areas', 'journeys'].map((n) => [n, data(`${dir}${n}.geojson`)])) as Story

const episodes = data<Episode[]>('episodes.json')
const flat = layers()
const oblique = layers('oblique/')
const translations = data<Translation[]>('translations.json')
const positions = ['none', ...episodes.map((e) => e.episode), 'all']

// The features behind each base-map layer the progress filters (graticule lines carry no story dates).
const features = (name: string) => data<FeatureCollection>(name).features
const vignettes = [...features('vignettes.geojson'), ...features('oblique/vignettes.geojson')]
const LAYER_DATA: Record<string, Feature[]> = {
  'mountain-glyph': features('mountain_glyphs.geojson'),
  'landform-label': features('landforms.geojson'),
  'pass-label': read<FeatureCollection>('../../public/labels/passes.geojson').features,
  'water-place': features('water_places.geojson'),
  'context-place': features('context_places.geojson'),
  vignette: vignettes,
  'vignette-label': vignettes,
}

// Names the reader has not met at `reached`: those of features first seen later, less any that is part of a name
// already met ("Madera" in "Sierra de la Madera"). The map's title cartouche names the three states throughout.
const named = [
  ...Object.values(flat).flatMap((fc: FeatureCollection) => fc.features.map((f) => f.properties)),
  ...features('mountain_glyphs.geojson').map((f) => f.properties),
  ...vignettes.map((f) => f.properties),
  ...data<GeoJsonProperties[]>('elsewhere.json'),
]
const ALWAYS_SHOWN = ['Sonora', 'Chihuahua', 'New Mexico']
function unmetNames(reached: string): string[] {
  const met = [...ALWAYS_SHOWN, ...named.filter((p) => shownAt(p, reached)).map((p) => p?.name as string)]
  const unmet = new Set(named.filter((p) => !shownAt(p, reached)).map((p) => p?.name as string))
  return [...unmet].filter((name) => name && !met.some((m) => m.includes(name)))
}
const questions = data<GeoJsonProperties[]>('open-questions.json')

const EPISODE_ID = /\b[1-4]-(0[1-9]|1[0-4])\b/g
// Every first_seen and every episode a text field cites, in a filtered story, past `reached`.
function later(story: Story, reached: string): string[] {
  const found: string[] = []
  for (const [layer, fc] of Object.entries(story) as [string, FeatureCollection][]) {
    for (const { properties: p } of fc.features) {
      if (p?.role !== 'context' && !(p?.first_seen <= reached)) found.push(`${layer} ${p?.id} first seen ${p?.first_seen}`)
      for (const lead of p?.leads ?? []) if (lead.first_seen > reached) found.push(`${layer} ${p?.id} lead ${lead.source} first seen ${lead.first_seen}`)
      for (const [key, value] of Object.entries(p ?? {})) {
        if (key === 'first_seen' || key === 'episode' || typeof value !== 'string') continue
        for (const id of value.match(EPISODE_ID) ?? []) if (id > reached) found.push(`${layer} ${p?.id} ${key} cites ${id}`)
      }
    }
  }
  return found
}

describe.each(positions)('at %s', (progress) => {
  const reached = reachedEpisode(progress)
  const spoilers = spoilersHidden(progress, episodes)

  it('keeps no later feature or text in the story layers, flat and oblique', () => {
    expect(later(storyUpTo(flat, reached, spoilers), reached)).toEqual([])
    expect(later(storyUpTo(oblique, reached, spoilers), reached)).toEqual([])
  })

  it('names no place the reader has not met in the leads it shows', () => {
    const unmet = unmetNames(reached)
    const found = Object.values(storyUpTo(flat, reached, spoilers))
      .flatMap((fc: FeatureCollection) => fc.features.map((f) => f.properties))
      .flatMap((p) => (p?.leads ?? []).flatMap((l: { note?: string }) => unmet.filter((n) => l.note?.includes(n)).map((n) => `${p?.id} names ${n}`)))
    expect(found).toEqual([])
  })

  it('keeps no later translation', () => {
    expect(translationsUpTo(translations, reached).filter((t) => t.first_seen > reached).map((t) => t.id)).toEqual([])
  })

  it('names no place the reader has not met in the open questions it shows', () => {
    const unmet = unmetNames(reached)
    const found = questions
      .filter((q) => shownAt(q, reached))
      .flatMap((q) => Object.values(q ?? {}).flatMap((v) => (typeof v === 'string' ? unmet.filter((n) => v.includes(n)).map((n) => `${q?.id} names ${n}`) : [])))
    expect(found).toEqual([])
  })

  it.each(Object.keys(LAYER_DATA))('lets no later feature through the %s filter', (id) => {
    const floor = PROGRESS_LAYERS[id]
    const pass = featureFilter(layerFilterUpTo(id, undefined, reached)).filter
    const leaked = LAYER_DATA[id]
      .filter((f) => pass({ zoom: 10 }, { type: 1, properties: f.properties ?? {} }))
      .filter((f) => f.properties?.first_seen > reached && f.properties?.first_seen > floor)
      .map((f) => `${f.properties?.name} first seen ${f.properties?.first_seen}`)
    expect(leaked).toEqual([])
  })
})

// Guards the test itself: a filter that hid everything would pass every check above.
it('lets features the reader has reached through the filters', () => {
  const pass = featureFilter(layerFilterUpTo('vignette', undefined, '2-01')).filter
  expect(vignettes.some((f) => f.properties?.first_seen <= '2-01' && pass({ zoom: 10 }, { type: 1, properties: f.properties ?? {} }))).toBe(true)
  expect(storyUpTo(flat, '2-01', true).stops.features.length).toBeGreaterThan(0)
})
