import { useCallback } from 'react'
import { readChoice, store, useStoredState } from '../storage'

// Which map the reader sees: the basemap, the view of the vintage map, and its ground. App owns the basemap and the
// view, so the story data it hands the map (flat or oblique) always matches the view drawn in the same render.
// MapView owns the ground (useGround).

const BASEMAPS = ['literary', 'satellite', 'topo', 'compare'] as const
export type Basemap = (typeof BASEMAPS)[number]
// Views of the literary map: flat (the default), tilted (live 3D terrain) and oblique (plan oblique relief).
const VIEWS = ['flat', 'tilted', 'oblique'] as const
export type View = (typeof VIEWS)[number]
// The ground under the vintage map: plain paper, land cover (decision 0040), or the faded satellite map.
const GROUNDS = ['paper', 'landcover', 'tint'] as const
export type Ground = (typeof GROUNDS)[number]
// The MapTiler map compare mode sets against the vintage map, right of the swipe (decision 0046).
const COMPARE_WITH = ['satellite', 'topo'] as const
export type CompareWith = (typeof COMPARE_WITH)[number]

// The views apply to the vintage basemap, and Flat and Tilted to compare mode too (the Oblique view's line work
// is shifted north, so it would not line up with the imagery); satellite and topo are always flat.
export const viewAvailable = (basemap: Basemap, view: View) =>
  basemap === 'literary' || (basemap === 'compare' && view !== 'oblique')

// The reader's choices of map, compare map, view and ground, kept for the next visit (decision 0078). Each key holds
// what the reader chose, not what is in force: Oblique stays the chosen view while Satellite shows.
const KEYS = { basemap: 'crossing-map.basemap', compareWith: 'crossing-map.compare-with', view: 'crossing-map.view', ground: 'crossing-map.ground' }

type Mode = { basemap: Basemap; compareWith: CompareWith }
const readMode = (): Mode => ({
  basemap: readChoice(KEYS.basemap, BASEMAPS, 'literary'),
  compareWith: readChoice(KEYS.compareWith, COMPARE_WITH, 'satellite'),
})
const saveMode = ({ basemap, compareWith }: Mode) => {
  store(KEYS.basemap, basemap)
  store(KEYS.compareWith, compareWith)
}
const readView = () => readChoice(KEYS.view, VIEWS, 'flat')
const saveView = (view: View) => store(KEYS.view, view)
// Land cover is the default ground (decision 0072).
const readGround = () => readChoice(KEYS.ground, GROUNDS, 'landcover')
const saveGround = (ground: Ground) => store(KEYS.ground, ground)

export const useGround = () => useStoredState(readGround, saveGround)

export function useMapMode() {
  const [{ basemap, compareWith }, setMode] = useStoredState(readMode, saveMode)
  const [chosenView, setView] = useStoredState(readView, saveView)
  const view: View = viewAvailable(basemap, chosenView) ? chosenView : 'flat'
  // Compare from the Oblique view keeps the relief standing up, as Tilted. In Compare, Satellite or Topo sets the
  // map right of the swipe; choosing the map already there shows it on its own (decision 0046).
  // Stable across renders: SatelliteMap rebuilds its map when a handler it depends on changes.
  const chooseBasemap = useCallback((next: Basemap) => {
    if (next === 'compare') setView((v) => (v === 'oblique' ? 'tilted' : v))
    setMode((m) =>
      m.basemap === 'compare' && (next === 'satellite' || next === 'topo') && next !== m.compareWith
        ? { ...m, compareWith: next }
        : { ...m, basemap: next },
    )
  }, [setMode, setView])
  return { basemap, chooseBasemap, view, setView, compareWith }
}
