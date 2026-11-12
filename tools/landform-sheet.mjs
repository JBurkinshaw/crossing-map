// The landform review sheet (stage 3): the glyph families, and the map where
// crossing.landforms finds clusters of mesas, domes and ridges, with the chosen
// relief treatment. Saves review/stage-3/landforms/{glyphs.png,<view>.jpg}.
// Usage: node landform-sheet.mjs [base-url]   (needs the built site served, as for relief-sheet.mjs)
import { mkdir, readdir, writeFile } from 'node:fs/promises'
import { fileURLToPath, pathToFileURL } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.argv[2] ?? 'http://localhost:4173/'
const repo = fileURLToPath(new URL('..', import.meta.url))
const out = path.join(repo, 'review', 'stage-3', 'landforms')
const svgDir = path.join(repo, 'art', 'glyphs', 'svg')
const families = ['peak', 'dome', 'mesa', 'butte', 'cone', 'ridge']
// Centres of the densest clusters of non-peak glyphs in data/mountain_glyphs.geojson, named for the
// summit at each centre, plus the Pilares, where the relief test hachures also show.
const views = {
  'torre-tres-ojitos': { lon: -108.3, lat: 28.85 },
  'la-gloria': { lon: -108.92, lat: 29.46 },
  'mesa-la-pelona': { lon: -109.92, lat: 30.07 },
  'el-tecolote': { lon: -108.2, lat: 28.03 },
  pilares: { lon: -109.31, lat: 30.85 },
}

await mkdir(out, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 })
const problems = []
page.on('console', (m) => m.type() === 'error' && problems.push(m.text().slice(0, 160)))

// The families: each shape and its mirrored twin, at twice their map size.
const files = new Set(await readdir(svgDir))
const rows = families
  .map((f) => {
    const cells = [...files].filter((n) => n.startsWith(`${f}-`)).sort()
    return `<tr><th>${f}</th>${cells.map((n) => `<td><img src="${pathToFileURL(path.join(svgDir, n)).href}"></td>`).join('')}</tr>`
  })
  .join('')
const html = path.join(out, 'glyphs.html')
await writeFile(html, `<!doctype html><meta charset="utf-8"><style>
  body{background:#e4ddcc;margin:16px;font:14px Georgia,serif} th{text-align:left;padding-right:12px;font-weight:normal;font-style:italic}
  img{zoom:2;display:block}</style><table>${rows}</table>`)
await page.setViewportSize({ width: 4200, height: 900 })
await page.goto(pathToFileURL(html).href, { waitUntil: 'load' })
await page.screenshot({ path: path.join(out, 'glyphs.png'), fullPage: true })
await page.setViewportSize({ width: 1440, height: 900 })
console.log('Glyphs: glyphs.png')

for (const [name, v] of Object.entries(views)) {
  await page.goto('about:blank')
  await page.goto(`${baseUrl}?relief=swiss-soft#map=9.5/${v.lat}/${v.lon}`, { waitUntil: 'load' })
  await page.waitForSelector('canvas.maplibregl-canvas')
  await page.waitForTimeout(3500)
  await page.screenshot({ path: path.join(out, `${name}.jpg`), type: 'jpeg', quality: 88 })
  console.log(`View: ${name}.jpg`)
}
await browser.close()
console.log(problems.length ? `Problems:\n${[...new Set(problems)].join('\n')}` : 'No console errors.')
