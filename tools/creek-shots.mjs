// Creek density screenshots: four places at zoom 9-12, desktop, as JPEG.
// Usage: node creek-shots.mjs <out-dir> <prefix> [base-url]
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { chromium } from 'playwright'

const [outDir, prefix, baseUrl = 'http://localhost:5194/'] = process.argv.slice(2)
const places = {
  morelos: [-109.224, 30.827],
  peloncillos: [-109.013, 31.667],
  bavispe: [-109.29, 30.0],
  babicora: [-107.748, 29.251],
}
const zooms = (process.env.ZOOMS ?? '9,10,11,12').split(',').map(Number)
await mkdir(outDir, { recursive: true })
const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1400, height: 900 } })
const page = await context.newPage()
await page.addInitScript(() => localStorage.setItem('crossing-map.progress', 'all'))
for (const [name, [lon, lat]] of Object.entries(places)) {
  for (const z of zooms) {
    await page.goto('about:blank')
    await page.goto(`${baseUrl}#map=${z}/${lat}/${lon}`, { waitUntil: 'load' })
    await page.waitForSelector('canvas.maplibregl-canvas', { timeout: 15000 })
    await page.waitForTimeout(4000)
    await page.screenshot({ path: path.join(outDir, `${prefix}-${name}-z${z}.jpg`), type: 'jpeg', quality: 78 })
  }
}
await browser.close()
console.log('done')
