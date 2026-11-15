import type { ReactNode } from 'react'
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
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  // What was said in Spanish at the current stop, and the line picked in search, if any.
  spokenAtStop: Translation[]
  // Lines spoken on the road from the current stop to the next (talk on the road), and how to show that road.
  spokenOnRoad: number
  onShowRoad: () => void
  currentTranslation: string | null
  onJourney: (journey: string) => void
  onStop: (index: number) => void
  // Whether "How this was placed" is open: App holds it, so it stays as the reader left it between stops.
  placementOpen: boolean
  onPlacement: (open: boolean) => void
  // On phones the panel is a bottom drawer (Drawer.tsx) at this height.
  phone: boolean
  drawer: DrawerHeight
  onDrawer: (height: DrawerHeight) => void
}

export function Panel(props: Props) {
  const { header, search, card, failed, failures, journey, journeys, elsewhere, stops, stopIndex, spokenAtStop, currentTranslation, onJourney, onStop } = props
  const { spokenOnRoad, onShowRoad } = props
  const { phone, drawer, onDrawer, units, questions, placementOpen, onPlacement } = props
  const stop = stops[stopIndex]
  // The stop the road from this one leads to.
  const next = stops[stopIndex + 1]

  const links = (
    <nav className="site-links" aria-label="Pages">
      <a href="#/about">About</a>
      <a href="#/about/how-its-built">How it’s built</a>
      <a href="#/open-questions">Open questions</a>
      <a href="#/data">Data</a>
      <a href="#/credits">Credits</a>
      <button type="button" className="link" onClick={showIntroduction}>
        Introduction
      </button>
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
      <h2>{stop.properties.name}</h2>
      {(stop.properties.note_full || stop.properties.note_safe) && <p>{stop.properties.note_full || stop.properties.note_safe}</p>}
      {/* Open or closed as the reader last left it, from stop to stop and journey to journey. */}
      <details className="placement" open={placementOpen} onToggle={(e) => onPlacement(e.currentTarget.open)}>
        <summary>How this was placed</summary>
        <div className="meta">
          {stop.properties.certainty}
          {stop.properties.uncertainty_m ? `, within about ${distance(stop.properties.uncertainty_m, units)}` : ''} ·{' '}
          {stop.properties.source}
          {stop.properties.source_id ? ` ${stop.properties.source_id}` : ''}
        </div>
        {stop.properties.reasoning && <p>{stop.properties.reasoning}</p>}
      </details>
      <FeatureQuestions id={stop.properties.id} name={stop.properties.name} questions={questions} />
      {spokenAtStop.length > 0 && (
        <>
          <h3>Spoken here</h3>
          <TranslationList key={stop.properties.id} items={spokenAtStop} current={currentTranslation} />
        </>
      )}
      {/* Talk on the road to the next stop: its own block, so it does not run on from the stop's lines above,
          and a button that opens the road's card (only that road's lines) and outlines the road on the map. */}
      {spokenOnRoad > 0 && (
        <div className="road-ahead">
          <h3>On the road{next ? ` to ${next.properties.name}` : ''}</h3>
          <button type="button" className="road-lines" onClick={onShowRoad}>
            Show the {spokenOnRoad === 1 ? 'line' : `${spokenOnRoad} lines`} spoken on this road, and the road on the map
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
  // page links. Phones put the stepper in the drawer's peek row, nearest the thumb, and the journey and its
  // stops straight under it; search and progress follow, as the drawer opens half way.
  if (phone) {
    return (
      <Drawer label="Journey" height={drawer} onHeight={onDrawer} peek={stepper}>
        {journeyPick}
        {stopList}
        {search}
        {header}
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
