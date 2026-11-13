import { lazy, Suspense, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import { useElsewhere, useStory } from './data/story'
import { MapView, type View } from './map/MapView'
import { Panel } from './panel/Panel'
import { useRoute } from './route'

// The About, How it's built, Data and Credits pages, loaded the first time one opens.
const Pages = lazy(() => import('./pages/Pages'))

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
  const route = useRoute()
  const loaded = useStory()
  const elsewhere = useElsewhere()
  const [view, setView] = useState<View>('flat')
  // The Raised view draws the story where the raised line work puts it: the copies in data/raised/,
  // fetched the first time the reader turns it on.
  const [raisedWanted, setRaisedWanted] = useState(false)
  if (view === 'raised' && !raisedWanted) setRaisedWanted(true)
  const raised = useStory('raised/', raisedWanted)
  const shown = view === 'raised' ? raised : loaded
  const story = shown === 'failed' ? null : shown
  const mapRef = useRef<MapRef>(null)
  const [state, dispatch] = useReducer(reducer, { journey: 'J1', stopIndex: 0 })

  // The journeys drawn so far, from the flat story data (the raised copies cover fewer).
  const journeys = useMemo(
    () => [...new Set((loaded && loaded !== 'failed' ? loaded.stops.features : []).map((f) => f.properties.journey ?? ''))].filter(Boolean).sort(),
    [loaded],
  )

  const stops = useMemo(
    () =>
      (story?.stops.features ?? [])
        .filter((f) => f.properties.journey === state.journey)
        .sort((a, b) => (a.properties.sequence ?? 0) - (b.properties.sequence ?? 0)),
    [story, state.journey],
  )

  // Frame the whole journey when the data arrives and whenever the reader switches journey.
  // A shared link with a #map= view keeps its view on first load.
  const framed = useRef<string | null>(window.location.hash.includes('map=') ? 'from-link' : null)
  useEffect(() => {
    const map = mapRef.current
    if (!map || stops.length === 0) return
    if (framed.current === 'from-link') {
      framed.current = state.journey
      return
    }
    if (framed.current === state.journey) return
    framed.current = state.journey
    const lons = stops.map((f) => f.geometry.coordinates[0])
    const lats = stops.map((f) => f.geometry.coordinates[1])
    map.fitBounds([Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)], {
      padding: 40,
      duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1200,
    })
  }, [stops, state.journey])

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
        stopIndex={state.stopIndex}
        onSelectStop={goToStop}
        onView={setView}
      />
      <Panel
        failed={loaded === 'failed'}
        journey={state.journey}
        journeys={journeys}
        elsewhere={elsewhere}
        stops={stops}
        stopIndex={state.stopIndex}
        onJourney={(journey) => dispatch({ type: 'journey', journey })}
        onStop={goToStop}
      />
      {route !== '/' && (
        <Suspense fallback={null}>
          <Pages route={route} />
        </Suspense>
      )}
    </main>
  )
}
