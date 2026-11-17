import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import type { StyleSpecification } from 'maplibre-gl'
import type { MapRef } from '@vis.gl/react-maplibre'
import { LabMap, type LabView } from '../LabMap'
import { applySettings, METHODS, PRESETS, SITE, usesAltitude, type HillshadeSettings, type Side } from './settings'

// The MapTiler Topo map beside the vintage one: the site's own satellite/topo map component, on the same camera.
const SatelliteMap = lazy(() => import('../../map/SatelliteMap'))

// Test places: centres for the relief the owner asked to compare.
const PLACES: { id: string; label: string; center: [number, number] }[] = [
  { id: 'peloncillos', label: 'The Peloncillos', center: [-109.01, 31.6] },
  { id: 'bavispe', label: 'The Bavispe at the wolf\'s crossing', center: [-109.288, 30.0] },
  { id: 'babicora', label: 'Sierra Madre near Babícora', center: [-107.98, 29.3] },
  { id: 'animas', label: 'The Animas Valley', center: [-108.86, 31.55] },
]
const ZOOMS = [8, 10, 12]
const START: LabView = { center: PLACES[0].center, zoom: 10 }

// The local test archive of zoom 11-12 heights from Copernicus (tiles/build_terrain_hi.py), if it has been built
// into public/tiles/. Not part of any release.
const SHARPER = new URL(`${import.meta.env.BASE_URL}tiles/terrain-hi.pmtiles`, window.location.origin).href

function Slider(props: { label: string; value: number; min: number; max: number; step: number; unit?: string;
  disabled?: boolean; onChange: (v: number) => void }) {
  const { label, value, min, max, step, unit = '', disabled, onChange } = props
  return (
    <label className="lab-slider">
      <span>{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} disabled={disabled} onChange={(e) => onChange(Number(e.target.value))} />
      <output>{value}{unit}</output>
    </label>
  )
}

export default function HillshadeLab() {
  const [s, setS] = useState<HillshadeSettings>(SITE)
  const [preset, setPreset] = useState('site')
  const [sharperAvailable, setSharperAvailable] = useState(false)
  const [sharper, setSharper] = useState(false)
  const [showTopo, setShowTopo] = useState(true)
  const [topoUnavailable, setTopoUnavailable] = useState(false)
  // A refused key (the dev server's address not among its allowed origins) leaves the vintage map on its own.
  const topoShown = showTopo && !topoUnavailable
  const [loaded, setLoaded] = useState(false)
  const [zoom, setZoom] = useState(START.zoom)
  const [copied, setCopied] = useState(false)
  const mapRef = useRef<MapRef | null>(null)

  // A missing file comes back as the dev server's HTML page, so check the archive's magic bytes.
  useEffect(() => {
    fetch(SHARPER, { headers: { Range: 'bytes=0-6' } })
      .then((r) => (r.ok ? r.text() : ''))
      .then((t) => setSharperAvailable(t.startsWith('PMTiles')), () => setSharperAvailable(false))
  }, [])

  const update = (change: Partial<HillshadeSettings>) => {
    setS((old) => ({ ...old, ...change }))
    setPreset('')
  }
  const updateSide = (side: 'low' | 'high', key: keyof Side, v: number) => update({ [side]: { ...s[side], [key]: v } })
  const choose = (id: string) => {
    setS(PRESETS.find((p) => p.id === id)!.settings)
    setPreset(id)
  }
  const overrides = useCallback((style: StyleSpecification) => applySettings(style, s, sharper ? SHARPER : null), [s, sharper])
  const onUnavailable = useCallback(() => setTopoUnavailable(true), [])
  const json = JSON.stringify(s, null, 2)
  const copy = () => {
    navigator.clipboard.writeText(json).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }, () => setCopied(false))
  }
  const goTo = (center: [number, number] | null, z: number | null) => {
    const map = mapRef.current
    if (!map) return
    map.jumpTo({ ...(center ? { center } : {}), ...(z !== null ? { zoom: z } : {}) })
  }
  const side = zoom < s.fade[0] ? 'zoomed-out look' : zoom >= s.fade[1] ? 'zoomed-in look' : 'fading between the two'
  const note = PRESETS.find((p) => p.id === preset)?.note

  return (
    <div className="lab-section">
      <aside className="lab-controls" aria-label="Hillshade settings">
        <fieldset>
          <legend>Place</legend>
          <div className="lab-buttons">
            {PLACES.map((p) => (
              <button key={p.id} type="button" onClick={() => goTo(p.center, null)}>{p.label}</button>
            ))}
          </div>
          <div className="lab-buttons" role="group" aria-label="Zoom">
            {ZOOMS.map((z) => (
              <button key={z} type="button" onClick={() => goTo(null, z)}>Zoom {z}</button>
            ))}
          </div>
          <p className="lab-note" aria-live="polite">Zoom {zoom.toFixed(1)}: the {side}.</p>
        </fieldset>

        <fieldset>
          <legend>Presets</legend>
          <div className="lab-buttons">
            {PRESETS.map((p) => (
              <button key={p.id} type="button" aria-pressed={preset === p.id} onClick={() => choose(p.id)} title={p.note}>{p.label}</button>
            ))}
            <button type="button" onClick={() => choose('site')}>Reset</button>
          </div>
          {note && <p className="lab-note">{note}</p>}
        </fieldset>

        <fieldset>
          <legend>Light</legend>
          <label className="lab-select">
            <span>Method</span>
            <select value={s.method} onChange={(e) => update({ method: e.target.value as HillshadeSettings['method'] })}>
              {METHODS.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
          </label>
          <p className="lab-note">{METHODS.find((m) => m.id === s.method)?.note}</p>
          <Slider label="Light from (degrees, 315 is north-west)" value={s.direction} min={0} max={359} step={5} unit="°"
            onChange={(v) => update({ direction: v })} />
          <Slider label={usesAltitude(s.method) ? 'Light height (0 low sun, 90 overhead)' : 'Light height (not used by this method)'}
            value={s.altitude} min={5} max={85} step={5} unit="°" disabled={!usesAltitude(s.method)} onChange={(v) => update({ altitude: v })} />
          <label className="lab-select">
            <span>Shade colours</span>
            <select value={s.colours} onChange={(e) => update({ colours: e.target.value as HillshadeSettings['colours'] })}>
              <option value="site">As the site: Imhof blue zoomed out, grey zoomed in</option>
              <option value="imhof">Imhof blue and warm light at every zoom</option>
              <option value="grey">Neutral grey at every zoom</option>
              <option value="maptiler">MapTiler Topo's grey, warm grey and yellow</option>
            </select>
          </label>
        </fieldset>

        <fieldset>
          <legend>Strength</legend>
          <table className="lab-sides">
            <thead>
              <tr><th scope="col"><span className="visually-hidden">Setting</span></th><th scope="col">Zoomed out</th><th scope="col">Zoomed in</th></tr>
            </thead>
            <tbody>
              {([['exaggeration', 'Exaggeration'], ['shadow', 'Shadow'], ['highlight', 'Highlight']] as [keyof Side, string][]).map(([key, label]) => (
                <tr key={key}>
                  <th scope="row">{label}</th>
                  {(['low', 'high'] as const).map((sd) => (
                    <td key={sd}>
                      <input type="range" min={0} max={1} step={0.05} value={s[sd][key]}
                        aria-label={`${label}, ${sd === 'low' ? 'zoomed out' : 'zoomed in'}`}
                        onChange={(e) => updateSide(sd, key, Number(e.target.value))} />
                      <output>{s[sd][key].toFixed(2)}</output>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <Slider label="Overall opacity" value={s.opacity} min={0} max={1.5} step={0.05} onChange={(v) => update({ opacity: v })} />
          <Slider label="Fade starts at zoom" value={s.fade[0]} min={6} max={12} step={0.5}
            onChange={(v) => update({ fade: [v, Math.max(v + 0.5, s.fade[1])] })} />
          <Slider label="Fade ends at zoom" value={s.fade[1]} min={6.5} max={12.5} step={0.5}
            onChange={(v) => update({ fade: [Math.min(s.fade[0], v - 0.5), v] })} />
          <Slider label="Hachure opacity" value={s.hachures} min={0} max={1.5} step={0.05} onChange={(v) => update({ hachures: v })} />
        </fieldset>

        <fieldset>
          <legend>Compare</legend>
          <label className="lab-check">
            <input type="checkbox" checked={topoShown} disabled={topoUnavailable} onChange={(e) => setShowTopo(e.target.checked)} />
            MapTiler Topo beside the map
          </label>
          {topoUnavailable && (
            <p className="lab-note" role="status">
              MapTiler Topo did not load: the key does not allow this address. Add it to the key's allowed origins in MapTiler Cloud,
              or compare with Topo on the published site.
            </p>
          )}
          <label className="lab-check" title={sharperAvailable ? '' : 'Build it first: see tiles/build_terrain_hi.py'}>
            <input type="checkbox" checked={sharper} disabled={!sharperAvailable} onChange={(e) => setSharper(e.target.checked)} />
            Sharper terrain from zoom 10 (local test archive{sharperAvailable ? '' : ', not built'})
          </label>
        </fieldset>

        <fieldset>
          <legend>Settings</legend>
          <button type="button" onClick={copy}>{copied ? 'Copied' : 'Copy settings'}</button>
          <pre className="lab-json" aria-label="Settings as JSON">{json}</pre>
        </fieldset>
      </aside>

      <div className={`lab-maps${topoShown ? ' two' : ''}`}>
        <div className="lab-pane">
          <LabMap mapRef={mapRef} initialView={START} styleOverrides={overrides} label="Vintage map with these settings"
            onLoad={(map) => { setLoaded(true); setZoom(map.getZoom()) }} onMove={(map) => setZoom(map.getZoom())} />
          <span className="lab-pane-label">Vintage map</span>
        </div>
        {topoShown && (
          <div className="lab-pane">
            {loaded && (
              <Suspense fallback={null}>
                <SatelliteMap literary={mapRef} hidden={false} topo terrain={null} onUnavailable={onUnavailable} />
              </Suspense>
            )}
            <span className="lab-pane-label">MapTiler Topo</span>
          </div>
        )}
      </div>
    </div>
  )
}
