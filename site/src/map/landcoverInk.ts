import type { LandCover } from './tokens'

// Land cover drawn in ink (decision 0036), one repeating texture per class, drawn over the land cover's colour, after the engraved land cover of the Carte générale de
// la Martinique (Dépôt général de la Marine, 1831): woods as dots, plantations and gardens as small marks in rows,
// fields as ruled parcels, buildings as small black blocks. Each texture is drawn on a canvas in the browser, with
// a fixed seed, so the same tile always looks the same; nothing here is copied from the map.

export const TILE = 96 // CSS px per side
export const RATIO = 2 // device pixels per CSS pixel, so the marks stay crisp on a high-density screen

type Pen = { ctx: CanvasRenderingContext2D; rnd: () => number; ink: string }

// A small seeded random generator (mulberry32), so a texture is the same on every load.
function seeded(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Marks are drawn three times across each edge, so the texture wraps without a seam.
function wrapped(ctx: CanvasRenderingContext2D, x: number, y: number, draw: (x: number, y: number) => void) {
  for (const dx of [-TILE, 0, TILE]) for (const dy of [-TILE, 0, TILE]) {
    ctx.save()
    draw(x + dx, y + dy)
    ctx.restore()
  }
}

// Points spread on a jittered grid, `n` per tile, so they cover evenly without looking ruled.
function scatter(rnd: () => number, n: number): [number, number][] {
  const side = Math.round(Math.sqrt(n))
  const cell = TILE / side
  const out: [number, number][] = []
  for (let i = 0; i < side; i++) for (let j = 0; j < side; j++) out.push([(i + rnd()) * cell, (j + rnd()) * cell])
  return out
}

const dot = (p: Pen, r: number, alpha: number, n: number) => {
  for (const [x, y] of scatter(p.rnd, n)) {
    const rr = r * (0.75 + 0.5 * p.rnd())
    wrapped(p.ctx, x, y, (cx, cy) => {
      p.ctx.globalAlpha = alpha
      p.ctx.fillStyle = p.ink
      p.ctx.beginPath()
      p.ctx.arc(cx, cy, rr, 0, Math.PI * 2)
      p.ctx.fill()
    })
  }
}

// The textures, by crossing.landcover's classes.
const DRAW: Record<LandCover, (p: Pen) => void> = {
  // Pine: close, dark dots, the woods of the mountain tops.
  pine: (p) => dot(p, 0.85, 0.8, 196),
  // Oak woodland: small open crowns, spaced like the orchard marks.
  oak: (p) => {
    for (const [x, y] of scatter(p.rnd, 49)) {
      const r = 1.3 + 0.5 * p.rnd()
      wrapped(p.ctx, x, y, (cx, cy) => {
        p.ctx.globalAlpha = 0.75
        p.ctx.strokeStyle = p.ink
        p.ctx.lineWidth = 0.6
        p.ctx.beginPath()
        p.ctx.arc(cx, cy, r, 0, Math.PI * 2)
        p.ctx.stroke()
      })
    }
  },
  // Gallery forest and wetland: dense dots, the darkest texture, so the rivers' trees read as a band.
  riparian: (p) => dot(p, 1, 0.85, 256),
  // Grassland: sparse tufts of three short strokes.
  grass: (p) => {
    for (const [x, y] of scatter(p.rnd, 36)) {
      wrapped(p.ctx, x, y, (cx, cy) => {
        p.ctx.globalAlpha = 0.55
        p.ctx.strokeStyle = p.ink
        p.ctx.lineWidth = 0.5
        p.ctx.beginPath()
        for (const dx of [-1.2, 0, 1.2]) {
          p.ctx.moveTo(cx + dx * 0.6, cy)
          p.ctx.lineTo(cx + dx, cy - 2.4)
        }
        p.ctx.stroke()
      })
    }
  },
  // Desert scrub: a fine, open stipple.
  scrub: (p) => dot(p, 0.5, 0.6, 100),
  // Fields: ruled parcels, the lines changing direction from parcel to parcel.
  fields: (p) => {
    const half = TILE / 2
    for (const [px, py, angle] of [[0, 0, 0], [half, 0, Math.PI / 2], [0, half, Math.PI / 2], [half, half, 0]] as const) {
      const ctx = p.ctx
      ctx.save()
      ctx.beginPath()
      ctx.rect(px + 1, py + 1, half - 2, half - 2)
      ctx.clip()
      ctx.translate(px + half / 2, py + half / 2)
      ctx.rotate(angle + (p.rnd() - 0.5) * 0.3)
      ctx.globalAlpha = 0.5
      ctx.strokeStyle = p.ink
      ctx.lineWidth = 0.5
      ctx.beginPath()
      for (let y = -half; y <= half; y += 3) {
        ctx.moveTo(-half, y)
        ctx.lineTo(half, y)
      }
      ctx.stroke()
      ctx.restore()
    }
  },
  // Towns: small black blocks.
  town: (p) => {
    for (const [x, y] of scatter(p.rnd, 25)) {
      const w = 1.8 + 1.4 * p.rnd(), h = 1.4 + 1.2 * p.rnd()
      wrapped(p.ctx, x, y, (cx, cy) => {
        p.ctx.globalAlpha = 0.85
        p.ctx.fillStyle = p.ink
        p.ctx.fillRect(cx - w / 2, cy - h / 2, w, h)
      })
    }
  },
  // Water: lining parallel to the shore is out of reach for a repeating texture, so close level lines.
  water: (p) => {
    p.ctx.globalAlpha = 0.6
    p.ctx.strokeStyle = p.ink
    p.ctx.lineWidth = 0.5
    p.ctx.beginPath()
    for (let y = 1; y < TILE; y += 2.5) {
      p.ctx.moveTo(0, y)
      p.ctx.lineTo(TILE, y)
    }
    p.ctx.stroke()
  },
}

// Each class's texture as MapLibre image data, at RATIO device pixels per CSS pixel. `water` is drawn in the
// water ink, the rest in the map's ink.
export function inkPatterns(ink: string, water: string): { id: string; image: ImageData }[] {
  return (Object.keys(DRAW) as LandCover[]).map((id, i) => {
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = TILE * RATIO
    const ctx = canvas.getContext('2d')!
    ctx.scale(RATIO, RATIO)
    DRAW[id]({ ctx, rnd: seeded(1831 + i), ink: id === 'water' ? water : ink })
    return { id: `ink-${id}`, image: ctx.getImageData(0, 0, canvas.width, canvas.height) }
  })
}

// A texture as a data URL, for a CSS background such as the layer key's swatches.
export function dataUrl(image: ImageData): string {
  const canvas = document.createElement('canvas')
  canvas.width = image.width
  canvas.height = image.height
  canvas.getContext('2d')!.putImageData(image, 0, 0)
  return canvas.toDataURL()
}
