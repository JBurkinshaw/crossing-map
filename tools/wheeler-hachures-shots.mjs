// Screenshots for the Wheeler hachure test build (review/stage-9/wheeler-hachures): the lab's Wheeler section at
// places in the test area, at zooms 10, 11 and 12, before (the site's hachures) and after (the toggle "Wheeler
// hachures (test area)"). A third set turns on the rest of the Wheeler lettering and draws the journeys over the
// strokes, in the site's route inks and widths, to check the ink against the type and the routes. The lab does not
// draw the story, so the journeys are added to the page's map for the shot only.
// Saves private/review/stage-9/wheeler-hachures/<place>-z<zoom>-<before|after|story>.jpg.
// Usage, with the dev server running: node tools/wheeler-hachures-shots.mjs [base-url] [only-place,...]
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { collectProblems, launch, newPage, report } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5194/'
const only = process.argv[3]?.split(',')
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', 'stage-9', 'wheeler-hachures')

// [lon, lat] of each place.
const places = {
  peloncillos: [-108.97, 31.43],
  animas: [-108.76, 31.52],
  // Mesa la Chata and Mesa el Güérigo, where the build finds rims.
  mesas: [-109.29, 30.71],
  // The escarpment the build finds most comb on, south of Cerro Agua Zarca.
  rim: [-109.02, 31.06],
}
const zooms = [10, 11, 12]
// The site's route inks (site/src/map/tokens.ts, journeyInks) and widths out of focus (StoryLayers.tsx).
const INKS = { J1: '#4a5560', J2: '#6e1f1c', J3: '#6e1f1c', J4: '#2f5d50', J5: '#6e1f1c', J6: '#6a3d5c', J7: '#6e1f1c' }

async function settle(page) {
  await page.waitForTimeout(400)
  await page.evaluate(() => new Promise((r) => (window.__wheelerMap.loaded() && window.__wheelerMap.areTilesLoaded() ? r() : window.__wheelerMap.once('idle', r))))
  await page.waitForTimeout(600)
}

async function addJourneys(page) {
  await page.evaluate(
    ([data, inks]) => {
      const m = window.__wheelerMap
      const ink = ['match', ['get', 'journey'], ...Object.entries(inks).flat(), '#2b2118']
      m.addSource('shot-journeys', { type: 'geojson', data })
      m.addLayer({ id: 'shot-journeys-casing', type: 'line', source: 'shot-journeys', filter: ['==', ['get', 'kind'], 'route-segment'],
        layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#f1ede2', 'line-width': 3.5, 'line-opacity': 0.5 } })
      m.addLayer({ id: 'shot-journeys-line', type: 'line', source: 'shot-journeys', filter: ['==', ['get', 'kind'], 'route-segment'],
        layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ink, 'line-width': 1.8, 'line-opacity': 0.85 } })
    },
    [`${baseUrl}data/journeys.geojson`, INKS],
  )
}

await mkdir(out, { recursive: true })
const browser = await launch()
const page = await newPage(browser, { viewport: { width: 1000, height: 700 } })
const problems = collectProblems(page, { ignore: /maptiler|403/i })
await page.goto(`${baseUrl}lab.html?debug#wheeler`, { waitUntil: 'load' })
await page.waitForSelector('.wheeler-map canvas')
await page.waitForFunction(() => window.__wheelerMap)
const toggle = page.getByLabel('Wheeler hachures (test area)')

for (const [place, center] of Object.entries(places)) {
  if (only && !only.includes(place)) continue
  for (const zoom of zooms) {
    for (const shot of ['before', 'after', 'story']) {
      await page.getByRole('button', { name: shot === 'story' ? 'All Wheeler' : 'All as today' }).click()
      if (shot === 'before') await toggle.uncheck()
      else await toggle.check()
      await page.evaluate(([c, z]) => window.__wheelerMap.jumpTo({ center: c, zoom: z }), [center, zoom])
      await settle(page)
      if (shot === 'story') {
        await addJourneys(page)
        await settle(page)
      }
      const name = `${place}-z${zoom}-${shot}.jpg`
      await page.locator('.wheeler-map').screenshot({ path: path.join(out, name), type: 'jpeg', quality: 85 })
      console.log(name)
    }
  }
}

await browser.close()
report(problems)
