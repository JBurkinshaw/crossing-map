import { useMemo, type ReactNode, type RefObject } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { StyleSpecification } from 'maplibre-gl'
import { AttributionControl, Map, NavigationControl, ScaleControl, type MapRef } from '@vis.gl/react-maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import { closeAttribution, dataBase, exposeForScripts, fontsBase, tilesBase } from '../map/setup'
import { literaryStyle } from '../map/style'
import { palette } from '../map/tokens'
import { WaterMarks } from '../map/WaterMarks'
import { reachedEpisode, useProgress } from '../spoiler/progress'
import { styleUpTo } from '../spoiler/filter'

// The lab's map: the site's vintage map, built by the same style builder from the same tiles, so whatever a
// lab section shows on it is what the site would show.

export type LabView = { center: [number, number]; zoom: number }

// Props of LabMap, for any lab section (Hillshade, Wheeler, ...):
//   styleOverrides  Optional. Gets a fresh copy of the vintage style (already filtered to the reader's progress,
//                   as on the site) and returns the style to draw; it may change the copy in place. It runs
//                   again whenever the function changes, and MapLibre applies only the difference, so keep it
//                   stable (useCallback or useMemo) and make a new one when the section's settings change.
//   initialView     Required. Where the map opens: centre [longitude, latitude] and zoom. Later moves go
//                   through mapRef (for example mapRef.current?.jumpTo(...)).
//   mapRef          Optional. A ref to the react-maplibre MapRef; mapRef.current.getMap() is the MapLibre map.
//   onLoad          Optional. Called once with the MapLibre map when its style first loads.
//   onMove          Optional. Called with the map whenever the camera moves (to show the zoom, sync a second map).
//   label           Optional. The map's accessible name (default "Vintage map").
//   children        Optional. Overlays drawn on the map: react-maplibre <Source> and <Layer>, <Marker>, <Popup>
//                   or controls. They draw above the vintage layers unless a <Layer> sets beforeId.
// The map fills its parent, which must have a size (position: relative and a height).
export type LabMapProps = {
  styleOverrides?: (style: StyleSpecification) => StyleSpecification
  initialView: LabView
  mapRef?: RefObject<MapRef | null>
  onLoad?: (map: maplibregl.Map) => void
  onMove?: (map: maplibregl.Map) => void
  label?: string
  children?: ReactNode
}

export function LabMap({ styleOverrides, initialView, mapRef, onLoad, onMove, label = 'Vintage map', children }: LabMapProps) {
  // The reader's own progress from the site (same storage): features first seen later stay hidden here too.
  const { progress } = useProgress()
  const reached = reachedEpisode(progress)
  const style = useMemo(() => {
    const base = styleUpTo(literaryStyle(tilesBase, fontsBase, dataBase, 'metric'), reached)
    return styleOverrides ? styleOverrides(base) : base
  }, [styleOverrides, reached])
  return (
    <Map
      ref={mapRef}
      mapLib={maplibregl}
      mapStyle={style}
      initialViewState={{ longitude: initialView.center[0], latitude: initialView.center[1], zoom: initialView.zoom }}
      minZoom={4}
      maxZoom={13}
      dragRotate={false}
      locale={{ 'Map.Title': `${label}. Arrow keys pan, plus and minus zoom` }}
      style={{ position: 'absolute', inset: 0 }}
      attributionControl={false}
      onLoad={(e) => {
        closeAttribution(e.target)
        onLoad?.(e.target)
        exposeForScripts('__labMap', e.target)
      }}
      onMove={(e) => onMove?.(e.target)}
    >
      <NavigationControl position="top-left" showCompass={false} />
      <ScaleControl position="bottom-left" unit="metric" maxWidth={120} />
      {/* The archives' credits, behind the (i) button as on the site. */}
      <AttributionControl position="bottom-right" compact />
      <WaterMarks palette={palette} />
      {children}
    </Map>
  )
}
