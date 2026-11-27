import { describe, expect, it } from 'vitest'
import { crawlerFiles, headTags } from './seo.ts'

const SITE = 'https://thecrossingmap.com/'

describe('search engine and link preview tags', () => {
  it('gives the release a canonical link, a preview image and structured data', () => {
    const html = headTags('/', SITE).join('\n')
    expect(html).toContain('<link rel="canonical" href="https://thecrossingmap.com/" />')
    expect(html).toContain('<meta property="og:image" content="https://thecrossingmap.com/og-image.jpg" />')
    expect(html).not.toContain('noindex')
    const json = JSON.parse(html.match(/<script type="application\/ld\+json">(.*)<\/script>/)![1])
    const dataset = json['@graph'].find((n: { '@type': string }) => n['@type'] === 'Dataset')
    expect(dataset.license).toBe('https://creativecommons.org/licenses/by/4.0/')
    expect(dataset.distribution).toContainEqual(expect.objectContaining({ contentUrl: `${SITE}data/places.geojson` }))
    // The translations' English is not licensed (decision 0047), so the dataset never offers it.
    expect(JSON.stringify(dataset)).not.toContain('translations')
  })

  it('keeps the preview out of search but gives its links a picture', () => {
    const html = headTags('/preview/', SITE).join('\n')
    expect(html).toContain('<meta name="robots" content="noindex" />')
    expect(html).toContain('<meta property="og:url" content="https://thecrossingmap.com/preview/" />')
    expect(html).not.toMatch(/canonical|ld\+json/)
  })

  it('follows the address when the site lives under a path', () => {
    const html = headTags('/crossing-map/', 'https://jburkinshaw.github.io/crossing-map/').join('\n')
    expect(html).toContain('href="https://jburkinshaw.github.io/crossing-map/"')
  })

  it('adds nothing but the noindex without an address', () => {
    expect(headTags('/', undefined)).toEqual([])
    expect(headTags('/preview/', undefined)).toEqual(['<meta name="robots" content="noindex" />'])
  })

  it('writes robots.txt and the sitemap for the release alone', () => {
    const files = crawlerFiles('/', SITE)
    expect(files['robots.txt']).toContain('Sitemap: https://thecrossingmap.com/sitemap.xml')
    expect(files['robots.txt']).not.toMatch(/Disallow/)
    expect(files['sitemap.xml']).toContain('<loc>https://thecrossingmap.com/</loc>')
    expect(crawlerFiles('/preview/', SITE)).toEqual({})
    expect(crawlerFiles('/', undefined)).toEqual({})
  })
})
