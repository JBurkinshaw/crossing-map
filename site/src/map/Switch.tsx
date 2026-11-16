import { useId, type KeyboardEvent, type ReactNode } from 'react'

// A row of switches, one of which is on: a radio group, one tab stop, with the arrow keys moving the choice.
// Under it, one line says what the chosen option does: hover titles never show on a touch screen.
export type SwitchOption<T extends string> = {
  id: T
  label: ReactNode
  // One short line on what the option does, shown under the row while it is chosen.
  description: string
  disabled: boolean
  // A paired option shows as half chosen (the two maps compare mode shows).
  paired?: boolean
}

export function Switch<T extends string>(props: {
  label: string
  options: SwitchOption<T>[]
  value: T
  onChange: (value: T) => void
  // Said instead of the chosen option's description, such as why the row cannot be used now.
  note?: string
}) {
  const { label, options, value, onChange, note } = props
  const noteId = useId()
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
    <div>
      <div className="basemap-switch" role="radiogroup" aria-label={label} aria-describedby={noteId} onKeyDown={onKeyDown}>
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            role="radio"
            data-id={o.id}
            data-paired={o.paired || undefined}
            aria-checked={value === o.id}
            tabIndex={value === o.id ? 0 : -1}
            disabled={o.disabled}
            onClick={() => onChange(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>
      <p className="control-note" id={noteId}>
        {note ?? options.find((o) => o.id === value)?.description}
      </p>
    </div>
  )
}
