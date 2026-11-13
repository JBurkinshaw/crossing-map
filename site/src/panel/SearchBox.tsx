import { useId, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import MiniSearch from 'minisearch'
import type { Feature, Point } from 'geojson'
import type { StoryProps } from '../data/story'
import type { Translation } from '../data/translations'
import { episodeLabel, PART_NUMERALS } from '../spoiler/progress'

// Search (docs/plan.md, sections 8 and 9): places, stops and translations in one box, accent- and
// case-insensitive, filtered by Part. It indexes only what it is given, and App gives it only what the
// reader has reached, so spoiler mode holds here too. The Spanish is indexed by its opening words only:
// the full spans are not published (plan section 3).

export type SearchHit = {
  id: string
  kind: 'place' | 'stop' | 'translation'
  // The feature or translation id.
  ref: string
  title: string
  en: string
  detail: string
  part: number | null
  first_seen: string
}

const fold = (s: string) => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()

const ROLE: Record<string, string> = {
  stop: 'Place on a journey',
  passing: 'Place passed or named',
  tale: 'Place in a tale',
  context: 'Town not named in the book',
}

const MAX_SHOWN = 20

type Props = {
  places: Feature<Point, StoryProps>[]
  stops: Feature<Point, StoryProps>[]
  translations: Translation[]
  onPick: (hit: SearchHit) => void
}

export function SearchBox({ places, stops, translations, onPick }: Props) {
  const id = useId()
  const [query, setQuery] = useState('')
  const [part, setPart] = useState(0)
  // Results close once one is picked, and open again as the reader types.
  const [open, setOpen] = useState(true)
  const list = useRef<HTMLUListElement>(null)
  const input = useRef<HTMLInputElement>(null)

  const index = useMemo(() => {
    const docs: SearchHit[] = [
      ...places.map((f) => ({
        id: `place:${f.properties.id}`,
        kind: 'place' as const,
        ref: f.properties.id,
        title: f.properties.name,
        en: '',
        detail: ROLE[f.properties.role ?? ''] ?? 'Place',
        part: f.properties.part ?? null,
        first_seen: f.properties.first_seen,
      })),
      ...stops.map((f) => ({
        id: `stop:${f.properties.id}`,
        kind: 'stop' as const,
        ref: f.properties.id,
        title: f.properties.name,
        en: '',
        detail: `${f.properties.journey}, stop ${f.properties.sequence}`,
        part: f.properties.part ?? null,
        first_seen: f.properties.first_seen,
      })),
      ...translations.map((t) => ({
        id: `translation:${t.id}`,
        kind: 'translation' as const,
        ref: t.id,
        title: t.es_incipit,
        en: t.en ?? '',
        detail: `${episodeLabel(t.episode)}${t.page ? `, p. ${t.page}` : ''}`,
        part: t.part,
        first_seen: t.first_seen,
      })),
    ]
    const search = new MiniSearch<SearchHit>({
      fields: ['title', 'en'],
      storeFields: ['kind', 'ref', 'title', 'en', 'detail', 'part', 'first_seen'],
      processTerm: (term) => fold(term),
      // On a name, the place comes first, then its stops, then lines said there.
      searchOptions: {
        prefix: true,
        fuzzy: (term) => (term.length > 4 ? 0.2 : false),
        boost: { title: 2 },
        boostDocument: (id) => (String(id).startsWith('place:') ? 3 : String(id).startsWith('stop:') ? 2 : 1),
        combineWith: 'AND',
      },
    })
    search.addAll(docs)
    return search
  }, [places, stops, translations])

  const hits = useMemo(() => {
    if (!query.trim()) return []
    return index.search(query, { filter: (r) => part === 0 || r.part === part }) as unknown as SearchHit[]
  }, [index, query, part])

  const pick = (hit: SearchHit) => {
    setOpen(false)
    onPick(hit)
  }

  // Arrow keys move between the box and the results; Escape clears the box.
  const onKey = (e: KeyboardEvent) => {
    const buttons = [...(list.current?.querySelectorAll('button') ?? [])]
    const at = buttons.indexOf(document.activeElement as HTMLButtonElement)
    if (e.key === 'ArrowDown' && buttons.length) {
      e.preventDefault()
      buttons[Math.min(at + 1, buttons.length - 1)].focus()
    } else if (e.key === 'ArrowUp' && at >= 0) {
      e.preventDefault()
      if (at === 0) input.current?.focus()
      else buttons[at - 1].focus()
    } else if (e.key === 'Escape') {
      setQuery('')
      input.current?.focus()
    } else if (e.key === 'Enter' && e.target === input.current && hits[0]) {
      pick(hits[0])
    }
  }

  return (
    <section className="search" role="search" onKeyDown={onKey}>
      <div className="search-row">
        <label htmlFor={`${id}-q`} className="visually-hidden">
          Search places and the Spanish
        </label>
        <input
          ref={input}
          id={`${id}-q`}
          type="search"
          placeholder="Search places, stops, Spanish…"
          autoComplete="off"
          spellCheck={false}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
        />
        <select aria-label="Part" value={part} onChange={(e) => setPart(Number(e.target.value))}>
          <option value={0}>All Parts</option>
          {[1, 2, 3, 4].map((p) => (
            <option key={p} value={p}>
              Part {PART_NUMERALS[p]}
            </option>
          ))}
        </select>
      </div>
      {open && query.trim() && (
        <>
          <p className="meta" role="status">
            {hits.length === 0
              ? 'Nothing found in what you have read so far.'
              : hits.length > MAX_SHOWN
                ? `${hits.length} found; the first ${MAX_SHOWN} are shown.`
                : `${hits.length} found.`}
          </p>
          <ul ref={list} className="search-results">
            {hits.slice(0, MAX_SHOWN).map((h) => (
              <li key={h.id} data-first-seen={h.first_seen}>
                <button type="button" onClick={() => pick(h)}>
                  <span className={h.kind === 'translation' ? 'es' : undefined} lang={h.kind === 'translation' ? 'es' : undefined}>
                    {h.title}
                  </span>
                  {h.en && <span className="en"> {h.en}</span>}
                  <span className="meta"> {h.kind === 'stop' ? `Stop: ${h.detail}` : h.detail}</span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
