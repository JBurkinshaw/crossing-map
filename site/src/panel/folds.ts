import { useCallback, useState } from 'react'

// How a stop's synopsis shows (decision 0051). A stop in an episode the reader has finished shows it in full. A stop
// in the episode being read folds it under "What happens here", because the synopsis can tell what happens later in
// that episode. `reached` is the episode being read, or '9-99' once the book is finished (spoiler/progress.ts).
export function synopsisFolded(stopEpisode: string, reached: string): boolean {
  return stopEpisode >= reached
}

export function readFold(key: string): boolean {
  try {
    return localStorage.getItem(key) === 'open'
  } catch {
    // Storage blocked or absent: the fold starts closed.
    return false
  }
}

// A fold that opens or closes as the reader last left it, on every stop and on later visits. It starts closed.
export function useRememberedFold(key: string): [boolean, (open: boolean) => void] {
  const [open, setState] = useState(() => readFold(key))
  const setOpen = useCallback(
    (next: boolean) => {
      try {
        localStorage.setItem(key, next ? 'open' : 'closed')
      } catch {
        // Storage blocked: the choice lasts for this visit only.
      }
      setState(next)
    },
    [key],
  )
  return [open, setOpen]
}
