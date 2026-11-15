// Screenshots of the context places on the site's map (review/stage-9/context-places): a mining district, a fort,
// ghost towns on the railway, the bootheel's playas and the Sierra Madre's railway tunnels, at zooms 9 to 12 with the
// whole book read. Saves private/review/stage-9/context-places/<view>.jpg.
// Usage, with the dev server or a VITE_DEBUG=1 preview running: node context-places-shots.mjs [base-url]
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { collectProblems, gotoMap, launch, newPage, report, settle } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5185/'
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', 'stage-9', 'context-places')

// name, zoom, centre.
const views = [
  ['silver-city-z9', 9, [-108.2, 32.8]],
  ['silver-city-z10', 10, [-108.2, 32.8]],
  ['pinos-altos-z11', 11, [-108.22, 32.86]],
  ['fort-bayard-z12', 12, [-108.15, 32.8]],
  ['lordsburg-shakespeare-z11', 11, [-108.73, 32.3]],
  ['hachita-playas-z10', 10, [-108.45, 31.95]],
  ['hachita-z12', 12, [-108.33, 31.92]],
  ['animas-valley-z11', 11, [-108.85, 31.6]],
  ['bavispe-z11', 11, [-108.95, 30.55]],
  ['cumbres-tunnels-z12', 12, [-108.08, 29.67]],
]

await mkdir(out, { recursive: true })
const browser = await launch()
const problems = []
for (const [name, zoom, [lon, lat]] of views) {
  const page = await newPage(browser, { viewport: { width: 1400, height: 900 } })
  collectProblems(page, { problems, ignore: /maptiler|403/i, label: name })
  await gotoMap(page, baseUrl, { zoom, lat, lon }, { debug: true })
  await settle(page, { pause: 1500 }).catch(() => {})
  await page.screenshot({ path: path.join(out, `${name}.jpg`), type: 'jpeg', quality: 82 })
  console.log(name)
  await page.context().close()
}
await browser.close()
report(problems)
