// Copy the published story layers from data/ into the app, so the site and
// the open-data downloads read one set of files.
import { cpSync, rmSync } from 'node:fs'

const from = new URL('../../data/', import.meta.url)
const to = new URL('../public/data/', import.meta.url)
rmSync(to, { recursive: true, force: true })
cpSync(from, to, { recursive: true })
