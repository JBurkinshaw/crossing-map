import { useEffect, useState } from 'react'

// A published JSON file from data/, fetched once `enabled` is first true. `failed` is set when the request or
// the parse fails, so the interface can say so rather than show an empty list as if there were nothing.
export type Loaded<T> = { data: T | null; failed: boolean }

export function useJson<T>(file: string, enabled = true): Loaded<T> {
  const [state, setState] = useState<Loaded<T>>({ data: null, failed: false })
  useEffect(() => {
    if (!enabled) return
    const controller = new AbortController()
    fetch(`${import.meta.env.BASE_URL}data/${file}`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`${file}: HTTP ${r.status}`)
        return r.json() as Promise<T>
      })
      .then(
        (data) => setState({ data, failed: false }),
        (e: unknown) => {
          if (controller.signal.aborted) return
          console.error('Data failed to load:', e)
          setState({ data: null, failed: true })
        },
      )
    return () => controller.abort()
  }, [file, enabled])
  return state
}
