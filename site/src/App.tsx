import { useEffect, useMemo, useReducer, useRef } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import { useStory } from './data/story'
import { MapView } from './map/MapView'
import { Panel } from './panel/Panel'

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
  const loaded = useStory()
  const story = loaded === 'failed' ? null : loaded
  const mapRef = useRef<MapRef>(null)
  const [state, dispatch] = useReducer(reducer, { journey: 'J1', stopIndex: 0 })

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
      />
      <Panel
        failed={loaded === 'failed'}
        journey={state.journey}
        stops={stops}
        stopIndex={state.stopIndex}
        onJourney={(journey) => dispatch({ type: 'journey', journey })}
        onStop={goToStop}
      />
    </main>
  )
}
