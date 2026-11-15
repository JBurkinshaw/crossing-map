import { useCallback, useEffect, useState } from 'react'

// The introduction (docs/design.md, section 9): what the site is, shown by itself on the first visit only. The
// choice is kept in localStorage, and the panel's "Introduction" link or the About page brings it back. On a first
// visit the reading-progress question waits until it is closed (ReadingProgress, `hold`). The dialog itself is
// Introduction.tsx.

const KEY = 'crossing-map.introduction-seen'
const SHOW = 'crossing-map:show-introduction'

function seen(): boolean {
  try {
    return localStorage.getItem(KEY) === 'yes'
  } catch {
    return false // storage blocked: show it, and it shows again next visit
  }
}

// Opens the introduction from anywhere (the panel's links, the About page).
export function showIntroduction() {
  window.dispatchEvent(new Event(SHOW))
}

// Whether the introduction is open, and a way to close it, which remembers that it has been seen.
export function useIntroduction(): [boolean, () => void] {
  const [open, setOpen] = useState(() => !seen())
  useEffect(() => {
    const show = () => setOpen(true)
    window.addEventListener(SHOW, show)
    return () => window.removeEventListener(SHOW, show)
  }, [])
  const close = useCallback(() => {
    try {
      localStorage.setItem(KEY, 'yes')
    } catch {
      // Storage blocked: closed for this visit only.
    }
    setOpen(false)
  }, [])
  return [open, close]
}
