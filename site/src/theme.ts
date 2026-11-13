import { useCallback, useEffect, useState } from 'react'
import type { Theme } from './map/tokens'

// The reader's theme (plan 5.1): "by lamplight" when the system asks for a dark colour scheme, unless the
// reader has picked the other theme, which is remembered. The theme is set on <html> as data-theme; the
// stylesheet's colours, and so the panel, pages and dialogs, follow it.
const KEY = 'crossing-map.theme'
const dark = window.matchMedia('(prefers-color-scheme: dark)')
const system = (): Theme => (dark.matches ? 'lamplight' : 'light')

function stored(): Theme | null {
  try {
    const value = localStorage.getItem(KEY)
    return value === 'light' || value === 'lamplight' ? value : null
  } catch {
    return null
  }
}

const initialTheme = (): Theme => stored() ?? system()
// Set at import, before the first render, so the page does not flash the other theme.
document.documentElement.dataset.theme = initialTheme()

export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setThemeState] = useState(initialTheme)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])
  // With no choice stored, a change of the system's scheme changes the theme.
  useEffect(() => {
    const follow = () => {
      if (!stored()) setThemeState(system())
    }
    dark.addEventListener('change', follow)
    return () => dark.removeEventListener('change', follow)
  }, [])
  const setTheme = useCallback((next: Theme) => {
    // A choice that matches the system is not stored, so the theme follows the system again.
    try {
      if (next === system()) localStorage.removeItem(KEY)
      else localStorage.setItem(KEY, next)
    } catch {
      // Storage blocked: the choice lasts for this visit only.
    }
    setThemeState(next)
  }, [])
  return [theme, setTheme]
}
