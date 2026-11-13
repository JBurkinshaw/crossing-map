import type { OpenQuestion } from '../data/openQuestions'
import { OpenQuestionNote } from '../panel/OpenQuestions'
import { REPO_URL } from './format'

// Every judgement call about where something is, as far as the reader has read.
export function OpenQuestions({ questions }: { questions: OpenQuestion[] }) {
  return (
    <>
      <p className="lede">
        Where the book, the gazetteers and other readers' maps disagree, the map shows one reading and says so.
        These are the places still in question. Each card on the map carries its own, and a link to suggest a
        correction.
      </p>
      <p>
        Other readers' maps used here: James Luther Bell's annotated dissertation (Texas Tech University, 2000) and
        Joe Hazelton's map of the novel on Gaia GPS. Questions about places you have not reached yet stay hidden.
      </p>
      {questions.length === 0 ? (
        <p className="meta">No open questions up to this point in the book.</p>
      ) : (
        questions.map((q) => <OpenQuestionNote key={q.id} q={q} />)
      )}
      <p>
        <a href={`${REPO_URL}/issues/new`} target="_blank" rel="noreferrer">
          Suggest a correction or a new reading
        </a>{' '}
        on GitHub.
      </p>
    </>
  )
}
