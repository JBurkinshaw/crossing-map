import { useCallback, useState } from 'react'
import { useJson, type Loaded } from '../data/json'
import { readStored, store } from '../storage'

// Reading progress: how far the reader has read, by episode (data/episodes.json). Spoiler mode hides every
// feature first seen after it (docs/design.md, sections 6 and 9).

// `words` is the episode's length; `pages` its page range in the Vintage paperback, such as "5–24" (null until
// it is filled in).
export type Episode = { episode: string; part: number; opening: string; words: number; pages: string | null; summary: string }

// 'none' (not started), 'all' (finished: nothing hidden) or the episode being read, such as '2-05', which shows in
// full (decision 0034).
export type Progress = string

const KEY = 'crossing-map.progress'
const VALID = /^(none|all|[1-4]-(0[1-9]|1[0-4]))$/

function storedProgress(): Progress | null {
  const value = readStored(KEY)
  return value && VALID.test(value) ? value : null
}

// Until the reader answers, spoiler mode is on and shows nothing past the start of the book.
export function useProgress(): { progress: Progress; isSet: boolean; setProgress: (p: Progress) => void } {
  const [stored, setStored] = useState<Progress | null>(storedProgress)
  const setProgress = useCallback((p: Progress) => {
    store(KEY, p)
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

// The episode after the one being read: what "Read on" sets progress to. Null when not started, finished, or
// reading the last episode (which already shows everything).
export function nextEpisode(progress: Progress, episodes: Episode[]): string | null {
  const i = episodes.findIndex((e) => e.episode === progress)
  return i < 0 ? null : (episodes[i + 1]?.episode ?? null)
}

export const PART_NUMERALS = ['', 'I', 'II', 'III', 'IV']

// The badge and picker label for a setting, such as "Part II, episode 5: ‘He was all…’".
export function progressLabel(progress: Progress, episodes: Episode[]): string {
  if (progress === 'none') return 'Not started'
  if (progress === 'all') return 'Finished: showing everything'
  const e = episodes.find((x) => x.episode === progress)
  if (!e) return `Episode ${progress}`
  return `Part ${PART_NUMERALS[e.part]}, episode ${Number(e.episode.split('-')[1])}: ${quotedOpening(e)}`
}

// An episode's opening words as the site shows them, quoted and trailing off into the episode: ‘They crossed…’. The
// book has no episode titles, so these words stand in for one (decision 0052).
export function quotedOpening(e: Episode): string {
  return `‘${e.opening}…’`
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
