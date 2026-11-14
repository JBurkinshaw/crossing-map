// Screenshots for the Wheeler card "type" (review/stage-9/wheeler-type): the lab map over the test area at zooms 9
// to 12, before (every parameter as today) and after (the same, with "Type hierarchy (test area)" on), on a desktop
// and a phone. Saves private/review/stage-9/wheeler-type/<device>-z<zoom>-<before|after>.jpg (git-ignored).
// Usage, with the dev server running: node wheeler-type-shots.mjs [base-url]
//   base-url defaults to http://localhost:5197/.
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { collectProblems, launch, newPage, report } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5197/'
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', 'stage-9', 'wheeler-type')
// The test area's middle at zooms 9 and 10; the Animas Mountains and Valley at 11; San Luis Pass and the San Luis
// Mountains at 12.
const views = [
  [9, [-109.0, 31.05]],
  [10, [-109.0, 31.05]],
  [11, [-108.8, 31.45]],
  [12, [-108.76, 31.38]],
]
const devices = [
  ['desktop', { width: 1400, height: 900 }, 1],
  ['phone', { width: 390, height: 844 }, 3],
]

await mkdir(out, { recursive: true })
const browser = await launch()
const problems = []
for (const [device, viewport, scale] of devices) {
  const page = await newPage(browser, { viewport, deviceScaleFactor: scale })
  collectProblems(page, { problems })
  await page.goto(`${baseUrl}lab.html?debug#wheeler`, { waitUntil: 'load' })
  await page.waitForSelector('.wheeler-map canvas')
  await page.getByRole('button', { name: 'All as today' }).click()
  for (const state of ['before', 'after']) {
    const box = page.getByRole('checkbox', { name: 'Type hierarchy (test area)' })
    if ((await box.isChecked()) !== (state === 'after')) await box.click()
    for (const [zoom, center] of views) {
      await page.evaluate(([z, c]) => window.__wheelerMap.jumpTo({ zoom: z, center: c }), [zoom, center])
      await page.waitForTimeout(600)
      await page.evaluate(() => new Promise((r) => (window.__wheelerMap.loaded() ? r() : window.__wheelerMap.once('idle', r))))
      await page.waitForTimeout(400)
      const name = `${device}-z${zoom}-${state}.jpg`
      await page.locator('.wheeler-map').screenshot({ path: path.join(out, name), type: 'jpeg', quality: 82 })
      console.log(name)
    }
  }
  await page.close()
}
await browser.close()
report(problems)
