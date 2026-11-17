import type { StoryProps } from '../data/story'

// How sure the map is about a place, in the reader's words: the stop section, the place card, the About page and
// How it's built all name the data's certainty values this way (design section 6 defines the values). The schema
// requires one of these four on every story feature.
export const CERTAINTY_LABEL: Record<StoryProps['certainty'], string> = {
  located: 'Named and found',
  approximate: 'Roughly here',
  inferred: 'Worked out from clues',
  reported: 'Someone in the book says so',
}
