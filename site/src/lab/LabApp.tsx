import { lazy, Suspense, useState } from 'react'

// The lab's sections, one at a time; each is loaded when first opened. A section is a default-exported component
// with no props that fills the space below the tabs; sections that need the classic map use LabMap (LabMap.tsx).
const SECTIONS = [
  { id: 'hillshade', label: 'Hillshade', component: lazy(() => import('./hillshade/HillshadeLab')) },
  { id: 'wheeler', label: 'Wheeler', component: lazy(() => import('./wheeler/WheelerLab')) },
] as const
type SectionId = (typeof SECTIONS)[number]['id']

// The open section is kept in the address (#hillshade, #wheeler), so a reload or a shared link opens it again.
const fromHash = (): SectionId => SECTIONS.find((s) => `#${s.id}` === window.location.hash)?.id ?? SECTIONS[0].id

export default function LabApp() {
  const [open, setOpen] = useState<SectionId>(fromHash)
  const choose = (id: SectionId) => {
    setOpen(id)
    history.replaceState(null, '', `#${id}`)
  }
  // Tabs: one tab stop, the arrow keys move between them (WAI-ARIA tabs pattern).
  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const by = { ArrowRight: 1, ArrowLeft: -1 }[e.key]
    if (!by) return
    e.preventDefault()
    const next = SECTIONS[(SECTIONS.findIndex((s) => s.id === open) + by + SECTIONS.length) % SECTIONS.length]
    choose(next.id)
    e.currentTarget.querySelector<HTMLButtonElement>(`#tab-${next.id}`)?.focus()
  }
  const Section = SECTIONS.find((s) => s.id === open)!.component
  return (
    <div className="lab">
      <header className="lab-header">
        <h1>Map lab</h1>
        <div role="tablist" aria-label="Lab sections" onKeyDown={onKeyDown}>
          {SECTIONS.map((s) => (
            <button key={s.id} id={`tab-${s.id}`} type="button" role="tab" aria-selected={open === s.id} aria-controls="lab-panel"
              tabIndex={open === s.id ? 0 : -1} onClick={() => choose(s.id)}>
              {s.label}
            </button>
          ))}
        </div>
        <a href="./">Back to the map</a>
      </header>
      <main id="lab-panel" role="tabpanel" aria-labelledby={`tab-${open}`} className="lab-panel">
        <Suspense fallback={<p className="lab-placeholder">Loading…</p>}>
          <Section />
        </Suspense>
      </main>
    </div>
  )
}
