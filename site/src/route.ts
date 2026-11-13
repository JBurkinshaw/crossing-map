import { useSyncExternalStore } from 'react'

// A small hash router for the site's pages. Only hashes starting `#/` are routes; anything else, such as the
// map's own `#map=zoom/lat/lon`, is the map. MapLibre adds `&map=...` to whatever hash is showing when the
// map moves, so a route ends at the first `&`.
export type Route = '/' | '/about' | '/about/how-its-built' | '/data' | '/credits'
const ROUTES: Route[] = ['/', '/about', '/about/how-its-built', '/data', '/credits']

function read(): Route {
  const hash = window.location.hash
  if (!hash.startsWith('#/')) return '/'
  const path = hash.slice(1).split('&')[0].replace(/(.)\/$/, '$1')
  return ROUTES.includes(path as Route) ? (path as Route) : '/'
}

// The map's camera when the reader left it, so "Back to the map" returns to the same view. MapLibre writes
// the camera with history.replaceState, which fires no event, so it is read from the URL being left.
let lastMapHash = ''

function subscribe(onChange: () => void) {
  const listener = (e: HashChangeEvent) => {
    const left = new URL(e.oldURL).hash
    if (!left.startsWith('#/')) lastMapHash = left
    onChange()
  }
  window.addEventListener('hashchange', listener)
  return () => window.removeEventListener('hashchange', listener)
}

export function useRoute(): Route {
  return useSyncExternalStore(subscribe, read)
}

export function mapHref(): string {
  // Opened straight on a page: MapLibre may still have added the camera after the route.
  const camera = window.location.hash.split('&').find((part) => part.startsWith('map='))
  return lastMapHash || (camera ? `#${camera}` : '#')
}
