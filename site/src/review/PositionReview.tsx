import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { Feature, FeatureCollection, Geometry, Position } from 'geojson'
import type { ExpressionSpecification, GeoJSONSource, Map as MapLibre } from 'maplibre-gl'
import { fonts, palette } from '../map/tokens'
import { parseCsv, toCsv } from './csv'
import './review.css'

// The local review of where each stop sits on its landform (review/positions/): one stop at a time, the published
// point and the other candidates on the real map, and a verdict the dev server writes to review.csv. Dev server
// only: App loads it behind import.meta.env.DEV and ?review=positions.

type Verdict = 'accept' | 'move' | 'needs-work'
type Mark = { verdict: Verdict | ''; choice: string; note: string; point: string; updated: string }
type Row = Record<string, string>
type Filter = 'all' | 'flagged' | 'unreviewed'
type Props = {
  stop?: string
  kind?: string
  label?: string
  aid?: boolean | string
  check?: string
  form_500?: string | null
  form_2000?: string | null
  saddle?: string | boolean | null
  height_m?: number | string | null
  height_pct?: number | string | null
  km?: number | string | null
}
type Candidate = { kind: string; label: string; aid: boolean; check: string; km: number | null; props: Props; at: Position | null }

const PACKET = '/__review/positions'
const STORE = 'crossing-map.review.positions'
const BLANK: Mark = { verdict: '', choice: '', note: '', point: '', updated: '' }
const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] }
// One colour per kind, brighter than any of the journeys' inks. Review aids are drawn hollow in the same colour.
const KIND_COLOURS: Record<string, string> = {
  published: palette.ink,
  gazetteer: '#0060ff',
  'gazetteer+dem': '#e400c8',
  vector: '#ff7a00',
  dem: '#00a88f',
  'dem-main-stem': '#00c853',
  'dem-divide': '#d4a017',
  'least-cost-path': '#00c2e0',
}
const KIND_LABELS: Record<string, string> = {
  published: 'Published point',
  gazetteer: 'Gazetteer',
  'gazetteer+dem': 'Gazetteer and DEM',
  vector: 'Vector (NHD)',
  dem: 'DEM',
  'dem-main-stem': 'DEM main stem',
  'dem-divide': 'DEM divide',
  'least-cost-path': 'Least-cost path',
}
const POINT_KINDS = ['published', 'gazetteer', 'gazetteer+dem', 'vector', 'dem']
const LINE_KINDS = ['dem-main-stem', 'dem-divide', 'least-cost-path']
const colourOf = (kind: string) => KIND_COLOURS[kind] ?? palette.ink
const kindColour: ExpressionSpecification = [
  'match',
  ['get', 'kind'],
  ...Object.entries(KIND_COLOURS).flat(),
  palette.ink,
] as unknown as ExpressionSpecification
const SOURCES = ['review-pos-lines', 'review-pos-points'] as const
const LAYERS = ['review-pos-lines', 'review-pos-line-points', 'review-pos-candidates', 'review-pos-published', 'review-pos-numbers'] as const

async function fetchJson<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${url}: ${r.status}`)
  return r.json() as Promise<T>
}

function loadMarks(): Record<string, Mark> {
  try {
    return JSON.parse(localStorage.getItem(STORE) ?? '{}') as Record<string, Mark>
  } catch {
    return {}
  }
}

const pointOf = (r: Row) => `${r.lon},${r.lat}`
const isAid = (v: unknown) => v === true || v === 'true'
const isFlag = (check: string | undefined) => !!check && check.trim().toLowerCase().startsWith('flag')

function positions(g: Geometry | null | undefined): Position[] {
  if (!g) return []
  switch (g.type) {
    case 'Point':
      return [g.coordinates]
    case 'MultiPoint':
    case 'LineString':
      return g.coordinates
    case 'MultiLineString':
    case 'Polygon':
      return g.coordinates.flat()
    case 'MultiPolygon':
      return g.coordinates.flat(2)
    default:
      return []
  }
}

function formatKm(km: number | null): string {
  if (km === null || !Number.isFinite(km)) return ''
  return `${km < 1 ? km.toFixed(2) : km.toFixed(1)} km`
}

// What the landform analysis says about a candidate, in one short line.
function detail(p: Props): string {
  const parts: string[] = []
  if (p.form_500) parts.push(`${p.form_500} at 500 m`)
  if (p.form_2000) parts.push(`${p.form_2000} at 2 km`)
  if (p.saddle === true || p.saddle === 'true') parts.push('saddle')
  if (p.height_m !== null && p.height_m !== undefined && p.height_m !== '') parts.push(`${Math.round(Number(p.height_m))} m`)
  if (p.height_pct !== null && p.height_pct !== undefined && p.height_pct !== '')
    parts.push(`${Math.round(Number(p.height_pct))}% up the local relief`)
  return parts.join(' · ')
}

export default function PositionReview({ mapRef }: { mapRef: RefObject<MapRef | null> }) {
  const [rows, setRows] = useState<Row[]>([])
  const [features, setFeatures] = useState<Feature[]>([])
  const [marks, setMarks] = useState<Record<string, Mark>>(loadMarks)
  const [index, setIndex] = useState(0)
  const [filter, setFilter] = useState<Filter>('all')
  const [moving, setMoving] = useState(false)
  const [saved, setSaved] = useState<'idle' | 'saving' | 'saved' | 'failed'>('idle')
  const [failed, setFailed] = useState<string | null>(null)
  const noteRef = useRef<HTMLTextAreaElement>(null)

  // Load the packet and any verdicts already saved on disk.
  useEffect(() => {
    Promise.all([
      fetch(`${PACKET}/results.csv`).then((r) => {
        if (!r.ok) throw new Error(`${PACKET}/results.csv: ${r.status}`)
        return r.text()
      }),
      fetchJson<FeatureCollection>(`${PACKET}/candidates.geojson`).catch(() => EMPTY),
      fetch(`${PACKET}/review.csv`).then((r) => (r.ok ? r.text() : '')),
    ])
      .then(([results, candidates, review]) => {
        setRows(parseCsv(results))
        setFeatures(candidates.features)
        if (review) {
          const onDisk: Record<string, Mark> = {}
          for (const r of parseCsv(review))
            onDisk[r.id] = {
              verdict: r.verdict as Mark['verdict'],
              choice: r.choice,
              note: r.note,
              point: r.point,
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

  // A verdict counts only while the published point is where it was when the verdict was given.
  const verdictOf = useCallback(
    (r: Row): Mark['verdict'] => {
      const m = marks[r.stop]
      return m?.verdict && m.point === pointOf(r) ? m.verdict : ''
    },
    [marks],
  )

  const items = useMemo(
    () =>
      rows.filter((r) => {
        if (filter === 'flagged') return r.flagged === 'true' || isFlag(r.check)
        if (filter === 'unreviewed') return !verdictOf(r)
        return true
      }),
    [rows, filter, verdictOf],
  )
  const at = Math.min(index, Math.max(items.length - 1, 0))
  const current = items[at] as Row | undefined
  const mark = current ? marks[current.stop] : undefined
  const stale = !!current && !!mark?.verdict && mark.point !== pointOf(current)
  const verdict = current ? verdictOf(current) : ''
  const reviewed = rows.filter((r) => verdictOf(r)).length

  // The stop's candidates: the published point first, then the adopted tiers, then the review aids. Every one
  // but the published point gets a number for the m-then-digit key.
  const { published, adopted, aids, lines } = useMemo(() => {
    const own = current ? features.filter((f) => f.properties?.stop === current.stop) : []
    const toCandidate = (f: Feature): Candidate => {
      const p = (f.properties ?? {}) as Props
      const km = p.km === null || p.km === undefined || p.km === '' ? null : Number(p.km)
      return {
        kind: String(p.kind ?? ''),
        label: String(p.label ?? ''),
        aid: isAid(p.aid),
        check: String(p.check ?? ''),
        km,
        props: p,
        at: f.geometry?.type === 'Point' ? f.geometry.coordinates : null,
      }
    }
    const points = own.filter((f) => f.geometry?.type === 'Point').map(toCandidate)
    const fromPacket = points.find((c) => c.kind === 'published')
    const published: Candidate | null = current
      ? {
          kind: 'published',
          label: fromPacket?.label || current.name,
          aid: false,
          check: fromPacket?.check || current.check,
          km: 0,
          props: fromPacket?.props ?? {},
          at: [Number(current.lon), Number(current.lat)],
        }
      : null
    const rest = points.filter((c) => c.kind !== 'published')
    return {
      published,
      adopted: rest.filter((c) => !c.aid),
      aids: rest.filter((c) => c.aid),
      lines: own.filter((f) => f.geometry && f.geometry.type !== 'Point'),
    }
  }, [current, features])
  const numbered = useMemo(() => [...adopted, ...aids], [adopted, aids])

  // Save every change: to localStorage at once, and to review.csv through the dev server shortly after.
  const timer = useRef<number | undefined>(undefined)
  const save = useCallback((next: Record<string, Mark>) => {
    localStorage.setItem(STORE, JSON.stringify(next))
    setSaved('saving')
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => {
      const body = toCsv(
        ['id', 'verdict', 'choice', 'note', 'point', 'updated'],
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
    (row: Row, change: Partial<Mark>) => {
      const before = marks[row.stop] ?? BLANK
      const point = pointOf(row)
      // A stale verdict is dropped rather than carried over to the point as it is now.
      const kept = before.point === point ? before : { ...before, verdict: '' as const, choice: '' }
      const next = { ...marks, [row.stop]: { ...kept, ...change, point, updated: new Date().toISOString() } }
      setMarks(next)
      save(next)
    },
    [marks, save],
  )
  const setVerdict = useCallback(
    (v: Verdict, choice = '') => {
      if (!current) return
      const same = verdict === v && (v !== 'move' || mark?.choice === choice)
      update(current, same ? { verdict: '', choice: '' } : { verdict: v, choice: v === 'move' ? choice : '' })
    },
    [current, verdict, mark, update],
  )

  // The review layers: added once, and again whenever the map's style is replaced (Topo, Satellite).
  const draw = useCallback(
    (map: MapLibre) => {
      const pointFeatures: Feature[] = []
      if (published?.at) pointFeatures.push({ type: 'Feature', geometry: { type: 'Point', coordinates: published.at }, properties: { kind: 'published', aid: false, n: '' } })
      numbered.forEach((c, i) => {
        if (c.at) pointFeatures.push({ type: 'Feature', geometry: { type: 'Point', coordinates: c.at }, properties: { kind: c.kind, aid: c.aid, n: String(i + 1) } })
      })
      // A MultiPoint line kind (a divide traced as points) is drawn as small dots, everything else as a line.
      for (const f of lines)
        if (f.geometry.type === 'MultiPoint')
          for (const c of f.geometry.coordinates)
            pointFeatures.push({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: { kind: f.properties?.kind, line: true } })
      const data: Record<(typeof SOURCES)[number], FeatureCollection> = {
        'review-pos-lines': { type: 'FeatureCollection', features: lines.filter((f) => f.geometry.type !== 'MultiPoint') },
        'review-pos-points': { type: 'FeatureCollection', features: pointFeatures },
      }
      for (const id of SOURCES) {
        const source = map.getSource(id) as GeoJSONSource | undefined
        if (source) source.setData(data[id])
        else map.addSource(id, { type: 'geojson', data: data[id] })
      }
      if (!map.getLayer('review-pos-lines'))
        map.addLayer({
          id: 'review-pos-lines',
          type: 'line',
          source: 'review-pos-lines',
          layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': kindColour, 'line-width': 2.5, 'line-dasharray': [2, 1.5], 'line-opacity': 0.9 },
        })
      if (!map.getLayer('review-pos-line-points'))
        map.addLayer({
          id: 'review-pos-line-points',
          type: 'circle',
          source: 'review-pos-points',
          filter: ['==', ['get', 'line'], true],
          paint: { 'circle-radius': 2.5, 'circle-color': kindColour },
        })
      // The published point is a wide ink ring, under the candidates, so that it shows around the story's stop
      // marker and a candidate on the same spot still shows inside it.
      if (!map.getLayer('review-pos-published'))
        map.addLayer({
          id: 'review-pos-published',
          type: 'circle',
          source: 'review-pos-points',
          filter: ['==', ['get', 'kind'], 'published'],
          paint: {
            'circle-radius': 17,
            'circle-color': palette.ink,
            'circle-opacity': 0.12,
            'circle-stroke-color': palette.ink,
            'circle-stroke-width': 3.5,
          },
        })
      if (!map.getLayer('review-pos-candidates'))
        map.addLayer({
          id: 'review-pos-candidates',
          type: 'circle',
          source: 'review-pos-points',
          filter: ['all', ['!=', ['get', 'kind'], 'published'], ['!=', ['get', 'line'], true]],
          paint: {
            'circle-radius': 7,
            'circle-color': kindColour,
            'circle-opacity': ['case', ['==', ['get', 'aid'], true], 0, 1],
            'circle-stroke-color': ['case', ['==', ['get', 'aid'], true], kindColour, palette.paper],
            'circle-stroke-width': ['case', ['==', ['get', 'aid'], true], 2.5, 1.5],
          },
        })
      if (!map.getLayer('review-pos-numbers'))
        map.addLayer({
          id: 'review-pos-numbers',
          type: 'symbol',
          source: 'review-pos-points',
          filter: ['!=', ['get', 'n'], ''],
          layout: {
            'text-field': ['get', 'n'],
            'text-font': [fonts.roman],
            'text-size': 16,
            'text-offset': [0, -1.3],
            'text-allow-overlap': true,
            'text-ignore-placement': true,
          },
          paint: { 'text-color': kindColour, 'text-halo-color': palette.paper, 'text-halo-width': 2 },
        })
    },
    [published, numbered, lines],
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
      for (const id of LAYERS) if (map.getLayer(id)) map.removeLayer(id)
      for (const id of SOURCES) if (map.getSource(id)) map.removeSource(id)
    },
    [mapRef],
  )

  // The story's stop markers are HTML above the canvas: dimmed while reviewing, so the points under them show.
  useEffect(() => {
    document.documentElement.classList.add('reviewing-positions')
    return () => document.documentElement.classList.remove('reviewing-positions')
  }, [])

  // Frame the stop: the published point, its candidates and its lines. These change only with the stop, not on a save.
  useEffect(() => {
    if (!published?.at) return
    const pts = [published.at, ...numbered.flatMap((c) => (c.at ? [c.at] : [])), ...lines.flatMap((f) => positions(f.geometry))]
    const xs = pts.map((p) => p[0])
    const ys = pts.map((p) => p[1])
    mapRef.current?.fitBounds(
      [
        [Math.min(...xs), Math.min(...ys)],
        [Math.max(...xs), Math.max(...ys)],
      ],
      { padding: { top: 80, bottom: 150, left: 80, right: 80 }, maxZoom: 13.5, duration: 600 },
    )
  }, [published, numbered, lines, mapRef])

  const go = useCallback(
    (step: number) => {
      setMoving(false)
      setIndex(Math.min(Math.max(at + step, 0), Math.max(items.length - 1, 0)))
    },
    [at, items.length],
  )

  // Keys: arrows or j/k to move, a accept, m then a digit to move the point, n needs work, e to write a note.
  // Ignored while typing.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.isContentEditable) return
      if (e.metaKey || e.ctrlKey || e.altKey) return
      if (moving) {
        const n = Number(e.key)
        if (Number.isInteger(n) && n >= 1 && n <= numbered.length) setVerdict('move', numbered[n - 1].kind)
        if (e.key !== 'Shift') setMoving(false)
        return
      }
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === 'j') {
        e.preventDefault()
        go(1)
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp' || e.key === 'k') {
        e.preventDefault()
        go(-1)
      } else if (e.key === 'e') {
        e.preventDefault()
        noteRef.current?.focus()
      } else if (e.key === 'a') setVerdict('accept')
      else if (e.key === 'n') setVerdict('needs-work')
      else if (e.key === 'm' && numbered.length > 0) setMoving(true)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go, moving, numbered, setVerdict])

  if (failed) return <aside className="panel review">Could not load the review packet in review/positions/: {failed}</aside>
  if (!current) return <aside className="panel review">{rows.length === 0 ? 'Loading the review packet…' : 'Nothing matches this filter.'}</aside>

  // Each candidate takes two rows: its kind, distance and button, then what it is and how it checks.
  const row = (c: Candidate, n: number | null) => {
    const chosen = verdict === 'move' && mark?.choice === c.kind
    const cls = `${c.aid ? 'aid' : ''} ${chosen ? 'chosen' : ''}`
    return [
      <tr key={`${c.kind}-${n ?? 0}`} className={`${cls} first`}>
        <td className="n">{n ?? ''}</td>
        <td>
          <span className={`swatch-dot${c.aid ? ' hollow' : ''}${c.kind === 'published' ? ' published' : ''}`} style={{ color: colourOf(c.kind) }} />{' '}
          {KIND_LABELS[c.kind] ?? c.kind}
          {c.aid && <span className="aid-tag">review aid, not published</span>}
        </td>
        <td className="km">{formatKm(c.km)}</td>
        <td className="action">
          {n !== null && (
            <button type="button" className="move-here" aria-pressed={chosen} onClick={() => setVerdict('move', c.kind)}>
              Move here
            </button>
          )}
        </td>
      </tr>,
      <tr key={`${c.kind}-${n ?? 0}-about`} className={`${cls} about`}>
        <td colSpan={4}>
          {c.label}
          {detail(c.props) && <span className="meta detail">{detail(c.props)}</span>}
          <span className={`check ${isFlag(c.check) ? 'flagged' : 'ok'}`}>Check: {c.check || 'none'}</span>
        </td>
      </tr>,
    ]
  }
  const head = (
    <tr>
      <th scope="col">#</th>
      <th scope="col">Kind, label and check</th>
      <th scope="col">From published</th>
      <th scope="col">
        <span className="visually-hidden">Verdict</span>
      </th>
    </tr>
  )
  const legendKinds = [...new Set([...numbered.map((c) => c.kind), ...lines.map((f) => String(f.properties?.kind ?? ''))])]

  return (
    <aside className="panel review" aria-label="Review: stop positions">
      <header className="review-head">
        <h2>Review: stop positions</h2>
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
          <button type="button" onClick={() => go(-1)} disabled={at === 0}>
            ← Back
          </button>
          <span>
            {at + 1} of {items.length}
          </span>
          <button type="button" onClick={() => go(1)} disabled={at >= items.length - 1}>
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
            <option value="all">every stop</option>
            <option value="flagged">flagged stops</option>
            <option value="unreviewed">stops not yet reviewed</option>
          </select>
        </label>
      </header>

      <section className="review-item">
        <h3>
          {current.journey} stop {current.seq}: {current.name}
        </h3>
        <p className="meta">
          <span className="status">{current.position}</span> · {current.candidates || '0'} candidates · <code>{current.stop}</code>
        </p>
        {current.note && <p>{current.note}</p>}
        <p className={isFlag(current.check) ? 'flags' : 'check-ok'}>Published point: {current.check || 'not checked'}</p>
        {stale && (
          <p className="stale">
            The point has moved since the verdict “{mark?.verdict}
            {mark?.choice ? ` to ${mark.choice}` : ''}” ({mark?.point}), so it counts as not yet reviewed.
          </p>
        )}

        <div className="verdicts" role="group" aria-label="Verdict">
          <button type="button" className="verdict verdict-accept" aria-pressed={verdict === 'accept'} onClick={() => setVerdict('accept')}>
            Accept <kbd>a</kbd>
          </button>
          <button
            type="button"
            className="verdict verdict-move"
            aria-pressed={verdict === 'move' || moving}
            disabled={numbered.length === 0}
            onClick={() => setMoving((m) => !m)}
          >
            {verdict === 'move' && !moving ? `Move to ${mark?.choice}` : 'Move'} <kbd>m</kbd>
          </button>
          <button type="button" className="verdict verdict-needs-work" aria-pressed={verdict === 'needs-work'} onClick={() => setVerdict('needs-work')}>
            Needs work <kbd>n</kbd>
          </button>
        </div>
        {moving && <p className="meta moving">Move to which candidate? Press 1 to {numbered.length}, or click “Move here”. Any other key cancels.</p>}
        <label className="note">
          Note <kbd>e</kbd>
          <textarea
            ref={noteRef}
            rows={3}
            value={mark?.note ?? ''}
            onChange={(e) => update(current, { note: e.target.value })}
            onKeyDown={(e) => e.key === 'Escape' && e.currentTarget.blur()}
          />
        </label>

        <table className="candidates">
          <thead>{head}</thead>
          <tbody>
            <tr className="group">
              <th colSpan={4} scope="rowgroup">
                Published and adopted tiers
              </th>
            </tr>
            {published && row(published, null)}
            {adopted.map((c, i) => row(c, i + 1))}
          </tbody>
          {aids.length > 0 && (
            <tbody className="aids">
              <tr className="group">
                <th colSpan={4} scope="rowgroup">
                  Review aids, not published
                </th>
              </tr>
              {aids.map((c, i) => row(c, adopted.length + i + 1))}
            </tbody>
          )}
        </table>

        <div className="review-legend" aria-label="On the map">
          <h4>On the map</h4>
          <p>
            <span className="swatch-dot published" style={{ color: palette.ink }} /> Published point
          </p>
          {legendKinds
            .filter((k) => POINT_KINDS.includes(k))
            .map((k) => (
              <p key={k}>
                <span
                  className={`swatch-dot${numbered.filter((c) => c.kind === k).every((c) => c.aid) ? ' hollow' : ''}`}
                  style={{ color: colourOf(k) }}
                />{' '}
                {KIND_LABELS[k] ?? k}
              </p>
            ))}
          {legendKinds
            .filter((k) => LINE_KINDS.includes(k))
            .map((k) => (
              <p key={k}>
                <span className="swatch swatch-dashed" style={{ borderColor: colourOf(k) }} /> {KIND_LABELS[k] ?? k} (review aid)
              </p>
            ))}
          <p>
            <span className="swatch-dot hollow" style={{ color: palette.ink }} /> Hollow: review aid, not published
          </p>
        </div>
      </section>

      <details className="review-list">
        <summary>All stops ({items.length})</summary>
        <ol>
          {items.map((r, i) => (
            <li key={r.stop}>
              <button
                type="button"
                aria-current={i === at ? 'true' : undefined}
                onClick={() => {
                  setMoving(false)
                  setIndex(i)
                }}
              >
                <span className={`dot dot-${verdictOf(r) || 'none'}`} aria-label={verdictOf(r) || 'not reviewed'} /> {r.stop}
                {(r.flagged === 'true' || isFlag(r.check)) && ' ⚑'}
              </button>
            </li>
          ))}
        </ol>
      </details>
      <p className="meta">Keys: ← → or j k to move, a accept, m then a number to move the point, n needs work, e for a note, Esc to leave it.</p>
    </aside>
  )
}
