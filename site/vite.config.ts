import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { siteFacts } from './scripts/site-facts.ts'

export default defineConfig({
  // GitHub Pages serves the site under /crossing-map/, and the stage preview
  // under /crossing-map/preview/. tools/build-site.sh sets VITE_BASE for each.
  base: process.env.VITE_BASE ?? '/',
  plugins: [react(), siteFacts()],
  // The How it's built page imports docs/decisions/*.md from outside site/ (plan section 4.3).
  server: { fs: { allow: ['..'] } },
})
