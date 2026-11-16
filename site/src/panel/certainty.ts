// How sure the map is about a place, in the reader's words: the stop section, the place card, the About page and
// How it's built all name the data's certainty values this way (design section 6 defines the values).
export const CERTAINTY_LABEL: Record<string, string> = {
  located: 'Named and found',
  approximate: 'Roughly here',
  inferred: 'Worked out from clues',
  reported: 'Someone in the book says so',
}

// A value with no reader's phrase (a new one in the data) shows as it is, rather than not at all.
export const certaintyLabel = (certainty: string | null | undefined): string => (certainty ? (CERTAINTY_LABEL[certainty] ?? certainty) : '')
