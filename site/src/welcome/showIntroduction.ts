import { useEffect } from 'react'

// The introduction (docs/design.md, section 9) is the first step of the reading-progress dialog
// (spoiler/ReadingProgress.tsx): it opens by itself until the reader answers its question. The panel's
// "Introduction" link and the About page bring it back with showIntroduction, from outside the panel.

const SHOW = 'crossing-map:show-introduction'

// Opens the introduction from anywhere (the panel's links, the About page).
export function showIntroduction() {
  window.dispatchEvent(new Event(SHOW))
}

// Calls `open` whenever showIntroduction is called. `open` should keep one identity (useCallback).
export function useShowIntroduction(open: () => void) {
  useEffect(() => {
    window.addEventListener(SHOW, open)
    return () => window.removeEventListener(SHOW, open)
  }, [open])
}
