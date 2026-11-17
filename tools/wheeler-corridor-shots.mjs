// Screenshots for the Wheeler hachures on the site (review/stage-9/wheeler-hachures-corridor): the main map,
// desktop, at four places in the journeys corridor at zooms 10, 11 and 12, saved under the given prefix. The
// production set it was first compared with is gone (decision 0024), so a new run shows the Wheeler set only.
// Saves private/review/stage-9/wheeler-hachures-corridor/<place>-z<zoom>-<prefix>.jpg.
// Usage, with the dev server running: node tools/wheeler-corridor-shots.mjs <prefix> [base-url]
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { collectProblems, gotoMap, launch, newPage, report, settle } from './lib/browser.mjs'

const [prefix, baseUrl = 'http://localhost:5194/'] = process.argv.slice(2)
if (!prefix) {
  console.error('Usage: node tools/wheeler-corridor-shots.mjs <prefix> [base-url]')
  process.exit(1)
}
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', 'stage-9', 'wheeler-hachures-corridor')
// [lon, lat] of each place, all inside the corridor.
const places = {
  peloncillos: [-109.013, 31.667],
  animas: [-108.77, 31.56],
  'sierra-el-tigre': [-109.165, 30.55],
  babicora: [-107.75, 29.25],
}
const zooms = [10, 11, 12]

await mkdir(out, { recursive: true })
const browser = await launch()
const page = await newPage(browser)
const problems = collectProblems(page, { ignore: /maptiler|403/i })
for (const [place, [lon, lat]] of Object.entries(places)) {
  for (const zoom of zooms) {
    await gotoMap(page, baseUrl, { zoom, lat, lon }, { debug: true })
    await settle(page, { pause: 1500, timeout: 60000 })
    const name = `${place}-z${zoom}-${prefix}.jpg`
    await page.screenshot({ path: path.join(out, name), type: 'jpeg', quality: 85 })
    console.log(name)
  }
}
await browser.close()
report(problems)
