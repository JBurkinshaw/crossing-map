import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { INCIPIT_WORDS, readLines, translationPages } from './translation-pages.ts'

// The static pages against the rules the app follows (docs/design.md, sections 3 and 11; decision 0085), on the
// published data.
const lines = readLines()
const pages = translationPages({ base: '/', head: () => [] })
const episodes: { summary: string }[] = JSON.parse(readFileSync(new URL('../../data/episodes.json', import.meta.url), 'utf8'))
const spanish = (html: string) => [...html.matchAll(/<span class="es" lang="es">(.*?)<\/span>/g)].map((m) => m[1])
const unescape = (s: string) => s.replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')

describe('the static translation pages', () => {
  it('has an index and a page for each Part', () => {
    expect(Object.keys(pages).sort()).toEqual([
      'translations/index.html',
      'translations/part-1/index.html',
      'translations/part-2/index.html',
      'translations/part-3/index.html',
      'translations/part-4/index.html',
    ])
  })

  for (const part of [1, 2, 3, 4]) {
    const html = pages[`translations/part-${part}/index.html`]
    const mine = lines.filter((l) => l.part === part)

    it(`Part ${part}: shows each of its lines once, as a published incipit of at most ${INCIPIT_WORDS} words`, () => {
      const shown = spanish(html).map(unescape)
      expect(shown).toEqual(mine.map((l) => l.es_incipit))
      for (const s of shown) expect(s.split(/\s+/).length).toBeLessThanOrEqual(INCIPIT_WORDS)
    })

    it(`Part ${part}: puts the spoiler notice above the first line and folds every episode shut`, () => {
      expect(html.indexOf('<strong>Spoilers.</strong>')).toBeGreaterThan(-1)
      expect(html.indexOf('<strong>Spoilers.</strong>')).toBeLessThan(html.indexOf('<details>'))
      expect(html).not.toMatch(/<details[^>]*\bopen\b/)
    })

    it(`Part ${part}: keeps every line out of search snippets`, () => {
      const blocks = [...html.matchAll(/<div data-nosnippet>([\s\S]*?)<\/div>/g)].map((m) => m[1]).join('')
      expect(spanish(blocks)).toHaveLength(mine.length)
    })

    it(`Part ${part}: shows no episode summary`, () => {
      for (const e of episodes) expect(html).not.toContain(e.summary)
    })
  }

  it('shows no line on the index', () => {
    expect(spanish(pages['translations/index.html'])).toEqual([])
  })
})
