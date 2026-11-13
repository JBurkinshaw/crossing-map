// The vignette review shots (plan section 10, stage 6): the classic map at zooms 7, 9 and 11 over three areas,
// with the vignettes drawn in each, then a check that they hide over satellite and in the Raised view, and a
// console check. Saves review/stage-6/vignettes/<area>-z<zoom>.png and prints what each shot shows.
// Usage: node vignette-sheet.mjs [base-url]   (needs the site served, e.g. npx vite in site/)
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.argv[2] ?? 'http://localhost:5183/'
const repo = fileURLToPath(new URL('..', import.meta.url))
const out = path.join(repo, 'review', 'stage-6', 'vignettes')
// Each area's centre, and a closer centre for zoom 11 between a vignette and what it stands for.
const areas = {
  'Part I border country': { lon: -109.05, lat: 31.05, z11: { lon: -109.13, lat: 31.32 } },
  'Casas Grandes': { lon: -107.95, lat: 30.35, z11: { lon: -107.87, lat: 30.33 } },
  'Babicora and Las Varas': { lon: -107.9, lat: 29.5, z11: { lon: -107.88, lat: 29.36 } },
}
const ZOOMS = [7, 9, 11]

await mkdir(out, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1200, height: 800 } })
const problems = []
// MapTiler refuses localhost (403), which the satellite map reports; that is expected here.
const expected = (t) => /maptiler|403/i.test(t)
page.on('console', (m) => m.type() === 'error' && !expected(m.text()) && problems.push(m.text().slice(0, 200)))
page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))

const settle = async () => {
  await page.waitForFunction(() => {
    const map = window.__map
    return map && !map.isMoving() && map.areTilesLoaded()
  }, null, { timeout: 30000 })
  await page.waitForTimeout(800)
}
const shown = () => page.evaluate(() => {
  const map = window.__map
  const names = map.queryRenderedFeatures({ layers: ['vignette'] }).map((f) => f.properties.id.replace('vignette-', ''))
  return [...new Set(names)]
})
const view = (label) => page.getByRole('radiogroup', { name: 'View of the classic map' }).getByRole('radio', { name: label })
const basemap = (label) => page.getByRole('radiogroup', { name: 'Basemap' }).getByRole('radio', { name: label })
const map = page.locator('.map-area')

for (const [name, p] of Object.entries(areas)) {
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-')
  for (const z of ZOOMS) {
    const c = z === 11 ? p.z11 : p
    await page.goto('about:blank')
    await page.goto(`${baseUrl}?debug#map=${z}/${c.lat}/${c.lon}`, { waitUntil: 'load' })
    await page.waitForFunction(() => window.__map)
    await settle()
    await map.screenshot({ path: path.join(out, `${slug}-z${z}.png`) })
    console.log(`${name}, zoom ${z}: ${(await shown()).join(', ') || 'none'}`)
  }
}

// Hidden over satellite (when MapTiler answers) and in the Raised view.
const visibility = () => page.evaluate(() => ['mountain-glyph', 'vignette', 'vignette-leader'].map((id) => window.__map.getLayoutProperty(id, 'visibility') ?? 'visible').join('/'))
if (await basemap('Satellite').isEnabled()) {
  await basemap('Satellite').click()
  await page.waitForTimeout(2500)
  console.log(`Satellite: glyph and vignette layers ${await visibility()}`)
  await basemap('Classic').click()
  await page.waitForTimeout(1000)
} else {
  console.log('Satellite: disabled (satellite unavailable)')
}
await view('Raised').click()
await settle()
console.log(`Raised: glyph and vignette layers ${await visibility()}`)
await view('Flat').click()
await settle()
console.log(`Flat: glyph and vignette layers ${await visibility()}`)

await browser.close()
console.log(problems.length ? `Console errors:\n${problems.join('\n')}` : 'No console errors.')
