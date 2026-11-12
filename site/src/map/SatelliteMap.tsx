import { useEffect, useRef } from 'react'
import * as maptilersdk from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
import type { MapRef } from '@vis.gl/react-maplibre'

// The satellite basemap: a MapTiler SDK map under the literary map, kept on the
// same camera. MapTiler counts a session per SDK map, so this module is loaded
// and the map created only when a reader leaves the literary basemap (decision 0005).

type Props = {
  literary: React.RefObject<MapRef | null>
  hidden: boolean
  onUnavailable: () => void
}

export default function SatelliteMap({ literary, hidden, onUnavailable }: Props) {
  const container = useRef<HTMLDivElement>(null)

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
    // A refused key or an exhausted quota surfaces as a failed style or tile request.
    sat.on('error', (e) => {
      const status = (e.error as { status?: number } | undefined)?.status
      if (status === 401 || status === 403 || status === 429) onUnavailable()
    })

    // Keep both cameras together, whichever map the reader drags.
    let syncing = false
    const follow = (from: { getCenter(): maptilersdk.LngLat; getZoom(): number }, to: { jumpTo(o: object): unknown }) => () => {
      if (syncing) return
      syncing = true
      to.jumpTo({ center: from.getCenter(), zoom: from.getZoom() })
      syncing = false
    }
    const topToSat = follow(top, sat)
    const satToTop = follow(sat, top)
    top.on('move', topToSat)
    sat.on('move', satToTop)

    return () => {
      top.off('move', topToSat)
      sat.remove()
    }
  }, [literary, onUnavailable])

  // Inline position: the SDK's stylesheet sets its map container to position: relative,
  // which would collapse this absolutely placed layer to zero height.
  return (
    <div ref={container} className="satellite" style={{ position: 'absolute', inset: 0, visibility: hidden ? 'hidden' : 'visible' }} />
  )
}
