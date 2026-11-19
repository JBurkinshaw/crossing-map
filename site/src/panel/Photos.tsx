import { useState, type KeyboardEvent } from 'react'
import type { Photo } from '../data/photos'

// A place's photos on its card or its stop (decision 0067): one at a time in a frame of fixed height, so the text
// below never moves, and the TASL credit under it. With more than one, arrows on the frame's edges and a count in its
// corner step through them, shaped unlike the stop stepper's Back and Next so the two never read as one. The photos have
// already passed the spoiler filter. `firstSeen` is the place's, or undefined for a context place, which always shows.
// A photo whose words name a later place carries its own. The parent keys this by place, so each starts at the first.
export function Photos({ photos, firstSeen }: { photos: Photo[]; firstSeen?: string }) {
  const [index, setIndex] = useState(0)
  if (photos.length === 0) return null
  const at = Math.min(index, photos.length - 1)
  const photo = photos[at]
  // The arrows go round, so the button pressed keeps the focus at either end.
  const step = (by: number) => setIndex((at + by + photos.length) % photos.length)
  // With either arrow focused, the left and right arrow keys step too.
  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    step(e.key === 'ArrowLeft' ? -1 : 1)
  }
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
        {photos.length > 1 && (
          <>
            <button type="button" className="photo-arrow previous" aria-label="Previous photo" onClick={() => step(-1)} onKeyDown={onKeyDown}>
              <span aria-hidden="true">‹</span>
            </button>
            <button type="button" className="photo-arrow next" aria-label="Next photo" onClick={() => step(1)} onKeyDown={onKeyDown}>
              <span aria-hidden="true">›</span>
            </button>
            <span className="photo-count" aria-live="polite">
              <span className="visually-hidden">Photo </span>
              {at + 1} / {photos.length}
            </span>
          </>
        )}
      </div>
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
