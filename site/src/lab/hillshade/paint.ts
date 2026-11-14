import { alphaOf, HILLSHADE, withAlpha, type Hillshade, type Shade } from '../../map/relief'
import type { Palette } from '../../map/tokens'

// The lab's hillshade settings: the site's (HILLSHADE in relief.ts) plus the options only the lab tries. With
// `colours: 'site'`, `opacity: 1`, `hachures: 1` and a single-light method, they draw exactly what the site draws.
export type HillshadeMethod = Hillshade['method'] | 'multidirectional'
// Which shade colours: the palette's Imhof colours below the fade and grey above it ('site'), either one at every
// zoom, or MapTiler Topo's.
export type ShadeColours = 'site' | 'imhof' | 'grey' | 'maptiler'
export type HillshadeSettings = Omit<Hillshade, 'method'> & {
  method: HillshadeMethod
  colours: ShadeColours
  // Multiplies every shade colour's alpha: a hillshade layer has no opacity of its own.
  opacity: number
  // Multiplies the hachures' opacity.
  hachures: number
}

export const SITE: HillshadeSettings = { ...HILLSHADE, colours: 'site', opacity: 1, hachures: 1 }

// MapTiler Topo's hillshade colours (its topo-v4 style): hsl(0, 0%, 50%), hsl(51, 12%, 83%), hsl(51, 67%, 56%).
const MAPTILER_SHADE: Shade = { shadow: 'rgba(128, 128, 128, 1)', highlight: 'rgba(217, 214, 206, 1)', accent: 'rgba(218, 193, 68, 1)' }

// The hillshade layer's paint for settings `s` in palette `p`: each value fades from the low side to the high one.
export function labHillshadePaint(s: HillshadeSettings, p: Palette): Record<string, unknown> {
  const [from, to] = s.fade
  const blend = (low: unknown, high: unknown) => ['interpolate', ['linear'], ['zoom'], from, low, to, high]
  const colour = (side: 'low' | 'high', key: keyof Shade) => {
    const pick = s.colours === 'site' ? side : s.colours === 'imhof' ? 'low' : 'high'
    const c = s.colours === 'maptiler' ? MAPTILER_SHADE : pick === 'low' ? p.shadeLow : p.shadeHigh
    // The accent (standard method only) darkens the steepest ground; it keeps its share of the shadow.
    const a = key === 'accent' ? (s[side].shadow * alphaOf(c.accent)) / alphaOf(c.shadow) : s[side][key]
    return withAlpha(c[key], a * s.opacity)
  }
  // Several lights: four, 45 degrees apart, around the chosen direction, as gdaldem -multidirectional does. Lists
  // of colours cannot be interpolated by zoom, so each side's colours hold up to the middle of the fade.
  const multi = s.method === 'multidirectional'
  const four = (v: unknown) => [v, v, v, v]
  const colours = (key: 'shadow' | 'highlight') => (multi
    ? ['step', ['zoom'], ['literal', four(colour('low', key))], (from + to) / 2, ['literal', four(colour('high', key))]]
    : blend(colour('low', key), colour('high', key)))
  return {
    'hillshade-method': s.method,
    'hillshade-illumination-direction': multi ? [-90, -45, 0, 45].map((d) => (s.direction + d + 360) % 360) : s.direction,
    'hillshade-illumination-altitude': multi ? four(s.altitude) : s.altitude,
    'hillshade-exaggeration': blend(s.low.exaggeration, s.high.exaggeration),
    'hillshade-shadow-color': colours('shadow'),
    'hillshade-highlight-color': colours('highlight'),
    'hillshade-accent-color': blend(colour('low', 'accent'), colour('high', 'accent')),
  }
}
