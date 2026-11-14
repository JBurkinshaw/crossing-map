import type { Map as MapLibreMap } from 'maplibre-gl'
import './frame.css'

// The Wheeler sheet's frame on the lab map (review/stage-9/wheeler-places/README.md): a thin-thick-thin rule, a
// margin band holding the graticule's labels, and a thin neatline round the map, drawn by frame.css over the map's
// edges; and a lab copy of the site's title cartouche with the same rule. Both show while the map's container has
// the class `wp-framed`.
//
// MapLibre cannot place a label at the edge of the viewport, so the margin labels are HTML: on every move, each
// 15′ meridian and parallel in view is projected to the screen and its label set in the band where it meets the
// edge, as Wheeler letters them (15′, 30′, 45′, and the whole degree as 109°). Web Mercator draws the lines
// straight, so one projection per line is exact while the map is flat; tilted, the lines converge and the labels
// are hidden.

const STEP = 0.25
const MIN_ZOOM = 8

function label(deg: number): string {
  const minutes = Math.round(Math.abs(deg) * 60)
  return minutes % 60 ? `${minutes % 60}′` : `${minutes / 60}°`
}

// The band's middle and the corner it must keep clear of, read from the CSS so the two stay in step. A custom
// property holding calc() reads back as its text, so the rule's width is summed here from its parts.
function metrics(el: HTMLElement) {
  const css = getComputedStyle(el)
  const px = (name: string) => parseFloat(css.getPropertyValue(name)) || 0
  const rule = 2 * px('--wp-thin') + 2 * px('--wp-gap') + px('--wp-heavy')
  const band = px('--wp-band')
  return { mid: rule + band / 2, inset: rule + band }
}

export function addFrame(map: MapLibreMap) {
  const box = map.getContainer()
  const frame = document.createElement('div')
  frame.className = 'wp-frame'
  frame.setAttribute('aria-hidden', 'true')
  const labels = document.createElement('div')
  labels.className = 'wp-frame-labels'
  frame.append(labels)

  const cartouche = document.createElement('div')
  cartouche.className = 'wp-cartouche'
  cartouche.setAttribute('aria-hidden', 'true')
  cartouche.innerHTML = `<div class="wp-cartouche-head">
    <svg class="north" viewBox="0 0 24 48" width="14" height="28"><path d="M12 2 L18 30 L12 24 L6 30 Z" fill="currentColor" />
    <text x="12" y="45" text-anchor="middle" font-size="12">N</text></svg>
    <div><div class="wp-cartouche-title">The Crossing</div><div class="wp-cartouche-sub">Sonora, Chihuahua &amp; the New Mexico bootheel</div></div>
  </div>`
  box.append(frame, cartouche)

  const place = () => {
    labels.replaceChildren()
    if (!box.classList.contains('wp-framed') || map.getZoom() < MIN_ZOOM || map.getPitch() > 0) return
    const { mid, inset } = metrics(frame)
    const w = box.clientWidth
    const h = box.clientHeight
    const b = map.getBounds()
    const c = map.getCenter()
    const put = (text: string, side: 'top' | 'bottom' | 'left' | 'right', at: number) => {
      const s = document.createElement('span')
      s.className = `wp-edge wp-edge-${side}`
      s.textContent = text
      if (side === 'top' || side === 'bottom') {
        s.style.left = `${at}px`
        s.style.top = `${side === 'top' ? mid : h - mid}px`
      } else {
        s.style.top = `${at}px`
        s.style.left = `${side === 'left' ? mid : w - mid}px`
      }
      labels.append(s)
    }
    for (let lon = Math.ceil(b.getWest() / STEP) * STEP; lon <= b.getEast(); lon += STEP) {
      const x = map.project([lon, c.lat]).x
      if (x > inset + 8 && x < w - inset - 8) for (const side of ['top', 'bottom'] as const) put(label(lon), side, x)
    }
    for (let lat = Math.ceil(b.getSouth() / STEP) * STEP; lat <= b.getNorth(); lat += STEP) {
      const y = map.project([c.lng, lat]).y
      if (y > inset + 8 && y < h - inset - 8) for (const side of ['left', 'right'] as const) put(label(lat), side, y)
    }
  }
  map.on('move', place)
  map.on('resize', place)
  map.on('load', place)
  return {
    // Shows or hides the frame, the cartouche copy and the margin labels.
    show(on: boolean) {
      box.classList.toggle('wp-framed', on)
      place()
    },
  }
}
