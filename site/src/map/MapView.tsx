import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { IControl, LayerSpecification } from 'maplibre-gl'
import { AttributionControl, Map, NavigationControl, ScaleControl, useControl, type MapRef } from '@vis.gl/react-maplibre'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { Feature, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import ClassicUnderlay from './ClassicUnderlay'
import { LayerKey } from './LayerKey'
import { OverviewInset } from './OverviewInset'
import { StoryLayers, type Corridor } from './StoryLayers'
import { contourText, glyphText, RAISED_BOUNDS, RAISED_MIN_ZOOM, raisedLayers } from './relief'
import { BASE_LAYERS, literaryStyle } from './style'
import { palette, storyBounds } from './tokens'
import { layerFilterUpTo, PROGRESS_LAYERS, styleUpTo } from '../spoiler/filter'
import type { Units } from '../units'
import { usePhone } from '../panel/usePhone'

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
const NOT_RAISED = new Set(['mexico', 'relief-tint', 'hillshade', 'contour', 'contour-label', 'hachure-coarse', 'hachure-coarse-copy',
  'hachure-fine', 'hachure-fine-copy', 'hachure-dense', 'hachure-dense-copy', 'mountain-glyph', 'county-line', 'state-line', 'country-line', 'creek',
  'river-minor', 'river', 'creek-label', 'river-label', 'road', 'railroad', 'railroad-ties', 'vignette-leader', 'vignette'])
// The units only change label text, which MapView sets on the map when they change.
const literary = (units: Units = 'metric') => literaryStyle(tilesBase, fontsBase, dataBase, units)
const RAISED_GROUPS = raisedLayers(literary().layers, palette)

type Basemap = 'literary' | 'satellite' | 'topo' | 'compare'
// Compare sits between the two maps it compares, as a narrow button with a split-frame icon.
const COMPARE_ICON = (
  <svg viewBox="0 0 18 14" width="18" height="14" aria-hidden="true">
    <rect x="1" y="1" width="16" height="12" fill="none" stroke="currentColor" strokeWidth="1.3" />
    <rect x="1" y="1" width="8" height="12" fill="currentColor" opacity="0.45" />
    <line x1="9" y1="0" x2="9" y2="14" stroke="currentColor" strokeWidth="1.6" />
  </svg>
)
const BASEMAPS: { id: Basemap; label: ReactNode; title?: string; ariaLabel?: string; narrow?: boolean }[] = [
  { id: 'literary', label: 'Classic' },
  {
    id: 'compare',
    label: COMPARE_ICON,
    title: 'Compare: the classic map and satellite, side by side',
    ariaLabel: 'Compare the classic map and satellite, side by side',
    narrow: true,
  },
  { id: 'satellite', label: 'Satellite' },
  { id: 'topo', label: 'Topo', title: 'MapTiler Topo: roads, places and contours of today' },
]
// In compare mode the two maps it compares show as paired, in a lighter way than the switch that is on.
const PAIRED: Basemap[] = ['literary', 'satellite']
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
  // A place or area picked on the map (null: a click on empty map), and the one now picked, outlined.
  onSelectFeature: (pick: { layer: 'places' | 'areas'; id: string } | null) => void
  selectedId: string | null
  // In step-through, the current stop's sequence: the road ahead of it fades.
  aheadFrom: number | null
  // The Home button: back to the whole journey in focus.
  onHome: () => void
  onView: (view: View) => void
  // The latest episode whose features may show (spoiler mode); the story layers arrive already filtered.
  reached: string
  // Talk on the road: the route segment to outline as a corridor, with its label.
  corridor: Corridor | null
  // Miles and feet, or kilometres and metres: the scale bar, and heights on summits, passes and contours.
  units: Units
  onUnits: (units: Units) => void
}

// A row of switches, one of which is on: a radio group, one tab stop, with the arrow keys moving the choice.
function Switch<T extends string>(props: {
  label: string
  // ariaLabel spells out what a short label means; it starts with the label, so speech input can use the label.
  // A narrow option holds an icon; a paired one shows as half chosen (the two maps compare mode shows).
  options: { id: T; label: ReactNode; title?: string; ariaLabel?: string; disabled: boolean; narrow?: boolean; paired?: boolean }[]
  value: T
  onChange: (value: T) => void
}) {
  const { label, options, value, onChange } = props
  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const by = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
    if (!by) return
    e.preventDefault()
    const enabled = options.filter((o) => !o.disabled)
    const next = enabled[(enabled.findIndex((o) => o.id === value) + by + enabled.length) % enabled.length]
    if (!next) return
    onChange(next.id)
    e.currentTarget.querySelector<HTMLButtonElement>(`[data-id="${next.id}"]`)?.focus()
  }
  return (
    <div className="basemap-switch" role="radiogroup" aria-label={label} onKeyDown={onKeyDown}>
      {options.map((o) => (
        <button
          key={o.id}
          type="button"
          role="radio"
          data-id={o.id}
          data-narrow={o.narrow || undefined}
          data-paired={o.paired || undefined}
          aria-checked={value === o.id}
          tabIndex={value === o.id ? 0 : -1}
          disabled={o.disabled}
          title={o.title}
          aria-label={o.ariaLabel}
          onClick={() => onChange(o.id)}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

// The base filters of the layers spoiler mode narrows (spoiler/filter.ts), before the reading-progress clause.
const BASE_FILTERS = Object.fromEntries(literary().layers
  .filter((l) => l.id in PROGRESS_LAYERS).map((l) => [l.id, 'filter' in l ? l.filter : undefined]))

// The Home button (plan section 9), under the zoom buttons: it frames the whole journey in focus. A house says
// "home page" to many readers, so the icon is a frame around a winding route, and the title names the action.
class HomeButton implements IControl {
  private box = document.createElement('div')
  constructor(onClick: () => void) {
    this.box.className = 'maplibregl-ctrl maplibregl-ctrl-group'
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'home-button'
    button.title = 'Show the whole journey'
    button.setAttribute('aria-label', 'Show the whole journey')
    button.innerHTML =
      '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor">' +
      '<path d="M2.5 7 V2.5 H7 M13 2.5 H17.5 V7 M17.5 13 V17.5 H13 M7 17.5 H2.5 V13" stroke-width="1.6"/>' +
      '<path d="M6 14 C8 12 7 9 10 8.5 S12.5 6 14 6" stroke-width="1.4" stroke-dasharray="2.2 1.4"/></svg>'
    button.addEventListener('click', onClick)
    this.box.append(button)
  }
  onAdd() {
    return this.box
  }
  onRemove() {
    this.box.remove()
  }
}

function HomeControl({ onHome }: { onHome: () => void }) {
  // The control is made once; the ref keeps its click on the latest handler.
  const latest = useRef(onHome)
  useEffect(() => {
    latest.current = onHome
  })
  useControl(() => new HomeButton(() => latest.current()), { position: 'top-left' })
  return null
}

export function MapView(props: Props) {
  const { mapRef, story, stops, stopIndex, onSelectStop, onSelectFeature, selectedId, aheadFrom, onHome, onView, reached } = props
  const { corridor, units, onUnits } = props
  const [basemap, setBasemap] = useState<Basemap>('literary')
  // Built once with the progress and units at first render; later changes go through setFilter and
  // setLayoutProperty below.
  const [style] = useState(() => styleUpTo(literary(units), reached))
  // Compare mode's classic underlay gets its own copy: a map may change the style object it is given.
  const underlayStyle = useMemo(() => styleUpTo(literary(), reached), [reached])
  const [unavailable, setUnavailable] = useState(false)
  // Once created, the satellite map stays (hidden on the literary basemap): MapTiler counts each new map as a session.
  const [satelliteStarted, setSatelliteStarted] = useState(false)
  // Compare mode: the classic base shows left of this split, in percent of the width.
  const [split, setSplit] = useState(50)
  // The views apply to the classic basemap, and Flat and Tilted to compare mode too (the Raised view's line work
  // is shifted north, so it would not line up with the imagery); satellite and topo are always flat.
  const [chosenView, setView] = useState<View>('flat')
  const view: View = basemap === 'literary' || (basemap === 'compare' && chosenView !== 'raised') ? chosenView : 'flat'
  // Compare from the Raised view keeps the relief standing up, as Tilted.
  const chooseBasemap = (next: Basemap) => {
    if (next === 'compare' && chosenView === 'raised') setView('tilted')
    setBasemap(next)
  }
  // Satellite tint: the satellite map, faded, under the literary map in the Flat and Tilted views. The Raised
  // view's line work is shifted north, so imagery would not line up under it.
  const [tint, setTint] = useState(false)
  const tintAvailable = basemap === 'literary' && view !== 'raised' && !unavailable
  const wash = tint && tintAvailable
  // Phones: the map's switches fold into one Map button, so they do not cover the map.
  const phone = usePhone()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuBox = useRef<HTMLDivElement>(null)
  const menuButton = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!phone || !menuOpen) return
    // A tap outside the menu closes it, as a tap on the map would otherwise leave it covering the map.
    const outside = (e: PointerEvent) => {
      if (!menuBox.current?.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [phone, menuOpen])
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

  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !loaded) return
    for (const [id, base] of Object.entries(BASE_FILTERS)) {
      if (map.getLayer(id)) map.setFilter(id, layerFilterUpTo(id, base, reached))
    }
  }, [reached, loaded, mapRef])

  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !loaded) return
    map.setLayoutProperty('mountain-glyph', 'text-field', glyphText(units))
    map.setLayoutProperty('contour-label', 'text-field', contourText(units))
  }, [units, loaded, mapRef])

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
    <div className={`map-area${basemap === 'literary' ? '' : ' has-satellite'}${wash ? ' satellite-tint' : ''}`}>
      {satelliteStarted && !unavailable && (
        <Suspense fallback={null}>
          <SatelliteMap
            literary={mapRef}
            hidden={basemap === 'literary' && !wash}
            topo={basemap === 'topo'}
            terrain={(wash || basemap === 'compare') && view === 'tilted' ? TERRAIN_EXAGGERATION : null}
            onUnavailable={onUnavailable}
          />
        </Suspense>
      )}
      {basemap === 'compare' && (
        <ClassicUnderlay
          main={mapRef}
          style={underlayStyle}
          split={split}
          units={units}
          terrain={view === 'tilted' ? { url: `pmtiles://${tilesBase}terrain.pmtiles`, exaggeration: TERRAIN_EXAGGERATION } : null}
        />
      )}
      <div className="literary">
        <Map
          ref={mapRef}
          mapLib={maplibregl}
          mapStyle={style}
          initialViewState={{ bounds: storyBounds, fitBoundsOptions: { padding: 24 } }}
          minZoom={MIN_ZOOM}
          maxZoom={13}
          dragRotate={false}
          // The map's own keyboard handler pans and zooms once the map has focus; its name says so.
          locale={{ 'Map.Title': 'Map. Arrow keys pan, plus and minus zoom', 'AttributionControl.ToggleAttribution': 'Show or hide the map credits' }}
          hash="map"
          attributionControl={false}
          interactiveLayerIds={['places-point', 'zone-places-point', 'areas-fill']}
          onClick={(e) => {
            const f = e.features?.[0]
            onSelectFeature(f ? { layer: f.layer.id === 'areas-fill' ? 'areas' : 'places', id: (f.properties as StoryProps).id } : null)
          }}
          style={{ position: 'absolute', inset: 0 }}
          onLoad={(e) => {
            setLoaded(true)
            // MapLibre opens the compact attribution at first; it starts closed, behind its (i) button. The
            // archives' credits arrive with their first tiles.
            const close = () => e.target.getContainer().querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show')
            close()
            e.target.once('idle', close)
            // Scripted review (Playwright) drives the map through this handle; only with ?debug.
            if (new URLSearchParams(window.location.search).has('debug')) {
              ;(window as unknown as { __map: unknown }).__map = e.target
            }
          }}
        >
          <NavigationControl position="top-left" showCompass={false} />
          <HomeControl onHome={onHome} />
          <ScaleControl position="bottom-left" unit={units} maxWidth={140} />
          {/* Added after the scale, so MapLibre stacks it above. Each archive brings its own credit (the terrain
              lines wherever the hillshade shows); the Credits page has the rest. */}
          <AttributionControl position="bottom-left" compact customAttribution='<a href="#/credits">Credits</a>' />
          {story && (
            <StoryLayers
              story={story}
              stops={stops}
              stopIndex={stopIndex}
              onSelectStop={onSelectStop}
              halo={basemap === 'literary'}
              selectedId={selectedId}
              aheadFrom={aheadFrom}
              corridor={corridor}
            />
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
      <div className="map-controls-box" ref={menuBox} onKeyDown={(e) => {
        if (phone && menuOpen && e.key === 'Escape') {
          setMenuOpen(false)
          menuButton.current?.focus()
        }
      }}>
        {phone && (
          <button
            ref={menuButton}
            type="button"
            className="map-menu-button"
            aria-expanded={menuOpen}
            aria-controls="map-controls"
            aria-label="Map options"
            onClick={() => setMenuOpen((o) => !o)}
          >
            <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.4">
              <path d="M10 3 L18 7 L10 11 L2 7 Z" />
              <path d="M2 10.5 L10 14.5 L18 10.5" />
              <path d="M2 14 L10 18 L18 14" />
            </svg>
            Map
          </button>
        )}
        {/* One family of switches. View and Ground hang under the basemap switch, ruled off with it, because
            they change the classic map (and View the compare mode); on Satellite and Topo they fade out. */}
        <div className="map-controls" id="map-controls" hidden={phone && !menuOpen}>
          <div className="control-row">
            <span className="control-label" aria-hidden="true">Map</span>
            <Switch
              label="Map"
              options={BASEMAPS.map((b) => ({ ...b, disabled: b.id !== 'literary' && unavailable, paired: basemap === 'compare' && PAIRED.includes(b.id) }))}
              value={basemap}
              onChange={chooseBasemap}
            />
          </div>
          <div className="control-sub" data-off={basemap === 'satellite' || basemap === 'topo' || undefined}>
            <div className="control-row">
              <span className="control-label" aria-hidden="true">View</span>
              <Switch
                label="View of the classic map"
                options={VIEWS.map((v) => ({ ...v, disabled: !(basemap === 'literary' || (basemap === 'compare' && v.id !== 'raised')) }))}
                value={view}
                onChange={setView}
              />
            </div>
            <div className="control-row">
              <span className="control-label" aria-hidden="true">Ground</span>
              <Switch
                label="Ground of the classic map"
                options={[
                  { id: 'paper', label: 'Paper', title: 'The paper colour of the map', disabled: !tintAvailable },
                  {
                    id: 'tint',
                    label: 'Satellite tint',
                    title: tintAvailable ? 'Faint colour from satellite imagery under the map' : 'Classic map in Flat or Tilted only',
                    disabled: !tintAvailable,
                  },
                ]}
                value={tint ? 'tint' : 'paper'}
                onChange={(v) => setTint(v === 'tint')}
              />
            </div>
          </div>
          <div className="control-row">
            <span className="control-label" aria-hidden="true">Units</span>
            <Switch
              label="Units"
              options={[
                { id: 'imperial', label: 'Imperial', title: 'Miles and feet', ariaLabel: 'Imperial: miles and feet', disabled: false },
                { id: 'metric', label: 'Metric', title: 'Kilometres and metres', ariaLabel: 'Metric: kilometres and metres', disabled: false },
              ]}
              value={units}
              onChange={onUnits}
            />
          </div>
        </div>
      </div>
      {basemap === 'literary' && <LayerKey story={story} journey={stops[0]?.properties.journey ?? ''} reached={reached} />}
      {loaded && view !== 'raised' && <OverviewInset mapRef={mapRef} story={story} journey={stops[0]?.properties.journey ?? ''} />}
      {view === 'raised' && (
        <p className="notice" role="status">The Raised view covers the country the journeys ride through; bus rides and reported journeys stay flat.</p>
      )}
      {unavailable && <p className="notice" role="status">Satellite and Topo are unavailable right now. The classic map works as normal.</p>}
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
