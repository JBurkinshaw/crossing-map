import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { AttributionControl, Map, NavigationControl, ScaleControl, type MapRef } from '@vis.gl/react-maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Feature, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import VintageUnderlay from './VintageUnderlay'
import { ChunkBoundary } from '../ChunkBoundary'
import { CompareSwipe } from './CompareSwipe'
import { HomeControl } from './HomeControl'
import { LayerKey } from './LayerKey'
import { MapFrame } from './MapFrame'
import { MapControls } from './MapControls'
import type { Basemap, Ground, View } from './mode'
import { OverviewInset } from './OverviewInset'
import { StoryLayers, type Corridor } from './StoryLayers'
import { WaterMarks } from './WaterMarks'
import { contourText, glyphText, LANDCOVER_ARCHIVE, landcoverLayers, OBLIQUE_BOUNDS, OBLIQUE_MIN_ZOOM, obliqueLayers, setVignetteOpacity } from './relief'
import { closeAttribution, dataBase, exposeForScripts, fontsBase, motion, TERRAIN_EXAGGERATION, tilesBase } from './setup'
import { baseLayerIds, literaryStyle, notObliqueIds } from './style'
import { inkPatterns, RATIO as INK_RATIO } from './landcoverInk'
import { palette, storyBounds } from './tokens'
import { layerFilterUpTo, PROGRESS_LAYERS, styleUpTo } from '../spoiler/filter'
import type { MapPick } from '../story/select'
import type { Units } from '../units'
import { usePhone } from '../panel/usePhone'

// Loaded only when the reader first leaves the literary basemap.
const SatelliteMap = lazy(() => import('./SatelliteMap'))

const MIN_ZOOM = 4
const TERRAIN_TILT = 50

// The units only change label text, which MapView sets on the map when they change; every derived list below
// comes from one build of the style.
const literary = (units: Units) => literaryStyle(tilesBase, fontsBase, dataBase, units)
const LITERARY = literary('metric')
const BASE_LAYERS = new Set(baseLayerIds(LITERARY))
const NOT_OBLIQUE = new Set(notObliqueIds(LITERARY))
const OBLIQUE_GROUPS = obliqueLayers(LITERARY.layers, palette)
// The base filters of the layers spoiler mode narrows (spoiler/filter.ts), before the reading-progress clause.
const BASE_FILTERS = Object.fromEntries(LITERARY.layers
  .filter((l) => l.id in PROGRESS_LAYERS).map((l) => [l.id, 'filter' in l ? l.filter : undefined]))

// The layers a click can pick, and which story layer each draws.
const CLICKABLE: Record<string, MapPick['layer']> = { 'places-point': 'places', 'zone-places-point': 'places', 'areas-fill': 'areas', 'journeys-hit': 'journeys' }

type Props = {
  mapRef: RefObject<MapRef | null>
  // In the Oblique view, the oblique copies of the story layers (App swaps them in).
  story: Story | null
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  onSelectStop: (index: number) => void
  // A click on the map: the story features under it, topmost first (none: a click on empty map), and where it
  // fell. App decides what it opens. selectedId is the place or area now picked, outlined.
  onMapClick: (picks: MapPick[], at: [number, number]) => void
  selectedId: string | null
  // In step-through, the current stop's sequence: the road ahead of it fades.
  aheadFrom: number | null
  // The Home button: back to the whole journey in focus.
  onHome: () => void
  // The basemap and the view in force (map/mode.ts); App owns them.
  basemap: Basemap
  onBasemap: (basemap: Basemap) => void
  view: View
  onView: (view: View) => void
  // The latest episode whose features may show (spoiler mode); the story layers arrive already filtered.
  reached: string
  // The oblique copies of the story layers could not be loaded.
  obliqueFailed: boolean
  // Talk on the road: the route segment to outline as a corridor, with its label.
  corridor: Corridor | null
  // Miles and feet, or kilometres and metres: the scale bar, and heights on summits, passes and contours.
  units: Units
  onUnits: (units: Units) => void
}

export function MapView(props: Props) {
  const { mapRef, story, stops, stopIndex, onSelectStop, onMapClick, selectedId, aheadFrom, onHome, reached } = props
  const { basemap, onBasemap, view, onView, obliqueFailed, corridor, units, onUnits } = props
  // Built once with the progress and units at first render; later changes go through setFilter and
  // setLayoutProperty below.
  const [style] = useState(() => styleUpTo(literary(units), reached))
  // Compare mode's vintage underlay gets its own copy: a map may change the style object it is given.
  const underlayStyle = useMemo<StyleSpecification | null>(
    () => (basemap === 'compare' ? styleUpTo(literary('metric'), reached) : null),
    [basemap, reached],
  )
  const [unavailable, setUnavailable] = useState(false)
  // Once created, the satellite map stays (hidden on the literary basemap): MapTiler counts each new map as a session.
  const [satelliteStarted, setSatelliteStarted] = useState(false)
  // The ground of the vintage map: plain paper, land cover (decision 0040) in every view, or the satellite tint,
  // the satellite map faded under the literary map in the Flat and Tilted views. The Oblique view's line work is
  // shifted north, so imagery would not line up under it; its land cover is shifted with it.
  const [ground, setGround] = useState<Ground>('paper')
  // The Map menu and the open layer key share the map's right-hand side, and on desktop the menu would cover the
  // top of the key: opening one closes the other.
  const [opened, setOpened] = useState<'menu' | 'key' | null>(null)
  const onMenuOpen = useCallback((open: boolean) => setOpened((o) => (open ? 'menu' : o === 'menu' ? null : o)), [])
  const onKeyOpen = useCallback((open: boolean) => setOpened((o) => (open ? 'key' : o === 'key' ? null : o)), [])
  const tintAvailable = basemap === 'literary' && view !== 'oblique' && !unavailable
  const landcoverAvailable = basemap === 'literary'
  const wash = ground === 'tint' && tintAvailable
  const landcover = ground === 'landcover' && landcoverAvailable
  const phone = usePhone()
  // The Wheeler frame and its graticule labels, on the vintage map in the Flat and Tilted views (MapFrame).
  const framed = basemap === 'literary' && view !== 'oblique'
  if ((basemap !== 'literary' || wash) && !satelliteStarted) setSatelliteStarted(true)
  // Set once the style first loads. map.isStyleLoaded() is not a substitute: it is false again whenever
  // tiles are loading, and 'load' fires only once.
  const [loaded, setLoaded] = useState(false)
  const [hovering, setHovering] = useState(false)
  // The Oblique view's archives, fetched the first time the reader turns it on; 'failed' if the list is missing.
  const [obliqueArchives, setObliqueArchives] = useState<string[] | 'failed' | null>(null)
  // Which copy of the drawings the vignettes source holds: the style loads the flat one.
  const vignettesShown = useRef(`${dataBase}vignettes.geojson`)
  useEffect(() => {
    if (view !== 'oblique' || obliqueArchives) return
    fetch(`${dataBase}oblique/archives.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`oblique/archives.json: HTTP ${r.status}`)
        return r.json()
      })
      .then(setObliqueArchives, (e: unknown) => {
        console.error('Oblique view failed to load:', e)
        setObliqueArchives('failed')
      })
  }, [view, obliqueArchives])

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

  // The drawings of the journey in focus at full strength, the others lighter.
  const journey = stops[0]?.properties.journey ?? ''
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !loaded) return
    setVignetteOpacity(map, journey)
  }, [journey, loaded, mapRef])

  const onUnavailable = useCallback(() => {
    setUnavailable(true)
    onBasemap('literary')
  }, [onBasemap])

  // In satellite and compare modes the literary paper and base layers hide, so the story layers draw over the
  // imagery (in compare mode, VintageUnderlay draws the vintage base left of the swipe);
  // in the Oblique view the base layers that cannot move with the terrain hide, and the oblique line work shows.
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !loaded) return
    const oblique = view === 'oblique'
    // The oblique line work comes in several archives (each under 100 MB), listed in data/oblique/archives.json;
    // every oblique layer is drawn once per archive.
    if (oblique && Array.isArray(obliqueArchives) && !map.getSource('oblique-1')) {
      obliqueArchives.forEach((file, i) => {
        const source = `oblique-${i + 1}`
        map.addSource(source, { type: 'vector', url: `pmtiles://${tilesBase}${file}` })
        for (const group of OBLIQUE_GROUPS) {
          for (const layer of group.layers) map.addLayer({ ...layer, id: `${layer.id}-${i + 1}`, source } as LayerSpecification, group.before)
        }
      })
    }
    // The drawings follow the story points north in the Oblique view: their source swaps to the oblique copy.
    const vignettes = map.getSource('vignettes') as GeoJSONSource | undefined
    const vignetteData = `${dataBase}${oblique ? 'oblique/' : ''}vignettes.geojson`
    if (vignettes && vignettesShown.current !== vignetteData) {
      vignettes.setData(vignetteData)
      vignettesShown.current = vignetteData
    }
    for (const id of new Set([...BASE_LAYERS, ...NOT_OBLIQUE])) {
      const hidden = (basemap !== 'literary' && BASE_LAYERS.has(id)) || (oblique && NOT_OBLIQUE.has(id))
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', hidden ? 'none' : 'visible')
    }
    // The land cover's ink textures (decision 0042), drawn and added the first time the reader asks for land cover.
    if (landcover && !map.hasImage('ink-scrub')) {
      for (const { id, image } of inkPatterns(palette.ink, palette.water)) map.addImage(id, image, { pixelRatio: INK_RATIO })
    }
    // The land cover on the ground, added the first time the reader asks for it: colour under the hillshade, ink over it.
    if (landcover && !oblique && !map.getSource('landcover')) {
      map.addSource('landcover', { type: 'vector', url: `pmtiles://${tilesBase}${LANDCOVER_ARCHIVE}` })
      for (const { before, layer } of landcoverLayers(palette)) map.addLayer(layer, before)
    }
    for (const id of ['landcover', 'landcover-ink']) {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', landcover && !oblique ? 'visible' : 'none')
    }
    for (const layer of map.getStyle().layers) {
      if (!layer.id.startsWith('oblique-')) continue
      const shown = oblique && (landcover || !layer.id.startsWith('oblique-landcover'))
      map.setLayoutProperty(layer.id, 'visibility', shown ? 'visible' : 'none')
    }
  }, [basemap, view, loaded, obliqueArchives, landcover, mapRef])

  // Only when the view changes, so changing the ground does not move the map.
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !loaded) return
    const oblique = view === 'oblique'
    // Below the oblique line work's first zoom the view would be bare paper.
    map.setMinZoom(oblique ? OBLIQUE_MIN_ZOOM : MIN_ZOOM)
    // The oblique data covers the corridor of the stretches ridden or walked, from zoom 9: from outside it, go to its middle;
    // from too far out, close in where the view is, enough to see the line work.
    const [w, s, e, n] = OBLIQUE_BOUNDS
    const { lng, lat } = map.getCenter()
    const inside = lng >= w && lng <= e && lat >= s && lat <= n
    if (oblique && (!inside || map.getZoom() < 11)) {
      map.flyTo({ center: inside ? [lng, lat] : [(w + e) / 2, (s + n) / 2], zoom: Math.max(map.getZoom(), 11.5), duration: motion(1600) })
    }
  }, [view, loaded, mapRef])

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
    if (map.getPitch() !== pitch) map.easeTo({ pitch, duration: motion(800) })
  }, [view, loaded, mapRef])

  return (
    <div className={`map-area${basemap === 'literary' ? '' : ' has-satellite'}${wash ? ' satellite-tint' : ''}${framed ? ' framed' : ''}`}>
      {satelliteStarted && !unavailable && (
        <ChunkBoundary onError={onUnavailable}>
          <Suspense fallback={null}>
            <SatelliteMap
              literary={mapRef}
              hidden={basemap === 'literary' && !wash}
              topo={basemap === 'topo'}
              terrain={(wash || basemap === 'compare') && view === 'tilted' ? TERRAIN_EXAGGERATION : null}
              onUnavailable={onUnavailable}
            />
          </Suspense>
        </ChunkBoundary>
      )}
      {underlayStyle && (
        <VintageUnderlay
          main={mapRef}
          style={underlayStyle}
          journey={journey}
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
          interactiveLayerIds={Object.keys(CLICKABLE)}
          onClick={(e) => {
            const picks = (e.features ?? []).map((f) => {
              const p = f.properties as StoryProps
              return { layer: CLICKABLE[f.layer.id], id: p.id, journey: p.journey ?? null, sequence: p.sequence ?? null }
            })
            onMapClick(picks, [e.lngLat.lng, e.lngLat.lat])
          }}
          // A pointer over what a click would open.
          cursor={hovering ? 'pointer' : undefined}
          onMouseEnter={() => setHovering(true)}
          onMouseLeave={() => setHovering(false)}
          style={{ position: 'absolute', inset: 0 }}
          onLoad={(e) => {
            setLoaded(true)
            closeAttribution(e.target)
            exposeForScripts('__map', e.target)
          }}
        >
          <NavigationControl position="top-left" showCompass={false} />
          <HomeControl onHome={onHome} />
          {/* Narrower on phones, where a 140 px bar covered the stops framed near the map's bottom edge. */}
          <ScaleControl position="bottom-left" unit={units} maxWidth={phone ? 72 : 140} />
          {/* Added after the scale, so MapLibre stacks it above. Each archive brings its own credit (the terrain
              lines wherever the hillshade shows); the Credits page has the rest. */}
          <AttributionControl position="bottom-left" compact customAttribution='<a href="#/credits">Credits</a>' />
          <WaterMarks palette={palette} />
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
              lineLabels={basemap === 'literary' && view !== 'oblique'}
            />
          )}
        </Map>
      </div>
      {basemap === 'compare' && <CompareSwipe />}
      {loaded && <MapFrame mapRef={mapRef} shown={framed} />}
      <MapControls
        basemap={basemap}
        onBasemap={onBasemap}
        unavailable={unavailable}
        view={view}
        onView={onView}
        ground={ground}
        tintAvailable={tintAvailable}
        landcoverAvailable={landcoverAvailable}
        onGround={setGround}
        units={units}
        onUnits={onUnits}
        menuOpen={opened === 'menu'}
        onMenuOpen={onMenuOpen}
      />
      {/* Not on phones: the inset would cover a fifth of a small map, and the Home button already brings back the whole journey. */}
      {loaded && view !== 'oblique' && !phone && <OverviewInset mapRef={mapRef} story={story} journey={stops[0]?.properties.journey ?? ''} />}
      {view === 'oblique' && (
        <p className="notice" role="status">
          {obliqueArchives === 'failed' || obliqueFailed
            ? 'The Oblique view could not be loaded. Try reloading the page, or switch back to Flat.'
            : 'The Oblique view covers the country the journeys ride through; bus rides and reported journeys stay flat.'}
        </p>
      )}
      {unavailable && <p className="notice" role="status">Satellite and Topo are unavailable right now. The vintage map works as normal.</p>}
      {/* The title cartouche holds the layer key, folded. The title itself is decoration: the page's heading
          names the map for screen readers. The key describes the vintage map, so it shows with it. */}
      <div className="cartouche">
        <div className="cartouche-head" aria-hidden="true">
          <svg className="north" viewBox="0 0 24 48" width="14" height="28">
            <path d="M12 2 L18 30 L12 24 L6 30 Z" fill="currentColor" />
            <text x="12" y="45" textAnchor="middle" fontSize="12">N</text>
          </svg>
          <div>
            <div className="cartouche-title">The Crossing</div>
            <div className="cartouche-sub">Sonora, Chihuahua &amp; the New Mexico bootheel</div>
          </div>
        </div>
        {(basemap === 'literary' || basemap === 'compare') && (
          <LayerKey story={story} journey={stops[0]?.properties.journey ?? ''} reached={reached} units={units} phone={phone} open={opened === 'key'} onOpen={onKeyOpen} landcover={landcover} />
        )}
      </div>
    </div>
  )
}
