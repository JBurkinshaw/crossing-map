import { useEffect, useState } from 'react'
import { useMap } from '@vis.gl/react-maplibre'
import type { GeoJSONSource, Map as MapLibreMap } from 'maplibre-gl'

// Cluster markers (docs/plan.md, section 9) only where the map is crowded: around Cloverdale and the
// Peloncillos, where J1, J2, J3 and J7 all pass and stops sit on top of the places they stand for.
// West, south, east, north; it takes in the Guadalupe and Peloncillo ranges, the Animas Valley and the SK Bar.
export const CLUSTER_ZONE: [number, number, number, number] = [-109.25, 31.3, -108.7, 31.72]
// Zoom 9 and in shows every marker; stepping to a stop flies to zoom 9 at least, so a step always shows it.
export const CLUSTER_MAX_ZOOM = 8
export const CLUSTER_RADIUS = 40
export const ZONE_SOURCE = 'cluster-zone'

export const inZone = ([lon, lat]: number[]) =>
  lon >= CLUSTER_ZONE[0] && lon <= CLUSTER_ZONE[2] && lat >= CLUSTER_ZONE[1] && lat <= CLUSTER_ZONE[3]

export type Cluster = { id: number; lon: number; lat: number; count: number }

// Two unseen layers on the zone's source, so the map can say which clusters and which loose stops it draws
// now (the source's own query also returns tiles kept from other zooms).
export const ZONE_CLUSTERS = 'zone-clusters'
export const ZONE_STOPS = 'zone-stops'

type State = { clusters: Cluster[]; clustered: Set<string> }

// The clusters drawn in the current view, and the ids of the zone's points inside them (their own markers
// hide). Null until the map has drawn the zone's source, so nothing hides before then.
export function useZoneClusters(ids: string[]): State | null {
  const { current: ref } = useMap()
  const [state, setState] = useState<State | null>(null)
  const key = ids.join(' ')
  useEffect(() => {
    const map = ref?.getMap()
    if (!map) return
    let last = ''
    const update = () => {
      if (!map.getLayer(ZONE_CLUSTERS) || !map.getLayer(ZONE_STOPS)) return
      const clusters = new Map<number, Cluster>()
      const loose = new Set<string>()
      for (const f of map.queryRenderedFeatures({ layers: [ZONE_CLUSTERS, ZONE_STOPS] })) {
        const p = f.properties ?? {}
        if (p.cluster && f.geometry.type === 'Point') {
          const [lon, lat] = f.geometry.coordinates
          clusters.set(p.cluster_id, { id: p.cluster_id, lon, lat, count: p.point_count })
        } else if (typeof p.id === 'string') loose.add(p.id)
      }
      // Off screen, a stop counts as clustered while any cluster shows; its marker would not show anyway.
      const clustered = clusters.size > 0 ? key.split(' ').filter((id) => id && !loose.has(id)) : []
      const next = [...clusters.keys()].sort().join(' ') + '|' + clustered.join(' ')
      if (next === last) return // 'idle' comes often; the markers redraw only when the clusters change
      last = next
      setState({ clusters: [...clusters.values()], clustered: new Set(clustered) })
    }
    update()
    map.on('idle', update)
    return () => {
      map.off('idle', update)
    }
  }, [ref, key])
  return state
}

// A cluster opens where its points first come apart (and at least one zoom step in).
export async function expandCluster(map: MapLibreMap, cluster: Cluster, reducedMotion: boolean) {
  const source = map.getSource<GeoJSONSource>(ZONE_SOURCE)
  if (!source) return
  const zoom = await source.getClusterExpansionZoom(cluster.id)
  map.easeTo({ center: [cluster.lon, cluster.lat], zoom: Math.max(zoom, map.getZoom() + 1), duration: reducedMotion ? 0 : 600 })
}
