import { useMemo } from 'react'
import * as maplibregl from 'maplibre-gl'
import { Map, NavigationControl } from '@vis.gl/react-maplibre'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { literaryStyle } from './style'
import { storyBounds } from './tokens'

// MapLibre 6 looks for its worker beside its own module file. Bundling moves
// that module into an app chunk, so point MapLibre at the copy Vite emits.
maplibregl.setWorkerUrl(workerUrl)

maplibregl.addProtocol('pmtiles', new Protocol().tile)

// The pmtiles protocol needs an absolute URL to make range requests against.
const tilesBase = new URL(`${import.meta.env.BASE_URL}tiles/`, window.location.origin).href

export function MapView() {
  const style = useMemo(() => literaryStyle(tilesBase), [])
  return (
    <Map
      mapLib={maplibregl}
      mapStyle={style}
      initialViewState={{ bounds: storyBounds, fitBoundsOptions: { padding: 24 } }}
      minZoom={4}
      maxZoom={13}
      dragRotate={false}
      hash="map"
      attributionControl={{ compact: true }}
      style={{ position: 'absolute', inset: 0 }}
    >
      <NavigationControl position="top-left" showCompass={false} />
    </Map>
  )
}
