import type { ExpressionSpecification, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { palette } from '../../map/tokens'

// The hillshade lab's settings, and how they change the classic style. The site's relief (relief.ts, decision 0016)
// has two looks either side of a zoom fade: below it a chromatic Imhof hillshade over the desert tint, above it
// a light grey hillshade over near-white paper, with the hachures and contours. Light, method and fade are shared;
// strength is set for each side.

export type Method = 'standard' | 'basic' | 'combined' | 'igor' | 'multidirectional'
export type Colours = 'site' | 'imhof' | 'grey' | 'maptiler'
// One side of the fade. Shadow and highlight are the alpha of their colours, 0 to 1.
export type Side = { exaggeration: number; shadow: number; highlight: number }
export type HillshadeSettings = {
  method: Method
  // Where the light comes from, degrees clockwise from north (315: north-west), and how high it is (0 to 90).
  direction: number
  altitude: number
  colours: Colours
  // Below the fade (zoomed out) and above it (zoomed in).
  low: Side
  high: Side
  // Multiplies every shade colour's alpha: the hillshade layer has no opacity of its own.
  opacity: number
  // The zooms over which the low look gives way to the high one.
  fade: [number, number]
  // Multiplies the hachures' opacity.
  hachures: number
}

export const METHODS: { id: Method; label: string; note: string }[] = [
  { id: 'standard', label: 'Standard', note: 'MapLibre\'s original shading. Ignores the light height.' },
  { id: 'basic', label: 'Basic', note: 'Plain sunlight on the slopes, like gdaldem\'s default.' },
  { id: 'combined', label: 'Combined', note: 'Sunlight weighted by steepness: flat ground stays clear (the site uses this).' },
  { id: 'igor', label: 'Igor', note: 'Soft, keeps the map underneath readable. Ignores the light height.' },
  { id: 'multidirectional', label: 'Several lights', note: 'Four lights fanned around the chosen direction, averaged: even, less directional.' },
]
export const usesAltitude = (m: Method) => m === 'basic' || m === 'combined' || m === 'multidirectional'

const alpha = (rgba: string) => Number(rgba.match(/[\d.]+\)$/)?.[0].slice(0, -1) ?? 1)
const rgb = (rgba: string) => rgba.match(/\d+,\s*\d+,\s*\d+/)?.[0] ?? '0, 0, 0'

// The site's hillshade today, read from its palette and relief.ts.
export const SITE: HillshadeSettings = {
  method: 'combined',
  direction: 315,
  altitude: 45,
  colours: 'site',
  low: { exaggeration: 0.65, shadow: alpha(palette.shadeLow.shadow), highlight: alpha(palette.shadeLow.highlight) },
  high: { exaggeration: 0.5, shadow: alpha(palette.shadeHigh.shadow), highlight: alpha(palette.shadeHigh.highlight) },
  opacity: 1,
  fade: [9, 10],
  hachures: 1,
}

export const PRESETS: { id: string; label: string; note: string; settings: HillshadeSettings }[] = [
  { id: 'site', label: 'Site today', note: 'What the site draws now.', settings: SITE },
  {
    id: 'maptiler',
    label: 'MapTiler-like',
    note: 'MapTiler Topo\'s own hillshade (topo-v4): the standard method, light from 335°, opaque mid-grey shadows, '
      + 'pale warm-grey highlights and a yellow accent on the steepest ground. Stronger on our paper than on their white.',
    settings: { ...SITE, method: 'standard', direction: 335, colours: 'maptiler',
      low: { exaggeration: 0.45, shadow: 1, highlight: 1 }, high: { exaggeration: 0.45, shadow: 1, highlight: 1 } },
  },
  {
    id: 'pronounced',
    label: 'Pronounced',
    note: 'The site\'s colours and method, with about twice the shadow above the fade and a lower sun.',
    settings: { ...SITE, altitude: 35,
      low: { exaggeration: 0.75, shadow: 0.6, highlight: 0.4 }, high: { exaggeration: 0.7, shadow: 0.45, highlight: 0.35 } },
  },
  {
    id: 'soft',
    label: 'Soft',
    note: 'Igor\'s method: ranges read clearly, basins and labels stay clean.',
    settings: { ...SITE, method: 'igor',
      low: { exaggeration: 0.6, shadow: 0.45, highlight: 0.25 }, high: { exaggeration: 0.55, shadow: 0.3, highlight: 0.25 } },
  },
  {
    id: 'imhof',
    label: 'Imhof-ish',
    note: 'Blue-violet shadows and warm light at every zoom, as in Imhof\'s Swiss relief, from a low north-west sun.',
    settings: { ...SITE, method: 'basic', altitude: 30, colours: 'imhof',
      low: { exaggeration: 0.7, shadow: 0.55, highlight: 0.45 }, high: { exaggeration: 0.6, shadow: 0.4, highlight: 0.4 } },
  },
  {
    id: 'shadow-only',
    label: 'Shadows only',
    note: 'No highlight on the lit slopes (the "night light" off): the paper stays its own colour, only shade is added.',
    settings: { ...SITE,
      low: { exaggeration: 0.7, shadow: 0.6, highlight: 0 }, high: { exaggeration: 0.65, shadow: 0.4, highlight: 0 } },
  },
]

type Shade = { shadow: string; highlight: string; accent: string }
// MapTiler Topo's hillshade colours (topo-v4 style): hsl(0, 0%, 50%), hsl(51, 12%, 83%) and hsl(51, 67%, 56%), opaque.
const MAPTILER: Shade = { shadow: 'rgba(128, 128, 128, 1)', highlight: 'rgba(217, 214, 206, 1)', accent: 'rgba(218, 193, 68, 1)' }
function shadeColours(colours: Colours, side: 'low' | 'high'): Shade {
  if (colours === 'maptiler') return MAPTILER
  const pick = colours === 'site' ? side : colours === 'imhof' ? 'low' : 'high'
  return pick === 'low' ? palette.shadeLow : palette.shadeHigh
}
const withAlpha = (rgba: string, a: number) => `rgba(${rgb(rgba)}, ${Math.round(Math.min(1, Math.max(0, a)) * 1000) / 1000})`

// The hillshade layer's paint for these settings: each value a zoom fade from the low side to the high one.
export function hillshadePaint(s: HillshadeSettings): Record<string, unknown> {
  const [from, to] = s.fade
  const blend = (low: unknown, high: unknown) => ['interpolate', ['linear'], ['zoom'], from, low, to, high]
  const colour = (side: 'low' | 'high', key: keyof Shade) => {
    const c = shadeColours(s.colours, side)
    // The accent (standard method only) darkens the steepest ground: the site keeps it at about a quarter of the
    // shadow; MapTiler's is opaque.
    const a = key === 'highlight' ? s[side].highlight : key === 'shadow' ? s[side].shadow : s[side].shadow * (s.colours === 'maptiler' ? 1 : 0.24)
    return withAlpha(c[key], a * s.opacity)
  }
  // Several lights: four, 45 degrees apart, centred on the chosen direction, as gdaldem -multidirectional does.
  const multi = s.method === 'multidirectional'
  const fan = (v: unknown) => (multi ? [v, v, v, v] : v)
  return {
    'hillshade-method': s.method,
    'hillshade-illumination-direction': multi ? [-90, -45, 0, 45].map((d) => (s.direction + d + 360) % 360) : s.direction,
    'hillshade-illumination-altitude': fan(s.altitude),
    'hillshade-exaggeration': blend(s.low.exaggeration, s.high.exaggeration),
    // Multiple colours cannot be interpolated by zoom, so with several lights each side's colour holds up to
    // the middle of the fade.
    'hillshade-shadow-color': multi
      ? ['step', ['zoom'], ['literal', fan(colour('low', 'shadow'))], (from + to) / 2, ['literal', fan(colour('high', 'shadow'))]]
      : blend(colour('low', 'shadow'), colour('high', 'shadow')),
    'hillshade-highlight-color': multi
      ? ['step', ['zoom'], ['literal', fan(colour('low', 'highlight'))], (from + to) / 2, ['literal', fan(colour('high', 'highlight'))]]
      : blend(colour('low', 'highlight'), colour('high', 'highlight')),
    'hillshade-accent-color': blend(colour('low', 'accent'), colour('high', 'accent')),
  }
}

// An interpolate-by-zoom expression with every output multiplied by k.
function scaleStops(e: unknown, k: number): unknown {
  if (!Array.isArray(e) || e[0] !== 'interpolate') return ['*', k, e]
  return [...e.slice(0, 3), ...e.slice(3).map((v, i) => (i % 2 ? ['*', k, v] : v))]
}

const SHARPER_FROM = 10

// The classic style with these settings: the hillshade's paint, the tint and paper fading over `fade`, the
// hachures scaled, and, with `sharper`, the hillshade drawn from the test archive of tile zoom 11-12 from map zoom 10
// (256 px tiles are sharp at one map zoom below their own: tile zoom 11 at map zoom 10).
export function applySettings(style: StyleSpecification, s: HillshadeSettings, sharper: string | null): StyleSpecification {
  const [from, to] = s.fade
  const fade = (low: number, high: number): ExpressionSpecification => ['interpolate', ['linear'], ['zoom'], from, low, to, high]
  const layers: LayerSpecification[] = []
  for (const layer of style.layers) {
    const l = { ...layer, paint: { ...('paint' in layer ? layer.paint : {}) } } as LayerSpecification & { paint: Record<string, unknown> }
    if (l.id === 'relief-tint') l.paint['color-relief-opacity'] = fade(0.9, 0)
    if (l.id === 'relief-paper') l.paint['color-relief-opacity'] = fade(0, 0.7)
    if (l.id.startsWith('hachure-')) l.paint['line-opacity'] = scaleStops(l.paint['line-opacity'], s.hachures)
    if (l.id === 'hillshade') {
      Object.assign(l.paint, hillshadePaint(s))
      if (sharper) {
        layers.push({ ...l, maxzoom: SHARPER_FROM } as LayerSpecification, { ...l, id: 'hillshade-sharper', source: 'terrain-sharper', minzoom: SHARPER_FROM } as LayerSpecification)
        continue
      }
    }
    layers.push(l)
  }
  const sources = sharper
    ? { ...style.sources, 'terrain-sharper': { type: 'raster-dem' as const, url: `pmtiles://${sharper}`, encoding: 'terrarium' as const, tileSize: 256 } }
    : style.sources
  // No transitions: a changed setting shows at once, and switching to several lights does not try to fade
  // between one colour and four.
  return { ...style, sources, layers, transition: { duration: 0, delay: 0 } }
}
