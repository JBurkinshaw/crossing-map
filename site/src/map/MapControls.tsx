import { useEffect, useRef, useState, type ReactNode } from 'react'
import type { Units } from '../units'
import { viewAvailable, type Basemap, type View } from './mode'
import { Switch } from './Switch'

// Compare sits between the two maps it compares, as a narrow button with a split-frame icon.
const COMPARE_ICON = (
  <svg viewBox="0 0 18 14" width="18" height="14" aria-hidden="true">
    <rect x="1" y="1" width="16" height="12" fill="none" stroke="currentColor" strokeWidth="1.3" />
    <rect x="1" y="1" width="8" height="12" fill="currentColor" opacity="0.45" />
    <line x1="9" y1="0" x2="9" y2="14" stroke="currentColor" strokeWidth="1.6" />
  </svg>
)
const BASEMAPS: { id: Basemap; label: ReactNode; title?: string; ariaLabel?: string; narrow?: boolean }[] = [
  { id: 'literary', label: 'Classic' },
  {
    id: 'compare',
    label: COMPARE_ICON,
    title: 'Compare: the classic map and satellite, side by side',
    ariaLabel: 'Compare the classic map and satellite, side by side',
    narrow: true,
  },
  { id: 'satellite', label: 'Satellite' },
  { id: 'topo', label: 'Topo', title: 'MapTiler Topo: roads, places and contours of today' },
]
// In compare mode the two maps it compares show as paired, in a lighter way than the switch that is on.
const PAIRED: Basemap[] = ['literary', 'satellite']
const VIEWS: { id: View; label: string; title: string }[] = [
  { id: 'flat', label: 'Flat', title: 'The map seen straight down' },
  { id: 'tilted', label: 'Tilted', title: 'The terrain in 3D, tilted towards the horizon' },
  { id: 'raised', label: 'Raised', title: 'A flat map on which the ranges stand up, like a block diagram' },
]

type Props = {
  phone: boolean
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
}

// The map's switches, top right. On phones they fold into one Map button, so they do not cover the map.
export function MapControls(props: Props) {
  const { phone, basemap, onBasemap, unavailable, view, onView, tint, tintAvailable, onTint, units, onUnits } = props
  const [menuOpen, setMenuOpen] = useState(false)
  const menuBox = useRef<HTMLDivElement>(null)
  const menuButton = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!phone || !menuOpen) return
    // A tap outside the menu closes it, as a tap on the map would otherwise leave it covering the map.
    const outside = (e: PointerEvent) => {
      if (!menuBox.current?.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [phone, menuOpen])
  // Escape closes the phone menu from anywhere inside it, and focus returns to the Map button.
  useEffect(() => {
    if (!phone || !menuOpen) return
    const box = menuBox.current
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      setMenuOpen(false)
      menuButton.current?.focus()
    }
    box?.addEventListener('keydown', onKey)
    return () => box?.removeEventListener('keydown', onKey)
  }, [phone, menuOpen])

  return (
    <div className="map-controls-box" ref={menuBox}>
      {phone && (
        <button
          ref={menuButton}
          type="button"
          className="map-menu-button"
          aria-expanded={menuOpen}
          aria-controls="map-controls"
          aria-label="Map options"
          onClick={() => setMenuOpen((o) => !o)}
        >
          <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.4">
            <path d="M10 3 L18 7 L10 11 L2 7 Z" />
            <path d="M2 10.5 L10 14.5 L18 10.5" />
            <path d="M2 14 L10 18 L18 14" />
          </svg>
          Map
        </button>
      )}
      {/* One family of switches. View and Ground hang under the basemap switch, ruled off with it, because
          they change the classic map (and View the compare mode); on Satellite and Topo they fade out. */}
      <div className="map-controls" id="map-controls" hidden={phone && !menuOpen}>
        <div className="control-row">
          <span className="control-label" aria-hidden="true">Map</span>
          <Switch
            label="Basemap"
            options={BASEMAPS.map((b) => ({ ...b, disabled: b.id !== 'literary' && unavailable, paired: basemap === 'compare' && PAIRED.includes(b.id) }))}
            value={basemap}
            onChange={onBasemap}
          />
        </div>
        <div className="control-sub" data-off={basemap === 'satellite' || basemap === 'topo' || undefined}>
          <div className="control-row">
            <span className="control-label" aria-hidden="true">View</span>
            <Switch
              label="View of the classic map"
              options={VIEWS.map((v) => ({ ...v, disabled: !viewAvailable(basemap, v.id) }))}
              value={view}
              onChange={onView}
            />
          </div>
          <div className="control-row">
            <span className="control-label" aria-hidden="true">Ground</span>
            <Switch
              label="Ground of the classic map"
              options={[
                { id: 'paper', label: 'Paper', title: 'The paper colour of the map', disabled: !tintAvailable },
                {
                  id: 'tint',
                  label: 'Satellite tint',
                  title: tintAvailable ? 'Faint colour from satellite imagery under the map' : 'Classic map in Flat or Tilted only',
                  disabled: !tintAvailable,
                },
              ]}
              value={tint ? 'tint' : 'paper'}
              onChange={(v) => onTint(v === 'tint')}
            />
          </div>
        </div>
        <div className="control-row">
          <span className="control-label" aria-hidden="true">Units</span>
          <Switch
            label="Units"
            options={[
              { id: 'imperial', label: 'Imperial', title: 'Miles and feet', ariaLabel: 'Imperial: miles and feet', disabled: false },
              { id: 'metric', label: 'Metric', title: 'Kilometres and metres', ariaLabel: 'Metric: kilometres and metres', disabled: false },
            ]}
            value={units}
            onChange={onUnits}
          />
        </div>
      </div>
    </div>
  )
}
