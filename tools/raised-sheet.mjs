// The Raised review sheet (decision 0018): Flat and Raised side by side at five places along J1 and J2,
// then a walk through J2's stops in Raised, checking that each step lands on the raised marker, and a
// console check of every view. Saves private/review/raised-j1j2/{sheet.png,<place>-<view>.png}.
// Usage: node raised-sheet.mjs [base-url]   (needs the site served, e.g. npx vite in site/)
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { fileURLToPath, pathToFileURL } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.argv[2] ?? 'http://localhost:5183/'
const repo = fileURLToPath(new URL('..', import.meta.url))
const out = path.join(repo, 'private', 'review', 'raised-j1j2')
const places = {
  'Border near 31.33 N': { lon: -109.2, lat: 31.36 },
  'Animas Valley': { lon: -108.86, lat: 31.6 },
  Peloncillos: { lon: -108.98, lat: 31.47 },
  'Colonia Morelos': { lon: -109.22, lat: 30.85 },
  Pilares: { lon: -109.08, lat: 30.79 },
}
const ZOOM = 11.5

await mkdir(out, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1300, height: 820 } })
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
const view = (label) => page.getByRole('radiogroup', { name: 'View of the classic map' }).getByRole('radio', { name: label })
const basemap = (label) => page.getByRole('radiogroup', { name: 'Basemap' }).getByRole('radio', { name: label })
const map = page.locator('.map-area')

const shots = []
for (const [name, p] of Object.entries(places)) {
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-')
  await page.goto('about:blank')
  await page.goto(`${baseUrl}?debug#map=${ZOOM}/${p.lat}/${p.lon}`, { waitUntil: 'load' })
  await page.waitForFunction(() => window.__map)
  await settle()
  await map.screenshot({ path: path.join(out, `${slug}-flat.png`) })
  await view('Raised').click()
  await settle()
  await map.screenshot({ path: path.join(out, `${slug}-raised.png`) })
  shots.push([name, slug])
  console.log(`${name}: flat and raised`)
}

// Every view and basemap once, for console errors.
for (const label of ['Tilted', 'Flat']) {
  await view(label).click()
  await settle()
}
// Once MapTiler has refused the key, Satellite and Compare are disabled and the classic map stays.
for (const label of ['Satellite', 'Compare', 'Classic']) {
  if (!(await basemap(label).isEnabled())) {
    console.log(`${label}: disabled (satellite unavailable)`)
    continue
  }
  await basemap(label).click()
  await page.waitForTimeout(2500)
}

// J2 in Raised: each step should centre the map on the raised stop, where its marker is drawn.
const raisedStops = JSON.parse(await readFile(path.join(repo, 'data', 'raised', 'stops.geojson'), 'utf8')).features
  .filter((f) => f.properties.journey === 'J2')
  .sort((a, b) => a.properties.sequence - b.properties.sequence)
await view('Raised').click()
await settle()
await page.locator('.journey-pick select').selectOption('J2')
await settle()
const steps = []
for (let i = 0; i < raisedStops.length; i++) {
  if (i > 0) await page.getByRole('button', { name: 'Next' }).click()
  await settle()
  const [lon, lat] = raisedStops[i].geometry.coordinates
  const result = await page.evaluate(([lon, lat]) => {
    const map = window.__map
    const c = map.getCenter()
    const canvas = map.getCanvas().getBoundingClientRect()
    const marker = document.querySelector('.stop-marker.is-current').getBoundingClientRect()
    const at = map.project([lon, lat])
    return {
      centre: Math.hypot(c.lng - lon, c.lat - lat) * 111000,
      // The marker's middle against the raised stop's position on screen, in pixels.
      marker: Math.hypot(marker.left + marker.width / 2 - canvas.left - at.x, marker.top + marker.height / 2 - canvas.top - at.y),
    }
  }, [lon, lat])
  steps.push(`${i + 1}. ${raisedStops[i].properties.name}: centre ${result.centre.toFixed(0)} m from the raised stop, marker ${result.marker.toFixed(1)} px from it`)
}
await page.screenshot({ path: path.join(out, 'j2-last-stop-raised.png') })

const rows = shots
  .map(([name, slug]) => `<tr><th>${name}</th>${['flat', 'raised'].map((v) => `<td><img src="${pathToFileURL(path.join(out, `${slug}-${v}.png`)).href}"></td>`).join('')}</tr>`)
  .join('')
const html = path.join(out, 'sheet.html')
await writeFile(html, `<!doctype html><meta charset="utf-8"><style>
  body{background:#fff;margin:16px;font:16px Georgia,serif} th{text-align:left;vertical-align:top;padding-right:12px;font-weight:normal;width:140px}
  thead th{padding-bottom:6px} img{width:820px;display:block;border:1px solid #ccc}</style>
  <table><thead><tr><th></th><th>Flat</th><th>Raised</th></tr></thead>${rows}</table>`)
await page.setViewportSize({ width: 1840, height: 900 })
await page.goto(pathToFileURL(html).href, { waitUntil: 'load' })
await page.screenshot({ path: path.join(out, 'sheet.png'), fullPage: true })
await browser.close()

const report = [`Sheet: ${path.join(out, 'sheet.png')}`, 'J2 in Raised:', ...steps,
  problems.length ? `Console errors:\n${[...new Set(problems)].join('\n')}` : 'No console errors (MapTiler 403s on localhost excepted).']
await writeFile(path.join(out, 'report.txt'), report.join('\n') + '\n')
console.log(report.join('\n'))
