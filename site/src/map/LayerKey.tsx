import { useEffect, useMemo, useState } from 'react'
import { JOURNEYS } from '../data/journeys'
import type { Story } from '../data/story'
import { journeyInk, tokens } from './tokens'

// The layer key (legend, plan section 9) for the classic map: one row per kind of mark the map draws, from
// the story it is given. That story is already filtered to the reader's progress, so a journey, a region or
// the false dawn appears in the key only once it can appear on the map; so does the vignettes' row, from the
// vignettes reached.

// The mountain glyph families, drawn from the map's own sprite sheet (art/glyphs/make_glyphs.py).
const GLYPHS: [string, string][] = [
  ['peak', 'Peak'],
  ['ridge', 'Ridge'],
  ['dome', 'Dome'],
  ['mesa', 'Mesa'],
  ['butte', 'Butte'],
  ['cone', 'Cone'],
  ['pass', 'Pass'],
]
// Glyphs at this fraction of their map size, vignettes smaller. The @2x sheet keeps the key sharp.
const GLYPH_SCALE = 0.6
const VIGNETTE_SCALE = 0.4
type Sprite = { icons: Record<string, { x: number; y: number; width: number; height: number }>; width: number; height: number }
type Vignette = { vignette: string; first_seen: string; priority: number }

const sheet = (name: string) => `${import.meta.env.BASE_URL}sprites/${name}`

// The sprite index and the 1x sheet's size, which the @2x sheet is scaled down to.
async function loadSprite(): Promise<Sprite> {
  const icons = await fetch(sheet('glyphs.json')).then((r) => r.json())
  const image = new Image()
  image.src = sheet('glyphs.png')
  await image.decode()
  return { icons, width: image.naturalWidth, height: image.naturalHeight }
}

function Line({ colour, dash, width = 2.5, opacity = 1 }: { colour: string; dash?: string; width?: number; opacity?: number }) {
  return (
    <svg width="34" height="12" aria-hidden="true">
      <line x1="2" y1="6" x2="32" y2="6" stroke={colour} strokeWidth={width} strokeDasharray={dash} strokeLinecap="round" opacity={opacity} />
    </svg>
  )
}

function Dot({ r, fill, stroke, inner }: { r: number; fill: string; stroke?: string; inner?: boolean }) {
  return (
    <svg width="34" height="14" aria-hidden="true">
      <circle cx="17" cy="7" r={r} fill={fill} stroke={stroke} strokeWidth={stroke ? 1.2 : 0} />
      {inner && <circle cx="17" cy="7" r="1.4" fill={tokens.ink} />}
    </svg>
  )
}

function Area({ colour }: { colour: string }) {
  return (
    <svg width="34" height="16" aria-hidden="true">
      <rect x="3" y="2" width="28" height="12" rx="4" fill={colour} fillOpacity={0.12} stroke={colour} strokeDasharray="2 2" />
    </svg>
  )
}

function Icon({ name, sprite, scale }: { name: string; sprite: Sprite | null; scale: number }) {
  const s = sprite?.icons[name]
  if (!sprite || !s) return <span className="key-glyph" />
  return (
    <span
      className="key-glyph"
      aria-hidden="true"
      style={{
        width: s.width * scale,
        height: s.height * scale,
        backgroundImage: `url(${sheet('glyphs@2x.png')})`,
        backgroundSize: `${sprite.width * scale}px ${sprite.height * scale}px`,
        backgroundPosition: `${-s.x * scale}px ${-s.y * scale}px`,
      }}
    />
  )
}

type Props = {
  story: Story | null
  journey: string
  // The latest episode whose features may show (spoiler mode).
  reached: string
}

export function LayerKey({ story, journey, reached }: Props) {
  const [open, setOpen] = useState(false)
  const [sprite, setSprite] = useState<Sprite | null>(null)
  const [vignettes, setVignettes] = useState<Vignette[]>([])
  useEffect(() => {
    if (!open || sprite) return
    loadSprite().then(setSprite, () => setSprite(null))
    fetch(`${import.meta.env.BASE_URL}data/vignettes.geojson`)
      .then((r) => (r.ok ? r.json() : { features: [] }))
      .then((fc: { features: { properties: Vignette & { kind: string } }[] }) =>
        setVignettes(fc.features.map((f) => f.properties).filter((p) => p.kind === 'vignette' && p.vignette)),
      )
      .catch(() => setVignettes([]))
  }, [open, sprite])
  // The first vignette the reader has reached stands for them all.
  const vignette = vignettes
    .filter((v) => v.first_seen <= reached)
    .sort((a, b) => a.first_seen.localeCompare(b.first_seen) || a.priority - b.priority)[0]

  const shown = useMemo(() => {
    const journeys = new Map<string, string>()
    for (const f of [...(story?.stops.features ?? []), ...(story?.journeys.features ?? [])]) {
      const { journey: id, first_seen } = f.properties ?? {}
      if (id && (!journeys.has(id) || first_seen < journeys.get(id)!)) journeys.set(id, first_seen)
    }
    const roles = new Set(story?.places.features.map((f) => f.properties.role))
    const areaKinds = new Set(story?.areas.features.map((f) => f.properties?.kind))
    const sightline = story?.journeys.features.find((f) => f.properties?.kind === 'sightline')
    return { journeys: [...journeys].sort(), roles, areaKinds, sightline }
  }, [story])
  const ink = journeyInk[journey] ?? tokens.ink

  return (
    <details className="layer-key" open={open} onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>Key</summary>
      <div className="layer-key-body">
        {shown.journeys.length > 0 && (
          <>
            <h3>Journeys</h3>
            <ul>
              {shown.journeys.map(([id, firstSeen]) => (
                <li key={id} data-first-seen={firstSeen}>
                  <Line colour={journeyInk[id] ?? tokens.ink} />
                  {id}. {JOURNEYS[id] ?? id}
                </li>
              ))}
              <li>
                <Line colour={tokens.ink} />
                The road or river the book names
              </li>
              <li>
                <Line colour={tokens.ink} dash="5 3.5" />
                The way is not known
              </li>
              <li>
                <Line colour={ink} opacity={0.4} />
                The road ahead, when stepping through
              </li>
              {shown.sightline && (
                <li data-first-seen={shown.sightline.properties?.first_seen}>
                  <Line colour={journeyInk[shown.sightline.properties?.journey] ?? tokens.ink} dash="0.1 5" width={3} />
                  The false dawn: its direction only
                </li>
              )}
            </ul>
          </>
        )}
        <h3>Places</h3>
        <ul>
          <li>
            <span className="key-mark">
              <span className="key-stop" style={{ borderColor: ink }}>
                1
              </span>
            </span>
            Stop on the journey in focus
          </li>
          {shown.roles.has('stop') && (
            <li>
              <Dot r={4} fill={tokens.paper} stroke={tokens.ink} />
              Place on a journey
            </li>
          )}
          {shown.roles.has('passing') && (
            <li>
              <Dot r={3} fill={tokens.paper} stroke={tokens.ink} />
              Place passed or named
            </li>
          )}
          {shown.roles.has('tale') && (
            <li>
              <Dot r={4} fill={tokens.paper} stroke={tokens.ink} inner />
              Place in a tale
            </li>
          )}
          <li>
            <Dot r={2} fill={tokens.inkFaint} />
            Town the book does not name
          </li>
          {shown.areaKinds.has('inferred-area') && (
            <li>
              <Area colour={ink} />
              Inferred area: somewhere in here
            </li>
          )}
          {shown.areaKinds.has('region') && (
            <li>
              <Area colour={tokens.ink} />
              Region
            </li>
          )}
        </ul>
        <h3>Mountains</h3>
        <ul className="key-glyphs">
          {GLYPHS.map(([name, label]) => (
            <li key={name}>
              <Icon name={`${name}-01`} sprite={sprite} scale={GLYPH_SCALE} />
              {label}
            </li>
          ))}
        </ul>
        {vignette && (
          <>
            <h3>Drawings</h3>
            <ul>
              <li data-first-seen={vignette.first_seen}>
                <Icon name={vignette.vignette} sprite={sprite} scale={VIGNETTE_SCALE} />
                A scene from the book, near where it happens; a fine line may lead to the place
              </li>
            </ul>
          </>
        )}
      </div>
    </details>
  )
}
