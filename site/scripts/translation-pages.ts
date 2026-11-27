import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { CAMPBELL_CREDIT, CAMPBELL_GUIDE } from '../src/data/campbell.ts'

// The Spanish of the novel as static pages that search engines can read (decision 0085): an index at
// /translations/ and one page per Part. Each line shows its incipit and page, this site's English, and the page of
// Campbell's guide that lists it. The app is not needed to read them.
//
// They are the one place the site shows lines past a reader's progress, so they carry a spoiler notice above the
// first line, every episode is folded shut, and every line sits in a data-nosnippet block, so that a search result
// never quotes a line.

type Line = { id: string; part: number; episode: string; page: number | null; es_incipit: string; en: string | null; guide_page: number | null }

// Only an incipit of at most this many words may be published (docs/design.md, section 3, and crossing.validate).
export const INCIPIT_WORDS = 5
const NUMERALS = ['I', 'II', 'III', 'IV']
const PARTS = [1, 2, 3, 4]

const pagePath = (part?: number) => (part ? `translations/part-${part}/` : 'translations/')
export const PATHS = [pagePath(), ...PARTS.map(pagePath)]

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

// In the book's order: an id holds the episode and the line's place in it (tr-1-03-001).
export function readLines(): Line[] {
  const data = fileURLToPath(new URL('../../data/', import.meta.url))
  const lines: Line[] = JSON.parse(readFileSync(join(data, 'translations.json'), 'utf8'))
  return lines.sort((a, b) => a.id.localeCompare(b.id))
}

type Options = {
  base: string
  // Tags for the page's head, from site/scripts/seo.ts: canonical, Open Graph, or the preview's noindex.
  head: (path: string) => string[]
  // The GoatCounter site code, in the release only (decision 0083).
  counter?: string
}

const STYLE = `
  :root { color: #2b2118; background: #f7f5e6; font-family: 'IM Fell English', 'Iowan Old Style', Georgia, serif; }
  body { max-width: 42rem; margin: 0 auto; padding: 1.5rem 1rem 3rem; line-height: 1.45; }
  a { color: inherit; }
  nav { font-size: 0.95rem; }
  .notice { border: 2px solid #8a2b1b; padding: 0.75rem 1rem; margin: 1.25rem 0; }
  details { border-top: 1px solid rgba(43, 33, 24, 0.35); padding: 0.4rem 0; }
  summary { cursor: pointer; font-size: 1.1rem; }
  ul.lines { list-style: none; padding: 0; margin: 0.5rem 0 0.75rem; }
  ul.lines li { margin: 0 0 0.85rem; }
  .es { font-style: italic; }
  .meta { color: rgba(43, 33, 24, 0.7); font-size: 0.9rem; }
  footer { margin-top: 2rem; font-size: 0.9rem; color: rgba(43, 33, 24, 0.7); }
`

// The request site/src/analytics.ts sends, for a page outside the app.
const countScript = (site: string, path: string) =>
  `<script>(function(){if(navigator.webdriver)return;var q=new URLSearchParams(location.search).get('ref');` +
  `var r=q&&/^[\\w.-]{1,40}$/.test(q)?q:document.referrer;` +
  `var f=new URLSearchParams({p:${JSON.stringify(`/${path.replace(/\/$/, '')}`)},s:String(screen.width),rnd:Math.random().toString(36).slice(2,7)});` +
  `if(r)f.set('r',r);try{navigator.sendBeacon&&navigator.sendBeacon('https://${site}.goatcounter.com/count?'+f)}catch(e){}})()</script>`

function page(o: Options, path: string, title: string, description: string, body: string): string {
  const head = [
    `<meta name="description" content="${esc(description)}" />`,
    `<meta property="og:type" content="website" />`,
    `<meta property="og:title" content="${esc(title)}" />`,
    `<meta property="og:description" content="${esc(description)}" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
    ...o.head(path),
  ]
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${esc(title)}</title>
    <link rel="icon" href="${o.base}favicon.svg" type="image/svg+xml" />
${head.map((t) => `    ${t}\n`).join('')}    <style>${STYLE}</style>
  </head>
  <body>
    <nav><a href="${o.base}">The Crossing: a reading map</a> · <a href="${o.base}${pagePath()}">Spanish in the novel</a></nav>
${body}
    <footer>
      <p>Only the opening words of each Spanish line are shown, at most ${INCIPIT_WORDS}, with the page in the Vintage paperback (approximate). The English is this site's own. It is not licensed for reuse, because translating the novel is its author's right. The translations are drafts: suggest a better one from the line on the map.</p>
      <p>${esc(CAMPBELL_CREDIT)}. The site links to his guide by page and does not copy it.</p>
    </footer>
${o.counter ? `    ${countScript(o.counter, path)}\n` : ''}  </body>
</html>
`
}

function partPage(o: Options, part: number, lines: Line[]): string {
  const numeral = NUMERALS[part - 1]
  const episodes = [...new Set(lines.map((l) => l.episode))]
  const groups = episodes.map((episode) => {
    const mine = lines.filter((l) => l.episode === episode)
    const pages = mine.map((l) => l.page).filter((p): p is number => p !== null)
    const [first, last] = [Math.min(...pages), Math.max(...pages)]
    const span = !pages.length ? '' : first === last ? ` · page ${first}` : ` · pages ${first}–${last}`
    const items = mine
      .map((l) => {
        const guide = l.guide_page
          ? `<br /><span class="meta"><a href="${CAMPBELL_GUIDE}" rel="noopener">Campbell's guide</a>, listed under page ${l.guide_page}</span>`
          : ''
        return (
          `          <li id="${esc(l.id)}"><span class="es" lang="es">${esc(l.es_incipit)}</span> <span class="meta">p. ${l.page ?? '?'}</span><br />` +
          `${esc(l.en ?? 'Translation still to come.')}${guide}</li>`
        )
      })
      .join('\n')
    return `    <details>
      <summary>Episode ${Number(episode.split('-')[1])}${span} · ${mine.length} ${mine.length === 1 ? 'line' : 'lines'}</summary>
      <div data-nosnippet>
        <ul class="lines">
${items}
        </ul>
      </div>
    </details>`
  })
  const title = `The Crossing, Part ${numeral}: Spanish translations by page`
  const description = `Every Spanish line in Part ${numeral} of Cormac McCarthy's The Crossing, by page in the Vintage edition, with an English translation of each.`
  const body = `    <h1>The Crossing, Part ${numeral}: the Spanish, in English</h1>
    <p class="notice"><strong>Spoilers.</strong> This page lists the Spanish of Part ${numeral} in the order the book has it, and an English line can give away what happens. Each episode is folded shut: open only those you have read. <a href="${o.base}">The map</a> hides everything past the page you have reached.</p>
${groups.join('\n')}
    <p>${PARTS.filter((p) => p !== part)
      .map((p) => `<a href="${o.base}${pagePath(p)}">Part ${NUMERALS[p - 1]}</a>`)
      .join(' · ')}</p>`
  return page(o, pagePath(part), title, description, body)
}

function indexPage(o: Options, lines: Line[]): string {
  const title = 'The Crossing by Cormac McCarthy: Spanish translations of every line'
  const description = `The ${lines.length} Spanish lines and words in Cormac McCarthy's The Crossing, Part by Part and by page, each with an English translation and a link to Campbell's guide.`
  const parts = PARTS.map((p) => {
    const n = lines.filter((l) => l.part === p).length
    return `      <li><a href="${o.base}${pagePath(p)}">Part ${NUMERALS[p - 1]}</a>: ${n} lines</li>`
  }).join('\n')
  const body = `    <h1>The Spanish in <cite>The Crossing</cite>, in English</h1>
    <p>Much of Cormac McCarthy's <cite>The Crossing</cite> is spoken in Spanish, and the book does not translate it. These pages give every Spanish line and word in the novel, ${lines.length} in all, with this site's English and the page in the Vintage paperback. Where Lt. Jim Campbell's translation guide lists a line, its page in the guide is given too.</p>
    <p>On <a href="${o.base}">the reading map</a>, each line is also shown where it was spoken, and only once you have read that far.</p>
    <p class="notice"><strong>Spoilers.</strong> Each Part's page shows its lines in the book's order. Every episode is folded shut, so you can open only those you have read.</p>
    <ul>
${parts}
    </ul>`
  return page(o, pagePath(), title, description, body)
}

// Every page, keyed by its path under the build's base (for example `translations/part-1/index.html`).
export function translationPages(o: Options, lines: Line[] = readLines()): Record<string, string> {
  const files: Record<string, string> = { [`${pagePath()}index.html`]: indexPage(o, lines) }
  for (const part of PARTS) {
    files[`${pagePath(part)}index.html`] = partPage(o, part, lines.filter((l) => l.part === part))
  }
  return files
}
