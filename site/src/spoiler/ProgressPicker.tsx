import { useId, useState } from 'react'
import { episodeAtPage, episodeAtPercent, hasPages } from './position'
import { PART_NUMERALS, progressLabel, reachedEpisode, type Episode, type Progress } from './progress'

// "Where are you up to?": the reading-progress dialog's second step (decision 0034). The episodes' opening words,
// which every edition prints in capitals, are in a native select grouped by Part: one control to tab to, the
// arrow keys and type-ahead work, and phones show their own full-screen picker. Two shortcuts pick the episode
// for readers who know a percentage (an ebook) or a page of the Vintage paperback.

type Props = {
  titleId: string
  progress: Progress
  isSet: boolean
  episodes: Episode[]
  // The episode list could not be loaded: only "I haven't started" can be chosen.
  episodesFailed: boolean
  onSet: (progress: Progress) => void
  // Back to the introduction, when the dialog opened there. Opened from the badge instead, the step offers
  // "Show everything" and "Close".
  onBack?: () => void
  onClose: () => void
}

export function ProgressPicker({ titleId, progress, isSet, episodes, episodesFailed, onSet, onBack, onClose }: Props) {
  const id = useId()
  // Until the reader picks, the picker follows the stored setting (the episode list may still be loading).
  const [chosen, setChosen] = useState<Progress | null>(null)
  const [percent, setPercent] = useState('')
  const [page, setPage] = useState('')
  const [confirming, setConfirming] = useState(false)
  const stored = progress === 'all' ? (episodes.at(-1)?.episode ?? 'none') : progress
  const value = chosen ?? stored
  // A summary tells what happens in its episode, so one shows only for episodes the reader has already said
  // they have read.
  const summary = isSet && value !== 'none' && value <= reachedEpisode(progress) ? episodes.find((e) => e.episode === value)?.summary : undefined
  const parts = [...new Set(episodes.map((e) => e.part))]
  const percentBad = percent !== '' && episodeAtPercent(Number(percent), episodes) === null
  const pageBad = page !== '' && episodeAtPage(Number(page), episodes) === null

  return (
    <>
      <h2 id={titleId}>Where are you up to?</h2>
      <p>Pick the episode you are reading. Each one opens with a few words in capitals.</p>
      {episodesFailed && (
        <p role="alert">The list of episodes could not be loaded, so only these choices work for now. Try reloading the page.</p>
      )}
      <label htmlFor={`${id}-episode`} className="meta">
        Episode
      </label>
      {/* Focus starts on the picker (ReadingProgress.tsx). */}
      <select
        id={`${id}-episode`}
        className="progress-episode"
        data-autofocus
        value={value}
        onChange={(e) => {
          setChosen(e.target.value)
          setPercent('')
          setPage('')
        }}
      >
        <option value="none">I haven’t started</option>
        {parts.map((part) => (
          <optgroup key={part} label={`Part ${PART_NUMERALS[part]}`}>
            {episodes
              .filter((e) => e.part === part)
              .map((e) => (
                <option key={e.episode} value={e.episode}>
                  {Number(e.episode.split('-')[1])}. {e.opening}
                </option>
              ))}
          </optgroup>
        ))}
      </select>
      <div className="progress-choice" aria-live="polite">
        {/* The episode in full, as the badge will name it ("I haven't started" says enough). */}
        {value !== 'none' && <strong>{progressLabel(value, episodes)}</strong>}
        {summary && <p>{summary}</p>}
      </div>

      <div className="progress-shortcuts">
        <label>
          or enter how far through the book you are, as a percentage{' '}
          <span className="progress-number">
            <input
              type="number"
              inputMode="decimal"
              min={0}
              max={100}
              step="any"
              value={percent}
              aria-invalid={percentBad}
              onChange={(e) => {
                setPercent(e.target.value)
                setPage('')
                const found = e.target.value === '' ? null : episodeAtPercent(Number(e.target.value), episodes)
                if (found) setChosen(found)
              }}
            />{' '}
            %
          </span>
        </label>
        {percentBad && <p className="meta">A number from 0 to 100.</p>}
        {hasPages(episodes) && (
          <>
            <label>
              or a page (Vintage paperback){' '}
              <span className="progress-number">
                <input
                  type="number"
                  inputMode="numeric"
                  min={1}
                  step={1}
                  value={page}
                  aria-invalid={pageBad}
                  onChange={(e) => {
                    setPage(e.target.value)
                    setPercent('')
                    const found = e.target.value === '' ? null : episodeAtPage(Number(e.target.value), episodes)
                    if (found) setChosen(found)
                  }}
                />
              </span>
            </label>
            {pageBad && <p className="meta">A page number, such as 120.</p>}
          </>
        )}
      </div>

      {confirming ? (
        <div className="progress-confirm">
          <p>Show everything? Places and routes from the whole book will show, the ending included.</p>
          <div className="progress-actions">
            {/* oxlint-disable-next-line jsx-a11y/no-autofocus */}
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
          <button type="button" className="primary" onClick={() => onSet(chosen ?? progress)}>
            Show the map up to here
          </button>
          {onBack ? (
            <button type="button" onClick={onBack}>
              Back
            </button>
          ) : (
            <>
              <button type="button" onClick={() => setConfirming(true)}>
                Show everything
              </button>
              <button type="button" onClick={onClose}>
                Close
              </button>
            </>
          )}
        </div>
      )}
    </>
  )
}
