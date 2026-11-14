import { lazy, Suspense, useMemo, useRef, useState } from 'react'
import { ChunkBoundary } from './ChunkBoundary'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { Feature, Geometry } from 'geojson'
import { useOpenQuestions } from './data/openQuestions'
import { useElsewhere, useStory, type StoryProps } from './data/story'
import { useTranslations, type Translation } from './data/translations'
import { CORRIDOR_M } from './map/corridor'
import { MapView } from './map/MapView'
import { useMapMode } from './map/mode'
import type { Corridor } from './map/StoryLayers'
import { useNavigation } from './navigation'
import type { DrawerHeight } from './panel/Drawer'
import { Panel } from './panel/Panel'
import { PlaceCard } from './panel/PlaceCard'
import { SearchBox } from './panel/SearchBox'
import { TranslationList } from './panel/TranslationList'
import { usePhone } from './panel/usePhone'
import { useRoute } from './route'
import { shownAt, storyUpTo, translationsUpTo } from './spoiler/filter'
import { reachedEpisode, spoilersHidden, useEpisodes, useProgress } from './spoiler/progress'
import { ReadingProgress } from './spoiler/ReadingProgress'
import { byId, roadLabel } from './story/select'
import { distance, useUnits } from './units'

// The About, How it's built, Data and Credits pages, loaded the first time one opens.
const Pages = lazy(() => import('./pages/Pages'))
// The owner's review of the modelled routes (?review=routes). Dev server only: a production build drops it.
const RouteReview = import.meta.env.DEV ? lazy(() => import('./review/RouteReview')) : null
const reviewing = import.meta.env.DEV && new URLSearchParams(window.location.search).get('review') === 'routes'

const NO_LIST: never[] = []

export default function App() {
  const route = useRoute()
  const loadedAll = useStory()
  const elsewhereAll = useElsewhere()
  const translationsAll = useTranslations(loadedAll !== null)
  const questionsAll = useOpenQuestions()
  // Spoiler mode: everything below sees only what the reader has reached (spoiler/filter.ts).
  const { progress, isSet, setProgress } = useProgress()
  const episodesLoaded = useEpisodes()
  const episodes = episodesLoaded.data ?? NO_LIST
  const reached = reachedEpisode(progress)
  const spoilers = spoilersHidden(progress, episodes)
  const loaded = useMemo(
    () => (loadedAll && loadedAll !== 'failed' ? storyUpTo(loadedAll, reached, spoilers) : loadedAll),
    [loadedAll, reached, spoilers],
  )
  const elsewhere = useMemo(() => (elsewhereAll.data ?? NO_LIST).filter((e) => shownAt(e, reached)), [elsewhereAll, reached])
  const questions = useMemo(() => (questionsAll.data ?? NO_LIST).filter((q) => shownAt(q, reached)), [questionsAll, reached])
  const translations = useMemo(() => translationsUpTo(translationsAll.data ?? NO_LIST, reached), [translationsAll, reached])
  const spokenAt = useMemo(() => {
    const at = new Map<string, Translation[]>()
    for (const t of translations) if (t.location_ref) at.set(t.location_ref, [...(at.get(t.location_ref) ?? []), t])
    return at
  }, [translations])
  const { basemap, chooseBasemap, view, setView } = useMapMode()
  // The Raised view draws the story where the raised line work puts it: the copies in data/raised/, fetched the
  // first time the reader turns it on.
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
  // "How this was placed" stays open or closed as the reader left it, whichever stop shows.
  const [placementOpen, setPlacementOpen] = useState(false)
  const [units, setUnits] = useUnits()
  // Phones: the panel is a bottom drawer. It opens half way, so the reading-progress badge and search show.
  const phone = usePhone()
  const [drawer, setDrawer] = useState<DrawerHeight>('half')
  const nav = useNavigation({
    mapRef,
    story,
    flat,
    translations,
    showCard: (from) => setDrawer((d) => (from === 'search' || d === 'peek' ? 'half' : d)),
  })
  const { stops, stopIndex, selection, translationId, setSelection, setTranslationId } = nav

  // Data the panel says could not be loaded; the story layers have their own message.
  const failures = [
    episodesLoaded.failed && 'the reading-progress episodes',
    translationsAll.failed && 'the translations',
    questionsAll.failed && 'the open questions',
    elsewhereAll.failed && 'the places named elsewhere',
  ].filter((f): f is string => !!f)

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
      units={units}
      questions={questions}
      title={roadLabel(flat, road)}
      spoken={spokenAt.get(road.properties.id) ?? []}
      spokenTitle="Spoken on this road"
      spokenNote={`The book does not say where these lines were spoken. The episode travels this road, so this site places them along it: the map outlines the route with ${distance(CORRIDOR_M, units)} either side.`}
      currentTranslation={translationId}
      onClose={() => {
        setSelection(null)
        setTranslationId(null)
      }}
    />
  ) : selected ? (
    <PlaceCard
      feature={selected}
      units={units}
      questions={questions}
      spoken={spokenAt.get(selected.properties.id) ?? []}
      currentTranslation={translationId}
      onClose={() => setSelection(null)}
    />
  ) : (
    translation &&
    !placed && (
      <section className="place-card">
        <button type="button" className="close" aria-label="Close" onClick={() => setTranslationId(null)}>
          ×
        </button>
        <h3 aria-live="polite">Said on the way</h3>
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
        onSelectStop={nav.goToStop}
        onMapClick={nav.onMapClick}
        selectedId={selected ? selected.properties.id : null}
        aheadFrom={nav.stepping ? (stop?.properties.sequence ?? null) : null}
        onHome={nav.onHome}
        basemap={basemap}
        onBasemap={chooseBasemap}
        view={view}
        onView={setView}
        reached={reached}
        raisedFailed={raisedAll === 'failed'}
        corridor={corridor}
        units={units}
        onUnits={setUnits}
      />
      {reviewing && RouteReview ? (
        <Suspense fallback={null}>
          <RouteReview mapRef={mapRef} />
        </Suspense>
      ) : (
        <Panel
          units={units}
          questions={questions}
          header={
            <ReadingProgress progress={progress} isSet={isSet} episodes={episodes} episodesFailed={episodesLoaded.failed} onSet={setProgress} />
          }
          search={<SearchBox places={flat?.places.features ?? []} stops={flat?.stops.features ?? []} translations={translations} onPick={nav.onPick} />}
          card={card}
          failed={loaded === 'failed'}
          failures={failures}
          journey={nav.journey}
          journeys={nav.journeys}
          elsewhere={elsewhere}
          stops={stops}
          stopIndex={stopIndex}
          spokenAtStop={stop ? (spokenAt.get(stop.properties.id) ?? []) : []}
          spokenOnRoad={roadAhead ? (spokenAt.get(roadAhead.properties.id)?.length ?? 0) : 0}
          onShowRoad={() => {
            if (!roadAhead) return
            setTranslationId(null)
            nav.showRoad(roadAhead.properties.id)
          }}
          currentTranslation={translationId}
          onJourney={nav.onJourney}
          onStop={nav.goToStop}
          placementOpen={placementOpen}
          onPlacement={setPlacementOpen}
          phone={phone}
          drawer={drawer}
          onDrawer={setDrawer}
        />
      )}
      {route !== '/' && (
        <ChunkBoundary
          fallback={
            <p className="notice" role="alert">
              This page could not load. Reload the page to try again.
            </p>
          }
        >
          <Suspense fallback={null}>
            <Pages route={route} questions={questions} />
          </Suspense>
        </ChunkBoundary>
      )}
    </main>
  )
}
