import { useEffect, useRef, type ReactNode } from 'react'
import type { Units } from '../units'
import { viewAvailable, type Basemap, type View } from './mode'
import { Switch } from './Switch'

// Compare sits between the two maps it compares: its word, after a split-frame icon.
const COMPARE_LABEL = (
  <span className="compare-label">
    <svg viewBox="0 0 18 14" width="18" height="14" aria-hidden="true">
      <rect x="1" y="1" width="16" height="12" fill="none" stroke="currentColor" strokeWidth="1.3" />
      <rect x="1" y="1" width="8" height="12" fill="currentColor" opacity="0.45" />
      <line x1="9" y1="0" x2="9" y2="14" stroke="currentColor" strokeWidth="1.6" />
    </svg>
    Compare
  </span>
)
const BASEMAPS: { id: Basemap; label: ReactNode; description: string }[] = [
  { id: 'literary', label: 'Classic', description: "This site’s own map, in ink on paper" },
  { id: 'compare', label: COMPARE_LABEL, description: 'Classic and satellite side by side: drag the line' },
  { id: 'satellite', label: 'Satellite', description: 'Satellite imagery of today, from MapTiler' },
  { id: 'topo', label: 'Topo', description: 'Roads, places and contours of today, from MapTiler' },
]
// In compare mode the two maps it compares show as paired, in a lighter way than the switch that is on.
const PAIRED: Basemap[] = ['literary', 'satellite']
const VIEWS: { id: View; label: string; description: string }[] = [
  { id: 'flat', label: 'Flat', description: 'The map seen straight down' },
  { id: 'tilted', label: 'Tilted', description: 'The terrain in 3D, tilted towards the horizon' },
  { id: 'raised', label: 'Raised', description: 'The ranges stand up, like a block diagram' },
]

type Props = {
  basemap: Basemap
  onBasemap: (basemap: Basemap) => void
  // The MapTiler basemaps refused (no key, or the quota is spent): only Classic can be chosen.
  unavailable: boolean
  view: View
  onView: (view: View) => void
  tint: boolean
  tintAvailable: boolean
  onTint: (tint: boolean) => void
  units: Units
  onUnits: (units: Units) => void
  // Whether the menu is open: MapView holds it, as opening the menu closes the layer key and the other way round.
  menuOpen: boolean
  onMenuOpen: (open: boolean) => void
}

// The map's switches, folded into one Map button top right, so the open box never sits over a stop the reader
// is looking at (the folded button is small enough for frameStops' padding to clear).
export function MapControls(props: Props) {
  const { basemap, onBasemap, unavailable, view, onView, tint, tintAvailable, onTint, units, onUnits, menuOpen, onMenuOpen: setMenuOpen } = props
  const menuBox = useRef<HTMLDivElement>(null)
  const menuButton = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!menuOpen) return
    // A click or tap outside the box closes it, as one on the map would otherwise leave it covering the map.
    const outside = (e: PointerEvent) => {
      if (!menuBox.current?.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [menuOpen, setMenuOpen])
  // Escape closes the box from anywhere inside it, and focus returns to the Map button.
  useEffect(() => {
    if (!menuOpen) return
    const box = menuBox.current
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      setMenuOpen(false)
      menuButton.current?.focus()
    }
    box?.addEventListener('keydown', onKey)
    return () => box?.removeEventListener('keydown', onKey)
  }, [menuOpen, setMenuOpen])
  const off = basemap === 'satellite' || basemap === 'topo'

  return (
    <div className="map-controls-box" ref={menuBox}>
      <button
        ref={menuButton}
        type="button"
        className="map-menu-button"
        aria-expanded={menuOpen}
        aria-controls="map-controls"
        aria-label="Map options"
        onClick={() => setMenuOpen(!menuOpen)}
      >
        <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.4">
          <path d="M10 3 L18 7 L10 11 L2 7 Z" />
          <path d="M2 10.5 L10 14.5 L18 10.5" />
          <path d="M2 14 L10 18 L18 14" />
        </svg>
        Map
      </button>
      {/* One family of switches. View and Ground hang under the basemap switch, ruled off with it, because
          they change the classic map (and View the compare mode); on Satellite and Topo they fade out. */}
      <div className="map-controls" id="map-controls" hidden={!menuOpen}>
        <div className="control-row">
          <span className="control-label" aria-hidden="true">Map</span>
          <Switch
            label="Basemap"
            options={BASEMAPS.map((b) => ({ ...b, disabled: b.id !== 'literary' && unavailable, paired: basemap === 'compare' && PAIRED.includes(b.id) }))}
            value={basemap}
            onChange={onBasemap}
          />
        </div>
        <div className="control-sub" data-off={off || undefined}>
          <div className="control-row">
            <span className="control-label" aria-hidden="true">View</span>
            <Switch
              label="View of the classic map"
              options={VIEWS.map((v) => ({ ...v, disabled: !viewAvailable(basemap, v.id) }))}
              value={view}
              onChange={onView}
              note={off ? 'For the classic map and Compare only' : undefined}
            />
          </div>
          <div className="control-row">
            <span className="control-label" aria-hidden="true">Ground</span>
            <Switch
              label="Ground of the classic map"
              options={[
                { id: 'paper', label: 'Paper', description: 'The paper colour of the map', disabled: !tintAvailable },
                { id: 'tint', label: 'Satellite tint', description: 'Faint colour from satellite imagery under the map', disabled: !tintAvailable },
              ]}
              value={tint ? 'tint' : 'paper'}
              onChange={(v) => onTint(v === 'tint')}
              note={tintAvailable ? undefined : 'For the classic map in Flat or Tilted only'}
            />
          </div>
        </div>
        <div className="control-row">
          <span className="control-label" aria-hidden="true">Units</span>
          <Switch
            label="Units"
            options={[
              { id: 'imperial', label: 'Imperial', description: 'Miles and feet', disabled: false },
              { id: 'metric', label: 'Metric', description: 'Kilometres and metres', disabled: false },
            ]}
            value={units}
            onChange={onUnits}
          />
        </div>
      </div>
    </div>
  )
}
