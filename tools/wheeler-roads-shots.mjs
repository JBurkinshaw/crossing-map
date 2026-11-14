// Screenshots for the Wheeler card "roads" (review/stage-9/wheeler-roads): the lab's Wheeler map over the test area
// at zooms 10, 11 and 12, with the historic roads off (before) and on (after), every other parameter as Wheeler.
// Saves private/review/stage-9/wheeler-roads/<name>.jpg (git-ignored).
// Usage, with the dev server running: node wheeler-roads-shots.mjs [base-url]
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { collectProblems, launch, newPage, report } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5193/'
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', 'stage-9', 'wheeler-roads')

// The views: the valley from Cloverdale to the Gray Ranch, Cloverdale and Guadalupe Pass, and the stretch with "9 m.".
const views = [
  ['z10', { zoom: 10, center: [-108.9, 31.45] }],
  ['z11', { zoom: 11, center: [-108.92, 31.42] }],
  ['z12', { zoom: 12, center: [-108.885, 31.47] }],
  // North of the test area: the clipped Butterfield trail through Stein's Pass and Lordsburg.
  ['butterfield-z10', { zoom: 10, center: [-108.95, 32.25] }],
]

await mkdir(out, { recursive: true })
const browser = await launch()
const page = await newPage(browser, { viewport: { width: 1400, height: 1000 } })
const problems = collectProblems(page)
await page.goto(`${baseUrl}lab.html?debug#wheeler`, { waitUntil: 'load' })
await page.waitForSelector('.wheeler-map canvas')
const roads = page.getByRole('checkbox', { name: 'Historic roads (test area)' })
for (const [zoom, view] of views) {
  for (const state of ['before', 'after']) {
    if ((await roads.isChecked()) !== (state === 'after')) await roads.click()
    await page.evaluate((v) => window.__wheelerMap.jumpTo(v), view)
    await page.waitForTimeout(500)
    await page.evaluate(() => new Promise((r) => (window.__wheelerMap.loaded() ? setTimeout(r, 300) : window.__wheelerMap.once('idle', r))))
    await page.waitForTimeout(1200)
    const name = `roads-${zoom}-${state}`
    await page.locator('.wheeler-map').screenshot({ path: path.join(out, `${name}.jpg`), type: 'jpeg', quality: 85 })
    console.log(`${name}.jpg`)
  }
}
await browser.close()
report(problems)
