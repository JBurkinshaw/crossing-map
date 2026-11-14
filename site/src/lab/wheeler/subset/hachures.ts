import type { ExpressionSpecification, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { tilesBase } from '../../../map/setup'

// Wheeler hachures for the test area (review/stage-9/wheeler-hachures/README.md): short strokes packed closer on
// steep ground, white partings on crests and spurs, white dots on summits, blank mesa tops and valley floors, and
// escarpments as one comb of wedges. Built by `crossing.hachures --style wheeler` and
// `tiles.build_relief --style wheeler` into lab-wheeler-hachures.pmtiles, which only covers the test box, so inside
// the box the site's hachures are hidden and these drawn in their place.

// The test area: west, south, east, north (the bootheel and the upper Bavispe).
export const SUBSET_BOX: [number, number, number, number] = [-109.6, 30.5, -108.4, 31.6]
const [w, s, e, n] = SUBSET_BOX
const inBox: ExpressionSpecification = ['within', { type: 'Polygon', coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]] }]

// Wheeler's darkest ink, measured at #110600 to #221802 in the dense hachures, lifted a little for the screen.
const INK = '#2e2010'

// Stroke width in CSS pixels: Wheeler's 0.14 mm at zoom 11 on a 96 dpi screen is 0.53 px. The strokes are laid out
// for zoom 11 (the build's DESIGN_ZOOM), so at zoom 10 they lie twice as close on screen: only 70% of them draw
// there (Rand is a fixed digit, 0-9), and the width is a little less. From 12 they widen so they stay visible as
// they spread apart. The wedges are drawn to scale, so the combs keep their weight at every zoom.
const WIDTH: ExpressionSpecification = ['interpolate', ['linear'], ['zoom'], 10, 0.42, 11, 0.53, 12, 0.8, 13, 1.2]

function layers(): LayerSpecification[] {
  return [
    {
      id: 'subset-hachure',
      type: 'line',
      source: 'subset-hachures',
      'source-layer': 'hachure',
      minzoom: 10,
      filter: ['step', ['zoom'], ['<', ['get', 'Rand'], 7], 11, true],
      layout: { 'line-cap': 'round' },
      paint: { 'line-color': INK, 'line-width': WIDTH, 'line-opacity': 0.92 },
    },
    {
      id: 'subset-rim',
      type: 'fill',
      source: 'subset-hachures',
      'source-layer': 'rim',
      minzoom: 10,
      paint: { 'fill-color': INK, 'fill-opacity': 0.92 },
    },
  ]
}

// The style with the site's hachures hidden inside the box (a stroke crossing its edge still draws) and the Wheeler
// strokes drawn just above where they were, under the water, roads and type.
export function subsetHachures(style: StyleSpecification): StyleSpecification {
  const base = style.layers.map((l) => {
    if (!l.id.startsWith('hachure-')) return l
    const own = (l as { filter?: ExpressionSpecification }).filter
    return { ...l, filter: own ? ['all', own, ['!', inBox]] : ['!', inBox] } as LayerSpecification
  })
  const last = base.map((l) => l.id.startsWith('hachure-')).lastIndexOf(true)
  return {
    ...style,
    sources: {
      ...style.sources,
      'subset-hachures': { type: 'vector', url: `pmtiles://${tilesBase}lab-wheeler-hachures.pmtiles` },
    },
    layers: [...base.slice(0, last + 1), ...layers(), ...base.slice(last + 1)],
  }
}
