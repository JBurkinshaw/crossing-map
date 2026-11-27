import type { Plugin } from 'vite'
import { LAYERS } from './site-facts.ts'

// What search engines and link previews read (decision 0084). The deploy workflow passes the site's public address
// as SITE_URL, and VITE_BASE says which build this is: the release at the root, or the preview under /preview/.
//
// The release gets a canonical link, og:url, og:image, JSON-LD, robots.txt and sitemap.xml. The preview gets
// og:url and og:image, so a shared link still shows the picture, and a noindex tag in place of the rest, so search
// engines list only the release. A build without SITE_URL (the dev server, local and test builds) gets only the
// preview's noindex where it applies.

const IMAGE = { file: 'og-image.jpg', width: 1200, height: 630, alt: "The Crossing's vintage map of the borderlands" }
const CC_BY = 'https://creativecommons.org/licenses/by/4.0/'

// The CC BY layers (decision 0045). translations.json is left out: its English is not licensed (decision 0047).
function structuredData(site: string) {
  const data = `${site}data/`
  const name = 'The Crossing: a reading map'
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebSite',
        name,
        url: site,
        inLanguage: 'en',
        about: { '@type': 'Book', name: 'The Crossing', author: { '@type': 'Person', name: 'Cormac McCarthy' } },
      },
      {
        '@type': 'Dataset',
        name: "Places and journeys of Cormac McCarthy's The Crossing",
        description:
          "Every journey, stop and named place in Cormac McCarthy's novel The Crossing, placed on real geographic data " +
          'in New Mexico, Sonora and Chihuahua. Each feature records how certain its position is, its source, and the ' +
          'episode of the book that first names it. Inferred places are areas with their reasoning.',
        url: site,
        license: CC_BY,
        isAccessibleForFree: true,
        creator: { '@type': 'Organization', name, url: site },
        keywords: ['Cormac McCarthy', 'The Crossing', 'Border Trilogy', 'literary map', 'GeoJSON', 'GeoParquet'],
        spatialCoverage: 'The New Mexico bootheel, Sonora and Chihuahua',
        distribution: LAYERS.flatMap((name) => [
          { '@type': 'DataDownload', encodingFormat: 'application/geo+json', contentUrl: `${data}${name}.geojson` },
          { '@type': 'DataDownload', encodingFormat: 'application/vnd.apache.parquet', contentUrl: `${data}parquet/${name}.parquet` },
        ]),
      },
    ],
  }
}

const attr = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;')

export function headTags(base: string, siteUrl: string | undefined): string[] {
  const preview = base.endsWith('/preview/')
  const tags = preview ? ['<meta name="robots" content="noindex" />'] : []
  if (!siteUrl) return tags
  const url = new URL(base, siteUrl).href
  const image = `${url}${IMAGE.file}`
  tags.push(
    `<meta property="og:url" content="${attr(url)}" />`,
    `<meta property="og:image" content="${attr(image)}" />`,
    `<meta property="og:image:width" content="${IMAGE.width}" />`,
    `<meta property="og:image:height" content="${IMAGE.height}" />`,
    `<meta property="og:image:alt" content="${attr(IMAGE.alt)}" />`,
  )
  if (preview) return tags
  // `<` is escaped so no string in the data can close the script element.
  const json = JSON.stringify(structuredData(url)).replace(/</g, '\\u003c')
  return [`<link rel="canonical" href="${attr(url)}" />`, ...tags, `<script type="application/ld+json">${json}</script>`]
}

// Only the release's robots.txt counts: crawlers read it at the root of the host. It allows everything, the preview
// included, so that crawlers reach the preview's noindex tag.
export function crawlerFiles(base: string, siteUrl: string | undefined): Record<string, string> {
  if (!siteUrl || base.endsWith('/preview/')) return {}
  const url = new URL(base, siteUrl).href
  return {
    'robots.txt': `User-agent: *\nAllow: /\n\nSitemap: ${url}sitemap.xml\n`,
    'sitemap.xml':
      '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      `  <url><loc>${url}</loc></url>\n` +
      '</urlset>\n',
  }
}

export function seo(base: string, siteUrl = process.env.SITE_URL || undefined): Plugin {
  return {
    name: 'seo',
    transformIndexHtml: (html) => {
      const tags = headTags(base, siteUrl)
      return tags.length ? html.replace(/\n\s*<\/head>/, `\n${tags.map((t) => `    ${t}\n`).join('')}  </head>`) : html
    },
    generateBundle() {
      for (const [fileName, source] of Object.entries(crawlerFiles(base, siteUrl))) {
        this.emitFile({ type: 'asset', fileName, source })
      }
    },
  }
}
