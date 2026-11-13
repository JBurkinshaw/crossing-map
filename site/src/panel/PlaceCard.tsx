import { useEffect, useRef, type ReactNode } from 'react'
import type { Feature, Geometry } from 'geojson'
import type { StoryProps } from '../data/story'
import type { Translation } from '../data/translations'
import { TranslationList } from './TranslationList'

const KIND: Record<string, string> = {
  'inferred-area': 'Inferred area',
  region: 'Region',
  'route-segment': 'Route segment',
}

type Props = {
  feature: Feature<Geometry, StoryProps>
  // The translations whose location_ref is this feature, already filtered to the reader's progress.
  spoken: Translation[]
  currentTranslation: string | null
  onClose: () => void
  // A route segment's card (talk on the road) is titled "On the road between X and Y" and says how its lines
  // were placed.
  title?: string
  spokenTitle?: string
  spokenNote?: ReactNode
}

// The card for a place or area picked on the map or in search, or for the road a line was spoken on: what it
// is, how it was placed, and what was said there in Spanish ("Spoken here", plan section 8).
export function PlaceCard({ feature, spoken, currentTranslation, onClose, title, spokenTitle = 'Spoken here', spokenNote }: Props) {
  const p = feature.properties
  const card = useRef<HTMLElement>(null)
  useEffect(() => {
    card.current?.scrollIntoView({ block: 'nearest' })
  }, [p.id])
  return (
    <section ref={card} className="place-card" aria-live="polite" data-first-seen={p.first_seen} data-role={p.role ?? undefined}>
      <button type="button" className="close" aria-label="Close" onClick={onClose}>
        ×
      </button>
      <h2>{title ?? p.name}</h2>
      <div className="meta">
        {KIND[p.kind ?? ''] ?? p.kind} · {p.certainty}
        {p.uncertainty_m ? `, within about ${p.uncertainty_m / 1000} km` : ''} · {p.source}
        {p.source_id ? ` ${p.source_id}` : ''}
      </div>
      {(p.note_full || p.note_safe) && <p>{p.note_full || p.note_safe}</p>}
      {p.reasoning && <p>{p.reasoning}</p>}
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
