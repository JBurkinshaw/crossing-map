import type { ExpressionSpecification, LayerSpecification, StyleSpecification } from 'maplibre-gl'
import { HILLSHADE, hillshadePaint, type HillshadeMethod, type HillshadeSettings } from '../../map/relief'
import { palette } from '../../map/tokens'

// The hillshade lab's presets, and how its settings change the classic style. The site's relief (relief.ts, decision
// 0016) has two looks either side of a zoom fade: below it a chromatic Imhof hillshade over the desert tint, above
// it a light grey hillshade over near-white paper, with the hachures and contours. Light, method and fade are
// shared; strength is set for each side. The settings are relief.ts's HillshadeSettings, so the lab's JSON can be
// pasted over HILLSHADE there.

export type { HillshadeSettings }
export type Side = HillshadeSettings['low']

export const METHODS: { id: HillshadeMethod; label: string; note: string }[] = [
  { id: 'standard', label: 'Standard', note: 'MapLibre\'s original shading. Ignores the light height.' },
  { id: 'basic', label: 'Basic', note: 'Plain sunlight on the slopes, like gdaldem\'s default.' },
  { id: 'combined', label: 'Combined', note: 'Sunlight weighted by steepness: flat ground stays clear.' },
  { id: 'igor', label: 'Igor', note: 'Soft, keeps the map underneath readable. Ignores the light height.' },
  { id: 'multidirectional', label: 'Several lights', note: 'Four lights fanned around the chosen direction, averaged: even, less directional.' },
]
export const usesAltitude = (m: HillshadeMethod) => m === 'basic' || m === 'combined' || m === 'multidirectional'

// What the site draws now: HILLSHADE in relief.ts.
export const SITE: HillshadeSettings = HILLSHADE

export const PRESETS: { id: string; label: string; note: string; settings: HillshadeSettings }[] = [
  { id: 'site', label: 'Site today', note: 'What the site draws now (HILLSHADE in relief.ts).', settings: SITE },
  {
    id: 's5',
    label: 'S5 as built',
    note: 'The light hillshade of decision 0016, before the lab: a faint grey above zoom 10.',
    settings: { ...SITE, method: 'combined', direction: 315, altitude: 45, colours: 'site',
      low: { exaggeration: 0.65, shadow: 0.5, highlight: 0.35 }, high: { exaggeration: 0.5, shadow: 0.22, highlight: 0.3 } },
  },
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
    note: 'The S5 colours and method, with about twice the shadow above the fade and a lower sun.',
    settings: { ...SITE, method: 'combined', direction: 315, altitude: 35, colours: 'site',
      low: { exaggeration: 0.75, shadow: 0.6, highlight: 0.4 }, high: { exaggeration: 0.7, shadow: 0.45, highlight: 0.35 } },
  },
  {
    id: 'soft',
    label: 'Soft',
    note: 'Igor\'s method: ranges read clearly, basins and labels stay clean.',
    settings: { ...SITE, method: 'igor', direction: 315, colours: 'site',
      low: { exaggeration: 0.6, shadow: 0.45, highlight: 0.25 }, high: { exaggeration: 0.55, shadow: 0.3, highlight: 0.25 } },
  },
  {
    id: 'imhof',
    label: 'Imhof-ish',
    note: 'Blue-violet shadows and warm light at every zoom, as in Imhof\'s Swiss relief, from a low north-west sun.',
    settings: { ...SITE, method: 'basic', direction: 315, altitude: 30, colours: 'imhof',
      low: { exaggeration: 0.7, shadow: 0.55, highlight: 0.45 }, high: { exaggeration: 0.6, shadow: 0.4, highlight: 0.4 } },
  },
  {
    id: 'shadow-only',
    label: 'Shadows only',
    note: 'No highlight on the lit slopes (the "night light" off): the paper keeps its own colour, only shade is added.',
    settings: { ...SITE, method: 'combined', direction: 315, altitude: 45, colours: 'site',
      low: { exaggeration: 0.7, shadow: 0.6, highlight: 0 }, high: { exaggeration: 0.65, shadow: 0.4, highlight: 0 } },
  },
]

// An interpolate-by-zoom expression with every output multiplied by k.
function scaleStops(e: unknown, k: number): unknown {
  if (!Array.isArray(e) || e[0] !== 'interpolate') return ['*', k, e]
  return [...e.slice(0, 3), ...e.slice(3).map((v, i) => (i % 2 ? ['*', k, v] : v))]
}

// 256 px tiles are sharp one map zoom below their own: the test archive's tile zoom 11 at map zoom 10.
const SHARPER_FROM = 10

// The classic style with these settings: the hillshade's paint, the tint and paper fading over `fade`, the
// hachures scaled (relative to HILLSHADE, which the style was built with), and, with `sharper`, the hillshade
// drawn from the test archive of tile zoom 11-12 from map zoom 10.
export function applySettings(style: StyleSpecification, s: HillshadeSettings, sharper: string | null): StyleSpecification {
  const [from, to] = s.fade
  const fade = (low: number, high: number): ExpressionSpecification => ['interpolate', ['linear'], ['zoom'], from, low, to, high]
  const layers: LayerSpecification[] = []
  for (const layer of style.layers) {
    const l = { ...layer, paint: { ...('paint' in layer ? layer.paint : {}) } } as LayerSpecification & { paint: Record<string, unknown> }
    if (l.id === 'relief-tint') l.paint['color-relief-opacity'] = fade(0.9, 0)
    if (l.id === 'relief-paper') l.paint['color-relief-opacity'] = fade(0, 0.7)
    if (l.id.startsWith('hachure-') && s.hachures !== HILLSHADE.hachures) {
      l.paint['line-opacity'] = scaleStops(l.paint['line-opacity'], s.hachures / HILLSHADE.hachures)
    }
    if (l.id === 'hillshade') {
      Object.assign(l.paint, hillshadePaint(s, palette))
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
