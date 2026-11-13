import { useEffect, useRef, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { StyleSpecification } from 'maplibre-gl'
import type { MapRef } from '@vis.gl/react-maplibre'
import { contourText, glyphText } from './relief'
import type { Units } from '../units'

// Compare mode: the classic base on its own map, clipped to the left of the swipe, between the satellite map
// and the main map. The main map then draws only the story layers, across the whole width, as in satellite
// mode. This map takes no input and follows the main map's camera.

type Props = {
  main: RefObject<MapRef | null>
  style: StyleSpecification
  // The classic base shows left of this split, in percent of the width.
  split: number
  // Heights on summits and contours: set on the map in place, so a change of units does not rebuild it.
  units: Units
}

function setUnits(map: maplibregl.Map, units: Units) {
  map.setLayoutProperty('mountain-glyph', 'text-field', glyphText(units))
  map.setLayoutProperty('contour-label', 'text-field', contourText(units))
}

export default function ClassicUnderlay({ main, style, split, units }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const unitsRef = useRef(units)
  // map.loaded() is false again whenever tiles load, so the first load is recorded here.
  const ready = useRef(false)

  useEffect(() => {
    const top = main.current?.getMap()
    if (!container.current || !top) return
    const map = new maplibregl.Map({
      container: container.current,
      style,
      center: top.getCenter(),
      zoom: top.getZoom(),
      interactive: false,
      attributionControl: false,
    })
    mapRef.current = map
    map.once('load', () => {
      ready.current = true
      setUnits(map, unitsRef.current)
    })
    const follow = () => map.jumpTo({ center: top.getCenter(), zoom: top.getZoom(), pitch: top.getPitch(), bearing: top.getBearing() })
    top.on('move', follow)
    return () => {
      top.off('move', follow)
      map.remove()
      mapRef.current = null
      ready.current = false
    }
  }, [main, style])

  useEffect(() => {
    unitsRef.current = units
    const map = mapRef.current
    if (map && ready.current) setUnits(map, units)
  }, [units])

  return <div ref={container} aria-hidden="true" style={{ position: 'absolute', inset: 0, clipPath: `inset(0 ${100 - split}% 0 0)` }} />
}
