import type { Feature, Point } from 'geojson'
import { JOURNEYS } from '../data/journeys'
import type { StoryProps } from '../data/story'
import type { Translation } from '../data/translations'
import { synopsisFolded } from '../panel/folds'
import { TranslationList } from '../panel/TranslationList'

type Props = {
  // The stops the reader has reached, and the Spanish the panel lists at each.
  stops: Feature<Point, StoryProps>[]
  spoken: (stop: string) => Translation[]
  // The episode being read: a stop in it folds its synopsis, as the panel does (decision 0051).
  reached: string
  // Whether anything is hidden.
  spoilers: boolean
}

// The journeys as text (decision 0062): each journey's stops in order, with what the panel says at each. The map
// draws its routes and places on a canvas, which a screen reader cannot read, so this page is the map's text
// alternative. It also reads without the map at all.
export function Itinerary({ stops, spoken, reached, spoilers }: Props) {
  const journeys = [...new Set(stops.flatMap((s) => s.properties.journey ?? []))].sort()
  return (
    <>
      <p className="lede">
        Every journey in the book, stop by stop, as text: what happens at each stop, and the Spanish spoken there with
        this site’s English.
        {spoilers && ' Stops you have not reached yet stay hidden.'}
      </p>
      {journeys.length === 0 && <p className="meta">No journey has begun by this point in the book.</p>}
      {journeys.map((j) => (
        <section key={j} className="itinerary">
          <h2>
            {j}. {JOURNEYS[j] ?? j}
          </h2>
          <ol>
            {stops
              .filter((s) => s.properties.journey === j)
              .sort((a, b) => (a.properties.sequence ?? 0) - (b.properties.sequence ?? 0))
              .map(({ properties: p }) => {
                const lines = spoken(p.id)
                return (
                  <li key={p.id} data-first-seen={p.first_seen}>
                    <h3>{p.name}</h3>
                    {p.synopsis &&
                      (synopsisFolded(p.first_seen, reached) ? (
                        <details>
                          <summary>What happens here</summary>
                          <p>{p.synopsis}</p>
                        </details>
                      ) : (
                        <p>{p.synopsis}</p>
                      ))}
                    {lines.length > 0 && (
                      <details>
                        <summary>Spanish here ({lines.length})</summary>
                        <TranslationList items={lines} current={null} />
                      </details>
                    )}
                  </li>
                )
              })}
          </ol>
        </section>
      ))}
    </>
  )
}
