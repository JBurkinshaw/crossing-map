import { useJson, type Loaded } from './json'

// The Spanish in the novel with this site's own English (data/translations.json; docs/design.md, sections 3 and 8).
// Only the opening words of each line are published; the Campbell guide is linked by page, never copied.
export type Translation = {
  id: string
  part: number
  episode: string
  page: number | null
  es_incipit: string
  // For search only: the line's other words, folded and in alphabetical order, so they cannot be read as the line
  // (decision 0047). Null when the incipit is the whole line.
  es_words: string[] | null
  en: string | null
  source: 'site' | 'campbell'
  confidence: 'high' | 'medium' | 'low' | null
  speaker: string | null
  listener: string | null
  // The stop, place or area where it was said, or the route segment for talk on the road; null when the text
  // does not pin it down. 'road' is this site's inference: the line has no place, and its episode travels that
  // segment (pipeline/seeds/road-refs.csv).
  location_ref: string | null
  location_kind: 'stop' | 'place' | 'area' | 'road' | null
  first_seen: string
  guide_page: number | null
  // A very common line ("Sí", "Gracias", "Buenas noches"): the panel leaves it out of a place's lines, and search
  // still finds it (crossing.translations sets it).
  common: boolean
}

export { CAMPBELL_CREDIT, CAMPBELL_GUIDE } from './campbell'

// Fetched once `enabled` is first true: App holds it back until the story layers have arrived, so the map's own
// data is not kept waiting behind it.
export const useTranslations = (enabled: boolean): Loaded<Translation[]> => useJson<Translation[]>('translations.json', enabled)
