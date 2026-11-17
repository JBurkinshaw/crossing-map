import { useEffect, useMemo, useState, type RefObject } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { Map as MapLibreMap } from 'maplibre-gl'
import type { Position } from 'geojson'
import type { Story } from '../data/story'
import { journeyInks, palette as tokens, storyBounds } from './tokens'

// The overview map (docs/design.md, section 9): a small inset of the whole story region, shown once the reader
// has zoomed in, with the journeys reached so far and a box where the view is. In the Tilted view the box is
// the view's footprint on the ground. MapView leaves it out of the Oblique view, whose line work is shifted
// north and would not sit under the box.

// The land and the international border, from Natural Earth 1:10m (public domain): admin-1 polygons merged,
// and admin-0 land boundary lines, clipped to the story box and simplified to 0.03 degrees with GDAL
// (ogr2ogr, SQLite dialect: ST_SimplifyPreserveTopology(ST_Intersection(...), 0.03)). Islands under about
// 5 km across are left out.
const LAND: Position[][] = [
  [[-109.91, 27.0], [-110.29, 27.15], [-110.52, 27.29], [-110.63, 27.64], [-110.55, 27.74], [-110.61, 27.82], [-110.51, 27.87],
    [-110.85, 27.91], [-111.0, 27.96], [-111.11, 27.94], [-111.33, 28.16], [-111.45, 28.33], [-111.71, 28.46], [-111.76, 28.58],
    [-111.95, 28.76], [-111.87, 28.8], [-112.17, 28.97], [-112.17, 29.12], [-112.24, 29.32], [-112.41, 29.34], [-112.38, 29.49],
    [-112.58, 29.72], [-112.67, 29.9], [-112.75, 29.91], [-112.75, 30.19], [-112.86, 30.27], [-112.86, 30.4], [-113.0, 30.55],
    [-113.0, 36.0], [-104.0, 36.0], [-104.0, 27.0]],
  [[-113.0, 28.46], [-112.85, 28.44], [-112.87, 28.28], [-112.79, 28.2], [-112.81, 28.03], [-112.77, 27.86], [-112.6, 27.65],
    [-112.35, 27.55], [-112.2, 27.25], [-111.95, 27.09], [-112.01, 27.0], [-113.0, 27.0]],
  [[-112.27, 28.77], [-112.36, 28.76], [-112.58, 28.88], [-112.49, 28.97], [-112.46, 29.18], [-112.26, 29.25], [-112.27, 29.14],
    [-112.2, 29.02]],
]
const BORDER: Position[] = [
  [-104.0, 29.31], [-104.53, 29.67], [-104.68, 29.94], [-104.68, 30.19], [-104.85, 30.41], [-104.93, 30.61], [-105.2, 30.8],
  [-105.36, 30.85], [-105.96, 31.37], [-106.21, 31.48], [-106.36, 31.72], [-106.43, 31.76], [-108.22, 31.78], [-108.21, 31.33],
  [-111.01, 31.33], [-113.0, 31.94],
]

// The inset's width in px; its height follows from the story box in Web Mercator.
const WIDTH = 92
const [WEST, SOUTH, EAST, NORTH] = storyBounds
const mercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))
const HEIGHT = Math.round((WIDTH * (mercY(NORTH) - mercY(SOUTH))) / (((EAST - WEST) * Math.PI) / 180))
const project = ([lon, lat]: Position): [number, number] => [
  ((lon - WEST) / (EAST - WEST)) * WIDTH,
  ((mercY(NORTH) - mercY(lat)) / (mercY(NORTH) - mercY(SOUTH))) * HEIGHT,
]

// An SVG path through the points, at half-pixel precision, without repeated points.
function path(lines: Position[][], close = false): string {
  return lines
    .map((line) => {
      const pts: string[] = []
      for (const p of line) {
        const [x, y] = project(p).map((v) => Math.round(v * 2) / 2)
        const pt = `${x} ${y}`
        if (pt !== pts[pts.length - 1]) pts.push(pt)
      }
      return pts.length > 1 ? `M${pts.join('L')}${close ? 'Z' : ''}` : ''
    })
    .join('')
}

const LAND_PATH = path(LAND, true)
const BORDER_PATH = path([BORDER])

// Shown once the view spans less than this share of the region's width.
const ZOOMED_IN = 0.5
// A box narrower or shorter than this, in inset px, shows as a small square around its centre instead.
const SMALLEST = 4
const SQUARE = 6

type Props = {
  mapRef: RefObject<MapRef | null>
  // The story the map draws, already filtered to the reader's progress.
  story: Story | null
  journey: string
}

// The view's corners on the ground, in inset px, kept inside the inset's frame (less half the box's stroke), so
// a view that runs past the region's edge, or a far edge in the Tilted view, still draws as a closed box.
// Null while the view is wide enough to need no inset. MapLibre's minimum zoom keeps every view far narrower
// than the world, but a span over 180 degrees (a view across the antimeridian) would hide the box too.
function footprintOf(map: MapLibreMap): [number, number][] | null {
  // The map's own box: the canvas container has no height of its own, as the canvas inside it is positioned.
  const { clientWidth: w, clientHeight: h } = map.getContainer()
  const corners = ([[0, 0], [w, 0], [w, h], [0, h]] as [number, number][]).map((c) => map.unproject(c))
  if (corners.some((c) => !Number.isFinite(c.lng) || !Number.isFinite(c.lat))) return null
  const lons = corners.map((c) => c.lng)
  const span = Math.max(...lons) - Math.min(...lons)
  if (span >= (EAST - WEST) * ZOOMED_IN || span > 180) return null
  const clamp = (v: number, max: number) => Math.min(max - 0.75, Math.max(0.75, v))
  return corners.map((c) => {
    const [x, y] = project([c.lng, c.lat])
    return [clamp(x, WIDTH), clamp(y, HEIGHT)]
  })
}

export function OverviewInset({ mapRef, story, journey }: Props) {
  const journeyInk = journeyInks(tokens)
  const [footprint, setFootprint] = useState<[number, number][] | null>(null)

  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    let frame = 0
    const update = () => {
      frame = 0
      setFootprint(footprintOf(map))
    }
    const onMove = () => {
      if (!frame) frame = requestAnimationFrame(update)
    }
    update()
    map.on('move', onMove)
    map.on('resize', onMove)
    return () => {
      map.off('move', onMove)
      map.off('resize', onMove)
      cancelAnimationFrame(frame)
    }
  }, [mapRef])

  // The journeys reached, the one in focus drawn last and darker.
  const routes = useMemo(() => {
    const byJourney = new Map<string, Position[][]>()
    for (const f of story?.journeys.features ?? []) {
      const id = f.properties?.journey
      const g = f.geometry
      if (!id || f.properties?.kind === 'sightline') continue
      const lines = g.type === 'LineString' ? [g.coordinates] : g.type === 'MultiLineString' ? g.coordinates : []
      byJourney.set(id, [...(byJourney.get(id) ?? []), ...lines])
    }
    return [...byJourney]
      .sort(([a], [b]) => Number(a === journey) - Number(b === journey))
      .map(([id, lines]) => ({ id, d: path(lines) }))
  }, [story, journey])

  if (!footprint) return null
  // A view smaller than a few px, or one pressed flat against the frame (the view lies past the region's
  // edge), shows as a small square around its centre.
  const xs = footprint.map((p) => p[0])
  const ys = footprint.map((p) => p[1])
  const small = Math.max(...xs) - Math.min(...xs) < SMALLEST || Math.max(...ys) - Math.min(...ys) < SMALLEST
  const cx = Math.min(WIDTH - SQUARE / 2, Math.max(SQUARE / 2, (Math.max(...xs) + Math.min(...xs)) / 2))
  const cy = Math.min(HEIGHT - SQUARE / 2, Math.max(SQUARE / 2, (Math.max(...ys) + Math.min(...ys)) / 2))

  return (
    <figure className="overview" title="Where you are: the whole story region, with a box around the part the map shows now">
      <figcaption>Where you are</figcaption>
      <svg
        width={WIDTH}
        height={HEIGHT}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label="The whole story region and its journeys; the box marks the part the map shows now"
      >
        <rect width={WIDTH} height={HEIGHT} fill={tokens.water} fillOpacity={0.35} />
        <path d={LAND_PATH} fill={tokens.paper} />
        <path d={BORDER_PATH} fill="none" stroke={tokens.ink} strokeWidth={0.8} strokeDasharray="3 1.5" />
        {routes.map(({ id, d }) => (
          <path
            key={id}
            d={d}
            fill="none"
            stroke={journeyInk[id] ?? tokens.ink}
            strokeWidth={id === journey ? 1.4 : 0.8}
            strokeOpacity={id === journey ? 1 : 0.45}
            strokeLinejoin="round"
          />
        ))}
        {small ? (
          <rect x={cx - SQUARE / 2} y={cy - SQUARE / 2} width={SQUARE} height={SQUARE} fill="none" stroke={tokens.ink} strokeWidth={1.5} />
        ) : (
          <polygon
            points={footprint.map((p) => p.join(',')).join(' ')}
            fill={tokens.ink}
            fillOpacity={0.12}
            stroke={tokens.ink}
            strokeWidth={1.5}
            strokeLinejoin="round"
          />
        )}
      </svg>
    </figure>
  )
}
