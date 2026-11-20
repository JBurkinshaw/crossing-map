import type { ExpressionSpecification, LayerSpecification, SourceSpecification } from 'maplibre-gl'

// Large drawings for the opening view (decision 0076): six pen drawings of the book's broad themes, no captions, in
// the empty quarters east and west of the story, where the map has room at low zoom. Each is a georeferenced image
// (art/vignettes/large.py draws them on a 288 x 216 grid and renders them to site/public/art/), so it grows with the
// map, and it fades out between FADE[0] and FADE[1] as the reader zooms in to the story. Corners are lon, lat:
// top left, top right, bottom right, bottom left, each box 3 degrees wide at its centre's latitude and 4:3 on screen
// in Web Mercator, at least half a degree clear of every stop and route line. They are not dated by reading
// progress: they show no event, only the country and its creatures.
const MUYBRIDGE = 'Horses and riders traced from Eadweard Muybridge, Animal Locomotion plate 580, 1887 (public domain)'

export const LARGE_ART: { id: string; name: string; credit: string; corners: [number, number][] }[] = [
  {
    id: 'large-she-wolf', name: 'The she-wolf',
    credit: 'Drawn after a US Fish and Wildlife Service photograph of a Mexican wolf (public domain)',
    corners: [[-113.9, 28.989], [-110.9, 28.989], [-110.9, 27.002], [-113.9, 27.002]],
  },
  {
    id: 'large-riders-in-the-sierra', name: 'Two riders in the sierra', credit: MUYBRIDGE,
    corners: [[-113.9, 31.316], [-110.9, 31.316], [-110.9, 29.374], [-113.9, 29.374]],
  },
  {
    id: 'large-cranes', name: 'Cranes over a desert range', credit: 'Drawn by hand',
    corners: [[-113.9, 33.642], [-110.9, 33.642], [-110.9, 31.748], [-113.9, 31.748]],
  },
  {
    id: 'large-ruined-church', name: 'A ruined church',
    credit: 'Drawn after a photograph of the Quarai mission ruin by suemruth (CC BY 2.0)',
    corners: [[-106.2, 29.187], [-103.2, 29.187], [-103.2, 27.204], [-106.2, 27.204]],
  },
  {
    id: 'large-horse-herd', name: 'A horse herd driven across the plain', credit: MUYBRIDGE,
    corners: [[-106.2, 31.365], [-103.2, 31.365], [-103.2, 29.425], [-106.2, 29.425]],
  },
  {
    id: 'large-lone-rider', name: 'A lone rider and his packhorse', credit: MUYBRIDGE,
    corners: [[-106.2, 34.532], [-103.2, 34.532], [-103.2, 32.658], [-106.2, 32.658]],
  },
]

// Full strength out to zoom 6, gone by 7, where a drawing would be about 550 px across and reach the story.
const FADE: [number, number] = [6, 7]
const OPACITY = 0.95

export function largeArtSources(siteBase: string): Record<string, SourceSpecification> {
  return Object.fromEntries(LARGE_ART.map(({ id, corners }) => [
    id, { type: 'image', url: `${siteBase}art/${id}.png`, coordinates: corners as [[number, number], [number, number], [number, number], [number, number]] },
  ]))
}

export function largeArtLayers(): LayerSpecification[] {
  return LARGE_ART.map(({ id }) => ({
    id,
    type: 'raster',
    source: id,
    maxzoom: FADE[1],
    paint: {
      'raster-opacity': ['interpolate', ['linear'], ['zoom'], FADE[0], OPACITY, FADE[1], 0] as ExpressionSpecification,
    },
  }))
}
