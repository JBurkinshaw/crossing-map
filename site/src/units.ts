import { useCallback, useState } from 'react'
import type { ExpressionSpecification } from 'maplibre-gl'

// Units for distances and heights: miles and feet, or kilometres and metres. The reader's choice is remembered;
// until then, US English browsers get imperial and everyone else metric.
export type Units = 'imperial' | 'metric'

const KEY = 'crossing-map.units'
const FEET = 3.28084
const MILE = 1609.344

function initialUnits(): Units {
  try {
    const value = localStorage.getItem(KEY)
    if (value === 'imperial' || value === 'metric') return value
  } catch {
    // Storage blocked: fall through to the browser's language.
  }
  return /-US$/i.test(navigator.language) ? 'imperial' : 'metric'
}

export function useUnits(): [Units, (units: Units) => void] {
  const [units, setState] = useState(initialUnits)
  const setUnits = useCallback((next: Units) => {
    try {
      localStorage.setItem(KEY, next)
    } catch {
      // Storage blocked: the choice lasts for this visit only.
    }
    setState(next)
  }, [])
  return [units, setUnits]
}

const trim = (n: number) => String(Math.round(n * 10) / 10)

// A distance given in metres, such as "2 km" or "1.2 mi"; under a quarter mile, in feet.
export function distance(metres: number, units: Units): string {
  if (units === 'metric') return metres < 1000 ? `${Math.round(metres)} m` : `${trim(metres / 1000)} km`
  const miles = metres / MILE
  if (miles < 0.25) return `${(Math.round((metres * FEET) / 50) * 50).toLocaleString('en-US')} ft`
  return miles < 10 ? `${trim(miles)} mi` : `${Math.round(miles)} mi`
}

// A map label for a height in metres, such as "3,275 m" or "10,745 ft", rounded to `step` in feet.
export function heightLabel(metres: ExpressionSpecification, units: Units, step = 1): ExpressionSpecification {
  const value: ExpressionSpecification =
    units === 'metric' ? metres : ['*', step, ['round', ['/', ['*', metres, FEET], step]]]
  return ['concat', ['number-format', value, { locale: 'en-US', 'max-fraction-digits': 0 }], units === 'metric' ? ' m' : ' ft']
}
