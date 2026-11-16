// Screenshots for the Wheeler study (review/stage-8/wheeler): the classic map today at the kinds of places the
// Wheeler sheets are studied for (a range and its plain, mesas, a river, an escarpment), flat and tilted, and the
// lab section's toggles. Saves review/stage-8/wheeler/shots/<name>.jpg.
// Usage, with the dev server running: node wheeler-shots.mjs [base-url] [only-name,...]
//   base-url defaults to http://localhost:5193/. The lab views need the dev server, which serves lab.html.
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { collectProblems, gotoMap, launch, newPage, report } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5193/'
const only = process.argv[3]?.split(',')
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'review', 'stage-8', 'wheeler', 'shots')

// The site at each view, and whether to switch to the Tilted view.
const site = {
  'now-peloncillos-z10': { zoom: 10, lat: 32.05, lon: -109.05 },
  'now-animas-z11': { zoom: 11, lat: 31.6, lon: -108.8 },
  'now-animas-z12': { zoom: 12, lat: 31.57, lon: -108.79 },
  'now-mesas-babicora-z10': { zoom: 10, lat: 29.2, lon: -107.5 },
  'now-bavispe-z9': { zoom: 9, lat: 30.4, lon: -109.2 },
  'now-escarpment-z11': { zoom: 11, lat: 29.95, lon: -108.75 },
  'now-animas-tilted-z11': { zoom: 11, lat: 31.45, lon: -108.8, tilted: true },
}

await mkdir(out, { recursive: true })
const browser = await launch()
const page = await newPage(browser)
const problems = collectProblems(page)

for (const [name, v] of Object.entries(site)) {
  if (only && !only.includes(name)) continue
  await gotoMap(page, baseUrl, v)
  await page.waitForTimeout(2500)
  if (v.tilted) {
    await page.getByRole('button', { name: 'Map options' }).click()
    await page.getByRole('radio', { name: 'Tilted' }).click()
    await page.keyboard.press('Escape')
    await page.waitForTimeout(4000)
  }
  await page.screenshot({ path: path.join(out, `${name}.jpg`), type: 'jpeg', quality: 80 })
  console.log(`${name}.jpg`)
}
// The lab section (site/src/lab/wheeler) on the dev-only lab page: each place with every parameter as today, then
// with all of them on, then one parameter at a time where it shows best.
const lab = [
  ['animas', ['today', 'wheeler']],
  ['peloncillos', ['today', 'wheeler']],
  ['hatchets', ['today', 'wheeler']],
  ['bavispe', ['today', 'wheeler']],
  ['tigre', ['today', 'wheeler']],
  ['babicora', ['today', 'wheeler']],
]
const labPage = await newPage(browser)
collectProblems(labPage, { problems })
await labPage.goto(`${baseUrl}lab.html?debug#wheeler`, { waitUntil: 'load' })
await labPage.waitForSelector('.wheeler-map canvas')
for (const [place, presets] of lab) {
  for (const preset of presets) {
    const name = `lab-${place}-${preset}`
    if (only && !only.includes(name)) continue
    const button = await labPage.locator('.wheeler-places button').nth(['animas', 'peloncillos', 'hatchets', 'bavispe', 'tigre', 'babicora'].indexOf(place))
    await button.click()
    await labPage.getByRole('button', { name: preset === 'today' ? 'All as today' : 'All Wheeler' }).click()
    await labPage.waitForTimeout(500)
    await labPage.evaluate(() => new Promise((r) => window.__wheelerMap.once('idle', r)))
    await labPage.locator('.wheeler-map').screenshot({ path: path.join(out, `${name}.jpg`), type: 'jpeg', quality: 80 })
    console.log(`${name}.jpg`)
  }
}

// The whole section: the controls and the first cards on a desktop, and the phone layout.
for (const [name, viewport, scale] of [['lab-page-desktop', { width: 1400, height: 900 }, 1], ['lab-page-phone', { width: 390, height: 844 }, 3]]) {
  if (only && !only.includes(name)) continue
  const p = await newPage(browser, { viewport, deviceScaleFactor: scale })
  collectProblems(p, { problems })
  await p.goto(`${baseUrl}lab.html?debug#wheeler`, { waitUntil: 'load' })
  await p.waitForSelector('.wheeler-map canvas')
  await p.evaluate(() => new Promise((r) => window.__wheelerMap.once('idle', r)))
  await p.screenshot({ path: path.join(out, `${name}.jpg`), type: 'jpeg', quality: 70, fullPage: name.endsWith('phone') ? false : true })
  console.log(`${name}.jpg`)
  await p.close()
}

await browser.close()
report(problems)
