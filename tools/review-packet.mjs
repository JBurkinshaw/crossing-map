// Screenshots for a stage review packet: the same named views every stage,
// desktop and phone, so one stage compares with the next.
// Usage: node review-packet.mjs <stage-number> [base-url]
import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium, devices } from 'playwright'

const stage = process.argv[2]
const baseUrl = process.argv[3] ?? 'http://localhost:4173/'
if (!stage) {
  console.error('Usage: node review-packet.mjs <stage-number> [base-url]')
  process.exit(1)
}

// [lon, lat, zoom], passed as `#map=zoom/lat/lon`. `whole` is the opening view.
const views = {
  whole: null,
  bootheel: [-108.8, 31.6, 8.5],
  bavispe: [-109.0, 30.6, 8.5],
  'casas-grandes': [-107.95, 30.35, 9],
  babicora: [-107.7, 29.3, 8.5],
}
const profiles = {
  desktop: { viewport: { width: 1440, height: 900 } },
  phone: devices['iPhone 14'],
}

const outDir = path.join(fileURLToPath(new URL('..', import.meta.url)), 'review', `stage-${stage}`, 'screenshots')
await mkdir(outDir, { recursive: true })

const browser = await chromium.launch()
const problems = []
for (const [profileName, profile] of Object.entries(profiles)) {
  const context = await browser.newContext(profile)
  const page = await context.newPage()
  page.on('console', (m) => m.type() === 'error' && problems.push(`${profileName}: console: ${m.text()}`))
  page.on('pageerror', (e) => problems.push(`${profileName}: pageerror: ${e.message}`))
  page.on('requestfailed', (r) => {
    // MapLibre cancels tile requests the view no longer needs; that is not a failure.
    if (r.failure()?.errorText !== 'net::ERR_ABORTED') problems.push(`${profileName}: failed: ${r.url()} ${r.failure()?.errorText}`)
  })
  for (const [name, view] of Object.entries(views)) {
    const hash = view ? `#map=${view[2]}/${view[1]}/${view[0]}` : ''
    // A hash-only change does not reload the page, so navigate fresh each time.
    await page.goto('about:blank')
    await page.goto(baseUrl + hash, { waitUntil: 'load' })
    await page.waitForSelector('canvas.maplibregl-canvas', { timeout: 15000 })
    // Tiles stream in after the canvas appears; a fixed pause is enough for a static site.
    await page.waitForTimeout(2500)
    await page.screenshot({ path: path.join(outDir, `${name}-${profileName}.png`) })
  }
  await context.close()
}
await browser.close()

await writeFile(path.join(outDir, 'problems.txt'), problems.length ? problems.join('\n') + '\n' : 'none\n')
console.log(`Screenshots in ${outDir}`)
console.log(problems.length ? `Problems:\n${problems.join('\n')}` : 'No console errors or failed requests.')
