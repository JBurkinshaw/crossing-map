// Shared Playwright helpers for the review and test scripts in tools/.
//
// The map handle `window.__map` exists only with `?debug` in the address, and only on the dev server or a build
// made with VITE_DEBUG=1. Scripts that read the map pass `{ debug: true }` to gotoMap.
import { chromium } from 'playwright'

export const PROGRESS_KEY = 'crossing-map.progress'

// Store a reading position before any page script runs. 'all' shows the whole book and keeps the spoiler
// dialog shut, which is what screenshots of the map want.
export const setProgress = (target, value) => target.addInitScript(([k, v]) => localStorage.setItem(k, v), [PROGRESS_KEY, value])

export const launch = () => chromium.launch()

// A page in its own context. `device` is a Playwright device descriptor; `progress: null` is a first visit.
export async function newPage(browser, { viewport = { width: 1400, height: 900 }, deviceScaleFactor = 1, device, progress = 'all', ...options } = {}) {
  const context = await browser.newContext(device ? { ...device, ...options } : { viewport, deviceScaleFactor, ...options })
  if (progress !== null) await setProgress(context, progress)
  return context.newPage()
}

// The map at `{ zoom, lat, lon }` (or the opening view when `view` is null), loaded fresh: a change of hash
// alone would not reload the page.
export async function gotoMap(page, baseUrl, view, { debug = false } = {}) {
  const hash = view ? `#map=${view.zoom}/${view.lat}/${view.lon}` : ''
  await page.goto('about:blank')
  await page.goto(`${baseUrl}${debug ? '?debug' : ''}${hash}`, { waitUntil: 'load' })
  await page.waitForSelector('canvas.maplibregl-canvas', { timeout: 15000 })
  if (debug) await page.waitForFunction(() => window.__map, null, { timeout: 30000 })
}

// Until the debug map handle has stopped moving and loaded every tile in view, then a short pause for fading.
export async function settle(page, { handle = '__map', pause = 800, timeout = 30000 } = {}) {
  await page.waitForFunction((h) => {
    const map = window[h]
    return map && !map.isMoving() && map.loaded() && map.areTilesLoaded()
  }, handle, { timeout })
  await page.waitForTimeout(pause)
}

// Console errors and page errors, skipping messages `ignore` matches. MapTiler refuses localhost (403), so
// scripts that run against the dev server usually ignore /maptiler|403/i.
export function collectProblems(page, { ignore = null, problems = [], label = '' } = {}) {
  const keep = (text) => !ignore || !ignore.test(text)
  const prefix = label ? `${label}: ` : ''
  page.on('console', (m) => m.type() === 'error' && keep(m.text()) && problems.push(`${prefix}${m.text().slice(0, 200)}`))
  page.on('pageerror', (e) => keep(e.message) && problems.push(`${prefix}pageerror: ${e.message}`))
  return problems
}

export const report = (problems) =>
  console.log(problems.length ? `Problems:\n${[...new Set(problems)].join('\n')}` : 'No console errors.')
