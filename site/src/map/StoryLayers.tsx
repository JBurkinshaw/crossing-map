import { Layer, Marker, Source } from '@vis.gl/react-maplibre'
import type { ExpressionSpecification } from 'maplibre-gl'
import type { Feature, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import { S5_PAPER_SHOWN } from './relief'
import { fonts, journeyInk, tokens } from './tokens'

const inkByJourney = ['match', ['get', 'journey'], ...Object.entries(journeyInk).flat(), tokens.ink] as unknown as ExpressionSpecification

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
}

export function StoryLayers({ story, stops, stopIndex, onSelectStop, halo, selectedId, aheadFrom }: Props) {
  const journey = stops[0]?.properties.journey ?? ''
  const inFocus: ExpressionSpecification = ['==', ['get', 'journey'], journey]
  const selected: ExpressionSpecification = ['==', ['get', 'id'], selectedId ?? '']
  // A segment joins stop `sequence` to the next, so the road ahead starts at the current stop's sequence.
  const ahead: ExpressionSpecification =
    aheadFrom === null ? ['boolean', false] : ['all', inFocus, ['>=', ['coalesce', ['get', 'sequence'], 9999], aheadFrom]]
  const routeOpacity: ExpressionSpecification = ['case', ahead, 0.4, inFocus, 0.95, 0.3]

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
            'line-color': ['interpolate', ['linear'], ['zoom'], 9, tokens.paper, 10, S5_PAPER_SHOWN],
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
      <Source id="places" type="geojson" data={story.places}>
        <Layer
          id="places-point"
          type="circle"
          paint={{
            // Context towns (never named in the book) are small solid dots; story places are open rings.
            'circle-radius': ['match', ['get', 'role'], 'context', 2, 'passing', 3, 4],
            'circle-color': ['match', ['get', 'role'], 'context', tokens.inkFaint, tokens.paper],
            'circle-stroke-color': tokens.ink,
            'circle-stroke-width': ['match', ['get', 'role'], 'context', 0, 1.2],
          }}
        />
        {/* Places in the tales told to Billy: a ring with a dot. */}
        <Layer id="places-tale" type="circle" filter={['==', ['get', 'role'], 'tale']} paint={{ 'circle-radius': 1.4, 'circle-color': tokens.ink }} />
        <Layer
          id="places-selected"
          type="circle"
          filter={selected}
          paint={{ 'circle-radius': 9, 'circle-color': 'rgba(0, 0, 0, 0)', 'circle-stroke-color': tokens.ink, 'circle-stroke-width': 2 }}
        />
        <Layer
          id="places-label"
          type="symbol"
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
        />
      </Source>
      {stops.map((f, i) => (
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
            data-first-seen={f.properties.first_seen}
          >
            {i + 1}
          </button>
        </Marker>
      ))}
    </>
  )
}
