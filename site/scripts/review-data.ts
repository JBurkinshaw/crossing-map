import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import type { Plugin } from 'vite'

// The local review mode (?review=routes, dev server only) reads a review packet under review/experiments/ and
// writes the owner's verdicts back beside it. Only these packets and files are served; only review.csv is written.
const PACKETS: Record<string, { read: string[]; write: string[] }> = {
  'least-cost': {
    read: ['routes-modeled.geojson', 'routes-plain.geojson', 'results.csv', 'review.csv'],
    write: ['review.csv'],
  },
}
const ROOT = resolve(import.meta.dirname, '..', '..', 'review', 'experiments')

export function reviewData(): Plugin {
  return {
    name: 'review-data',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__review', (req, res, next) => {
        const [packet, file] = (req.url ?? '').split('?')[0].split('/').filter(Boolean)
        const allowed = PACKETS[packet]
        if (!allowed) return next()
        const path = join(ROOT, packet, file ?? '')
        if (req.method === 'GET' && allowed.read.includes(file)) {
          // A verdicts file not yet written reads as empty, not missing.
          if (!existsSync(path)) {
            res.statusCode = allowed.write.includes(file) ? 200 : 404
            return res.end()
          }
          res.setHeader('Content-Type', file.endsWith('.csv') ? 'text/csv; charset=utf-8' : 'application/geo+json')
          return res.end(readFileSync(path))
        }
        if (req.method === 'PUT' && allowed.write.includes(file)) {
          const chunks: Buffer[] = []
          req.on('data', (c: Buffer) => chunks.push(c))
          req.on('end', () => {
            writeFileSync(path, Buffer.concat(chunks))
            res.statusCode = 204
            res.end()
          })
          return
        }
        res.statusCode = 405
        res.end()
      })
    },
  }
}
