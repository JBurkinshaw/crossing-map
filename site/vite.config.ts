import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { reviewData } from './scripts/review-data.ts'
import { seo } from './scripts/seo.ts'
import { siteFacts } from './scripts/site-facts.ts'

// GitHub Pages serves the site at the root of its domain, and the stage preview under /preview/. The deploy
// workflow works out each base from the SITE_URL repository variable, and tools/build-site.sh sets VITE_BASE.
const base = process.env.VITE_BASE ?? '/'

export default defineConfig({
  base,
  plugins: [react(), siteFacts(), reviewData(), seo(base)],
  // The How it's built page imports docs/decisions/*.md from outside site/ (design section 4.3).
  server: { fs: { allow: ['..'] } },
})
