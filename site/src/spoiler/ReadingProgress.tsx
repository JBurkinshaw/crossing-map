import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useRoute } from '../route'
import { Introduction } from '../welcome/Introduction'
import type { ProgressDialogState, Step } from './progressDialog'
import { ProgressPicker } from './ProgressPicker'
import { badgeLabel, type Episode, type Progress } from './progress'

// The reading-progress badge and its dialog (docs/design.md, section 9; decision 0034). The dialog has two
// steps: the introduction, which asks whether the reader has finished the book, and "Where are you up to?".
// It opens by itself at the first step until the reader answers; the badge opens the second step, and the panel's
// Introduction link and the About page the first.
//
// The badge sits in the panel, which is a bottom drawer on phones and a side panel on desktop, so it remounts when
// the window crosses the phone breakpoint. The dialog's state is held by useReadingProgress (progressDialog.ts),
// called in App above the panel, and App renders the dialog into the body: a resize mid-dialog keeps its step and
// the reader's pick. Being outside the panel also matters because a page opened over the map makes the panel inert, and a modal
// dialog inside an inert subtree cannot be used.

type Props = {
  progress: Progress
  isSet: boolean
  episodes: Episode[]
}

// Opens the dialog's second step, "Where are you up to?".
export function ProgressBadge({ progress, isSet, episodes, onOpen }: Props & { onOpen: () => void }) {
  return (
    <button type="button" className="progress-badge" aria-haspopup="dialog" onClick={onOpen}>
      {!isSet && <span className="meta">Reading progress</span>}
      <span>{badgeLabel(progress, isSet, episodes)}</span>
    </button>
  )
}

type ReadingProgressDialogProps = Props & {
  dialog: ProgressDialogState
  // The episode list could not be loaded: the picker has nothing to list.
  episodesFailed: boolean
  onSet: (progress: Progress) => void
}

export function ReadingProgressDialog({ dialog, onSet, ...props }: ReadingProgressDialogProps) {
  const route = useRoute()
  const { start, close } = dialog
  if (!start) return null
  return createPortal(
    <ProgressDialog
      key={start}
      start={start}
      {...props}
      onSet={(p) => {
        onSet(p)
        close()
      }}
      onClose={() => close()}
      // "More about this map" opens the About page, which focuses its heading; already on it, nothing navigates,
      // so focus goes back to what opened the dialog.
      onMore={() => close(route === '/about')}
    />,
    document.body,
  )
}

type DialogProps = Props & {
  start: Step
  episodesFailed: boolean
  onSet: (progress: Progress) => void
  onClose: () => void
  onMore: () => void
}

function ProgressDialog({ start, progress, isSet, episodes, episodesFailed, onSet, onClose, onMore }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const [step, setStep] = useState<Step>(start)
  useEffect(() => {
    const dialog = ref.current
    if (dialog && !dialog.open) dialog.showModal()
  }, [])
  // Each step marks where focus starts with data-autofocus. React's autoFocus cannot: it focuses on mount, while
  // the dialog is still closed, and showModal then moves focus to the first button. On a short phone the focused
  // control can sit below the fold: the dialog stays at its top, so it opens on its title, not part way down.
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>('[data-autofocus]')?.focus({ preventScroll: true })
    ref.current?.scrollTo(0, 0)
  }, [step])
  return (
    <dialog ref={ref} className={`progress-dialog${step === 'ask' ? ' introduction' : ''}`} aria-labelledby={titleId} onCancel={onClose}>
      {step === 'ask' ? (
        <Introduction
          titleId={titleId}
          onFinished={() => onSet('all')}
          onNotYet={() => setStep('where')}
          onClose={isSet ? onClose : undefined}
          onMore={onMore}
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
