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
  reasoning: string | null
}

export type Story = {
  places: FeatureCollection<Point, StoryProps>
  stops: FeatureCollection<Point, StoryProps>
  areas: FeatureCollection
  journeys: FeatureCollection
}

const LAYERS = ['places', 'stops', 'areas', 'journeys'] as const

export function useStory(): Story | 'failed' | null {
  const [story, setStory] = useState<Story | 'failed' | null>(null)
  useEffect(() => {
    const base = `${import.meta.env.BASE_URL}data/`
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
  }, [])
  return story
}
