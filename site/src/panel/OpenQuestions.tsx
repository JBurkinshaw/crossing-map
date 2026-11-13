import type { OpenQuestion } from '../data/openQuestions'
import { REPO_URL } from '../pages/format'

// One judgement call: what the map shows, the other reading, and why.
// `label` goes before the title on cards; the Open questions page leaves it out.
export function OpenQuestionNote({ q, label }: { q: OpenQuestion; label?: string }) {
  return (
    <aside className="open-question" data-first-seen={q.first_seen}>
      <h3>{label ? `${label}: ${q.title}` : q.title}</h3>
      <dl>
        <dt>Shown</dt>
        <dd>{q.shown}</dd>
        <dt>Other reading</dt>
        <dd>{q.other}</dd>
        <dt>Why</dt>
        <dd>{q.why}</dd>
      </dl>
    </aside>
  )
}

// The open questions about one feature, already filtered to the reader's progress, and a way to send a
// correction: a GitHub issue form with the feature named.
export function FeatureQuestions({ id, name, questions }: { id: string; name: string; questions: OpenQuestion[] }) {
  const mine = questions.filter((q) => q.features.includes(id))
  const issue = `${REPO_URL}/issues/new?${new URLSearchParams({
    title: `Correction: ${name}`,
    body: `Feature: ${id} (${name})\n\nWhat is wrong, and how do you know? A page of the book, a map or a source helps.\n`,
  })}`
  return (
    <>
      {mine.map((q) => (
        <OpenQuestionNote key={q.id} q={q} label="Open question" />
      ))}
      <p className="correction">
        {mine.length > 0 && (
          <>
            <a href="#/open-questions">All open questions</a> ·{' '}
          </>
        )}
        <a href={issue} target="_blank" rel="noreferrer">
          Suggest a correction
        </a>
      </p>
    </>
  )
}
