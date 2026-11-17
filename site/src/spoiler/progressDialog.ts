import { useCallback, useEffect, useRef, useState } from 'react'
import { useShowIntroduction } from '../welcome/showIntroduction'

// The reading-progress dialog's state (spoiler/ReadingProgress.tsx): which step it opened at, if open, and where
// focus goes when it closes. App holds it, above the panel, as the panel's badge remounts when the layout changes.

export type Step = 'ask' | 'where'

export type ProgressDialogState = {
  start: Step | null
  open: (step: Step) => void
  // `refocus` false: the dialog closes by opening a page, which takes focus itself (Pages.tsx).
  close: (refocus?: boolean) => void
}

export function useReadingProgress(isSet: boolean): ProgressDialogState {
  const [start, setStart] = useState<Step | null>(isSet ? null : 'ask')
  // What had focus when the dialog opened (the badge, the Introduction link), for focus to go back to on close,
  // as a modal dialog should. On the first visit nothing had, and focus goes to the badge.
  const opener = useRef<Element | null>(null)
  const open = useCallback((step: Step) => {
    opener.current = document.activeElement
    setStart(step)
  }, [])
  useShowIntroduction(useCallback(() => open('ask'), [open]))
  const returnFocus = useRef(false)
  const close = useCallback((refocus = true) => {
    setStart(null)
    returnFocus.current = refocus
  }, [])
  // Once the dialog has gone: while it is open, everything behind it is inert.
  useEffect(() => {
    if (start || !returnFocus.current) return
    returnFocus.current = false
    const back = opener.current
    const target = back instanceof HTMLElement && back.isConnected && back !== document.body ? back : document.querySelector<HTMLElement>('.progress-badge')
    target?.focus()
  }, [start])
  return { start, open, close }
}
