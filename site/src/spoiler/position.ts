import type { Episode, Progress } from './progress'

// Shortcuts to an episode for readers who know where they are in other terms: an ebook's percentage, or a page of
// the Vintage paperback. Each gives the episode the reader is in, which the progress dialog then offers to set.

// The episode that holds the point `percent` of the way through the book, weighted by each episode's length in
// words. 0 % is before the first word: not started. An ebook's percentage also counts its front and back matter,
// so near an episode's edge the answer can be one episode out.
export function episodeAtPercent(percent: number, episodes: Episode[]): Progress | null {
  if (!Number.isFinite(percent) || percent < 0 || percent > 100 || episodes.length === 0) return null
  if (percent === 0) return 'none'
  const total = episodes.reduce((sum, e) => sum + e.words, 0)
  const at = (percent / 100) * total
  let end = 0
  for (const e of episodes) {
    end += e.words
    if (at <= end) return e.episode
  }
  return episodes[episodes.length - 1].episode
}

// The first page of a range such as "5–24" (any dash), or null.
export function firstPage(pages: string | null): number | null {
  const n = Number(pages?.match(/\d+/)?.[0])
  return Number.isInteger(n) && n > 0 ? n : null
}

// Page lookup works only once every episode has its first page.
export const hasPages = (episodes: Episode[]) => episodes.length > 0 && episodes.every((e) => firstPage(e.pages) !== null)

// The episode a page falls in: the last one starting on or before it. A page before the first episode (the front
// matter) is not started.
export function episodeAtPage(page: number, episodes: Episode[]): Progress | null {
  if (!Number.isInteger(page) || page < 1 || !hasPages(episodes)) return null
  let found: Progress = 'none'
  for (const e of episodes) if (firstPage(e.pages)! <= page) found = e.episode
  return found
}
