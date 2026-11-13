// The spoiler-leak test (docs/plan.md, section 11, acceptance criteria): for several reading positions, load
// the app and check that nothing first seen later shows anywhere: the story data given to the map, the
// features it renders, the stop markers, the panel (journey picker, stop list, stepping through every stop,
// "Named elsewhere"), mountain glyphs, vignettes, search results and the cards they open (places and the
// translations "Spoken here"), the layer key, and the same again in the Raised view.
//
// Usage, with the app running (cd site && npm run dev -- --port 5185, or npm run build && npx vite preview --port 5185):
//   cd tools && npm run spoiler-leak -- [base-url]     (default http://localhost:5185/; about 10 minutes)
// Exits 1 on any leak. CI could run it as a job after "Validate data against schemas" in deploy.yml: npm ci in
// site/ and tools/, `npx playwright install --with-deps chromium`, build the site, start `npx vite preview
// --port 5185 --strictPort` in the background, wait for the port, then run this script. The checks read the
// story data, which ships with the site; whether they run without the release tiles is not yet tried.
import { readFile } from 'node:fs/promises'
import { chromium } from 'playwright'

const baseUrl = process.argv[2] ?? 'http://localhost:5185/'
const dataDir = new URL('../data/', import.meta.url)
const read = async (name) => JSON.parse(await readFile(new URL(name, dataDir), 'utf8'))
const layers = Object.fromEntries(
  await Promise.all(['places', 'stops', 'areas', 'journeys'].map(async (n) => [n, (await read(`${n}.geojson`)).features])),
)
const elsewhere = await read('elsewhere.json')
const glyphs = (await read('mountain_glyphs.geojson')).features
const vignettes = (await read('vignettes.geojson')).features
const translations = await read('translations.json')
const KEY = 'crossing-map.progress'

// null is a first visit (nothing stored); the rest are stored settings. Episode ids sort in reading order.
// SPOILER_POINTS=1-08,3-12 runs only those ("unset" for a first visit).
const POINTS = process.env.SPOILER_POINTS
  ? process.env.SPOILER_POINTS.split(',').map((p) => (p === 'unset' ? null : p))
  : [null, 'none', '1-03', '1-08', '2-04', '3-08', '3-12', '4-05', '4-08', 'all']
const reachedOf = (p) => (p === null || p === 'none' ? '0-00' : p === 'all' ? '9-99' : p)
// Context towns are never named in the book; the schema shows them at every reading position.
const allowed = (props, reached) => props.role === 'context' || props.first_seen <= reached
const EPISODE_ID = /\b[1-4]-(0[1-9]|1[0-4])\b/g

function laterOnlyNames(reached) {
  const all = [...Object.values(layers).flat().map((f) => f.properties), ...elsewhere, ...glyphs.map((f) => f.properties), ...vignettes.map((f) => f.properties)]
  const early = new Set(all.filter((p) => allowed(p, reached)).map((p) => p.name))
  return new Set(all.filter((p) => !allowed(p, reached) && !early.has(p.name)).map((p) => p.name))
}

// Translation text (our English, the Spanish opening) found only in lines first seen later. A line the reader
// has reached can share its words with a later one ("Sí."), so those are left out.
function laterOnlyLines(reached) {
  const texts = (t) => [t.en, t.es_incipit].filter(Boolean)
  const early = new Set(translations.filter((t) => t.first_seen <= reached).flatMap(texts))
  return new Set(translations.filter((t) => t.first_seen > reached).flatMap(texts).filter((x) => !early.has(x)))
}

// Search: words common in the Spanish and the English, the line the plan names as a spoiler, and the names of
// places first seen later. Results and the cards they open must hold only what the reader has reached.
const SEARCHES = ['a', 'el', 'que', 'the', 'se murio', 'casas', 'san', 'rio', 'boyd', 'girl', 'wolf', 'babicora']

const leaks = []
const leak = (where, what) => leaks.push(`${where}: ${what}`)

// The panel's visible text, the names it lists, and the episode ids it cites.
async function checkPanel(page, reached, where, later, lines = new Set()) {
  const { text, names, firstSeen, shownLines } = await page.evaluate(() => {
    const panel = document.querySelector('.panel')
    const key = document.querySelector('.layer-key')?.innerText ?? ''
    const names = [...document.querySelectorAll('.panel li, .panel h2, .maplibregl-popup strong')].map((e) => e.textContent.trim())
    for (const m of document.querySelectorAll('.stop-marker')) names.push(m.getAttribute('aria-label').replace(/^Stop \d+: /, ''))
    const firstSeen = [...document.querySelectorAll('[data-first-seen]')].map((e) => [e.textContent.trim().slice(0, 60), e.dataset.firstSeen, e.dataset.role])
    const popups = [...document.querySelectorAll('.maplibregl-popup')].map((e) => e.innerText).join('\n')
    // Each line's Spanish opening and English, in cards and search results.
    const shownLines = [...document.querySelectorAll('.panel .es, .panel .en')].map((e) => e.textContent.trim())
    return { text: `${panel.innerText}\n${popups}\n${key}`, names, firstSeen, shownLines }
  })
  for (const [label, first_seen, role] of firstSeen) if (!allowed({ first_seen, role }, reached)) leak(where, `element first seen ${first_seen}: ${label}`)
  for (const name of names) if (later.has(name)) leak(where, `later name shown: ${name}`)
  for (const id of text.match(EPISODE_ID) ?? []) if (id > reached) leak(where, `text cites episode ${id}`)
  for (const line of shownLines) if (lines.has(line)) leak(where, `later translation shown: ${line}`)
}

// What the map holds and draws: the GeoJSON in each story source, and every rendered feature with a first_seen.
async function checkMap(page, reached, where) {
  const found = await page.evaluate(async () => {
    const map = window.__map
    const out = []
    for (const id of ['places', 'stops', 'areas', 'journeys']) {
      const src = map.getSource(id)
      if (!src) continue
      const data = await src.getData()
      for (const f of data.features) out.push([`source ${id}`, f.properties.id, f.properties.first_seen, f.properties.role])
    }
    for (const f of map.queryRenderedFeatures()) {
      if (f.properties.first_seen) out.push([`rendered ${f.layer.id}`, f.properties.id ?? f.properties.name, f.properties.first_seen, f.properties.role])
    }
    return out
  })
  for (const [kind, id, first_seen, role] of found) {
    const land = kind === 'rendered mountain-glyph' && first_seen === '1-01'
    if (!land && !allowed({ first_seen, role }, reached)) leak(where, `${kind} ${id} first seen ${first_seen}`)
  }
  return found.length
}

// Until the map has drawn what it was asked for (at most 10 s: an idle event can be missed between checks).
async function idle(page) {
  await page.evaluate(
    () => new Promise((done) => (window.__map.loaded() ? done() : (window.__map.once('idle', done), setTimeout(done, 10000)))),
  )
}

const browser = await chromium.launch()
for (const point of POINTS) {
  const reached = reachedOf(point)
  const later = laterOnlyNames(reached)
  const lines = laterOnlyLines(reached)
  const where = `progress ${point ?? 'unset'}`
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' })
  if (point !== null) await context.addInitScript(([k, v]) => localStorage.setItem(k, v), [KEY, point])
  const page = await context.newPage()
  page.on('pageerror', (e) => leak(where, `page error: ${e.message}`))
  await page.goto(`${baseUrl}?debug`)
  await page.waitForFunction(() => window.__map?.getSource('places'), null, { timeout: 30000 })
  await idle(page)

  // A first visit opens the onboarding dialog; dismissing it keeps spoiler mode on at "not started".
  const dialogOpen = await page.locator('dialog[open]').count()
  if (point === null) {
    if (!dialogOpen) leak(where, 'onboarding dialog did not open')
    await page.keyboard.press('Escape')
    if (await page.locator('dialog[open]').count()) leak(where, 'Escape did not close the dialog')
  } else if (dialogOpen) leak(where, 'dialog opened although progress is stored')

  const features = await checkMap(page, reached, `${where}, flat`)
  await checkPanel(page, reached, `${where}, panel`, later)

  // Every journey offered, stepped through stop by stop with Next.
  const options = await page.locator('.journey-pick option').evaluateAll((os) => os.map((o) => o.value))
  let steps = 0
  for (const journey of options) {
    const first = layers.stops.filter((f) => f.properties.journey === journey).map((f) => f.properties.first_seen).sort()[0]
    if (!(first <= reached)) leak(where, `journey ${journey} offered before its first stop (${first})`)
    await page.selectOption('.journey-pick select', journey)
    const next = page.getByRole('button', { name: 'Next' })
    for (;;) {
      for (const more of await page.locator('.stop .text-button').all()) await more.click()
      await checkPanel(page, reached, `${where}, ${journey} step ${steps}`, later, lines)
      steps++
      if (await next.isDisabled()) break
      await next.click()
    }
  }

  // Search, in every Part and in Part IV alone: each query's results, then the card its first result opens.
  // Later-only place names and lines are searched for too; they must find nothing.
  const queries = [...SEARCHES, ...[...later].slice(0, 5), ...[...lines].slice(0, 5)]
  let searched = 0
  for (const part of ['0', '4']) {
    await page.selectOption('.search select', part)
    for (const q of queries) {
      await page.fill('.search input', q)
      const hits = await page.locator('.search-results li').evaluateAll((ls) => ls.map((l) => [l.textContent.slice(0, 60), l.dataset.firstSeen, l.dataset.role]))
      for (const [label, first_seen, role] of hits) if (!allowed({ first_seen, role }, reached)) leak(where, `search "${q}" found ${label} first seen ${first_seen}`)
      await checkPanel(page, reached, `${where}, search "${q}"`, later, lines)
      if (hits.length && part === '0' && SEARCHES.includes(q)) {
        await page.locator('.search-results button').first().click()
        await page.waitForTimeout(200)
        await checkPanel(page, reached, `${where}, search "${q}" picked`, later, lines)
        // Every line a card lists, not only the first few.
        for (const more of await page.locator('.panel .text-button').all()) await more.click()
        await checkPanel(page, reached, `${where}, search "${q}" picked, all lines`, later, lines)
      }
      searched++
    }
  }
  await page.selectOption('.search select', '0')
  await page.fill('.search input', '')

  // The layer key, opened.
  await page.locator('.layer-key summary').click()
  await page.waitForTimeout(300)
  await checkPanel(page, reached, `${where}, layer key`, later, lines)

  // Glyphs named later than this point: go to each and look at what the map draws there.
  // Glyphs first seen 1-01 are the land itself, named from gazetteers; they show at every position.
  for (const g of glyphs.filter((f) => f.properties.first_seen > reached && f.properties.first_seen > '1-01')) {
    const [lon, lat] = g.geometry.coordinates
    await page.evaluate(([lo, la]) => window.__map.jumpTo({ center: [lo, la], zoom: 10 }), [lon, lat])
    await idle(page)
    const shown = await page.evaluate(() => window.__map.queryRenderedFeatures({ layers: ['mountain-glyph'] }).map((f) => [f.properties.name, f.properties.first_seen]))
    for (const [name, fs] of shown) if (fs > reached && fs > '1-01') leak(where, `glyph ${name} first seen ${fs}`)
  }

  // Vignettes drawn later than this point: go to each, inside its zoom range, and look for it and its leader.
  for (const v of vignettes.filter((f) => f.properties.first_seen > reached)) {
    // Leader lines are LineStrings: go to where they start.
    const [lon, lat] = v.geometry.type === 'Point' ? v.geometry.coordinates : v.geometry.coordinates[0]
    const zoom = Math.max(v.properties.min_zoom, Math.min(9, v.properties.max_zoom - 0.5))
    await page.evaluate(([lo, la, z]) => window.__map.jumpTo({ center: [lo, la], zoom: z }), [lon, lat, zoom])
    await idle(page)
    const shown = await page.evaluate(() => window.__map.queryRenderedFeatures({ layers: ['vignette', 'vignette-leader'].filter((id) => window.__map.getLayer(id)) })
      .map((f) => [f.properties.name, f.properties.first_seen]))
    for (const [name, fs] of shown) if (fs > reached) leak(where, `vignette ${name} first seen ${fs}`)
  }

  // The Raised view loads its own copies of the story layers.
  const raisedLoaded = page.waitForResponse((r) => r.url().includes('/data/raised/journeys.geojson'))
  await page.getByRole('radio', { name: 'Raised' }).click()
  await raisedLoaded
  await page.waitForTimeout(500)
  await idle(page)
  await checkMap(page, reached, `${where}, raised`)
  await checkPanel(page, reached, `${where}, raised panel`, later, lines)

  console.log(`${where}: ${features} map features checked, ${options.length} journeys offered, ${steps} panel steps, ${searched} searches`)
  await context.close()
}
await browser.close()

if (leaks.length) {
  // The first hundred are enough to see the pattern.
  console.error(`\n${leaks.length} spoiler leaks:\n${leaks.slice(0, 100).join('\n')}`)
  process.exit(1)
}
console.log('\nNo spoiler leaks.')
