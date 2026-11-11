// Browse the Cartographers' Guild for style references, at a reader's pace.
// Usage: node guild-browse/browse.mjs [--budget 40]
//
// Runs the installed Chrome Canary in a visible window with a persistent
// profile in private/browser-profile/, so cookies and any login carry over
// between runs. Opens one page at a time, pauses 8-20 s between pages, and
// stops at the page budget or at any challenge or block page.
// Screenshots go to private/inspiration/guild/ (git-ignored); thread titles
// and URLs are appended to docs/inspiration/guild.md (committed).
import { appendFile, mkdir, readFile, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { chromium } from 'playwright'

const ROOT = fileURLToPath(new URL('../..', import.meta.url))
const PROFILE = path.join(ROOT, 'private', 'browser-profile')
const SHOTS = path.join(ROOT, 'private', 'inspiration', 'guild')
const INDEX = path.join(ROOT, 'docs', 'inspiration', 'guild.md')
const HOME = 'https://www.cartographersguild.com/forum.php'

const budgetArg = process.argv.indexOf('--budget')
const BUDGET = budgetArg > 0 ? Number(process.argv[budgetArg + 1]) : 40

// Forums to open from the forum index, matched on link text, most useful first.
const FORUMS = [/^tutorials\/how-to$/i, /^pen and paper/i, /^mapping elements$/i, /^finished maps$/i, /^mapping challenge archive$/i]
// Listing pages to read per forum; thread titles on later pages are older.
const LISTING_PAGES = 3
// Threads worth a screenshot, matched on thread title (plan, section 5.1).
const TOPICS = [
  /gidde/i, /hand[- ]?drawn/i, /mountains?/i, /weathered|old paper|parchment/i, /saderan/i,
  /western|desert|mexic|arizona|sonora|chihuahua|southwest/i, /old map|treasure map|antique/i,
  /hachur/i, /ink(ed)?\b/i,
]

let pagesUsed = 0
const pause = () => new Promise((r) => setTimeout(r, 8000 + Math.random() * 12000))

async function visit(page, url) {
  if (pagesUsed >= BUDGET) return false
  pagesUsed++
  const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
  const title = await page.title()
  const status = response?.status() ?? 0
  if (status === 403 || status === 429 || /just a moment|attention required|access denied|captcha/i.test(title)) {
    throw new Error(`Stopped: the site answered ${status} "${title}" at ${url}. Not retrying.`)
  }
  if (await page.getByText('You are not logged in').count()) {
    throw new Error(
      'Stopped: the forum needs a login. Run `npm run guild-login`, log in, and close the window; then run this again.',
    )
  }
  // Scroll down the page in steps, as a reader would.
  for (let i = 0; i < 4; i++) {
    await page.mouse.wheel(0, 600 + Math.random() * 400)
    await page.waitForTimeout(700 + Math.random() * 900)
  }
  return true
}

async function links(page, selector) {
  return page.$$eval(selector, (as) =>
    as.map((a) => ({ text: a.textContent.trim().replace(/\s+/g, ' '), href: a.href })).filter((l) => l.text && l.href),
  )
}

async function indexedUrls() {
  if (!existsSync(INDEX)) {
    await writeFile(
      INDEX,
      '# Cartographers\' Guild references\n\nThreads read for style inspiration. Screenshots stay in `private/inspiration/guild/`; nothing from the Guild is published. Written by `tools/guild-browse/browse.mjs`; add a note on what to take from each.\n\n| Date | Thread | Note |\n| --- | --- | --- |\n',
    )
  }
  return new Set([...(await readFile(INDEX, 'utf8')).matchAll(/\]\((https?:[^)]+)\)/g)].map((m) => m[1]))
}

async function main() {
  await mkdir(SHOTS, { recursive: true })
  await mkdir(path.dirname(INDEX), { recursive: true })
  const seen = await indexedUrls()

  const context = await chromium.launchPersistentContext(PROFILE, {
    channel: 'chrome-canary',
    headless: false,
    viewport: null,
  })
  const page = context.pages()[0] ?? (await context.newPage())
  const saved = []
  try {
    await visit(page, HOME)
    const forumLinks = (await links(page, 'a[href*="forumdisplay"], a[href*="/forums/"]'))
      .filter((l) => FORUMS.some((re) => re.test(l.text)))
    const forums = [...new Map(forumLinks.map((l) => [l.href, l])).values()]
    console.log(`Forums matched: ${forums.map((f) => f.text).join(', ') || 'none'}`)

    for (const forum of FORUMS.map((re) => forums.find((f) => re.test(f.text))).filter(Boolean)) {
      const unique = new Map()
      for (let n = 1; n <= LISTING_PAGES; n++) {
        await pause()
        if (!(await visit(page, n === 1 ? forum.href : `${forum.href}&page=${n}`))) break
        // vBulletin marks each thread's title link with class "title"; other links on the row go to pages or posts.
        for (const l of await links(page, 'a.title[href*="showthread"]')) {
          const id = new URL(l.href).searchParams.get('t')
          const href = `https://www.cartographersguild.com/showthread.php?t=${id}`
          if (id && TOPICS.some((re) => re.test(l.text)) && !seen.has(href)) unique.set(href, { text: l.text, href })
        }
      }
      console.log(`${forum.text}: ${unique.size} matching threads`)
      for (const thread of unique.values()) {
        await pause()
        if (!(await visit(page, thread.href))) break
        const slug = thread.text.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 60)
        const id = thread.href.match(/(\d+)/)?.[1] ?? String(pagesUsed)
        await page.screenshot({ path: path.join(SHOTS, `${id}-${slug}.png`), fullPage: true })
        const title = thread.text.replace(/\|/g, '/')
        await appendFile(INDEX, `| ${new Date().toISOString().slice(0, 10)} | [${title}](${thread.href}) | |\n`)
        seen.add(thread.href)
        saved.push(title)
        console.log(`Saved ${pagesUsed}/${BUDGET}: ${title}`)
      }
      if (pagesUsed >= BUDGET) break
    }
  } finally {
    await context.close()
    console.log(`Pages opened: ${pagesUsed}. Threads saved: ${saved.length}.`)
  }
}

main().catch((e) => {
  console.error(e.message)
  process.exit(1)
})
