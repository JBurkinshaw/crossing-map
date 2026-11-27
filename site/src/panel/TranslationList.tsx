import { useEffect, useRef, useState, type RefObject } from 'react'
import { countEvent } from '../analytics'
import { CAMPBELL_CREDIT, CAMPBELL_GUIDE, type Translation } from '../data/translations'
import { feedbackUrl } from '../pages/format'
import { episodeLabel } from '../spoiler/progress'

const SHOWN_AT_FIRST = 6

type Props = {
  items: Translation[]
  // The line the reader picked in search, marked and scrolled to.
  current: string | null
}

// The translations are drafts: readers who know the Spanish, northern Mexican usage above all, review them.
const suggestion = (t: Translation) => feedbackUrl({ kind: 'translation', line: t.id, episode: t.episode })

// Lines of Spanish with this site's English (design sections 3 and 8): the opening words only, our English, and a
// link to suggest better English. "About this translation" holds the episode, our confidence, and the Campbell
// guide's page where it lists the line, with the credit the design asks for on each.
// A long list that spans several episodes is grouped by episode, in the order the lines come: the first group
// starts open, and so does the one holding the line picked in search.
export function TranslationList({ items, current }: Props) {
  const marked = useRef<HTMLLIElement>(null)
  // Braces: scrollIntoView can return a promise, which an effect must not.
  useEffect(() => {
    marked.current?.scrollIntoView({ block: 'nearest' })
  }, [current])
  const episodes = [...new Set(items.map((t) => t.episode))]
  if (items.length <= SHOWN_AT_FIRST || episodes.length === 1) return <Lines items={items} current={current} marked={marked} />
  return episodes.map((episode, i) => {
    const lines = items.filter((t) => t.episode === episode)
    return (
      <details key={episode} className="translation-group" open={i === 0 || lines.some((t) => t.id === current)}>
        <summary>
          {episodeLabel(episode)} ({lines.length})
        </summary>
        <Lines items={lines} current={current} marked={marked} />
      </details>
    )
  })
}

// The first few lines, then all of them at a click (or at once, if the line picked in search is further down).
function Lines({ items, current, marked }: Props & { marked: RefObject<HTMLLIElement | null> }) {
  const [all, setAll] = useState(false)
  const currentAt = items.findIndex((t) => t.id === current)
  const shown = all || currentAt >= SHOWN_AT_FIRST ? items : items.slice(0, SHOWN_AT_FIRST)
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
            {suggestion(t) && (
              <div className="meta">
                <a
                  href={suggestion(t) ?? undefined}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => countEvent('feedback-translation')}
                >
                  Suggest a better translation
                </a>
              </div>
            )}
            {/* The fine print, folded away: most readers want only the line and its English. */}
            <details className="translation-about meta">
              <summary>About this translation</summary>
              <p>{episodeLabel(t.episode)}</p>
              <p>Added by this site{t.confidence ? `, ${t.confidence} confidence` : ''}</p>
              {t.guide_page && (
                <p>
                  <a href={CAMPBELL_GUIDE} target="_blank" rel="noopener">
                    {CAMPBELL_CREDIT}
                  </a>
                  , listed under page {t.guide_page}
                </p>
              )}
            </details>
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
