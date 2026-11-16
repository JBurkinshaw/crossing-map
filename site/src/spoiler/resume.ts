import type { Feature, Geometry } from 'geojson'
import type { StoryProps } from '../data/story'
import type { Progress } from './progress'

// Where the map opens for a reader part way through the book: the stop they reached most recently. Among the
// stops at or before their episode, the one with the latest first_seen, and its journey. Where two journeys
// reach that episode together, the one the book tells first-hand wins over a reported one (J6, told by others),
// then the journey that started later, as the story has moved on to it (J2 takes over from J1 in 1-08).
// Within the journey, its last stop at or before the episode. Null when there is nothing to choose: not
// started, finished ('all' opens at the start of the book), or no stop reached yet.
export function resumeStop(stops: Feature<Geometry, StoryProps>[], progress: Progress): { journey: string; id: string } | null {
  if (progress === 'none' || progress === 'all') return null
  const reached = stops.filter((s) => s.properties.journey && s.properties.first_seen <= progress)
  if (reached.length === 0) return null
  const latest = reached.reduce((m, s) => (s.properties.first_seen > m ? s.properties.first_seen : m), '')
  const start = new Map<string, string>()
  for (const s of reached) {
    const j = s.properties.journey!
    if (!start.has(j) || s.properties.first_seen < start.get(j)!) start.set(j, s.properties.first_seen)
  }
  const told = (j: string) => reached.some((s) => s.properties.journey === j && s.properties.certainty !== 'reported')
  const candidates = [...new Set(reached.filter((s) => s.properties.first_seen === latest).map((s) => s.properties.journey!))]
  candidates.sort((a, b) => Number(told(b)) - Number(told(a)) || start.get(b)!.localeCompare(start.get(a)!) || b.localeCompare(a))
  const journey = candidates[0]
  const last = reached
    .filter((s) => s.properties.journey === journey)
    .reduce((m, s) => ((s.properties.sequence ?? 0) > (m.properties.sequence ?? 0) ? s : m))
  return { journey, id: last.properties.id }
}
