import { useEffect, useMemo, useReducer, useRef, useState, type RefObject } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { Feature, Geometry } from 'geojson'
import type { Story, StoryProps } from './data/story'
import type { Translation } from './data/translations'
import { isPhone, motion } from './map/setup'
import type { SearchHit } from './panel/SearchBox'
import { bounds, byId, clickResult, corridorBounds, journeyStops, journeysOf, type MapPick } from './story/select'

// How the reader moves through the story: the journey in focus and its current stop, the place, area or road
// picked, and the translation picked. Every way in (the stepper, a click on the map, search, a translation)
// ends here, and each moves the map to what it opens.

// `stepping` is true once the reader steps from stop to stop; the road ahead then fades (design 9, data dimming).
type State = { journey: string; stopIndex: number; stepping: boolean }
type Action =
  | { type: 'journey'; journey: string }
  | { type: 'stop'; index: number }
  | { type: 'goto'; journey: string; index: number; stepping: boolean }
  | { type: 'home' }

export function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'journey':
      return { journey: action.journey, stopIndex: 0, stepping: false }
    case 'stop':
      return { ...state, stopIndex: action.index, stepping: true }
    case 'goto':
      return { journey: action.journey, stopIndex: action.index, stepping: action.stepping }
    case 'home':
      return { ...state, stepping: false }
  }
}

// A place or area picked on the map or in search, or the road a line was spoken on (a route segment).
export type Selection = { layer: 'places' | 'areas' | 'journeys'; id: string } | null
type StoryFeature = Feature<Geometry, StoryProps>

// The whole of a journey: its stops, clear of the map's switches (top right), the zoom buttons (left), and the
// inset and cartouche (bottom right). Phones have no room to spare.
function frameStops(map: MapRef | null, stops: StoryFeature[]) {
  const padding = isPhone() ? 30 : { top: 70, right: 130, bottom: 100, left: 80 }
  if (stops.length > 0) map?.fitBounds(bounds(stops), { padding, duration: motion(1200) })
}

type Options = {
  mapRef: RefObject<MapRef | null>
  // The story the map draws (the raised copies in the Raised view), and the flat story, which lists every
  // journey reached; both already filtered to the reader's progress.
  story: Story | null
  flat: Story | null
  translations: Translation[]
  // Shows a pick's card on phones: the drawer goes to half height, with the map still in view above it. A pick
  // from search always does (search opens the drawer fully); a click on the map only raises a lowered drawer.
  showCard: (from: 'search' | 'map') => void
}

export function useNavigation({ mapRef, story, flat, translations, showCard }: Options) {
  const [state, dispatch] = useReducer(reducer, { journey: 'J1', stopIndex: 0, stepping: false })
  const [selection, setSelection] = useState<Selection>(null)
  const [translationId, setTranslationId] = useState<string | null>(null)

  // The journeys drawn so far and reached, from the flat story data (the raised copies cover fewer).
  const journeys = useMemo(() => journeysOf(flat), [flat])
  // A journey not reached yet (after the reader moves progress back) gives way to the first one reached.
  const journey = journeys.some((j) => j.id === state.journey) ? state.journey : (journeys[0]?.id ?? '')
  const stopsOf = (j: string) => journeyStops(story, j)
  const stops = useMemo(() => journeyStops(story, journey), [story, journey])
  const stopIndex = Math.min(state.stopIndex, Math.max(0, stops.length - 1))

  // Frame the whole journey when the data arrives and whenever the reader switches journey.
  // A shared link with a #map= view keeps its view on first load.
  const framed = useRef<string | null>(window.location.hash.includes('map=') ? 'from-link' : null)
  useEffect(() => {
    if (!mapRef.current || stops.length === 0) return
    if (framed.current === 'from-link') {
      framed.current = journey
      return
    }
    if (framed.current === journey) return
    framed.current = journey
    frameStops(mapRef.current, stops)
  }, [stops, journey, mapRef])

  const flyTo = (f: StoryFeature) => {
    const map = mapRef.current
    if (!map) return
    if (f.geometry.type === 'Point') {
      map.flyTo({ center: f.geometry.coordinates as [number, number], zoom: Math.max(map.getZoom(), 9), duration: motion(1600) })
    } else {
      map.fitBounds(bounds([f]), { padding: 60, maxZoom: 11, duration: motion(1600) })
    }
  }

  // Stepping through the stops of the journey in focus.
  const goToStop = (index: number) => {
    const stop = stops[index]
    if (!stop) return
    dispatch({ type: 'stop', index })
    setSelection(null)
    setTranslationId(null)
    flyTo(stop)
  }

  // A stop of any journey, from search or a translation: that journey comes into focus at that stop.
  const showStop = (id: string) => {
    const f = byId(flat, 'stops', id)
    const j = f?.properties.journey
    if (!f || !j) return
    const list = stopsOf(j)
    const index = Math.max(0, list.findIndex((s) => s.properties.id === id))
    framed.current = j
    dispatch({ type: 'goto', journey: j, index, stepping: true })
    setSelection(null)
    flyTo(list[index] ?? f)
  }

  // A click on the map (story/select.ts, clickResult). Only journeys and stops the reader has reached are drawn
  // or listed (spoiler/filter.ts), so a click never jumps ahead in the book.
  const onMapClick = (picks: MapPick[], at: [number, number]) => {
    setTranslationId(null)
    const result = clickResult(picks, at, story, journey, stops, stopIndex)
    if (result.kind === 'step') return goToStop(result.index)
    if (result.kind === 'stop') return showStop(result.id)
    setSelection(result.kind === 'select' ? { layer: result.layer, id: result.id } : null)
    if (picks.length > 0) showCard('map')
  }

  const showFeature = (layer: 'places' | 'areas', id: string) => {
    const f = byId(story, layer, id) ?? byId(flat, layer, id)
    if (!f) return
    setSelection({ layer, id })
    flyTo(f)
  }

  // Talk on the road: the segment's journey comes into focus at the stop the segment leaves from, its card
  // opens, and the map frames the corridor.
  const showRoad = (id: string) => {
    const f = byId(flat, 'journeys', id)
    const j = f?.properties.journey
    if (!f || !j) return
    const index = Math.max(0, stopsOf(j).findIndex((s) => s.properties.sequence === f.properties.sequence))
    framed.current = j
    dispatch({ type: 'goto', journey: j, index, stepping: false })
    setSelection({ layer: 'journeys', id })
    mapRef.current?.fitBounds(corridorBounds(byId(story, 'journeys', id) ?? f), { padding: 60, maxZoom: 11, duration: motion(1600) })
  }

  // A translation goes to where it was said (a stop, place or area, or the road for talk on the road); when
  // the book does not say, to its episode on the journey then in progress (the one in focus if it has stops in
  // that episode).
  const showTranslation = (t: Translation) => {
    setTranslationId(t.id)
    const ref = t.location_ref
    if (ref && t.location_kind === 'road') return showRoad(ref)
    if (ref && byId(flat, 'stops', ref)) return showStop(ref)
    if (ref && byId(flat, 'places', ref)) return showFeature('places', ref)
    if (ref && byId(flat, 'areas', ref)) return showFeature('areas', ref)
    setSelection(null)
    const inEpisode = (story?.stops.features ?? []).filter((f) => f.properties.episode === t.episode)
    if (inEpisode.length === 0) return
    const count = new Map<string, number>()
    for (const f of inEpisode) count.set(f.properties.journey!, (count.get(f.properties.journey!) ?? 0) + 1)
    const j = count.has(journey) ? journey : [...count].sort((a, b) => b[1] - a[1])[0][0]
    const list = stopsOf(j)
    const own = inEpisode.filter((f) => f.properties.journey === j)
    framed.current = j
    dispatch({ type: 'goto', journey: j, index: Math.max(0, list.indexOf(own[0])), stepping: false })
    mapRef.current?.fitBounds(bounds(own), { padding: 60, maxZoom: 10, duration: motion(1600) })
  }

  const onPick = (hit: SearchHit) => {
    showCard('search')
    if (hit.kind === 'translation') {
      const t = translations.find((x) => x.id === hit.ref)
      if (t) showTranslation(t)
      return
    }
    setTranslationId(null)
    if (hit.kind === 'stop') showStop(hit.ref)
    else showFeature('places', hit.ref)
  }

  return {
    journey,
    journeys,
    stops,
    stopIndex,
    stepping: state.stepping,
    selection,
    translationId,
    setSelection,
    setTranslationId,
    goToStop,
    showRoad,
    onMapClick,
    onPick,
    onJourney: (j: string) => dispatch({ type: 'journey', journey: j }),
    onHome: () => {
      dispatch({ type: 'home' })
      frameStops(mapRef.current, stops)
    },
  }
}
