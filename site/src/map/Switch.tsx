import type { KeyboardEvent, ReactNode } from 'react'

// A row of switches, one of which is on: a radio group, one tab stop, with the arrow keys moving the choice.
export type SwitchOption<T extends string> = {
  id: T
  label: ReactNode
  title?: string
  // Spells out what a short label means; it starts with the label, so speech input can use the label.
  ariaLabel?: string
  disabled: boolean
  // A narrow option holds an icon; a paired one shows as half chosen (the two maps compare mode shows).
  narrow?: boolean
  paired?: boolean
}

export function Switch<T extends string>(props: { label: string; options: SwitchOption<T>[]; value: T; onChange: (value: T) => void }) {
  const { label, options, value, onChange } = props
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const by = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
    if (!by) return
    e.preventDefault()
    const enabled = options.filter((o) => !o.disabled)
    const next = enabled[(enabled.findIndex((o) => o.id === value) + by + enabled.length) % enabled.length]
    if (!next) return
    onChange(next.id)
    e.currentTarget.querySelector<HTMLButtonElement>(`[data-id="${next.id}"]`)?.focus()
  }
  return (
    <div className="basemap-switch" role="radiogroup" aria-label={label} onKeyDown={onKeyDown}>
      {options.map((o) => (
        <button
          key={o.id}
          type="button"
          role="radio"
          data-id={o.id}
          data-narrow={o.narrow || undefined}
          data-paired={o.paired || undefined}
          aria-checked={value === o.id}
          tabIndex={value === o.id ? 0 : -1}
          disabled={o.disabled}
          title={o.title}
          aria-label={o.ariaLabel}
          onClick={() => onChange(o.id)}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}
