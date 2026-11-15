// Facts the About pages show, computed from the files at build time and served to the app as the virtual
// module `virtual:site-facts`: counts by certainty, source and method from the story GeoJSON, each download's
// size and columns, each tile archive the site reads with its size in site/public/tiles, and the commit built.
import { execSync } from 'node:child_process'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'

const repo = fileURLToPath(new URL('../../', import.meta.url))
const data = join(repo, 'data')
const tiles = join(repo, 'site', 'public', 'tiles')
const LAYERS = ['places', 'stops', 'areas', 'journeys', 'mountain_glyphs', 'landforms', 'water_places', 'context_places', 'vignettes']
// Published files beside the layers, in the order the Data page lists them.
const FILES = ['episodes.json', 'translations.json', 'open-questions.json', 'elsewhere.json']
const SCHEMAS = ['story-layer.schema.json', 'episodes.schema.json', 'translations.schema.json']
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

// The tile archives the site reads: those the map's styles name (src/map/), and the Raised view's list. Anything
// else in public/tiles, such as a local test archive, is not part of the site.
function archivesUsed(): Set<string> {
  const mapSource = join(repo, 'site', 'src', 'map')
  const named = readdirSync(mapSource)
    .flatMap((f) => [...readFileSync(join(mapSource, f), 'utf8').matchAll(/([\w-]+\.pmtiles)/g)].map((m) => m[1]))
  const raised: string[] = JSON.parse(readFileSync(join(data, 'raised', 'archives.json'), 'utf8'))
  return new Set([...named, ...raised])
}

// The commit this build is made from, so links into the repository match the deployed code. The deploy builds
// each branch in its own checkout, so the commit is read from the checkout, not from the CI run.
function commit(): string {
  try {
    return execSync('git rev-parse HEAD', { cwd: repo, encoding: 'utf8' }).trim()
  } catch {
    return 'main'
  }
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
    files: FILES.map((file) => ({ file, bytes: size(join(data, file)) })),
    schemas: SCHEMAS.filter((file) => existsSync(join(data, 'schema', file))),
    commit: commit(),
    dataBytes: dirBytes(data),
    raisedBytes: dirBytes(join(data, 'raised')),
    tileRelease: readFileSync(join(repo, 'tiles', 'release.txt'), 'utf8').trim(),
    // A build that reads another build's tiles (VITE_TILES_BASE) has none of its own to measure: the sizes are
    // then null and the page says so.
    tiles: [...archivesUsed()].sort().map((file) => ({ file, bytes: size(join(tiles, file)) })),
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
