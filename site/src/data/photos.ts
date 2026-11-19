import { useJson, type Loaded } from './json'

// The Wikimedia Commons photos on the place and stop cards (data/photos.json, decision 0067). Each keeps its own
// licence, and is credited in TASL form: title, author, source and licence.
export type Photo = {
  // Relative to the site's root: site/public/photos/.
  file: string
  width: number
  height: number
  title: string
  author: string
  licence: string
  // Null for public domain files, which Commons gives no licence page.
  licence_url: string | null
  date: string | null
  commons_url: string
  via: string
  alt: string
  // Only where the photo's words name a place met later than its own place. Otherwise it shows with its place.
  first_seen?: string
}

// A place's photos (or a stop's, for a stop with no place of its own), and the stops whose cards show them too.
export type PlacePhotos = { place_id: string; stop_ids: string[]; photos: Photo[] }

export const usePhotos = (enabled = true): Loaded<PlacePhotos[]> => useJson<PlacePhotos[]>('photos.json', enabled)
