import * as maplibregl from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'

// One-time MapLibre setup shared by the site's map and the lab's maps, and the URLs every style reads from.

// MapLibre 6 looks for its worker beside its own module file. Bundling moves that module into an app chunk, so
// point MapLibre at the copy Vite emits.
maplibregl.setWorkerUrl(workerUrl)
// With metadata, each archive's attribution (terrain, relief, raised) reaches the map's attribution control.
maplibregl.addProtocol('pmtiles', new Protocol({ metadata: true }).tile)

// The pmtiles protocol needs absolute URLs to make range requests against. VITE_TILES_BASE points a build at
// another build's tiles: the deploy sets it for the preview when it shares the release of the root site.
const absolute = (folder: string) => new URL(`${import.meta.env.BASE_URL}${folder}/`, window.location.origin).href
const tilesOverride: string | undefined = import.meta.env.VITE_TILES_BASE
export const tilesBase = tilesOverride ? new URL(tilesOverride, window.location.origin).href : absolute('tiles')
export const fontsBase = absolute('fonts')
export const dataBase = absolute('data')

// The terrain's exaggeration in the Tilted view, on every map that draws it.
export const TERRAIN_EXAGGERATION = 1.8

// The width below which the panel becomes a bottom drawer; styles/panel.css and styles/map.css use the same.
export const PHONE_QUERY = '(max-width: 720px)'
export const isPhone = () => window.matchMedia(PHONE_QUERY).matches

export const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
// An animation's duration, or 0 for readers who ask for reduced motion.
export const motion = (ms: number) => (prefersReducedMotion() ? 0 : ms)

// MapLibre opens the compact attribution at first; it should start closed, behind its (i) button. The archives'
// credits arrive with their first tiles, which reopen it, so it is closed again once the map is idle.
export function closeAttribution(map: maplibregl.Map) {
  const close = () => map.getContainer().querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show')
  close()
  map.once('idle', close)
}

// Scripted review (Playwright, tools/) drives a map through a handle on window, with ?debug in the address. The
// handle exists only on the dev server, or in a build made with VITE_DEBUG=1; a production build drops the code.
export function exposeForScripts(name: string, map: maplibregl.Map) {
  if (!(import.meta.env.DEV || import.meta.env.VITE_DEBUG === '1')) return
  if (new URLSearchParams(window.location.search).has('debug')) (window as unknown as Record<string, unknown>)[name] = map
}
