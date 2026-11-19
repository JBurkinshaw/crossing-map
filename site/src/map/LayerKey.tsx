import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { createPortal } from 'react-dom'
import { JOURNEY_SHORT, JOURNEYS } from '../data/journeys'
import { ROUTE_LABEL } from '../data/routeLabels'
import type { Story } from '../data/story'
import type { Units } from '../units'
import { inZone } from './cluster'
import { contextImageId, drawContextMark } from './contextPlaces'
import { dataUrl, inkPatterns, TILE as INK_TILE } from './landcoverInk'
import { journeyInks, LAND_COVERS, palette as tokens, routeLines, SPRITE } from './tokens'
import { useOtherReadingShown } from './otherReading'
import { drawWaterMark, type WaterMark } from './waterPlaces'

// The layer key (legend, design section 9) for the vintage map: one row per kind of mark the map draws, from
// the story it is given. That story is already filtered to the reader's progress, so a journey, a region or
// the false dawn appears in the key only once it can appear on the map; so does the drawings' row, from the
// drawings reached. The rows split into two tabs, the story's marks and the land's, so neither runs off a
// laptop screen. On phones the key opens as a sheet from the bottom of the screen.

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
// Glyphs at this fraction of their map size; the drawing at this one. The @2x sheet keeps the key sharp.
const GLYPH_SCALE = 0.6
const VIGNETTE_SCALE = 0.8
type Sprite = { icons: Record<string, { x: number; y: number; width: number; height: number }>; width: number; height: number }
type Vignette = { vignette: string; first_seen: string; priority: number; label?: string }

// The small marks of the context places (contextPlaces.ts) and the water places (waterPlaces.ts), drawn by the
// map's own functions so the key matches the map. Ruin and station are both open squares, a little apart in
// size, and corral and spring both rings, in ink and in water blue; their labels say which is which.
// The long labels take a whole row, after the rest.
type SmallMark = { label: string; context?: string; water?: WaterMark; opacity: number; wide?: boolean }
const CONTEXT_OPACITY = 0.8 // contextPlaceLayer's icon-opacity
const WATER_OPACITY = 0.9 // waterPlaceLayer's icon-opacity
const SMALL_MARKS: SmallMark[] = [
  { label: 'Fort', context: 'flag', opacity: CONTEXT_OPACITY },
  { label: 'Mine', context: 'picks', opacity: CONTEXT_OPACITY },
  { label: 'Church', context: 'cross', opacity: CONTEXT_OPACITY },
  { label: 'Cemetery', context: 'grave', opacity: CONTEXT_OPACITY },
  { label: 'Ranch', context: 'square', opacity: CONTEXT_OPACITY },
  { label: 'Camp', context: 'tent', opacity: CONTEXT_OPACITY },
  { label: 'Sawmill', context: 'saw', opacity: CONTEXT_OPACITY },
  { label: 'Railway tunnel', context: 'tunnel', opacity: CONTEXT_OPACITY },
  { label: 'Corral (ink ring)', context: 'ring', opacity: CONTEXT_OPACITY },
  { label: 'Spring (blue ring)', water: 'ring', opacity: WATER_OPACITY },
  { label: 'Well', context: 'well', opacity: CONTEXT_OPACITY },
  { label: 'Tank', water: 'ringdot', opacity: WATER_OPACITY },
  { label: 'Windmill', context: 'windmill', opacity: CONTEXT_OPACITY },
  { label: 'School, post office or customs', context: 'dot', opacity: CONTEXT_OPACITY, wide: true },
  { label: 'Ruin or abandoned place: the smaller square', context: 'ruin', opacity: CONTEXT_OPACITY, wide: true },
  { label: 'Station: the larger square', context: 'station', opacity: CONTEXT_OPACITY, wide: true },
]

// A mark drawn at the map's pixel ratio, as an image the key can show at the map's size.
function markUrl(m: SmallMark): string {
  const image = m.context ? drawContextMark(contextImageId(m.context), tokens) : drawWaterMark(m.water!, tokens)
  const canvas = document.createElement('canvas')
  canvas.width = image.width
  canvas.height = image.height
  canvas.getContext('2d')!.putImageData(image, 0, 0)
  return canvas.toDataURL()
}

const sheet = (name: string) => `${import.meta.env.BASE_URL}sprites/${name}`

// The sprite index and the 1x sheet's size, which the @2x sheet is scaled down to.
async function loadSprite(): Promise<Sprite> {
  const icons = await fetch(sheet(`${SPRITE}.json`)).then((r) => r.json())
  const image = new Image()
  image.src = sheet(`${SPRITE}.png`)
  await image.decode()
  return { icons, width: image.naturalWidth, height: image.naturalHeight }
}

function Line({ colour, dash, width = 2.5, opacity = 1, cap = 'round', length = 34 }: {
  colour: string; dash?: string; width?: number; opacity?: number; cap?: 'round' | 'butt'; length?: number
}) {
  return (
    <svg width={length} height="12" aria-hidden="true">
      <line x1="2" y1="6" x2={length - 2} y2="6" stroke={colour} strokeWidth={width} strokeDasharray={dash} strokeLinecap={cap} opacity={opacity} />
    </svg>
  )
}

// A route line as StoryLayers draws it with its journey in focus: the same widths and dashes (tokens.routeLines).
function RouteLine({ colour, kind }: { colour: string; kind: keyof typeof routeLines }) {
  const line: { width: number; dash: readonly number[] | null; opacity?: number } = routeLines[kind]
  return line.dash ? (
    <Line colour={colour} width={line.width} dash={line.dash.join(' ')} opacity={line.opacity ?? 1} cap="butt" />
  ) : (
    <Line colour={colour} width={line.width} />
  )
}

// The railroad as style.ts draws it: a thin ink line under 1 px cross-ties, 4 px tall and 13 px apart (a line
// dash array scales with the line's width, so [0.25, 3] at width 4 gives 1 px ties and 12 px gaps).
function Railroad() {
  return (
    <svg width="34" height="12" aria-hidden="true">
      <line x1="2" y1="6" x2="32" y2="6" stroke={tokens.ink} strokeWidth={0.8} />
      <line x1="4" y1="6" x2="32" y2="6" stroke={tokens.ink} strokeWidth={4} strokeDasharray="1 12" />
    </svg>
  )
}

function Dot({ r, fill, stroke, width = 1.2 }: { r: number; fill: string; stroke?: string; width?: number }) {
  return (
    <svg width="34" height="14" aria-hidden="true">
      <circle cx="17" cy="7" r={r} fill={fill} stroke={stroke} strokeWidth={stroke ? width : 0} />
    </svg>
  )
}

function Diamond({ fill, stroke }: { fill: string; stroke: string }) {
  return (
    <svg width="34" height="14" aria-hidden="true">
      <path d="M17 1.5 L22.5 7 L17 12.5 L11.5 7 Z" fill={fill} stroke={stroke} strokeWidth={1.3} />
    </svg>
  )
}

// An inferred area as StoryLayers draws it in focus: a flat tint with a dotted edge.
function Area({ colour }: { colour: string }) {
  return (
    <svg width="34" height="16" aria-hidden="true">
      <rect x="3" y="2" width="28" height="12" rx="4" fill={colour} fillOpacity={0.18} stroke={colour} strokeWidth={1.5}
        strokeDasharray="0.1 3.75" strokeLinecap="round" strokeOpacity={0.9} />
    </svg>
  )
}

// A land cover class as relief.ts fills it: its colour, with its ink texture over it (decision 0042).
function Swatch({ colour, ink }: { colour: string; ink?: string }) {
  return (
    <span className="key-swatch" aria-hidden="true"
      style={{ backgroundColor: colour, backgroundImage: ink ? `url(${ink})` : undefined, backgroundSize: `${INK_TILE}px` }} />
  )
}

// Each class's ink texture as an image, for the key's swatches.
const inkUrls = () => Object.fromEntries(inkPatterns(tokens.ink, tokens.water).map(({ id, image }) => [id, dataUrl(image)]))

// A region as StoryLayers draws it: no fill, a fine ink line with a broad soft band inside it.
function Region() {
  return (
    <svg width="34" height="16" aria-hidden="true">
      <rect x="4.5" y="3.5" width="25" height="9" rx="3" fill="none" stroke={tokens.ink} strokeWidth={3} strokeOpacity={0.15} />
      <rect x="3" y="2" width="28" height="12" rx="4" fill="none" stroke={tokens.ink} strokeWidth={0.8} strokeOpacity={0.8} />
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
        backgroundImage: `url(${sheet(`${SPRITE}@2x.png`)})`,
        backgroundSize: `${sprite.width * scale}px ${sprite.height * scale}px`,
        backgroundPosition: `${-s.x * scale}px ${-s.y * scale}px`,
      }}
    />
  )
}

const TABS = [
  ['story', 'The story'],
  ['land', 'The land'],
] as const
type Tab = (typeof TABS)[number][0]

type Props = {
  story: Story | null
  journey: string
  // The latest episode whose features may show (spoiler mode).
  reached: string
  // The spot height's sample is in the map's units.
  units: Units
  // On phones the key opens as a sheet from the bottom of the screen, with its own close button.
  phone: boolean
  // Whether the key is open: MapView holds it, as opening the key closes the Map menu and the other way round.
  open: boolean
  onOpen: (open: boolean) => void
  // The reader has picked Land cover as the ground (decision 0040).
  landcover: boolean
  // Whether the map draws every journey or only the one in focus, and the switch between them.
  allJourneys: boolean
  onAllJourneys: (all: boolean) => void
}

export function LayerKey({ story, journey, reached, units, phone, open, onOpen, landcover, allJourneys, onAllJourneys }: Props) {
  const journeyInk = journeyInks(tokens)
  const [tab, setTab] = useState<Tab>('story')
  const [sprite, setSprite] = useState<Sprite | null>(null)
  const [vignettes, setVignettes] = useState<Vignette[]>([])
  const toggle = useRef<HTMLButtonElement>(null)
  const sheetClose = useRef<HTMLButtonElement>(null)
  const id = useId()
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
  // On phones the key is a modal sheet: everything behind it is inert, and focus starts on its Close button, so
  // a screen reader and the keyboard land in it.
  const sheet = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = sheet.current
    if (!open || !phone || !dialog) return
    if (!dialog.open) dialog.showModal()
    sheetClose.current?.focus()
  }, [open, phone])
  // The drawing that stands for them all: the first person or animal the reader has reached (their drawings
  // carry no caption), else the first drawing reached.
  const vignette = useMemo(() => {
    const reachedSoFar = vignettes
      .filter((v) => v.first_seen <= reached)
      .sort((a, b) => a.first_seen.localeCompare(b.first_seen) || a.priority - b.priority)
    return reachedSoFar.find((v) => !v.label) ?? reachedSoFar[0]
  }, [vignettes, reached])
  const marks = useMemo(() => (open ? SMALL_MARKS.map((m) => ({ ...m, url: markUrl(m) })) : []), [open])

  const otherReading = useOtherReadingShown()
  const shown = useMemo(() => {
    const journeys = new Map<string, string>()
    for (const f of [...(story?.stops.features ?? []), ...(story?.journeys.features ?? [])]) {
      const { journey: id, first_seen } = f.properties ?? {}
      if (id && (!journeys.has(id) || first_seen < journeys.get(id)!)) journeys.set(id, first_seen)
    }
    const roles = new Set(story?.places.features.map((f) => f.properties.role))
    const areaKinds = new Set(story?.areas.features.map((f) => f.properties?.kind))
    const sightline = story?.journeys.features.find((f) => f.properties?.kind === 'sightline')
    const modeled = story?.journeys.features
      .filter((f) => f.properties?.method === 'modeled')
      .sort((a, b) => a.properties?.first_seen.localeCompare(b.properties?.first_seen))[0]
    // Grouped-stop markers draw only around Cloverdale and the Peloncillos (cluster.ts).
    const grouped = [...(story?.stops.features ?? []), ...(story?.places.features ?? [])].some((f) => inZone(f.geometry.coordinates))
    return { journeys: [...journeys].sort(), roles, areaKinds, sightline, modeled, grouped }
  }, [story])
  const ink = journeyInk[journey] ?? tokens.ink
  // Drawn only once the key is open with land cover on.
  const landcoverInk = useMemo(() => (open && landcover ? inkUrls() : null), [open, landcover])

  // Closed by the reader (Close, Escape, a tap outside the sheet), the key gives focus back to the Key button.
  // That waits until the sheet has gone, as the button is inert while the modal sheet is open. Closed because the
  // Map menu opened, it leaves focus in the menu.
  const returnFocus = useRef(false)
  const close = () => {
    returnFocus.current = true
    onOpen(false)
  }
  useEffect(() => {
    if (open || !returnFocus.current) return
    returnFocus.current = false
    toggle.current?.focus()
  }, [open])
  // Escape closes the desktop key from anywhere inside it; the phone sheet, a <dialog>, has its own cancel event.
  const box = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open || phone) return
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape' && box.current?.contains(e.target as Node)) close()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  })
  // The tabs: one tab stop, the arrow keys (and Home and End) moving to the other tab and showing it.
  const onTabKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const at = TABS.findIndex(([t]) => t === tab)
    const to = { ArrowRight: at + 1, ArrowLeft: at - 1, Home: 0, End: TABS.length - 1 }[e.key]
    if (to === undefined) return
    e.preventDefault()
    const next = TABS[(to + TABS.length) % TABS.length][0]
    setTab(next)
    document.getElementById(`${id}-tab-${next}`)?.focus()
  }

  const storyPanel = (
    <>
      {shown.journeys.length > 0 && (
        <>
          <h3>Journeys</h3>
          <ul className="key-journeys">
            {shown.journeys.map(([j, firstSeen]) => (
              <li key={j} data-first-seen={firstSeen} title={`${j}. ${JOURNEYS[j] ?? j}`}>
                <Line colour={journeyInk[j] ?? tokens.ink} length={16} />
                <span aria-hidden="true">{j} {JOURNEY_SHORT[j] ?? JOURNEYS[j] ?? j}</span>
                <span className="visually-hidden">{j}. {JOURNEYS[j] ?? j}</span>
              </li>
            ))}
          </ul>
          {shown.journeys.length > 1 && (
            <label className="key-all-journeys">
              <input type="checkbox" checked={allJourneys} onChange={(e) => onAllJourneys(e.target.checked)} />
              Show all journeys
            </label>
          )}
          <ul>
            <li>
              <Line colour={ink} opacity={0.4} />
              Legs after the stop you are on
            </li>
            {shown.sightline && (
              <li data-first-seen={shown.sightline.properties?.first_seen}>
                <Line colour={journeyInk[shown.sightline.properties?.journey] ?? tokens.ink} dash="0.1 5" width={3} />
                The false dawn: its direction only
              </li>
            )}
          </ul>
          <h3>How sure the line is</h3>
          <ul>
            <li>
              <RouteLine colour={tokens.ink} kind="traced" />
              {ROUTE_LABEL.traced}
            </li>
            {shown.modeled && (
              <li data-first-seen={shown.modeled.properties?.first_seen}>
                <RouteLine colour={tokens.ink} kind="modeled" />
                {ROUTE_LABEL.modeled}
              </li>
            )}
            <li>
              <RouteLine colour={tokens.ink} kind="curve" />
              {ROUTE_LABEL.curve}
            </li>
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
        {shown.grouped && (
          <li>
            <span className="key-mark">
              <span className="cluster-marker">
                3<span className="cluster-word">places</span>
              </span>
            </span>
            Stops or places close together: click or tap to spread them
          </li>
        )}
        {shown.roles.has('stop') && (
          <li>
            <Dot r={4} fill={tokens.ink} stroke={tokens.paper} width={1.5} />
            Place on a journey
          </li>
        )}
        {shown.roles.has('passing') && (
          <li>
            <Dot r={3.5} fill={tokens.paper} stroke={tokens.ink} />
            Place passed or named
          </li>
        )}
        {shown.roles.has('tale') && (
          <li>
            <Diamond fill={tokens.paper} stroke={tokens.ink} />
            Place in a tale
          </li>
        )}
        {shown.areaKinds.has('inferred-area') && (
          <li>
            <Area colour={ink} />
            Inferred area: somewhere in here
          </li>
        )}
        {shown.areaKinds.has('region') && (
          <li>
            <Region />
            Region
          </li>
        )}
        {otherReading && (
          <li>
            {/* As otherReading.ts draws it: a dashed ink ring on a faint ink wash. */}
            <svg className="key-mark" width="34" height="18" viewBox="0 0 34 18" aria-hidden="true">
              <circle cx="17" cy="9" r="7.5" fill={tokens.ink} fillOpacity={0.06} stroke={tokens.ink} strokeWidth={1.5} strokeDasharray="3 2" />
            </svg>
            An open question’s other reading: {otherReading.charAt(0).toLowerCase() + otherReading.slice(1)}
          </li>
        )}
      </ul>
    </>
  )

  const landPanel = (
    <>
      <ul>
        <li>
          {/* As style.ts draws the country line: dash, gap, dot, gap ([6, 2, 1, 2]), scaled by a 1.8 px width. */}
          <Line colour={tokens.ink} width={1.8} dash="10.8 3.6 1.8 3.6" cap="butt" />
          International boundary
        </li>
        <li>
          {/* The state line: [4, 2] dashes at 0.9 px, 55 % ink. */}
          <Line colour={tokens.ink} width={0.9} dash="3.6 1.8" opacity={0.55} cap="butt" />
          State line
        </li>
        <li>
          <Railroad />
          Railway
        </li>
        <li>
          <Dot r={2} fill={tokens.inkFaint} />
          Town the book does not name
        </li>
        <li>
          <span className="key-mark key-mark-wide">
            <span className="key-spot">{units === 'metric' ? '1,585 m' : '5,200 ft'}</span>
          </span>
          Spot height
        </li>
      </ul>
      {landcover && (
        <>
          <h3>Land cover, along the journeys</h3>
          <ul>
            {LAND_COVERS.map((c) => (
              <li key={c.id}>
                <Swatch colour={tokens.landcover[c.id]} ink={landcoverInk?.[`ink-${c.id}`]} />
                {c.label}
              </li>
            ))}
          </ul>
        </>
      )}
      <h3>Small marks</h3>
      <ul className="key-small-marks">
        {marks.map((m) => (
          <li key={m.label} className={m.wide ? 'key-wide' : undefined}>
            <img src={m.url} width={8} height={8} alt="" style={{ opacity: m.opacity }} />
            {m.label}
          </li>
        ))}
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
              People, animals and things from the book, set just beside their place, not on it. Not to scale.
            </li>
          </ul>
        </>
      )}
    </>
  )

  const body = (
    <>
      <div className="key-tabs" role="tablist" aria-label="Key" onKeyDown={onTabKey}>
        {TABS.map(([t, label]) => (
          <button
            key={t}
            type="button"
            role="tab"
            id={`${id}-tab-${t}`}
            aria-selected={tab === t}
            aria-controls={`${id}-panel-${t}`}
            tabIndex={tab === t ? 0 : -1}
            onClick={() => setTab(t)}
          >
            {label}
          </button>
        ))}
      </div>
      {TABS.map(([t]) => (
        // In the tab order, so a keyboard can scroll a panel that holds no controls.
        <div key={t} className="key-panel" role="tabpanel" id={`${id}-panel-${t}`} aria-labelledby={`${id}-tab-${t}`} tabIndex={0} hidden={tab !== t}>
          {t === 'story' ? storyPanel : landPanel}
        </div>
      ))}
    </>
  )

  return (
    <div className="layer-key" ref={box}>
      <button ref={toggle} type="button" className="layer-key-toggle" aria-expanded={open} aria-controls={`${id}-body`} onClick={() => onOpen(!open)}>
        Key
      </button>
      {open &&
        (phone ? (
          // Portalled to the page, so the modal sheet is not inside the cartouche, which goes inert behind it.
          createPortal(
            // Escape, the keyboard's way out, is the dialog's cancel event; the click is for a tap on the backdrop.
            // oxlint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions
            <dialog
              ref={sheet}
              className="key-sheet"
              id={`${id}-body`}
              aria-labelledby={`${id}-title`}
              onCancel={(e) => {
                e.preventDefault()
                close()
              }}
              // A tap on the backdrop lands on the <dialog> itself, outside its box.
              onClick={(e) => {
                const r = e.currentTarget.getBoundingClientRect()
                const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom
                if (e.target === e.currentTarget && !inside) close()
              }}
            >
              <div className="key-sheet-head">
                <h2 id={`${id}-title`}>Key</h2>
                <button ref={sheetClose} type="button" className="key-sheet-close" onClick={close}>
                  Close
                </button>
              </div>
              {body}
            </dialog>,
            document.body,
          )
        ) : (
          <div className="layer-key-body" id={`${id}-body`}>
            {body}
          </div>
        ))}
    </div>
  )
}
