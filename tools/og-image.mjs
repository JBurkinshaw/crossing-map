// The preview image that link previews show (og:image, decision 0084), 1200 x 630: the Animas Valley in the
// Tilted view, north up, over J1, with the land cover and the drawings of the trapping episodes. The reading
// position is Part I, episode 6, so nothing later shows. The panel and the map's buttons are left out. Saves
// site/public/og-image.jpg.
//
// Usage, with the dev server or a VITE_DEBUG=1 preview running: node og-image.mjs [base-url]
import { fileURLToPath } from 'node:url'
import { collectProblems, gotoMap, launch, newPage, report, settle } from './lib/browser.mjs'

const baseUrl = process.argv[2] ?? 'http://localhost:5173/'
const out = fileURLToPath(new URL('../site/public/og-image.jpg', import.meta.url))
const WIDTH = 1200
const HEIGHT = 630
const PANEL = 380 // --panel-width in site/src/styles/base.css
const CAMERA = { zoom: 11, center: [-108.95, 31.47], pitch: 60, bearing: 0 }
const HIDE = '.notice, .overview, .map-controls-box, .maplibregl-ctrl-top-left, .maplibregl-ctrl-bottom-left, .maplibregl-ctrl-bottom-right'

const browser = await launch()
// Wider than the image by the panel, so the map itself is 1200 px across.
const page = await newPage(browser, { viewport: { width: WIDTH + PANEL, height: HEIGHT }, progress: '1-06' })
const problems = collectProblems(page, { ignore: /maptiler|403|localStorage/i })
await gotoMap(page, baseUrl, { zoom: CAMERA.zoom, lat: CAMERA.center[1], lon: CAMERA.center[0] }, { debug: true })
await settle(page, { pause: 500 })
await page.getByRole('button', { name: 'Map options' }).click()
await page.getByRole('radio', { name: 'Tilted', exact: true }).click()
await page.keyboard.press('Escape')
// Tilted sets its own pitch as it opens: wait for that, then set the camera.
await page.waitForTimeout(1500)
await page.evaluate((camera) => window.__map.jumpTo(camera), CAMERA)
await page.addStyleTag({ content: `${HIDE} { display: none !important }` })
await settle(page, { pause: 6000, timeout: 60000 })
const box = await page.locator('.map-area').boundingBox()
if (Math.round(box.width) !== WIDTH || Math.round(box.height) !== HEIGHT) {
  throw new Error(`The map is ${box.width} x ${box.height}, not ${WIDTH} x ${HEIGHT}: check PANEL against the site's CSS.`)
}
await page.screenshot({ path: out, type: 'jpeg', quality: 85, clip: box })
await browser.close()
console.log(out)
report(problems)
