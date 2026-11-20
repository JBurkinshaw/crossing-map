// The spoiler-leak test, browser half (docs/design.md, section 11, acceptance criteria, and decision 0054). The data
// half, site/src/spoiler/leak.test.ts, runs the spoiler filters on the published data at every reading position.
// This half checks that the site shows only what those filters pass. It walks the book once, pressing "Read on"
// from the first episode to the last, and at each episode checks the map's progress filters, the story data given
// to the map and the features it renders, the panel, the journeys offered, and each stop the episode adds (with
// the stop before it, whose road now leads on). At the start of each Part it checks every page (About, How it's
// built, Open questions, Data, Credits) and the reading-progress dialog. Then it moves progress back, opens a link
// to a later stop with a later place saved, and checks once what the walk leaves out: search and the cards it
// opens, the layer key, a later glyph, landform, pass and water name and vignette drawn on the map, the Tilted,
// compare and Oblique views, and the phone drawer at each height. A first visit must open the onboarding dialog,
// and a first visit straight to a page must leave the page and the progress dialog usable.
//
// Usage, with the app running on the dev server or a build made with VITE_DEBUG=1 (the map handle
// window.__map needs one of them):
//   cd site && npm run dev -- --port 5185
//   cd tools && npm run spoiler-leak -- [base-url]     (default http://localhost:5185/)
// Exits 1 on any leak. CI runs it against the pushed commit (.github/workflows/deploy.yml, job spoiler-leak).
import { readFile } from 'node:fs/promises'
import { devices } from 'playwright'
import { launch, newPage, PROGRESS_KEY } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5185/'
const dataDir = new URL('../data/', import.meta.url)
const read = async (name) => JSON.parse(await readFile(new URL(name, dataDir), 'utf8'))
const layers = Object.fromEntries(
  await Promise.all(['places', 'stops', 'areas', 'journeys'].map(async (n) => [n, (await read(`${n}.geojson`)).features])),
)
const elsewhere = await read('elsewhere.json')
const glyphs = (await read('mountain_glyphs.geojson')).features
const vignettes = (await read('vignettes.geojson')).features
const obliqueVignettes = (await read('oblique/vignettes.geojson')).features
const landforms = (await read('landforms.geojson')).features
const waterPlaces = (await read('water_places.geojson')).features
const contextPlaces = (await read('context_places.geojson')).features
// The pass names the map sets across each saddle (crossing.pass_lines), beside the site's other label data.
const passes = JSON.parse(await readFile(new URL('../site/public/labels/passes.geojson', import.meta.url), 'utf8')).features
const translations = await read('translations.json')
// The photos on the cards (decision 0067), by file, with the first episode any card may show it from: its own
// first_seen, else its place's or stop's. A context place always shows ('' here), and so do its photos.
const props = new Map([...layers.places, ...layers.stops].map((f) => [f.properties.id, f.properties]))
const photoFrom = new Map()
for (const e of await read('photos.json')) {
  const place = props.get(e.place_id)
  for (const p of e.photos) {
    const from = p.first_seen ?? (place.role === 'context' ? '' : place.first_seen)
    if (!photoFrom.has(p.file) || from < photoFrom.get(p.file)) photoFrom.set(p.file, from)
  }
}
const episodes = await read('episodes.json')

// The walk moves progress back to here at the end, from the last episode.
const BACK_TO = '1-08'
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
  const { text, names, firstSeen, shownLines, photos } = await page.evaluate(() => {
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
    const photos = [...document.querySelectorAll('.photo img')].map((e) => e.getAttribute('src'))
    return { text: `${panel.innerText}\n${popups}\n${key}`, names, firstSeen, shownLines, photos }
  })
  for (const src of photos) {
    const file = src.slice(src.indexOf('photos/'))
    if (!photoFrom.has(file) || photoFrom.get(file) > reached) leak(where, `photo shown: ${file}`)
  }
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

// The base-map layers the progress filters (PROGRESS_LAYERS in site/src/spoiler/filter.ts). Which features each
// filter lets through is checked on the data by site/src/spoiler/leak.test.ts. Here, that the live map carries
// the filter at the reader's progress: a cut later than that (and later than the land's 1-01) is a leak.
const FILTERED_LAYERS = ['mountain-glyph', 'landform-label', 'pass-label', 'water-place', 'context-place', 'graticule', 'vignette', 'vignette-label']
const CUT = /\["<=",\["to-string",\["get","first_seen"\]\],"([^"]+)"\]/g

async function checkFilters(page, reached, where) {
  const filters = await page.evaluate(
    (ids) => ids.map((id) => [id, window.__map.getLayer(id) ? JSON.stringify(window.__map.getFilter(id)) : null]),
    FILTERED_LAYERS,
  )
  for (const [id, filter] of filters) {
    const cuts = filter ? [...filter.matchAll(CUT)].map((m) => m[1]) : []
    if (cuts.length === 0) leak(where, `${id} has no progress filter`)
    for (const cut of cuts) if (cut > reached && cut > '1-01') leak(where, `${id} shows up to ${cut}`)
  }
}

// One feature of each kind first seen later, gone to and looked for: the check that the map applies its filters.
// Each kind is [what, layer ids, features, zoom, the episode it always shows from].
async function checkDrawn(page, reached, where, kinds) {
  for (const [what, ids, list, zoom, floor] of kinds) {
    const f = list.find((x) => x.properties.first_seen > reached && x.properties.first_seen > floor)
    if (!f) continue
    // A line's label sits near its middle.
    const { type, coordinates } = f.geometry
    const center = type === 'Point' ? coordinates : coordinates[Math.floor(coordinates.length / 2)]
    await page.evaluate(([c, z]) => window.__map.jumpTo({ center: c, zoom: z }), [center, zoom(f)])
    await idle(page)
    const shown = await page.evaluate(
      (ids) => window.__map.queryRenderedFeatures({ layers: ids.filter((id) => window.__map.getLayer(id)) }).map((r) => [r.properties.name, r.properties.first_seen]),
      ids,
    )
    for (const [name, fs] of shown) if (fs > reached && fs > floor) leak(where, `${what} ${name} first seen ${fs}`)
  }
}
const vignetteZoom = (f) => Math.max(f.properties.min_zoom, 9)
const DRAWN = [
  ['glyph', ['mountain-glyph'], glyphs, () => 10, '1-01'],
  ['landform name', ['landform-label'], landforms, () => 9, '1-01'],
  ['pass name', ['pass-label'], passes, () => 10, '1-01'],
  ['water place', ['water-place'], waterPlaces, () => 12, '1-01'],
  ['context place', ['context-place'], contextPlaces, () => 12, '1-01'],
  ['vignette', ['vignette', 'vignette-label'], vignettes, vignetteZoom, ''],
]

// Until the map has drawn what it was asked for (at most 10 s: an idle event can be missed between checks).
async function idle(page) {
  await page.evaluate(
    () => new Promise((done) => (window.__map.loaded() ? done() : (window.__map.once('idle', done), setTimeout(done, 10000)))),
  )
}

// Until the map's filters and story data match `reached` (at most 10 s). The map can report itself loaded before
// React has handed it the filtered data, so idle() alone can return on the frame drawn before. A leak that is still
// there after 10 s is real, and the checks that follow report it.
async function settle(page, reached) {
  await idle(page)
  for (let i = 0; i < 20; i++) {
    const n = leaks.length
    await checkFilters(page, reached, 'settling')
    await checkMap(page, reached, 'settling')
    if (leaks.splice(n).length === 0) return
    await page.waitForTimeout(500)
    await idle(page)
  }
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
const PAGES = ['/about', '/about/how-its-built', '/itinerary', '/open-questions', '/data', '/credits']

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

// The journeys offered: none before its first stop is reached.
async function checkJourneys(page, reached, where) {
  const offered = await page.locator('.journey-pick option').evaluateAll((os) => os.map((o) => o.value))
  for (const journey of offered) {
    const first = layers.stops.filter((f) => f.properties.journey === journey).map((f) => f.properties.first_seen).sort()[0]
    if (!(first <= reached)) leak(where, `journey ${journey} offered before its first stop (${first})`)
  }
}

// Every page, then back to the map where it was.
async function checkPages(page, reached, where, later) {
  const map = await page.evaluate(() => window.location.hash)
  for (const route of PAGES) await checkPage(page, route, reached, where, later)
  await page.evaluate((hash) => (window.location.hash = hash), map)
  await page.waitForTimeout(300)
}

// The stops of a journey reached so far, in the order the panel lists them.
const reachedStops = (journey, reached) =>
  layers.stops.filter((f) => f.properties.journey === journey && f.properties.first_seen <= reached).sort((a, b) => a.properties.sequence - b.properties.sequence)
const stopById = (id) => layers.stops.find((f) => f.properties.id === id)
const placeInHash = (page) => page.evaluate(() => /(?:^#|&)stop=([^&]*)/.exec(window.location.hash)?.[1] ?? null)

// Opens a stop from its journey's "All stops" list, and waits for the address to name it as the reader's place.
// A CI runner draws the map in software, and with every vignette on it the page can take over 5 s to answer.
async function openStop(page, stop, reached) {
  const { id, journey } = stop.properties
  if ((await page.locator('.journey-pick select').inputValue()) !== journey) await page.selectOption('.journey-pick select', journey)
  await page.evaluate(() => (document.querySelector('.all-stops').open = true))
  await page.locator('.all-stops .stop-list button').nth(reachedStops(journey, reached).indexOf(stop)).click()
  await page.waitForFunction((stopId) => window.location.hash.includes(`stop=${stopId}`), id, { timeout: 15000 })
}

// The stop in focus, every line it lists, and the card of the road on from it if lines were spoken there.
async function checkStop(page, reached, where, later, lines) {
  await showAllLines(page, '.stop')
  await checkPanel(page, reached, where, later, lines)
  if (await page.locator('.stop .road-lines').count()) {
    await page.locator('.stop .road-lines').click()
    await showAllLines(page, '.place-card')
    await checkPanel(page, reached, `${where} road`, later, lines)
    await checkMap(page, reached, `${where} road`)
    await page.locator('.place-card .close').click()
  }
}

// Sets progress with the "Where are you up to?" dialog.
async function setProgressInDialog(page, progress) {
  await page.locator('.progress-badge').click()
  await page.locator('dialog[open] .progress-episode').selectOption(progress)
  await page.locator('dialog[open] button.primary').click()
}

// Then two frames, for React to filter the story and bring the stop reached most recently into focus. Reading on
// only adds features, so a frame drawn before the change holds nothing past the new progress, and the checks that
// follow need no wait for tiles.
async function waitForProgress(page, progress) {
  await page.waitForFunction(([k, v]) => localStorage.getItem(k) === v, [PROGRESS_KEY, progress], { timeout: 5000 })
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))))
}

// A first visit: the onboarding dialog, then "not started", the pages, and the phone.
async function checkFirstVisit(browser) {
  const where = 'first visit'
  const later = laterOnlyNames('0-00')
  await checkFirstVisitPages(browser, null)
  const page = await newPage(browser, { viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce', progress: null })
  page.on('pageerror', (e) => leak(where, `page error: ${e.message}`))
  await page.goto(`${baseUrl}?debug`)
  await page.waitForFunction(() => window.__map?.getSource('places'), null, { timeout: 30000 })
  await idle(page)
  if (!(await page.locator('dialog[open]').count())) leak(where, 'onboarding dialog did not open')
  await checkDialogText(page, '0-00', `${where}, onboarding`)
  // Dismissing it keeps spoiler mode on at "not started".
  await page.keyboard.press('Escape')
  if (await page.locator('dialog[open]').count()) leak(where, 'Escape did not close the dialog')
  await checkFilters(page, '0-00', where)
  await checkMap(page, '0-00', where)
  await checkPanel(page, '0-00', where, later)
  await checkPages(page, '0-00', where, later)
  await page.context().close()
  await checkPhone(browser, null, '0-00', later, laterOnlyLines('0-00'))
}

// The book from its first episode to its last. Each episode is reached with "Read on" from the stop reached most
// recently, or with the dialog before the book's first stop. Returns the page, at the last episode.
async function walk(browser) {
  const where = 'walk'
  const page = await newPage(browser, { viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce', progress: episodes[0].episode })
  page.on('pageerror', (e) => leak(where, `page error: ${e.message}`))
  await page.goto(`${baseUrl}?debug`)
  await page.waitForFunction(() => window.__map?.getSource('places'), null, { timeout: 30000 })
  await idle(page)
  if (await page.locator('dialog[open]').count()) leak(where, 'dialog opened although progress is stored')
  let visits = 0
  for (const [i, { episode: reached }] of episodes.entries()) {
    const at = `${where} ${reached}`
    const later = laterOnlyNames(reached)
    const lines = laterOnlyLines(reached)
    // Where the map brought the reader: the stop reached most recently, which offers "Read on" once it is in
    // focus. A frame later the address names it.
    const next = episodes[i + 1]?.episode
    let latest = null
    if (next && layers.stops.some((f) => f.properties.first_seen <= reached)) {
      const offered = await page.waitForSelector('.read-on button', { timeout: 5000 }).then(() => true, () => false)
      if (offered) {
        await page.evaluate(() => new Promise((done) => requestAnimationFrame(done)))
        latest = await placeInHash(page)
      } else leak(at, 'no Read on at the stop reached most recently')
    }
    await checkFilters(page, reached, at)
    await checkMap(page, reached, at)
    await checkPanel(page, reached, at, later, lines)
    await checkJourneys(page, reached, at)
    if (reached.endsWith('-01')) {
      await checkPages(page, reached, at, later)
      await checkProgressDialog(page, reached, `${at}, progress dialog`)
    }
    // The stops this episode adds, and the stop before each, whose road now leads on to it.
    const visit = new Set()
    for (const stop of layers.stops.filter((f) => f.properties.journey && f.properties.first_seen === reached)) {
      const list = reachedStops(stop.properties.journey, reached)
      const k = list.indexOf(stop)
      if (k > 0) visit.add(list[k - 1])
      visit.add(stop)
    }
    for (const stop of visit) {
      await openStop(page, stop, reached)
      await checkStop(page, reached, `${at}, ${stop.properties.id}`, later, lines)
      visits++
    }
    if (!next) break
    if (latest) {
      await openStop(page, stopById(latest), reached)
      await page.locator('.read-on button').click()
    } else await setProgressInDialog(page, next)
    await waitForProgress(page, next)
  }
  console.log(`${where}: ${episodes.length} episodes, ${visits} stop visits`)
  return page
}

// Progress moved back from the end of the book, which leaves a later stop saved as the reader's place, and then a
// link to a later stop opened: neither may show. Then, once, what the walk does not check.
async function checkMovedBack(browser, walked) {
  const reached = BACK_TO
  const where = `back to ${reached}`
  const later = laterOnlyNames(reached)
  const lines = laterOnlyLines(reached)
  await setProgressInDialog(walked, reached)
  await waitForProgress(walked, reached)
  // Moving back, unlike reading on, leaves later features in the frame drawn before. They go once the map has
  // redrawn its story layers. The reader has seen them, so only the settled map counts.
  await settle(walked, reached)
  await checkFilters(walked, reached, where)
  await checkMap(walked, reached, where)
  await checkPanel(walked, reached, where, later, lines)
  const saved = stopById(await walked.evaluate(() => localStorage.getItem('crossing-map.place')))
  if (!(saved?.properties.first_seen <= reached)) leak(where, `saved place ${saved?.properties.id} is past progress`)

  await walked.context().close()

  // A fresh visit with the last stop in the book saved, through a link to the next stop past progress.
  const ahead = layers.stops.find((f) => f.properties.first_seen > reached).properties.id
  const last = layers.stops.reduce((m, f) => (f.properties.first_seen > m.properties.first_seen ? f : m)).properties.id
  const page = await newPage(browser, { viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce', progress: reached })
  page.on('pageerror', (e) => leak(where, `page error: ${e.message}`))
  await page.addInitScript((id) => localStorage.setItem('crossing-map.place', id), last)
  await page.goto(`${baseUrl}?debug#stop=${ahead}`)
  await page.waitForFunction(() => window.__map?.getSource('places'), null, { timeout: 30000 })
  await idle(page)
  const linked = `${where}, link to ${ahead}`
  const opened = stopById(await placeInHash(page))
  if (!(opened?.properties.first_seen <= reached)) leak(linked, `opened at ${opened?.properties.id ?? 'no stop'}`)
  await checkFilters(page, reached, linked)
  await checkMap(page, reached, linked)
  await checkPanel(page, reached, linked, later, lines)

  // Search, in every Part and in Part IV alone: each query's results, then the card its first result opens.
  // Later-only place names and lines are searched for too; they must find nothing.
  const queries = [...SEARCHES, ...[...later].slice(0, 5), ...[...lines].slice(0, 5)]
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
        // Every line a card lists, not only the first few.
        await showAllLines(page, '.panel')
        await checkPanel(page, reached, `${where}, search "${q}" picked`, later, lines)
      }
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

  await checkDrawn(page, reached, where, DRAWN)

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
    await page.getByRole('radio', { name: 'Vintage', exact: true }).click()
  }

  // The Oblique view loads its own copies of the story layers, and draws the vignettes where they put them.
  const obliqueLoaded = page.waitForResponse((r) => r.url().includes('/data/oblique/journeys.geojson'))
  await page.getByRole('radio', { name: 'Oblique', exact: true }).click()
  await obliqueLoaded
  await page.waitForTimeout(500)
  await idle(page)
  await checkFilters(page, reached, `${where}, oblique`)
  await checkMap(page, reached, `${where}, oblique`)
  await checkPanel(page, reached, `${where}, oblique panel`, later, lines)
  await checkDrawn(page, reached, `${where}, oblique`, [['vignette', ['vignette', 'vignette-label'], obliqueVignettes, vignetteZoom, '']])
  await page.context().close()

  await checkFirstVisitPages(browser, reached)
  await checkPhone(browser, reached, reached, later, lines)
}

const started = Date.now()
const browser = await launch()
await checkFirstVisit(browser)
await checkMovedBack(browser, await walk(browser))
await browser.close()
console.log(`${Math.round((Date.now() - started) / 1000)} s`)

if (leaks.length) {
  // The first hundred are enough to see the pattern.
  console.error(`\n${leaks.length} spoiler leaks:\n${leaks.slice(0, 100).join('\n')}`)
  process.exit(1)
}
console.log('\nNo spoiler leaks.')
