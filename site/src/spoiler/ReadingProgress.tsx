import { useEffect, useId, useRef, useState } from 'react'
import { PART_NUMERALS, progressLabel, spoilersHidden, type Episode, type Progress } from './progress'

// The reading-progress badge and its dialog (docs/plan.md, section 9): on the first visit the dialog opens by
// itself and asks how far the reader has read; afterwards the badge shows the setting and reopens it.

type Props = {
  progress: Progress
  isSet: boolean
  episodes: Episode[]
  onSet: (progress: Progress) => void
}

export function ReadingProgress({ progress, isSet, episodes, onSet }: Props) {
  const [open, setOpen] = useState(!isSet)
  const badge = useRef<HTMLButtonElement>(null)
  const close = () => {
    setOpen(false)
    badge.current?.focus()
  }
  const hidden = spoilersHidden(progress, episodes)
  return (
    <>
      <button ref={badge} type="button" className="progress-badge" aria-haspopup="dialog" onClick={() => setOpen(true)}>
        <span className="meta">{hidden ? 'Spoilers hidden · read up to' : 'Spoilers shown'}</span>
        <span>{isSet ? progressLabel(progress, episodes) : 'Not set: how far have you read?'}</span>
      </button>
      {open && (
        <ProgressDialog
          first={!isSet}
          progress={progress}
          episodes={episodes}
          onSet={(p) => {
            onSet(p)
            close()
          }}
          onClose={close}
        />
      )}
    </>
  )
}

type DialogProps = {
  first: boolean
  progress: Progress
  episodes: Episode[]
  onSet: (progress: Progress) => void
  onClose: () => void
}

function ProgressDialog({ first, progress, episodes, onSet, onClose }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const id = useId()
  useEffect(() => {
    const dialog = ref.current
    if (dialog && !dialog.open) dialog.showModal()
  }, [])

  // One slider step per episode; step 0 is "not started". Until the reader moves it, it follows the
  // stored setting (the episode list may still be loading when the dialog opens).
  const [chosen, setChosen] = useState<number | null>(null)
  const stored = progress === 'none' ? 0 : progress === 'all' ? episodes.length : episodes.findIndex((e) => e.episode === progress) + 1
  const step = chosen ?? stored
  const value: Progress = step === 0 ? 'none' : (episodes[step - 1]?.episode ?? 'none')
  const episode = episodes[step - 1]
  const [confirming, setConfirming] = useState(false)

  // Part labels under the slider, each at its Part's first episode.
  const parts = episodes.flatMap((e, i) => (i === 0 || episodes[i - 1].part !== e.part ? [{ part: e.part, at: i + 1 }] : []))

  return (
    <dialog ref={ref} className="progress-dialog" aria-labelledby={`${id}-title`} onCancel={onClose}>
      <h2 id={`${id}-title`}>How far have you read?</h2>
      {first && (
        <p>
          This map follows the journeys in Cormac McCarthy's <cite>The Crossing</cite>. It shows only what you have read so far,
          so tell it where you are. You can change this at any time from the button at the top of the panel.
        </p>
      )}

      <label htmlFor={`${id}-slider`} className="meta">
        Read up to
      </label>
      <input
        id={`${id}-slider`}
        className="progress-slider"
        type="range"
        min={0}
        max={episodes.length}
        step={1}
        value={step}
        aria-valuetext={progressLabel(value, episodes)}
        onChange={(e) => setChosen(Number(e.target.value))}
      />
      <div className="part-ticks" aria-hidden="true">
        {parts.map(({ part, at }) => (
          <span key={part} style={{ left: `${(at / Math.max(1, episodes.length)) * 100}%` }}>
            Part {PART_NUMERALS[part]}
          </span>
        ))}
      </div>
      <div className="progress-choice" aria-live="polite">
        <strong>{progressLabel(value, episodes)}</strong>
        {episode && <p>{episode.summary}</p>}
      </div>

      {confirming ? (
        <div className="progress-confirm">
          <p>Show everything? Places and routes from the whole book will show, the ending included.</p>
          <div className="progress-actions">
            <button type="button" autoFocus onClick={() => onSet('all')}>
              Show everything
            </button>
            <button type="button" onClick={() => setConfirming(false)}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="progress-actions">
          <button type="button" className="primary" onClick={() => onSet(value)}>
            {step === 0 ? 'Not started' : 'Show the map up to here'}
          </button>
          {step !== 0 && (
            <button type="button" onClick={() => onSet('none')}>
              Not started
            </button>
          )}
          {first ? (
            <button type="button" onClick={() => onSet('all')}>
              I've finished it
            </button>
          ) : (
            <button type="button" onClick={() => setConfirming(true)}>
              Show everything
            </button>
          )}
          {!first && (
            <button type="button" onClick={onClose}>
              Close
            </button>
          )}
        </div>
      )}
    </dialog>
  )
}
