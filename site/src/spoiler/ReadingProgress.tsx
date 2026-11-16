import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Introduction } from '../welcome/Introduction'
import { useShowIntroduction } from '../welcome/showIntroduction'
import { ProgressPicker } from './ProgressPicker'
import { badgeLabel, type Episode, type Progress } from './progress'

// The reading-progress badge and its dialog (docs/design.md, section 9; decision 0034). The dialog has two
// steps: the introduction, which asks whether the reader has finished the book, and "Where are you up to?".
// It opens by itself at the first step until the reader answers; the badge opens the second step, and the panel's
// Introduction link and the About page the first. The dialog is rendered into the body, outside the panel: a
// page opened over the map makes the panel inert, and a modal dialog inside an inert subtree cannot be used.

type Step = 'ask' | 'where'

type Props = {
  progress: Progress
  isSet: boolean
  episodes: Episode[]
  // The episode list could not be loaded: the picker has nothing to list.
  episodesFailed: boolean
  onSet: (progress: Progress) => void
}

export function ReadingProgress({ progress, isSet, episodes, episodesFailed, onSet }: Props) {
  const [start, setStart] = useState<Step | null>(isSet ? null : 'ask')
  const badge = useRef<HTMLButtonElement>(null)
  // What had focus when the dialog opened (the badge, the Introduction link), for focus to go back to on close,
  // as a modal dialog should. On the first visit nothing had, and focus goes to the badge.
  const opener = useRef<Element | null>(null)
  const open = useCallback((step: Step) => {
    opener.current = document.activeElement
    setStart(step)
  }, [])
  useShowIntroduction(useCallback(() => open('ask'), [open]))
  const returnFocus = useRef(false)
  const close = () => {
    setStart(null)
    returnFocus.current = true
  }
  // Once the dialog has gone: while it is open, everything behind it is inert.
  useEffect(() => {
    if (start || !returnFocus.current) return
    returnFocus.current = false
    const back = opener.current
    const target = back instanceof HTMLElement && back.isConnected && back !== document.body ? back : badge.current
    target?.focus()
  }, [start])
  return (
    <>
      <button ref={badge} type="button" className="progress-badge" aria-haspopup="dialog" onClick={() => open('where')}>
        {!isSet && <span className="meta">Reading progress</span>}
        <span>{badgeLabel(progress, isSet, episodes)}</span>
      </button>
      {start &&
        createPortal(
          <ProgressDialog
            key={start}
            start={start}
            progress={progress}
            isSet={isSet}
            episodes={episodes}
            episodesFailed={episodesFailed}
            onSet={(p) => {
              onSet(p)
              close()
            }}
            onClose={close}
          />,
          document.body,
        )}
    </>
  )
}

type DialogProps = Omit<Props, 'onSet'> & { start: Step; onSet: (progress: Progress) => void; onClose: () => void }

function ProgressDialog({ start, progress, isSet, episodes, episodesFailed, onSet, onClose }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const [step, setStep] = useState<Step>(start)
  useEffect(() => {
    const dialog = ref.current
    if (dialog && !dialog.open) dialog.showModal()
  }, [])
  // Each step marks where focus starts with data-autofocus. React's autoFocus cannot: it focuses on mount, while
  // the dialog is still closed, and showModal then moves focus to the first button.
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>('[data-autofocus]')?.focus()
  }, [step])
  return (
    <dialog ref={ref} className={`progress-dialog ${step === 'ask' ? 'introduction' : 'progress-where'}`} aria-labelledby={titleId} onCancel={onClose}>
      {step === 'ask' ? (
        <Introduction
          titleId={titleId}
          onFinished={() => onSet('all')}
          onNotYet={() => setStep('where')}
          onClose={isSet ? onClose : undefined}
          onMore={onClose}
        />
      ) : (
        <ProgressPicker
          titleId={titleId}
          progress={progress}
          isSet={isSet}
          episodes={episodes}
          episodesFailed={episodesFailed}
          onSet={onSet}
          onBack={start === 'ask' ? () => setStep('ask') : undefined}
          onClose={onClose}
        />
      )}
    </dialog>
  )
}
