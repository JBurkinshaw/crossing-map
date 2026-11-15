import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

// The introduction dialog: what the site is (showIntroduction.ts opens and remembers it).
export function Introduction({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  const id = useId()
  // Whatever had focus when it opened (the link), read at first render: the Start button's autoFocus takes focus
  // before any effect runs. Focus returns there on close, as a modal dialog should.
  const [opener] = useState(() => document.activeElement)
  useEffect(() => {
    const dialog = ref.current
    if (dialog && !dialog.open) dialog.showModal()
    // After the dialog has left the page: removing it would otherwise drop focus on the body.
    return () => {
      const back = opener as HTMLElement | null
      requestAnimationFrame(() => back?.focus?.())
    }
  }, [opener])
  return createPortal(
    <dialog ref={ref} className="progress-dialog introduction" aria-labelledby={`${id}-title`} onCancel={onClose}>
      <h2 id={`${id}-title`}>
        A reading map of <cite>The Crossing</cite>
      </h2>
      <p>
        Cormac McCarthy’s novel moves through real country on both sides of the border, from the New Mexico bootheel
        into Sonora and Chihuahua, but it comes with no map. This site draws one: the journeys, stop by stop and
        episode by episode, on real geographic data.
      </p>
      <p>
        Every place says how sure it is. Places the book names come from gazetteers; places it only describes are
        worked out from its clues and drawn as areas, with the reasoning written down. Where the book leaves us
        guessing, the map says so, and readers can suggest a correction.
      </p>
      <p>The map shows only what you have read so far. Next, tell it how far you are; you can change that at any time.</p>
      <div className="progress-actions">
        <button type="button" className="primary" autoFocus onClick={onClose}>
          Start
        </button>
        <a
          className="introduction-more"
          href="#/about"
          onClick={() => {
            onClose()
          }}
        >
          More about this map
        </a>
      </div>
    </dialog>,
    document.body,
  )
}
