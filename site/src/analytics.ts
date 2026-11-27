import type { Route } from './route'

// Visits are counted with GoatCounter (decision 0083). Only a build given a site code counts: the release build
// in CI sets VITE_GOATCOUNTER, and the dev server, the preview and the test builds do not.
const SITE: string | undefined = import.meta.env.VITE_GOATCOUNTER

// Whether this build counts visits, for the About page's Privacy section.
export const COUNTING = !!SITE

// Everything the site may count besides a page. A name never holds a place, a stop or an episode, so the counts
// cannot say how far anyone has read.
export type CountedEvent =
  | 'basemap-satellite'
  | 'basemap-topo'
  | 'basemap-compare'
  | 'view-tilted'
  | 'view-oblique'
  | 'read-on'
  | 'search-used'
  | 'feedback-correction'
  | 'feedback-translation'
  | 'feedback-general'
  | 'data-download'

// A link the owner shares carries a tag naming where it was posted, such as `?ref=reddit-cm`, and GoatCounter
// lists the tag as the referrer, as its own count.js does. Only a short word is sent, so a query string cannot carry
// anything else to GoatCounter.
function referrer(): string {
  const ref = new URLSearchParams(window.location.search).get('ref')
  return ref && /^[\w.-]{1,40}$/.test(ref) ? ref : document.referrer
}

// The request GoatCounter's own count.js makes, with fewer fields: no page title, and of the query string only the
// `ref` tag. `path` is a route or an event name, never the address bar's hash, which holds the reader's stop and
// the map's camera.
function send(path: Route | CountedEvent, event: boolean) {
  // Automated browsers, such as this project's own tests, are not readers.
  if (!SITE || navigator.webdriver) return
  const fields = new URLSearchParams({ p: path, s: String(window.screen.width) })
  if (event) fields.set('e', 'true')
  else if (referrer()) fields.set('r', referrer())
  // Browsers may answer a repeated address from cache.
  fields.set('rnd', Math.random().toString(36).slice(2, 7))
  // Counting must never break the site: some browsers have no sendBeacon, and a blocker may make it throw.
  try {
    navigator.sendBeacon?.(`https://${SITE}.goatcounter.com/count?${fields}`)
  } catch {
    // Not counted.
  }
}

export const countPage = (route: Route) => send(route, false)
export const countEvent = (name: CountedEvent) => send(name, true)
