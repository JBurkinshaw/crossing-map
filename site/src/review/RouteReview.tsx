import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { Feature, FeatureCollection, Geometry, LineString, MultiLineString, Position } from 'geojson'
import type { GeoJSONSource, Map as MapLibre } from 'maplibre-gl'
import { palette } from '../map/tokens'
import { parseCsv, toCsv } from './csv'
import './review.css'

// The local review of the least-cost experiment (review/experiments/least-cost/): one leg at a time, the
// schematic curve, the modelled path and the slope-only path on the real map, with the model's numbers and
// flags, and a verdict the dev server writes to review.csv. Dev server only: App loads it behind
// import.meta.env.DEV and ?review=routes.

type Verdict = 'accept' | 'reject' | 'needs-work'
type Mark = { verdict: Verdict | ''; note: string; updated: string }
type Row = Record<string, string>
type Filter = 'all' | 'unreviewed' | 'flagged' | 'modelled'

const PACKET = '/__review/least-cost'
const DATA = `${import.meta.env.BASE_URL}data/`
const STORE = 'crossing-map.review.least-cost'
const VERDICTS: { id: Verdict; label: string; key: string }[] = [
  { id: 'accept', label: 'Accept', key: 'a' },
  { id: 'needs-work', label: 'Needs work', key: 'n' },
  { id: 'reject', label: 'Reject', key: 'r' },
]
// Drawn above the story layers, in colours the story does not use: the modelled path blue on a paper casing.
const LAYERS = [
  { id: 'review-journey', source: 'review-journey', color: palette.ink, width: 1.5, dash: [1, 2], opacity: 0.5, toggle: 'review-journey' },
  { id: 'review-schematic', source: 'review-schematic', color: palette.ink, width: 2.5, dash: [3, 2], opacity: 0.95, toggle: 'review-schematic' },
  { id: 'review-plain', source: 'review-plain', color: '#d9831f', width: 3, dash: [0.6, 1.6], opacity: 1, toggle: 'review-plain' },
  { id: 'review-modeled-casing', source: 'review-modeled', color: '#f4efe3', width: 7, dash: undefined, opacity: 0.9, toggle: 'review-modeled' },
  { id: 'review-modeled', source: 'review-modeled', color: '#0b5fd0', width: 3.5, dash: undefined, opacity: 1, toggle: 'review-modeled' },
] as const
const SOURCES = ['review-journey', 'review-schematic', 'review-plain', 'review-modeled'] as const
const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] }
const BLANK: Mark = { verdict: '', note: '', updated: '' }
// The numbers shown for each leg, from results.csv: column, label, unit.
const NUMBERS: [string, string, string][] = [
  ['straight_km', 'Straight line', 'km'],
  ['schematic_km', 'Schematic curve', 'km'],
  ['modeled_km', 'Modelled path', 'km'],
  ['detour', 'Detour (modelled / straight)', '×'],
  ['off_schematic_km', 'Furthest from the curve', 'km'],
  ['off_plain_km', 'Furthest from slope-only path', 'km'],
  ['model_h', 'Model time', 'h'],
  ['tobler_h', 'Slope-only time', 'h'],
  ['budget', 'Time the text allows', ''],
  ['climb_m', 'Climb', 'm'],
  ['max_z', 'Highest point', 'm'],
  ['stream_entries', 'River crossings', ''],
  ['on_corridor', 'Share on a named road or river', ''],
  ['passes', 'Passes near (not its own stops)', ''],
  ['res_m', 'Grid', 'm'],
]

async function fetchJson<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${url}: ${r.status}`)
  return r.json() as Promise<T>
}

function byId(fc: FeatureCollection): Map<string, Feature> {
  return new Map(fc.features.map((f) => [String(f.properties?.id), f]))
}

function coords(g: Geometry | undefined): Position[] {
  if (!g) return []
  if (g.type === 'LineString') return (g as LineString).coordinates
  if (g.type === 'MultiLineString') return (g as MultiLineString).coordinates.flat()
  return []
}

function collection(...fs: (Feature | undefined)[]): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: fs.filter((f): f is Feature => !!f),
  }
}

function loadMarks(): Record<string, Mark> {
  try {
    return JSON.parse(localStorage.getItem(STORE) ?? '{}') as Record<string, Mark>
  } catch {
    return {}
  }
}

export default function RouteReview({ mapRef }: { mapRef: RefObject<MapRef | null> }) {
  const [rows, setRows] = useState<Row[]>([])
  const [modeled, setModeled] = useState<Map<string, Feature>>(new Map())
  const [plain, setPlain] = useState<Map<string, Feature>>(new Map())
  const [schematic, setSchematic] = useState<Map<string, Feature>>(new Map())
  const [journeys, setJourneys] = useState<Feature[]>([])
  const [marks, setMarks] = useState<Record<string, Mark>>(loadMarks)
  const [index, setIndex] = useState(0)
  const [filter, setFilter] = useState<Filter>('all')
  const [shown, setShown] = useState({
    'review-schematic': true,
    'review-modeled': true,
    'review-plain': true,
    'review-journey': true,
  })
  const [saved, setSaved] = useState<'idle' | 'saving' | 'saved' | 'failed'>('idle')
  const [failed, setFailed] = useState<string | null>(null)
  const noteRef = useRef<HTMLTextAreaElement>(null)

  // Load the packet, the published route segments, and any verdicts already saved on disk.
  useEffect(() => {
    Promise.all([
      fetch(`${PACKET}/results.csv`).then((r) => r.text()),
      fetchJson<FeatureCollection>(`${PACKET}/routes-modeled.geojson`),
      fetchJson<FeatureCollection>(`${PACKET}/routes-plain.geojson`).catch(() => EMPTY),
      fetchJson<FeatureCollection>(`${DATA}journeys.geojson`),
      fetch(`${PACKET}/review.csv`).then((r) => (r.ok ? r.text() : '')),
    ])
      .then(([results, m, p, j, review]) => {
        setRows(parseCsv(results))
        setModeled(byId(m))
        setPlain(byId(p))
        setSchematic(byId(j))
        setJourneys(j.features)
        if (review) {
          const onDisk: Record<string, Mark> = {}
          for (const r of parseCsv(review))
            onDisk[r.id] = {
              verdict: r.verdict as Mark['verdict'],
              note: r.note,
              updated: r.updated,
            }
          // Whichever was changed last wins, so an unsaved local change survives a reload.
          setMarks((local) => {
            const out = { ...onDisk }
            for (const [id, m] of Object.entries(local)) if (!out[id] || m.updated > out[id].updated) out[id] = m
            return out
          })
        }
      })
      .catch((e: unknown) => setFailed(String(e)))
  }, [])

  const items = useMemo(
    () =>
      rows.filter((r) => {
        if (filter === 'unreviewed') return !marks[r.id]?.verdict
        if (filter === 'flagged') return r.flags.trim() !== ''
        if (filter === 'modelled') return modeled.has(r.id)
        return true
      }),
    [rows, filter, marks, modeled],
  )
  const current = items[Math.min(index, Math.max(items.length - 1, 0))]
  const mark = current ? marks[current.id] : undefined
  const reviewed = rows.filter((r) => marks[r.id]?.verdict).length

  // Save every change: to localStorage at once, and to review.csv through the dev server shortly after.
  const timer = useRef<number | undefined>(undefined)
  const save = useCallback((next: Record<string, Mark>) => {
    localStorage.setItem(STORE, JSON.stringify(next))
    setSaved('saving')
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => {
      const body = toCsv(
        ['id', 'verdict', 'note', 'updated'],
        Object.entries(next)
          .filter(([, m]) => m.verdict || m.note)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([id, m]) => ({ id, ...m })),
      )
      fetch(`${PACKET}/review.csv`, { method: 'PUT', body, headers: { 'Content-Type': 'text/csv' } })
        .then((r) => setSaved(r.ok ? 'saved' : 'failed'))
        .catch(() => setSaved('failed'))
    }, 400)
  }, [])
  const update = useCallback(
    (id: string, change: Partial<Mark>) => {
      const next = { ...marks, [id]: { ...(marks[id] ?? BLANK), ...change, updated: new Date().toISOString() } }
      setMarks(next)
      save(next)
    },
    [marks, save],
  )

  // The review layers: added once, and again whenever the map's style is replaced (Topo, Satellite).
  const draw = useCallback(
    (map: MapLibre) => {
      if (!current) return
      const data: Record<string, FeatureCollection> = {
        'review-journey': {
          type: 'FeatureCollection',
          features: journeys.filter((f) => f.properties?.journey === current.journey && f.properties?.id !== current.id),
        },
        'review-schematic': collection(schematic.get(current.id)),
        'review-plain': collection(plain.get(current.id)),
        'review-modeled': collection(modeled.get(current.id)),
      }
      for (const id of SOURCES) {
        const source = map.getSource(id) as GeoJSONSource | undefined
        if (source) source.setData(data[id])
        else map.addSource(id, { type: 'geojson', data: data[id] })
      }
      for (const l of LAYERS) {
        if (!map.getLayer(l.id)) {
          map.addLayer({
            id: l.id,
            type: 'line',
            source: l.source,
            layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: {
              'line-color': l.color,
              'line-width': l.width,
              'line-opacity': l.opacity,
              ...(l.dash ? { 'line-dasharray': [...l.dash] } : {}),
            },
          })
        }
        map.setLayoutProperty(l.id, 'visibility', shown[l.toggle] ? 'visible' : 'none')
      }
    },
    [current, journeys, schematic, plain, modeled, shown],
  )
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    // The style may still be loading (the first visit, or after Topo or Satellite replaces it): adding a source
    // then throws, so the draw is retried once the map is idle.
    const redraw = () => {
      try {
        draw(map)
      } catch {
        map.once('idle', redraw)
      }
    }
    redraw()
    map.on('style.load', redraw)
    return () => {
      map.off('style.load', redraw)
      map.off('idle', redraw)
    }
  }, [mapRef, draw])
  useEffect(
    () => () => {
      const map = mapRef.current?.getMap()
      if (!map?.isStyleLoaded()) return
      for (const l of LAYERS) if (map.getLayer(l.id)) map.removeLayer(l.id)
      for (const id of SOURCES) if (map.getSource(id)) map.removeSource(id)
    },
    [mapRef],
  )

  // Frame the leg: its curve and both paths.
  useEffect(() => {
    if (!current) return
    const pts = [schematic, modeled, plain].flatMap((m) => coords(m.get(current.id)?.geometry))
    if (pts.length === 0) return
    const xs = pts.map((p) => p[0])
    const ys = pts.map((p) => p[1])
    mapRef.current?.fitBounds(
      [
        [Math.min(...xs), Math.min(...ys)],
        [Math.max(...xs), Math.max(...ys)],
      ],
      { padding: { top: 80, bottom: 150, left: 80, right: 80 }, maxZoom: 13, duration: 600 },
    )
  }, [current, schematic, modeled, plain, mapRef])

  const go = useCallback((step: number) => setIndex((i) => Math.min(Math.max(i + step, 0), Math.max(items.length - 1, 0))), [items.length])

  // Keys: arrows or j/k to move, a/n/r for a verdict, e to write a note. Ignored while typing.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT' || target.tagName === 'SELECT' || e.metaKey || e.ctrlKey) return
      if (e.key === 'ArrowRight' || e.key === 'j') go(1)
      else if (e.key === 'ArrowLeft' || e.key === 'k') go(-1)
      else if (e.key === 'e') {
        e.preventDefault()
        noteRef.current?.focus()
      } else if (current) {
        const v = VERDICTS.find((x) => x.key === e.key)
        if (v) update(current.id, { verdict: mark?.verdict === v.id ? '' : v.id })
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go, current, mark, update])

  if (failed) return <aside className="panel review">Could not load the review packet: {failed}</aside>
  if (!current) return <aside className="panel review">{rows.length === 0 ? 'Loading the review packet…' : 'Nothing matches this filter.'}</aside>

  const flags = current.flags
    .split(';')
    .map((f) => f.trim())
    .filter(Boolean)
  return (
    <aside className="panel review" aria-label="Review: modelled routes">
      <header className="review-head">
        <h2>Review: modelled routes</h2>
        <p className="meta">
          {reviewed} of {rows.length} reviewed ·{' '}
          <span className={`save-${saved}`}>
            {saved === 'saving'
              ? 'saving…'
              : saved === 'saved'
                ? 'saved to review.csv'
                : saved === 'failed'
                  ? 'not saved to disk (kept in this browser)'
                  : ''}
          </span>
        </p>
        <div className="review-nav">
          <button type="button" onClick={() => go(-1)} disabled={index === 0}>
            ← Back
          </button>
          <span>
            {Math.min(index, items.length - 1) + 1} of {items.length}
          </span>
          <button type="button" onClick={() => go(1)} disabled={index >= items.length - 1}>
            Next →
          </button>
        </div>
        <label className="review-filter">
          Show{' '}
          <select
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value as Filter)
              setIndex(0)
            }}
          >
            <option value="all">every leg</option>
            <option value="modelled">modelled legs</option>
            <option value="flagged">flagged legs</option>
            <option value="unreviewed">legs not yet reviewed</option>
          </select>
        </label>
      </header>

      <section className="review-item">
        <h3>
          {current.journey} leg {Number(current.id.split('-').pop())}: {current.name}
        </h3>
        <p className="meta">
          <span className={`status status-${current.status.replace(/ /g, '-')}`}>{current.status}</span> · {current.mode || current.travel || 'horse'}{' '}
          · <code>{current.id}</code>
        </p>
        {current.why && <p>{current.why}</p>}
        {flags.length > 0 && (
          <ul className="flags">
            {flags.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        )}

        <div className="verdicts" role="group" aria-label="Verdict">
          {VERDICTS.map((v) => (
            <button
              key={v.id}
              type="button"
              className={`verdict verdict-${v.id}`}
              aria-pressed={mark?.verdict === v.id}
              onClick={() =>
                update(current.id, {
                  verdict: mark?.verdict === v.id ? '' : v.id,
                })
              }
            >
              {v.label} <kbd>{v.key}</kbd>
            </button>
          ))}
        </div>
        <label className="note">
          Note <kbd>e</kbd>
          <textarea
            ref={noteRef}
            rows={3}
            value={mark?.note ?? ''}
            onChange={(e) => update(current.id, { note: e.target.value })}
            onKeyDown={(e) => e.key === 'Escape' && e.currentTarget.blur()}
          />
        </label>

        <fieldset className="review-layers">
          <legend>On the map</legend>
          {(
            [
              ['review-modeled', 'Modelled path', 'swatch-modeled'],
              ['review-schematic', 'Schematic curve (now)', 'swatch-schematic'],
              ['review-plain', 'Slope-only path', 'swatch-plain'],
              ['review-journey', 'The rest of the journey', 'swatch-journey'],
            ] as const
          ).map(([id, label, swatch]) => (
            <label key={id}>
              <input type="checkbox" checked={shown[id]} onChange={(e) => setShown((s) => ({ ...s, [id]: e.target.checked }))} />{' '}
              <span className={`swatch ${swatch}`} /> {label}
            </label>
          ))}
        </fieldset>

        <table className="numbers">
          <tbody>
            {NUMBERS.filter(([k]) => current[k] !== undefined && current[k] !== '').map(([k, label, unit]) => (
              <tr key={k}>
                <th scope="row">{label}</th>
                <td>
                  {current[k]}
                  {unit && ` ${unit}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <details className="review-list">
        <summary>All legs ({items.length})</summary>
        <ol>
          {items.map((r, i) => (
            <li key={r.id}>
              <button type="button" aria-current={i === index ? 'true' : undefined} onClick={() => setIndex(i)}>
                <span className={`dot dot-${marks[r.id]?.verdict || 'none'}`} aria-label={marks[r.id]?.verdict || 'not reviewed'} /> {r.id}
                {r.flags.trim() && ' ⚑'}
              </button>
            </li>
          ))}
        </ol>
      </details>
      <p className="meta">Keys: ← → or j k to move, a n r for a verdict, e for a note, Esc to leave it.</p>
    </aside>
  )
}
