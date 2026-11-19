import { useEffect, useRef, useState } from 'react'
import { requestOtherReading, type OpenQuestion } from '../data/openQuestions'
import { feedbackUrl, repoUrl } from '../pages/format'

// One judgement call: what the map shows, the other reading, and why. `feature` is set on cards, where the map
// sits beside the panel, so a question with `other_at` can show the other reading there, framed with that feature.
function Readings({ q, feature }: { q: OpenQuestion; feature?: string }) {
  const onMap = feature !== undefined
  const [shown, setShown] = useState(false)
  const shownRef = useRef(false)
  // The ring belongs to this card: leaving the stop clears it, and the move to the next stop sets the camera.
  useEffect(() => {
    if (!feature) return
    return () => {
      if (shownRef.current) requestOtherReading({ ring: null, feature })
    }
  }, [feature])
  const toggle = () => {
    if (!feature || !q.other_at) return
    requestOtherReading(shown ? { ring: null, feature, back: true } : { ring: q.other_at, feature })
    shownRef.current = !shown
    setShown(!shown)
  }
  return (
    <>
      <dl>
        <dt>Shown</dt>
        <dd>{q.shown}</dd>
        <dt>Other reading</dt>
        <dd>{q.other}</dd>
        <dt>Why</dt>
        <dd>{q.why}</dd>
      </dl>
      {onMap && q.other_at && (
        <button type="button" className="show-other" aria-pressed={shown} onClick={toggle}>
          {shown ? 'Hide the other reading' : 'Show the other reading on the map'}
        </button>
      )}
      {(q.detail || (!onMap && q.evidence?.length)) && (
        <details className="question-detail">
          <summary>More about this</summary>
          {q.detail && <p>{q.detail}</p>}
          {/* How the call was made: on the Open questions page only, not on the map's cards. */}
          {!onMap && q.evidence && q.evidence.length > 0 && (
            <p className="evidence">
              {q.evidence.map((e, i) => (
                <span key={e.path}>
                  {i > 0 && ' · '}
                  <a href={repoUrl(e.path)} target="_blank" rel="noreferrer">
                    {e.label}
                  </a>
                </span>
              ))}
            </p>
          )}
        </details>
      )}
    </>
  )
}

// A question set out in full, as the Open questions page has it.
export function OpenQuestionNote({ q }: { q: OpenQuestion }) {
  return (
    <aside className="open-question" data-first-seen={q.first_seen}>
      <h3>{q.title}</h3>
      <Readings q={q} />
    </aside>
  )
}

// The same on a card or a stop, folded to its title: how a place was settled is the map's craft, one step behind
// the story the reader came for (decision 0060).
function FoldedQuestion({ q, feature }: { q: OpenQuestion; feature: string }) {
  return (
    <details className="open-question" data-first-seen={q.first_seen}>
      <summary>Open question: {q.title}</summary>
      <Readings q={q} feature={feature} />
    </details>
  )
}

// The open questions about one feature, already filtered to the reader's progress, and a way to send a
// correction: the feedback form, with the feature named.
export function FeatureQuestions({ id, name, questions }: { id: string; name: string; questions: OpenQuestion[] }) {
  const mine = questions.filter((q) => q.features.includes(id))
  const form = feedbackUrl({ kind: 'correction', feature: id, name })
  return (
    <>
      {mine.map((q) => (
        <FoldedQuestion key={q.id} q={q} feature={id} />
      ))}
      {(mine.length > 0 || form) && (
        <p className="correction">
          {mine.length > 0 && <a href="#/open-questions">All open questions</a>}
          {mine.length > 0 && form && ' · '}
          {form && (
            <a href={form} target="_blank" rel="noreferrer">
              Suggest a correction
            </a>
          )}
        </p>
      )}
    </>
  )
}
