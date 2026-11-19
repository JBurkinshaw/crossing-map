import { useId } from 'react'

// The introduction: what the site is, then the one question that sets spoiler mode (decision 0034). It is the
// first step of the reading-progress dialog (spoiler/ReadingProgress.tsx), which owns the <dialog>.

type Props = {
  titleId: string
  // "Yes": the reader has finished the book; nothing is hidden.
  onFinished: () => void
  // "Not yet": on to the step that asks where they are.
  onNotYet: () => void
  // The reader has set their progress before: they may close it without answering again.
  onClose?: () => void
  // "More about this map" opens the About page, so the dialog closes.
  onMore: () => void
}

export function Introduction({ titleId, onFinished, onNotYet, onClose, onMore }: Props) {
  const question = useId()
  return (
    <>
      <h2 id={titleId}>
        A reading map of <cite>The Crossing</cite>
      </h2>
      <p>
        Cormac McCarthy’s novel moves through real country on both sides of the border, from the New Mexico bootheel
        into Sonora and Chihuahua, but it comes with no map. This site draws one: the journeys, stop by stop and
        episode by episode, on real geographic data.
      </p>
      <p>
        Much of the dialogue is in Spanish, and every line has the site’s own English translation. Type any Spanish
        word from the page into the search box to find it.
      </p>
      <p id={question} className="progress-question">
        Have you finished <cite>The Crossing</cite>?
      </p>
      <div className="progress-answers" role="group" aria-labelledby={question}>
        <button type="button" onClick={onFinished}>
          Yes – show me everything
        </button>
        {/* Focus starts here (ReadingProgress.tsx), so a reader who presses Enter straight away keeps spoilers
            hidden. */}
        <button type="button" data-autofocus onClick={onNotYet}>
          Not yet – hide what’s ahead
        </button>
      </div>
      <div className="progress-actions">
        <a className="introduction-more" href="#/about" onClick={onMore}>
          More about this map
        </a>
        {onClose && (
          <button type="button" onClick={onClose}>
            Close
          </button>
        )}
      </div>
    </>
  )
}
