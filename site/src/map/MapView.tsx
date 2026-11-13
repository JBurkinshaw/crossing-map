import { lazy, Suspense, useCallback, useEffect, useMemo, useState, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { LayerSpecification } from 'maplibre-gl'
import { Map, NavigationControl, Popup, ScaleControl, type MapRef } from '@vis.gl/react-maplibre'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { Feature, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import ClassicUnderlay from './ClassicUnderlay'
import { StoryLayers } from './StoryLayers'
import { RAISED_BOUNDS, RAISED_MIN_ZOOM, raisedLayers } from './relief'
import { BASE_LAYERS, literaryStyle } from './style'
import { storyBounds } from './tokens'

// MapLibre 6 looks for its worker beside its own module file. Bundling moves
// that module into an app chunk, so point MapLibre at the copy Vite emits.
maplibregl.setWorkerUrl(workerUrl)
// With metadata, each archive's attribution (terrain, relief, raised) reaches the map's attribution control.
maplibregl.addProtocol('pmtiles', new Protocol({ metadata: true }).tile)

// Loaded only when the reader first leaves the literary basemap.
const SatelliteMap = lazy(() => import('./SatelliteMap'))

// The pmtiles protocol needs an absolute URL to make range requests against.
const tilesBase = new URL(`${import.meta.env.BASE_URL}tiles/`, window.location.origin).href
const fontsBase = new URL(`${import.meta.env.BASE_URL}fonts/`, window.location.origin).href
const dataBase = new URL(`${import.meta.env.BASE_URL}data/`, window.location.origin).href

const MIN_ZOOM = 4
const TERRAIN_EXAGGERATION = 1.5
const TERRAIN_TILT = 40

// Base layers that cannot move with the terrain, hidden in the Raised view; raisedLayers() redraws the
// boundaries, roads, streams and the Mexico side from raised copies.
const NOT_RAISED = new Set(['mexico', 'relief-tint', 'hillshade', 'contour', 'hachure-coarse', 'hachure-coarse-copy',
  'hachure-fine', 'hachure-fine-copy', 'hachure-dense', 'hachure-dense-copy', 'mountain-glyph', 'county-line', 'state-line', 'country-line', 'creek',
  'river-minor', 'river', 'creek-label', 'river-label', 'road', 'railroad', 'railroad-ties'])
const RAISED_GROUPS = raisedLayers(literaryStyle(tilesBase, fontsBase, dataBase).layers)

type Picked = { lon: number; lat: number; props: StoryProps }
type Basemap = 'literary' | 'satellite' | 'compare'
// Views of the literary map: flat (the default), tilted (live 3D terrain) and raised (plan oblique relief).
export type View = 'flat' | 'tilted' | 'raised'
const VIEWS: { id: View; label: string; title: string }[] = [
  { id: 'flat', label: 'Flat', title: 'The map seen straight down' },
  { id: 'tilted', label: 'Tilted', title: 'The terrain in 3D, tilted towards the horizon' },
  { id: 'raised', label: 'Raised', title: 'A flat map on which the ranges stand up, like a block diagram' },
]

type Props = {
  mapRef: RefObject<MapRef | null>
  // In the Raised view, the raised copies of the story layers (App swaps them in).
  story: Story | null
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  onSelectStop: (index: number) => void
  onView: (view: View) => void
}

export function MapView({ mapRef, story, stops, stopIndex, onSelectStop, onView }: Props) {
  const style = useMemo(() => literaryStyle(tilesBase, fontsBase, dataBase), [])
  // Compare mode's classic underlay gets its own copy: a map may change the style object it is given.
  const underlayStyle = useMemo(() => literaryStyle(tilesBase, fontsBase, dataBase), [])
  const [picked, setPicked] = useState<Picked | null>(null)
  const [basemap, setBasemap] = useState<Basemap>('literary')
  const [unavailable, setUnavailable] = useState(false)
  // Once created, the satellite map stays (hidden on the literary basemap): MapTiler counts each new map as a session.
  const [satelliteStarted, setSatelliteStarted] = useState(false)
  // Compare mode: the classic base shows left of this split, in percent of the width.
  const [split, setSplit] = useState(50)
  // The views apply to the classic basemap only; satellite and compare modes are always flat.
  const [chosenView, setView] = useState<View>('flat')
  const view: View = basemap === 'literary' ? chosenView : 'flat'
  // Land colour: the satellite map, faded, under the literary map in the Flat and Tilted views. The Raised view's
  // line work is shifted north, so imagery would not line up under it.
  const [landColour, setLandColour] = useState(false)
  const wash = landColour && !unavailable && basemap === 'literary' && view !== 'raised'
  if ((basemap !== 'literary' || wash) && !satelliteStarted) setSatelliteStarted(true)
  // Set once the style first loads. map.isStyleLoaded() is not a substitute: it is false again whenever
  // tiles are loading, and 'load' fires only once.
  const [loaded, setLoaded] = useState(false)
  // The Raised view's archives, fetched the first time the reader turns it on.
  const [raisedArchives, setRaisedArchives] = useState<string[] | null>(null)
  useEffect(() => {
    if (view !== 'raised' || raisedArchives) return
    fetch(`${dataBase}raised/archives.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setRaisedArchives, () => setRaisedArchives([]))
  }, [view, raisedArchives])

  useEffect(() => onView(view), [view, onView])

  const onUnavailable = useCallback(() => {
    setUnavailable(true)
    setBasemap('literary')
  }, [])

  // In satellite and compare modes the literary paper and base layers hide, so the story layers draw over the
  // imagery (in compare mode, ClassicUnderlay draws the classic base left of the swipe);
  // in the Raised view the base layers that cannot move with the terrain hide, and the raised line work shows.
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !loaded) return
    const raised = view === 'raised'
    // The raised line work comes in several archives (each under 100 MB), listed in data/raised/archives.json;
    // every raised layer is drawn once per archive.
    if (raised && raisedArchives && !map.getSource('oblique-1')) {
      raisedArchives.forEach((file, i) => {
        const source = `oblique-${i + 1}`
        map.addSource(source, { type: 'vector', url: `pmtiles://${tilesBase}${file}` })
        for (const group of RAISED_GROUPS) {
          for (const layer of group.layers) map.addLayer({ ...layer, id: `${layer.id}-${i + 1}`, source } as LayerSpecification, group.before)
        }
      })
    }
    // The international line is not a base layer (it stays over satellite imagery), but it is raised.
    for (const id of new Set([...BASE_LAYERS, ...NOT_RAISED])) {
      const hidden = (basemap !== 'literary' && BASE_LAYERS.includes(id)) || (raised && NOT_RAISED.has(id))
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', hidden ? 'none' : 'visible')
    }
    for (const layer of map.getStyle().layers) {
      if (layer.id.startsWith('raised-')) map.setLayoutProperty(layer.id, 'visibility', raised ? 'visible' : 'none')
    }
    // Below the raised line work's first zoom the view would be bare paper.
    map.setMinZoom(raised ? RAISED_MIN_ZOOM : MIN_ZOOM)
    // The raised data covers the corridor of the stretches ridden or walked, from zoom 9: from outside it, go to its middle;
    // from too far out, close in where the view is, enough to see the line work.
    const [w, s, e, n] = RAISED_BOUNDS
    const { lng, lat } = map.getCenter()
    const inside = lng >= w && lng <= e && lat >= s && lat <= n
    if (raised && (!inside || map.getZoom() < 11)) {
      map.flyTo({ center: inside ? [lng, lat] : [(w + e) / 2, (s + n) / 2], zoom: Math.max(map.getZoom(), 11.5),
        duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1600 })
    }
  }, [basemap, view, loaded, raisedArchives, mapRef])

  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !loaded) return
    const tilted = view === 'tilted'
    if (tilted && !map.getSource('terrain3d')) {
      // Its own source, as MapLibre recommends, so the hillshade keeps its tiles.
      map.addSource('terrain3d', { type: 'raster-dem', url: `pmtiles://${tilesBase}terrain.pmtiles`, encoding: 'terrarium', tileSize: 256 })
    }
    map.setTerrain(tilted ? { source: 'terrain3d', exaggeration: TERRAIN_EXAGGERATION } : null)
    // Only when the tilt changes: on load this would otherwise cancel the journey's opening fitBounds.
    const pitch = tilted ? TERRAIN_TILT : 0
    if (map.getPitch() !== pitch) {
      map.easeTo({ pitch, duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 800 })
    }
  }, [view, loaded, mapRef])

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
    <div className={`map-area${basemap === 'literary' ? '' : ' has-satellite'}${wash ? ' land-colour' : ''}`}>
      {satelliteStarted && !unavailable && (
        <Suspense fallback={null}>
          <SatelliteMap
            literary={mapRef}
            hidden={basemap === 'literary' && !wash}
            terrain={wash && view === 'tilted' ? TERRAIN_EXAGGERATION : null}
            onUnavailable={onUnavailable}
          />
        </Suspense>
      )}
      {basemap === 'compare' && <ClassicUnderlay main={mapRef} style={underlayStyle} split={split} />}
      <div className="literary">
        <Map
          ref={mapRef}
          mapLib={maplibregl}
          mapStyle={style}
          initialViewState={{ bounds: storyBounds, fitBoundsOptions: { padding: 24 } }}
          minZoom={MIN_ZOOM}
          maxZoom={13}
          dragRotate={false}
          hash="map"
          // Each archive brings its own credit (the terrain lines wherever the hillshade shows); the Credits page has the rest.
          attributionControl={{ compact: true, customAttribution: '<a href="#/credits">Credits</a>' }}
          interactiveLayerIds={['places-point', 'areas-fill']}
          onClick={(e) => {
            const f = e.features?.[0]
            setPicked(f ? { lon: e.lngLat.lng, lat: e.lngLat.lat, props: f.properties as StoryProps } : null)
          }}
          style={{ position: 'absolute', inset: 0 }}
          onLoad={(e) => {
            setLoaded(true)
            // Scripted review (Playwright) drives the map through this handle; only with ?debug.
            if (new URLSearchParams(window.location.search).has('debug')) {
              ;(window as unknown as { __map: unknown }).__map = e.target
            }
          }}
        >
          <NavigationControl position="top-left" showCompass={false} />
          {/* Miles, the book's own unit. */}
          <ScaleControl position="bottom-left" unit="imperial" maxWidth={140} />
          {story && <StoryLayers story={story} stops={stops} stopIndex={stopIndex} onSelectStop={onSelectStop} halo={basemap === 'literary'} />}
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
          aria-label="Compare the classic map and satellite"
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
      <div className="map-switches">
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
              {b === 'literary' ? 'Classic' : b === 'satellite' ? 'Satellite' : 'Compare'}
            </button>
          ))}
        </div>
        <div className="basemap-switch" role="radiogroup" aria-label="View of the classic map">
          {VIEWS.map((v) => (
            <button
              key={v.id}
              type="button"
              role="radio"
              aria-checked={view === v.id}
              disabled={basemap !== 'literary'}
              title={v.title}
              onClick={() => setView(v.id)}
            >
              {v.label}
            </button>
          ))}
        </div>
        <label className="land-colour-toggle" title={view === 'raised' ? 'Not available in the Raised view' : 'Faint satellite colour under the map'}>
          <input
            type="checkbox"
            checked={landColour}
            disabled={basemap !== 'literary' || view === 'raised' || unavailable}
            onChange={(e) => setLandColour(e.target.checked)}
          />
          Land colour
        </label>
      </div>
      {view === 'raised' && (
        <p className="notice" role="status">The Raised view covers the country the journeys ride through; bus rides and reported journeys stay flat.</p>
      )}
      {unavailable && <p className="notice" role="status">Satellite imagery is unavailable right now. The classic map works as normal.</p>}
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
