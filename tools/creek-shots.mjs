// Creek density screenshots: four places at zoom 9-12, desktop, as JPEG.
// Usage: node creek-shots.mjs <out-dir> <prefix> [base-url]   (ZOOMS=9,10 to choose zooms)
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { gotoMap, launch, newPage } from './lib/browser.mjs'

const [outDir, prefix, baseUrl = 'http://localhost:5194/'] = process.argv.slice(2)
if (!outDir || !prefix) {
  console.error('Usage: node creek-shots.mjs <out-dir> <prefix> [base-url]')
  process.exit(1)
}
const places = {
  morelos: [-109.224, 30.827],
  peloncillos: [-109.013, 31.667],
  bavispe: [-109.29, 30.0],
  babicora: [-107.748, 29.251],
}
const zooms = (process.env.ZOOMS ?? '9,10,11,12').split(',').map(Number)
await mkdir(outDir, { recursive: true })
const browser = await launch()
const page = await newPage(browser)
for (const [name, [lon, lat]] of Object.entries(places)) {
  for (const zoom of zooms) {
    await gotoMap(page, baseUrl, { zoom, lat, lon })
    // Tiles stream in after the canvas appears; creeks are the last layer to fill in.
    await page.waitForTimeout(4000)
    await page.screenshot({ path: path.join(outDir, `${prefix}-${name}-z${zoom}.jpg`), type: 'jpeg', quality: 78 })
  }
}
await browser.close()
console.log('done')
