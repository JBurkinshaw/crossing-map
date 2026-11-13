import { useEffect, useState } from 'react'
import type { FeatureCollection, Point } from 'geojson'

// Properties shared by every story feature; data/schema/story-layer.schema.json is the full contract.
export type StoryProps = {
  id: string
  name: string
  journey: string | null
  sequence: number | null
  certainty: 'located' | 'approximate' | 'inferred' | 'reported'
  uncertainty_m: number | null
  source: string
  source_id: string | null
  first_seen: string
  note_safe: string
  // Absent while spoiler mode is on: spoiler/filter.ts drops it so only note_safe can show.
  note_full?: string | null
  reasoning: string | null
}

export type Story = {
  places: FeatureCollection<Point, StoryProps>
  stops: FeatureCollection<Point, StoryProps>
  areas: FeatureCollection
  journeys: FeatureCollection
}

const LAYERS = ['places', 'stops', 'areas', 'journeys'] as const

// Tale places outside the story box: named in the panel, not mapped (data/elsewhere.json).
export type Elsewhere = { id: string; name: string; first_seen: string; role: string }

export function useElsewhere(): Elsewhere[] {
  const [list, setList] = useState<Elsewhere[]>([])
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/elsewhere.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setList, () => setList([]))
  }, [])
  return list
}

// The story layers from data/, or from the raised copies in data/raised/ (the Raised view), fetched once
// `enabled` is first true.
export function useStory(folder: '' | 'raised/' = '', enabled = true): Story | 'failed' | null {
  const [story, setStory] = useState<Story | 'failed' | null>(null)
  useEffect(() => {
    if (!enabled) return
    const base = `${import.meta.env.BASE_URL}data/${folder}`
    Promise.all(
      LAYERS.map((name) =>
        fetch(`${base}${name}.geojson`).then((r) => {
          if (!r.ok) throw new Error(`${name}.geojson: HTTP ${r.status}`)
          return r.json()
        }),
      ),
    )
      .then(([places, stops, areas, journeys]) => setStory({ places, stops, areas, journeys }))
      .catch((e) => {
        console.error('Story data failed to load:', e)
        setStory('failed')
      })
  }, [folder, enabled])
  return story
}
