import { useEffect, useRef, useState } from 'react'
import * as maptilersdk from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { IControl, Map as MapLibreMap } from 'maplibre-gl'

// The MapTiler basemaps: one MapTiler SDK map under the literary map, kept on the
// same camera, showing satellite imagery or MapTiler Topo. MapTiler counts a session
// per SDK map, so this module is loaded and the map created only when a reader first
// needs it, and Topo switches the style of the same map (decision 0005).

type Props = {
  literary: React.RefObject<MapRef | null>
  hidden: boolean
  // MapTiler Topo instead of satellite imagery.
  topo: boolean
  // Terrain exaggeration while the literary map is tilted over 3D terrain, so the imagery stays under it.
  terrain: number | null
  onUnavailable: () => void
  // The credits of the MapTiler style's sources, which the literary map's attribution control shows. The
  // dev-only hillshade lab leaves it out.
  onCredits?: (credits: string[]) => void
}

export default function SatelliteMap({ literary, hidden, topo, terrain, onUnavailable, onCredits }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const satRef = useRef<maptilersdk.Map | null>(null)
  // Set on the style's first load; isStyleLoaded() is false again whenever tiles are loading.
  const [loaded, setLoaded] = useState(false)
  const styleOf = (isTopo: boolean) => (isTopo ? maptilersdk.MapStyle.TOPO : maptilersdk.MapStyle.SATELLITE)
  const shownTopo = useRef(topo)
  const terrainRef = useRef(terrain)
  useEffect(() => {
    terrainRef.current = terrain
  }, [terrain])

  // The map is made once per mount: a new handler must not tear it down, as MapTiler counts each map as a session.
  const unavailable = useRef(onUnavailable)
  useEffect(() => {
    unavailable.current = onUnavailable
  }, [onUnavailable])
  const credits = useRef(onCredits)
  useEffect(() => {
    credits.current = onCredits
  }, [onCredits])
  // MapTiler's logo, in the literary map's bottom-left controls (decision 0043).
  const logo = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const onUnavailable = () => unavailable.current()
    const top = literary.current?.getMap()
    const key = import.meta.env.VITE_MAPTILER_KEY
    if (!container.current || !top || !key) {
      onUnavailable()
      return
    }
    maptilersdk.config.apiKey = key
    // The SDK's own usage reports to MapTiler (its version, the key, which features are on) are not needed here.
    maptilersdk.config.telemetry = false
    const sat = new maptilersdk.Map({
      container: container.current,
      style: styleOf(shownTopo.current),
      center: top.getCenter(),
      zoom: top.getZoom(),
      navigationControl: false,
      geolocateControl: false,
      terrainControl: false,
      scaleControl: false,
      fullscreenControl: false,
      projectionControl: false,
      // The SDK's own logo and attribution would sit on this hidden-under map, apart from the literary map's
      // controls. Both move to the literary map instead: MapTiler's free plan needs both shown (decision 0043).
      forceNoAttributionControl: true,
    })
    satRef.current = sat

    const sdkLogo = new maptilersdk.MaptilerLogoControl()
    const logoControl: IControl = {
      onAdd: (m: MapLibreMap) => {
        const el = sdkLogo.onAdd(m as unknown as maptilersdk.Map)
        el.classList.add('maptiler-logo')
        logo.current = el
        return el
      },
      onRemove: () => {
        sdkLogo.onRemove()
        logo.current = null
      },
    }
    top.addControl(logoControl, 'bottom-left')

    // Each source's credit, as MapLibre's attribution control would gather it, sent on whenever it changes
    // (a style switch between satellite and Topo changes the sources).
    let sent = ''
    const sendCredits = () => {
      const all = Object.keys(sat.getStyle()?.sources ?? {})
        .map((id) => (sat.getSource(id) as { attribution?: string } | undefined)?.attribution)
        .filter((a): a is string => !!a)
      const unique = [...new Set(all)]
      if (unique.join('|') === sent) return
      sent = unique.join('|')
      credits.current?.(unique)
    }
    sat.on('idle', sendCredits)
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
      top.removeControl(logoControl)
      credits.current?.([])
      sat.remove()
      satRef.current = null
      setLoaded(false)
    }
  }, [literary])

  // A new style drops the terrain, so it goes back on once the style has loaded.
  useEffect(() => {
    const sat = satRef.current
    if (!sat || !loaded || shownTopo.current === topo) return
    shownTopo.current = topo
    sat.setStyle(styleOf(topo))
    sat.once('style.load', () => {
      if (terrainRef.current) sat.enableTerrain(terrainRef.current)
    })
  }, [topo, loaded])

  useEffect(() => {
    const sat = satRef.current
    if (!sat || !loaded) return
    if (terrain) sat.enableTerrain(terrain)
    else if (sat.hasTerrain()) sat.disableTerrain()
  }, [terrain, loaded])

  useEffect(() => {
    if (logo.current) logo.current.style.display = hidden ? 'none' : 'block'
  }, [hidden, loaded])

  // Inline position: the SDK's stylesheet sets its map container to position: relative,
  // which would collapse this absolutely placed layer to zero height.
  return (
    <div ref={container} className="satellite" style={{ position: 'absolute', inset: 0, visibility: hidden ? 'hidden' : 'visible' }} />
  )
}
