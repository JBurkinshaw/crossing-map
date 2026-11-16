import { useEffect, useMemo } from 'react'
import { Layer, Marker, Source, useMap } from '@vis.gl/react-maplibre'
import type { CircleLayerSpecification, ExpressionSpecification } from 'maplibre-gl'
import type { Feature, FeatureCollection, Geometry, Point } from 'geojson'
import { useJson } from '../data/json'
import type { Story, StoryProps } from '../data/story'
import { CLUSTER_MAX_ZOOM, CLUSTER_PROPERTIES, CLUSTER_RADIUS, clusterDetail, clusterWord, expandCluster, inZone, useZoneClusters, ZONE_CLUSTERS, ZONE_SOURCE, ZONE_STOPS } from './cluster'
import { corridor, midpoint } from './corridor'
import { pinsApart } from '../story/select'
import { prefersReducedMotion } from './setup'
import { dashInWidths, fonts, journeyInks, OUT_OF_FOCUS_WIDTH, palette as tokens, QUIET_OPACITY, routeLines, typeScale } from './tokens'

// Talk on the road: the route segment a picked line was spoken on, and its label ("on the road between X and Y").
export type Corridor = { segment: Feature<Geometry, StoryProps>; label: string }

type Props = {
  story: Story
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  onSelectStop: (index: number) => void
  // A wide band of paper under the journey in focus, which clears the relief around it. Off over satellite imagery.
  halo: boolean
  // The place or area picked on the map or in search, outlined.
  selectedId: string | null
  // In step-through, the sequence of the current stop: the road from there on fades (data dimming, design 9).
  aheadFrom: number | null
  // The corridor to outline, when the line picked was spoken on the road.
  corridor: Corridor | null
  // The classic map letters ranges and valleys along their axis (relief.ts, landform-label); their point labels
  // then step aside. Off where the base map is hidden or replaced (satellite, the Raised view).
  lineLabels: boolean
}

// The type scale (tokens.ts; decision 0027): towns in roman at about 1.4 times the spot height, the cities in
// capitals; ranches and springs in small quiet italic. Both grow a little with zoom, as the base map's names do.
const TOWNS = ['town', 'city', 'locale']
const QUIET = ['ranch', 'spring']
const placeSize = (k: number): ExpressionSpecification =>
  ['match', ['get', 'kind'], ['range', 'valley'], 14, TOWNS, typeScale.town * k, QUIET, typeScale.quiet * k,
    ['match', ['get', 'role'], 'stop', 13.5, 12.5]] as unknown as ExpressionSpecification

// The tale places' diamond, drawn once into the map's images: paper inside an ink edge, 11 px across.
const TALE_ICON = 'tale-diamond'
function taleDiamond(): ImageData {
  const size = 24
  const ctx = document.createElement('canvas').getContext('2d')!
  ctx.canvas.width = ctx.canvas.height = size
  ctx.beginPath()
  ctx.moveTo(size / 2, 1.5)
  ctx.lineTo(size - 1.5, size / 2)
  ctx.lineTo(size / 2, size - 1.5)
  ctx.lineTo(1.5, size / 2)
  ctx.closePath()
  ctx.fillStyle = tokens.paper
  ctx.fill()
  ctx.lineWidth = 2.6
  ctx.strokeStyle = tokens.ink
  ctx.stroke()
  return ctx.getImageData(0, 0, size, size)
}

export function StoryLayers({ story, stops, stopIndex, onSelectStop, halo, selectedId, aheadFrom, corridor: road, lineLabels }: Props) {
  const { current: mapRef } = useMap()
  const landforms = useJson<FeatureCollection>('map/landforms.geojson', lineLabels)
  const lined = useMemo(
    () => (lineLabels ? (landforms.data?.features ?? []).map((f) => f.properties?.place_ref).filter((id): id is string => !!id) : []),
    [landforms.data, lineLabels],
  )
  // The places and the journey's stops around Cloverdale and the Peloncillos go to the clustered source; the
  // current stop stays out of it, so the stop being read always shows.
  // Pins that stand apart from their stops are marked `apart`: drawn by a layer a click passes through.
  const current = stops[stopIndex]?.properties.id
  const places = useMemo(() => {
    const apart = pinsApart(story)
    const marked = story.places.features.map((f) => (apart.has(f.properties.id) ? { ...f, properties: { ...f.properties, apart: true } } : f))
    const outside: FeatureCollection<Point, StoryProps> = { ...story.places, features: marked.filter((f) => !inZone(f.geometry.coordinates)) }
    const zone: FeatureCollection<Point> = {
      type: 'FeatureCollection',
      features: [
        ...marked.filter((f) => inZone(f.geometry.coordinates)).map((f) => ({ ...f, properties: { ...f.properties, cat: 'place' } })),
        ...stops
          .filter((f) => f.properties.id !== current && inZone(f.geometry.coordinates))
          .map((f) => ({ ...f, properties: { id: f.properties.id, first_seen: f.properties.first_seen, cat: 'stop' } })),
      ],
    }
    return { outside, zone }
  }, [story, stops, current])
  useEffect(() => {
    const map = mapRef?.getMap()
    if (map && !map.hasImage(TALE_ICON)) map.addImage(TALE_ICON, taleDiamond(), { pixelRatio: 2 })
  }, [mapRef])
  // The vignettes' captions (relief.ts) belong to the base style, under these layers; moved to the top, they are
  // placed before every other label, so the other labels make room for them. The story layers above are added
  // first: a child's effects run before its parent's.
  useEffect(() => {
    const map = mapRef?.getMap()
    if (map?.getLayer('vignette-label')) map.moveLayer('vignette-label')
  }, [mapRef, story])
  const zoneIds = useMemo(() => places.zone.features.map((f) => String(f.properties?.id)), [places.zone])
  // The journey's stops grouped by spot (to about 100 m), in order: a journey that comes back to a place, such as
  // J4 to San Diego, gets one badge there instead of markers drawn over each other.
  const stopGroups = useMemo(() => {
    const groups = new Map<string, number[]>()
    stops.forEach((f, i) => {
      const key = f.geometry.coordinates.map((c) => c.toFixed(3)).join(',')
      groups.set(key, [...(groups.get(key) ?? []), i])
    })
    return [...groups.values()]
  }, [stops])
  const clusters = useZoneClusters(zoneIds)
  const corridorData = useMemo((): FeatureCollection | null => {
    if (!road) return null
    const area = corridor(road.segment.geometry)
    const at = midpoint(road.segment.geometry)
    if (!area || !at) return null
    const properties = { id: road.segment.properties.id, first_seen: road.segment.properties.first_seen, label: road.label }
    return {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', geometry: area, properties: { ...properties, part: 'area' } },
        { type: 'Feature', geometry: { type: 'Point', coordinates: at }, properties: { ...properties, part: 'label' } },
      ],
    }
  }, [road])

  // A place whose name the map sets along its landform's axis, or across its pass (relief.ts, pass-label), has no
  // point label while those show, unless its pin stands apart from its stops; a city's name is in capitals.
  const apart: ExpressionSpecification = ['boolean', ['get', 'apart'], false]
  const nameUnlessLined: ExpressionSpecification = ['case',
    ['all', ['!', apart], ['in', ['get', 'id'], ['literal', lined]]], '',
    ['all', ['boolean', lineLabels], ['==', ['get', 'kind'], 'pass']], '',
    ['==', ['get', 'kind'], 'city'], ['upcase', ['get', 'name']],
    ['get', 'name']]
  const journeyInk = journeyInks(tokens)
  const inkByJourney = ['match', ['get', 'journey'], ...Object.entries(journeyInk).flat(), tokens.ink] as unknown as ExpressionSpecification
  const journey = stops[0]?.properties.journey ?? ''
  const inFocus: ExpressionSpecification = ['==', ['get', 'journey'], journey]
  const selected: ExpressionSpecification = ['==', ['get', 'id'], selectedId ?? '']
  // A segment joins stop `sequence` to the next, so the road ahead starts at the current stop's sequence.
  const ahead: ExpressionSpecification =
    aheadFrom === null ? ['boolean', false] : ['all', inFocus, ['>=', ['coalesce', ['get', 'sequence'], 9999], aheadFrom]]
  const routeOpacity: ExpressionSpecification = ['case', ahead, 0.4, inFocus, 1, 0.6]
  const routeWidth = (width: number): ExpressionSpecification => ['case', inFocus, width, width * OUT_OF_FOCUS_WIDTH]
  const { traced, modeled, curve } = routeLines

  // The place layers, drawn alike from the places source and from the loose points of the clustered one.
  // An array, not a fragment: the Source gives its id to each of its direct children.
  const placeLayers = (prefix: string, only?: ExpressionSpecification) => {
    const and = (f: ExpressionSpecification): ExpressionSpecification => (only ? ['all', only, f] : f)
    const pointPaint: CircleLayerSpecification['paint'] = {
      // Told apart by fill and shape more than size: places on a journey are solid ink dots, places passed
      // or named open rings, towns the book never names small faint dots. Cities are a step larger.
      // Tale places keep an unseen circle here, so they stay clickable under their diamond.
      'circle-radius': ['+', ['match', ['get', 'role'], 'context', 2, 'passing', 3.5, 'tale', 5, 4], ['match', ['get', 'kind'], 'city', 1, 0]],
      'circle-color': ['match', ['get', 'role'], 'context', tokens.inkFaint, 'stop', tokens.ink, tokens.paper],
      'circle-opacity': ['match', ['get', 'role'], 'tale', 0, 1],
      'circle-stroke-color': ['match', ['get', 'role'], 'stop', tokens.paper, tokens.ink],
      'circle-stroke-width': ['match', ['get', 'role'], 'context', 0, 'stop', 1.5, 1.2],
      'circle-stroke-opacity': ['match', ['get', 'role'], 'tale', 0, 1],
    }
    return [
      <Layer key="point" id={`${prefix}-point`} type="circle" filter={and(['!', apart])} paint={pointPaint} />,
      // Pins apart from their stops look the same, on a layer MapView does not make clickable.
      <Layer key="apart" id={`${prefix}-apart`} type="circle" filter={and(apart)} paint={pointPaint} />,
      // Places in the tales told to Billy: a hollow diamond (TALE_ICON), told rather than travelled.
      <Layer
        key="tale"
        id={`${prefix}-tale`}
        type="symbol"
        filter={and(['==', ['get', 'role'], 'tale'])}
        layout={{ 'icon-image': TALE_ICON, 'icon-allow-overlap': true, 'icon-ignore-placement': true }}
      />,
      <Layer
        key="selected"
        id={`${prefix}-selected`}
        type="circle"
        filter={and(selected)}
        paint={{ 'circle-radius': 9, 'circle-color': 'rgba(0, 0, 0, 0)', 'circle-stroke-color': tokens.ink, 'circle-stroke-width': 2 }}
      />,
      <Layer
        key="label"
        id={`${prefix}-label`}
        type="symbol"
        {...(only ? { filter: only } : {})}
        layout={{
          // Towns the book never names are labelled only from zoom 9.
          // A place whose name the map sets along its landform's axis has no point label.
          'text-field': ['step', ['zoom'], ['match', ['get', 'role'], 'context', '', nameUnlessLined], 9, nameUnlessLined],
          // Ranges, valleys and streams in spaced italic, as on the survey sheets, and so are tale places, ranches
          // and springs; settlements in roman.
          'text-font': ['case',
            ['any', ['==', ['get', 'role'], 'tale'], ['in', ['get', 'kind'], ['literal', ['range', 'valley', 'stream', 'plain', ...QUIET]]]],
            ['literal', [fonts.italic]], ['literal', [fonts.roman]]],
          'text-letter-spacing': ['match', ['get', 'kind'], ['range', 'valley'], 0.15, 'city', 0.08, 0.02],
          // Towns and quiet places on the type scale; other places on a journey a size up from places passed.
          'text-size': ['interpolate', ['linear'], ['zoom'], 9, placeSize(0.85), 11, placeSize(1), 13, placeSize(1.15)],
          'text-anchor': 'top',
          'text-offset': [0, 0.6],
          'text-optional': true,
        }}
        paint={{
          'text-color': tokens.ink,
          // Ranches and springs are quiet unless the journey stops there.
          'text-opacity': ['case', ['==', ['get', 'role'], 'context'], 0.75,
            ['all', ['in', ['get', 'kind'], ['literal', QUIET]], ['!=', ['get', 'role'], 'stop']], QUIET_OPACITY, 1],
          'text-halo-color': tokens.paper,
          'text-halo-width': 1.5,
        }}
      />,
    ]
  }

  return (
    <>
      <Source id="areas" type="geojson" data={story.areas}>
        {/* Inferred areas: a flat tint in the journey's ink with a dotted edge, after the land-class tints of
            Wheeler sheet 84 (decision 0033). */}
        {/* Regions are in this layer too, unfilled, because it is the layer a click on an area hits (MapView). */}
        <Layer
          id="areas-fill"
          type="fill"
          paint={{ 'fill-color': inkByJourney, 'fill-opacity': ['case', ['==', ['get', 'kind'], 'region'], 0, inFocus, 0.18, 0.05] }}
        />
        <Layer
          id="areas-edge"
          type="line"
          filter={['!=', ['get', 'kind'], 'region']}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{ 'line-color': inkByJourney, 'line-width': 1.5, 'line-dasharray': [0.1, 2.5], 'line-opacity': ['case', inFocus, 0.9, 0.3] }}
        />
        {/* Regions: no fill, a fine ink line with a broad soft band inside it, after the ribboned county edges of
            the Mitchell and Gray atlas maps (decision 0033). The offset puts the band inside the line: the
            regions' outer rings run clockwise (crossing.validate checks it), so their inside is to the line's right. */}
        <Layer
          id="regions-band"
          type="line"
          filter={['==', ['get', 'kind'], 'region']}
          layout={{ 'line-join': 'round' }}
          paint={{ 'line-color': tokens.ink, 'line-width': 6, 'line-offset': 3, 'line-opacity': 0.15 }}
        />
        <Layer
          id="regions-edge"
          type="line"
          filter={['==', ['get', 'kind'], 'region']}
          layout={{ 'line-join': 'round' }}
          paint={{ 'line-color': tokens.ink, 'line-width': 0.8, 'line-opacity': 0.8 }}
        />
        <Layer id="areas-selected" type="line" filter={selected} paint={{ 'line-color': tokens.ink, 'line-width': 2.5 }} />
      </Source>
      <Source id="journeys" type="geojson" data={story.journeys}>
        {/* Above the relief, below the boundaries and water; the colour of the paper on screen at each zoom. */}
        <Layer
          id="journeys-halo"
          type="line"
          beforeId="county-line"
          filter={inFocus}
          layout={{ 'line-cap': 'round', 'line-join': 'round', visibility: halo ? 'visible' : 'none' }}
          paint={{
            'line-color': ['interpolate', ['linear'], ['zoom'], 9, tokens.paper, 10, tokens.paperShown],
            'line-width': ['interpolate', ['linear'], ['zoom'], 8, 16, 13, 40],
            'line-blur': 10,
            'line-opacity': 0.9,
          }}
        />
        {/* A paper casing under every route keeps the ink readable over satellite imagery. */}
        <Layer
          id="journeys-casing"
          type="line"
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{ 'line-color': tokens.paper, 'line-width': ['case', inFocus, 6.5, 3.5], 'line-opacity': ['case', inFocus, 0.8, 0.5] }}
        />
        {/* How sure the line is (decision 0033): solid where the book names the road or river followed; long dashes
            where the line is modelled over the ground (decision 0021); sparse short dashes, thinner and lighter,
            where the line only joins the stops. Dashed lines have butt caps: round caps would fill their gaps. */}
        <Layer
          id="journeys-line"
          type="line"
          filter={['==', ['get', 'method'], 'narrated-path']}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{
            'line-color': inkByJourney,
            'line-width': routeWidth(traced.width),
            'line-opacity': routeOpacity,
          }}
        />
        <Layer
          id="journeys-line-schematic"
          type="line"
          filter={['all', ['!', ['in', ['get', 'method'], ['literal', ['narrated-path', 'modeled']]]], ['!=', ['get', 'kind'], 'sightline']]}
          layout={{ 'line-cap': 'butt', 'line-join': 'round' }}
          paint={{
            'line-color': inkByJourney,
            'line-width': routeWidth(curve.width),
            'line-opacity': ['*', curve.opacity, routeOpacity],
            'line-dasharray': dashInWidths(curve.dash, curve.width),
          }}
        />
        <Layer
          id="journeys-line-modeled"
          type="line"
          filter={['==', ['get', 'method'], 'modeled']}
          layout={{ 'line-cap': 'butt', 'line-join': 'round' }}
          paint={{
            'line-color': inkByJourney,
            'line-width': routeWidth(modeled.width),
            'line-opacity': routeOpacity,
            'line-dasharray': dashInWidths(modeled.dash, modeled.width),
          }}
        />
        {/* Unseen and wide: what a click on a route hits (MapView), so the thin lines are easy to pick. */}
        <Layer
          id="journeys-hit"
          type="line"
          filter={['!=', ['get', 'kind'], 'sightline']}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{ 'line-color': tokens.ink, 'line-width': 14, 'line-opacity': 0 }}
        />
        {/* The false dawn: a direction, not a road, so dotted. */}
        <Layer
          id="journeys-sightline"
          type="line"
          filter={['==', ['get', 'kind'], 'sightline']}
          layout={{ 'line-cap': 'round' }}
          paint={{ 'line-color': inkByJourney, 'line-width': 2, 'line-opacity': ['case', inFocus, 0.9, 0.6], 'line-dasharray': [0.1, 2.5] }}
        />
      </Source>
      <Source id="places" type="geojson" data={places.outside}>
        {placeLayers('places')}
      </Source>
      {/* Around Cloverdale and the Peloncillos the places and the journey's stops share one clustered source
          (cluster.ts). Its clusters are markers, below; its loose places draw as places do everywhere else. */}
      <Source id={ZONE_SOURCE} type="geojson" data={places.zone} cluster clusterMaxZoom={CLUSTER_MAX_ZOOM} clusterRadius={CLUSTER_RADIUS} clusterProperties={CLUSTER_PROPERTIES}>
        {[
          ...placeLayers('zone-places', ['all', ['!', ['has', 'point_count']], ['==', ['get', 'cat'], 'place']]),
          // Unseen: they let cluster.ts ask which clusters and loose stops the map draws now.
          <Layer key="clusters" id={ZONE_CLUSTERS} type="circle" filter={['has', 'point_count']} paint={{ 'circle-radius': 1, 'circle-opacity': 0 }} />,
          <Layer key="stops" id={ZONE_STOPS} type="circle" filter={['==', ['get', 'cat'], 'stop']} paint={{ 'circle-radius': 1, 'circle-opacity': 0 }} />,
        ]}
      </Source>
      {corridorData && (
        <Source id="corridor" type="geojson" data={corridorData}>
          <Layer id="corridor-fill" type="fill" filter={['==', ['get', 'part'], 'area']} paint={{ 'fill-color': tokens.ink, 'fill-opacity': 0.08 }} />
          <Layer
            id="corridor-edge"
            type="line"
            filter={['==', ['get', 'part'], 'area']}
            layout={{ 'line-join': 'round' }}
            paint={{ 'line-color': tokens.ink, 'line-width': 1.5, 'line-dasharray': [4, 2] }}
          />
          <Layer
            id="corridor-label"
            type="symbol"
            filter={['==', ['get', 'part'], 'label']}
            layout={{ 'text-field': ['get', 'label'], 'text-font': ['literal', [fonts.italic]], 'text-size': 13, 'text-max-width': 12 }}
            paint={{ 'text-color': tokens.ink, 'text-halo-color': tokens.paper, 'text-halo-width': 2 }}
          />
        </Source>
      )}
      {clusters?.clusters.map((c) => (
        <Marker key={c.id} longitude={c.lon} latitude={c.lat}>
          {/* In the tab order, unlike the stop markers (the panel's stop list stands in for those): only a
              cluster's own button opens it from the keyboard. */}
          <button
            type="button"
            className="cluster-marker"
            aria-label={`${c.count} ${clusterWord(c)} close together: ${clusterDetail(c)}. Zoom in to see them`}
            title={`${clusterDetail(c)}. Zoom in to see them`}
            onClick={(e) => {
              e.stopPropagation()
              const map = mapRef?.getMap()
              if (map) void expandCluster(map, c, prefersReducedMotion())
            }}
          >
            {c.count}
            <span className="cluster-word">{clusterWord(c)}</span>
          </button>
        </Marker>
      ))}
      {stopGroups.map((group) => {
        const shown = group.filter((i) => !clusters?.clustered.has(stops[i].properties.id))
        if (shown.length === 0) return null
        const [lon, lat] = stops[shown[0]].geometry.coordinates
        const marker = (i: number) => (
          <button
            key={stops[i].properties.id}
            type="button"
            className={`stop-marker${i === stopIndex ? ' is-current' : ''}${i < stopIndex ? ' is-visited' : ''}`}
            style={{ borderColor: journeyInk[journey] }}
            aria-label={`Stop ${i + 1}: ${stops[i].properties.name}`}
            // The panel's stop list reaches the same stops by keyboard; out of the tab order, the map's markers
            // do not add up to 57 tab stops before the map's controls.
            tabIndex={-1}
            data-first-seen={stops[i].properties.first_seen}
            data-index={i}
          >
            {i + 1}
          </button>
        )
        return (
          <Marker
            key={stops[shown[0]].properties.id}
            longitude={lon}
            latitude={lat}
            onClick={(e) => {
              // Stopped here, natively, so the map does not take the click as one on empty map.
              e.originalEvent.stopPropagation()
              const index = (e.originalEvent.target as HTMLElement).closest<HTMLElement>('[data-index]')?.dataset.index
              if (index !== undefined) onSelectStop(Number(index))
            }}
          >
            {shown.length === 1 ? (
              marker(shown[0])
            ) : (
              // Stops at the same spot share one badge, each number its own button.
              <div className={`stop-group${shown.includes(stopIndex) ? ' has-current' : ''}`} style={{ borderColor: journeyInk[journey] }}>
                {shown.map(marker)}
              </div>
            )}
          </Marker>
        )
      })}
    </>
  )
}
