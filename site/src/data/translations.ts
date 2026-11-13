import { useEffect, useState } from 'react'

// The Spanish in the novel with this site's own English (data/translations.json; docs/plan.md, sections 3 and 8).
// Only the opening words of each line are published; the Campbell guide is linked by page, never copied.
export type Translation = {
  id: string
  part: number
  episode: string
  page: number | null
  es_incipit: string
  en: string | null
  source: 'site' | 'campbell'
  confidence: 'high' | 'medium' | 'low' | null
  speaker: string | null
  listener: string | null
  // The stop, place or area where it was said; null when the text does not pin it down.
  location_ref: string | null
  first_seen: string
  guide_page: number | null
}

export const CAMPBELL_GUIDE =
  'https://d41cfaf2-ac52-4400-a6e1-aaf2dee170dc.filesusr.com/ugd/842cf5_fac7639eeb8e4ed0812f996b15164ccd.pdf'
export const CAMPBELL_CREDIT = 'Campbell’s guide: Lt. Jim Campbell, cormacmccarthy.com'

export function useTranslations(): Translation[] {
  const [list, setList] = useState<Translation[]>([])
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/translations.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setList, () => setList([]))
  }, [])
  return list
}
