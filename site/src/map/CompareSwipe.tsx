import { useEffect, useRef, type PointerEvent } from 'react'
import type { CompareWith } from './mode'

// Compare mode's swipe: the vintage base shows left of the split, satellite or Topo right of it. The split lives
// in a CSS variable, --split, on the map area, which VintageUnderlay's clip and this handle read, so a drag
// repaints two elements instead of re-rendering the map tree.
const MIN = 5
const MAX = 95
const STEP = 5

// Kept at module level so the split survives leaving and re-entering compare mode.
let lastSplit = 50

export function CompareSwipe({ compareWith }: { compareWith: CompareWith }) {
  const handle = useRef<HTMLDivElement>(null)
  const split = useRef(lastSplit)
  const other = compareWith === 'topo' ? 'Topo' : 'satellite'
  const set = (value: number) => {
    split.current = Math.min(MAX, Math.max(MIN, value))
    lastSplit = split.current
    const el = handle.current
    el?.parentElement?.style.setProperty('--split', `${split.current}%`)
    const share = Math.round(split.current)
    el?.setAttribute('aria-valuenow', String(share))
    // The other map's name is read from the handle, so this function depends on nothing that changes.
    el?.setAttribute('aria-valuetext', `Vintage map ${share}%, ${el.dataset.other} ${100 - share}%`)
  }
  useEffect(() => {
    set(split.current)
    const area = handle.current?.parentElement
    return () => {
      area?.style.removeProperty('--split')
    }
  }, [])

  const drag = (e: PointerEvent<HTMLDivElement>) => {
    const area = e.currentTarget.parentElement!.getBoundingClientRect()
    const move = (ev: globalThis.PointerEvent) => set(((ev.clientX - area.left) / area.width) * 100)
    const up = () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
    }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
  }

  return (
    <div
      ref={handle}
      className="swipe"
      data-other={other}
      onPointerDown={drag}
      role="slider"
      aria-label={`Compare the vintage map and ${other}`}
      aria-valuemin={MIN}
      aria-valuemax={MAX}
      aria-valuenow={50}
      tabIndex={0}
      onKeyDown={(e) => {
        const to = { ArrowLeft: split.current - STEP, ArrowRight: split.current + STEP, Home: MIN, End: MAX }[e.key]
        if (to === undefined) return
        e.preventDefault()
        set(to)
      }}
    >
      {/* The line also moves without a drag (WCAG 2.5.7): a tap on the map already picks a place, so the handle
          carries two buttons. They are outside the tab order, as the slider itself takes the arrow keys. */}
      <button type="button" className="swipe-step swipe-left" tabIndex={-1} aria-label={`More ${other}`} onPointerDown={(e) => e.stopPropagation()} onClick={() => set(split.current - STEP)}>
        ‹
      </button>
      <button type="button" className="swipe-step swipe-right" tabIndex={-1} aria-label="More of the vintage map" onPointerDown={(e) => e.stopPropagation()} onClick={() => set(split.current + STEP)}>
        ›
      </button>
    </div>
  )
}
