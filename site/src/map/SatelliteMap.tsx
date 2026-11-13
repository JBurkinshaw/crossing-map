import { useEffect, useRef, useState } from 'react'
import * as maptilersdk from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
import type { MapRef } from '@vis.gl/react-maplibre'

// The satellite basemap: a MapTiler SDK map under the literary map, kept on the
// same camera. MapTiler counts a session per SDK map, so this module is loaded
// and the map created only when a reader first needs imagery: the satellite basemap,
// or the land colour under the literary map (decision 0005).

type Props = {
  literary: React.RefObject<MapRef | null>
  hidden: boolean
  // Terrain exaggeration while the literary map is tilted over 3D terrain, so the imagery stays under it.
  terrain: number | null
  onUnavailable: () => void
}

export default function SatelliteMap({ literary, hidden, terrain, onUnavailable }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const satRef = useRef<maptilersdk.Map | null>(null)
  // Set on the style's first load; isStyleLoaded() is false again whenever tiles are loading.
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    const top = literary.current?.getMap()
    const key = import.meta.env.VITE_MAPTILER_KEY
    if (!container.current || !top || !key) {
      onUnavailable()
      return
    }
    maptilersdk.config.apiKey = key
    const sat = new maptilersdk.Map({
      container: container.current,
      style: maptilersdk.MapStyle.SATELLITE,
      center: top.getCenter(),
      zoom: top.getZoom(),
      navigationControl: false,
      geolocateControl: false,
      terrainControl: false,
      scaleControl: false,
      fullscreenControl: false,
      projectionControl: false,
    })
    satRef.current = sat
    sat.once('load', () => setLoaded(true))
    // A refused key or an exhausted quota surfaces as a failed style or tile request.
    sat.on('error', (e) => {
      const status = (e.error as { status?: number } | undefined)?.status
      if (status === 401 || status === 403 || status === 429) onUnavailable()
    })

    // Keep both cameras together, whichever map the reader drags.
    let syncing = false
    type Camera = { getCenter(): maptilersdk.LngLat; getZoom(): number; getPitch(): number; getBearing(): number }
    const follow = (from: Camera, to: { jumpTo(o: object): unknown }) => () => {
      if (syncing) return
      syncing = true
      to.jumpTo({ center: from.getCenter(), zoom: from.getZoom(), pitch: from.getPitch(), bearing: from.getBearing() })
      syncing = false
    }
    const topToSat = follow(top, sat)
    const satToTop = follow(sat, top)
    top.on('move', topToSat)
    sat.on('move', satToTop)

    return () => {
      top.off('move', topToSat)
      sat.remove()
      satRef.current = null
      setLoaded(false)
    }
  }, [literary, onUnavailable])

  useEffect(() => {
    const sat = satRef.current
    if (!sat || !loaded) return
    if (terrain) sat.enableTerrain(terrain)
    else if (sat.hasTerrain()) sat.disableTerrain()
  }, [terrain, loaded])

  // Inline position: the SDK's stylesheet sets its map container to position: relative,
  // which would collapse this absolutely placed layer to zero height.
  return (
    <div ref={container} className="satellite" style={{ position: 'absolute', inset: 0, visibility: hidden ? 'hidden' : 'visible' }} />
  )
}
