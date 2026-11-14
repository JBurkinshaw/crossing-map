// Before and after screenshots for the stage 2 leftovers experiment (review/experiments/stage-2/).
// Usage: node stage2-shots.mjs <label> [base-url]
// Writes <view>-<label>.png for the named views into review/experiments/stage-2/screenshots/.
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium, devices } from 'playwright'

const label = process.argv[2]
const baseUrl = process.argv[3] ?? 'http://localhost:5186/'
if (!label) {
  console.error('Usage: node stage2-shots.mjs <label> [base-url]')
  process.exit(1)
}

// name -> [lon, lat, zoom, journey in focus, profile]
const views = {
  'states-z5-desktop': [-108.5, 31.5, 5.2, 'J1', 'desktop'],
  'states-z6-desktop': [-108.6, 30.8, 6.2, 'J1', 'desktop'],
  'states-z7-desktop': [-108.6, 31.0, 7.2, 'J1', 'desktop'],
  'states-z5-phone': [-108.5, 31.0, 4.6, 'J1', 'phone'],
  'states-z6-phone': [-108.3, 31.6, 6, 'J1', 'phone'],
  'states-z7.5-desktop': [-107.2, 30.0, 7.5, 'J1', 'desktop'],
  'cloverdale-z11-desktop': [-108.955, 31.43, 11.6, 'J2', 'desktop'],
  'cloverdale-z13-desktop': [-108.96, 31.432, 13, 'J2', 'desktop'],
}
const profiles = {
  desktop: { viewport: { width: 1440, height: 900 } },
  phone: devices['iPhone 14'],
}

const outDir = path.join(fileURLToPath(new URL('..', import.meta.url)), 'review', 'experiments', 'stage-2', 'screenshots')
await mkdir(outDir, { recursive: true })

const browser = await chromium.launch()
for (const [name, [lon, lat, zoom, journey, profileName]] of Object.entries(views)) {
  const context = await browser.newContext(profiles[profileName])
  const page = await context.newPage()
  await page.addInitScript(() => localStorage.setItem('crossing-map.progress', 'all'))
  page.on('pageerror', (e) => console.error(`${name}: ${e.message}`))
  await page.goto(baseUrl + '?debug', { waitUntil: 'load' })
  await page.waitForSelector('canvas.maplibregl-canvas', { timeout: 15000 })
  await page.waitForFunction(() => window.__map)
  if (journey !== 'J1') await page.selectOption('.journey-pick select', journey)
  await page.waitForTimeout(1500)
  // Set the camera after the journey is framed, then wait for the map to settle.
  await page.evaluate(([lon, lat, zoom]) => window.__map.jumpTo({ center: [lon, lat], zoom }), [lon, lat, zoom])
  await page.waitForTimeout(500)
  await page.waitForFunction(() => window.__map.loaded() && window.__map.areTilesLoaded(), null, { timeout: 30000 }).catch(() => {})
  await page.waitForTimeout(1500)
  console.log(name)
  await page.screenshot({ path: path.join(outDir, `${name}-${label}.png`) })
  await context.close()
}
await browser.close()
console.log(`Screenshots in ${outDir}`)
