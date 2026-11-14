import { useEffect, useRef, useState } from 'react'
import { CAMPBELL_CREDIT, CAMPBELL_GUIDE, type Translation } from '../data/translations'
import { issueUrl } from '../pages/format'
import { episodeLabel } from '../spoiler/progress'

const SHOWN_AT_FIRST = 6

type Props = {
  items: Translation[]
  // The line the reader picked in search, marked and scrolled to.
  current: string | null
}

// The translations are drafts: readers who know the Spanish, northern Mexican usage above all, review them.
function suggestion(t: Translation): string {
  return issueUrl(
    `Translation: ${t.id}`,
    `Line: ${t.id} (${t.episode}, page ${t.page ?? 'unknown'})\nSpanish begins: ${t.es_incipit}\nThe map's English: ${t.en ?? '(none yet)'}\n\nA better translation, and why:\n`,
  )
}

// Lines of Spanish with this site's English (plan sections 3 and 8): the opening words only, our English, the
// episode, and the Campbell guide's page where it lists the line, with the credit the plan asks for on each.
export function TranslationList({ items, current }: Props) {
  const [all, setAll] = useState(false)
  const currentAt = items.findIndex((t) => t.id === current)
  const shown = all || currentAt >= SHOWN_AT_FIRST ? items : items.slice(0, SHOWN_AT_FIRST)
  const marked = useRef<HTMLLIElement>(null)
  // Braces: scrollIntoView can return a promise, which an effect must not.
  useEffect(() => {
    marked.current?.scrollIntoView({ block: 'nearest' })
  }, [current])
  return (
    <>
      <ul className="translations">
        {shown.map((t) => (
          <li
            key={t.id}
            ref={t.id === current ? marked : undefined}
            aria-current={t.id === current ? 'true' : undefined}
            data-first-seen={t.first_seen}
          >
            <div>
              <span className="es" lang="es">
                {t.es_incipit}
              </span>
              {t.page && <span className="meta" title="Vintage edition, approximate"> p. {t.page}</span>}
            </div>
            <div className="en">{t.en ?? 'Translation still to come.'}</div>
            <div className="meta">
              {episodeLabel(t.episode)} · Added by this site{t.confidence ? `, ${t.confidence} confidence` : ''} ·{' '}
              <a href={suggestion(t)} target="_blank" rel="noreferrer">
                Suggest a better translation
              </a>
            </div>
            {t.guide_page && (
              <div className="meta">
                <a href={CAMPBELL_GUIDE} target="_blank" rel="noopener">
                  {CAMPBELL_CREDIT}
                </a>
                , listed under page {t.guide_page}
              </div>
            )}
          </li>
        ))}
      </ul>
      {shown.length < items.length && (
        <button type="button" className="text-button" onClick={() => setAll(true)}>
          Show all {items.length}
        </button>
      )}
    </>
  )
}
