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
