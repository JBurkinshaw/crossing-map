import { useMemo } from 'react'
import { Layer, Marker, Source, useMap } from '@vis.gl/react-maplibre'
import type { ExpressionSpecification } from 'maplibre-gl'
import type { Feature, FeatureCollection, Geometry, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import { CLUSTER_MAX_ZOOM, CLUSTER_RADIUS, expandCluster, inZone, useZoneClusters, ZONE_CLUSTERS, ZONE_SOURCE, ZONE_STOPS } from './cluster'
import { corridor, midpoint } from './corridor'
import { fonts, journeyInks, palettes, type Theme } from './tokens'

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
  // In step-through, the sequence of the current stop: the road from there on fades (data dimming, plan 9).
  aheadFrom: number | null
  // The palette the layers are drawn in: the map's theme on the classic basemap.
  theme: Theme
  // The corridor to outline, when the line picked was spoken on the road.
  corridor: Corridor | null
}

const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

export function StoryLayers({ story, stops, stopIndex, onSelectStop, halo, selectedId, aheadFrom, theme, corridor: road }: Props) {
  const { current: mapRef } = useMap()
  // The places and the journey's stops around Cloverdale and the Peloncillos go to the clustered source; the
  // current stop stays out of it, so the stop being read always shows.
  const current = stops[stopIndex]?.properties.id
  const places = useMemo(() => {
    const outside: FeatureCollection<Point, StoryProps> = { ...story.places, features: story.places.features.filter((f) => !inZone(f.geometry.coordinates)) }
    const zone: FeatureCollection<Point> = {
      type: 'FeatureCollection',
      features: [
        ...story.places.features.filter((f) => inZone(f.geometry.coordinates)).map((f) => ({ ...f, properties: { ...f.properties, cat: 'place' } })),
        ...stops
          .filter((f) => f.properties.id !== current && inZone(f.geometry.coordinates))
          .map((f) => ({ ...f, properties: { id: f.properties.id, first_seen: f.properties.first_seen, cat: 'stop' } })),
      ],
    }
    return { outside, zone }
  }, [story.places, stops, current])
  const zoneIds = useMemo(() => places.zone.features.map((f) => String(f.properties?.id)), [places.zone])
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

  const tokens = palettes[theme]
  const journeyInk = journeyInks(tokens)
  const inkByJourney = ['match', ['get', 'journey'], ...Object.entries(journeyInk).flat(), tokens.ink] as unknown as ExpressionSpecification
  const journey = stops[0]?.properties.journey ?? ''
  const inFocus: ExpressionSpecification = ['==', ['get', 'journey'], journey]
  const selected: ExpressionSpecification = ['==', ['get', 'id'], selectedId ?? '']
  // A segment joins stop `sequence` to the next, so the road ahead starts at the current stop's sequence.
  const ahead: ExpressionSpecification =
    aheadFrom === null ? ['boolean', false] : ['all', inFocus, ['>=', ['coalesce', ['get', 'sequence'], 9999], aheadFrom]]
  const routeOpacity: ExpressionSpecification = ['case', ahead, 0.4, inFocus, 0.95, 0.3]

  // The place layers, drawn alike from the places source and from the loose points of the clustered one.
  // An array, not a fragment: the Source gives its id to each of its direct children.
  const placeLayers = (prefix: string, only?: ExpressionSpecification) => {
    const and = (f: ExpressionSpecification): ExpressionSpecification => (only ? ['all', only, f] : f)
    return [
      <Layer
        key="point"
        id={`${prefix}-point`}
        type="circle"
        {...(only ? { filter: only } : {})}
        paint={{
          // Context towns (never named in the book) are small solid dots; story places are open rings.
          'circle-radius': ['match', ['get', 'role'], 'context', 2, 'passing', 3, 4],
          'circle-color': ['match', ['get', 'role'], 'context', tokens.inkFaint, tokens.paper],
          'circle-stroke-color': tokens.ink,
          'circle-stroke-width': ['match', ['get', 'role'], 'context', 0, 1.2],
        }}
      />,
      // Places in the tales told to Billy: a ring with a dot.
      <Layer key="tale" id={`${prefix}-tale`} type="circle" filter={and(['==', ['get', 'role'], 'tale'])} paint={{ 'circle-radius': 1.4, 'circle-color': tokens.ink }} />,
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
          'text-field': ['get', 'name'],
          // Ranges, valleys and streams in spaced italic, as on the survey sheets; settlements in roman.
          'text-font': ['match', ['get', 'kind'], ['range', 'valley', 'stream', 'spring', 'plain'], ['literal', [fonts.italic]], ['literal', [fonts.roman]]],
          'text-letter-spacing': ['match', ['get', 'kind'], ['range', 'valley'], 0.15, 0.02],
          'text-size': ['match', ['get', 'kind'], ['range', 'valley'], 14, 12.5],
          'text-anchor': 'top',
          'text-offset': [0, 0.6],
          'text-optional': true,
        }}
        paint={{
          'text-color': tokens.ink,
          'text-opacity': ['match', ['get', 'role'], 'context', 0.6, 1],
          'text-halo-color': tokens.paper,
          'text-halo-width': 1.5,
        }}
      />,
    ]
  }

  return (
    <>
      <Source id="areas" type="geojson" data={story.areas}>
        <Layer
          id="areas-fill"
          type="fill"
          paint={{ 'fill-color': inkByJourney, 'fill-opacity': ['case', inFocus, 0.12, 0.04] }}
        />
        <Layer
          id="areas-edge"
          type="line"
          paint={{ 'line-color': inkByJourney, 'line-width': 1, 'line-dasharray': [2, 2], 'line-opacity': ['case', inFocus, 0.8, 0.25] }}
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
          paint={{ 'line-color': tokens.paper, 'line-width': ['case', inFocus, 5, 2.5], 'line-opacity': ['case', inFocus, 0.7, 0.3] }}
        />
        {/* Solid where the book names the road or river followed; dashed where the path is not known. */}
        <Layer
          id="journeys-line"
          type="line"
          filter={['==', ['get', 'method'], 'narrated-path']}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{
            'line-color': inkByJourney,
            'line-width': ['case', inFocus, 2.5, 1.2],
            'line-opacity': routeOpacity,
          }}
        />
        <Layer
          id="journeys-line-schematic"
          type="line"
          filter={['all', ['!=', ['get', 'method'], 'narrated-path'], ['!=', ['get', 'kind'], 'sightline']]}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{
            'line-color': inkByJourney,
            'line-width': ['case', inFocus, 2.5, 1.2],
            'line-opacity': routeOpacity,
            'line-dasharray': [3, 2],
          }}
        />
        {/* The false dawn: a direction, not a road, so dotted. */}
        <Layer
          id="journeys-sightline"
          type="line"
          filter={['==', ['get', 'kind'], 'sightline']}
          layout={{ 'line-cap': 'round' }}
          paint={{ 'line-color': inkByJourney, 'line-width': 2, 'line-opacity': ['case', inFocus, 0.9, 0.3], 'line-dasharray': [0.1, 2.5] }}
        />
      </Source>
      <Source id="places" type="geojson" data={places.outside}>
        {placeLayers('places')}
      </Source>
      {/* Around Cloverdale and the Peloncillos the places and the journey's stops share one clustered source
          (cluster.ts). Its clusters are markers, below; its loose places draw as places do everywhere else. */}
      <Source id={ZONE_SOURCE} type="geojson" data={places.zone} cluster clusterMaxZoom={CLUSTER_MAX_ZOOM} clusterRadius={CLUSTER_RADIUS}>
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
            aria-label={`${c.count} places and stops here. Zoom in to see them`}
            title="Zoom in to see them"
            onClick={(e) => {
              e.stopPropagation()
              const map = mapRef?.getMap()
              if (map) void expandCluster(map, c, reducedMotion())
            }}
          >
            {c.count}
          </button>
        </Marker>
      ))}
      {stops.map((f, i) => clusters?.clustered.has(f.properties.id) ? null : (
        <Marker
          key={f.properties.id}
          longitude={f.geometry.coordinates[0]}
          latitude={f.geometry.coordinates[1]}
          onClick={(e) => {
            e.originalEvent.stopPropagation()
            onSelectStop(i)
          }}
        >
          <button
            type="button"
            className={`stop-marker${i === stopIndex ? ' is-current' : ''}${i < stopIndex ? ' is-visited' : ''}`}
            style={{ borderColor: journeyInk[journey] }}
            aria-label={`Stop ${i + 1}: ${f.properties.name}`}
            // The panel's stop list reaches the same stops by keyboard; out of the tab order, the map's markers
            // do not add up to 57 tab stops before the map's controls.
            tabIndex={-1}
            data-first-seen={f.properties.first_seen}
          >
            {i + 1}
          </button>
        </Marker>
      ))}
    </>
  )
}
