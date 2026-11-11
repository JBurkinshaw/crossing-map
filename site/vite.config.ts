import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  // GitHub Pages serves the site under /crossing-map/, and the stage preview
  // under /crossing-map/preview/. tools/build-site.sh sets VITE_BASE for each.
  base: process.env.VITE_BASE ?? '/',
  plugins: [react()],
})
