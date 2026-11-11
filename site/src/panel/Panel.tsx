import type { Feature, Point } from 'geojson'
import type { StoryProps } from '../data/story'

const JOURNEYS: Record<string, string> = {
  J1: 'The she-wolf, north out of Sonora',
  J2: "Billy's first crossing, with the wolf",
}

type Props = {
  failed: boolean
  journey: string
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  onJourney: (journey: string) => void
  onStop: (index: number) => void
}

export function Panel({ failed, journey, stops, stopIndex, onJourney, onStop }: Props) {
  const stop = stops[stopIndex]
  return (
    <aside className="panel" aria-label="Journey">
      <label className="journey-pick">
        <span>Journey</span>
        <select value={journey} onChange={(e) => onJourney(e.target.value)}>
          {Object.entries(JOURNEYS).map(([id, title]) => (
            <option key={id} value={id}>
              {id}. {title}
            </option>
          ))}
        </select>
      </label>

      {failed && <p role="alert">The story data could not be loaded. Try reloading the page.</p>}

      {stop && (
        <section className="stop" aria-live="polite">
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
          {stop.properties.reasoning && <p>{stop.properties.reasoning}</p>}
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
          <li key={f.properties.id}>
            <button type="button" aria-current={i === stopIndex ? 'step' : undefined} onClick={() => onStop(i)}>
              {f.properties.name}
            </button>
          </li>
        ))}
      </ol>
    </aside>
  )
}
