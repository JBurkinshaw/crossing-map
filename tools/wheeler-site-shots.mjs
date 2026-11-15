// Before and after screenshots for the Wheeler rollout on the site's map (review/stage-9/wheeler-site): the
// graticule and frame, the water places and the type hierarchy, at zooms 8, 10 and 12 on a desktop and zoom 10 on
// a phone, with the whole book read. Saves private/review/stage-9/wheeler-site/<view>-<label>.jpg.
// Usage, with the dev server or a VITE_DEBUG=1 preview running: node wheeler-site-shots.mjs <label> [base-url]
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { devices } from 'playwright'
import { collectProblems, gotoMap, launch, newPage, report, settle } from './lib/browser.mjs'

const label = process.argv[2]
const baseUrl = process.argv[3] ?? 'http://localhost:5185/'
if (!label) {
  console.error('Usage: node wheeler-site-shots.mjs <label> [base-url]')
  process.exit(1)
}
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', 'stage-9', 'wheeler-site')

// name, zoom, centre, device. The bootheel and the upper Bavispe at 8 and 10 (towns, the graticule); the Guadalupe
// Mountains' springs and San Luis Pass at 12; the Sonoran ranches at 11.
const views = [
  ['desktop-z8', 8, [-108.9, 31.1], 'desktop'],
  ['desktop-z10', 10, [-108.95, 31.3], 'desktop'],
  ['desktop-z12', 12, [-109.06, 31.46], 'desktop'],
  ['desktop-z12-pass', 12, [-108.75, 31.39], 'desktop'],
  ['desktop-z11-bavispe', 11, [-109.15, 30.9], 'desktop'],
  ['phone-z10', 10, [-108.95, 31.3], 'phone'],
]

await mkdir(out, { recursive: true })
const browser = await launch()
const problems = []
for (const [name, zoom, [lon, lat], device] of views) {
  const page = await newPage(browser, device === 'phone' ? { device: devices['iPhone 14'] } : { viewport: { width: 1400, height: 900 } })
  collectProblems(page, { problems, ignore: /maptiler|403/i, label: name })
  await gotoMap(page, baseUrl, { zoom, lat, lon }, { debug: true })
  await settle(page, { pause: 1500 }).catch(() => {})
  const file = `${name}-${label}.jpg`
  await page.screenshot({ path: path.join(out, file), type: 'jpeg', quality: 82 })
  console.log(file)
  await page.context().close()
}
await browser.close()
report(problems)
