import { useCallback, useState } from 'react'
import { useJson, type Loaded } from '../data/json'

// Reading progress: how far the reader has read, by episode (data/episodes.json). Spoiler mode hides every
// feature first seen after it (docs/design.md, sections 6 and 9).

// `words` is the episode's length; `pages` its page range in the Vintage paperback, such as "5–24" (null until
// it is filled in).
export type Episode = { episode: string; part: number; opening: string; words: number; pages: string | null; summary: string }

// 'none' (not started), 'all' (finished: nothing hidden) or the last episode read, such as '2-05'.
export type Progress = string

const KEY = 'crossing-map.progress'
const VALID = /^(none|all|[1-4]-(0[1-9]|1[0-4]))$/

function readStored(): Progress | null {
  try {
    const value = localStorage.getItem(KEY)
    return value && VALID.test(value) ? value : null
  } catch {
    return null
  }
}

// Until the reader answers, spoiler mode is on and shows nothing past the start of the book.
export function useProgress(): { progress: Progress; isSet: boolean; setProgress: (p: Progress) => void } {
  const [stored, setStored] = useState<Progress | null>(readStored)
  const setProgress = useCallback((p: Progress) => {
    try {
      localStorage.setItem(KEY, p)
    } catch {
      // Private browsing can refuse storage; the setting then lasts for this visit only.
    }
    setStored(p)
  }, [])
  return { progress: stored ?? 'none', isSet: stored !== null, setProgress }
}

// The latest first_seen that may show. Episode ids sort as strings in reading order: the schema pins them to
// ^[1-4]-(0[1-9]|1[0-4])$, so '0-00' is before the book and '9-99' after it.
export function reachedEpisode(progress: Progress): string {
  if (progress === 'none') return '0-00'
  if (progress === 'all') return '9-99'
  return progress
}

// Spoiler mode is on unless the reader has read the last episode.
export function spoilersHidden(progress: Progress, episodes: Episode[]): boolean {
  const last = episodes.at(-1)?.episode
  // Compared as episode ids: 'none' itself sorts after every id, so it goes through reachedEpisode.
  return progress !== 'all' && (!last || reachedEpisode(progress) < last)
}

export const PART_NUMERALS = ['', 'I', 'II', 'III', 'IV']

// The badge and slider label for a setting, such as "Part II, episode 5: He was all day".
export function progressLabel(progress: Progress, episodes: Episode[]): string {
  if (progress === 'none') return 'Not started'
  if (progress === 'all') return 'Finished: showing everything'
  const e = episodes.find((x) => x.episode === progress)
  if (!e) return `Episode ${progress}`
  return `Part ${PART_NUMERALS[e.part]}, episode ${Number(e.episode.split('-')[1])}: ${e.opening}`
}

// The progress badge: what the map is hiding, in the words of the dialog it opens.
export function badgeLabel(progress: Progress, isSet: boolean, episodes: Episode[]): string {
  if (!isSet) return 'Not set'
  if (!spoilersHidden(progress, episodes)) return 'Showing everything'
  if (progress === 'none') return 'Hiding the whole book'
  return `Hiding what’s after ${progressLabel(progress, episodes)}`
}

// "Part I, episode 7", from an episode id such as '1-07'.
export function episodeLabel(episode: string): string {
  const [part, n] = episode.split('-').map(Number)
  return `Part ${PART_NUMERALS[part] ?? part}, episode ${n}`
}

export const useEpisodes = (): Loaded<Episode[]> => useJson<Episode[]>('episodes.json')
