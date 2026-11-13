// Facts the About pages show, computed from the files at build time and served to the app as the virtual
// module `virtual:site-facts`: counts by certainty, source and method from the story GeoJSON, each download's
// size and columns, and the size of each tile archive in site/public/tiles (in CI, the release the deploy
// downloads; locally, whatever archives are there).
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'

const repo = fileURLToPath(new URL('../../', import.meta.url))
const data = join(repo, 'data')
const tiles = join(repo, 'site', 'public', 'tiles')
const LAYERS = ['places', 'stops', 'areas', 'journeys', 'mountain_glyphs']
const ID = 'virtual:site-facts'

type SchemaProp = { type?: string | string[]; enum?: unknown[]; description?: string; items?: { enum?: unknown[] } }

function count(values: unknown[]): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const v of values) counts[String(v)] = (counts[String(v)] ?? 0) + 1
  return counts
}

function dirBytes(dir: string): number {
  return readdirSync(dir, { withFileTypes: true }).reduce(
    (sum, e) => sum + (e.isDirectory() ? dirBytes(join(dir, e.name)) : statSync(join(dir, e.name)).size),
    0,
  )
}

function size(path: string): number | null {
  return existsSync(path) ? statSync(path).size : null
}

function facts() {
  const schema = JSON.parse(readFileSync(join(data, 'schema', 'story-layer.schema.json'), 'utf8'))
  const props: Record<string, SchemaProp> = schema.$defs.properties.properties
  const required: string[] = schema.$defs.properties.required
  const layers = LAYERS.map((name) => {
    const features: { geometry: { type: string }; properties: Record<string, unknown> }[] = JSON.parse(
      readFileSync(join(data, `${name}.geojson`), 'utf8'),
    ).features
    const columns: string[] = []
    for (const f of features) for (const k of Object.keys(f.properties)) if (!columns.includes(k)) columns.push(k)
    return {
      name,
      features: features.length,
      geometry: [...new Set(features.map((f) => f.geometry.type))],
      geojsonBytes: size(join(data, `${name}.geojson`)),
      parquetBytes: size(join(data, 'parquet', `${name}.parquet`)),
      certainty: count(features.map((f) => f.properties.certainty)),
      source: count(features.map((f) => f.properties.source)),
      method: count(features.map((f) => f.properties.method)),
      columns: columns.map((c) => ({
        name: c,
        type: props[c]?.type ?? null,
        values: props[c]?.enum ?? props[c]?.items?.enum ?? null,
        description: props[c]?.description ?? null,
        required: required.includes(c),
      })),
    }
  })
  return {
    layers,
    files: ['episodes.json', 'elsewhere.json'].map((file) => ({ file, bytes: size(join(data, file)) })),
    dataBytes: dirBytes(data),
    raisedBytes: dirBytes(join(data, 'raised')),
    tileRelease: readFileSync(join(repo, 'tiles', 'release.txt'), 'utf8').trim(),
    tiles: existsSync(tiles)
      ? readdirSync(tiles)
          .filter((f) => f.endsWith('.pmtiles'))
          .sort()
          .map((file) => ({ file, bytes: statSync(join(tiles, file)).size }))
      : [],
  }
}

// The app's type for these facts is in src/pages/site-facts.d.ts.
export function siteFacts(): Plugin {
  return {
    name: 'site-facts',
    resolveId: (id) => (id === ID ? `\0${ID}` : null),
    load: (id) => (id === `\0${ID}` ? `export default ${JSON.stringify(facts())}` : null),
  }
}
