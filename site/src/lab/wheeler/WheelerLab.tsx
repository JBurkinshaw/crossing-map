import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { closeAttribution, exposeForScripts, motion } from '../../map/setup'
import { LEARNINGS, SHEETS, type Param } from './learnings'
import { TODAY, WHEELER, wheelerStyle, type Paper, type Params } from './wheelerStyle'
import { addFrame } from './subset/frame'
import { addPlaceMarks, READING, type PlacesParams } from './subset/places'
import './wheeler.css'

// The lab section for the Wheeler Survey study (review/stage-8/wheeler/README.md): the classic map with a few
// parameters that try what the 1870s survey sheets do, and the list of what was learned from them. The map is its
// own MapLibre instance, so the section works on any page; the site's map module is not loaded here.

// Places to compare with the sheets: zoom, centre.
const PLACES: { id: string; label: string; zoom: number; center: [number, number] }[] = [
  { id: 'animas', label: 'Animas and Playas valleys', zoom: 10, center: [-108.75, 31.62] },
  { id: 'peloncillos', label: 'Peloncillos and San Simon (as on sheet 83)', zoom: 10, center: [-109.05, 32.05] },
  { id: 'hatchets', label: 'The Hatchet ranges', zoom: 10.5, center: [-108.4, 31.55] },
  { id: 'bavispe', label: 'Río Bavispe and the Pilares', zoom: 9.5, center: [-109.1, 30.4] },
  { id: 'tigre', label: 'Sierra el Tigre', zoom: 10, center: [-109.3, 30.65] },
  { id: 'babicora', label: 'Mesas by the Babícora', zoom: 11, center: [-107.5, 29.23] },
  { id: 'subset', label: 'Test area: bootheel and Bavispe', zoom: 10, center: [-109.0, 31.05] },
]

const PAPERS: { id: Paper; label: string }[] = [
  { id: 'today', label: 'Today' },
  { id: 'cream', label: 'Cream (70A)' },
  { id: 'grey', label: 'Grey (83)' },
]

const TOGGLES: { id: Exclude<keyof Params, 'contrast' | 'paper' | 'tilted' | 'places'>; label: string }[] = [
  { id: 'water', label: 'River lettering' },
  { id: 'spotHeights', label: 'Spot heights' },
  { id: 'landforms', label: 'Landform names along axis' },
  { id: 'taper', label: 'Drainage by rank' },
  { id: 'darkInk', label: 'Hachures in brown-black' },
  { id: 'roads', label: 'Historic roads (test area)' },
  { id: 'type', label: 'Type hierarchy (test area)' },
  { id: 'subsetHachures', label: 'Wheeler hachures (test area)' },
]

const PARAM_LABEL: Record<Param, string> = {
  water: 'River lettering',
  spotHeights: 'Spot heights',
  landforms: 'Landform names along axis',
  contrast: 'Hachure contrast',
  darkInk: 'Hachures in brown-black',
  taper: 'Drainage by rank',
  paper: 'Paper',
  type: 'Type hierarchy (test area)',
}

export default function WheelerLab() {
  const box = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [params, setParams] = useState<Params>(WHEELER)
  const set = <K extends keyof Params>(key: K, value: Params[K]) => setParams((p) => ({ ...p, [key]: value }))
  const setPlaces = <K extends keyof PlacesParams>(key: K, value: PlacesParams[K]) => setParams((p) => ({ ...p, places: { ...p.places, [key]: value } }))
  const frame = useRef<ReturnType<typeof addFrame> | null>(null)

  // The parameters the map was made with; later changes go through setStyle below.
  const [first] = useState(params)
  useEffect(() => {
    const m = new maplibregl.Map({
      container: box.current!,
      style: wheelerStyle(first),
      center: PLACES[0].center,
      zoom: PLACES[0].zoom,
      minZoom: 6,
      maxZoom: 13,
      maxPitch: 60,
      dragRotate: false,
      attributionControl: { compact: true },
      locale: { 'Map.Title': 'Wheeler lab map. Arrow keys pan, plus and minus zoom' },
    })
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left')
    m.addControl(new maplibregl.ScaleControl({ unit: 'imperial', maxWidth: 120 }), 'bottom-left')
    map.current = m
    addPlaceMarks(m)
    frame.current = addFrame(m)
    frame.current.show(first.places.graticule)
    closeAttribution(m)
    exposeForScripts('__wheelerMap', m)
    return () => {
      m.remove()
      map.current = null
    }
  }, [first])

  useEffect(() => {
    const m = map.current
    if (!m) return
    m.setStyle(wheelerStyle(params))
    frame.current?.show(params.places.graticule)
    const pitch = params.tilted ? 50 : 0
    if (m.getPitch() !== pitch) m.easeTo({ pitch, duration: motion(800) })
  }, [params])

  const goTo = (center: [number, number], zoom: number) => map.current?.flyTo({ center, zoom, duration: motion(1500) })
  const topics = [...new Set(LEARNINGS.map((l) => l.topic))]

  return (
    <section className="wheeler-lab" aria-labelledby="wheeler-lab-title">
      <h2 id="wheeler-lab-title">Wheeler Survey sheets: lessons for the classic map</h2>
      <p className="wheeler-intro">
        Two atlas sheets of the US Geographical Surveys West of the 100th Meridian, studied at full resolution: what they do, what our classic map does
        now, and a small set of parameters to try their devices on our own data. The scans are CC BY-NC-SA and are not reproduced here; open them from the
        catalogue links.
      </p>
      <ul className="wheeler-sheets">
        {SHEETS.map((s) => (
          <li key={s.id}>
            <a href={s.url} target="_blank" rel="noreferrer">
              Sheet {s.id}
            </a>
            : <i>{s.title}</i>, {s.date}, {s.scale}. David Rumsey Map Collection, list no. {s.list}.
          </li>
        ))}
      </ul>

      <div className="wheeler-workspace">
        <div className="wheeler-controls">
          <fieldset>
            <legend>Presets</legend>
            <div className="wheeler-row">
              <button type="button" onClick={() => setParams({ ...TODAY, tilted: params.tilted })}>
                All as today
              </button>
              <button type="button" onClick={() => setParams({ ...WHEELER, tilted: params.tilted })}>
                All Wheeler
              </button>
            </div>
          </fieldset>
          <fieldset>
            <legend>Parameters</legend>
            {TOGGLES.map((t) => (
              <label key={t.id} className="wheeler-check">
                <input type="checkbox" checked={params[t.id]} onChange={(e) => set(t.id, e.target.checked)} />
                {t.label}
              </label>
            ))}
            <label className="wheeler-range">
              Hachure contrast <span aria-hidden="true">{params.contrast === 0 ? 'today' : params.contrast.toFixed(2)}</span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.25}
                value={params.contrast}
                aria-valuetext={params.contrast === 0 ? 'as today' : `${Math.round(params.contrast * 100)}% of Wheeler's range`}
                onChange={(e) => set('contrast', Number(e.target.value))}
              />
            </label>
            <div className="wheeler-radio" role="radiogroup" aria-label="Paper">
              <span className="wheeler-radio-label">Paper</span>
              {PAPERS.map((p) => (
                <label key={p.id}>
                  <input type="radio" name="wheeler-paper" checked={params.paper === p.id} onChange={() => set('paper', p.id)} />
                  {p.label}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Test area (stage 9)</legend>
            <label className="wheeler-check">
              <input type="checkbox" checked={params.places.water} onChange={(e) => setPlaces('water', e.target.checked)} />
              Water and stations (test area)
            </label>
            <label className="wheeler-check">
              <input type="checkbox" checked={params.places.graticule} onChange={(e) => setPlaces('graticule', e.target.checked)} />
              Graticule and frame
            </label>
            <label className="wheeler-check">
              <input type="checkbox" checked={params.places.lineLabels} onChange={(e) => setPlaces('lineLabels', e.target.checked)} />
              Graticule labels on the lines
            </label>
            <label className="wheeler-range">
              Read up to{' '}
              <span aria-hidden="true">
                {params.places.reached === '0-00' ? 'not started' : params.places.reached === '9-99' ? 'the end' : params.places.reached}
              </span>
              <input
                type="range"
                min={0}
                max={READING.length - 1}
                step={1}
                value={READING.indexOf(params.places.reached)}
                aria-valuetext={params.places.reached}
                onChange={(e) => setPlaces('reached', READING[Number(e.target.value)])}
              />
            </label>
          </fieldset>
          <fieldset>
            <legend>View</legend>
            <div className="wheeler-radio" role="radiogroup" aria-label="View">
              <label>
                <input type="radio" name="wheeler-view" checked={!params.tilted} onChange={() => set('tilted', false)} />
                Flat
              </label>
              <label>
                <input type="radio" name="wheeler-view" checked={params.tilted} onChange={() => set('tilted', true)} />
                Tilted
              </label>
            </div>
          </fieldset>
          <fieldset>
            <legend>Go to</legend>
            <div className="wheeler-places">
              {PLACES.map((p) => (
                <button key={p.id} type="button" onClick={() => goTo(p.center, p.zoom)}>
                  {p.label}
                </button>
              ))}
            </div>
          </fieldset>
        </div>
        <div className="wheeler-map" ref={box} />
      </div>
      <p className="wheeler-note">
        Landform lines are a demonstration set of ranges, valleys, mesas and a plain, derived for this lab from GNIS (public domain) and GeoNames (CC BY
        4.0) names, with the axis from the gazetteer or the Copernicus DEM. The story layers are not drawn here.
      </p>

      <h3>What the sheets do, and what we could take</h3>
      {topics.map((topic) => (
        <div key={topic} className="wheeler-topic">
          <h4>{topic}</h4>
          <ul className="wheeler-cards">
            {LEARNINGS.filter((l) => l.topic === topic).map((l) => (
              <li key={l.title} className="wheeler-card">
                <h5>{l.title}</h5>
                <dl>
                  <dt>Wheeler</dt>
                  <dd>{l.wheeler}</dd>
                  <dt>Our map</dt>
                  <dd>{l.ours}</dd>
                  <dt>Proposal</dt>
                  <dd>{l.proposal}</dd>
                </dl>
                <p className="wheeler-card-foot">
                  {l.param ? <>Try it: {PARAM_LABEL[l.param]}. </> : <>Not in the lab: needs new data or a new build step. </>}
                  Seen on sheet{l.sheets.length > 1 ? 's' : ''} {l.sheets.join(' and ')}.
                </p>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  )
}
