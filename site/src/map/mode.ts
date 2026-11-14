import { useCallback, useState } from 'react'

// Which map the reader sees: the basemap, and the view of the classic map. App owns both, so the story data it
// hands the map (flat or raised) always matches the view drawn in the same render.

export type Basemap = 'literary' | 'satellite' | 'topo' | 'compare'
// Views of the literary map: flat (the default), tilted (live 3D terrain) and raised (plan oblique relief).
export type View = 'flat' | 'tilted' | 'raised'

// The views apply to the classic basemap, and Flat and Tilted to compare mode too (the Raised view's line work
// is shifted north, so it would not line up with the imagery); satellite and topo are always flat.
export const viewAvailable = (basemap: Basemap, view: View) =>
  basemap === 'literary' || (basemap === 'compare' && view !== 'raised')

export function useMapMode() {
  const [basemap, setBasemap] = useState<Basemap>('literary')
  const [chosenView, setView] = useState<View>('flat')
  const view: View = viewAvailable(basemap, chosenView) ? chosenView : 'flat'
  // Compare from the Raised view keeps the relief standing up, as Tilted.
  // Stable across renders: SatelliteMap rebuilds its map when a handler it depends on changes.
  const chooseBasemap = useCallback((next: Basemap) => {
    if (next === 'compare') setView((v) => (v === 'raised' ? 'tilted' : v))
    setBasemap(next)
  }, [])
  return { basemap, chooseBasemap, view, setView }
}
