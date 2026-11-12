// One-off comparison sheet for the paper tints (stage 2 review).
// Usage: node paper-sheet.mjs [base-url]
// Loads the bootheel view, swaps the paper colours through MapLibre's style
// API for each option, and screenshots the map. Needs the map instance on
// window.__map, which the app exposes only in local builds with ?debug.
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.argv[2] ?? 'http://localhost:4173/'
const options = {
  'A-current': ['#e6d9bd', '#dccdaa'],
  'B-caliche': ['#e4ddcc', '#d9cfbb'],
  'C-pale': ['#ede6d6', '#e1d7c3'],
}
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'review', 'stage-2', 'paper')
await mkdir(out, { recursive: true })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
await page.goto(`${baseUrl}?debug#map=8.5/31.45/-108.95`, { waitUntil: 'load' })
await page.waitForFunction(() => window.__map?.isStyleLoaded(), null, { timeout: 20000 })
for (const [name, [us, mx]] of Object.entries(options)) {
  await page.evaluate(([us, mx]) => {
    window.__map.setPaintProperty('paper', 'background-color', us)
    window.__map.setPaintProperty('mexico', 'fill-color', mx)
    document.documentElement.style.setProperty('--paper', us)
  }, [us, mx])
  await page.waitForTimeout(1500)
  await page.screenshot({ path: path.join(out, `${name}.png`) })
}
await browser.close()
console.log(`Paper sheet in ${out}`)
