import { useEffect, useRef, type PointerEvent } from 'react'

// Compare mode's swipe: the classic base shows left of the split. The split lives in a CSS variable, --split, on
// the map area, which ClassicUnderlay's clip and this handle read, so a drag repaints two elements instead of
// re-rendering the map tree.
const MIN = 5
const MAX = 95
const STEP = 5

// Kept at module level so the split survives leaving and re-entering compare mode.
let lastSplit = 50

export function CompareSwipe() {
  const handle = useRef<HTMLDivElement>(null)
  const split = useRef(lastSplit)
  const set = (value: number) => {
    split.current = Math.min(MAX, Math.max(MIN, value))
    lastSplit = split.current
    const el = handle.current
    el?.parentElement?.style.setProperty('--split', `${split.current}%`)
    el?.setAttribute('aria-valuenow', String(Math.round(split.current)))
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
      onPointerDown={drag}
      role="slider"
      aria-label="Compare the classic map and satellite"
      aria-valuemin={MIN}
      aria-valuemax={MAX}
      aria-valuenow={50}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'ArrowLeft') set(split.current - STEP)
        if (e.key === 'ArrowRight') set(split.current + STEP)
      }}
    />
  )
}
