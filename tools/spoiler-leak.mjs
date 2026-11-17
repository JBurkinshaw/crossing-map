// The spoiler-leak test (docs/design.md, section 11, acceptance criteria): for several reading positions, load
// the app and check that nothing first seen later shows anywhere: the story data given to the map, the
// features it renders, the stop markers, the panel (journey picker, stop list, stepping through every stop and
// the road card of each stop with talk on the road, "Named elsewhere"), mountain glyphs, landform and pass names,
// water and context places, vignettes (in the Flat and Raised views),
// search results and the cards they open (places and the translations "Spoken here"), the layer key, the
// reading-progress dialog, every page (About, How it's built, Open questions, Data, Credits), the Tilted,
// compare and Raised views, and the phone drawer at each height. A first visit straight to a page must leave
// the page and the progress dialog usable.
//
// Usage, with the app running on the dev server or a build made with VITE_DEBUG=1 (the map handle
// window.__map needs one of them):
//   cd site && npm run dev -- --port 5185
//   cd tools && npm run spoiler-leak -- [base-url]     (default http://localhost:5185/; about 100 seconds per reading position)
// Exits 1 on any leak. CI runs it against the pushed commit (.github/workflows/deploy.yml, job spoiler-leak).
import { readFile } from 'node:fs/promises'
import { devices } from 'playwright'
import { launch, newPage } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5185/'
const dataDir = new URL('../data/', import.meta.url)
const read = async (name) => JSON.parse(await readFile(new URL(name, dataDir), 'utf8'))
const layers = Object.fromEntries(
  await Promise.all(['places', 'stops', 'areas', 'journeys'].map(async (n) => [n, (await read(`${n}.geojson`)).features])),
)
const elsewhere = await read('elsewhere.json')
const glyphs = (await read('mountain_glyphs.geojson')).features
const vignettes = (await read('vignettes.geojson')).features
const raisedVignettes = (await read('raised/vignettes.geojson')).features
const landforms = (await read('landforms.geojson')).features
const waterPlaces = (await read('water_places.geojson')).features
const contextPlaces = (await read('context_places.geojson')).features
// The pass names the map sets across each saddle (crossing.pass_lines), beside the site's other label data.
const passes = JSON.parse(await readFile(new URL('../site/public/labels/passes.geojson', import.meta.url), 'utf8')).features
const translations = await read('translations.json')
const episodes = await read('episodes.json')

// null is a first visit (nothing stored); the rest are stored settings. Episode ids sort in reading order.
// SPOILER_POINTS=1-08,3-12 runs only those ("unset" for a first visit).
const POINTS = process.env.SPOILER_POINTS
  ? process.env.SPOILER_POINTS.split(',').map((p) => (p === 'unset' ? null : p))
  : [null, 'none', '1-03', '1-08', '2-04', '3-08', '3-12', '4-05', '4-08', 'all']
const reachedOf = (p) => (p === null || p === 'none' ? '0-00' : p === 'all' ? '9-99' : p)
// Context towns are never named in the book; the schema shows them at every reading position.
const allowed = (props, reached) => props.role === 'context' || props.first_seen <= reached
const EPISODE_ID = /\b[1-4]-(0[1-9]|1[0-4])\b/g

function reachedNames(reached) {
  const all = [...Object.values(layers).flat().map((f) => f.properties), ...elsewhere, ...glyphs.map((f) => f.properties), ...vignettes.map((f) => f.properties)]
  return new Set(all.filter((p) => allowed(p, reached)).map((p) => p.name))
}

// The map's title cartouche names these at every reading position (site/src/map/MapView.tsx).
const ALWAYS_SHOWN = new Set(['Sonora', 'Chihuahua', 'New Mexico'])

function laterOnlyNames(reached) {
  const all = [...Object.values(layers).flat().map((f) => f.properties), ...elsewhere, ...glyphs.map((f) => f.properties), ...vignettes.map((f) => f.properties)]
  const early = new Set(all.filter((p) => allowed(p, reached)).map((p) => p.name))
  return new Set(all.filter((p) => !allowed(p, reached) && !early.has(p.name) && !ALWAYS_SHOWN.has(p.name)).map((p) => p.name))
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
    // Folded sections count too: open them, so innerText includes them.
    for (const d of panel.querySelectorAll('details')) d.open = true
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

// Base-map layers whose features first seen 1-01 are the land itself, named from gazetteers: they show at every
// reading position, "not started" included (PROGRESS_LAYERS in site/src/spoiler/filter.ts).
const LAND_LAYERS = new Set(['mountain-glyph', 'landform-label', 'pass-label', 'water-place', 'graticule'].map((id) => `rendered ${id}`))

// What the map holds and draws: the GeoJSON in each story source, and every rendered feature with a first_seen.
async function checkMap(page, reached, where) {
  const found = await page.evaluate(async () => {
    const map = window.__map
    const out = []
    for (const id of ['places', 'stops', 'areas', 'journeys', 'cluster-zone', 'corridor']) {
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
    const land = LAND_LAYERS.has(kind) && first_seen === '1-01'
    if (!land && !allowed({ first_seen, role }, reached)) leak(where, `${kind} ${id} first seen ${first_seen}`)
  }
  return found.length
}

// Vignettes drawn later than this point: go to each, inside its zoom range, and look for it.
async function checkVignettes(page, reached, where, list) {
  for (const v of list.filter((f) => f.properties.first_seen > reached)) {
    const [lon, lat] = v.geometry.coordinates
    const zoom = Math.max(v.properties.min_zoom, 9)
    await page.evaluate(([lo, la, z]) => window.__map.jumpTo({ center: [lo, la], zoom: z }), [lon, lat, zoom])
    await idle(page)
    const shown = await page.evaluate(() => window.__map.queryRenderedFeatures({ layers: ['vignette', 'vignette-label'].filter((id) => window.__map.getLayer(id)) })
      .map((f) => [f.properties.name, f.properties.first_seen]))
    for (const [name, fs] of shown) if (fs > reached) leak(where, `vignette ${name} first seen ${fs}`)
  }
}

// Until the map has drawn what it was asked for (at most 10 s: an idle event can be missed between checks).
async function idle(page) {
  await page.evaluate(
    () => new Promise((done) => (window.__map.loaded() ? done() : (window.__map.once('idle', done), setTimeout(done, 10000)))),
  )
}

// Every line a list holds: open its episode groups (TranslationList), then click each "Show all".
async function showAllLines(page, scope) {
  await page.evaluate((s) => document.querySelectorAll(`${s} details.translation-group`).forEach((d) => (d.open = true)), scope)
  // Each click removes its button, so click the first left until none is.
  const more = page.locator(`${scope} .translations + .text-button`)
  while (await more.count()) await more.first().click()
}


// The site's pages. A later name that is part of a reached one ("Madera" in "Sierra de la Madera", "Bavispe" in
// "Crossing of the Bavispe") is already known to the reader, so it is not a leak.
const PAGES = ['/about', '/about/how-its-built', '/open-questions', '/data', '/credits']

async function checkPage(page, route, reached, where, later) {
  await page.evaluate((r) => (window.location.hash = `#${r}`), route)
  await page.waitForSelector('.page h1')
  await page.waitForTimeout(300)
  const pageText = await page.evaluate(() => ({
    firstSeen: [...document.querySelectorAll('.page [data-first-seen]')].map((e) => [e.textContent.trim().slice(0, 60), e.dataset.firstSeen]),
    text: document.querySelector('.page').innerText,
  }))
  for (const [label, first_seen] of pageText.firstSeen) if (!allowed({ first_seen }, reached)) leak(`${where}, ${route}`, `item first seen ${first_seen}: ${label}`)
  // The decision records name places and events from the whole book in prose the name check cannot catch, so they
  // stay hidden behind a warning until the reader has reached the end.
  if (route === '/about/how-its-built' && reached < episodes.at(-1).episode && (await page.locator('.page .record').count())) {
    leak(`${where}, ${route}`, 'decision records shown')
  }
  const known = [...reachedNames(reached)]
  for (const name of later) {
    if (pageText.text.includes(name) && !known.some((k) => k.includes(name))) leak(`${where}, ${route}`, `later name shown: ${name}`)
  }
}

// The text of the open dialog must not summarise any episode past `reached`.
async function checkDialogText(page, reached, where) {
  const text = await page.locator('dialog[open]').innerText()
  for (const e of episodes) if (e.episode > reached && e.summary && text.includes(e.summary)) leak(where, `progress dialog summarises ${e.episode}`)
}

// The reading-progress dialog, opened from the badge: moved to the last episode with the picker, then with the
// percentage shortcut, it must not summarise episodes past the stored progress.
async function checkProgressDialog(page, reached, where) {
  if (!(await page.locator('dialog.progress-dialog[open]').count())) await page.locator('.progress-badge').click()
  await page.locator('dialog[open] .progress-episode').selectOption(episodes.at(-1).episode)
  await page.waitForTimeout(200)
  await checkDialogText(page, reached, `${where}, picker`)
  await page.locator('dialog[open]').getByLabel(/percentage/).fill('100')
  await page.waitForTimeout(200)
  await checkDialogText(page, reached, `${where}, percentage`)
  await page.keyboard.press('Escape')
}

// A first visit opened straight on a page: the page and the progress dialog must both be usable (nothing open
// inside an inert subtree), and choosing a position must work: "Not yet", then "Show the map up to here".
async function checkFirstVisitPages(browser, point) {
  for (const route of PAGES) {
    const where = `progress ${point ?? 'unset'}, first visit to ${route}`
    const page = await newPage(browser, { viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce', progress: point })
    page.on('pageerror', (e) => leak(where, `page error: ${e.message}`))
    await page.goto(`${baseUrl}?debug#${route}`)
    await page.waitForSelector('.page h1')
    await page.waitForTimeout(500)
    const blocked = await page.evaluate(() => [...document.querySelectorAll('dialog[open], .page')].filter((e) => e.closest('[inert]')).map((e) => e.className))
    for (const c of blocked) leak(where, `${c} is inside an inert element`)
    if (await page.locator('dialog[open]').count()) {
      await page
        .locator('dialog[open]')
        .getByRole('button', { name: /^Not yet/ })
        .click({ timeout: 3000 })
        .then(() => page.locator('dialog[open] button.primary').click({ timeout: 3000 }))
        .catch(() => leak(where, 'progress dialog cannot be used'))
    }
    // The page's own links must answer too.
    await page.locator('.page nav a', { hasText: 'Credits' }).click({ timeout: 3000 }).catch(() => leak(where, 'page links cannot be used'))
    await page.context().close()
  }
}

// The phone layout: the drawer at each height (Home is peek, End is full, ArrowUp steps), and its peek row.
async function checkPhone(browser, point, reached, later, lines) {
  const where = `progress ${point ?? 'unset'}, phone`
  const page = await newPage(browser, { device: devices['iPhone 14'], reducedMotion: 'reduce', progress: point })
  page.on('pageerror', (e) => leak(where, `page error: ${e.message}`))
  await page.goto(`${baseUrl}?debug`)
  await page.waitForFunction(() => window.__map?.getSource('places'), null, { timeout: 30000 })
  if (await page.locator('dialog[open]').count()) await page.keyboard.press('Escape')
  const handle = page.locator('.drawer-handle')
  for (const [key, height] of [['Home', 'peek'], ['ArrowUp', 'half'], ['End', 'full']]) {
    await handle.focus()
    await page.keyboard.press(key)
    await page.waitForTimeout(300)
    await checkPanel(page, reached, `${where}, drawer ${height}`, later, lines)
  }
  await checkMap(page, reached, where)
  await page.context().close()
}

const browser = await launch()
for (const point of POINTS) {
  const reached = reachedOf(point)
  const later = laterOnlyNames(reached)
  const lines = laterOnlyLines(reached)
  const where = `progress ${point ?? 'unset'}`
  await checkFirstVisitPages(browser, point)
  const page = await newPage(browser, { viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce', progress: point })
  page.on('pageerror', (e) => leak(where, `page error: ${e.message}`))
  await page.goto(`${baseUrl}?debug`)
  await page.waitForFunction(() => window.__map?.getSource('places'), null, { timeout: 30000 })
  await idle(page)

  // A first visit opens the onboarding dialog; dismissing it keeps spoiler mode on at "not started".
  const dialogOpen = await page.locator('dialog[open]').count()
  if (point === null) {
    if (!dialogOpen) leak(where, 'onboarding dialog did not open')
    await checkDialogText(page, reached, `${where}, onboarding`)
    await page.keyboard.press('Escape')
    if (await page.locator('dialog[open]').count()) leak(where, 'Escape did not close the dialog')
  } else if (dialogOpen) leak(where, 'dialog opened although progress is stored')

  const features = await checkMap(page, reached, `${where}, flat`)
  await checkPanel(page, reached, `${where}, panel`, later)

  // Every page; the Open questions page lists only the questions reached.
  for (const route of PAGES) await checkPage(page, route, reached, where, later)
  await page.evaluate(() => (window.location.hash = ''))
  await page.waitForTimeout(500)
  if (point !== null && point !== 'all') await checkProgressDialog(page, reached, `${where}, progress dialog`)

  // Every journey offered, stepped through stop by stop with Next.
  const options = await page.locator('.journey-pick option').evaluateAll((os) => os.map((o) => o.value))
  let steps = 0
  for (const journey of options) {
    const first = layers.stops.filter((f) => f.properties.journey === journey).map((f) => f.properties.first_seen).sort()[0]
    if (!(first <= reached)) leak(where, `journey ${journey} offered before its first stop (${first})`)
    await page.selectOption('.journey-pick select', journey)
    const next = page.getByRole('button', { name: 'Next' })
    for (;;) {
      await showAllLines(page, '.stop')
      await checkPanel(page, reached, `${where}, ${journey} step ${steps}`, later, lines)
      // Talk on the road from this stop: its road's card, every line, and the corridor on the map.
      if (await page.locator('.stop .road-lines').count()) {
        await page.locator('.stop .road-lines').click()
        await showAllLines(page, '.place-card')
        await checkPanel(page, reached, `${where}, ${journey} step ${steps} road`, later, lines)
        await checkMap(page, reached, `${where}, ${journey} step ${steps} road`)
        await page.locator('.place-card .close').click()
      }
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
        await showAllLines(page, '.panel')
        await checkPanel(page, reached, `${where}, search "${q}" picked, all lines`, later, lines)
      }
      searched++
    }
  }
  await page.selectOption('.search select', '0')
  await page.fill('.search input', '')

  // The layer key, opened, on each of its tabs.
  await page.locator('.layer-key-toggle').click()
  for (const tab of ['The story', 'The land']) {
    await page.getByRole('tab', { name: tab }).click()
    await page.waitForTimeout(300)
    await checkPanel(page, reached, `${where}, layer key, ${tab}`, later, lines)
  }

  // Glyphs named later than this point: go to each and look at what the map draws there.
  // Glyphs first seen 1-01 are the land itself, named from gazetteers; they show at every position.
  for (const g of glyphs.filter((f) => f.properties.first_seen > reached && f.properties.first_seen > '1-01')) {
    const [lon, lat] = g.geometry.coordinates
    await page.evaluate(([lo, la]) => window.__map.jumpTo({ center: [lo, la], zoom: 10 }), [lon, lat])
    await idle(page)
    const shown = await page.evaluate(() => window.__map.queryRenderedFeatures({ layers: ['mountain-glyph'] }).map((f) => [f.properties.name, f.properties.first_seen]))
    for (const [name, fs] of shown) if (fs > reached && fs > '1-01') leak(where, `glyph ${name} first seen ${fs}`)
  }

  // Landform names the book gives later than this point: go to the middle of each line and look for its label.
  // As with the glyphs, names first seen 1-01 are the land itself, named from gazetteers, and show at every position.
  for (const l of landforms.filter((f) => f.properties.first_seen > reached && f.properties.first_seen > '1-01')) {
    const line = l.geometry.coordinates
    const [lon, lat] = line[Math.floor(line.length / 2)]
    await page.evaluate(([lo, la]) => window.__map.jumpTo({ center: [lo, la], zoom: 9 }), [lon, lat])
    await idle(page)
    const shown = await page.evaluate(() => window.__map.queryRenderedFeatures({ layers: ['landform-label'] }).map((f) => [f.properties.name, f.properties.first_seen]))
    for (const [name, fs] of shown) if (fs > reached && fs > '1-01') leak(where, `landform name ${name} first seen ${fs}`)
  }

  // Pass names the book gives later than this point, and water and context places first seen later (the map draws
  // only the gazetteer's, all 1-01, so none may show): go to each and look at what the map draws there.
  const seenLater = (f) => f.properties.first_seen > reached && f.properties.first_seen > '1-01'
  for (const [what, layer, zoom, list] of [['pass name', 'pass-label', 10, passes], ['water place', 'water-place', 12, waterPlaces],
    ['context place', 'context-place', 12, contextPlaces]]) {
    for (const f of list.filter(seenLater)) {
      await page.evaluate(([lo, la, z]) => window.__map.jumpTo({ center: [lo, la], zoom: z }), [...f.geometry.coordinates, zoom])
      await idle(page)
      const shown = await page.evaluate((id) => window.__map.queryRenderedFeatures({ layers: [id] }).map((r) => [r.properties.name, r.properties.first_seen]), layer)
      for (const [name, fs] of shown) if (fs > reached && fs > '1-01') leak(where, `${what} ${name} first seen ${fs}`)
    }
  }

  await checkVignettes(page, reached, where, vignettes)

  // The Tilted view, then compare mode when satellite is available (it needs the MapTiler key). The switches
  // fold under the Map button; clicks inside the open box leave it open.
  await page.getByRole('button', { name: 'Map options' }).click()
  await page.getByRole('radio', { name: 'Tilted', exact: true }).click()
  await page.waitForTimeout(500)
  await idle(page)
  await checkMap(page, reached, `${where}, tilted`)
  await page.getByRole('radio', { name: 'Flat', exact: true }).click()
  const compare = page.getByRole('radio', { name: /^Compare/ })
  if (await compare.isEnabled()) {
    await compare.click()
    await page.waitForTimeout(1000)
    await idle(page)
    await checkMap(page, reached, `${where}, compare`)
    await checkPanel(page, reached, `${where}, compare panel`, later, lines)
    await page.getByRole('radio', { name: 'Classic', exact: true }).click()
  }

  // The Raised view loads its own copies of the story layers.
  const raisedLoaded = page.waitForResponse((r) => r.url().includes('/data/raised/journeys.geojson'))
  await page.getByRole('radio', { name: 'Raised', exact: true }).click()
  await raisedLoaded
  await page.waitForTimeout(500)
  await idle(page)
  await checkMap(page, reached, `${where}, raised`)
  await checkPanel(page, reached, `${where}, raised panel`, later, lines)
  // In the Raised view the drawings stand where their raised copies put them.
  await checkVignettes(page, reached, `${where}, raised`, raisedVignettes)

  console.log(`${where}: ${features} map features checked, ${options.length} journeys offered, ${steps} panel steps, ${searched} searches`)
  await page.context().close()
  await checkPhone(browser, point, reached, later, lines)
}
await browser.close()

if (leaks.length) {
  // The first hundred are enough to see the pattern.
  console.error(`\n${leaks.length} spoiler leaks:\n${leaks.slice(0, 100).join('\n')}`)
  process.exit(1)
}
console.log('\nNo spoiler leaks.')
