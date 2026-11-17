import { useMemo, useRef, useState } from 'react'
import type * as maplibregl from 'maplibre-gl'
import { Layer, Source, type MapRef } from '@vis.gl/react-maplibre'
import { LabMap, type LabView } from '../LabMap'
import { LANDCOVER_ARCHIVE, landcoverColour, landcoverInk } from '../../map/relief'
import { tilesBase } from '../../map/setup'
import { LAND_COVERS, palette } from '../../map/tokens'
import { dataUrl, inkPatterns, RATIO as INK_RATIO } from '../../map/landcoverInk'
import './landcover.css'

// The land cover drawn in ink (decision 0036): each class as a repeating texture over its colour, after the engraved
// land cover of the Carte générale de la Martinique (1831), which an r/mapmaking thread on "land cover hachures"
// pointed to. The wash of the site's colours under the ink can be turned down to the ink alone. Vintage map, Flat view only; the same fills would
// cover the Oblique view's shifted polygons.

const PLACES: { id: string; label: string; center: [number, number] }[] = [
  { id: 'morelos', label: 'Colonia Morelos: fields, town and the Bavispe', center: [-109.2, 30.82] },
  { id: 'sierra', label: 'Sierra de la Madera: pine and oak', center: [-109.33, 30.92] },
  { id: 'animas', label: 'Cloverdale and the Animas Valley: grass and scrub', center: [-108.98, 31.43] },
]
const ZOOMS = [10, 11.5, 13]
const START: LabView = { center: PLACES[0].center, zoom: 11.5 }
const MODES = [
  { id: 'colour', label: 'Colour only' },
  { id: 'ink', label: 'Ink textures (the site: at a 60% wash)' },
] as const
type Mode = (typeof MODES)[number]['id']
// The site mixes its tints 60% over the paper (tokens.landcover); the wash is a share of that.
const SITE_WASH = 60

const colour = landcoverColour(palette)

export default function LandcoverInkLab() {
  const [mode, setMode] = useState<Mode>('ink')
  const [wash, setWash] = useState(SITE_WASH)
  const [ready, setReady] = useState(false)
  const mapRef = useRef<MapRef | null>(null)
  const textures = useMemo(() => inkPatterns(palette.ink, palette.water), [])
  // The textures go into the map once it has loaded, and only then do the layers that use them mount.
  const onLoad = (map: maplibregl.Map) => {
    for (const { id, image } of textures) if (!map.hasImage(id)) map.addImage(id, image, { pixelRatio: INK_RATIO })
    setReady(true)
  }
  const swatches = useMemo(() => Object.fromEntries(textures.map((p) => [p.id, dataUrl(p.image)])), [textures])
  const shownWash = mode === 'colour' ? SITE_WASH : wash
  const goTo = (center: [number, number] | null, zoom: number | null) =>
    mapRef.current?.flyTo({ ...(center ? { center } : {}), ...(zoom ? { zoom } : {}), duration: 0 })

  return (
    <div className="lab-section">
      <aside className="lab-controls" aria-label="Land cover ink settings">
        <fieldset>
          <legend>Place</legend>
          <div className="lab-buttons">
            {PLACES.map((p) => <button key={p.id} type="button" onClick={() => goTo(p.center, null)}>{p.label}</button>)}
          </div>
          <div className="lab-buttons" role="group" aria-label="Zoom">
            {ZOOMS.map((z) => <button key={z} type="button" onClick={() => goTo(null, z)}>Zoom {z}</button>)}
          </div>
        </fieldset>
        <fieldset>
          <legend>Land cover</legend>
          {MODES.map((m) => (
            <label key={m.id} className="lab-check">
              <input type="radio" name="landcover-mode" checked={mode === m.id} onChange={() => setMode(m.id)} />
              {m.label}
            </label>
          ))}
          <label className="lab-slider">
            <span>Colour wash</span>
            <input type="range" min={0} max={SITE_WASH} step={5} value={shownWash} disabled={mode === 'colour'}
              onChange={(e) => setWash(Number(e.target.value))} />
            <output>{shownWash}%</output>
          </label>
          <p className="lab-note">The land cover's colours at this share over the paper: 60% is the site's, 0% the ink alone.</p>
        </fieldset>
        <fieldset>
          <legend>Key</legend>
          <ul className="ink-key">
            {LAND_COVERS.map((c) => {
              const swatch = swatches[`ink-${c.id}`]
              return (
                <li key={c.id}>
                  <span className="ink-swatch" style={{
                    backgroundColor: shownWash ? palette.landcover[c.id] : palette.paper,
                    backgroundImage: mode === 'colour' || !swatch ? 'none' : `url(${swatch})`,
                    backgroundSize: '96px',
                  }} />
                  {c.label}
                </li>
              )
            })}
          </ul>
          <p className="lab-note">
            After the engraved land cover of the <a href="https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~372081~90137794:Carte-Generale-De-La-Martinique">Carte
            générale de la Martinique</a> (1831), from an <a href="https://www.reddit.com/r/mapmaking/comments/1w1xxt1/example_of_land_cover_hachure_lines/">r/mapmaking
            thread</a>. The textures are drawn here; nothing is copied from the map.
          </p>
        </fieldset>
      </aside>
      <div className="lab-maps">
        <div className="lab-pane">
          <LabMap initialView={START} mapRef={mapRef} label="Vintage map with land cover" onLoad={onLoad}>
            {ready && (
              <Source id="landcover" type="vector" url={`pmtiles://${tilesBase}${LANDCOVER_ARCHIVE}`}>
                {/* The wash under the hillshade, as the site draws its colour; the ink above it, so the hillshade
                    does not grey it. The tints are already 60% over the paper, so the wash is their opacity. */}
                <Layer id="landcover-colour" type="fill" source-layer="landcover" beforeId="hillshade"
                  layout={{ visibility: shownWash ? 'visible' : 'none' }}
                  paint={{ 'fill-color': colour, 'fill-opacity': shownWash / SITE_WASH }} />
                <Layer id="landcover-ink" type="fill" source-layer="landcover" beforeId="contour"
                  layout={{ visibility: mode === 'colour' ? 'none' : 'visible' }} paint={{ 'fill-pattern': landcoverInk }} />
              </Source>
            )}
          </LabMap>
        </div>
      </div>
    </div>
  )
}
