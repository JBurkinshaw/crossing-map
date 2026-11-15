import { useEffect, useRef, useState, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { StyleSpecification } from 'maplibre-gl'
import type { MapRef } from '@vis.gl/react-maplibre'
import { contourText, glyphText } from './relief'
import { palette } from './tokens'
import { addWaterMarks } from './waterPlaces'
import type { Units } from '../units'

// Compare mode: the classic base on its own map, clipped to the left of the swipe, between the satellite map
// and the main map. The main map then draws only the story layers, across the whole width, as in satellite
// mode. This map takes no input and follows the main map's camera. It shows left of the swipe's split, which
// CompareSwipe keeps in the --split CSS variable on the map area.

type Props = {
  main: RefObject<MapRef | null>
  style: StyleSpecification
  // Heights on summits and contours: set on the map in place, so a change of units does not rebuild it.
  units: Units
  // In the Tilted view, the same 3D terrain as the main map, so the base stays under the story layers.
  terrain: { url: string; exaggeration: number } | null
}

function setUnits(map: maplibregl.Map, units: Units) {
  map.setLayoutProperty('mountain-glyph', 'text-field', glyphText(units))
  map.setLayoutProperty('contour-label', 'text-field', contourText(units))
}

export default function ClassicUnderlay({ main, style, units, terrain }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  // map.loaded() is false again whenever tiles load, so the first load is recorded here.
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const top = main.current?.getMap()
    if (!container.current || !top) return
    const map = new maplibregl.Map({
      container: container.current,
      style,
      center: top.getCenter(),
      zoom: top.getZoom(),
      pitch: top.getPitch(),
      interactive: false,
      attributionControl: false,
    })
    mapRef.current = map
    addWaterMarks(map, palette)
    map.once('load', () => setReady(true))
    const follow = () => map.jumpTo({ center: top.getCenter(), zoom: top.getZoom(), pitch: top.getPitch(), bearing: top.getBearing() })
    top.on('move', follow)
    return () => {
      top.off('move', follow)
      map.remove()
      mapRef.current = null
      setReady(false)
    }
  }, [main, style])

  useEffect(() => {
    const map = mapRef.current
    if (map && ready) setUnits(map, units)
  }, [units, ready])

  const terrainUrl = terrain?.url
  const exaggeration = terrain?.exaggeration
  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready) return
    if (terrainUrl && !map.getSource('terrain3d')) {
      map.addSource('terrain3d', { type: 'raster-dem', url: terrainUrl, encoding: 'terrarium', tileSize: 256 })
    }
    map.setTerrain(terrainUrl && exaggeration ? { source: 'terrain3d', exaggeration } : null)
  }, [terrainUrl, exaggeration, ready])

  return <div ref={container} aria-hidden="true" style={{ position: 'absolute', inset: 0, clipPath: 'inset(0 calc(100% - var(--split, 50%)) 0 0)' }} />
}
