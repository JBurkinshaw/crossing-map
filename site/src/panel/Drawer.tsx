import { useRef, useState, type FocusEvent, type KeyboardEvent, type PointerEvent, type ReactNode } from 'react'

// The phone shell of the panel (docs/plan.md, section 9): a bottom sheet with three heights, peek (96 px, the
// stepper only), half and full. The handle drags, taps (each tap raises it a step, from full back to peek) and
// takes the arrow keys. The panel's own children go inside; Panel puts the stepper first so it shows at peek.

export type DrawerHeight = 'peek' | 'half' | 'full'
const HEIGHTS: DrawerHeight[] = ['peek', 'half', 'full']
const NAMES: Record<DrawerHeight, string> = { peek: 'lowered', half: 'half open', full: 'open' }

// A drag shorter than this is a tap; a release faster than this (px per ms) carries on to the next height.
const TAP_PX = 6
const PEEK_PX = 96
const FLICK = 0.5

type Props = {
  label: string
  height: DrawerHeight
  onHeight: (height: DrawerHeight) => void
  // The part that shows at peek height; focus anywhere below it raises the drawer.
  peek: ReactNode
  children: ReactNode
}

export function Drawer({ label, height, onHeight, peek, children }: Props) {
  const sheet = useRef<HTMLElement>(null)
  const peekRow = useRef<HTMLDivElement>(null)
  // The height in px while the handle is dragged; null otherwise.
  const [dragged, setDragged] = useState<number | null>(null)
  const drag = useRef<{ y: number; start: number; last: number; t: number; v: number; moved: boolean } | null>(null)
  // A drag ends in a click too, which must not change the height again.
  const dragEnded = useRef(false)
  const at = HEIGHTS.indexOf(height)
  const step = (by: number) => onHeight(HEIGHTS[Math.max(0, Math.min(HEIGHTS.length - 1, at + by))])

  // Each height in px, as index.css sets them: peek is 96 px over the safe-area inset (the bottom padding).
  const heightsPx = () => {
    const el = sheet.current!
    const box = el.parentElement!.getBoundingClientRect().height
    return [PEEK_PX + parseFloat(getComputedStyle(el).paddingBottom), box * 0.5, box * 0.92]
  }

  const onPointerDown = (e: PointerEvent<HTMLButtonElement>) => {
    if (e.button !== 0) return
    dragEnded.current = false
    const now = sheet.current!.getBoundingClientRect().height
    drag.current = { y: e.clientY, start: now, last: e.clientY, t: e.timeStamp, v: 0, moved: false }
    e.currentTarget.setPointerCapture(e.pointerId)
  }
  const onPointerMove = (e: PointerEvent<HTMLButtonElement>) => {
    const d = drag.current
    if (!d) return
    if (!d.moved && Math.abs(e.clientY - d.y) < TAP_PX) return
    d.moved = true
    const dt = Math.max(1, e.timeStamp - d.t)
    d.v = (e.clientY - d.last) / dt
    d.last = e.clientY
    d.t = e.timeStamp
    const [min, , max] = heightsPx()
    setDragged(Math.max(min, Math.min(max, d.start - (e.clientY - d.y))))
  }
  const onPointerUp = (e: PointerEvent<HTMLButtonElement>) => {
    const d = drag.current
    drag.current = null
    if (!d?.moved) return
    // A drag ends at the nearest height, or the next one along after a flick.
    const px = heightsPx()
    const now = Math.max(px[0], Math.min(px[2], d.start - (e.clientY - d.y)))
    let nearest = px.reduce((best, h, i) => (Math.abs(h - now) < Math.abs(px[best] - now) ? i : best), 0)
    if (d.v < -FLICK) nearest = px.findIndex((h) => h > now) === -1 ? 2 : px.findIndex((h) => h > now)
    else if (d.v > FLICK) nearest = Math.max(0, px.filter((h) => h < now).length - 1)
    dragEnded.current = true
    setDragged(null)
    onHeight(HEIGHTS[nearest])
  }

  const onClick = () => {
    if (dragEnded.current) {
      dragEnded.current = false
      return
    }
    onHeight(HEIGHTS[(at + 1) % HEIGHTS.length])
  }

  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    const by = { ArrowUp: 1, ArrowDown: -1, Home: -2, End: 2 }[e.key]
    if (by === undefined) return
    e.preventDefault()
    step(by)
  }

  // Focus that moves below the peek row brings the rest of the panel into view; the search box opens it fully,
  // so its results show above a phone's keyboard.
  const onFocus = (e: FocusEvent<HTMLElement>) => {
    if (e.target.matches('input[type="search"]')) return onHeight('full')
    if (height !== 'peek' || e.target.classList.contains('drawer-handle')) return
    if (peekRow.current?.contains(e.target)) return
    onHeight('half')
  }

  return (
    <aside
      ref={sheet}
      className={`panel drawer${dragged !== null ? ' is-dragging' : ''}`}
      data-height={height}
      aria-label={label}
      style={dragged !== null ? { height: dragged } : undefined}
      onFocus={onFocus}
    >
      <button
        type="button"
        className="drawer-handle"
        aria-label={`${label} panel, ${NAMES[height]}`}
        aria-expanded={height !== 'peek'}
        title="Drag, tap or use the arrow keys to resize"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={() => {
          drag.current = null
          setDragged(null)
        }}
        onClick={onClick}
        onKeyDown={onKeyDown}
      >
        <span aria-hidden="true" />
      </button>
      <div className="drawer-peek" ref={peekRow}>
        {peek}
      </div>
      <div className="drawer-body">{children}</div>
    </aside>
  )
}
