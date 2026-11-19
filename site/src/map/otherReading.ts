import { useEffect, useState, type RefObject } from 'react'
import type { MapRef } from '@vis.gl/react-maplibre'
import type { GeoJSONSource, LngLatBoundsLike, Map as MlMap } from 'maplibre-gl'
import { OTHER_READING_EVENT, type OtherReading, type OtherReadingRequest } from '../data/openQuestions'
import type { Story } from '../data/story'
import { motion } from './setup'
import { fonts, palette, textPx } from './tokens'

// An open question's other reading, drawn as a dashed ring with its label when the reader asks for it on the
// card (decision 0063). The camera frames the stop and the ring together, so the distance between the
// two readings is plain.

const SOURCE = 'other-reading'
const LAYERS = ['other-reading-fill', 'other-reading-line', 'other-reading-label']

// A circle of `radius_km` round the centre, on a sphere: close enough at this scale.
function ring({ coordinates: [lon, lat], radius_km }: OtherReading): [number, number][] {
  const dLat = radius_km / 111.32
  const dLon = dLat / Math.cos((lat * Math.PI) / 180)
  return Array.from({ length: 65 }, (_, i) => {
    const a = (i / 64) * 2 * Math.PI
    return [lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)] as [number, number]
  })
}

function data(r: OtherReading | null): GeoJSON.FeatureCollection {
  if (!r) return { type: 'FeatureCollection', features: [] }
  const coords = ring(r)
  return {
    type: 'FeatureCollection',
    features: [
      { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [coords] } },
      { type: 'Feature', properties: { label: r.label }, geometry: { type: 'Point', coordinates: [r.coordinates[0], r.coordinates[1] - r.radius_km / 111.32] } },
    ],
  }
}

function draw(map: MlMap, r: OtherReading | null) {
  const src = map.getSource(SOURCE) as GeoJSONSource | undefined
  if (src) {
    src.setData(data(r))
    return
  }
  if (!r) return
  map.addSource(SOURCE, { type: 'geojson', data: data(r) })
  map.addLayer({ id: LAYERS[0], type: 'fill', source: SOURCE, filter: ['==', '$type', 'Polygon'], paint: { 'fill-color': palette.ink, 'fill-opacity': 0.06 } })
  map.addLayer({
    id: LAYERS[1], type: 'line', source: SOURCE, filter: ['==', '$type', 'Polygon'],
    paint: { 'line-color': palette.ink, 'line-width': 2, 'line-dasharray': [3, 2] },
  })
  map.addLayer({
    id: LAYERS[2], type: 'symbol', source: SOURCE, filter: ['==', '$type', 'Point'],
    layout: { 'text-field': ['get', 'label'], 'text-font': [fonts.italic], 'text-size': textPx(13), 'text-anchor': 'top', 'text-offset': [0, 0.4], 'text-allow-overlap': true },
    paint: { 'text-color': palette.ink, 'text-halo-color': palette.paper, 'text-halo-width': 1.5 },
  })
}

// Whether an other reading is on the map, for the key: its label, or null.
export function useOtherReadingShown(): string | null {
  const [label, setLabel] = useState<string | null>(null)
  useEffect(() => {
    const on = (e: Event) => setLabel((e as CustomEvent<OtherReadingRequest>).detail.ring?.label ?? null)
    window.addEventListener(OTHER_READING_EVENT, on)
    return () => window.removeEventListener(OTHER_READING_EVENT, on)
  }, [])
  return label
}

// Every coordinate pair in a geometry, for its bounds.
function points(g: GeoJSON.Geometry): [number, number][] {
  const out: [number, number][] = []
  const walk = (c: unknown): void => {
    if (Array.isArray(c) && typeof c[0] === 'number') out.push([c[0], c[1] as number])
    else if (Array.isArray(c)) c.forEach(walk)
  }
  if (g.type === 'GeometryCollection') g.geometries.forEach((x) => out.push(...points(x)))
  else walk(g.coordinates)
  return out
}

function boundsOf(pts: [number, number][]): LngLatBoundsLike {
  const lons = pts.map((p) => p[0])
  const lats = pts.map((p) => p[1])
  return [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]]
}

// Extra room at the bottom and right, where the title cartouche and the inset map sit over the map.
const PADDING = { top: 60, left: 60, right: 140, bottom: 200 }

export function useOtherReading(mapRef: RefObject<MapRef | null>, loaded: boolean, story: Story | null) {
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!loaded || !map || !story) return
    let current: OtherReading | null = null
    // The zoom the reader had before the ring was shown, so hiding it returns to the same view every time.
    let zoomBefore: number | null = null
    const find = (id: string) =>
      [...story.stops.features, ...story.places.features].find((f) => f.properties?.id === id)
    const onEvent = (e: Event) => {
      const { ring: next, feature, back } = (e as CustomEvent<OtherReadingRequest>).detail
      const f = find(feature)
      if (next && !current) zoomBefore = map.getZoom()
      current = next
      draw(map, current)
      if (!f) return
      const at = f.geometry.coordinates as [number, number]
      if (current) {
        // Always the same frame for a question: the feature's area (or its point) and the whole ring.
        const area = story.areas.features.find((a) => a.properties?.id === `area-${feature}`)
        const own = area ? points(area.geometry) : [at]
        map.fitBounds(boundsOf([...own, ...ring(current)]), { padding: PADDING, duration: motion(1200) })
      } else if (back) {
        map.easeTo({ center: at, zoom: zoomBefore ?? Math.max(map.getZoom(), 9), duration: motion(1200) })
        zoomBefore = null
      }
    }
    // A basemap change rebuilds the style and drops the ring: draw it again.
    const onStyle = () => draw(map, current)
    window.addEventListener(OTHER_READING_EVENT, onEvent)
    map.on('style.load', onStyle)
    return () => {
      window.removeEventListener(OTHER_READING_EVENT, onEvent)
      map.off('style.load', onStyle)
    }
  }, [mapRef, loaded, story])
}
