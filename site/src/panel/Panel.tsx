import type { ReactNode } from 'react'
import type { Feature, Point } from 'geojson'
import { JOURNEYS } from '../data/journeys'
import type { Elsewhere, StoryProps } from '../data/story'
import type { Translation } from '../data/translations'
import { TranslationList } from './TranslationList'

type Props = {
  // The reading-progress badge, at the top of the panel.
  header: ReactNode
  // The search box, and the card for whatever was picked on the map or in search.
  search: ReactNode
  card: ReactNode
  failed: boolean
  journey: string
  // The journeys drawn so far, each with the episode it starts in, and the places named outside the map.
  journeys: { id: string; first_seen: string }[]
  elsewhere: Elsewhere[]
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  // What was said in Spanish at the current stop, and the line picked in search, if any.
  spokenAtStop: Translation[]
  currentTranslation: string | null
  onJourney: (journey: string) => void
  onStop: (index: number) => void
}

export function Panel(props: Props) {
  const { header, search, card, failed, journey, journeys, elsewhere, stops, stopIndex, spokenAtStop, currentTranslation, onJourney, onStop } = props
  const stop = stops[stopIndex]
  return (
    <aside className="panel" aria-label="Journey">
      <nav className="site-links" aria-label="Pages">
        <a href="#/about">About</a>
        <a href="#/about/how-its-built">How it’s built</a>
        <a href="#/data">Data</a>
        <a href="#/credits">Credits</a>
      </nav>

      {header}
      {search}
      {card}
      {journeys.length > 0 ? (
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
      )}

      {failed && <p role="alert">The story data could not be loaded. Try reloading the page.</p>}

      {stop && (
        <section className="stop" aria-live="polite" data-first-seen={stop.properties.first_seen}>
          <div className="stop-count">
            Stop {stopIndex + 1} of {stops.length}
          </div>
          <h2>{stop.properties.name}</h2>
          <div className="meta">
            {stop.properties.certainty}
            {stop.properties.uncertainty_m ? `, within about ${stop.properties.uncertainty_m / 1000} km` : ''} ·{' '}
            {stop.properties.source}
            {stop.properties.source_id ? ` ${stop.properties.source_id}` : ''}
          </div>
          {(stop.properties.note_full || stop.properties.note_safe) && <p>{stop.properties.note_full || stop.properties.note_safe}</p>}
          {stop.properties.reasoning && <p>{stop.properties.reasoning}</p>}
          {spokenAtStop.length > 0 && (
            <>
              <h3>Spoken here</h3>
              <TranslationList key={stop.properties.id} items={spokenAtStop} current={currentTranslation} />
            </>
          )}
        </section>
      )}

      <div className="stepper">
        <button type="button" onClick={() => onStop(stopIndex - 1)} disabled={stopIndex === 0}>
          Back
        </button>
        <button type="button" onClick={() => onStop(stopIndex + 1)} disabled={stopIndex >= stops.length - 1}>
          Next
        </button>
      </div>

      <ol className="stop-list">
        {stops.map((f, i) => (
          <li key={f.properties.id} data-first-seen={f.properties.first_seen}>
            <button type="button" aria-current={i === stopIndex ? 'step' : undefined} onClick={() => onStop(i)}>
              {f.properties.name}
            </button>
          </li>
        ))}
      </ol>

      {elsewhere.length > 0 && (
        <section className="elsewhere">
          <h3>Named elsewhere</h3>
          <p className="meta">Places the book names that lie beyond this map.</p>
          <ul>
            {elsewhere.map((e) => (
              <li key={e.id} data-first-seen={e.first_seen}>
                {e.name}
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  )
}
