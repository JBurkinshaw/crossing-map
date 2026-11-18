import { useEffect, useRef, useState, type ReactNode } from 'react'
import { showIntroduction } from '../welcome/showIntroduction'
import type { Feature, Point } from 'geojson'
import { JOURNEYS } from '../data/journeys'
import type { Elsewhere, StoryProps } from '../data/story'
import type { Translation } from '../data/translations'
import { Drawer, type DrawerHeight } from './Drawer'
import { TranslationList } from './TranslationList'
import { distance, type Units } from '../units'
import type { OpenQuestion } from '../data/openQuestions'
import { FeatureQuestions } from './OpenQuestions'
import { episodeLabel, progressLabel, type Episode } from '../spoiler/progress'
import { CERTAINTY_LABEL } from './certainty'
import { synopsisFolded } from './folds'

type Props = {
  units: Units
  // Open questions reached so far; the stop shows those about it.
  questions: OpenQuestion[]
  // The reading-progress badge, at the top of the panel.
  header: ReactNode
  // The search box, and the card for whatever was picked on the map or in search.
  search: ReactNode
  card: ReactNode
  // The story layers failed to load, and the other files that did (named for the reader).
  failed: boolean
  failures: string[]
  journey: string
  // The journeys drawn so far, each with the episode it starts in, and the places named outside the map.
  journeys: { id: string; first_seen: string }[]
  elsewhere: Elsewhere[]
  // The episodes reached so far: the stop section says what happens in its stop's episode.
  episodes: Episode[]
  // The episode being read ('9-99' once the book is finished): a stop's synopsis folds while its episode is read.
  reached: string
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  // What was said in Spanish at the current stop (less the common lines), and the line picked in search, if any.
  spokenAtStop: Translation[]
  // Lines spoken on the road from the current stop to the next (talk on the road), and how to show that road.
  spokenOnRoad: number
  onShowRoad: () => void
  // At the stop the reader reached most recently, the next episode's label, and how to set progress to it.
  readOn: string | null
  onReadOn: () => void
  currentTranslation: string | null
  onJourney: (journey: string) => void
  onStop: (index: number) => void
  // Whether "How this was placed" is open: App holds it, so it stays as the reader left it between stops.
  placementOpen: boolean
  onPlacement: (open: boolean) => void
  // Whether "Spanish here" is open: closed at first, then as the reader left it, on later visits too.
  spanishOpen: boolean
  onSpanish: (open: boolean) => void
  // On phones the panel is a bottom drawer (Drawer.tsx) at this height.
  phone: boolean
  drawer: DrawerHeight
  onDrawer: (height: DrawerHeight) => void
}

export function Panel(props: Props) {
  const { header, search, card, failed, failures, journey, journeys, elsewhere, stops, stopIndex, spokenAtStop, currentTranslation, onJourney, onStop } = props
  const { spokenOnRoad, onShowRoad, readOn, onReadOn } = props
  const { phone, drawer, onDrawer, units, questions, placementOpen, onPlacement, episodes, reached } = props
  const { spanishOpen, onSpanish } = props
  const stop = stops[stopIndex]
  // The stop's episode: reached, as the stop is, so its summary is safe to show.
  const episode = stop && episodes.find((e) => e.episode === stop.properties.episode)
  // The stop the road from this one leads to.
  const next = stops[stopIndex + 1]
  const synopsis = stop?.properties.synopsis
  // A line picked in search opens "Spanish here", whatever the reader left it as, so the line can be seen. The reader
  // can still close it, and the fold then stays shut for that line.
  const [shutOnPick, setShutOnPick] = useState<string | null>(null)
  // A new pick, or the same line picked again after another, opens the fold afresh.
  const [lastPick, setLastPick] = useState(currentTranslation)
  if (lastPick !== currentTranslation) {
    setLastPick(currentTranslation)
    setShutOnPick(null)
  }
  const picked = spokenAtStop.some((t) => t.id === currentTranslation) && shutOnPick !== currentTranslation
  const spanishShown = spanishOpen || picked
  // The toggle event also fires when the open prop changes; only a change the reader made is saved.
  const toggleSpanish = (open: boolean) => {
    if (open === spanishShown) return
    if (!open && picked) setShutOnPick(currentTranslation)
    onSpanish(open)
  }
  // "Read on" can vanish with the stop it was on, so focus moves to the stop's name once the new episode shows.
  const heading = useRef<HTMLHeadingElement>(null)
  const readingOn = useRef(false)
  useEffect(() => {
    if (!readingOn.current) return
    readingOn.current = false
    heading.current?.focus()
  }, [reached])

  // What the site is, and the two pages a new reader wants first; the footer links hold the rest.
  const siteHeader = (
    <header className="panel-header">
      <p className="panel-title">
        <cite>The Crossing</cite> · a reading map
      </p>
      <nav aria-label="About this site">
        <a href="#/about">About</a>
        <button type="button" className="link" onClick={showIntroduction}>
          Introduction
        </button>
      </nav>
    </header>
  )

  const links = (
    <nav className="site-links" aria-label="Pages">
      <a href="#/about/how-its-built">How it’s built</a>
      <a href="#/open-questions">Open questions</a>
      <a href="#/data">Data</a>
      <a href="#/credits">Credits</a>
    </nav>
  )

  const journeyPick =
    journeys.length > 0 ? (
      <label className="journey-pick">
        <span>Journey</span>
        <select value={journey} onChange={(e) => onJourney(e.target.value)}>
          {journeys.map(({ id, first_seen }) => (
            <option key={id} value={id} data-first-seen={first_seen}>
              {id}. {JOURNEYS[id] ?? id}
            </option>
          ))}
        </select>
      </label>
    ) : (
      !failed && <p className="meta">No journey has begun by this point in the book.</p>
    )

  const failure = (failed || failures.length > 0) && (
    <p role="alert">
      {failed ? 'The story data could not be loaded.' : `Some data could not be loaded: ${failures.join(', ')}.`} Try reloading the page.
    </p>
  )

  const stopSection = stop && (
    <section className="stop" data-first-seen={stop.properties.first_seen}>
      <h2 ref={heading} tabIndex={-1}>
        {stop.properties.name}
      </h2>
      {/* What happens here: the stop's episode and its summary in the faint meta style, written to give nothing away
          past its opening. Then, below a rule, the stop's own synopsis at full ink (decision 0052), which can tell the
          rest of the episode. While that episode is being read the synopsis is folded, and the fold starts closed on
          every stop (keyed by stop), so each one is the reader's choice (decision 0051). */}
      {episode && (
        <div className="stop-episode" data-first-seen={episode.episode}>
          <p className="meta" title="The book has no chapter titles. Each episode is named by the words it opens with, which the book sets in capitals.">
            {progressLabel(episode.episode, episodes)}
          </p>
          <p className="meta">{episode.summary}</p>
        </div>
      )}
      {synopsis &&
        (synopsisFolded(stop.properties.first_seen, reached) ? (
          <details key={stop.properties.id} className="synopsis">
            <summary>What happens here</summary>
            <p>{synopsis}</p>
          </details>
        ) : (
          <p className="synopsis">{synopsis}</p>
        ))}
      {(stop.properties.note_full || stop.properties.note_safe) && <p>{stop.properties.note_full || stop.properties.note_safe}</p>}
      {/* Open or closed as the reader last left it, from stop to stop and journey to journey. */}
      <details className="placement" open={placementOpen} onToggle={(e) => onPlacement(e.currentTarget.open)}>
        <summary>How this was placed</summary>
        <p className="meta">
          {CERTAINTY_LABEL[stop.properties.certainty]}
          {stop.properties.uncertainty_m ? ` · within about ${distance(stop.properties.uncertainty_m, units)}` : ''}
        </p>
        {stop.properties.reasoning && <p>{stop.properties.reasoning}</p>}
        <p className="meta">
          Source: {stop.properties.source}
          {stop.properties.source_id ? ` ${stop.properties.source_id}` : ''}
        </p>
      </details>
      <FeatureQuestions id={stop.properties.id} name={stop.properties.name} questions={questions} />
      {spokenAtStop.length > 0 && (
        <details className="spanish-here" open={spanishShown} onToggle={(e) => toggleSpanish(e.currentTarget.open)}>
          <summary>
            <h3>Spanish here ({spokenAtStop.length})</h3>
          </summary>
          <TranslationList key={stop.properties.id} items={spokenAtStop} current={currentTranslation} />
        </details>
      )}
      {/* Talk on the road to the next stop: its own block, so it does not run on from the stop's lines above,
          and a button that opens the road's card (only that road's lines) and outlines the road on the map. */}
      {spokenOnRoad > 0 && (
        <div className="road-ahead">
          <h3>On the road{next ? ` to ${next.properties.name}` : ''}</h3>
          <button type="button" className="road-lines" onClick={onShowRoad}>
            Show the {spokenOnRoad === 1 ? 'line' : `${spokenOnRoad} lines`} of Spanish on this road, and the road on the map
          </button>
        </div>
      )}
      {/* The end of what the reader has reached: reading on shows one more episode (decision 0053). */}
      {readOn && (
        <div className="read-on">
          <p className="meta">Finished {episodeLabel(reached)}?</p>
          <button
            type="button"
            onClick={() => {
              readingOn.current = true
              onReadOn()
            }}
          >
            Read on: {readOn}
          </button>
        </div>
      )}
    </section>
  )

  // The stepper counts the stops between its buttons; on phones it also names the stop, so the drawer at peek
  // height says where you are.
  const stepper = (
    <div className="stepper">
      <button type="button" onClick={() => onStop(stopIndex - 1)} disabled={stopIndex === 0}>
        Back
      </button>
      {stop && (
        <div className="stepper-stop">
          <span className="stop-count" aria-live="polite">
            Stop {stopIndex + 1} of {stops.length}
          </span>
          {phone && (
            <span className="stepper-name" aria-hidden="true">
              {stop.properties.name}
            </span>
          )}
        </div>
      )}
      <button type="button" onClick={() => onStop(stopIndex + 1)} disabled={stopIndex >= stops.length - 1}>
        Next
      </button>
    </div>
  )

  const stopList = stops.length > 0 && (
    <details className="more all-stops">
      <summary>All stops ({stops.length})</summary>
      <ol className="stop-list">
        {stops.map((f, i) => (
          <li key={f.properties.id} data-first-seen={f.properties.first_seen}>
            <button type="button" aria-current={i === stopIndex ? 'step' : undefined} onClick={() => onStop(i)}>
              {f.properties.name}
            </button>
          </li>
        ))}
      </ol>
    </details>
  )

  const elsewhereList = elsewhere.length > 0 && (
    <details className="more elsewhere">
      <summary>Named elsewhere ({elsewhere.length})</summary>
      <p className="meta">Places the book names that lie beyond this map.</p>
      <ul>
        {elsewhere.map((e) => (
          <li key={e.id} data-first-seen={e.first_seen}>
            {e.name}
          </li>
        ))}
      </ul>
    </details>
  )

  // The panel reads from the general to the particular: reading progress and search, which govern the whole
  // map; then the way through a journey (which journey, Back and Next, all its stops); then what is in focus
  // (the card for a pick on the map or in search, and the current stop); then places beyond the map and the
  // page links. Phones put the stepper in the drawer's peek row, nearest the thumb; then reading progress, so the
  // drawer opened half way says how much the map hides; then the journey and its stops, then search.
  if (phone) {
    return (
      <Drawer label="Journey" height={drawer} onHeight={onDrawer} peek={stepper}>
        {siteHeader}
        {header}
        {journeyPick}
        {stopList}
        {search}
        {failure}
        {card}
        {stopSection}
        {elsewhereList}
        {links}
      </Drawer>
    )
  }

  return (
    <aside className="panel" aria-label="Journey">
      {siteHeader}
      {header}
      {search}
      {journeyPick}
      {failure}
      {stepper}
      {stopList}
      {card}
      {stopSection}
      {elsewhereList}
      {links}
    </aside>
  )
}
