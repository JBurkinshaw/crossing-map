import type { ExpressionSpecification, LayerSpecification, SourceSpecification } from 'maplibre-gl'

// Large drawings for the opening view (decisions 0076 and 0079): six pen drawings of the book's broad themes, no
// captions, set close around the story where no stop or route line lies under them. Each is a georeferenced image
// (art/vignettes/large.py draws them on a 288 x 216 grid and renders them to site/public/art/), so it grows with the
// map, and it fades out between FADE[0] and FADE[1] as the reader zooms in to the story. Corners are lon, lat:
// top left, top right, bottom right, bottom left, each box 2.2 degrees wide at its centre's latitude and 4:3 on
// screen in Web Mercator. They are not dated by reading progress: they show no event, only the country and its
// creatures.
const MUYBRIDGE = 'Horses and riders traced from Eadweard Muybridge, Animal Locomotion plate 580, 1887 (public domain)'

export const LARGE_ART: { id: string; name: string; credit: string; corners: [number, number][] }[] = [
  {
    id: 'large-she-wolf', name: 'The she-wolf',
    credit: 'Drawn after a US Fish and Wildlife Service photograph of a Mexican wolf (public domain)',
    corners: [[-110.8, 29.520], [-108.6, 29.520], [-108.6, 28.075], [-110.8, 28.075]],
  },
  {
    id: 'large-riders-in-the-sierra', name: 'Two riders in the sierra', credit: MUYBRIDGE,
    corners: [[-112.0, 31.506], [-109.8, 31.506], [-109.8, 30.089], [-112.0, 30.089]],
  },
  {
    id: 'large-cranes', name: 'Cranes over a desert range', credit: 'Drawn by hand',
    corners: [[-112.4, 33.491], [-110.2, 33.491], [-110.2, 32.104], [-112.4, 32.104]],
  },
  {
    id: 'large-ruined-church', name: 'A ruined church',
    credit: 'Drawn after a photograph of the Quarai mission ruin by suemruth (CC BY 2.0)',
    corners: [[-106.6, 29.520], [-104.4, 29.520], [-104.4, 28.075], [-106.6, 28.075]],
  },
  {
    id: 'large-horse-herd', name: 'A horse herd driven across the plain', credit: MUYBRIDGE,
    corners: [[-107.4, 31.506], [-105.2, 31.506], [-105.2, 30.089], [-107.4, 30.089]],
  },
  {
    id: 'large-lone-rider', name: 'A lone rider and his packhorse', credit: MUYBRIDGE,
    corners: [[-107.0, 33.491], [-104.8, 33.491], [-104.8, 32.104], [-107.0, 32.104]],
  },
]

// Full strength out to zoom 7, where a drawing is about 400 px across, gone by 8, where it would fill the screen.
const FADE: [number, number] = [7, 8]
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
