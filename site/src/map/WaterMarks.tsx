import { useEffect } from 'react'
import { useMap } from '@vis.gl/react-maplibre'
import type { Palette } from './tokens'
import { addWaterMarks } from './waterPlaces'

// The water places' marks (waterPlaces.ts) on the map a react-maplibre Map holds: render it inside the Map.
export function WaterMarks({ palette }: { palette: Palette }) {
  const { current } = useMap()
  useEffect(() => {
    const map = current?.getMap()
    return map ? addWaterMarks(map, palette) : undefined
  }, [current, palette])
  return null
}
