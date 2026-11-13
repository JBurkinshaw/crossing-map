import { useEffect, useRef, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { StyleSpecification } from 'maplibre-gl'
import type { MapRef } from '@vis.gl/react-maplibre'

// Compare mode: the classic base on its own map, clipped to the left of the swipe, between the satellite map
// and the main map. The main map then draws only the story layers, across the whole width, as in satellite
// mode. This map takes no input and follows the main map's camera.

type Props = {
  main: RefObject<MapRef | null>
  style: StyleSpecification
  // The classic base shows left of this split, in percent of the width.
  split: number
}

export default function ClassicUnderlay({ main, style, split }: Props) {
  const container = useRef<HTMLDivElement>(null)

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
    const follow = () => map.jumpTo({ center: top.getCenter(), zoom: top.getZoom(), pitch: top.getPitch(), bearing: top.getBearing() })
    top.on('move', follow)
    return () => {
      top.off('move', follow)
      map.remove()
    }
  }, [main, style])

  return <div ref={container} aria-hidden="true" style={{ position: 'absolute', inset: 0, clipPath: `inset(0 ${100 - split}% 0 0)` }} />
}
