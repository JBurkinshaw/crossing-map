import { hashParam, setHashParam } from '../route'
import { readStored, store } from '../storage'

// The reader's place in the book: the stop in focus (decision 0053). It is kept in the address as `#stop=<id>`, so a
// bookmark or a shared link opens there, and in localStorage, so the next visit does too.

const KEY = 'crossing-map.place'

// Where the reader was, best first: the link they opened, then their last visit on this device. Either may name a
// stop past their progress: a link from a reader further on, or a place left from before they moved progress
// back. navigation.ts looks each up in the story already filtered to their progress, so such a stop is skipped.
export const savedPlaces = (): string[] => [hashParam('stop'), readStored(KEY)].filter((id): id is string => !!id)

export function savePlace(id: string) {
  store(KEY, id)
  setHashParam('stop', id)
}
