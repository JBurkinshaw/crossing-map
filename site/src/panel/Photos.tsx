import { useState } from 'react'
import type { Photo } from '../data/photos'

// A place's photos on its card or its stop (decision 0067): one at a time in a frame of fixed height, so the text
// below never moves, with Back and Next when there is more than one, and the TASL credit under it. The photos have
// already passed the spoiler filter. `firstSeen` is the place's, or undefined for a context place, which always shows.
// A photo whose words name a later place carries its own. The parent keys this by place, so each starts at the first.
export function Photos({ photos, firstSeen }: { photos: Photo[]; firstSeen?: string }) {
  const [index, setIndex] = useState(0)
  if (photos.length === 0) return null
  const at = Math.min(index, photos.length - 1)
  const photo = photos[at]
  // Back and Next go round, so the button pressed keeps the focus at either end.
  const step = (by: number) => setIndex((at + by + photos.length) % photos.length)
  return (
    <figure className="photo" data-first-seen={photo.first_seen ?? firstSeen}>
      <div className="photo-frame">
        <img
          key={photo.file}
          src={`${import.meta.env.BASE_URL}${photo.file}`}
          alt={photo.alt}
          width={photo.width}
          height={photo.height}
          loading="lazy"
          decoding="async"
        />
      </div>
      {photos.length > 1 && (
        <div className="photo-stepper">
          <button type="button" onClick={() => step(-1)}>
            Back<span className="visually-hidden"> to the previous photo</span>
          </button>
          <span className="meta" aria-live="polite">
            {at + 1} of {photos.length}
          </span>
          <button type="button" onClick={() => step(1)}>
            Next<span className="visually-hidden"> photo</span>
          </button>
        </div>
      )}
      <figcaption className="meta photo-credit">
        <PhotoCredit photo={photo} />
      </figcaption>
    </figure>
  )
}

// Title, author, source and licence (TASL), as Creative Commons asks: the source links to the file's page on
// Commons, and the licence to its deed where it has one.
export function PhotoCredit({ photo }: { photo: Photo }) {
  return (
    <>
      “{photo.title}”, {photo.author}. <a href={photo.commons_url}>Wikimedia Commons</a>,{' '}
      {photo.licence_url ? <a href={photo.licence_url}>{photo.licence}</a> : photo.licence}.
    </>
  )
}
