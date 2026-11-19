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
  // Optional context: more on the call, where the other reading would put it, and how the call was made.
  detail?: string
  other_at?: OtherReading
  evidence?: { label: string; path: string }[]
}

// The other reading as a ring on the map: a centre (longitude, latitude) and a radius.
export type OtherReading = { coordinates: [number, number]; radius_km: number; label: string }

// The panel asks the map to show or clear the other reading's ring through this window event, so the card need
// not be wired to the map. `feature` is the stop or place whose card asked, so the map frames that feature, not
// wherever the camera happens to be. `back` returns the camera to the feature when the reader hides the ring;
// leaving the card clears the ring without moving the camera.
export type OtherReadingRequest = { ring: OtherReading | null; feature: string; back?: boolean }
export const OTHER_READING_EVENT = 'crossing:other-reading'
export const requestOtherReading = (request: OtherReadingRequest) =>
  window.dispatchEvent(new CustomEvent<OtherReadingRequest>(OTHER_READING_EVENT, { detail: request }))

export const useOpenQuestions = (): Loaded<OpenQuestion[]> => useJson<OpenQuestion[]>('open-questions.json')
