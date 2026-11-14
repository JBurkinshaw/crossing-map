// Copy the published data from data/ into the app, so the site and the open-data downloads read one set of
// files. The map also gets a trimmed copy of the summit glyphs in public/data/map/: the download keeps every
// property, while the map fetches only those its style reads (src/map/relief.ts and spoiler/filter.ts).
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'

const from = new URL('../../data/', import.meta.url)
const to = new URL('../public/data/', import.meta.url)
rmSync(to, { recursive: true, force: true })
cpSync(from, to, { recursive: true })

const GLYPH_PROPERTIES = ['name', 'size', 'landform', 'glyph', 'flip', 'glyph_scale', 'glyph_rotate', 'elevation_m', 'prominence_m', 'first_seen']
const glyphs = JSON.parse(readFileSync(new URL('mountain_glyphs.geojson', from), 'utf8'))
const trimmed = {
  type: 'FeatureCollection',
  features: glyphs.features.map((f) => ({
    type: 'Feature',
    geometry: f.geometry,
    properties: Object.fromEntries(GLYPH_PROPERTIES.filter((k) => k in f.properties).map((k) => [k, f.properties[k]])),
  })),
}
mkdirSync(new URL('map/', to), { recursive: true })
writeFileSync(new URL('map/mountain_glyphs.geojson', to), JSON.stringify(trimmed))

// The landform name lines the map letters (decision 0023), trimmed to the properties the style reads.
const LANDFORM_PROPERTIES = ['name', 'kind', 'len_m', 'mpp0', 'first_seen', 'place_ref']
const landforms = JSON.parse(readFileSync(new URL('landforms.geojson', from), 'utf8'))
writeFileSync(new URL('map/landforms.geojson', to), JSON.stringify({
  type: 'FeatureCollection',
  features: landforms.features.map((f) => ({
    type: 'Feature',
    geometry: f.geometry,
    properties: Object.fromEntries(LANDFORM_PROPERTIES.filter((k) => k in f.properties).map((k) => [k, f.properties[k]])),
  })),
}))
