import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'
import { reviewData } from './scripts/review-data.ts'
import { siteFacts } from './scripts/site-facts.ts'

// GitHub Pages serves the site under /crossing-map/, and the stage preview under /crossing-map/preview/.
// tools/build-site.sh sets VITE_BASE for each.
const base = process.env.VITE_BASE ?? '/'

// The preview holds unreleased work: search engines are asked not to index it, so they list only the release.
function noindexPreview(): Plugin {
  return {
    name: 'noindex-preview',
    transformIndexHtml: (html) =>
      base.endsWith('/preview/') ? html.replace('</head>', '    <meta name="robots" content="noindex" />\n  </head>') : html,
  }
}

export default defineConfig({
  base,
  plugins: [react(), siteFacts(), reviewData(), noindexPreview()],
  // The How it's built page imports docs/decisions/*.md from outside site/ (design section 4.3).
  server: { fs: { allow: ['..'] } },
})
