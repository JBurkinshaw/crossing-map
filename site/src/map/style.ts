import type { StyleSpecification } from 'maplibre-gl'
import { tokens } from './tokens'

// Stage 0 style: paper, plus the test archive that proves PMTiles range
// requests work on the host. Later stages replace the test source.
export function literaryStyle(tilesBase: string): StyleSpecification {
  return {
    version: 8,
    sources: {
      test: {
        type: 'vector',
        url: `pmtiles://${tilesBase}test.pmtiles`,
      },
    },
    layers: [
      { id: 'paper', type: 'background', paint: { 'background-color': tokens.paper } },
      {
        id: 'graticule',
        type: 'line',
        source: 'test',
        'source-layer': 'graticule',
        paint: { 'line-color': tokens.inkFaint, 'line-width': 0.5 },
      },
      {
        id: 'story-box',
        type: 'line',
        source: 'test',
        'source-layer': 'story_box',
        paint: { 'line-color': tokens.ink, 'line-width': 1.2 },
      },
    ],
  }
}
