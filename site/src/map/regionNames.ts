import type { ExpressionSpecification, LayerSpecification, SourceSpecification } from 'maplibre-gl'
import { fonts } from './tokens'

// Large region names for the opening view (decision 0082): the book's own names for open country, lettered faintly
// across the land in spaced small capitals, as the Wheeler sheets letter a valley or a plain. Each stands at a
// point in its country, turned to follow its valley or river, and grows and fades with the large drawings
// (largeArt.ts), so the map at low zoom reads as country before it reads as stops. Every name is the book's: the
// Animas Plains (1-04), the bootheel (4-01), the Carretas Plain (2-01), the plains of Chihuahua (2-08), the high plains
// of the Babícora (3-03, shortened) and the Bavispe. The map's title covers the plains of Saint Augustine (4-02).
export const REGION_NAMES: { name: string; at: [number, number]; rotate: number }[] = [
  { name: 'The Animas Plains', at: [-108.86, 32.05], rotate: -78 },
  { name: 'The Bootheel', at: [-108.45, 31.5], rotate: 0 },
  { name: 'The Carretas Plain', at: [-108.55, 30.55], rotate: -6 },
  { name: 'The Plains of Chihuahua', at: [-107.05, 31.05], rotate: -12 },
  { name: 'The Babícora', at: [-107.5, 29.45], rotate: -35 },
  { name: 'The Bavispe', at: [-109.28, 30.2], rotate: -72 },
]

// In the ink at 0.8, readable but lighter than the story's own names: about 15 px at the opening view and 24 px at
// zoom 7, at full strength to 7.5, after the place pins come in at 7, and gone by 8.5, before a journey's own view
// gets busy.
const SIZE: [number, number][] = [[5, 13], [6, 18], [7, 24], [8.5, 33]]
const FADE: [number, number] = [7.5, 8.5]

export const regionNameSource = (): SourceSpecification => ({
  type: 'geojson',
  data: {
    type: 'FeatureCollection',
    features: REGION_NAMES.map(({ name, at, rotate }) => ({
      type: 'Feature', properties: { name, rotate }, geometry: { type: 'Point', coordinates: at },
    })),
  },
})

export function regionNameLayer(ink: string, paper: string): LayerSpecification {
  return {
    id: 'region-names',
    type: 'symbol',
    source: 'region-names',
    maxzoom: FADE[1],
    layout: {
      'text-field': ['get', 'name'],
      'text-font': [fonts.smallCaps],
      'text-size': ['interpolate', ['linear'], ['zoom'], ...SIZE.flat()] as ExpressionSpecification,
      'text-letter-spacing': 0.45,
      'text-rotate': ['get', 'rotate'],
      'text-rotation-alignment': 'map',
      'text-max-width': 30,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
    },
    paint: {
      'text-color': ink,
      'text-halo-color': paper,
      'text-halo-width': 1.2,
      'text-opacity': ['interpolate', ['linear'], ['zoom'], FADE[0], 0.8, FADE[1], 0] as ExpressionSpecification,
    },
  }
}
