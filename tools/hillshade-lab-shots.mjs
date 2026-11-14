// Screenshots for the hillshade lab packet (review/stage-8/lab-hillshade/): the classic map in the lab page under
// each named preset, at the test places and zooms, and, with --topo, MapTiler Topo at the same views from the
// published preview (the MapTiler key only works on the Pages origin). Each shot is an 800 x 600 JPEG cut from
// the middle of the map.
// Usage, with the dev server running (cd site && npx vite --port 5192):
//   cd tools && node hillshade-lab-shots.mjs --out <dir> [--presets site,pronounced] [--sharper] [--topo] [--base http://localhost:5192/]
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { parseArgs } from 'node:util'
import { collectProblems, launch, newPage, report } from './lib/browser.mjs'

const { values } = parseArgs({ options: {
  out: { type: 'string' }, presets: { type: 'string', default: 'site' }, sharper: { type: 'boolean', default: false },
  topo: { type: 'boolean', default: false }, base: { type: 'string', default: 'http://localhost:5192/' },
} })
const out = path.resolve(values.out)
await mkdir(out, { recursive: true })
// [lon, lat]: the lab's test places (site/src/lab/hillshade/HillshadeLab.tsx).
const places = {
  peloncillos: [-109.01, 31.6], bavispe: [-109.288, 30.0], babicora: [-107.98, 29.3], animas: [-108.86, 31.55],
}
const zooms = [8, 10, 12]
// The preset buttons' labels by preset id (site/src/lab/hillshade/settings.ts).
const LABELS = { site: 'Site today', s5: 'S5 as built', maptiler: 'MapTiler-like', pronounced: 'Pronounced', soft: 'Soft', imhof: 'Imhof-ish', 'shadow-only': 'Shadows only' }
const W = 800
const H = 600

const browser = await launch()
// Not started: only the land shows, as for a new reader.
const page = await newPage(browser, { progress: 'none', userAgent: 'crossing-map-research/0.1' })
// MapTiler refuses localhost (403); the Topo shots come from the published preview instead.
const problems = collectProblems(page, { ignore: /maptiler|403/i })

const clipAround = async (selector) => {
  const box = await page.locator(selector).first().boundingBox()
  return { x: Math.round(box.x + box.width / 2 - W / 2), y: Math.round(box.y + box.height / 2 - H / 2), width: W, height: H }
}

await page.goto(`${values.base}lab.html?debug#hillshade`)
await page.waitForFunction(() => window.__labMap?.loaded(), null, { timeout: 30000 })
await page.getByLabel('MapTiler Topo beside the map').uncheck()
if (values.sharper) await page.getByLabel(/Sharper terrain/).check()
for (const preset of values.presets.split(',')) {
  await page.getByRole('button', { name: LABELS[preset] ?? preset, exact: true }).click()
  for (const [place, center] of Object.entries(places)) {
    for (const zoom of zooms) {
      await page.evaluate(([c, z]) => window.__labMap.jumpTo({ center: c, zoom: z }), [center, zoom])
      await page.waitForFunction(() => window.__labMap.loaded() && window.__labMap.areTilesLoaded(), null, { timeout: 30000 })
      await page.waitForTimeout(400)
      const file = path.join(out, `${place}-z${zoom}-${preset}${values.sharper ? '-sharper' : ''}.jpg`)
      await page.screenshot({ path: file, type: 'jpeg', quality: 82, clip: await clipAround('.lab-pane') })
    }
  }
}

if (values.topo) {
  // One page load, then hash changes: MapTiler counts a session per map, not per view.
  await page.goto('https://jburkinshaw.github.io/crossing-map/preview/#map=10/31.6/-109.01')
  await page.getByRole('radio', { name: 'Topo' }).click({ timeout: 30000 })
  await page.waitForTimeout(4000)
  for (const [place, [lon, lat]] of Object.entries(places)) {
    for (const zoom of zooms) {
      await page.evaluate((h) => { window.location.hash = h }, `map=${zoom}/${lat}/${lon}`)
      await page.waitForTimeout(5000)
      await page.screenshot({ path: path.join(out, `${place}-z${zoom}-topo.jpg`), type: 'jpeg', quality: 82, clip: await clipAround('.map-area') })
    }
  }
}

await browser.close()
report(problems)
console.log(`Wrote shots to ${out}`)
