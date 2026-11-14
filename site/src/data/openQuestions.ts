import { useJson, type Loaded } from './json'

// Judgement calls about where something is, in short (data/open-questions.json; the long form is
// docs/open-questions.md and review/stage-7/README.md). Each is shown from its own first_seen, which is the
// latest episode its text refers to, on the cards of its features and on the Open questions page.
export type OpenQuestion = {
  id: string
  title: string
  first_seen: string
  features: string[]
  shown: string
  other: string
  why: string
}

export const useOpenQuestions = (): Loaded<OpenQuestion[]> => useJson<OpenQuestion[]>('open-questions.json')
