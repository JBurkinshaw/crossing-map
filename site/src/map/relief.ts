import type { ExpressionSpecification, LayerSpecification, Map as MaplibreMap, SourceSpecification } from 'maplibre-gl'
import { fonts, typeScale, zoomedSize, type Palette } from './tokens'
import { heightLabel, type Units } from '../units'

// Relief (docs/design.md, section 5.2; decision 0016, "S5"): an Imhof desert tint below zoom 10, then
// near-white paper, a light grey hillshade, 50 m contours and hachures (HACHURE_SET), with mountain glyphs.
export function reliefSources(tilesBase: string, dataBase: string): Record<string, SourceSpecification> {
  return {
    // A trimmed copy of data/mountain_glyphs.geojson with only the properties drawn (scripts/copy-data.mjs).
    glyphs: { type: 'geojson', data: `${dataBase}map/mountain_glyphs.geojson` },
    vignettes: { type: 'geojson', data: `${dataBase}vignettes.geojson` },
    // The landform name lines the map letters, trimmed and filtered by scripts/copy-data.mjs.
    landforms: { type: 'geojson', data: `${dataBase}map/landforms.geojson` },
    terrain: { type: 'raster-dem', url: `pmtiles://${tilesBase}terrain.pmtiles`, encoding: 'terrarium', tileSize: 256 },
    ...hachureSources(tilesBase),
    contours: { type: 'vector', url: `pmtiles://${tilesBase}contours.pmtiles` },
  }
}

// Which hachures draw inside the journeys corridor (decision 0024). 'wheeler': Wheeler-style strokes from
// relief-wheeler*.pmtiles (crossing.wheeler_hachures). 'production': the fine and dense sepia strokes from
// relief.pmtiles and relief-dense.pmtiles (decision 0016). Outside the corridor the coarse strokes draw either way,
// in the same paint; the Wheeler archives carry their own copy of them, so that set fetches no other hachure archive.
// Both sets are built and released, so this one line swaps them.
type HachureSet = 'wheeler' | 'production'
export const HACHURE_SET = 'wheeler' as HachureSet

// The Wheeler archives, split by zoom so each stays under 100 MB (design 5.2) and a reader who stays zoomed out
// never fetches the zoom 12 tiles. Each holds the layers `coarse`, `hachure` and `rim` (tiles.build_relief).
const WHEELER_PARTS: { source: string; file: string; zooms: [number, number] }[] = [
  { source: 'relief-wheeler', file: 'relief-wheeler.pmtiles', zooms: [10, 11] },
  { source: 'relief-wheeler-12', file: 'relief-wheeler-12.pmtiles', zooms: [12, 12] },
]

function hachureSources(tilesBase: string): Record<string, SourceSpecification> {
  if (HACHURE_SET === 'wheeler') {
    return Object.fromEntries(WHEELER_PARTS.map((w) => [w.source, { type: 'vector', url: `pmtiles://${tilesBase}${w.file}` }]))
  }
  return {
    relief: { type: 'vector', url: `pmtiles://${tilesBase}relief.pmtiles` },
    // Split from relief.pmtiles so each archive stays under 100 MB (design 5.2) and readers who stay zoomed out
    // never fetch the dense strokes.
    'relief-dense': { type: 'vector', url: `pmtiles://${tilesBase}relief-dense.pmtiles` },
  }
}

// Named summits from medium size up, and every named pass (passes are all small), with their height.
// Named medium and large summits and named passes: the name over the height. Unnamed and small summits: from zoom 10
// (about the scale of Wheeler Survey sheet 83), the height alone as a smaller spot height, as the sheets print them
// (review/stage-8/wheeler/README.md); below it they crowd the map.
const namedGlyph: ExpressionSpecification = ['all', ['!=', ['get', 'name'], 'Unnamed summit'], ['!=', ['get', 'name'], 'Unnamed pass'],
  ['any', ['!=', ['get', 'size'], 'small'], ['==', ['get', 'landform'], 'pass']]]
const spotHeight: ExpressionSpecification = ['all', ['!=', ['get', 'landform'], 'pass'], ['!=', ['get', 'elevation_m'], null]]
// A named pass has no glyph: its name is set across the saddle instead (pass-label), as Wheeler letters a pass.
const namedPass: ExpressionSpecification = ['all', ['==', ['get', 'landform'], 'pass'], ['!=', ['get', 'name'], 'Unnamed pass']]

export function glyphText(units: Units): ExpressionSpecification {
  const name: ExpressionSpecification =
    ['case', ['!=', ['get', 'elevation_m'], null], ['concat', ['get', 'name'], '\n', heightLabel(['get', 'elevation_m'], units)], ['get', 'name']]
  return ['step', ['zoom'],
    ['case', namedGlyph, name, ''],
    10, ['case', namedGlyph, name, spotHeight, heightLabel(['get', 'elevation_m'], units), '']]
}

// Heights on the heavier contours (every 200 m), in feet rounded to 10, since the lines are drawn in metres.
export function contourText(units: Units): ExpressionSpecification {
  return heightLabel(['get', 'Ele'], units, 10)
}

// Pass names in small capitals laid across the saddle, or along the road through the pass where one crosses it
// (crossing.pass_lines; decision 0027), as Wheeler letters RATON PASS. Point labels turned to the pass's line: a
// line label would need a line longer than the name. They are placed after the summit glyphs, so a summit wins.
// The passes the book names show from zoom 7, as the book's landforms do; the others from 9, where the small glyphs
// start. The layer is in PROGRESS_LAYERS (spoiler/filter.ts): a pass the book names shows from its episode.
function passLabel(p: Palette): LayerSpecification {
  return {
    id: 'pass-label',
    type: 'symbol',
    source: 'passes',
    minzoom: 7,
    filter: ['any', ['!=', ['get', 'place_ref'], null], ['>=', ['zoom'], 9]],
    layout: {
      'text-field': ['get', 'name'],
      'text-font': [fonts.smallCaps],
      'text-size': zoomedSize(typeScale.pass),
      'text-letter-spacing': 0.08,
      'text-rotate': ['get', 'rotate'],
      // A pass the book names keeps its place's ring on the saddle (StoryLayers): its name sits just beside it.
      'text-offset': ['case', ['!=', ['get', 'place_ref'], null], ['literal', [0, 0.9]], ['literal', [0, 0]]],
      'text-rotation-alignment': 'map',
      'text-pitch-alignment': 'viewport',
      'text-padding': 2,
    },
    paint: { 'text-color': p.ink, 'text-halo-color': p.paper, 'text-halo-width': 1.2 },
  }
}

function glyphs(p: Palette, units: Units): LayerSpecification[] {
  const size: ExpressionSpecification = ['*', ['match', ['get', 'size'], 'large', 0.85, 'medium', 0.65, 0.5], ['get', 'glyph_scale']]
  return [
    {
      id: 'contour-label',
      type: 'symbol',
      source: 'contours',
      'source-layer': 'contour',
      minzoom: 11,
      filter: ['==', ['%', ['get', 'Ele'], 200], 0],
      layout: {
        'symbol-placement': 'line',
        'symbol-spacing': 350,
        'text-field': contourText(units),
        'text-font': [fonts.italic],
        'text-size': 10,
        // Contours traced from a 30 m model wiggle; a strict angle limit leaves almost nowhere to put a label.
        'text-max-angle': 80,
        'text-padding': 4,
      },
      paint: { 'text-color': p.contour, 'text-halo-color': p.paperShown, 'text-halo-width': 1.5 },
    },
    passLabel(p),
    {
      id: 'mountain-glyph',
      type: 'symbol',
      source: 'glyphs',
      // Large glyphs from zoom 6, medium from 7, small from 9: below zoom 10 the Imhof tint has no line work,
      // so the glyphs carry the relief there.
      filter: [
        'all',
        ['!', namedPass],
        ['any', ['==', ['get', 'size'], 'large'], ['all', ['==', ['get', 'size'], 'medium'], ['>=', ['zoom'], 7]], ['>=', ['zoom'], 9]],
      ],
      layout: {
        // <landform>-<nn>[-flip], from art/glyphs/make_glyphs.py.
        'icon-image': [
          'concat', ['coalesce', ['get', 'landform'], 'peak'], '-',
          ['case', ['<', ['get', 'glyph'], 10], '0', ''], ['to-string', ['get', 'glyph']],
          ['case', ['get', 'flip'], '-flip', ''],
        ],
        // A fifth smaller up to zoom 8, so more glyphs pass collision where they first appear.
        'icon-size': ['interpolate', ['linear'], ['zoom'], 8, ['*', 0.8, size], 10, size],
        'icon-rotate': ['get', 'glyph_rotate'],
        'icon-anchor': 'bottom',
        'icon-padding': 2,
        // Biggest peaks win collisions; unknown prominence (the highest summits) sorts first. Passes come after
        // every summit, named before unnamed, each by the prominence of the summit whose key col it is.
        'symbol-sort-key': ['case', ['==', ['get', 'landform'], 'pass'],
          ['-', ['case', ['==', ['get', 'name'], 'Unnamed pass'], 200000, 100000], ['get', 'prominence_m']],
          ['-', 0, ['coalesce', ['get', 'prominence_m'], 99999]]],
        'text-field': glyphText(units),
        'text-font': [fonts.italic],
        'text-size': ['case', namedGlyph, 12, typeScale.spot],
        'text-anchor': 'top',
        'text-optional': true,
      },
      paint: { 'text-color': p.ink, 'text-opacity': 0.8, 'text-halo-color': p.paper, 'text-halo-width': 1.2 },
    },
  ]
}

// Landform names along each landform's long axis (data/landforms.geojson, decision 0023), in spaced roman capitals
// as the Wheeler sheets letter TRINIDAD MESA or PELONCILLO RANGE, spread over about 80% of the axis at every zoom.
// Each capital is taken as 0.8 em wide. Where the axis is short for the name at full size, the type shrinks (to
// 9 px) before the letters close up to 0.15 em; past that MapLibre drops the label. Spacing tops out at 4 em.
// Landforms the book names show from zoom 7, the gazetteer's from 10 (mesas from 10 too). The layer draws just over
// the glyphs, so a long name is placed first and a glyph's optional text gives way to it.
const LANDFORM_SIZE: Record<string, [number, number]> = { range: [12, 17], valley: [11, 15], plain: [11, 15], plateau: [11, 15], mesa: [10, 13] }
function landformLabel(p: Palette): LayerSpecification {
  const capEm = 0.8
  const fill = 0.8
  const zooms = [6, 7, 8, 9, 10, 11, 12, 13]
  const size = (kind: string, z: number) => {
    const [a, b] = LANDFORM_SIZE[kind]
    return a + ((b - a) * Math.min(Math.max(z - 7, 0), 5)) / 5
  }
  const chars: ExpressionSpecification = ['length', ['get', 'name']]
  // MapLibre's zoom 0 is one 512 px tile, so metres per pixel at zoom z = mpp0 / 2 / 2^z (mpp0 is for 256 px tiles).
  const room = (z: number): ExpressionSpecification => ['*', fill, ['/', ['get', 'len_m'], ['/', ['get', 'mpp0'], 2 * 2 ** z]]]
  const sizeAt = (z: number): ExpressionSpecification => ['max', 9, ['min',
    ['match', ['get', 'kind'], ...Object.keys(LANDFORM_SIZE).flatMap((k) => [k, size(k, z)]), 12],
    ['/', room(z), ['*', chars, capEm + 0.15]]]] as unknown as ExpressionSpecification
  const spacingAt = (z: number): ExpressionSpecification => ['max', 0.15, ['min', 4,
    ['/', ['-', ['/', room(z), sizeAt(z)], ['*', capEm, chars]], ['max', 1, ['-', chars, 1]]]]]
  const named: ExpressionSpecification = ['!=', ['get', 'place_ref'], null]
  return {
    id: 'landform-label',
    type: 'symbol',
    source: 'landforms',
    minzoom: 7,
    filter: ['any', ['all', named, ['!=', ['get', 'kind'], 'mesa']], ['>=', ['zoom'], 10]],
    layout: {
      'symbol-placement': 'line-center',
      'text-field': ['upcase', ['get', 'name']],
      'text-font': [fonts.roman],
      'text-size': ['interpolate', ['linear'], ['zoom'], ...zooms.flatMap((z) => [z, sizeAt(z)])] as ExpressionSpecification,
      'text-letter-spacing': ['interpolate', ['linear'], ['zoom'], ...zooms.flatMap((z) => [z, spacingAt(z)])] as ExpressionSpecification,
      'text-max-angle': 60,
      'text-keep-upright': true,
      'text-padding': 4,
    },
    // A wider halo than other labels: the names cross the densest hachures.
    paint: { 'text-color': p.ink, 'text-opacity': 0.78, 'text-halo-color': p.paper, 'text-halo-width': 1.5 },
  }
}

// Vignettes (design section 10): drawings of the book's creatures, buildings and objects, from data/vignettes.geojson
// and the vignette-<id> drawings in the sprite, each with its short italic label under it. Each point is on the thing
// the drawing stands for, and the drawing is set beside it on its `side`, a fixed gap away in screen space, so it
// sits next to its pin at every zoom and never covers it. Each shows only in its own zoom range; its caption gives way
// to other labels, the lowest `priority` placed first. The layer is in PROGRESS_LAYERS
// (spoiler/filter.ts), so each vignette shows from its own first_seen.
// crossing.build_vignettes picks each side and min_zoom from these sizes: change them there too.
const VIGNETTE_HALF = 48 // half the 96 px drawing grid
const VIGNETTE_GAP = 16 // between the pin and the drawing's nearest edge, in drawing pixels
const VIGNETTE_SIZE: [number, number][] = [[6, 0.52], [9, 0.72], [12, 0.91]] // zoom, icon-size
const VIGNETTE_TEXT: [number, number][] = [[6, 12.5], [9, 13.3], [12, 14.5]] // zoom, text-size
// Each side: the icon anchor that puts the drawing on that side of the point, and the unit step towards it.
const SIDES: Record<string, { anchor: string; dx: number; dy: number }> = {
  n: { anchor: 'bottom', dx: 0, dy: -1 },
  ne: { anchor: 'bottom-left', dx: Math.SQRT1_2, dy: -Math.SQRT1_2 },
  e: { anchor: 'left', dx: 1, dy: 0 },
  se: { anchor: 'top-left', dx: Math.SQRT1_2, dy: Math.SQRT1_2 },
  s: { anchor: 'top', dx: 0, dy: 1 },
  sw: { anchor: 'top-right', dx: -Math.SQRT1_2, dy: Math.SQRT1_2 },
  w: { anchor: 'right', dx: -1, dy: 0 },
  nw: { anchor: 'bottom-right', dx: -Math.SQRT1_2, dy: -Math.SQRT1_2 },
}
// The drawings of journeys other than the one in focus, drawing and caption, are this much lighter, as their route
// lines are (StoryLayers.tsx).
const VIGNETTE_OTHER_JOURNEY = 0.6
export const VIGNETTE_LAYERS = { drawing: 'vignette', caption: 'vignette-label' }

// Full strength for the drawings of the journey in focus (each vignette's `journey`), lighter for the rest.
export function vignetteOpacity(journey: string): ExpressionSpecification {
  return ['case', ['==', ['get', 'journey'], journey], 1, VIGNETTE_OTHER_JOURNEY]
}

// Sets it on a map that draws the drawings: the main map, and in compare mode the classic underlay.
export function setVignetteOpacity(map: MaplibreMap, journey: string) {
  const opacity = vignetteOpacity(journey)
  if (map.getLayer(VIGNETTE_LAYERS.drawing)) map.setPaintProperty(VIGNETTE_LAYERS.drawing, 'icon-opacity', opacity)
  if (map.getLayer(VIGNETTE_LAYERS.caption)) map.setPaintProperty(VIGNETTE_LAYERS.caption, 'text-opacity', opacity)
}

const bySide = (f: (side: { anchor: string; dx: number; dy: number }) => unknown, fallback: unknown): ExpressionSpecification =>
  ['match', ['get', 'side'], ...Object.entries(SIDES).flatMap(([k, v]) => [k, f(v)]), fallback] as unknown as ExpressionSpecification

function vignettes(p: Palette): LayerSpecification[] {
  // A diagonal side moves the drawing's corner, not its middle, off the pin, so its centre is a half-drawing further
  // out along each axis; a straight side moves its middle edge.
  const centre = (v: { dx: number; dy: number }, size: number): [number, number] => {
    const diagonal = v.dx !== 0 && v.dy !== 0
    const reach = (d: number) => (d === 0 ? 0 : Math.sign(d) * (VIGNETTE_HALF + (diagonal ? VIGNETTE_GAP * Math.SQRT1_2 : VIGNETTE_GAP)))
    return [reach(v.dx) * size, reach(v.dy) * size]
  }
  // The label's top sits just under the drawing: its centre, plus half a drawing and 2 px, in ems of the label.
  const labelOffset = VIGNETTE_SIZE.flatMap(([z, size], k) => {
    const text = VIGNETTE_TEXT[k][1]
    return [z, bySide((v) => {
      const [x, y] = centre(v, size)
      return ['literal', [x / text, (y + VIGNETTE_HALF * size + 2) / text]]
    }, ['literal', [0, (VIGNETTE_HALF * size + 2) / text]])]
  })
  const filter: ExpressionSpecification =
    ['all', ['==', ['get', 'kind'], 'vignette'], ['>=', ['zoom'], ['get', 'min_zoom']]]
  return [
    {
      id: VIGNETTE_LAYERS.drawing,
      type: 'symbol',
      source: 'vignettes',
      filter,
      layout: {
        'icon-image': ['get', 'vignette'],
        // Drawn on a 96 px grid: about 50 px across at zoom 6, 69 px at 9 and 87 px from 12.
        'icon-size': ['interpolate', ['linear'], ['zoom'], ...VIGNETTE_SIZE.flat()] as ExpressionSpecification,
        'icon-anchor': bySide((v) => v.anchor, 'center'),
        // In drawing pixels (scaled by icon-size): the gap between the pin and the drawing, along its side.
        'icon-offset': bySide((v) => ['literal', [v.dx * VIGNETTE_GAP, v.dy * VIGNETTE_GAP]], ['literal', [0, 0]]),
        'icon-padding': 4,
        // The drawing always shows in its zoom range and blocks no other label: names draw over it.
        'icon-allow-overlap': true,
        'icon-ignore-placement': true,
        'symbol-sort-key': ['get', 'priority'],
      },
    },
    {
      // The caption, under the drawing. Its own layer, which StoryLayers moves to the top of the stack, so it is
      // placed before every other label and the others make room for it.
      id: VIGNETTE_LAYERS.caption,
      type: 'symbol',
      source: 'vignettes',
      filter,
      layout: {
        'symbol-sort-key': ['get', 'priority'],
        'text-field': ['get', 'label'],
        'text-font': [fonts.italic],
        'text-size': ['interpolate', ['linear'], ['zoom'], ...VIGNETTE_TEXT.flat()] as ExpressionSpecification,
        'text-anchor': 'top',
        'text-offset': ['interpolate', ['linear'], ['zoom'], ...labelOffset] as ExpressionSpecification,
        'text-max-width': 9,
        'text-padding': 4,
      },
      paint: { 'text-color': p.ink, 'text-halo-color': p.paper, 'text-halo-width': 1.5 },
    },
  ]
}

// S5 (decision 0016). Below zoom 10: Imhof's desert colours and chromatic hillshade, and no line work.
// Over HILLSHADE.fade (zoom 9 to 10) they fade into near-white paper and a light grey hillshade, and from 10 the contours
// and hachures draw.
const S5_SPLIT = 10

// The hillshade: one light, its colours fading over `fade` from the palette's shadeLow below to its shadeHigh
// above (today both are MapTiler Topo's colours, so only the strength fades). The lab's Hillshade section (site/lab.html) edits a superset of these
// settings; its "Copy settings" output pastes over HILLSHADE.
export type ShadeSide = { exaggeration: number; shadow: number; highlight: number }
export type Hillshade = {
  method: 'standard' | 'basic' | 'combined' | 'igor'
  // Where the light comes from, degrees clockwise from north (315: north-west), and how high it is (0 to 90; the
  // standard and igor methods ignore it). Shadow and highlight are the alpha of their colours, 0 to 1.
  direction: number
  altitude: number
  // Below the fade (zoomed out) and above it (zoomed in).
  low: ShadeSide
  high: ShadeSide
  // The zooms over which the low look (tint, chromatic shade) gives way to the high one (paper, grey shade).
  fade: [number, number]
}
// The lab's "MapTiler-like" preset (review/stage-8/lab-hillshade/; decision 0025): MapTiler Topo's own hillshade,
// the standard method with light from 335 degrees and opaque shade colours (tokens.ts). Stronger on our paper than
// on their white.
export const HILLSHADE: Hillshade = {
  method: 'standard',
  direction: 335,
  altitude: 35,
  low: { exaggeration: 0.45, shadow: 1, highlight: 1 },
  high: { exaggeration: 0.45, shadow: 1, highlight: 1 },
  fade: [9, 10],
}

export type Shade = Palette['shadeLow']
export const alphaOf = (rgba: string) => Number(/([\d.]+)\)$/.exec(rgba)?.[1] ?? 1)
export const withAlpha = (rgba: string, a: number) =>
  `rgba(${/\d+,\s*\d+,\s*\d+/.exec(rgba)?.[0] ?? '0, 0, 0'}, ${Math.round(Math.min(1, Math.max(0, a)) * 1000) / 1000})`

// The hillshade layer's paint: each value fades from the low side to the high one.
export function hillshadePaint(s: Hillshade, p: Palette): Record<string, unknown> {
  const [from, to] = s.fade
  const blend = (low: unknown, high: unknown) => ['interpolate', ['linear'], ['zoom'], from, low, to, high]
  const colour = (side: 'low' | 'high', key: keyof Shade) => {
    const c = side === 'low' ? p.shadeLow : p.shadeHigh
    // The accent (standard method only) darkens the steepest ground; it keeps its share of the shadow.
    const a = key === 'accent' ? (s[side].shadow * alphaOf(c.accent)) / alphaOf(c.shadow) : s[side][key]
    return withAlpha(c[key], a)
  }
  return {
    'hillshade-method': s.method,
    'hillshade-illumination-direction': s.direction,
    'hillshade-illumination-altitude': s.altitude,
    'hillshade-exaggeration': blend(s.low.exaggeration, s.high.exaggeration),
    'hillshade-shadow-color': blend(colour('low', 'shadow'), colour('high', 'shadow')),
    'hillshade-highlight-color': blend(colour('low', 'highlight'), colour('high', 'highlight')),
    'hillshade-accent-color': blend(colour('low', 'accent'), colour('high', 'accent')),
  }
}

const s5Blend = <T,>(low: T, high: T) => ['interpolate', ['linear'], ['zoom'], HILLSHADE.fade[0], low, HILLSHADE.fade[1], high] as never

function s5Ground(p: Palette): LayerSpecification[] {
  return [
    {
      id: 'relief-tint',
      type: 'color-relief',
      source: 'terrain',
      paint: {
        // Imhof's aerial perspective, adapted to the desert (tokens.ts).
        'color-relief-color': ['interpolate', ['linear'], ['elevation'], ...p.imhof.flat()] as ExpressionSpecification,
        'color-relief-opacity': s5Blend(0.9, 0),
      },
    },
    {
      id: 'relief-paper',
      type: 'color-relief',
      source: 'terrain',
      paint: {
        'color-relief-color': ['interpolate', ['linear'], ['elevation'], 0, p.reliefPaper[0], 3000, p.reliefPaper[1]],
        'color-relief-opacity': s5Blend(0, 0.7),
      },
    },
    { id: 'hillshade', type: 'hillshade', source: 'terrain', paint: hillshadePaint(HILLSHADE, p) } as LayerSpecification,
  ]
}

// Shade under the hachures' own light, from the north-west and 40 degrees up: 0 lit, 1 in full shade, from each
// line's Slope and Aspect. It is tuned apart from the hillshade's (HILLSHADE.altitude), which shades the ground.
const rad = Math.PI / 180
const HACHURE_LIGHT_ALTITUDE = 40
const zenith = (90 - HACHURE_LIGHT_ALTITUDE) * rad
const slopeRad: ExpressionSpecification = ['*', ['get', 'Slope'], rad]
const shade: ExpressionSpecification = ['-', 1, ['max', 0, ['min', 1, ['+', ['*', Math.cos(zenith), ['cos', slopeRad]],
  ['*', Math.sin(zenith), ['*', ['sin', slopeRad], ['cos', ['-', 315 * rad, ['*', ['get', 'Aspect'], rad]]]]]]]]]
// Between 1 - amount and 1 + 1.5 * amount: about 1 on typical ground, more on slopes facing away from the light.
const byShade = (amount: number): ExpressionSpecification => ['+', 1 - amount, ['*', amount * 2.5, shade]]

// Sepia strokes, heavier and darker on shaded slopes, steeper is wider. They fade in from zoom 10 to 13,
// and below zoom 12 only 70% of them draw (Rand is a fixed digit, 0-9). The 90 m coarse DEM gives gentler
// slopes, so coarse lines get their own slope range. In the corridor a denser set takes over from zoom 12:
// the fine strokes fade out (`out`) as the dense ones fade in (`in`) by zoom 12.6.
const FADE = {
  none: [10, 0.55, 13, 1],
  out: [10, 0.55, 12, 0.85, 12.6, 0],
  in: [12, 0, 12.6, 0.94, 13, 1],
} as const
// Contrast after the Wheeler sheets: their hachures run from a faint broken stipple on gentle ground (about 5% ink)
// to a near-solid mass on steep slopes (40 to 50%). At HACHURE_CONTRAST t, a stroke's width is scaled by 1 + t * k
// with k from -0.4 on gentle ground to +0.25 on steep, and its opacity by 1 + t * k with k from -0.6 to +0.45. Width
// grows only a little, because Wheeler's strokes darken by packing, not width.
const HACHURE_CONTRAST = 0.5
const bySlope = (slope: [number, number], gentle: number, steep: number): ExpressionSpecification =>
  ['+', 1, ['*', HACHURE_CONTRAST, ['interpolate', ['linear'], ['get', 'Slope'], slope[0], gentle, slope[1], steep]]]

function strokePaint(ink: string, slope: [number, number], copy: boolean, fade: keyof typeof FADE = 'none') {
  const w: ExpressionSpecification = ['*', 0.9, ['interpolate', ['linear'], ['get', 'Slope'], slope[0], 0.25, slope[1], 1.3], byShade(0.4),
    bySlope(slope, -0.4, 0.25)]
  const o: ExpressionSpecification = ['*', copy ? 0.4 : 1, ['min', 1, ['*', 0.65, byShade(0.6), bySlope(slope, -0.6, 0.45)]]]
  const stops = FADE[fade].flatMap((v, i) => (i % 2 ? [['min', 1, ['*', v, o]]] : [v]))
  return {
    'line-color': ink,
    'line-width': ['interpolate', ['linear'], ['zoom'], 10, ['*', 0.8, w], 13, w] as ExpressionSpecification,
    'line-opacity': ['interpolate', ['linear'], ['zoom'], ...stops] as unknown as ExpressionSpecification,
    // A faint second stroke beside each line gives it body.
    ...(copy ? { 'line-offset': 0.35 } : {}),
  }
}
const strokeFilter = (kind?: string): ExpressionSpecification => ['all',
  ...(kind ? [['==', ['get', 'kind'], kind] as ExpressionSpecification] : []),
  ['step', ['zoom'], ['<', ['get', 'Rand'], 7], 12, true]]

// Wheeler-style strokes (decision 0024; review/stage-9/wheeler-hachures/README.md): one width, Wheeler's 0.14 mm at
// zoom 11 on a 96 dpi screen (0.53 px), and one opacity. Steep ground darkens because the build packs the strokes
// closer, so the slope contrast and the hachure light above do not apply to them. They are laid out for zoom 11, so at
// zoom 10 they lie twice as close on screen: only 70% of them draw there (by Rand), a little thinner. From 12 they
// widen so they stay visible as they spread apart. The rim wedges are polygons drawn to scale.
const WHEELER_WIDTH: ExpressionSpecification = ['interpolate', ['linear'], ['zoom'], 10, 0.42, 11, 0.53, 12, 0.8, 13, 1.2]
const WHEELER_OPACITY = 0.92

// A sepia stroke layer and its faint copy.
const strokes = (p: Palette, id: string, source: string, layer: string, fade: keyof typeof FADE, minzoom = S5_SPLIT): LayerSpecification[] =>
  [false, true].map((copy) => ({
    id: copy ? `${id}-copy` : id, type: 'line', source, 'source-layer': layer, minzoom,
    filter: strokeFilter(), layout: { 'line-cap': 'round' },
    paint: strokePaint(p.hachure, layer === 'coarse' ? [5, 25] : [10, 40], copy, fade),
  }))

function wheelerLines(p: Palette): LayerSpecification[] {
  return WHEELER_PARTS.flatMap(({ source, zooms: [from, to] }, i): LayerSpecification[] => {
    const last = i === WHEELER_PARTS.length - 1
    // Each part draws only at its own zooms; the last over-zooms past its top.
    const range = { minzoom: from, ...(last ? {} : { maxzoom: to + 1 }) }
    const suffix = i ? `-${from}` : ''
    return [
      ...strokes(p, `hachure-coarse${suffix}`, source, 'coarse', 'none', from).map((l) => ({ ...l, ...range }) as LayerSpecification),
      {
        id: `hachure-wheeler${suffix}`, type: 'line', source, 'source-layer': 'hachure', ...range,
        filter: ['step', ['zoom'], ['<', ['get', 'Rand'], 7], 11, true], layout: { 'line-cap': 'round' },
        paint: { 'line-color': p.hachure, 'line-width': WHEELER_WIDTH, 'line-opacity': WHEELER_OPACITY },
      },
      // Not named hachure-*, which the labs restyle as lines.
      { id: `rim-wedge${suffix}`, type: 'fill', source, 'source-layer': 'rim', ...range, paint: { 'fill-color': p.hachure, 'fill-opacity': WHEELER_OPACITY } },
    ]
  })
}

function s5Lines(p: Palette): LayerSpecification[] {
  const hachures = HACHURE_SET === 'wheeler'
    ? wheelerLines(p)
    : [
        ...strokes(p, 'hachure-coarse', 'relief', 'coarse', 'none'),
        ...strokes(p, 'hachure-fine', 'relief', 'fine', 'out'),
        ...strokes(p, 'hachure-dense', 'relief-dense', 'dense', 'in', 12),
      ]
  return [
    {
      // Orange-brown, as on the Siegfried sheets: every 100 m below zoom 12, every 50 m from 12, heavier every 200 m.
      id: 'contour', type: 'line', source: 'contours', 'source-layer': 'contour', minzoom: S5_SPLIT,
      filter: ['step', ['zoom'], ['==', ['%', ['get', 'Ele'], 100], 0], 12, true],
      layout: { 'line-join': 'round' },
      paint: { 'line-color': p.contour, 'line-opacity': 0.45, 'line-width': ['case', ['==', ['%', ['get', 'Ele'], 200], 0], 0.8, 0.4] },
    },
    ...hachures,
  ]
}

// The relief layers in the palette; literaryStyle places each group at its depth.
export function reliefLayers(p: Palette, units: Units): {
  hillshade: LayerSpecification[]; hachures: LayerSpecification[]; glyphs: LayerSpecification[]; vignettes: LayerSpecification[]
} {
  return { hillshade: s5Ground(p), hachures: s5Lines(p), glyphs: [...glyphs(p, units), landformLabel(p)], vignettes: vignettes(p) }
}

// The Raised view (plan oblique relief): line work from oblique-<n>.pmtiles in which every point has moved north
// by its height, so ranges stand up and hide the ground behind them. It covers the corridor of the stretches
// ridden or walked in every journey (decisions 0018 and 0019); the map's layers that cannot move with the terrain are hidden by MapView.
export const RAISED_BOUNDS: [number, number, number, number] = [-109.9, 28.23, -106.66, 34.0]
export const RAISED_MIN_ZOOM = 9

// Classic base layers drawn again from the raised copies of their lines, by the `kind` in the oblique archives.
const RAISED_BASE: Record<string, string> = {
  mexico: 'mexico', 'county-line': 'county', 'state-line': 'state', 'country-line': 'country', road: 'road',
  railroad: 'railroad', 'railroad-ties': 'railroad', 'creek-label': 'stream',
}

// Each group of raised layers goes in below the classic layer named by `before`: the Mexico side under the
// paper tint, the relief under the journeys' halo, and the boundaries, water and roads over it. `classic` is the
// literary style's layers in the palette `p`.
export function raisedLayers(classic: LayerSpecification[], p: Palette): { before: string; layers: LayerSpecification[] }[] {
  const source = { source: 'oblique', 'source-layer': 'oblique' } as const
  const base = { ...source, minzoom: RAISED_MIN_ZOOM, layout: { 'line-cap': 'round', 'line-join': 'round', visibility: 'none' } } as const
  const kind = (k: string): ExpressionSpecification => ['==', ['get', 'kind'], k]
  // The classic layer's look, drawn from the raised lines of its kind.
  const copy = (id: string): LayerSpecification => {
    const layer = classic.find((l) => l.id === id) as LayerSpecification & { filter?: ExpressionSpecification; layout?: object }
    return { ...layer, ...source, id: `raised-${id}`, filter: layer.filter ? ['all', kind(RAISED_BASE[id]), layer.filter] : kind(RAISED_BASE[id]),
      layout: { ...layer.layout, visibility: 'none' } } as LayerSpecification
  }
  return [
    { before: 'relief-tint', layers: [copy('mexico')] },
    {
      before: 'contour',
      layers: [
        { ...base, id: 'raised-contour', type: 'line', filter: kind('contour'),
          paint: { 'line-color': p.contour, 'line-width': 0.4, 'line-opacity': 0.45 } },
        { ...base, id: 'raised-stroke', type: 'line', filter: strokeFilter('stroke'), paint: strokePaint(p.hachure, [10, 40], false) },
        { ...base, id: 'raised-stroke-copy', type: 'line', filter: strokeFilter('stroke'), paint: strokePaint(p.hachure, [10, 40], true) },
        // Ridgelines, heavier on higher ridges (rel: height above the ground around, metres); below zoom 12 only the higher ones.
        { ...base, id: 'raised-ridge', type: 'line',
          filter: ['all', kind('ridge'), ['step', ['zoom'], ['>=', ['get', 'rel'], 160], 12, true]],
          paint: { 'line-color': p.ink, 'line-width': ['interpolate', ['linear'], ['get', 'rel'], 100, 0.5, 300, 1.1], 'line-opacity': 0.7 } },
        { ...base, id: 'raised-crest', type: 'line', filter: kind('crest'),
          paint: { 'line-color': p.ink, 'line-width': 0.9, 'line-opacity': 0.8 } },
      ],
    },
    {
      before: 'creek-label',
      layers: [
        copy('county-line'), copy('state-line'), copy('country-line'),
        // Streams on both sides of the border, wider with Strahler order (or NHD's stand-in for it).
        { ...base, id: 'raised-stream', type: 'line', filter: kind('stream'),
          paint: { 'line-color': p.raisedStream, 'line-width': ['interpolate', ['linear'], ['get', 'ord'], 3, 0.6, 8, 2.2], 'line-opacity': 0.6 } },
        copy('road'), copy('railroad'), copy('railroad-ties'), copy('creek-label'),
      ],
    },
  ]
}
