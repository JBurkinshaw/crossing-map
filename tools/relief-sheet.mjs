// The relief comparison sheet (plan section 5.2, stage 3): five treatments x
// three test areas x zooms 7, 9 and 11. Captures the middle of the map at 2x
// pixel density for each, then lays each area out at full size as one page
// (rows: treatments, columns: zooms) and saves it as review/stage-3/sheet/<area>.jpg.
// Usage: node relief-sheet.mjs [base-url]   (needs relief-test.pmtiles in the build)
import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath, pathToFileURL } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.argv[2] ?? 'http://localhost:4173/'
const out = path.join(fileURLToPath(new URL('..', import.meta.url)), 'review', 'stage-3', 'sheet')
const areas = {
  peloncillos: { title: 'Peloncillos and the Animas Valley', lon: -108.9, lat: 31.55 },
  pilares: { title: 'The Pilares Teras and the Bavispe barranca', lon: -109.125, lat: 30.75 },
  babicora: { title: 'The Babícora plains', lon: -107.75, lat: 29.3 },
}
const treatments = {
  survey: 'Survey: systematic hachures + glyphs',
  'survey-lines': 'Survey, whole lines: continuous hachures weighted by mean slope + glyphs',
  'survey-noglyphs': 'Survey, no glyphs',
  sierra: 'Sierra: short dense hatches + stipple + glyphs',
  swiss: 'Swiss accent: hillshade + steep-slope hachures + glyphs',
  'swiss-dense': 'Swiss, dense: hillshade + hachures on about half the slopes + glyphs',
  control: 'Control: hillshade only',
}
const zooms = [7, 9, 11]

await mkdir(path.join(out, 'shots'), { recursive: true })
const browser = await chromium.launch()
// 2x pixel density so individual hachure strokes stay sharp when the sheet is zoomed.
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 })
// The middle of the map panel, clear of the controls and cartouche: 900 x 700 CSS px.
const CLIP = { x: 80, y: 100, width: 900, height: 700 }
const problems = []
page.on('console', (m) => m.type() === 'error' && problems.push(m.text().slice(0, 160)))

for (const [area, a] of Object.entries(areas)) {
  for (const t of Object.keys(treatments)) {
    for (const z of zooms) {
      await page.goto('about:blank')
      await page.goto(`${baseUrl}?relief=${t}#map=${z}/${a.lat}/${a.lon}`, { waitUntil: 'load' })
      await page.waitForSelector('canvas.maplibregl-canvas')
      await page.waitForTimeout(3500)
      await page.screenshot({ path: path.join(out, 'shots', `${area}-${t}-z${z}.png`), clip: CLIP })
    }
  }
  const rows = Object.entries(treatments)
    .map(([t, label]) => `<tr><th>${label}</th>${zooms.map((z) => `<td><img src="shots/${area}-${t}-z${z}.png"></td>`).join('')}</tr>`)
    .join('')
  const html = `<!doctype html><meta charset="utf-8"><style>
    body{font:14px Georgia,serif;margin:16px;background:#fff} h1{font-weight:normal;font-size:20px}
    th{text-align:left;width:150px;vertical-align:middle;font-weight:normal;font-style:italic;padding-right:8px}
    td{padding:4px} img{width:900px;border:1px solid #999;display:block}</style>
    <h1>${a.title}: relief treatments at zoom ${zooms.join(', ')}</h1>
    <table><tr><th></th>${zooms.map((z) => `<th style="font-style:normal">Zoom ${z}</th>`).join('')}</tr>${rows}</table>`
  const file = path.join(out, `${area}.html`)
  await writeFile(file, html)
  await page.setViewportSize({ width: 2960, height: 900 })
  await page.goto(pathToFileURL(file).href, { waitUntil: 'load' })
  await page.screenshot({ path: path.join(out, `${area}.jpg`), fullPage: true, type: 'jpeg', quality: 88 })
  await page.setViewportSize({ width: 1440, height: 900 })
  console.log(`Sheet: ${area}.jpg`)
}
await browser.close()
console.log(problems.length ? `Problems:\n${[...new Set(problems)].join('\n')}` : 'No console errors.')
