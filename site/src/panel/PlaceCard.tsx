import { useEffect, useRef, type ReactNode } from 'react'
import type { Feature, Geometry } from 'geojson'
import { routeLabel } from '../data/routeLabels'
import type { StoryProps } from '../data/story'
import type { Translation } from '../data/translations'
import { TranslationList } from './TranslationList'
import { FeatureQuestions } from './OpenQuestions'
import type { OpenQuestion } from '../data/openQuestions'
import { distance, type Units } from '../units'
import { CERTAINTY_LABEL } from './certainty'
import { FEEDBACK_FORM } from '../pages/format'

type Props = {
  feature: Feature<Geometry, StoryProps>
  units: Units
  // Open questions reached so far; the card shows those about this feature.
  questions: OpenQuestion[]
  // The translations whose location_ref is this feature, already filtered to the reader's progress.
  spoken: Translation[]
  currentTranslation: string | null
  onClose: () => void
  // A route segment's card (talk on the road) is titled "On the road between X and Y" and says how its lines
  // were placed.
  title?: string
  spokenTitle?: string
  spokenNote?: ReactNode
  // Whether "How this was placed" is open: shared with the stop section, so it stays as the reader left it.
  placementOpen: boolean
  onPlacement: (open: boolean) => void
  // For an inferred area: the stop it was worked out for, and how to go to it.
  stop?: Feature<Geometry, StoryProps>
  onStop?: (id: string) => void
}

// What kind of place it is, before how sure the map is of it: "Inferred area · Worked out from clues". The data's
// kinds are single words ("town", "range") apart from these two.
const KIND: Record<string, string> = { 'inferred-area': 'Inferred area', region: 'Region' }
const kindWord = (kind: string | undefined) => (kind ? `${KIND[kind] ?? kind[0].toUpperCase() + kind.slice(1)} · ` : '')

// The card for a place or area picked on the map or in search, or for the road a line was spoken on: what it
// is, how sure the map is of it and how it was placed, and what was said there in Spanish ("Spanish here", design
// section 8).
export function PlaceCard(props: Props) {
  const { feature, units, questions, spoken, currentTranslation, onClose, title, spokenTitle = 'Spanish here', spokenNote } = props
  const { placementOpen, onPlacement, stop, onStop } = props
  const p = feature.properties
  const card = useRef<HTMLElement>(null)
  // The card's top, with its title: a card taller than the panel would otherwise show its foot. When the card
  // marks a line picked in search, TranslationList scrolls to that line first, and 'nearest' leaves it in view.
  const marksLine = spoken.some((t) => t.id === currentTranslation)
  useEffect(() => {
    card.current?.scrollIntoView({ block: marksLine ? 'nearest' : 'start' })
  }, [p.id, marksLine])
  return (
    <section ref={card} className="place-card" data-first-seen={p.first_seen} data-role={p.role ?? undefined}>
      <button type="button" className="close" aria-label="Close" onClick={onClose}>
        ×
      </button>
      {/* Only the title is announced when a card opens: the whole card would be read out on every pick. */}
      <h2 aria-live="polite">{title ?? p.name}</h2>
      <div className="meta">
        {p.kind === 'route-segment' ? (routeLabel(p.method) ?? 'Route segment') : `${kindWord(p.kind)}${CERTAINTY_LABEL[p.certainty]}`}
        {p.uncertainty_m ? ` · within about ${distance(p.uncertainty_m, units)}` : ''}
      </div>
      {(p.note_full || p.note_safe) && <p>{p.note_full || p.note_safe}</p>}
      {stop && onStop && (
        <p className="area-stop">
          The area for {stop.properties.journey}, stop {stop.properties.sequence}:{' '}
          <button type="button" className="link" onClick={() => onStop(stop.properties.id)}>
            {stop.properties.name}
          </button>
        </p>
      )}
      <details className="placement" open={placementOpen} onToggle={(e) => onPlacement(e.currentTarget.open)}>
        <summary>How this was placed</summary>
        {p.reasoning && <p>{p.reasoning}</p>}
        <p className="meta">
          Source: {p.source}
          {p.source_id ? ` ${p.source_id}` : ''}
        </p>
      </details>
      {p.drawn && (
        <aside className="area-outline">
          <h3>How this line was drawn</h3>
          <p>{p.drawn}</p>
          {p.method === 'modeled' && (
            <p>
              <a href="#/about/how-its-built">How it’s built</a> explains the model.
            </p>
          )}
        </aside>
      )}
      {p.kind === 'inferred-area' && <AreaOutline rule={p.outline_rule ?? null} straightRoad={p.straight_road ?? false} />}
      <FeatureQuestions id={p.id} name={title ?? p.name} questions={questions} />
      {spoken.length > 0 && (
        <>
          <h3>{spokenTitle}</h3>
          {spokenNote && <p className="meta">{spokenNote}</p>}
          <TranslationList key={p.id} items={spoken} current={currentTranslation} />
        </>
      )}
    </section>
  )
}

// How an inferred area's outline was made, said plainly: a rule applied to data, not a drawing from a source,
// and open to change (decision 0020). The correction link itself is in FeatureQuestions, below on the card.
function AreaOutline({ rule, straightRoad }: { rule: string | null; straightRoad: boolean }) {
  return (
    <aside className="area-outline">
      <h3>How this area was drawn</h3>
      {rule ? (
        <p>
          A draft: the area around the stop, cut by a rule to the ground the reasoning describes. It was made by the rule from
          elevation, river and road data, not drawn by hand from a historical source. The rule: {rule}
        </p>
      ) : (
        <p>The area around the stop, as wide as the reasoning allows. Nothing in the book or the data narrows it further.</p>
      )}
      {straightRoad && (
        <p>
          No source this site has found maps the old roads here, so a straight line between the towns stands in for the road. A historical
          map of the roads would improve this area.
        </p>
      )}
      <p>
        If you know more, such as a page of the book, an old map or the ground itself, the area can be redrawn.
        {FEEDBACK_FORM && ' Suggest a correction below.'}
      </p>
    </aside>
  )
}
