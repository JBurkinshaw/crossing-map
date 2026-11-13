import { useState } from 'react'

// Extent-driven content (docs/plan.md, section 9): the stops, places and areas in the map's current view,
// already filtered to the reader's progress. App works the list out each time the map stops moving.
export type InViewItem = {
  layer: 'stops' | 'places' | 'areas'
  id: string
  name: string
  first_seen: string
  role: string | null
  // Stops: the stop's place in the journey in focus.
  index?: number
}

const GROUPS: { layer: InViewItem['layer']; title: string }[] = [
  { layer: 'stops', title: 'Stops' },
  { layer: 'places', title: 'Places' },
  { layer: 'areas', title: 'Areas' },
]
const SHOWN_AT_FIRST = 12

type Props = {
  items: InViewItem[]
  onPick: (item: InViewItem) => void
  // Open at first on a desktop; closed in the phone drawer, where room is short.
  open: boolean
  onToggle: (open: boolean) => void
}

export function InView({ items, onPick, open, onToggle }: Props) {
  // Groups the reader has asked to see in full.
  const [all, setAll] = useState<Set<string>>(new Set())
  return (
    <details className="in-view" open={open} onToggle={(e) => onToggle(e.currentTarget.open)}>
      <summary>
        In view <span className="meta">({items.length})</span>
      </summary>
      {items.length === 0 ? (
        <p className="meta">Nothing named in this part of the map yet.</p>
      ) : (
        GROUPS.map(({ layer, title }) => {
          const group = items.filter((i) => i.layer === layer)
          if (group.length === 0) return null
          const shown = all.has(layer) ? group : group.slice(0, SHOWN_AT_FIRST)
          return (
            <div key={layer}>
              <h3>{title}</h3>
              <ul>
                {shown.map((item) => (
                  <li key={item.id} data-first-seen={item.first_seen} data-role={item.role ?? undefined}>
                    {/* The name alone, as in the stop list, so the spoiler test can match it. */}
                    <button type="button" onClick={() => onPick(item)}>
                      {item.name}
                    </button>
                  </li>
                ))}
              </ul>
              {shown.length < group.length && (
                <button type="button" className="text-button" onClick={() => setAll(new Set([...all, layer]))}>
                  Show all {group.length} {title.toLowerCase()}
                </button>
              )}
            </div>
          )
        })
      )}
    </details>
  )
}
