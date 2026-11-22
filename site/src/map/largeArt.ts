import type { ExpressionSpecification, LayerSpecification, SourceSpecification } from 'maplibre-gl'
import { fonts } from './tokens'

// Large drawings for the opening view (decisions 0076, 0079 and 0082): pen drawings of the book's broad themes, no
// captions, set close around the story where no stop or route line lies under them. Each is a georeferenced image
// (art/vignettes/large.py draws them on a 288 x 216 grid and renders them to site/public/art/), so it grows with the
// map, and it fades out between FADE[0] and FADE[1] as the reader zooms in to the story. Corners are lon, lat:
// top left, top right, bottom right, bottom left, each box 2.2 degrees wide at its centre's latitude (the north
// arrow 1.8) and 4:3 on screen in Web Mercator. They are not dated by reading progress: they show no event, only
// the country and its creatures.
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
  {
    // The map's north arrow (decision 0082): smaller than the rest, 1.8 degrees wide, set over the horned moon so the
    // book's two night skies stand together.
    id: 'large-cassiopeia', name: 'North: the polestar, with Cassiopeia wheeling round it (2-05)',
    credit: 'Drawn by hand; the stars after the Yale Bright Star Catalogue',
    corners: [[-113.9, 31.113], [-112.1, 31.113], [-112.1, 29.95], [-113.9, 29.95]],
  },
  {
    id: 'large-horned-moon', name: 'The horned moon with Venus (3-08)', credit: MUYBRIDGE,
    corners: [[-113.2, 29.818], [-111.0, 29.818], [-111.0, 28.377], [-113.2, 28.377]],
  },
]

// Full strength out to zoom 7, where a drawing is about 400 px across, gone by 8, where it would fill the screen.
const FADE: [number, number] = [7, 8]
// The zoom from which the story's detail takes over as the drawings fade: the land cover fades in and the place
// pins and names show (decision 0082).
export const DETAIL_FROM = FADE[0]
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

// The map's title at the same scale as the drawings (decisions 0081 and 0082): "THE CROSSING" in spaced small capitals
// in the map's ink, after the titles of the survey sheets the map follows. It stands over the north of the story,
// and at low zoom it draws above the stops and glyphs (StoryLayers lifts it), giving way to them as it fades. Its
// size doubles with each zoom step, as the land does.
const TITLE_AT: [number, number] = [-108.4, 33.75]
const TITLE_SIZE: [number, number] = [5, 26] // zoom, text-size in px of the title line

// The first view's frame: every drawing and the title, its lettering about half a degree tall (decision 0082). The
// map opens on it, before the reader's journey or stop takes over.
export const OPENING_BOUNDS: [number, number, number, number] = (() => {
  const points = [...LARGE_ART.flatMap(({ corners }) => corners), [TITLE_AT[0], TITLE_AT[1] + 0.3], [TITLE_AT[0], TITLE_AT[1] - 0.3]]
  const lons = points.map(([lon]) => lon)
  const lats = points.map(([, lat]) => lat)
  return [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)]
})()

export const largeTitleSource = (): SourceSpecification => ({
  type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: TITLE_AT } },
})

export function largeTitleLayer(ink: string, paper: string): LayerSpecification {
  const [z, size] = TITLE_SIZE
  return {
    id: 'large-title',
    type: 'symbol',
    source: 'large-title',
    maxzoom: FADE[1],
    layout: {
      'text-field': 'THE CROSSING',
      'text-font': [fonts.smallCaps],
      'text-size': ['interpolate', ['exponential', 2], ['zoom'], z, size, FADE[1], size * 2 ** (FADE[1] - z)] as ExpressionSpecification,
      'text-letter-spacing': 0.3,
      'text-max-width': 60,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
    },
    paint: {
      'text-color': ink,
      'text-halo-color': paper,
      'text-halo-width': 1.6,
      'text-opacity': ['interpolate', ['linear'], ['zoom'], FADE[0], 0.85, FADE[1], 0] as ExpressionSpecification,
    },
  }
}
