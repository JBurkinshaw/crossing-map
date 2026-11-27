import { useCallback, useState } from 'react'
import { countEvent } from '../analytics'

// Which map the reader sees: the basemap, and the view of the vintage map. App owns both, so the story data it
// hands the map (flat or oblique) always matches the view drawn in the same render.

export type Basemap = 'literary' | 'satellite' | 'topo' | 'compare'
// Views of the literary map: flat (the default), tilted (live 3D terrain) and oblique (plan oblique relief).
export type View = 'flat' | 'tilted' | 'oblique'
// The ground under the vintage map: plain paper, land cover (decision 0040), or the faded satellite map.
export type Ground = 'paper' | 'landcover' | 'tint'
// The MapTiler map compare mode sets against the vintage map, right of the swipe (decision 0046).
export type CompareWith = 'satellite' | 'topo'

// The views apply to the vintage basemap, and Flat and Tilted to compare mode too (the Oblique view's line work
// is shifted north, so it would not line up with the imagery); satellite and topo are always flat.
export const viewAvailable = (basemap: Basemap, view: View) =>
  basemap === 'literary' || (basemap === 'compare' && view !== 'oblique')

export function useMapMode() {
  const [{ basemap, compareWith }, setMode] = useState<{ basemap: Basemap; compareWith: CompareWith }>({ basemap: 'literary', compareWith: 'satellite' })
  const [chosenView, setChosenView] = useState<View>('flat')
  const view: View = viewAvailable(basemap, chosenView) ? chosenView : 'flat'
  // Compare from the Oblique view keeps the relief standing up, as Tilted. In Compare, Satellite or Topo sets the
  // map right of the swipe; choosing the map already there shows it on its own (decision 0046).
  // Stable across renders: SatelliteMap rebuilds its map when a handler it depends on changes.
  const chooseBasemap = useCallback((next: Basemap) => {
    if (next !== 'literary') countEvent(`basemap-${next}`)
    if (next === 'compare') setChosenView((v) => (v === 'oblique' ? 'tilted' : v))
    setMode((m) =>
      m.basemap === 'compare' && (next === 'satellite' || next === 'topo') && next !== m.compareWith
        ? { ...m, compareWith: next }
        : { ...m, basemap: next },
    )
  }, [])
  const setView = useCallback((next: View) => {
    if (next !== 'flat') countEvent(`view-${next}`)
    setChosenView(next)
  }, [])
  return { basemap, chooseBasemap, view, setView, compareWith }
}
