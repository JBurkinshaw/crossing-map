import { useEffect, useRef, type RefObject } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'

// The Wheeler sheet's frame round the vintage map (review/stage-9/wheeler-places/README.md and
// review/stage-9/wheeler-site/README.md): a thin-thick-thin rule, a margin band holding the 15′ graticule's
// labels, and a thin neatline, drawn by map.css over the map's edges so the map keeps its size. MapView shows it
// on the vintage map in the Flat and Tilted views; on phones it is the rule alone (map.css), with no band.
//
// MapLibre cannot place a label at the edge of the viewport, so the margin labels are HTML: on every move, each 15′
// meridian and parallel in view is projected to the screen and its label set in the band where it meets the edge,
// as Wheeler letters them (15′, 30′, 45′, and the whole degree as 109°). Web Mercator draws the lines straight, so
// one projection per line is exact while the map is flat; tilted, the lines converge and the labels are hidden.
// The frame is decoration (aria-hidden): the map's position is in its address and its scale bar.

const STEP = 0.25
// The graticule's lines start at this zoom (style.ts).
export const GRATICULE_MIN_ZOOM = 8

function label(deg: number): string {
  const minutes = Math.round(Math.abs(deg) * 60)
  return minutes % 60 ? `${minutes % 60}′` : `${minutes / 60}°`
}

// The band's middle and how far in it ends, read from the CSS so the two stay in step. A custom property holding
// calc() reads back as its text, so the rule's width is summed here from its parts.
function metrics(el: HTMLElement) {
  const css = getComputedStyle(el)
  const px = (name: string) => parseFloat(css.getPropertyValue(name)) || 0
  const rule = 2 * px('--frame-thin') + 2 * px('--frame-gap') + px('--frame-heavy')
  const band = px('--frame-band')
  return { band, mid: rule + band / 2, inset: rule + band }
}

type Props = { mapRef: RefObject<MapRef | null>; shown: boolean }

export function MapFrame({ mapRef, shown }: Props) {
  const frameRef = useRef<HTMLDivElement>(null)
  const labelsRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const map = mapRef.current?.getMap()
    const frame = frameRef.current
    const labels = labelsRef.current
    if (!map || !frame || !labels) return
    const place = () => {
      labels.replaceChildren()
      const { band, mid, inset } = metrics(frame)
      if (!shown || band === 0 || map.getZoom() < GRATICULE_MIN_ZOOM || map.getPitch() > 0) return
      const w = frame.clientWidth
      const h = frame.clientHeight
      const b = map.getBounds()
      const c = map.getCenter()
      const put = (text: string, side: 'top' | 'bottom' | 'left' | 'right', at: number) => {
        const s = document.createElement('span')
        s.className = 'frame-edge'
        s.textContent = text
        const across = side === 'top' || side === 'left' ? mid : (side === 'bottom' ? h : w) - mid
        s.style.left = `${side === 'top' || side === 'bottom' ? at : across}px`
        s.style.top = `${side === 'top' || side === 'bottom' ? across : at}px`
        labels.append(s)
      }
      // Labels that would land in a corner of the band are skipped.
      for (let lon = Math.ceil(b.getWest() / STEP) * STEP; lon <= b.getEast(); lon += STEP) {
        const x = map.project([lon, c.lat]).x
        if (x > inset + 8 && x < w - inset - 8) for (const side of ['top', 'bottom'] as const) put(label(lon), side, x)
      }
      for (let lat = Math.ceil(b.getSouth() / STEP) * STEP; lat <= b.getNorth(); lat += STEP) {
        const y = map.project([c.lng, lat]).y
        if (y > inset + 8 && y < h - inset - 8) for (const side of ['left', 'right'] as const) put(label(lat), side, y)
      }
    }
    place()
    map.on('move', place)
    map.on('resize', place)
    return () => {
      map.off('move', place)
      map.off('resize', place)
      labels.replaceChildren()
    }
  }, [mapRef, shown])
  return (
    <div ref={frameRef} className="map-frame" aria-hidden="true" hidden={!shown}>
      <div ref={labelsRef} />
    </div>
  )
}
