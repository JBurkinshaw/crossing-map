import { Layer, Marker, Source } from '@vis.gl/react-maplibre'
import type { ExpressionSpecification } from 'maplibre-gl'
import type { Feature, Point } from 'geojson'
import type { Story, StoryProps } from '../data/story'
import { fonts, journeyInk, tokens } from './tokens'

const inkByJourney: ExpressionSpecification = [
  'match', ['get', 'journey'], 'J1', journeyInk.J1, 'J2', journeyInk.J2, tokens.ink,
]

type Props = {
  story: Story
  stops: Feature<Point, StoryProps>[]
  stopIndex: number
  onSelectStop: (index: number) => void
}

export function StoryLayers({ story, stops, stopIndex, onSelectStop }: Props) {
  const journey = stops[0]?.properties.journey ?? ''
  const inFocus: ExpressionSpecification = ['==', ['get', 'journey'], journey]

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
      </Source>
      <Source id="journeys" type="geojson" data={story.journeys}>
        {/* Solid where the book names the road or river followed; dashed where the path is not known. */}
        <Layer
          id="journeys-line"
          type="line"
          filter={['==', ['get', 'method'], 'narrated-path']}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{
            'line-color': inkByJourney,
            'line-width': ['case', inFocus, 2.5, 1.2],
            'line-opacity': ['case', inFocus, 0.95, 0.3],
          }}
        />
        <Layer
          id="journeys-line-schematic"
          type="line"
          filter={['!=', ['get', 'method'], 'narrated-path']}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{
            'line-color': inkByJourney,
            'line-width': ['case', inFocus, 2.5, 1.2],
            'line-opacity': ['case', inFocus, 0.95, 0.3],
            'line-dasharray': [3, 2],
          }}
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
          >
            {i + 1}
          </button>
        </Marker>
      ))}
    </>
  )
}
