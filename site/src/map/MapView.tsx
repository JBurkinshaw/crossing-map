import { lazy, Suspense, useCallback, useEffect, useMemo, useState, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import { Map, NavigationControl, Popup, ScaleControl, type MapRef } from '@vis.gl/react-maplibre'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { Feature, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import { StoryLayers } from './StoryLayers'
import { treatmentFromUrl } from './relief'
import { BASE_LAYERS, literaryStyle } from './style'
import { storyBounds } from './tokens'

// MapLibre 6 looks for its worker beside its own module file. Bundling moves
// that module into an app chunk, so point MapLibre at the copy Vite emits.
maplibregl.setWorkerUrl(workerUrl)
maplibregl.addProtocol('pmtiles', new Protocol().tile)

// Loaded only when the reader first leaves the literary basemap.
const SatelliteMap = lazy(() => import('./SatelliteMap'))

// The pmtiles protocol needs an absolute URL to make range requests against.
const tilesBase = new URL(`${import.meta.env.BASE_URL}tiles/`, window.location.origin).href
const fontsBase = new URL(`${import.meta.env.BASE_URL}fonts/`, window.location.origin).href
const dataBase = new URL(`${import.meta.env.BASE_URL}data/`, window.location.origin).href

type Picked = { lon: number; lat: number; props: StoryProps }
type Basemap = 'literary' | 'satellite' | 'compare'

type Props = {
  mapRef: RefObject<MapRef | null>
  story: Story | null
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  onSelectStop: (index: number) => void
}

export function MapView({ mapRef, story, stops, stopIndex, onSelectStop }: Props) {
  const style = useMemo(() => literaryStyle(tilesBase, fontsBase, dataBase, treatmentFromUrl()), [])
  const [picked, setPicked] = useState<Picked | null>(null)
  const [basemap, setBasemap] = useState<Basemap>('literary')
  const [unavailable, setUnavailable] = useState(false)
  // Once created, the satellite map stays (hidden on the literary basemap): MapTiler counts each new map as a session.
  const [satelliteStarted, setSatelliteStarted] = useState(false)
  if (basemap !== 'literary' && !satelliteStarted) setSatelliteStarted(true)
  // Compare mode: the literary map shows left of this split, in percent of the width.
  const [split, setSplit] = useState(50)

  const onUnavailable = useCallback(() => {
    setUnavailable(true)
    setBasemap('literary')
  }, [])

  // In satellite mode the literary paper and base layers hide, so the story layers draw over the imagery.
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    const apply = () => {
      for (const id of BASE_LAYERS) {
        if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', basemap === 'satellite' ? 'none' : 'visible')
      }
    }
    if (map.isStyleLoaded()) apply()
    else map.once('load', apply)
  }, [basemap, mapRef])

  const dragSplit = (e: React.PointerEvent<HTMLDivElement>) => {
    const area = e.currentTarget.parentElement!.getBoundingClientRect()
    const move = (ev: PointerEvent) => setSplit(Math.min(95, Math.max(5, ((ev.clientX - area.left) / area.width) * 100)))
    const up = () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
    }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
  }

  return (
    <div className={`map-area${basemap === 'literary' ? '' : ' has-satellite'}`}>
      {satelliteStarted && !unavailable && (
        <Suspense fallback={null}>
          <SatelliteMap literary={mapRef} hidden={basemap === 'literary'} onUnavailable={onUnavailable} />
        </Suspense>
      )}
      <div className="literary" style={basemap === 'compare' ? { clipPath: `inset(0 ${100 - split}% 0 0)` } : undefined}>
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
      </div>
      {basemap === 'compare' && (
        <div
          className="swipe"
          style={{ left: `${split}%` }}
          onPointerDown={dragSplit}
          role="slider"
          aria-label="Compare the literary map and satellite"
          aria-valuemin={5}
          aria-valuemax={95}
          aria-valuenow={Math.round(split)}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'ArrowLeft') setSplit((s) => Math.max(5, s - 5))
            if (e.key === 'ArrowRight') setSplit((s) => Math.min(95, s + 5))
          }}
        />
      )}
      <div className="basemap-switch" role="radiogroup" aria-label="Basemap">
        {(['literary', 'satellite', 'compare'] as const).map((b) => (
          <button
            key={b}
            type="button"
            role="radio"
            aria-checked={basemap === b}
            disabled={b !== 'literary' && unavailable}
            onClick={() => setBasemap(b)}
          >
            {b === 'literary' ? 'Literary' : b === 'satellite' ? 'Satellite' : 'Compare'}
          </button>
        ))}
      </div>
      {unavailable && <p className="notice" role="status">Satellite imagery is unavailable right now. The literary map works as normal.</p>}
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
