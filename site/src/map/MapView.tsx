import { useMemo, useState, type Ref } from 'react'
import * as maplibregl from 'maplibre-gl'
import { Map, NavigationControl, Popup, ScaleControl, type MapRef } from '@vis.gl/react-maplibre'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { Feature, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import { StoryLayers } from './StoryLayers'
import { literaryStyle } from './style'
import { storyBounds } from './tokens'

// MapLibre 6 looks for its worker beside its own module file. Bundling moves
// that module into an app chunk, so point MapLibre at the copy Vite emits.
maplibregl.setWorkerUrl(workerUrl)
maplibregl.addProtocol('pmtiles', new Protocol().tile)

// The pmtiles protocol needs an absolute URL to make range requests against.
const tilesBase = new URL(`${import.meta.env.BASE_URL}tiles/`, window.location.origin).href
const fontsBase = new URL(`${import.meta.env.BASE_URL}fonts/`, window.location.origin).href

type Picked = { lon: number; lat: number; props: StoryProps }

type Props = {
  mapRef: Ref<MapRef>
  story: Story | null
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  onSelectStop: (index: number) => void
}

export function MapView({ mapRef, story, stops, stopIndex, onSelectStop }: Props) {
  const style = useMemo(() => literaryStyle(tilesBase, fontsBase), [])
  const [picked, setPicked] = useState<Picked | null>(null)

  return (
    <div className="map-area">
    <Map
      ref={mapRef}
      mapLib={maplibregl}
      mapStyle={style}
      initialViewState={{ bounds: storyBounds, fitBoundsOptions: { padding: 24 } }}
      minZoom={4}
      maxZoom={13}
      dragRotate={false}
      hash="map"
      attributionControl={{ compact: true }}
      interactiveLayerIds={['places-point', 'areas-fill']}
      onClick={(e) => {
        const f = e.features?.[0]
        setPicked(f ? { lon: e.lngLat.lng, lat: e.lngLat.lat, props: f.properties as StoryProps } : null)
      }}
      style={{ position: 'absolute', inset: 0 }}
      onLoad={(e) => {
        // Review tooling (tools/*.mjs) drives the map through this handle; only with ?debug.
        if (new URLSearchParams(window.location.search).has('debug')) {
          ;(window as unknown as { __map: unknown }).__map = e.target
        }
      }}
    >
      <NavigationControl position="top-left" showCompass={false} />
      {/* Miles, the book's own unit. */}
      <ScaleControl position="bottom-left" unit="imperial" maxWidth={140} />
      {story && <StoryLayers story={story} stops={stops} stopIndex={stopIndex} onSelectStop={onSelectStop} />}
      {picked && (
        <Popup longitude={picked.lon} latitude={picked.lat} onClose={() => setPicked(null)} maxWidth="280px">
          <strong>{picked.props.name}</strong>
          <div className="meta">
            {picked.props.certainty} · {picked.props.source}
            {picked.props.source_id ? ` ${picked.props.source_id}` : ''}
          </div>
          {picked.props.reasoning && <p>{picked.props.reasoning}</p>}
        </Popup>
      )}
    </Map>
    <div className="cartouche" aria-hidden="true">
      <svg className="north" viewBox="0 0 24 48" width="14" height="28">
        <path d="M12 2 L18 30 L12 24 L6 30 Z" fill="currentColor" />
        <text x="12" y="45" textAnchor="middle" fontSize="12">N</text>
      </svg>
      <div>
        <div className="cartouche-title">The Crossing</div>
        <div className="cartouche-sub">Sonora, Chihuahua &amp; the New Mexico bootheel</div>
      </div>
    </div>
    </div>
  )
}
