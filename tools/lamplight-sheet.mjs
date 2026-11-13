// The lamplight review (plan 5.1): checks that the theme follows the system, is remembered, and swaps without
// losing the camera, the view, the story layers or the spoiler filters; then screenshots both themes at zoom 7,
// 10 and 12.5 (Flat), 12.5 (Raised), the panel and a page. Saves review/stage-6/lamplight/<shot>-<theme>.png.
// Usage: node lamplight-sheet.mjs [base-url] [--checks]   (needs the site served, e.g. npx vite in site/)
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.argv.slice(2).find((a) => !a.startsWith('--')) ?? 'http://localhost:5190/'
const repo = fileURLToPath(new URL('..', import.meta.url))
const out = path.join(repo, 'review', 'stage-6', 'lamplight')
const THEME_KEY = 'crossing-map.theme'
const PROGRESS_KEY = 'crossing-map.progress'
// Around the Pilares, inside the Raised view's corridor.
const PLACE = { lat: 30.79, lon: -109.08 }

await mkdir(out, { recursive: true })
const browser = await chromium.launch()
const problems = []
const check = (ok, what) => {
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}`)
  if (!ok) problems.push(what)
}

async function open({ scheme, progress = 'all', theme = null }) {
  const context = await browser.newContext({ viewport: { width: 1300, height: 820 }, colorScheme: scheme })
  await context.addInitScript(([pk, pv, tk, tv]) => {
    if (location.protocol === 'about:' || sessionStorage.getItem('seeded')) return
    sessionStorage.setItem('seeded', '1')
    localStorage.setItem(pk, pv)
    if (tv) localStorage.setItem(tk, tv)
  }, [PROGRESS_KEY, progress, THEME_KEY, theme])
  const page = await context.newPage()
  // MapTiler refuses localhost (403), which the satellite map reports; that is expected here.
  const expected = (t) => /maptiler|403/i.test(t)
  page.on('console', (m) => m.type() === 'error' && !expected(m.text()) && problems.push(`console: ${m.text().slice(0, 200)}`))
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  return page
}

const settle = async (page) => {
  await page.waitForFunction(() => {
    const map = window.__map
    return map && !map.isMoving() && map.areTilesLoaded()
  }, null, { timeout: 30000 })
  await page.waitForTimeout(800)
}
// Through a blank page, so each visit loads afresh (a change of hash alone would keep the view).
const goto = async (page, zoom, p = PLACE) => {
  await page.goto('about:blank')
  await page.goto(`${baseUrl}?debug#map=${zoom}/${p.lat}/${p.lon}`, { waitUntil: 'load' })
  await page.waitForFunction(() => window.__map)
  await settle(page)
}
const toggle = (page) => page.getByRole('button', { name: 'Lamplight' })
const view = (page, label) => page.getByRole('radiogroup', { name: 'View of the classic map' }).getByRole('radio', { name: label })
const theme = (page) => page.evaluate(() => document.documentElement.dataset.theme)
const paint = (page, layer, prop) => page.evaluate(([l, p]) => window.__map.getPaintProperty(l, p), [layer, prop])
const camera = (page) => page.evaluate(() => {
  const m = window.__map
  return JSON.stringify([m.getCenter().lng.toFixed(5), m.getCenter().lat.toFixed(5), m.getZoom().toFixed(3), m.getPitch()])
})

// 1. The system's scheme sets the theme; a choice is remembered; a choice matching the system is not stored.
{
  const page = await open({ scheme: 'dark' })
  await goto(page, 10)
  check((await theme(page)) === 'lamplight', 'dark system scheme: lamplight')
  check((await paint(page, 'paper', 'background-color')) !== undefined, 'map painted')
  const before = await camera(page)
  await toggle(page).click()
  await settle(page)
  check((await theme(page)) === 'light', 'toggle: light')
  check((await camera(page)) === before, 'camera kept across the switch')
  check((await page.evaluate((k) => localStorage.getItem(k), THEME_KEY)) === 'light', 'choice stored')
  await page.reload({ waitUntil: 'load' })
  await page.waitForFunction(() => window.__map)
  check((await theme(page)) === 'light', 'choice remembered after reload')
  await toggle(page).click()
  check((await page.evaluate((k) => localStorage.getItem(k), THEME_KEY)) === null, 'choice matching the system not stored')
  await page.context().close()
}
{
  const page = await open({ scheme: 'light' })
  await goto(page, 10)
  check((await theme(page)) === 'light', 'light system scheme: light')
  await page.context().close()
}

// 2. Spoiler filtering, the story layers and the Raised view survive a switch.
{
  const page = await open({ scheme: 'light', progress: '1-08' })
  await goto(page, 12.5)
  const filters = () => page.evaluate(() => JSON.stringify(window.__map.getStyle().layers.map((l) => [l.id, l.filter ?? null])))
  const features = () => page.evaluate(() => ['places', 'stops', 'journeys', 'areas']
    .map((s) => window.__map.getSource(s)?._data?.geojson?.features?.length ?? window.__map.getSource(s)?._data?.features?.length ?? null).join(','))
  const ink0 = await paint(page, 'places-label', 'text-color')
  await view(page, 'Raised').click()
  await settle(page)
  await page.waitForFunction(() => window.__map.getLayer('raised-stroke-1'))
  const f0 = await filters()
  const n0 = await features()
  const cam = await camera(page)
  await toggle(page).click()
  await settle(page)
  check((await camera(page)) === cam, 'Raised: camera kept across the switch')
  check(await view(page, 'Raised').getAttribute('aria-checked') === 'true', 'Raised: view kept')
  const vis = (id) => page.evaluate((i) => window.__map.getLayoutProperty(i, 'visibility'), id)
  check((await vis('raised-stroke-1')) === 'visible' && (await vis('hillshade')) === 'none', 'Raised: raised layers shown, flat relief hidden')
  check((await paint(page, 'raised-stroke-1', 'line-color')) === '#9a846f', 'Raised: strokes repainted in lamplight sepia')
  check((await paint(page, 'places-label', 'text-color')) !== ink0, 'story labels repainted')
  check((await paint(page, 'journeys-halo', 'line-color'))?.[6] === '#171512', 'journeys halo on the lamplight paper')
  check((await filters()) === f0, 'spoiler filters unchanged by the switch')
  check((await features()) === n0, 'story data unchanged by the switch')
  check(/glyphs-lamplight$/.test(JSON.stringify(await page.evaluate(() => window.__map.getStyle().sprite)).replace(/"$/, '')), 'sprite swapped')
  await page.context().close()
}

// 3. Screenshots: each shot in both themes (skipped with --checks).
if (!process.argv.includes('--checks')) {
  const shots = [
    ['z7', async (page) => goto(page, 7, { lat: 30.9, lon: -108.6 })],
    ['z10', async (page) => goto(page, 10)],
    ['z12-5', async (page) => goto(page, 12.5)],
    ['z12-5-raised', async (page) => {
      await goto(page, 12.5)
      await view(page, 'Raised').click()
      await settle(page)
    }],
  ]
  for (const scheme of ['light', 'dark']) {
    const name = scheme === 'dark' ? 'lamplight' : 'light'
    const page = await open({ scheme })
    const map = page.locator('.map-area')
    for (const [shot, go] of shots) {
      await go(page)
      await map.screenshot({ path: path.join(out, `${shot}-${name}.png`) })
    }
    // The panel beside the map, with the key open, and a page.
    await goto(page, 9)
    await page.locator('.layer-key summary').click()
    await page.waitForFunction(() => [...document.querySelectorAll('.key-glyph')].some((e) => e.style.backgroundImage))
    await page.waitForTimeout(1500)
    await page.screenshot({ path: path.join(out, `panel-${name}.png`) })
    await page.goto('about:blank')
    await page.goto(`${baseUrl}?debug#/about`, { waitUntil: 'load' })
    await page.waitForTimeout(1200)
    await page.screenshot({ path: path.join(out, `page-${name}.png`) })
    await page.context().close()
    console.log(`${name}: ${shots.length + 2} shots`)
  }
}

await browser.close()
if (problems.length) {
  console.error(`\n${problems.length} problems:\n${problems.join('\n')}`)
  process.exit(1)
}
console.log('\nAll checks passed.')
