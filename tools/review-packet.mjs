// Screenshots for a stage review packet: the same named views every stage,
// desktop and phone, so one stage compares with the next. Screenshots stay out of git: they go to
// private/review/stage-<n>/screenshots/.
// Usage: node review-packet.mjs <stage-number> [base-url]
import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { devices } from 'playwright'
import { collectProblems, gotoMap, launch, newPage } from './lib/browser.mjs'

const stage = process.argv[2]
const baseUrl = process.argv[3] ?? 'http://localhost:4173/'
if (!stage) {
  console.error('Usage: node review-packet.mjs <stage-number> [base-url]')
  process.exit(1)
}

// `whole` is the opening view.
const views = {
  whole: null,
  bootheel: { zoom: 8.5, lat: 31.6, lon: -108.8 },
  bavispe: { zoom: 8.5, lat: 30.6, lon: -109.0 },
  'casas-grandes': { zoom: 9, lat: 30.35, lon: -107.95 },
  babicora: { zoom: 8.5, lat: 29.3, lon: -107.7 },
}
const profiles = {
  desktop: { viewport: { width: 1440, height: 900 } },
  phone: { device: devices['iPhone 14'] },
}

const outDir = path.join(fileURLToPath(new URL('..', import.meta.url)), 'private', 'review', `stage-${stage}`, 'screenshots')
await mkdir(outDir, { recursive: true })

const browser = await launch()
const problems = []
for (const [profileName, profile] of Object.entries(profiles)) {
  const page = await newPage(browser, profile)
  collectProblems(page, { problems, label: profileName })
  page.on('requestfailed', (r) => {
    // MapLibre cancels tile requests the view no longer needs; that is not a failure.
    if (r.failure()?.errorText !== 'net::ERR_ABORTED') problems.push(`${profileName}: failed: ${r.url()} ${r.failure()?.errorText}`)
  })
  for (const [name, view] of Object.entries(views)) {
    await gotoMap(page, baseUrl, view)
    // Tiles stream in after the canvas appears; a fixed pause is enough for a static site.
    await page.waitForTimeout(2500)
    await page.screenshot({ path: path.join(outDir, `${name}-${profileName}.png`) })
  }
  await page.context().close()
}
await browser.close()

await writeFile(path.join(outDir, 'problems.txt'), problems.length ? problems.join('\n') + '\n' : 'none\n')
console.log(`Screenshots in ${outDir}`)
console.log(problems.length ? `Problems:\n${problems.join('\n')}` : 'No console errors or failed requests.')
