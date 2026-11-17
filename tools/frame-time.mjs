// A 60 fps proxy for a mid-range phone (plan, stage 2): frame times in Chromium with the CPU throttled through the
// DevTools protocol, a phone-sized viewport, and a scripted pan and zoom over a dense area of the built site.
// Usage: serve the built site (cd site && npm run build && npx vite preview --port 5186), then
//   node frame-time.mjs [base-url] [--gl=metal|swiftshader] [--quick]
// Writes review/experiments/stage-2/frame-times-<gl>.json and prints a table.
import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const args = process.argv.slice(2)
const baseUrl = args.find((a) => a.startsWith('http')) ?? 'http://localhost:5186/'
const gl = (args.find((a) => a.startsWith('--gl='))?.split('=')[1]) ?? 'metal'
const quick = args.includes('--quick')

// A mid-range Android phone's screen (412 x 915 CSS px at 2.625 device pixels per px, as a Galaxy A5x or Pixel 6a).
const PHONE = { viewport: { width: 412, height: 915 }, deviceScaleFactor: 2.625, isMobile: true, hasTouch: true }
// The bootheel round Cloverdale and Animas: hachures, contours, creeks, glyphs and four journeys' stops.
const CENTRE = [-108.85, 31.5]
const FRAME = 1000 / 60

// Layer groups switched off one at a time, by id (prefix match with a trailing *).
const GROUPS = {
  'relief shading (tint, paper, hillshade)': ['relief-tint', 'relief-paper', 'hillshade'],
  hachures: ['hachure-*'],
  contours: ['contour', 'contour-label'],
  'glyphs and vignettes': ['mountain-glyph', 'vignette*'],
  'water (creeks, rivers, labels)': ['creek', 'creek-label', 'river', 'river-minor', 'river-label', 'lake'],
  'roads, rail, boundaries': ['road', 'railroad', 'railroad-ties', 'county-line', 'state-line', 'country-line'],
  'story (areas, journeys, places)': ['areas-*', 'journeys-*', 'places-*', 'zone-*', 'corridor-*'],
  'all text labels': ['@symbol'],
}

const browser = await chromium.launch({
  args: gl === 'metal' ? ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] : ['--use-angle=swiftshader'],
})
const context = await browser.newContext(PHONE)
await context.addInitScript(() => localStorage.setItem('crossing-map.progress', 'all'))
const page = await context.newPage()
const cdp = await context.newCDPSession(page)
const renderer = await (async () => {
  await page.goto(baseUrl + '?debug', { waitUntil: 'load' })
  return page.evaluate(() => {
    const g = document.createElement('canvas').getContext('webgl2')
    const ext = g.getExtension('WEBGL_debug_renderer_info')
    return ext ? g.getParameter(ext.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER)
  })
})()
console.log(`Renderer: ${renderer}`)
// Check the throttle bites: a fixed loop, timed at each rate.
const loop = () => page.evaluate(() => { const t0 = performance.now(); let x = 0; for (let i = 0; i < 2e7; i++) x += Math.sqrt(i); return [performance.now() - t0, x] })
const throttleCheck = {}
for (const rate of [1, 4, 6]) {
  await cdp.send('Emulation.setCPUThrottlingRate', { rate })
  throttleCheck[rate] = +(await loop())[0].toFixed(1)
}
await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 })
console.log(`Fixed loop, ms at 1x/4x/6x: ${Object.values(throttleCheck).join(' / ')}`)

async function open(zoom, oblique) {
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 })
  await page.goto('about:blank')
  await page.goto(`${baseUrl}?debug#map=${zoom}/${CENTRE[1]}/${CENTRE[0]}`, { waitUntil: 'load' })
  await page.waitForFunction(() => window.__map?.loaded(), null, { timeout: 30000 })
  if (oblique) {
    await page.getByRole('radio', { name: 'Oblique' }).click()
    await page.waitForFunction(() => window.__map.getStyle().layers.some((l) => l.id.startsWith('oblique-') && l.layout?.visibility !== 'none'), null, { timeout: 30000 })
    await page.waitForTimeout(2500)
    await page.evaluate(([c, z]) => window.__map.jumpTo({ center: c, zoom: z }), [CENTRE, zoom])
  }
  await settle()
}

const settle = () =>
  page.waitForFunction(() => window.__map.loaded() && window.__map.areTilesLoaded() && !window.__map.isMoving(), null, { timeout: 60000 })
    .catch(() => {}).then(() => page.waitForTimeout(500))

// Pan right, down, back, then zoom in one level and out again: 5 s of motion. Returns the rAF intervals and the
// number of frames MapLibre drew.
const motion = () => page.evaluate(async () => {
  const map = window.__map
  const step = (fn) => new Promise((done) => { map.once('moveend', done); fn() })
  const times = []
  let drawn = 0
  const onRender = () => { drawn++ }
  map.on('render', onRender)
  // Main-thread time MapLibre spends drawing each frame (its internal _render), the headroom a slower phone eats.
  const cpu = []
  const original = map._render
  map._render = function (...a) { const t0 = performance.now(); const r = original.apply(this, a); cpu.push(performance.now() - t0); return r }
  let running = true
  const tick = (now) => { times.push(now); if (running) requestAnimationFrame(tick) }
  requestAnimationFrame(tick)
  const z = map.getZoom()
  await step(() => map.panBy([160, 0], { duration: 1000, easing: (t) => t }))
  await step(() => map.panBy([0, 240], { duration: 1000, easing: (t) => t }))
  await step(() => map.panBy([-160, -240], { duration: 1000, easing: (t) => t }))
  await step(() => map.zoomTo(z + 1, { duration: 1000 }))
  await step(() => map.zoomTo(z, { duration: 1000 }))
  running = false
  map.off('render', onRender)
  map._render = original
  return { intervals: times.slice(1).map((t, i) => t - times[i]), drawn, cpu }
})

const quantile = (values, p) => {
  const s = [...values].sort((a, b) => a - b)
  return s[Math.min(s.length - 1, Math.floor(p * s.length))]
}

function stats({ intervals, drawn, cpu }) {
  const s = [...intervals].sort((a, b) => a - b)
  const q = (p) => quantile(intervals, p)
  const total = intervals.reduce((a, b) => a + b, 0)
  // A frame that takes n vsync periods drops n - 1.
  const dropped = intervals.reduce((n, dt) => n + Math.max(0, Math.round(dt / FRAME) - 1), 0)
  const expected = Math.round(total / FRAME)
  return {
    frames: intervals.length, drawn, median_ms: +q(0.5).toFixed(1), p95_ms: +q(0.95).toFixed(1), max_ms: +s[s.length - 1].toFixed(1),
    dropped, dropped_pct: +((100 * dropped) / Math.max(1, expected)).toFixed(1), fps: +((1000 * intervals.length) / total).toFixed(1),
    render_median_ms: +quantile(cpu, 0.5).toFixed(2), render_p95_ms: +quantile(cpu, 0.95).toFixed(2),
  }
}

async function hide(patterns, hidden) {
  return page.evaluate(([patterns, hidden]) => {
    const map = window.__map
    const ids = map.getStyle().layers.filter((l) => patterns.some((p) =>
      p === '@symbol' ? l.type === 'symbol' : p.endsWith('*') ? l.id.startsWith(p.slice(0, -1)) : l.id === p)).map((l) => l.id)
    for (const id of ids) map.setLayoutProperty(id, 'visibility', hidden ? 'none' : 'visible')
    return ids.length
  }, [patterns, hidden])
}

async function measure(rate) {
  // A warm-up pass loads the tiles along the path, so the measured pass times drawing, not the network.
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 })
  await motion()
  await settle()
  await cdp.send('Emulation.setCPUThrottlingRate', { rate })
  const result = stats(await motion())
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 })
  await settle()
  return result
}

const rows = []
const record = (row) => {
  rows.push(row)
  const { view, zoom, throttle, layers, median_ms, p95_ms, dropped, dropped_pct, fps, render_median_ms, render_p95_ms } = row
  console.log(`${view.padEnd(6)} z${String(zoom).padEnd(3)} ${throttle}x  ${layers.padEnd(48)} frame ${median_ms}/${p95_ms} ms  dropped ${dropped} (${dropped_pct}%)  ${fps} fps  render ${render_median_ms}/${render_p95_ms} ms`)
}

// Cold: the first pass over fresh ground in a fresh page, so tiles load, parse and upload while the map moves.
async function measureCold(zoom, oblique, rate) {
  await open(zoom, oblique)
  await cdp.send('Emulation.setCPUThrottlingRate', { rate })
  const result = stats(await motion())
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 })
  return result
}

const zooms = quick ? [10] : [8, 10, 12]
const rates = quick ? [4] : [1, 4, 6]
for (const zoom of zooms) {
  for (const rate of rates.filter((r) => r > 1)) {
    record({ view: 'flat', zoom, throttle: rate, layers: 'all, cold (tiles loading)', ...(await measureCold(zoom, false, rate)) })
  }
  await open(zoom, false)
  for (const rate of rates) record({ view: 'flat', zoom, throttle: rate, layers: 'all', ...(await measure(rate)) })
  for (const [name, patterns] of Object.entries(GROUPS)) {
    const n = await hide(patterns, true)
    await settle()
    record({ view: 'flat', zoom, throttle: 4, layers: `without ${name} (${n})`, ...(await measure(4)) })
    await hide(patterns, false)
    await settle()
  }
}
// The Oblique view starts at zoom 9.
for (const zoom of quick ? [] : [10, 12]) {
  for (const rate of rates.filter((r) => r > 1)) {
    record({ view: 'oblique', zoom, throttle: rate, layers: 'all, cold (tiles loading)', ...(await measureCold(zoom, true, rate)) })
  }
  await open(zoom, true)
  for (const rate of rates) record({ view: 'oblique', zoom, throttle: rate, layers: 'all', ...(await measure(rate)) })
}
await browser.close()

const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'review', 'experiments', 'stage-2')
await mkdir(out, { recursive: true })
await writeFile(path.join(out, `frame-times-${gl}.json`), JSON.stringify({
  measured: new Date().toISOString(), renderer, throttle_check_ms: throttleCheck, phone: PHONE, centre: CENTRE,
  motion: 'pan 160 px right, 240 px down and back (1 s each), zoom in one level and out (1 s each); warm rows after an unthrottled pass over the same path, cold rows on a fresh page',
  rows,
}, null, 1) + '\n')
console.log(`Wrote frame-times-${gl}.json`)
