import { lazy, Suspense, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { Feature, Geometry, Position } from 'geojson'
import { useElsewhere, useStory, type Story, type StoryProps } from './data/story'
import { useTranslations, type Translation } from './data/translations'
import { MapView, type View } from './map/MapView'
import { corridor as corridorOf } from './map/corridor'
import type { Corridor } from './map/StoryLayers'
import type { DrawerHeight } from './panel/Drawer'
import { Panel } from './panel/Panel'
import { PlaceCard } from './panel/PlaceCard'
import { SearchBox, type SearchHit } from './panel/SearchBox'
import { TranslationList } from './panel/TranslationList'
import { usePhone } from './panel/usePhone'
import { useRoute } from './route'
import { shownAt, storyUpTo, translationsUpTo } from './spoiler/filter'
import { reachedEpisode, spoilersHidden, useEpisodes, useProgress } from './spoiler/progress'
import { ReadingProgress } from './spoiler/ReadingProgress'

// The About, How it's built, Data and Credits pages, loaded the first time one opens.
const Pages = lazy(() => import('./pages/Pages'))

// `stepping` is true once the reader steps from stop to stop; the road ahead then fades (plan 9, data dimming).
type State = { journey: string; stopIndex: number; stepping: boolean }
type Action =
  | { type: 'journey'; journey: string }
  | { type: 'stop'; index: number }
  | { type: 'goto'; journey: string; index: number; stepping: boolean }
  | { type: 'home' }

function reducer(state: State, action: Action): State {
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
type Selection = { layer: 'places' | 'areas' | 'journeys'; id: string } | null

const motion = (ms: number) => (window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : ms)

function positions(g: Geometry): Position[] {
  if (g.type === 'Point') return [g.coordinates]
  if (g.type === 'LineString' || g.type === 'MultiPoint') return g.coordinates
  if (g.type === 'Polygon' || g.type === 'MultiLineString') return g.coordinates.flat()
  if (g.type === 'MultiPolygon') return g.coordinates.flat(2)
  return []
}

function bounds(features: Feature[]): [number, number, number, number] {
  const all = features.flatMap((f) => positions(f.geometry))
  const lons = all.map((p) => p[0])
  const lats = all.map((p) => p[1])
  return [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)]
}

// The whole of a journey: its stops, clear of the map's switches (top), zoom buttons and key (left), and the
// inset and cartouche (bottom right). Phones have no room to spare.
function frameStops(map: MapRef | null, stops: Feature<Geometry, StoryProps>[]) {
  const padding = window.matchMedia('(max-width: 720px)').matches ? 30 : { top: 70, right: 130, bottom: 100, left: 80 }
  if (stops.length > 0) map?.fitBounds(bounds(stops), { padding, duration: motion(1200) })
}

// A journey's stops in order.
const journeyStops = (story: Story | null, journey: string) =>
  (story?.stops.features ?? [])
    .filter((f) => f.properties.journey === journey)
    .sort((a, b) => (a.properties.sequence ?? 0) - (b.properties.sequence ?? 0))

const byId = (story: Story | null, layer: 'places' | 'stops' | 'areas' | 'journeys', id: string) =>
  (story?.[layer].features as Feature<Geometry, StoryProps>[] | undefined)?.find((f) => f.properties.id === id)

// Talk on the road (plan section 8): a route segment is named by the places at its two ends, or by its stops
// where a stop is not at a named place. Both ends are reached once the segment is (spoiler/filter.ts).
function roadLabel(story: Story | null, segment: Feature<Geometry, StoryProps>): string {
  const end = (sequence: number | null) => {
    const stop = (story?.stops.features ?? []).find((s) => s.properties.journey === segment.properties.journey && s.properties.sequence === sequence)
    const place = stop?.properties.place_ref ? byId(story, 'places', stop.properties.place_ref) : undefined
    return place?.properties.name ?? stop?.properties.name
  }
  const seq = segment.properties.sequence
  const [from, to] = [end(seq), end(seq === null ? null : seq + 1)]
  return from && to ? `On the road between ${from} and ${to}` : segment.properties.name
}

// The bounds of a segment's corridor, else of the segment.
const corridorBounds = (f: Feature<Geometry, StoryProps>) => {
  const area = corridorOf(f.geometry)
  return bounds(area ? [{ type: 'Feature', geometry: area, properties: {} }] : [f])
}

export default function App() {
  const route = useRoute()
  const loadedAll = useStory()
  const elsewhereAll = useElsewhere()
  const translationsAll = useTranslations()
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
  const translations = useMemo(() => translationsUpTo(translationsAll, reached), [translationsAll, reached])
  const spokenAt = useMemo(() => {
    const at = new Map<string, Translation[]>()
    for (const t of translations) if (t.location_ref) at.set(t.location_ref, [...(at.get(t.location_ref) ?? []), t])
    return at
  }, [translations])
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
  const flat = loaded === 'failed' ? null : loaded
  const mapRef = useRef<MapRef>(null)
  const [state, dispatch] = useReducer(reducer, { journey: 'J1', stopIndex: 0, stepping: false })
  const [selection, setSelection] = useState<Selection>(null)
  const [translationId, setTranslationId] = useState<string | null>(null)
  // Phones: the panel is a bottom drawer. It opens half way, so the reading-progress badge and search show.
  const phone = usePhone()
  const [drawer, setDrawer] = useState<DrawerHeight>('half')
  // A pick shows its card at half height, with the map still in view above it.
  const showDrawer = () => setDrawer('half')

  // The journeys drawn so far and reached, from the flat story data (the raised copies cover fewer), each with
  // the episode of its first stop.
  const journeys = useMemo(() => {
    const first = new Map<string, string>()
    for (const f of flat?.stops.features ?? []) {
      const { journey: id, first_seen } = f.properties
      if (id && (!first.has(id) || first_seen < first.get(id)!)) first.set(id, first_seen)
    }
    return [...first].map(([id, first_seen]) => ({ id, first_seen })).sort((a, b) => a.id.localeCompare(b.id))
  }, [flat])
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
  }, [stops, journey])

  const flyTo = (f: Feature<Geometry, StoryProps>) => {
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
    showDrawer()
    if (hit.kind === 'translation') {
      const t = translations.find((x) => x.id === hit.ref)
      if (t) showTranslation(t)
      return
    }
    setTranslationId(null)
    if (hit.kind === 'stop') showStop(hit.ref)
    else showFeature('places', hit.ref)
  }

  // What the card shows: only what the reader has reached (a change of progress can hide it).
  const selected = selection ? byId(flat, selection.layer, selection.id) : undefined
  const translation = translations.find((t) => t.id === translationId) ?? null
  // A line said at a stop shows in that stop's "Spoken here", and one said at a place in the place's card.
  const ref = translation?.location_ref
  const placed = !!ref && (!!byId(flat, 'stops', ref) || selected?.properties.id === ref)
  const stop = stops[stopIndex]
  // The road from the current stop to the next, and the lines spoken on it.
  const roadAhead = stop
    ? (flat?.journeys.features as Feature<Geometry, StoryProps>[] | undefined)?.find(
        (f) => f.properties.journey === stop.properties.journey && f.properties.sequence === stop.properties.sequence,
      )
    : undefined
  const road = selection?.layer === 'journeys' ? selected : undefined
  const corridor = useMemo((): Corridor | null => {
    if (!road) return null
    // In the Raised view the corridor follows the raised copy of the route.
    const segment = byId(story, 'journeys', road.properties.id) ?? road
    return { segment, label: roadLabel(flat, road).replace(/^On /, 'on ') }
  }, [road, story, flat])

  const card = road ? (
    <PlaceCard
      feature={road}
      title={roadLabel(flat, road)}
      spoken={spokenAt.get(road.properties.id) ?? []}
      spokenTitle="Spoken on this road"
      spokenNote="The book does not say where these lines were spoken. The episode travels this road, so this site places them along it: the map outlines the route with 2 km either side."
      currentTranslation={translationId}
      onClose={() => {
        setSelection(null)
        setTranslationId(null)
      }}
    />
  ) : selected ? (
    <PlaceCard
      feature={selected}
      spoken={spokenAt.get(selected.properties.id) ?? []}
      currentTranslation={translationId}
      onClose={() => setSelection(null)}
    />
  ) : (
    translation &&
    !placed && (
      <section className="place-card" aria-live="polite">
        <button type="button" className="close" aria-label="Close" onClick={() => setTranslationId(null)}>
          ×
        </button>
        <h3>Said on the way</h3>
        <p className="meta">The book does not say where this was said; the map shows the journey in that episode.</p>
        <TranslationList items={[translation]} current={null} />
      </section>
    )
  )

  return (
    <main className="app" data-drawer={phone ? drawer : undefined}>
      <h1 className="visually-hidden">The Crossing: a reading map</h1>
      <MapView
        mapRef={mapRef}
        story={story}
        stops={stops}
        stopIndex={stopIndex}
        onSelectStop={goToStop}
        onSelectFeature={(pick) => {
          setSelection(pick)
          setTranslationId(null)
          if (pick && drawer === 'peek') showDrawer()
        }}
        selectedId={selected ? selected.properties.id : null}
        aheadFrom={state.stepping ? (stop?.properties.sequence ?? null) : null}
        onHome={() => {
          dispatch({ type: 'home' })
          frameStops(mapRef.current, stops)
        }}
        onView={setView}
        reached={reached}
        corridor={corridor}
      />
      <Panel
        header={<ReadingProgress progress={progress} isSet={isSet} episodes={episodes} onSet={setProgress} />}
        search={<SearchBox places={flat?.places.features ?? []} stops={flat?.stops.features ?? []} translations={translations} onPick={onPick} />}
        card={card}
        failed={loaded === 'failed'}
        journey={journey}
        journeys={journeys}
        elsewhere={elsewhere}
        stops={stops}
        stopIndex={stopIndex}
        spokenAtStop={stop ? (spokenAt.get(stop.properties.id) ?? []) : []}
        spokenOnRoad={roadAhead ? (spokenAt.get(roadAhead.properties.id)?.length ?? 0) : 0}
        onShowRoad={() => {
          if (!roadAhead) return
          setTranslationId(null)
          showRoad(roadAhead.properties.id)
        }}
        currentTranslation={translationId}
        onJourney={(journey) => dispatch({ type: 'journey', journey })}
        onStop={goToStop}
        phone={phone}
        drawer={drawer}
        onDrawer={setDrawer}
      />
      {route !== '/' && (
        <Suspense fallback={null}>
          <Pages route={route} />
        </Suspense>
      )}
    </main>
  )
}
