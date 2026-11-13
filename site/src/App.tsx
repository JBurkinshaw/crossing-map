import { useEffect, useMemo, useReducer, useRef, useState } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import { useElsewhere, useStory } from './data/story'
import { MapView, type View } from './map/MapView'
import { Panel } from './panel/Panel'
import { shownAt, storyUpTo } from './spoiler/filter'
import { reachedEpisode, spoilersHidden, useEpisodes, useProgress } from './spoiler/progress'
import { ReadingProgress } from './spoiler/ReadingProgress'

type State = { journey: string; stopIndex: number }
type Action = { type: 'journey'; journey: string } | { type: 'stop'; index: number }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'journey':
      return { journey: action.journey, stopIndex: 0 }
    case 'stop':
      return { ...state, stopIndex: action.index }
  }
}

export default function App() {
  const loadedAll = useStory()
  const elsewhereAll = useElsewhere()
  // Spoiler mode: everything below sees only what the reader has reached (spoiler/filter.ts).
  const { progress, isSet, setProgress } = useProgress()
  const episodes = useEpisodes()
  const reached = reachedEpisode(progress)
  const spoilers = spoilersHidden(progress, episodes)
  const loaded = useMemo(
    () => (loadedAll && loadedAll !== 'failed' ? storyUpTo(loadedAll, reached, spoilers) : loadedAll),
    [loadedAll, reached, spoilers],
  )
  const elsewhere = useMemo(() => elsewhereAll.filter((e) => shownAt(e, reached)), [elsewhereAll, reached])
  const [view, setView] = useState<View>('flat')
  // The Raised view draws the story where the raised line work puts it: the copies in data/raised/,
  // fetched the first time the reader turns it on.
  const [raisedWanted, setRaisedWanted] = useState(false)
  if (view === 'raised' && !raisedWanted) setRaisedWanted(true)
  const raisedAll = useStory('raised/', raisedWanted)
  const raised = useMemo(
    () => (raisedAll && raisedAll !== 'failed' ? storyUpTo(raisedAll, reached, spoilers) : raisedAll),
    [raisedAll, reached, spoilers],
  )
  const shown = view === 'raised' ? raised : loaded
  const story = shown === 'failed' ? null : shown
  const mapRef = useRef<MapRef>(null)
  const [state, dispatch] = useReducer(reducer, { journey: 'J1', stopIndex: 0 })

  // The journeys drawn so far and reached, from the flat story data (the raised copies cover fewer), each with
  // the episode of its first stop.
  const journeys = useMemo(() => {
    const first = new Map<string, string>()
    for (const f of loaded && loaded !== 'failed' ? loaded.stops.features : []) {
      const { journey: id, first_seen } = f.properties
      if (id && (!first.has(id) || first_seen < first.get(id)!)) first.set(id, first_seen)
    }
    return [...first].map(([id, first_seen]) => ({ id, first_seen })).sort((a, b) => a.id.localeCompare(b.id))
  }, [loaded])
  // A journey not reached yet (after the reader moves progress back) gives way to the first one reached.
  const journey = journeys.some((j) => j.id === state.journey) ? state.journey : (journeys[0]?.id ?? '')

  const stops = useMemo(
    () =>
      (story?.stops.features ?? [])
        .filter((f) => f.properties.journey === journey)
        .sort((a, b) => (a.properties.sequence ?? 0) - (b.properties.sequence ?? 0)),
    [story, journey],
  )
  const stopIndex = Math.min(state.stopIndex, Math.max(0, stops.length - 1))

  // Frame the whole journey when the data arrives and whenever the reader switches journey.
  // A shared link with a #map= view keeps its view on first load.
  const framed = useRef<string | null>(window.location.hash.includes('map=') ? 'from-link' : null)
  useEffect(() => {
    const map = mapRef.current
    if (!map || stops.length === 0) return
    if (framed.current === 'from-link') {
      framed.current = journey
      return
    }
    if (framed.current === journey) return
    framed.current = journey
    const lons = stops.map((f) => f.geometry.coordinates[0])
    const lats = stops.map((f) => f.geometry.coordinates[1])
    map.fitBounds([Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)], {
      padding: 40,
      duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1200,
    })
  }, [stops, journey])

  const goToStop = (index: number) => {
    const stop = stops[index]
    if (!stop) return
    dispatch({ type: 'stop', index })
    const [lon, lat] = stop.geometry.coordinates
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    mapRef.current?.flyTo({ center: [lon, lat], zoom: Math.max(mapRef.current.getZoom(), 9), duration: reduce ? 0 : 1600 })
  }

  return (
    <main className="app">
      <MapView
        mapRef={mapRef}
        story={story}
        stops={stops}
        stopIndex={stopIndex}
        onSelectStop={goToStop}
        onView={setView}
        reached={reached}
      />
      <Panel
        header={<ReadingProgress progress={progress} isSet={isSet} episodes={episodes} onSet={setProgress} />}
        failed={loaded === 'failed'}
        journey={journey}
        journeys={journeys}
        elsewhere={elsewhere}
        stops={stops}
        stopIndex={stopIndex}
        onJourney={(journey) => dispatch({ type: 'journey', journey })}
        onStop={goToStop}
      />
    </main>
  )
}
