// Screenshots for the placement write-up (talks/placement/): the same views before and after a change, so the
// pairs line up. Desktop at 1400 x 900, 2x for print.
// Usage, with the dev server running (cd site && npm run dev -- --port 5185):
//   node placement-shots.mjs <out-dir> <before|after> [base-url]
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { gotoMap, launch, newPage, settle } from './lib/browser.mjs'

const [outDir, label, baseUrl = 'http://localhost:5185/'] = process.argv.slice(2)
if (!outDir || !label) {
  console.error('Usage: node placement-shots.mjs <out-dir> <before|after> [base-url]')
  process.exit(1)
}
await mkdir(outDir, { recursive: true })
const shot = (name) => path.join(outDir, `${name}-${label}.png`)

// Map views: a stop in focus, framed on the ground the write-up is about.
const views = {
  'j1-san-luis': { stop: 'j1-san-luis-mountains', zoom: 11, lat: 31.42, lon: -108.75 },
  'j1-foster-draw': { stop: 'j1-foster-draw', zoom: 11, lat: 31.5, lon: -108.94 },
  'j1-clanton-foster': { stop: 'j1-clanton-foster', zoom: 11, lat: 31.5, lon: -108.94 },
  'j1-starvation-canyon': { stop: 'j1-starvation-canyon', zoom: 11.5, lat: 31.55, lon: -109.11 },
  'type-bootheel': { stop: null, zoom: 9.5, lat: 31.5, lon: -108.85 },
}

const browser = await launch()
const page = await newPage(browser, { deviceScaleFactor: 2 })
for (const [name, v] of Object.entries(views)) {
  await page.goto('about:blank')
  const stop = v.stop ? `&stop=${v.stop}` : ''
  await page.goto(`${baseUrl}?debug#map=${v.zoom}/${v.lat}/${v.lon}${stop}`, { waitUntil: 'load' })
  await page.waitForFunction(() => window.__map, null, { timeout: 30000 })
  // Opening a stop flies the camera to it; put the camera back on the framed view.
  await page.waitForTimeout(2500)
  await page.evaluate(([z, lat, lon]) => window.__map.jumpTo({ zoom: z, center: [lon, lat] }), [v.zoom, v.lat, v.lon])
  await settle(page, { pause: 1500 })
  await page.screenshot({ path: shot(name) })
}

// The key, opened on its story tab: the grouped-stops row.
await gotoMap(page, baseUrl, { zoom: 9, lat: 31.5, lon: -108.85 }, { debug: true })
await settle(page)
await page.click('.layer-key-toggle')
await page.waitForTimeout(500)
await page.locator('.cartouche').screenshot({ path: shot('key') })

// The credits opened, at a desktop and a narrow width, with the key closed and then open.
await page.click('.layer-key-toggle')
for (const [w, h] of [[1400, 900], [900, 700]]) {
  await page.setViewportSize({ width: w, height: h })
  await page.waitForTimeout(500)
  await page.click('.maplibregl-ctrl-attrib-button')
  await page.waitForTimeout(400)
  await page.screenshot({ path: shot(`attribution-${w}`), clip: { x: 0, y: h - 260, width: w, height: 260 } })
  await page.click('.layer-key-toggle')
  await page.waitForTimeout(500)
  await page.screenshot({ path: shot(`attribution-${w}-key-open`) })
  await page.click('.layer-key-toggle')
  await page.click('.maplibregl-ctrl-attrib-button')
}
await browser.close()
console.log('done')
