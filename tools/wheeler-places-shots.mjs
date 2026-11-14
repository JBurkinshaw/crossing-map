// Screenshots for the stage 9 Wheeler places card (review/stage-9/wheeler-places): the lab map in the test area at
// zooms 8, 10, 11 and 12, desktop and phone, with every Wheeler parameter on (water and stations, graticule and
// frame included), and a pair proving the reading filter. Saves private/review/stage-9/wheeler-places/<name>.jpg.
// Usage, with the dev server running: node wheeler-places-shots.mjs [base-url]
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { collectProblems, launch, newPage, report } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5193/'
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', 'stage-9', 'wheeler-places')

// The test area's middle at the low zooms; the Guadalupe Mountains' springs and the Sonoran ranches at the high ones.
const views = [
  ['z8', 8, [-109.0, 31.05]],
  ['z10', 10, [-109.0, 31.05]],
  ['z11', 11, [-109.05, 31.44]],
  ['z12', 12, [-109.06, 31.46]],
  ['z11-sonora', 11, [-108.66, 30.88]],
]
const devices = [
  ['desktop', { width: 1400, height: 900 }, 1],
  ['phone', { width: 390, height: 844 }, 3],
]

await mkdir(out, { recursive: true })
const browser = await launch()
const problems = []

const idle = (p) => p.evaluate(() => new Promise((r) => (window.__wheelerMap.loaded() && !window.__wheelerMap.isMoving() ? setTimeout(r, 300) : window.__wheelerMap.once('idle', r))))
const jump = (p, zoom, center) => p.evaluate(([z, c]) => window.__wheelerMap.jumpTo({ zoom: z, center: c }), [zoom, center])

for (const [device, viewport, scale] of devices) {
  const p = await newPage(browser, { viewport, deviceScaleFactor: scale })
  collectProblems(p, { problems })
  await p.goto(`${baseUrl}lab.html?debug#wheeler`, { waitUntil: 'load' })
  await p.waitForSelector('.wheeler-map canvas')
  await idle(p)
  for (const [name, zoom, center] of views) {
    await jump(p, zoom, center)
    await p.waitForTimeout(300)
    await idle(p)
    const file = `${device}-${name}.jpg`
    await p.locator('.wheeler-map').screenshot({ path: path.join(out, file), type: 'jpeg', quality: 82 })
    console.log(file)
  }
  if (device === 'desktop') {
    // The reading filter: Hog Canyon Spring is first named in 1-04, so it hides at 1-03 and shows at 1-04.
    await jump(p, 12, [-109.08, 31.49])
    const slider = p.getByRole('slider', { name: /Read up to/ })
    for (const reached of ['1-03', '1-04']) {
      await slider.evaluate((el, v) => {
        const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
        set.call(el, String(v))
        el.dispatchEvent(new Event('input', { bubbles: true }))
      }, 1 + (Number(reached.slice(2)) - 1))
      await p.waitForTimeout(500)
      await idle(p)
      const file = `desktop-filter-${reached}.jpg`
      await p.locator('.wheeler-map').screenshot({ path: path.join(out, file), type: 'jpeg', quality: 82 })
      console.log(file)
    }
    // The other way to label the graticule: MapLibre's own labels along each line.
    await p.getByRole('checkbox', { name: 'Graticule labels on the lines' }).check()
    for (const [name, zoom, center] of views.slice(0, 2)) {
      await jump(p, zoom, center)
      await p.waitForTimeout(500)
      await idle(p)
      const file = `desktop-${name}-line-labels.jpg`
      await p.locator('.wheeler-map').screenshot({ path: path.join(out, file), type: 'jpeg', quality: 82 })
      console.log(file)
    }
    await p.screenshot({ path: path.join(out, 'desktop-page.jpg'), type: 'jpeg', quality: 70 })
  }
  await p.close()
}
await browser.close()
report(problems)
