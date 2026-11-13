import { useCallback, useEffect, useState } from 'react'

// Reading progress: how far the reader has read, by episode (data/episodes.json). Spoiler mode hides every
// feature first seen after it (docs/plan.md, sections 6 and 9).

export type Episode = { episode: string; part: number; opening: string; summary: string }

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
  return progress !== 'all' && (!last || progress < last)
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

export function useEpisodes(): Episode[] {
  const [list, setList] = useState<Episode[]>([])
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/episodes.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setList, () => setList([]))
  }, [])
  return list
}
