import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import type { Plugin } from 'vite'

// The local review modes (?review=..., dev server only) read a review packet and write the owner's verdicts back
// beside it. A packet lives in review/experiments/<packet>/ unless it names its own directory (relative to the repo
// root). Only these packets and files are served, and only the files under `write` are written.
type Packet = { dir?: string; read: string[]; write: string[] }
const PACKETS: Record<string, Packet> = {
  'least-cost': {
    read: ['routes-modeled.geojson', 'routes-plain.geojson', 'results.csv', 'review.csv'],
    write: ['review.csv'],
  },
  // Where each stop sits on its landform (?review=positions).
  positions: {
    dir: 'review/positions',
    read: ['candidates.geojson', 'results.csv', 'review.csv'],
    write: ['review.csv'],
  },
}
const REPO = resolve(import.meta.dirname, '..', '..')
const folder = (name: string, packet: Packet) => resolve(REPO, packet.dir ?? join('review', 'experiments', name))

export function reviewData(): Plugin {
  return {
    name: 'review-data',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__review', (req, res, next) => {
        const [packet, file] = (req.url ?? '').split('?')[0].split('/').filter(Boolean)
        const allowed = Object.hasOwn(PACKETS, packet) ? PACKETS[packet] : undefined
        if (!allowed) return next()
        const path = join(folder(packet, allowed), file ?? '')
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
            // A packet whose directory is missing answers 500 rather than taking the dev server down.
            try {
              writeFileSync(path, Buffer.concat(chunks))
              res.statusCode = 204
            } catch {
              res.statusCode = 500
            }
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
