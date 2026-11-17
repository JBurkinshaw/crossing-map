import { useEffect, useState } from 'react'
import type { FeatureCollection, Point } from 'geojson'
import { useJson, type Loaded } from './json'

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
  // Present on some layers only: places and areas have a kind and a role, stops an episode.
  kind?: string
  role?: string | null
  part?: number | null
  episode?: string | null
  // Stops: the place the stop stands at, if it is a named one.
  place_ref?: string | null
  // How the feature was placed; a route segment with "modeled" is a least-cost line, not the book's way.
  method?: string
  // Route segments: how the line was drawn, in words (decision 0032).
  drawn?: string
  // Inferred areas: the rule that cut the stop's circle to the ground its reasoning describes (null for a plain
  // circle), and whether a straight line between towns stands in for an unmapped old road.
  outline_rule?: string | null
  straight_road?: boolean
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

export const useElsewhere = (): Loaded<Elsewhere[]> => useJson<Elsewhere[]>('elsewhere.json')

// The story layers from data/, or from the oblique copies in data/oblique/ (the Oblique view), fetched once
// `enabled` is first true.
export function useStory(folder: '' | 'oblique/' = '', enabled = true): Story | 'failed' | null {
  const [story, setStory] = useState<Story | 'failed' | null>(null)
  useEffect(() => {
    if (!enabled) return
    const base = `${import.meta.env.BASE_URL}data/${folder}`
    const controller = new AbortController()
    Promise.all(
      LAYERS.map((name) =>
        fetch(`${base}${name}.geojson`, { signal: controller.signal }).then((r) => {
          if (!r.ok) throw new Error(`${name}.geojson: HTTP ${r.status}`)
          return r.json()
        }),
      ),
    )
      .then(([places, stops, areas, journeys]) => setStory({ places, stops, areas, journeys }))
      .catch((e) => {
        if (controller.signal.aborted) return
        console.error('Story data failed to load:', e)
        setStory('failed')
      })
    return () => controller.abort()
  }, [folder, enabled])
  return story
}
