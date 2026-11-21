import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from 'react'

// The reader's settings in localStorage. Private browsing and some privacy settings refuse storage: reads then
// find nothing, and a setting lasts for this visit only.

export function readStored(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function store(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Refused: see above.
  }
}

// A stored choice, if it is still one of `choices`, else `fallback`. A value a later release renamed or dropped
// falls back, so a setting from an old visit cannot reach the map.
export function readChoice<T extends string>(key: string, choices: readonly T[], fallback: T): T {
  const value = readStored(key)
  return choices.includes(value as T) ? (value as T) : fallback
}

// useState for a setting the reader expects to find again on the next visit. `read` gives the starting value. `write`
// saves it once the reader has chosen, never before, so a reader who never chose keeps getting the current default.
// Pass module-level functions: `write` is an effect dependency.
export function useStoredState<T>(read: () => T, write: (value: T) => void): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState(read)
  const [chosen, setChosen] = useState(false)
  useEffect(() => {
    if (chosen) write(value)
  }, [chosen, value, write])
  const set = useCallback((next: SetStateAction<T>) => {
    setChosen(true)
    setValue(next)
  }, [])
  return [value, set]
}
