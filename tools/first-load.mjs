// First load of the built site on a throttled phone connection (docs/plan.md, stage 6 performance pass):
// the time to a drawn map, and what was fetched to draw it, by kind.
//
// Usage, after `cd site && npm run build`:
//   cd tools && node first-load.mjs [runs]
// It serves site/dist itself, gzipped as GitHub Pages does (archives unzipped, with range requests), and
// loads it as a first visit (no reading progress stored) at two settings:
//   phone: iPhone 14 viewport, Lighthouse's mobile throttling (150 ms round trip, 1.6 Mbit/s down,
//          750 kbit/s up, CPU slowed 4 times);
//   desktop: 1280 x 800, no throttling.
// "Map ready" is MapLibre's load event (style, sprites and first tiles in); "map drawn" is the first moment
// every tile of the opening view has loaded and the map is idle. Medians of the runs (default 3).
import { createServer } from 'node:http'
import { readFile, stat } from 'node:fs/promises'
import { gzipSync } from 'node:zlib'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium, devices } from 'playwright'

const runs = Number(process.argv[2] ?? 3)
const dist = fileURLToPath(new URL('../site/dist/', import.meta.url))
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.geojson': 'application/geo+json', '.png': 'image/png', '.pbf': 'application/x-protobuf', '.pmtiles': 'application/octet-stream',
  '.woff2': 'font/woff2', '.svg': 'image/svg+xml' }
const ZIPPED = new Set(['.html', '.js', '.mjs', '.css', '.json', '.geojson', '.svg', '.pbf'])
const zipped = new Map()

const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x')
  let file = path.join(dist, decodeURIComponent(url.pathname))
  if (!file.startsWith(dist)) return res.writeHead(403).end()
  if (url.pathname.endsWith('/')) file = path.join(file, 'index.html')
  const info = await stat(file).catch(() => null)
  if (!info?.isFile()) return res.writeHead(404).end()
  const ext = path.extname(file)
  const type = TYPES[ext] ?? 'application/octet-stream'
  const range = req.headers.range?.match(/bytes=(\d+)-(\d*)/)
  if (range) {
    const { open } = await import('node:fs/promises')
    const start = Number(range[1])
    const end = range[2] ? Math.min(Number(range[2]), info.size - 1) : info.size - 1
    const fh = await open(file)
    const buf = Buffer.alloc(end - start + 1)
    await fh.read(buf, 0, buf.length, start)
    await fh.close()
    res.writeHead(206, { 'content-type': type, 'content-range': `bytes ${start}-${end}/${info.size}`, 'content-length': buf.length, 'accept-ranges': 'bytes' })
    return res.end(buf)
  }
  let body = await readFile(file)
  const headers = { 'content-type': type, 'accept-ranges': 'bytes' }
  if (ZIPPED.has(ext) && /gzip/.test(req.headers['accept-encoding'] ?? '')) {
    if (!zipped.has(file)) zipped.set(file, gzipSync(body))
    body = zipped.get(file)
    headers['content-encoding'] = 'gzip'
  }
  res.writeHead(200, { ...headers, 'content-length': body.length }).end(body)
})
await new Promise((r) => server.listen(0, r))
const base = `http://localhost:${server.address().port}/`

const kind = (url) => {
  const p = new URL(url).pathname
  if (p.endsWith('.pmtiles')) return `tiles ${path.basename(p)}`
  if (/\.(m?js)$/.test(p)) return 'script'
  if (p.endsWith('.css')) return 'style sheet'
  if (p.startsWith('/fonts/')) return 'glyphs'
  if (p.startsWith('/sprites/')) return 'sprites'
  if (p.startsWith('/data/')) return 'story data'
  return 'page and other'
}

async function once(profile) {
  const browser = await chromium.launch()
  const context = await browser.newContext(profile === 'phone' ? devices['iPhone 14'] : { viewport: { width: 1280, height: 800 } })
  const page = await context.newPage()
  const cdp = await context.newCDPSession(page)
  await cdp.send('Network.enable')
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true })
  if (profile === 'phone') {
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: (1.6e6 / 8) * 0.9, uploadThroughput: (750e3 / 8) * 0.9 })
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 })
  }
  const urls = new Map()
  const bytes = new Map()
  cdp.on('Network.requestWillBeSent', (e) => urls.set(e.requestId, e.request.url))
  cdp.on('Network.loadingFinished', (e) => {
    const u = urls.get(e.requestId)
    if (!u || !u.startsWith(base)) return
    const k = kind(u)
    const b = bytes.get(k) ?? { n: 0, bytes: 0 }
    bytes.set(k, { n: b.n + 1, bytes: b.bytes + e.encodedDataLength })
  })
  const t0 = Date.now()
  await page.goto(`${base}?debug`, { waitUntil: 'commit' })
  await page.waitForFunction(() => !!window.__map, null, { timeout: 120000, polling: 50 })
  const ready = Date.now() - t0
  await page.waitForFunction(() => window.__map.loaded() && window.__map.areTilesLoaded(), null, { timeout: 120000, polling: 50 })
  const drawn = Date.now() - t0
  // Anything still arriving for the opening view (the framing of the first journey) is counted too.
  await page.waitForTimeout(1500)
  await page.waitForFunction(() => window.__map.loaded(), null, { timeout: 120000, polling: 100 })
  await browser.close()
  return { ready, drawn, bytes }
}

const median = (xs) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)]
for (const profile of ['phone', 'desktop']) {
  const results = []
  for (let i = 0; i < runs; i++) results.push(await once(profile))
  console.log(`\n${profile}: map ready ${(median(results.map((r) => r.ready)) / 1000).toFixed(1)} s, map drawn ${(median(results.map((r) => r.drawn)) / 1000).toFixed(1)} s (median of ${runs})`)
  const last = results[results.length - 1].bytes
  let total = 0
  for (const [k, { n, bytes }] of [...last].sort((a, b) => b[1].bytes - a[1].bytes)) {
    total += bytes
    console.log(`  ${k.padEnd(28)} ${String(n).padStart(4)} requests ${(bytes / 1000).toFixed(0).padStart(7)} kB`)
  }
  console.log(`  ${'total'.padEnd(28)} ${String([...last.values()].reduce((s, b) => s + b.n, 0)).padStart(4)} requests ${(total / 1000).toFixed(0).padStart(7)} kB`)
}
server.close()
