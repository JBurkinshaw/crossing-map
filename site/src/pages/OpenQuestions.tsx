import type { OpenQuestion } from '../data/openQuestions'
import { OpenQuestionNote } from '../panel/OpenQuestions'
import { feedbackUrl } from './format'

// Every judgement call about where something is, as far as the reader has read.
export function OpenQuestions({ questions }: { questions: OpenQuestion[] }) {
  const general = feedbackUrl({ kind: 'general' })
  return (
    <>
      <p className="lede">
        Where the book, the gazetteers and other readers disagree, the map shows one reading and says so.
        These are the places still in question. Each card on the map carries its own
        {general ? ', and a link to suggest a correction.' : '.'}
      </p>
      <p>
        Other readings used here: James Luther Bell’s{' '}
        <a href="https://ttu-ir.tdl.org/bitstreams/ec52ab01-a89b-423d-aee5-92df180a15c4/download">annotated dissertation</a> (Texas Tech University, 2000) and
        Joe Hazelton’s reader’s map of the novel on Gaia GPS. Questions about places you have not reached yet stay hidden.
      </p>
      {questions.length === 0 ? (
        <p className="meta">No open questions up to this point in the book.</p>
      ) : (
        questions.map((q) => <OpenQuestionNote key={q.id} q={q} />)
      )}
      <p>
        Think a place is wrong? <a href="#/about/how-its-built">How it’s built</a> says how places are worked out
        and how a clue is tested, so a new reading can be checked the same way.
        {general && (
          <>
            {' '}
            <a href={general} target="_blank" rel="noreferrer">
              Suggest a correction or a new reading
            </a>
            .
          </>
        )}
      </p>
    </>
  )
}
